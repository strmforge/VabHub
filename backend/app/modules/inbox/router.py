"""
统一待整理收件箱路由器

根据媒体类型检测结果，将文件路由到对应的 Importer。
"""

from pathlib import Path
from typing import Optional, List
from loguru import logger
import re
import shutil
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.inbox.models import InboxItem
from app.modules.inbox.media_detection.base import MediaTypeGuess
from app.modules.ebook.importer import EBookImporter
from app.modules.audiobook.importer import AudiobookImporter
from app.modules.novel.pipeline import NovelToEbookPipeline
from app.modules.novel.sources.local_txt import LocalTxtNovelSourceAdapter
from app.modules.novel.models import NovelMetadata
from app.modules.novel.epub_builder import EpubBuilder
from app.modules.tts.factory import get_tts_engine
from app.modules.tts.job_service import create_job_for_ebook
from app.modules.video.importer import VideoImporter
from app.modules.comic.importer import ComicImporter
from app.modules.music.importer import MusicImporter
from app.models.novel_inbox_import_log import NovelInboxImportLog, NovelInboxStatus
from sqlalchemy import select
from app.constants.media_types import (
    MEDIA_TYPE_MOVIE,
    MEDIA_TYPE_TV,
    MEDIA_TYPE_ANIME,
    MEDIA_TYPE_SHORT_DRAMA,
    MEDIA_TYPE_MUSIC
)


class InboxRouter:
    """
    统一待整理收件箱路由器
    
    根据媒体类型检测结果，将文件分发到对应的 Importer。
    """
    
    def __init__(
        self,
        db: AsyncSession,
        ebook_importer: Optional[EBookImporter] = None,
        audiobook_importer: Optional[AudiobookImporter] = None,
        novel_pipeline: Optional[NovelToEbookPipeline] = None,
        video_importer: Optional[VideoImporter] = None,
        comic_importer: Optional[ComicImporter] = None,
        music_importer: Optional[MusicImporter] = None
    ):
        """
        初始化路由器
        
        Args:
            db: 数据库会话
            ebook_importer: 电子书导入器
            audiobook_importer: 有声书导入器
            novel_pipeline: 小说流水线
            video_importer: 视频导入器（可选，根据项目实际情况）
        """
        self.db = db
        self.ebook_importer = ebook_importer or EBookImporter(db)
        self.audiobook_importer = audiobook_importer or AudiobookImporter(db)
        
        # 创建小说流水线（如果需要）
        if novel_pipeline is None:
            epub_builder = EpubBuilder()
            # 如果 TTS 启用，创建 TTS 引擎和有声书导入器
            tts_engine = get_tts_engine(settings) if settings.SMART_TTS_ENABLED else None
            audiobook_importer_for_tts = AudiobookImporter(db) if settings.SMART_TTS_ENABLED else None
            self.novel_pipeline = NovelToEbookPipeline(
                db=db,
                ebook_importer=self.ebook_importer,
                epub_builder=epub_builder,
                tts_engine=tts_engine,
                audiobook_importer=audiobook_importer_for_tts,
                settings=settings
            )
        else:
            self.novel_pipeline = novel_pipeline
        
        # 创建视频导入器（如果需要）
        self.video_importer = video_importer or VideoImporter(db)
        
        # 创建漫画导入器（如果需要）
        self.comic_importer = comic_importer or ComicImporter(db)
        
        # 创建音乐导入器（如果需要）
        self.music_importer = music_importer or MusicImporter(db)
    
    @staticmethod
    def _clean_title_for_display(title: str) -> str:
        """
        清洗标题用于显示（移除常见标记）
        
        Args:
            title: 原始标题
        
        Returns:
            清洗后的标题
        """
        if not title:
            return ""
        
        cleaned = title.strip()
        
        # 移除常见的后缀标记
        common_suffixes = [
            r'\s*\[精校[^\]]*\]',
            r'\s*\[全本[^\]]*\]',
            r'\s*\[完本[^\]]*\]',
            r'\s*\[EPUB[^\]]*\]',
            r'\s*\[完整版[^\]]*\]',
            r'\s*\[校对[^\]]*\]',
            r'\s*\(精校[^\)]*\)',
            r'\s*\(全本[^\)]*\)',
            r'\s*\(完本[^\)]*\)',
            r'\s*\(EPUB[^\)]*\)',
            r'\s*\(完整版[^\)]*\)',
        ]
        
        for pattern in common_suffixes:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    
    @staticmethod
    def _create_safe_filename(original_filename: str) -> str:
        """
        生成安全的文件名（去除特殊字符，避免路径注入）
        
        Args:
            original_filename: 原始文件名
        
        Returns:
            str: 安全的文件名
        """
        # 提取文件名（不含路径）
        filename = Path(original_filename).name
        
        # 清理文件名：只保留字母、数字、中文、下划线、连字符
        safe_stem = re.sub(r'[^\w\u4e00-\u9fa5-]', '_', Path(filename).stem)
        
        # 如果清理后为空，使用时间戳 + UUID
        if not safe_stem:
            safe_stem = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # 保持原扩展名
        suffix = Path(filename).suffix
        return f"{safe_stem}{suffix}"
    
    async def _handle_novel_txt(self, item: InboxItem, generate_tts_job: bool = False) -> str:
        """
        处理小说 TXT 文件
        
        Args:
            item: InboxItem 对象
            generate_tts_job: 是否自动创建 TTS Job
        
        Returns:
            str: 处理结果字符串
        """
        # 1. 检查文件存在
        source_path = Path(item.path)
        if not source_path.exists():
            logger.warning(f"文件不存在: {item.path}")
            return "failed:novel_txt_file_not_found"
        
        if not source_path.is_file():
            logger.warning(f"路径不是文件: {item.path}")
            return "failed:novel_txt_invalid_path"
        
        # 1.5. 检查是否已导入（防重复）
        original_path_str = str(source_path.resolve())  # 使用绝对路径
        existing_log_stmt = select(NovelInboxImportLog).where(
            NovelInboxImportLog.original_path == original_path_str
        )
        existing_log_result = await self.db.execute(existing_log_stmt)
        existing_log = existing_log_result.scalar_one_or_none()
        
        if existing_log:
            if existing_log.status == NovelInboxStatus.SUCCESS:
                logger.info(f"文件已导入过，跳过: {item.path} (EBook ID: {existing_log.ebook_id})")
                return "skipped:already_imported"
            elif existing_log.status == NovelInboxStatus.FAILED:
                logger.info(f"文件之前导入失败，跳过: {item.path} (原因: {existing_log.reason})")
                return "skipped:failed_before"
            # 如果是 pending，继续处理（可能是上次中断）
        
        # 获取文件信息
        stat = source_path.stat()
        file_size = stat.st_size
        file_mtime = datetime.fromtimestamp(stat.st_mtime)
        
        # 创建或更新日志记录
        if existing_log:
            import_log = existing_log
            import_log.status = NovelInboxStatus.PENDING
            import_log.reason = None
            import_log.error_message = None
        else:
            import_log = NovelInboxImportLog(
                original_path=original_path_str,
                status=NovelInboxStatus.PENDING,
                file_size=file_size,
                file_mtime=file_mtime
            )
            self.db.add(import_log)
        
        await self.db.flush()
        
        # 2. 构造 NovelMetadata
        # 从文件名提取标题并清洗
        raw_title = source_path.stem
        cleaned_title = self._clean_title_for_display(raw_title)
        if not cleaned_title:
            cleaned_title = raw_title  # 如果清洗后为空，使用原始文件名
        
        # 构造 tags
        tags: List[str] = ["from_inbox_novel_txt"]
        if item.source_tags:
            if isinstance(item.source_tags, list):
                tags.extend(item.source_tags)
            elif isinstance(item.source_tags, str):
                # 如果是逗号分隔的字符串，分割后添加
                tag_list = [t.strip() for t in item.source_tags.split(',') if t.strip()]
                tags.extend(tag_list)
        
        metadata = NovelMetadata(
            title=cleaned_title,
            author=None,  # 暂时留空，未来可以从文件名或 PT 信息中提取
            description="Imported from INBOX",
            language="zh-CN",
            tags=tags
        )
        
        # 3. 创建 LocalTxtNovelSourceAdapter
        source = LocalTxtNovelSourceAdapter(
            file_path=source_path,
            metadata=metadata,
            encoding="utf-8"
        )
        
        # 4. 确定输出目录
        output_dir = Path(settings.EBOOK_LIBRARY_ROOT) / "novel_output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 5. 预先确定归档路径（在流水线执行前）
        archive_dir = Path(settings.NOVEL_UPLOAD_ROOT) / "source_txt"
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成安全的文件名
        safe_filename = self._create_safe_filename(source_path.name)
        archive_path = archive_dir / safe_filename
        
        # 如果目标文件已存在，添加时间戳后缀
        if archive_path.exists():
            stem = archive_path.stem
            suffix = archive_path.suffix
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_path = archive_dir / f"{stem}_{timestamp}{suffix}"
        
        # 6. 执行流水线（不在这里生成 TTS 有声书，只导入 EBook）
        # 先设置归档路径，以便 pipeline 可以保存到 extra_metadata
        self.novel_pipeline._archived_txt_path = archive_path
        
        # 注意：这里不生成有声书，只导入 EBook
        # 如果需要 TTS，通过 generate_tts_job 参数创建 Job，由 Runner 异步处理
        generate_audiobook = False
        result = await self.novel_pipeline.run(
            source=source,
            output_dir=output_dir,
            generate_audiobook=generate_audiobook
        )
        
        if not result or not result.ebook:
            logger.warning(f"小说 TXT 导入失败: {item.path}")
            import_log.status = NovelInboxStatus.FAILED
            import_log.reason = "import_failed"
            import_log.error_message = "Pipeline 返回的 ebook 为空"
            await self.db.commit()
            return "failed:novel_txt_import_failed"
        
        # 更新日志记录
        import_log.ebook_id = result.ebook.id
        import_log.status = NovelInboxStatus.SUCCESS
        import_log.file_size = file_size
        import_log.file_mtime = file_mtime
        await self.db.flush()
        
        # 7. 可选：创建 TTS Job
        tts_job_created = False
        if generate_tts_job and settings.SMART_TTS_ENABLED:
            try:
                job = await create_job_for_ebook(
                    db=self.db,
                    ebook_id=result.ebook.id,
                    created_by="novel-inbox",
                    strategy=None  # 使用默认策略
                )
                await self.db.flush()
                logger.info(f"为 EBook {result.ebook.id} 创建了 TTS Job {job.id}")
                tts_job_created = True
            except Exception as e:
                logger.warning(f"创建 TTS Job 失败: {e}", exc_info=True)
                # 不影响导入结果
        
        # 8. 成功后将 TXT 移动到归档目录
        try:
            # 移动文件
            shutil.move(str(source_path), str(archive_path))
            logger.info(f"小说 TXT 文件已归档: {source_path} -> {archive_path}")
            
            await self.db.commit()
            logger.info(f"小说 TXT 导入成功: {item.path} -> EBook {result.ebook.id}" + 
                       (f", TTS Job 已创建" if tts_job_created else ""))
            return "handled:novel_txt" + (":tts_job_created" if tts_job_created else "")
            
        except Exception as e:
            # 归档失败不影响导入结果，但记录警告
            logger.warning(f"小说 TXT 文件归档失败: {item.path}, 错误: {e}")
            await self.db.commit()
            # 仍然返回成功，因为 EBook 已经入库
            return "handled:novel_txt" + (":tts_job_created" if tts_job_created else "")
    
    async def route(self, item: InboxItem, guess: MediaTypeGuess) -> str:
        """
        根据媒体类型检测结果，路由到对应的 Importer
        
        Args:
            item: 待处理的项目
            guess: 媒体类型检测结果
        
        Returns:
            str: 处理结果字符串，例如：
                - "handled:ebook"
                - "handled:novel_txt"
                - "skipped:unknown"
                - "skipped:disabled"
                - "skipped:unsupported_movie"
        """
        media_type = guess.media_type
        
        # 未识别或未知类型
        if media_type == "unknown":
            logger.debug(f"跳过未知类型文件: {item.path}")
            return "skipped:unknown"
        
        try:
            # 电子书：epub/mobi/azw3/pdf
            if media_type == "ebook":
                if not settings.INBOX_ENABLE_EBOOK:
                    logger.debug(f"电子书处理已禁用，跳过: {item.path}")
                    return "skipped:ebook_disabled"
                
                result = await self.ebook_importer.import_ebook_from_file(
                    file_path=str(item.path),
                    media_type="ebook"
                )
                
                if result:
                    logger.info(f"电子书导入成功: {item.path}")
                    return "handled:ebook"
                else:
                    logger.warning(f"电子书导入失败: {item.path}")
                    return "failed:ebook"
            
            # 有声书：mp3/flac/m4b 等
            elif media_type == "audiobook":
                if not settings.INBOX_ENABLE_AUDIOBOOK:
                    logger.debug(f"有声书处理已禁用，跳过: {item.path}")
                    return "skipped:audiobook_disabled"
                
                result = await self.audiobook_importer.import_audiobook_from_file(
                    file_path=str(item.path),
                    media_type="audiobook"
                )
                
                if result:
                    logger.info(f"有声书导入成功: {item.path}")
                    return "handled:audiobook"
                else:
                    logger.warning(f"有声书导入失败: {item.path}")
                    return "failed:audiobook"
            
            # 小说 txt：走 NovelToEbookPipeline
            elif media_type == "novel_txt":
                if not settings.INBOX_ENABLE_NOVEL_TXT:
                    logger.debug(f"小说 TXT 处理已禁用，跳过: {item.path}")
                    return "skipped:novel_txt_disabled"
                
                try:
                    result = await self._handle_novel_txt(item)
                    return result
                except Exception as e:
                    logger.error(f"小说 TXT 导入异常: {item.path}, 错误: {e}", exc_info=True)
                    return "failed:novel_txt_import_error"
            
            # 视频类：movie/tv/anime/short_drama
            elif media_type in (MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV, MEDIA_TYPE_ANIME, MEDIA_TYPE_SHORT_DRAMA):
                if not settings.INBOX_ENABLE_VIDEO:
                    logger.debug(f"视频处理已禁用，跳过: {item.path}")
                    return "skipped:video_disabled"
                
                try:
                    # 调用视频导入器
                    new_path = await self.video_importer.import_video_from_path(
                        file_path=item.path,
                        media_type=media_type,
                        download_task_id=item.download_task_id,
                        source_site_id=item.source_site_id,
                        extra_metadata={
                            "source_site_name": item.source_site_name,
                            "source_category": item.source_category,
                            "source_tags": item.source_tags
                        } if item.source_site_name or item.source_category or item.source_tags else None
                    )
                    
                    if new_path:
                        logger.info(f"视频导入成功: {item.path} -> {new_path}")
                        return f"handled:video:{media_type}"
                    else:
                        logger.warning(f"视频导入失败: {item.path}")
                        return f"failed:video:{media_type}"
                        
                except Exception as e:
                    logger.error(f"视频导入异常: {item.path}, 错误: {e}", exc_info=True)
                    return f"error:video:{media_type}"
            
            # 漫画：comic
            elif media_type == "comic":
                if not settings.INBOX_ENABLE_COMIC:
                    logger.debug(f"漫画处理已禁用，跳过: {item.path}")
                    return "skipped:comic_disabled"
                
                if self.comic_importer:
                    try:
                        new_path = await self.comic_importer.import_comic_from_path(
                            file_path=item.path,
                            hints=item,  # 传入整个 InboxItem 作为 hints
                        )
                        
                        if new_path:
                            logger.info(f"漫画导入成功: {item.path} -> {new_path}")
                            return "handled:comic"
                        else:
                            logger.warning(f"漫画导入失败: {item.path}")
                            return "failed:comic_import_error"
                    except Exception as e:
                        logger.error(f"漫画导入异常: {item.path}, 错误: {e}", exc_info=True)
                        return "failed:comic_import_error"
                else:
                    logger.warning(f"漫画导入器未配置，跳过: {item.path}")
                    return "skipped:comic_not_implemented"
            
            # 音乐：music
            elif media_type == MEDIA_TYPE_MUSIC:
                if not settings.INBOX_ENABLE_MUSIC:
                    logger.debug(f"音乐处理已禁用，跳过: {item.path}")
                    return "skipped:music_disabled"
                
                if self.music_importer:
                    try:
                        # 构建 hints 字典
                        hints = {}
                        if item.download_task_id:
                            hints["download_task_id"] = item.download_task_id
                        if item.source_site_id:
                            hints["source_site_id"] = item.source_site_id
                        if item.source_site_name:
                            hints["source_site_name"] = item.source_site_name
                        if item.source_category:
                            hints["source_category"] = item.source_category
                        if item.source_tags:
                            hints["source_tags"] = item.source_tags
                        
                        new_path = await self.music_importer.import_music_from_path(
                            file_path=item.path,
                            hints=hints if hints else None
                        )
                        
                        if new_path:
                            logger.info(f"音乐导入成功: {item.path} -> {new_path}")
                            return "handled:music"
                        else:
                            logger.warning(f"音乐导入失败: {item.path}")
                            return "failed:music_import_failed"
                            
                    except Exception as e:
                        logger.error(f"音乐导入异常: {item.path}, 错误: {e}", exc_info=True)
                        return "failed:music_import_error"
                else:
                    logger.warning(f"音乐导入器未配置，跳过: {item.path}")
                    return "skipped:music_not_implemented"
            
            # 其他暂未实现的类型
            else:
                logger.debug(f"暂不支持的类型 {media_type}，跳过: {item.path}")
                return f"skipped:unsupported_{media_type}"
        
        except Exception as e:
            logger.error(f"路由处理失败: {item.path}, 媒体类型: {media_type}, 错误: {e}", exc_info=True)
            return f"error:{media_type}"

