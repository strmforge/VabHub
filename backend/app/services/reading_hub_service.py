"""
阅读中心聚合服务

从各子系统中聚合阅读进度和历史记录
"""
from typing import List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_, or_
from loguru import logger

from app.models.user_novel_reading_progress import UserNovelReadingProgress
from app.models.user_audiobook_progress import UserAudiobookProgress
from app.models.manga_reading_progress import MangaReadingProgress
from app.models.ebook import EBook
from app.models.manga_series_local import MangaSeriesLocal
from app.models.manga_chapter_local import MangaChapterLocal
from app.models.manga_source import MangaSource
from app.models.enums.reading_media_type import ReadingMediaType
from app.schemas.reading_hub import ReadingOngoingItem, ReadingHistoryItem, ReadingActivityItem
from app.schemas.reading_status import ReadingStatusHelper, ReadingItemDisplayStatus


async def list_ongoing_reading(
    session: AsyncSession,
    user_id: int,
    limit_per_type: int = 10,
) -> List[ReadingOngoingItem]:
    """
    返回当前用户"正在进行"的阅读/收听项目
    
    从小说、有声书、漫画进度表中取出未读完的最近 N 本，合并后按 last_read_at 降序排序
    """
    items = []
    
    # 1. 小说进度（未读完）
    try:
        stmt = (
            select(UserNovelReadingProgress, EBook)
            .join(EBook, UserNovelReadingProgress.ebook_id == EBook.id)
            .where(
                and_(
                    UserNovelReadingProgress.user_id == user_id,
                    UserNovelReadingProgress.is_finished == False  # noqa: E712
                )
            )
            .order_by(desc(UserNovelReadingProgress.last_read_at))
            .limit(limit_per_type)
        )
        result = await session.execute(stmt)
        rows = result.all()
        
        for progress, ebook in rows:
            # 计算进度标签和百分比
            progress_label = f"第 {progress.current_chapter_index + 1} 章"
            progress_percent = None
            if hasattr(ebook, 'chapter_count') and ebook.chapter_count and ebook.chapter_count > 0:
                progress_percent = round((progress.current_chapter_index + 1) / ebook.chapter_count * 100, 1)
                progress_label += f" · {progress_percent:.0f}%"
            elif progress.chapter_offset > 0:
                progress_label += " · 阅读中"
            
            # 计算状态 (使用统一枚举)
            has_progress = progress.current_chapter_index > 0 or progress.chapter_offset > 0
            status: ReadingItemDisplayStatus = ReadingStatusHelper.get_display_status(
                is_finished=progress.is_finished,
                has_progress=has_progress
            )
            
            # 构建封面 URL
            cover_url = None
            if ebook.cover_url:
                if ebook.cover_url.startswith('http'):
                    cover_url = ebook.cover_url
                else:
                    cover_url = f"/media/{ebook.cover_url}"
            
            items.append(ReadingOngoingItem(
                media_type=ReadingMediaType.NOVEL,
                item_id=ebook.id,
                title=ebook.title,
                sub_title=ebook.author if hasattr(ebook, 'author') else None,
                cover_url=cover_url,
                source_label="小说中心",
                progress_label=progress_label,
                progress_percent=progress_percent,
                status=status,
                is_finished=progress.is_finished,
                last_read_at=progress.last_read_at,
                last_activity_at=progress.last_read_at,
                route_name="NovelReader",
                route_params={"ebookId": ebook.id}
            ))
    except Exception as e:
        logger.error(f"获取小说进度失败: {e}", exc_info=True)
    
    # 2. 有声书进度（未听完）
    try:
        stmt = (
            select(UserAudiobookProgress, EBook)
            .join(EBook, UserAudiobookProgress.ebook_id == EBook.id)
            .where(
                and_(
                    UserAudiobookProgress.user_id == user_id,
                    UserAudiobookProgress.is_finished == False  # noqa: E712
                )
            )
            .order_by(desc(UserAudiobookProgress.last_played_at))
            .limit(limit_per_type)
        )
        result = await session.execute(stmt)
        rows = result.all()
        
        for progress, ebook in rows:
            # 计算进度标签和百分比
            progress_percent = None
            if progress.duration_seconds and progress.duration_seconds > 0:
                current_min = progress.position_seconds // 60
                current_sec = progress.position_seconds % 60
                total_min = progress.duration_seconds // 60
                total_sec = progress.duration_seconds % 60
                progress_label = f"{current_min}:{current_sec:02d} / {total_min}:{total_sec:02d}"
                progress_percent = round(progress.position_seconds / progress.duration_seconds * 100, 1)
            else:
                progress_label = f"{progress.position_seconds // 60} 分钟"
            
            # 计算状态 (使用统一枚举)
            has_progress = progress.position_seconds > 0
            status: ReadingItemDisplayStatus = ReadingStatusHelper.get_display_status(
                is_finished=progress.is_finished,
                has_progress=has_progress
            )
            last_activity = progress.last_played_at or progress.updated_at
            
            # 构建封面 URL
            cover_url = None
            if ebook.cover_url:
                if ebook.cover_url.startswith('http'):
                    cover_url = ebook.cover_url
                else:
                    cover_url = f"/media/{ebook.cover_url}"
            
            items.append(ReadingOngoingItem(
                media_type=ReadingMediaType.AUDIOBOOK,
                item_id=ebook.id,
                title=ebook.title,
                sub_title=ebook.author if hasattr(ebook, 'author') else None,
                cover_url=cover_url,
                source_label="有声书",
                progress_label=progress_label,
                progress_percent=progress_percent,
                status=status,
                is_finished=progress.is_finished,
                last_read_at=last_activity,
                last_activity_at=last_activity,
                route_name="WorkDetail",
                route_params={"ebookId": ebook.id}
            ))
    except Exception as e:
        logger.error(f"获取有声书进度失败: {e}", exc_info=True)
    
    # 3. 漫画进度（未读完）
    try:
        stmt = (
            select(MangaReadingProgress, MangaSeriesLocal, MangaChapterLocal, MangaSource)
            .join(MangaSeriesLocal, MangaReadingProgress.series_id == MangaSeriesLocal.id)
            .outerjoin(MangaChapterLocal, MangaReadingProgress.chapter_id == MangaChapterLocal.id)
            .outerjoin(MangaSource, MangaSeriesLocal.source_id == MangaSource.id)
            .where(
                and_(
                    MangaReadingProgress.user_id == user_id,
                    MangaReadingProgress.is_finished == False  # noqa: E712
                )
            )
            .order_by(desc(MangaReadingProgress.last_read_at))
            .limit(limit_per_type)
        )
        result = await session.execute(stmt)
        rows = result.all()
        
        for progress, series, chapter, source in rows:
            # 计算进度标签和百分比
            progress_percent = None
            if chapter:
                chapter_label = chapter.title or f"第 {chapter.number or progress.chapter_id} 话"
                progress_label = f"{chapter_label} · 第 {progress.last_page_index} 页"
                # 如果有总页数，计算百分比
                if hasattr(chapter, 'page_count') and chapter.page_count and chapter.page_count > 0:
                    progress_percent = round(progress.last_page_index / chapter.page_count * 100, 1)
            else:
                progress_label = f"第 {progress.last_page_index} 页"
            
            # 计算状态 (使用统一枚举)
            has_progress = progress.last_page_index > 0
            status: ReadingItemDisplayStatus = ReadingStatusHelper.get_display_status(
                is_finished=progress.is_finished,
                has_progress=has_progress
            )
            
            # 构建封面 URL
            cover_url = None
            if series.cover_path:
                cover_url = f"/media/{series.cover_path}"
            
            # 路由参数
            route_params = {"series_id": series.id}
            if progress.chapter_id:
                route_params["chapter_id"] = progress.chapter_id
            
            items.append(ReadingOngoingItem(
                media_type=ReadingMediaType.MANGA,
                item_id=series.id,
                title=series.title,
                sub_title=series.author if hasattr(series, 'author') else None,
                cover_url=cover_url,
                source_label=source.name if source else "漫画",
                progress_label=progress_label,
                progress_percent=progress_percent,
                status=status,
                is_finished=progress.is_finished,
                last_read_at=progress.last_read_at,
                last_activity_at=progress.last_read_at,
                route_name="MangaReaderPage",
                route_params=route_params
            ))
    except Exception as e:
        logger.error(f"获取漫画进度失败: {e}", exc_info=True)
    
    # 按 last_read_at 降序排序
    items.sort(key=lambda x: x.last_read_at, reverse=True)
    
    return items


async def list_reading_history(
    session: AsyncSession,
    user_id: int,
    limit: int = 30,
    offset: int = 0,
    media_type: ReadingMediaType = None,
) -> List[ReadingHistoryItem]:
    """
    返回统一"阅读历史"列表
    
    聚合小说 / 有声书 / 漫画各自的历史记录，按 last_read_at 降序
    """
    items = []
    
    # 1. 小说历史
    if not media_type or media_type == ReadingMediaType.NOVEL:
        try:
            stmt = (
                select(UserNovelReadingProgress, EBook)
                .join(EBook, UserNovelReadingProgress.ebook_id == EBook.id)
                .where(UserNovelReadingProgress.user_id == user_id)
                .order_by(desc(UserNovelReadingProgress.last_read_at))
            )
            result = await session.execute(stmt)
            rows = result.all()
            
            for progress, ebook in rows:
                last_position_label = f"第 {progress.current_chapter_index + 1} 章"
                progress_percent = None
                if hasattr(ebook, 'chapter_count') and ebook.chapter_count and ebook.chapter_count > 0:
                    progress_percent = round((progress.current_chapter_index + 1) / ebook.chapter_count * 100, 1)
                
                if progress.is_finished:
                    last_position_label = "已读完"
                    progress_percent = 100.0
                
                status = 'finished' if progress.is_finished else ('in_progress' if progress.current_chapter_index > 0 else 'not_started')
                
                cover_url = None
                if ebook.cover_url:
                    if ebook.cover_url.startswith('http'):
                        cover_url = ebook.cover_url
                    else:
                        cover_url = f"/media/{ebook.cover_url}"
                
                items.append(ReadingHistoryItem(
                    media_type=ReadingMediaType.NOVEL,
                    item_id=ebook.id,
                    title=ebook.title,
                    sub_title=ebook.author if hasattr(ebook, 'author') else None,
                    cover_url=cover_url,
                    source_label="小说中心",
                    last_position_label=last_position_label,
                    progress_percent=progress_percent,
                    status=status,
                    is_finished=progress.is_finished,
                    last_read_at=progress.last_read_at,
                    last_activity_at=progress.last_read_at,
                    route_name="NovelReader",
                    route_params={"ebookId": ebook.id}
                ))
        except Exception as e:
            logger.error(f"获取小说历史失败: {e}", exc_info=True)
    
    # 2. 有声书历史
    if not media_type or media_type == ReadingMediaType.AUDIOBOOK:
        try:
            stmt = (
                select(UserAudiobookProgress, EBook)
                .join(EBook, UserAudiobookProgress.ebook_id == EBook.id)
                .where(UserAudiobookProgress.user_id == user_id)
                .order_by(desc(UserAudiobookProgress.last_played_at))
            )
            result = await session.execute(stmt)
            rows = result.all()
            
            for progress, ebook in rows:
                progress_percent = None
                if progress.duration_seconds and progress.duration_seconds > 0:
                    current_min = progress.position_seconds // 60
                    current_sec = progress.position_seconds % 60
                    total_min = progress.duration_seconds // 60
                    total_sec = progress.duration_seconds % 60
                    last_position_label = f"{current_min}:{current_sec:02d} / {total_min}:{total_sec:02d}"
                    progress_percent = round(progress.position_seconds / progress.duration_seconds * 100, 1)
                else:
                    last_position_label = f"{progress.position_seconds // 60} 分钟"
                
                if progress.is_finished:
                    last_position_label = "已听完"
                    progress_percent = 100.0
                
                status = 'finished' if progress.is_finished else ('in_progress' if progress.position_seconds > 0 else 'not_started')
                last_activity = progress.last_played_at or progress.updated_at
                
                cover_url = None
                if ebook.cover_url:
                    if ebook.cover_url.startswith('http'):
                        cover_url = ebook.cover_url
                    else:
                        cover_url = f"/media/{ebook.cover_url}"
                
                items.append(ReadingHistoryItem(
                    media_type=ReadingMediaType.AUDIOBOOK,
                    item_id=ebook.id,
                    title=ebook.title,
                    sub_title=ebook.author if hasattr(ebook, 'author') else None,
                    cover_url=cover_url,
                    source_label="有声书",
                    last_position_label=last_position_label,
                    progress_percent=progress_percent,
                    status=status,
                    is_finished=progress.is_finished,
                    last_read_at=last_activity,
                    last_activity_at=last_activity,
                    route_name="WorkDetail",
                    route_params={"ebookId": ebook.id}
                ))
        except Exception as e:
            logger.error(f"获取有声书历史失败: {e}", exc_info=True)
    
    # 3. 漫画历史
    if not media_type or media_type == ReadingMediaType.MANGA:
        try:
            stmt = (
                select(MangaReadingProgress, MangaSeriesLocal, MangaChapterLocal, MangaSource)
                .join(MangaSeriesLocal, MangaReadingProgress.series_id == MangaSeriesLocal.id)
                .outerjoin(MangaChapterLocal, MangaReadingProgress.chapter_id == MangaChapterLocal.id)
                .outerjoin(MangaSource, MangaSeriesLocal.source_id == MangaSource.id)
                .where(MangaReadingProgress.user_id == user_id)
                .order_by(desc(MangaReadingProgress.last_read_at))
            )
            result = await session.execute(stmt)
            rows = result.all()
            
            for progress, series, chapter, source in rows:
                progress_percent = None
                if chapter:
                    chapter_label = chapter.title or f"第 {chapter.number or progress.chapter_id} 话"
                    last_position_label = f"{chapter_label} · 第 {progress.last_page_index} 页"
                    if hasattr(chapter, 'page_count') and chapter.page_count and chapter.page_count > 0:
                        progress_percent = round(progress.last_page_index / chapter.page_count * 100, 1)
                else:
                    last_position_label = f"第 {progress.last_page_index} 页"
                
                if progress.is_finished:
                    last_position_label = "已读完"
                    progress_percent = 100.0
                
                status = 'finished' if progress.is_finished else ('in_progress' if progress.last_page_index > 0 else 'not_started')
                
                cover_url = None
                if series.cover_path:
                    cover_url = f"/media/{series.cover_path}"
                
                route_params = {"series_id": series.id}
                if progress.chapter_id:
                    route_params["chapter_id"] = progress.chapter_id
                
                items.append(ReadingHistoryItem(
                    media_type=ReadingMediaType.MANGA,
                    item_id=series.id,
                    title=series.title,
                    sub_title=series.author if hasattr(series, 'author') else None,
                    cover_url=cover_url,
                    source_label=source.name if source else "漫画",
                    last_position_label=last_position_label,
                    progress_percent=progress_percent,
                    status=status,
                    is_finished=progress.is_finished,
                    last_read_at=progress.last_read_at,
                    last_activity_at=progress.last_read_at,
                    route_name="MangaReaderPage",
                    route_params=route_params
                ))
        except Exception as e:
            logger.error(f"获取漫画历史失败: {e}", exc_info=True)
    
    # 按 last_read_at 降序排序
    items.sort(key=lambda x: x.last_read_at, reverse=True)
    
    # 分页
    return items[offset:offset + limit]


async def get_reading_stats(
    session: AsyncSession,
    user_id: int,
) -> dict:
    """
    获取阅读统计信息（增强版）
    """
    stats = {
        "ongoing_count": 0,
        "finished_count": 0,
        "finished_count_recent_30d": 0,
        "favorites_count": 0,
        "recent_activity_count": 0,
        "by_type": {}
    }
    
    thirty_days_ago = datetime.now() - timedelta(days=30)
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    # 统计各类型
    for media_type in ReadingMediaType:
        type_stats = {"ongoing": 0, "finished": 0, "recent_finished": 0, "recent_activity": 0}
        
        if media_type == ReadingMediaType.NOVEL:
            # 小说进行中
            stmt = select(func.count()).select_from(UserNovelReadingProgress).where(
                and_(
                    UserNovelReadingProgress.user_id == user_id,
                    UserNovelReadingProgress.is_finished == False  # noqa: E712
                )
            )
            result = await session.execute(stmt)
            type_stats["ongoing"] = result.scalar() or 0
            
            # 总完成
            stmt = select(func.count()).select_from(UserNovelReadingProgress).where(
                and_(
                    UserNovelReadingProgress.user_id == user_id,
                    UserNovelReadingProgress.is_finished == True  # noqa: E712
                )
            )
            result = await session.execute(stmt)
            type_stats["finished"] = result.scalar() or 0
            
            # 最近30天完成
            stmt = select(func.count()).select_from(UserNovelReadingProgress).where(
                and_(
                    UserNovelReadingProgress.user_id == user_id,
                    UserNovelReadingProgress.is_finished == True,  # noqa: E712
                    UserNovelReadingProgress.last_read_at >= thirty_days_ago
                )
            )
            result = await session.execute(stmt)
            type_stats["recent_finished"] = result.scalar() or 0
            
            # 最近7天活动
            stmt = select(func.count()).select_from(UserNovelReadingProgress).where(
                and_(
                    UserNovelReadingProgress.user_id == user_id,
                    UserNovelReadingProgress.last_read_at >= seven_days_ago
                )
            )
            result = await session.execute(stmt)
            type_stats["recent_activity"] = result.scalar() or 0
            
        elif media_type == ReadingMediaType.AUDIOBOOK:
            # 有声书进行中
            stmt = select(func.count()).select_from(UserAudiobookProgress).where(
                and_(
                    UserAudiobookProgress.user_id == user_id,
                    UserAudiobookProgress.is_finished == False  # noqa: E712
                )
            )
            result = await session.execute(stmt)
            type_stats["ongoing"] = result.scalar() or 0
            
            # 总完成
            stmt = select(func.count()).select_from(UserAudiobookProgress).where(
                and_(
                    UserAudiobookProgress.user_id == user_id,
                    UserAudiobookProgress.is_finished == True  # noqa: E712
                )
            )
            result = await session.execute(stmt)
            type_stats["finished"] = result.scalar() or 0
            
            # 最近30天完成
            stmt = select(func.count()).select_from(UserAudiobookProgress).where(
                and_(
                    UserAudiobookProgress.user_id == user_id,
                    UserAudiobookProgress.is_finished == True,  # noqa: E712
                    or_(
                        UserAudiobookProgress.last_played_at >= thirty_days_ago,
                        UserAudiobookProgress.updated_at >= thirty_days_ago
                    )
                )
            )
            result = await session.execute(stmt)
            type_stats["recent_finished"] = result.scalar() or 0
            
            # 最近7天活动
            stmt = select(func.count()).select_from(UserAudiobookProgress).where(
                and_(
                    UserAudiobookProgress.user_id == user_id,
                    or_(
                        UserAudiobookProgress.last_played_at >= seven_days_ago,
                        UserAudiobookProgress.updated_at >= seven_days_ago
                    )
                )
            )
            result = await session.execute(stmt)
            type_stats["recent_activity"] = result.scalar() or 0
            
        elif media_type == ReadingMediaType.MANGA:
            # 漫画进行中
            stmt = select(func.count()).select_from(MangaReadingProgress).where(
                and_(
                    MangaReadingProgress.user_id == user_id,
                    MangaReadingProgress.is_finished == False  # noqa: E712
                )
            )
            result = await session.execute(stmt)
            type_stats["ongoing"] = result.scalar() or 0
            
            # 总完成
            stmt = select(func.count()).select_from(MangaReadingProgress).where(
                and_(
                    MangaReadingProgress.user_id == user_id,
                    MangaReadingProgress.is_finished == True  # noqa: E712
                )
            )
            result = await session.execute(stmt)
            type_stats["finished"] = result.scalar() or 0
            
            # 最近30天完成
            stmt = select(func.count()).select_from(MangaReadingProgress).where(
                and_(
                    MangaReadingProgress.user_id == user_id,
                    MangaReadingProgress.is_finished == True,  # noqa: E712
                    MangaReadingProgress.last_read_at >= thirty_days_ago
                )
            )
            result = await session.execute(stmt)
            type_stats["recent_finished"] = result.scalar() or 0
            
            # 最近7天活动
            stmt = select(func.count()).select_from(MangaReadingProgress).where(
                and_(
                    MangaReadingProgress.user_id == user_id,
                    MangaReadingProgress.last_read_at >= seven_days_ago
                )
            )
            result = await session.execute(stmt)
            type_stats["recent_activity"] = result.scalar() or 0
        
        stats["by_type"][media_type.value] = type_stats
        stats["ongoing_count"] += type_stats["ongoing"]
        stats["finished_count"] += type_stats.get("finished", 0)
        stats["finished_count_recent_30d"] += type_stats["recent_finished"]
        stats["recent_activity_count"] += type_stats.get("recent_activity", 0)
    
    return stats


async def get_recent_activity(
    session: AsyncSession,
    user_id: int,
    limit: int = 50,
) -> List[ReadingActivityItem]:
    """
    获取最近阅读活动时间线
    
    聚合小说 / 有声书 / 漫画的最近活动，按时间倒序
    """
    items = []
    
    # 1. 小说活动
    try:
        stmt = (
            select(UserNovelReadingProgress, EBook)
            .join(EBook, UserNovelReadingProgress.ebook_id == EBook.id)
            .where(UserNovelReadingProgress.user_id == user_id)
            .order_by(desc(UserNovelReadingProgress.last_read_at))
            .limit(limit)
        )
        result = await session.execute(stmt)
        rows = result.all()
        
        for progress, ebook in rows:
            status = 'finished' if progress.is_finished else ('in_progress' if progress.current_chapter_index > 0 else 'not_started')
            activity_label = f"阅读了第 {progress.current_chapter_index + 1} 章"
            if progress.is_finished:
                activity_label = "已读完"
            
            cover_url = None
            if ebook.cover_url:
                cover_url = ebook.cover_url if ebook.cover_url.startswith('http') else f"/media/{ebook.cover_url}"
            
            items.append(ReadingActivityItem(
                media_type=ReadingMediaType.NOVEL,
                item_id=ebook.id,
                title=ebook.title,
                sub_title=ebook.author if hasattr(ebook, 'author') else None,
                cover_url=cover_url,
                status=status,
                activity_type='read',
                activity_label=activity_label,
                occurred_at=progress.last_read_at,
                route_name="NovelReader",
                route_params={"ebookId": ebook.id}
            ))
    except Exception as e:
        logger.error(f"获取小说活动失败: {e}", exc_info=True)
    
    # 2. 有声书活动
    try:
        stmt = (
            select(UserAudiobookProgress, EBook)
            .join(EBook, UserAudiobookProgress.ebook_id == EBook.id)
            .where(UserAudiobookProgress.user_id == user_id)
            .order_by(desc(UserAudiobookProgress.last_played_at))
            .limit(limit)
        )
        result = await session.execute(stmt)
        rows = result.all()
        
        for progress, ebook in rows:
            status = 'finished' if progress.is_finished else ('in_progress' if progress.position_seconds > 0 else 'not_started')
            if progress.is_finished:
                activity_label = "已听完"
            else:
                listened_min = progress.position_seconds // 60
                activity_label = f"收听了 {listened_min} 分钟"
            
            cover_url = None
            if ebook.cover_url:
                cover_url = ebook.cover_url if ebook.cover_url.startswith('http') else f"/media/{ebook.cover_url}"
            
            occurred_at = progress.last_played_at or progress.updated_at
            
            items.append(ReadingActivityItem(
                media_type=ReadingMediaType.AUDIOBOOK,
                item_id=ebook.id,
                title=ebook.title,
                sub_title=ebook.author if hasattr(ebook, 'author') else None,
                cover_url=cover_url,
                status=status,
                activity_type='listen',
                activity_label=activity_label,
                occurred_at=occurred_at,
                route_name="WorkDetail",
                route_params={"ebookId": ebook.id}
            ))
    except Exception as e:
        logger.error(f"获取有声书活动失败: {e}", exc_info=True)
    
    # 3. 漫画活动
    try:
        stmt = (
            select(MangaReadingProgress, MangaSeriesLocal, MangaChapterLocal, MangaSource)
            .join(MangaSeriesLocal, MangaReadingProgress.series_id == MangaSeriesLocal.id)
            .outerjoin(MangaChapterLocal, MangaReadingProgress.chapter_id == MangaChapterLocal.id)
            .outerjoin(MangaSource, MangaSeriesLocal.source_id == MangaSource.id)
            .where(MangaReadingProgress.user_id == user_id)
            .order_by(desc(MangaReadingProgress.last_read_at))
            .limit(limit)
        )
        result = await session.execute(stmt)
        rows = result.all()
        
        for progress, series, chapter, source in rows:
            status = 'finished' if progress.is_finished else ('in_progress' if progress.last_page_index > 0 else 'not_started')
            if progress.is_finished:
                activity_label = "已读完"
            elif chapter:
                chapter_label = chapter.title or f"第 {chapter.number or progress.chapter_id} 话"
                activity_label = f"阅读了 {chapter_label}"
            else:
                activity_label = f"阅读了第 {progress.last_page_index} 页"
            
            cover_url = f"/media/{series.cover_path}" if series.cover_path else None
            
            route_params = {"series_id": series.id}
            if progress.chapter_id:
                route_params["chapter_id"] = progress.chapter_id
            
            items.append(ReadingActivityItem(
                media_type=ReadingMediaType.MANGA,
                item_id=series.id,
                title=series.title,
                sub_title=series.author if hasattr(series, 'author') else None,
                cover_url=cover_url,
                status=status,
                activity_type='read',
                activity_label=activity_label,
                occurred_at=progress.last_read_at,
                route_name="MangaReaderPage",
                route_params=route_params
            ))
    except Exception as e:
        logger.error(f"获取漫画活动失败: {e}", exc_info=True)
    
    # 按 occurred_at 降序排序并限制数量
    items.sort(key=lambda x: x.occurred_at, reverse=True)
    return items[:limit]
