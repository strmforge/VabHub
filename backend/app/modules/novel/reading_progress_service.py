"""
小说阅读进度聚合服务

提供批量查询和计算阅读进度的功能，供小说中心和有声书中心复用
"""
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.user_novel_reading_progress import UserNovelReadingProgress
from app.models.ebook import EBook
from app.modules.novel.reader_service import get_chapters_from_ebook


async def get_reading_progress_map(
    db: AsyncSession,
    user_id: int,
    ebook_ids: List[int]
) -> Dict[int, UserNovelReadingProgress]:
    """
    批量查询阅读进度
    
    Returns:
        Dict[ebook_id, UserNovelReadingProgress]
    """
    if not ebook_ids:
        return {}
    
    try:
        stmt = (
            select(UserNovelReadingProgress)
            .where(
                UserNovelReadingProgress.user_id == user_id,
                UserNovelReadingProgress.ebook_id.in_(ebook_ids)
            )
        )
        result = await db.execute(stmt)
        progress_records = result.scalars().all()
        
        return {p.ebook_id: p for p in progress_records}
    except Exception as e:
        logger.error(f"批量查询阅读进度失败 (user_id={user_id}): {e}", exc_info=True)
        return {}


async def get_chapters_map(
    db: AsyncSession,
    ebooks: List[EBook]
) -> Dict[int, List]:
    """
    批量获取章节列表（缓存）
    
    Returns:
        Dict[ebook_id, List[StandardChapter]]
    """
    chapters_map = {}
    
    for ebook in ebooks:
        try:
            chapters = await get_chapters_from_ebook(ebook)
            chapters_map[ebook.id] = chapters
        except Exception as e:
            logger.warning(f"获取章节列表失败 (ebook_id={ebook.id}): {e}")
            chapters_map[ebook.id] = []
    
    return chapters_map


def calculate_reading_progress(
    progress: Optional[UserNovelReadingProgress],
    chapters: List,
    ebook_id: int
) -> Dict:
    """
    计算阅读进度信息
    
    Returns:
        {
            "has_progress": bool,
            "is_finished": bool,
            "progress_percent": float,
            "current_chapter_index": Optional[int],
            "current_chapter_title": Optional[str],
            "last_read_at": Optional[datetime]
        }
    """
    if not progress:
        return {
            "has_progress": False,
            "is_finished": False,
            "progress_percent": 0.0,
            "current_chapter_index": None,
            "current_chapter_title": None,
            "last_read_at": None
        }
    
    # 基本信息
    has_progress = True
    is_finished = progress.is_finished
    current_chapter_index = progress.current_chapter_index
    last_read_at = progress.last_read_at
    
    # 获取当前章节标题
    current_chapter_title = None
    if chapters and current_chapter_index is not None:
        if 0 <= current_chapter_index < len(chapters):
            current_chapter_title = chapters[current_chapter_index].title
    
    # 计算进度百分比
    progress_percent = 0.0
    if is_finished:
        progress_percent = 100.0
    elif chapters:
        total_chapters = len(chapters)
        if total_chapters > 0 and current_chapter_index is not None:
            # 使用章节索引计算进度
            # 当前章节索引 / (总章节数 - 1) * 100
            progress_percent = (current_chapter_index / max(total_chapters - 1, 1)) * 100.0
            progress_percent = min(100.0, max(0.0, progress_percent))
    
    return {
        "has_progress": has_progress,
        "is_finished": is_finished,
        "progress_percent": progress_percent,
        "current_chapter_index": current_chapter_index,
        "current_chapter_title": current_chapter_title,
        "last_read_at": last_read_at
    }

