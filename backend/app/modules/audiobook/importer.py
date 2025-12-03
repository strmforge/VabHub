"""
有声书入库服务

负责从下载完成的文件中识别有声书，并移动到统一的有声书库目录结构。
"""

import os
import shutil
import re
from pathlib import Path
from typing import Optional, Dict, Any, Mapping
from datetime import datetime
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ebook import EBook
from app.models.audiobook import AudiobookFile
from app.modules.ebook.work_resolver import EBookWorkResolver
from app.modules.audiobook.media_info import probe_audio_file
from app.constants.media_types import MEDIA_TYPE_AUDIOBOOK, normalize_media_type
from app.modules.media_renamer.category_helper import CategoryHelper


# 支持的有声书文件格式
SUPPORTED_AUDIOBOOK_FORMATS = {".mp3", ".m4b", ".m4a", ".flac", ".ogg", ".opus", ".aac", ".wav"}


class AudiobookImporter:
    """有声书入库服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.library_root = Path(settings.EBOOK_LIBRARY_ROOT)  # 使用与电子书相同的库根目录
        self.library_root.mkdir(parents=True, exist_ok=True)
        self.work_resolver = EBookWorkResolver()
        self.category_helper = CategoryHelper()  # 用于二级分类
    
    def is_audiobook_file(self, file_path: str) -> bool:
        """判断文件是否为有声书格式"""
        path = Path(file_path)
        return path.suffix.lower() in SUPPORTED_AUDIOBOOK_FORMATS
    
    def parse_filename(self, filename: str) -> Dict[str, Any]:
        """
        从文件名解析书名、作者、朗读者等信息
        
        支持的格式示例：
        - "作者 - 书名 - 朗读者.mp3"
        - "书名 - 作者 - 朗读者.m4b"
        - "系列名 第1卷 - 书名 - 朗读者.mp3"
        - "书名 (作者) - 朗读者.mp3"
        """
        path = Path(filename)
        stem = path.stem  # 不含扩展名的文件名
        
        # 尝试匹配 "作者 - 书名 - 朗读者" 或 "书名 - 作者 - 朗读者" 格式
        # 先尝试匹配包含三个部分的格式
        match = re.match(r"^(.+?)\s*-\s*(.+?)\s*-\s*(.+)$", stem)
        if match:
            part1, part2, part3 = match.groups()
            # 判断哪个是作者（通常作者较短）
            if len(part1) < 30 and not re.search(r"[第卷集]", part1):
                return {
                    "author": part1.strip(),
                    "title": part2.strip(),
                    "narrator": part3.strip(),
                }
            else:
                return {
                    "title": part1.strip(),
                    "author": part2.strip(),
                    "narrator": part3.strip(),
                }
        
        # 尝试匹配 "作者 - 书名" 或 "书名 - 作者" 格式（无朗读者）
        match = re.match(r"^(.+?)\s*-\s*(.+)$", stem)
        if match:
            author_part, title_part = match.groups()
            # 判断哪个是作者
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
            "narrator": None,
        }
    
    def build_target_path(
        self,
        title: str,
        author: Optional[str] = None,
        series: Optional[str] = None,
        volume_index: Optional[str] = None,
        narrator: Optional[str] = None,
        format: str = "mp3",
        ebook: Optional[EBook] = None,
        audiobook_file: Optional[AudiobookFile] = None
    ) -> Path:
        """
        构建目标文件路径
        
        目录结构：
        - 如果命中分类：Audiobooks/分类名/作者/系列名/卷号 - 书名 - 朗读者.扩展名
        - 如果未命中分类：Audiobooks/作者/系列名/卷号 - 书名 - 朗读者.扩展名（保持原有结构）
        
        Args:
            title: 书名
            author: 作者
            series: 系列名
            volume_index: 卷号
            narrator: 朗读者
            format: 文件格式
            ebook: EBook 对象（可选，用于获取 tags/language 等信息进行分类）
            audiobook_file: AudiobookFile 对象（可选，用于获取额外信息）
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
            audiobook_info = {
                "tags": ebook.tags,
                "language": ebook.language or audiobook_file.language if audiobook_file else None,
                "extra_metadata": ebook.extra_metadata
            }
            # 如果有 audiobook_file，可以从其 extra_metadata 中补充信息
            if audiobook_file and audiobook_file.extra_metadata:
                if not audiobook_info.get("extra_metadata"):
                    audiobook_info["extra_metadata"] = {}
                audiobook_info["extra_metadata"].update(audiobook_file.extra_metadata or {})
            
            category_result = self.category_helper.get_audiobook_category(audiobook_info)
        
        author_clean = clean_name(author) if author else "未知作者"
        title_clean = clean_name(title)
        narrator_clean = clean_name(narrator) if narrator else ""
        
        # 构建基础路径（Audiobooks/）
        base_dir = self.library_root / "Audiobooks"
        
        # 如果命中分类，在 Audiobooks/ 下增加分类目录
        if category_result and category_result.subcategory:
            base_dir = base_dir / category_result.subcategory
        
        if series:
            series_clean = clean_name(series)
            if volume_index:
                # Audiobooks/[分类/]作者/系列名/卷号 - 书名 - 朗读者.mp3
                target_dir = base_dir / author_clean / series_clean
                if narrator_clean:
                    filename = f"{volume_index} - {title_clean} - {narrator_clean}.{format}"
                else:
                    filename = f"{volume_index} - {title_clean}.{format}"
            else:
                # Audiobooks/[分类/]作者/系列名/书名 - 朗读者.mp3
                target_dir = base_dir / author_clean / series_clean
                if narrator_clean:
                    filename = f"{title_clean} - {narrator_clean}.{format}"
                else:
                    filename = f"{title_clean}.{format}"
        else:
            # Audiobooks/[分类/]作者/书名 - 朗读者.mp3
            target_dir = base_dir / author_clean
            if narrator_clean:
                filename = f"{title_clean} - {narrator_clean}.{format}"
            else:
                filename = f"{title_clean}.{format}"
        
        return target_dir / filename
    
    async def import_audiobook_from_file(
        self,
        file_path: str,
        source_site_id: Optional[str] = None,
        source_torrent_id: Optional[str] = None,
        download_task_id: Optional[int] = None,
        media_type: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        bitrate_kbps: Optional[int] = None,
        channels: Optional[int] = None,
        sample_rate_hz: Optional[int] = None,
        ebook: Optional[EBook] = None,
        hints: Optional[Dict[str, Any]] = None
    ) -> Optional[AudiobookFile]:
        """
        从文件路径导入有声书
        
        Args:
            file_path: 源文件路径
            source_site_id: 来源站点 ID
            source_torrent_id: 来源种子 ID
            download_task_id: 下载任务 ID
            media_type: 媒体类型（如果为 audiobook 则处理）
            duration_seconds: 时长（秒，可选，未来可通过音频解析获取）
            bitrate_kbps: 比特率（kbps，可选）
            channels: 声道数（可选）
            sample_rate_hz: 采样率（Hz，可选）
        
        Returns:
            创建的 AudiobookFile 对象，如果失败返回 None
        """
        # 检查媒体类型
        if media_type:
            normalized_type = normalize_media_type(media_type)
            if normalized_type != MEDIA_TYPE_AUDIOBOOK:
                logger.debug(f"文件 {file_path} 的媒体类型为 {normalized_type}，不是有声书，跳过")
                return None
        
        # 检查文件是否存在
        source_path = Path(file_path)
        if not source_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return None
        
        # 检查文件格式
        if not self.is_audiobook_file(file_path):
            logger.debug(f"文件 {file_path} 不是支持的有声书格式")
            return None
        
        try:
            # 步骤 1: 解析文件名，获取基础元信息
            file_info = self.parse_filename(source_path.name)
            parsed_title = file_info.get("title") or source_path.stem
            parsed_author = file_info.get("author")
            parsed_series = file_info.get("series")
            parsed_volume_index = file_info.get("volume_index")
            parsed_narrator = file_info.get("narrator")
            
            # 获取文件大小和格式
            file_size_bytes = source_path.stat().st_size
            file_format = source_path.suffix[1:].lower()  # 去掉点号
            
            # 步骤 2: 使用 WorkResolver 查找/创建 EBook（作品）
            # 如果 hints 中提供了 ebook，直接使用；否则查找/创建
            if ebook:
                # 使用传入的 ebook
                logger.info(f"使用传入的 EBook: {ebook.id} - {ebook.title}")
            else:
                # 注意：有声书和电子书共享同一个作品（EBook），通过 ebook_id 关联
                existing_ebook = await self.work_resolver.find_existing_work(
                    self.db,
                    isbn=None,  # 有声书通常没有 ISBN
                    title=parsed_title,
                    author=parsed_author,
                    series=parsed_series,
                    volume_index=parsed_volume_index
                )
                
                if existing_ebook:
                    # 复用已存在的作品
                    ebook = existing_ebook
                    logger.info(f"找到已存在的作品，复用 EBook: {ebook.id} - {ebook.title}")
                else:
                    # 创建新的作品记录
                    ebook = EBook(
                        title=parsed_title,
                        author=parsed_author,
                        series=parsed_series,
                        volume_index=parsed_volume_index,
                        language="zh-CN",  # 默认中文，后续可以通过元数据识别
                    )
                    self.db.add(ebook)
                    await self.db.flush()  # 获取 ID
                    # 确保 ebook.id 已设置
                    if not ebook.id:
                        await self.db.refresh(ebook)
                    logger.info(f"创建新的作品记录: {ebook.id} - {ebook.title}")
            
            # 步骤 3: 构建目标路径（使用最终确定的 title/author 等信息）
            # 注意：此时 audiobook_file 还未创建，所以传入 None
            target_path = self.build_target_path(
                title=ebook.title,  # 使用 EBook 中的最终 title
                author=ebook.author,  # 使用 EBook 中的最终 author
                series=ebook.series,
                volume_index=ebook.volume_index,
                narrator=parsed_narrator,
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
            
            # 移动文件
            shutil.move(str(source_path), str(target_path))
            logger.info(f"有声书文件已移动: {source_path} -> {target_path}")
            
            # 步骤 4: 解析音频元数据（从文件本身读取）
            audio_meta = probe_audio_file(target_path)
            
            # 优先使用解析出的元数据，如果解析失败则使用传入的参数（如果有）
            final_duration = audio_meta.duration_seconds if audio_meta.duration_seconds is not None else duration_seconds
            final_bitrate = audio_meta.bitrate_kbps if audio_meta.bitrate_kbps is not None else bitrate_kbps
            final_channels = audio_meta.channels if audio_meta.channels is not None else channels
            final_sample_rate = audio_meta.sample_rate_hz if audio_meta.sample_rate_hz is not None else sample_rate_hz
            
            # 步骤 5: 从 hints 中提取 TTS 信息
            is_tts_generated = False
            tts_provider = None
            if hints:
                is_tts_generated = bool(hints.get("tts_generated", False))
                if is_tts_generated:
                    tts_provider = hints.get("tts_provider")
            
            # 步骤 6: 创建有声书文件记录
            audiobook_file = AudiobookFile(
                ebook_id=ebook.id,
                file_path=str(target_path),
                file_size_bytes=file_size_bytes,
                format=file_format,
                duration_seconds=final_duration,
                bitrate_kbps=final_bitrate,
                channels=final_channels,
                sample_rate_hz=final_sample_rate,
                narrator=parsed_narrator,
                language=ebook.language,  # 使用作品的语言
                source_site_id=source_site_id,
                source_torrent_id=source_torrent_id,
                download_task_id=download_task_id,
                is_tts_generated=is_tts_generated,
                tts_provider=tts_provider if is_tts_generated else None,
            )
            self.db.add(audiobook_file)
            
            # 提交事务
            await self.db.commit()
            logger.info(f"有声书入库成功: {ebook.title} ({audiobook_file.format})")
            
            # 创建AUDIOBOOK_READY通知（不影响主流程）
            try:
                from app.services.notification_service import notify_audiobook_ready
                
                # 确定来源类型
                source_type = "import"
                if download_task_id:
                    source_type = "download"
                elif is_tts_generated:
                    source_type = "tts"
                
                # 创建通知（默认使用用户ID 1，实际项目中应该根据具体情况设置）
                await notify_audiobook_ready(
                    session=self.db,
                    user_id=1,  # 默认管理员用户，实际项目中应该根据具体情况设置
                    audiobook_id=audiobook_file.id,
                    audiobook_title=ebook.title,
                    source_type=source_type
                )
                
                logger.info(f"Created AUDIOBOOK_READY notification for audiobook {audiobook_file.id}")
                
            except Exception as notify_err:
                logger.warning(f"Failed to create AUDIOBOOK_READY notification for audiobook {audiobook_file.id}: {notify_err}", exc_info=True)
                # 不影响主流程，继续执行
            
            return audiobook_file
            
        except Exception as e:
            logger.error(f"导入有声书失败: {file_path}, 错误: {e}", exc_info=True)
            await self.db.rollback()
            return None

