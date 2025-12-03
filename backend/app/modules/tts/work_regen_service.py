"""
TTS 重新生成服务

为已有 EBook 重新生成 TTS 有声书（基于原始 TXT 小说源）
"""

from pathlib import Path
from typing import Optional, Literal
from loguru import logger
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.models.ebook import EBook
from app.modules.novel.sources.local_txt import LocalTxtNovelSourceAdapter
from app.modules.novel.models import NovelMetadata
from app.modules.novel.pipeline import NovelToEbookPipeline, TTSSummary
from app.modules.tts.base import TTSEngine
from app.core.config import Settings


class RegenerateTTSResult(BaseModel):
    """TTS 重新生成结果"""
    status: Literal[
        "ok", "tts_disabled", "no_novel_source",
        "unsupported_source_type", "archived_txt_missing",
        "error"
    ]
    created_count: int = 0
    skipped_count: int = 0
    error_message: Optional[str] = None
    tts_summary: Optional[TTSSummary] = None


async def regenerate_tts_for_ebook(
    ebook: EBook,
    db: AsyncSession,
    settings: Settings,
    tts_engine: Optional[TTSEngine],
    audiobook_importer,
    pipeline: NovelToEbookPipeline,
    resume_from_chapter_index: Optional[int] = None
) -> RegenerateTTSResult:
    """
    为指定 EBook 重新生成 TTS 有声书
    
    Args:
        ebook: 电子书对象
        db: 数据库会话
        settings: 应用配置
        tts_engine: TTS 引擎
        audiobook_importer: 有声书导入器
        pipeline: NovelToEbookPipeline 实例（用于复用 _generate_audiobook_from_chapters）
    
    Returns:
        RegenerateTTSResult: 重新生成结果
    """
    # 1. 检查 TTS 是否启用
    if not settings.SMART_TTS_ENABLED:
        return RegenerateTTSResult(
            status="tts_disabled",
            error_message="TTS 当前未启用"
        )
    
    if not tts_engine:
        return RegenerateTTSResult(
            status="tts_disabled",
            error_message="TTS 引擎不可用"
        )
    
    # 2. 检查小说源信息
    if not ebook.extra_metadata:
        return RegenerateTTSResult(
            status="no_novel_source",
            error_message="该作品没有绑定小说 TXT 源"
        )
    
    novel_source = ebook.extra_metadata.get("novel_source")
    if not novel_source:
        return RegenerateTTSResult(
            status="no_novel_source",
            error_message="该作品没有绑定小说 TXT 源"
        )
    
    # 3. 检查源类型
    source_type = novel_source.get("type")
    if source_type != "local_txt":
        return RegenerateTTSResult(
            status="unsupported_source_type",
            error_message=f"不支持的小说源类型: {source_type}"
        )
    
    # 4. 检查归档 TXT 文件是否存在
    archived_txt_path = novel_source.get("archived_txt_path")
    if not archived_txt_path:
        return RegenerateTTSResult(
            status="archived_txt_missing",
            error_message="找不到存档 TXT 文件路径"
        )
    
    txt_file = Path(archived_txt_path)
    if not txt_file.exists():
        return RegenerateTTSResult(
            status="archived_txt_missing",
            error_message=f"找不到存档 TXT 文件: {archived_txt_path}"
        )
    
    # 5. 构造 LocalTxtNovelSourceAdapter
    try:
        # 从 EBook 获取元数据
        metadata = NovelMetadata(
            title=ebook.title,
            author=ebook.author,
            description=ebook.description,
            language=ebook.language or "zh-CN",
            tags=ebook.tags.split(",") if ebook.tags else []
        )
        
        source_adapter = LocalTxtNovelSourceAdapter(
            file_path=txt_file,
            metadata=metadata,
            encoding="utf-8"
        )
        
        # 6. 获取章节列表
        chapters = list(source_adapter.iter_chapters())
        if not chapters:
            return RegenerateTTSResult(
                status="error",
                error_message="无法从 TXT 文件中提取章节"
            )
        
        logger.info(f"从 TXT 文件提取到 {len(chapters)} 个章节，开始重新生成 TTS 有声书")
        
        # 7. 调用 pipeline 的 _generate_audiobook_from_chapters 方法
        # 注意：这里直接调用内部方法，只生成有声书，不重新生成 EPUB
        try:
            start_index = resume_from_chapter_index or 1
            if resume_from_chapter_index:
                logger.info(f"从第 {resume_from_chapter_index} 章继续生成 TTS")
            
            audiobook_files, tts_summary = await pipeline._generate_audiobook_from_chapters(
                ebook=ebook,
                chapters=chapters,
                metadata=metadata,
                settings=settings,
                start_chapter_index=start_index
            )
            
            created_count = len(audiobook_files)
            logger.info(f"TTS 重新生成完成，创建了 {created_count} 个有声书文件")
            
            return RegenerateTTSResult(
                status="ok",
                created_count=created_count,
                skipped_count=0,
                tts_summary=tts_summary
            )
            
        except Exception as e:
            logger.exception(f"TTS 重新生成过程中出错: {e}")
            return RegenerateTTSResult(
                status="error",
                error_message=str(e)
            )
        
    except Exception as e:
        logger.exception(f"重新生成 TTS 失败: {e}")
        return RegenerateTTSResult(
            status="error",
            error_message=str(e)
        )

