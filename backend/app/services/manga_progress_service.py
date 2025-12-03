"""
漫画阅读进度和历史服务
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from loguru import logger

from app.models.manga_reading_progress import MangaReadingProgress
from app.models.manga_series_local import MangaSeriesLocal
from app.models.manga_chapter_local import MangaChapterLocal
from app.models.manga_source import MangaSource
from app.schemas.manga_reading_progress import (
    MangaReadingProgressRead,
    MangaReadingProgressUpdate,
    MangaReadingHistoryItem,
)


async def get_progress_for_series(
    session: AsyncSession,
    user_id: int,
    series_id: int,
) -> Optional[MangaReadingProgressRead]:
    """
    获取当前用户在某个 series 上的阅读进度
    """
    stmt = select(MangaReadingProgress).where(
        MangaReadingProgress.user_id == user_id,
        MangaReadingProgress.series_id == series_id
    )
    result = await session.execute(stmt)
    progress = result.scalar_one_or_none()
    
    if progress:
        return MangaReadingProgressRead.model_validate(progress)
    return None


async def upsert_progress(
    session: AsyncSession,
    user_id: int,
    data: MangaReadingProgressUpdate,
) -> MangaReadingProgressRead:
    """
    根据 user_id + series_id 更新或创建进度
    
    - 若存在则更新 last_page_index / chapter_id / total_pages / is_finished / last_read_at
    - 若不存在则新建
    """
    stmt = select(MangaReadingProgress).where(
        MangaReadingProgress.user_id == user_id,
        MangaReadingProgress.series_id == data.series_id
    )
    result = await session.execute(stmt)
    progress = result.scalar_one_or_none()
    
    if progress:
        # 更新现有记录
        progress.chapter_id = data.chapter_id
        progress.last_page_index = data.last_page_index
        progress.total_pages = data.total_pages
        progress.is_finished = data.is_finished
        progress.last_read_at = datetime.now()
    else:
        # 创建新记录
        progress = MangaReadingProgress(
            user_id=user_id,
            series_id=data.series_id,
            chapter_id=data.chapter_id,
            last_page_index=data.last_page_index,
            total_pages=data.total_pages,
            is_finished=data.is_finished,
            last_read_at=datetime.now()
        )
        session.add(progress)
    
    await session.commit()
    await session.refresh(progress)
    
    return MangaReadingProgressRead.model_validate(progress)


async def list_reading_history(
    session: AsyncSession,
    user_id: int,
    limit: int = 20,
    offset: int = 0,
) -> List[MangaReadingHistoryItem]:
    """
    返回用户最近阅读的漫画列表（按 last_read_at 降序）
    
    需要 join MangaSeriesLocal / MangaChapterLocal / MangaSource
    """
    stmt = (
        select(
            MangaReadingProgress,
            MangaSeriesLocal,
            MangaChapterLocal,
            MangaSource
        )
        .join(MangaSeriesLocal, MangaReadingProgress.series_id == MangaSeriesLocal.id)
        .outerjoin(MangaChapterLocal, MangaReadingProgress.chapter_id == MangaChapterLocal.id)
        .outerjoin(MangaSource, MangaSeriesLocal.source_id == MangaSource.id)
        .where(MangaReadingProgress.user_id == user_id)
        .order_by(desc(MangaReadingProgress.last_read_at))
        .limit(limit)
        .offset(offset)
    )
    
    result = await session.execute(stmt)
    rows = result.all()
    
    history_items = []
    for progress, series, chapter, source in rows:
        # 构建封面 URL
        cover_url = None
        if series.cover_path:
            cover_url = f"/media/{series.cover_path}"
        
        history_items.append(MangaReadingHistoryItem(
            series_id=series.id,
            series_title=series.title,
            series_cover_url=cover_url,
            source_name=source.name if source else None,
            last_chapter_id=progress.chapter_id,
            last_chapter_title=chapter.title if chapter else None,
            last_page_index=progress.last_page_index,
            total_pages=progress.total_pages,
            is_finished=progress.is_finished,
            last_read_at=progress.last_read_at
        ))
    
    return history_items

