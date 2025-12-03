"""
漫画媒体导入器

负责从下载完成的文件中识别漫画，并移动到统一的漫画库目录结构。
"""

import os
import shutil
import re
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.comic import Comic, ComicFile
from app.modules.comic.work_resolver import ComicWorkResolver
from app.modules.media_renamer.category_helper import CategoryHelper
from app.modules.inbox.models import InboxItem


# 支持的漫画文件格式
SUPPORTED_COMIC_FORMATS = {".cbz", ".cbr", ".zip", ".rar"}


class ComicImporter:
    """漫画入库服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.library_root = Path(settings.COMIC_LIBRARY_ROOT)
        self.library_root.mkdir(parents=True, exist_ok=True)
        self.work_resolver = ComicWorkResolver()
        self.category_helper = CategoryHelper()  # 用于二级分类
    
    @staticmethod
    def is_comic_file(file_path: str) -> bool:
        """判断文件是否为支持的漫画格式"""
        path = Path(file_path)
        return path.suffix.lower() in SUPPORTED_COMIC_FORMATS
    
    def parse_filename(self, filename: str) -> Dict[str, Any]:
        """
        解析文件名，提取作品信息
        
        支持的格式：
        - 系列名_v01.cbz / 系列名_01.cbz / 系列名 第01卷.cbz
        - 系列名 - 第01卷 - 标题.cbz
        - 系列名 - 01 - 标题.cbz
        
        Returns:
            包含 series, volume_index, title, author 等信息的字典
        """
        stem = Path(filename).stem
        
        # 尝试匹配 "系列名 - 第XX卷 - 标题" 或 "系列名 - XX - 标题"
        match = re.match(r"^(.+?)\s*[-_]\s*第?(\d+)[卷集话]\s*[-_]\s*(.+)$", stem)
        if match:
            series_part, volume, title_part = match.groups()
            return {
                "series": series_part.strip(),
                "volume_index": int(volume),
                "title": title_part.strip(),
            }
        
        # 尝试匹配 "系列名_v01" 或 "系列名_01"
        match = re.match(r"^(.+?)[_]\s*v?(\d+)$", stem, re.IGNORECASE)
        if match:
            series_part, volume = match.groups()
            return {
                "series": series_part.strip(),
                "volume_index": int(volume),
                "title": None,
            }
        
        # 尝试匹配 "系列名 第XX卷"
        match = re.match(r"^(.+?)\s+第?(\d+)[卷集话]", stem)
        if match:
            series_part, volume = match.groups()
            return {
                "series": series_part.strip(),
                "volume_index": int(volume),
                "title": None,
            }
        
        # 默认：整个文件名作为系列名或标题
        return {
            "series": stem.strip(),
            "title": None,
            "volume_index": None,
        }
    
    def build_target_path(
        self,
        comic: Comic,
        comic_file: Optional[ComicFile] = None
    ) -> Path:
        """
        构建目标文件路径
        
        目录结构：
        - 如果命中分类：Comics/分类名/系列名/卷号 - 标题.ext
        - 如果未命中分类：Comics/系列名/卷号 - 标题.ext（保持原有结构）
        
        Args:
            comic: Comic 对象
            comic_file: ComicFile 对象（可选，用于获取文件格式）
        
        Returns:
            目标文件路径
        """
        # 清理文件名中的非法字符
        def clean_name(name: str) -> str:
            illegal_chars = r'[<>:"/\\|?*]'
            return re.sub(illegal_chars, "_", name).strip()
        
        # 尝试获取分类
        category_subcategory = None
        if comic:
            # 构建分类匹配用的信息字典
            comic_info = {
                "region": comic.region,
                "language": comic.language,
                "extra_metadata": comic.extra_metadata
            }
            category_result = self.category_helper.get_comic_category(comic_info)
            if category_result and hasattr(category_result, 'subcategory') and category_result.subcategory:
                category_subcategory = category_result.subcategory
        
        # 构建基础路径（Comics/）
        base_dir = self.library_root / "Comics"
        
        # 如果命中分类，在 Comics/ 下增加分类目录
        if category_subcategory:
            base_dir = base_dir / category_subcategory
        
        # 确定文件名
        series_clean = clean_name(comic.series) if comic.series else "未知系列"
        title_clean = clean_name(comic.title) if comic.title else (comic.series or "未知标题")
        
        # 确定文件格式
        if comic_file and comic_file.format:
            file_format = comic_file.format
        else:
            # 从 comic 的 extra_metadata 中获取，或使用默认
            file_format = comic.extra_metadata.get("format", "cbz") if comic.extra_metadata else "cbz"
        
        # 构建文件名
        if comic.volume_index is not None:
            filename = f"{comic.volume_index:02d} - {title_clean}.{file_format}"
        else:
            filename = f"{title_clean}.{file_format}"
        
        # 如果有系列，在分类目录下创建系列子目录
        if comic.series:
            target_dir = base_dir / series_clean
        else:
            target_dir = base_dir
        
        return target_dir / filename
    
    async def import_comic_from_path(
        self,
        file_path: Path,
        hints: Optional[InboxItem] = None,
    ) -> Optional[Path]:
        """
        从文件路径导入漫画
        
        Args:
            file_path: 源文件路径（Path 对象）
            hints: InboxItem 对象，包含 PT 相关信息
        
        Returns:
            成功时返回新路径，失败时返回 None
        """
        # 检查文件是否存在
        source_path = Path(file_path)
        if not source_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return None
        
        # 检查文件格式
        if not self.is_comic_file(str(file_path)):
            logger.debug(f"文件 {file_path} 不是支持的漫画格式")
            return None
        
        try:
            # 步骤 1: 解析文件名，获取基础元信息
            file_info = self.parse_filename(source_path.name)
            parsed_title = file_info.get("title") or source_path.stem
            parsed_series = file_info.get("series")
            parsed_volume_index = file_info.get("volume_index")
            
            # 从 hints 中提取更多信息
            extra_metadata = {}
            if hints:
                if hints.source_category:
                    extra_metadata["category"] = hints.source_category
                if hints.source_tags:
                    extra_metadata["tags"] = hints.source_tags
                # 可以从 source_category 推断 region（如果可能）
                # 例如：如果 category 包含 "日漫"、"JP" 等，可以设置 region="JP"
                if hints.extra_metadata:
                    extra_metadata.update(hints.extra_metadata)
                
                # 从 hints 的 extra_metadata 中提取更多信息
                if hints.extra_metadata:
                    parsed_title = hints.extra_metadata.get("title") or parsed_title
                    parsed_series = hints.extra_metadata.get("series") or parsed_series
                    parsed_volume_index = hints.extra_metadata.get("volume_index") or parsed_volume_index
                    if isinstance(parsed_volume_index, str):
                        try:
                            parsed_volume_index = int(parsed_volume_index)
                        except:
                            parsed_volume_index = None
            
            # 获取文件大小和格式
            file_size_bytes = source_path.stat().st_size
            file_format = source_path.suffix[1:].lower()  # 去掉点号
            
            # 步骤 2: 使用 WorkResolver 查找已存在的作品
            existing_comic = await self.work_resolver.find_existing_work(
                self.db,
                title=parsed_title,
                author=None,  # 文件名解析通常不包含作者
                series=parsed_series,
                volume_index=parsed_volume_index
            )
            
            if existing_comic:
                # 复用已存在的作品
                comic = existing_comic
                logger.info(f"找到已存在的作品，复用 Comic: {comic.id} - {comic.title}")
            else:
                # 创建新的作品记录
                # 从 hints 和 extra_metadata 中提取 region 和 language
                region = None
                language = "zh-CN"  # 默认中文
                if hints and hints.extra_metadata:
                    region = hints.extra_metadata.get("region")
                    language = hints.extra_metadata.get("language") or language
                if extra_metadata:
                    region = extra_metadata.get("region") or region
                    language = extra_metadata.get("language") or language
                
                comic = Comic(
                    title=parsed_title,
                    series=parsed_series,
                    volume_index=parsed_volume_index,
                    language=language,
                    region=region,
                    extra_metadata=extra_metadata or {}
                )
                self.db.add(comic)
                await self.db.flush()  # 获取 ID
                # 确保 comic.id 已设置
                if not comic.id:
                    await self.db.refresh(comic)
                logger.info(f"创建新的作品记录: {comic.id} - {comic.title}")
            
            # 步骤 3: 构建目标路径
            # 先创建临时 comic_file 用于传递格式信息
            temp_comic_file = ComicFile(
                comic_id=comic.id,
                file_path="",  # 临时，稍后更新
                format=file_format,
                file_size_bytes=file_size_bytes
            )
            target_path = self.build_target_path(comic, temp_comic_file)
            
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
            logger.info(f"漫画文件已移动: {source_path} -> {target_path}")
            
            # 步骤 4: 创建漫画文件记录
            comic_file = ComicFile(
                comic_id=comic.id,
                file_path=str(target_path),
                file_size_bytes=file_size_bytes,
                format=file_format,
                source_site_id=hints.source_site_id if hints else None,
                source_torrent_id=None,  # InboxItem 中没有 source_torrent_id 字段
                download_task_id=hints.download_task_id if hints else None,
            )
            self.db.add(comic_file)
            await self.db.commit()
            
            logger.info(f"漫画导入成功: {comic.title} -> {target_path}")
            return target_path
            
        except Exception as e:
            logger.error(f"导入漫画失败: {file_path}, 错误: {e}", exc_info=True)
            await self.db.rollback()
            return None
