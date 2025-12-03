"""
电子书入库服务

负责从下载完成的文件中识别电子书，并移动到统一的书库目录结构。
"""

import os
import shutil
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.ebook import EBook, EBookFile
from app.constants.media_types import MEDIA_TYPE_EBOOK, normalize_media_type
from app.modules.ebook.work_resolver import EBookWorkResolver
from app.modules.media_renamer.category_helper import CategoryHelper


# 支持的电子书文件格式
SUPPORTED_EBOCK_FORMATS = {".epub", ".mobi", ".azw3", ".pdf", ".txt", ".fb2", ".djvu"}


class EBookImporter:
    """电子书入库服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.library_root = Path(settings.EBOOK_LIBRARY_ROOT)
        self.library_root.mkdir(parents=True, exist_ok=True)
        self.work_resolver = EBookWorkResolver()
        self.category_helper = CategoryHelper()  # 用于二级分类
    
    def is_ebook_file(self, file_path: str) -> bool:
        """判断文件是否为电子书格式"""
        path = Path(file_path)
        return path.suffix.lower() in SUPPORTED_EBOCK_FORMATS
    
    def parse_filename(self, filename: str) -> Dict[str, Any]:
        """
        从文件名解析书名、作者等信息
        
        支持的格式示例：
        - "作者 - 书名.epub"
        - "书名 - 作者.epub"
        - "系列名 第1卷 - 书名.epub"
        - "书名 (作者).epub"
        """
        path = Path(filename)
        stem = path.stem  # 不含扩展名的文件名
        
        # 尝试匹配 "作者 - 书名" 格式
        match = re.match(r"^(.+?)\s*-\s*(.+)$", stem)
        if match:
            author_part, title_part = match.groups()
            # 判断哪个是作者（通常作者较短或包含常见姓氏）
            if len(author_part) < 30 and not re.search(r"[第卷集]", author_part):
                return {
                    "author": author_part.strip(),
                    "title": title_part.strip(),
                }
            else:
                return {
                    "title": author_part.strip(),
                    "author": title_part.strip(),
                }
        
        # 尝试匹配 "书名 (作者)" 格式
        match = re.match(r"^(.+?)\s*\((.+?)\)$", stem)
        if match:
            title_part, author_part = match.groups()
            return {
                "title": title_part.strip(),
                "author": author_part.strip(),
            }
        
        # 尝试匹配 "系列名 第X卷 - 书名" 格式
        match = re.match(r"^(.+?)\s+第?(\d+)[卷集册]\s*-\s*(.+)$", stem)
        if match:
            series_part, volume, title_part = match.groups()
            return {
                "series": series_part.strip(),
                "volume_index": volume,
                "title": title_part.strip(),
            }
        
        # 默认：整个文件名作为书名
        return {
            "title": stem.strip(),
            "author": None,
        }
    
    def build_target_path(
        self,
        title: str,
        author: Optional[str] = None,
        series: Optional[str] = None,
        volume_index: Optional[str] = None,
        format: str = "epub",
        ebook: Optional[EBook] = None
    ) -> Path:
        """
        构建目标文件路径
        
        目录结构：
        - 如果命中分类：Books/分类名/作者/系列名/卷号 - 书名.扩展名
        - 如果未命中分类：Books/作者/系列名/卷号 - 书名.扩展名（保持原有结构）
        
        Args:
            title: 书名
            author: 作者
            series: 系列名
            volume_index: 卷号
            format: 文件格式
            ebook: EBook 对象（可选，用于获取 tags/language 等信息进行分类）
        """
        # 清理文件名中的非法字符
        def clean_name(name: str) -> str:
            # Windows 和 Linux 都不允许的字符
            illegal_chars = r'[<>:"/\\|?*]'
            return re.sub(illegal_chars, "_", name).strip()
        
        # 尝试获取分类
        category_result = None
        if ebook:
            # 构建分类匹配用的信息字典
            ebook_info = {
                "tags": ebook.tags,
                "language": ebook.language,
                "extra_metadata": ebook.extra_metadata
            }
            category_result = self.category_helper.get_ebook_category(ebook_info)
        
        author_clean = clean_name(author) if author else "未知作者"
        title_clean = clean_name(title)
        
        # 构建基础路径（Books/）
        base_dir = self.library_root / "Books"
        
        # 如果命中分类，在 Books/ 下增加分类目录
        if category_result and category_result.subcategory:
            base_dir = base_dir / category_result.subcategory
        
        if series:
            series_clean = clean_name(series)
            if volume_index:
                # Books/[分类/]作者/系列名/卷号 - 书名.epub
                target_dir = base_dir / author_clean / series_clean
                filename = f"{volume_index} - {title_clean}.{format}"
            else:
                # Books/[分类/]作者/系列名/书名.epub
                target_dir = base_dir / author_clean / series_clean
                filename = f"{title_clean}.{format}"
        else:
            # Books/[分类/]作者/书名.epub
            target_dir = base_dir / author_clean
            filename = f"{title_clean}.{format}"
        
        return target_dir / filename
    
    async def import_ebook_from_file(
        self,
        file_path: str,
        source_site_id: Optional[str] = None,
        source_torrent_id: Optional[str] = None,
        download_task_id: Optional[int] = None,
        media_type: Optional[str] = None
    ) -> Optional[EBook]:
        """
        从文件路径导入电子书
        
        Args:
            file_path: 源文件路径
            source_site_id: 来源站点 ID
            source_torrent_id: 来源种子 ID
            download_task_id: 下载任务 ID
            media_type: 媒体类型（如果为 ebook 则处理）
        
        Returns:
            创建的 EBook 对象，如果失败返回 None
        """
        # 检查媒体类型
        if media_type:
            normalized_type = normalize_media_type(media_type)
            if normalized_type != MEDIA_TYPE_EBOOK:
                logger.debug(f"文件 {file_path} 的媒体类型为 {normalized_type}，不是电子书，跳过")
                return None
        
        # 检查文件是否存在
        source_path = Path(file_path)
        if not source_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return None
        
        # 检查文件格式
        if not self.is_ebook_file(file_path):
            logger.debug(f"文件 {file_path} 不是支持的电子书格式")
            return None
        
        try:
            # 步骤 1: 解析文件名，获取基础元信息
            file_info = self.parse_filename(source_path.name)
            parsed_title = file_info.get("title") or source_path.stem
            parsed_author = file_info.get("author")
            parsed_series = file_info.get("series")
            parsed_volume_index = file_info.get("volume_index")
            
            # 获取文件大小和格式
            file_size_bytes = source_path.stat().st_size
            file_format = source_path.suffix[1:].lower()  # 去掉点号
            
            # 步骤 2: 先创建一个临时的 EBook 对象用于元数据增强（如果启用）
            # 这样可以先获取更准确的 ISBN/title/author 等信息
            temp_ebook = EBook(
                title=parsed_title,
                author=parsed_author,
                series=parsed_series,
                volume_index=parsed_volume_index,
                language="zh-CN",
            )
            
            # 步骤 3: 如果元数据增强已启用，先进行增强以获取更准确的信息
            enhanced_isbn = None
            enhanced_title = parsed_title
            enhanced_author = parsed_author
            enhanced_series = parsed_series
            enhanced_volume_index = parsed_volume_index
            
            try:
                from app.modules.ebook.metadata_service import get_metadata_service
                
                if settings.SMART_EBOOK_METADATA_ENABLED:
                    metadata_service = get_metadata_service()
                    update = await metadata_service.enrich_ebook_metadata(temp_ebook)
                    
                    if update:
                        # 使用增强后的元数据（优先使用增强后的字段）
                        if update.isbn:
                            enhanced_isbn = update.isbn
                        if update.title:
                            enhanced_title = update.title
                        if update.author:
                            enhanced_author = update.author
                        if update.series:
                            enhanced_series = update.series
                        if update.volume_index:
                            enhanced_volume_index = update.volume_index
                        
                        logger.debug(f"元数据增强完成: ISBN={enhanced_isbn}, title={enhanced_title}")
            except Exception as e:
                # 元数据增强失败不影响主流程，继续使用解析出的信息
                logger.debug(f"元数据增强失败，使用文件名解析结果: {e}")
            
            # 步骤 4: 使用 WorkResolver 查找已存在的作品
            existing_ebook = await self.work_resolver.find_existing_work(
                self.db,
                isbn=enhanced_isbn,
                title=enhanced_title,
                author=enhanced_author,
                series=enhanced_series,
                volume_index=enhanced_volume_index
            )
            
            if existing_ebook:
                # 复用已存在的作品
                ebook = existing_ebook
                logger.info(f"找到已存在的作品，复用 EBook: {ebook.id} - {ebook.title}")
                
                # 对于现有 EBook，如果一些字段为空，而增强提供了新字段，可以补全
                # 注意：这里不再重复调用元数据增强，因为已经在步骤 3 中调用过了
                # 如果需要补全，可以在后续的元数据增强流程中处理
            else:
                # 创建新的作品记录
                ebook = EBook(
                    title=enhanced_title,
                    author=enhanced_author,
                    series=enhanced_series,
                    volume_index=enhanced_volume_index,
                    isbn=enhanced_isbn,  # 如果有增强后的 ISBN，直接设置
                    language="zh-CN",  # 默认中文，后续可以通过元数据识别
                )
                self.db.add(ebook)
                await self.db.flush()  # 获取 ID
                # 确保 ebook.id 已设置
                if not ebook.id:
                    await self.db.refresh(ebook)
                logger.info(f"创建新的作品记录: {ebook.id} - {ebook.title}")
                
                # 注意：元数据增强已经在步骤 3 中完成，这里不需要再次调用
                # 如果需要在创建后再次增强，可以在后续流程中处理
            
            # 步骤 5: 构建目标路径（使用最终确定的 title/author 等信息）
            target_path = self.build_target_path(
                title=ebook.title,  # 使用 EBook 中的最终 title
                author=ebook.author,  # 使用 EBook 中的最终 author
                series=ebook.series,
                volume_index=ebook.volume_index,
                format=file_format,
                ebook=ebook  # 传入 ebook 对象用于分类
            )
            
            # 如果目标文件已存在，生成唯一文件名
            if target_path.exists():
                base_path = target_path.parent / target_path.stem
                counter = 1
                while target_path.exists():
                    target_path = base_path.parent / f"{base_path.name} ({counter}){target_path.suffix}"
                    counter += 1
            
            # 创建目标目录
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 移动文件（在数据库操作之前完成文件操作）
            shutil.move(str(source_path), str(target_path))
            logger.info(f"电子书文件已移动: {source_path} -> {target_path}")
            
            # 步骤 6: 创建电子书文件记录（无论是否复用 EBook，都创建新的 EBookFile）
            ebook_file = EBookFile(
                ebook_id=ebook.id,
                file_path=str(target_path),
                file_size_bytes=file_size_bytes,
                format=file_format,
                source_site_id=source_site_id,
                source_torrent_id=source_torrent_id,
                download_task_id=download_task_id,
            )
            self.db.add(ebook_file)
            
            # 提交事务
            try:
                await self.db.commit()
                logger.info(f"电子书入库成功: {ebook.title} ({ebook_file.format})")
            except Exception as commit_error:
                # 如果提交失败，尝试回滚并恢复文件
                logger.error(f"提交事务失败: {commit_error}")
                await self.db.rollback()
                # 尝试恢复文件（如果可能）
                try:
                    if target_path.exists() and not source_path.exists():
                        shutil.move(str(target_path), str(source_path))
                except Exception as restore_error:
                    logger.warning(f"恢复文件失败: {restore_error}")
                raise
            
            return ebook
            
        except Exception as e:
            logger.error(f"导入电子书失败: {file_path}, 错误: {e}", exc_info=True)
            await self.db.rollback()
            return None
    
    async def import_ebooks_from_directory(
        self,
        directory_path: str,
        source_site_id: Optional[str] = None,
        source_torrent_id: Optional[str] = None,
        download_task_id: Optional[int] = None,
        media_type: Optional[str] = None
    ) -> List[EBook]:
        """
        从目录中批量导入电子书
        
        Args:
            directory_path: 目录路径
            source_site_id: 来源站点 ID
            source_torrent_id: 来源种子 ID
            download_task_id: 下载任务 ID
            media_type: 媒体类型
        
        Returns:
            成功导入的 EBook 列表
        """
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            logger.warning(f"目录不存在或不是目录: {directory_path}")
            return []
        
        imported_books = []
        
        # 递归查找所有电子书文件
        for file_path in directory.rglob("*"):
            if file_path.is_file() and self.is_ebook_file(str(file_path)):
                ebook = await self.import_ebook_from_file(
                    file_path=str(file_path),
                    source_site_id=source_site_id,
                    source_torrent_id=source_torrent_id,
                    download_task_id=download_task_id,
                    media_type=media_type
                )
                if ebook:
                    imported_books.append(ebook)
        
        return imported_books

