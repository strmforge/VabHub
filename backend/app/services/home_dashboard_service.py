"""
首页仪表盘服务
HOME-1 实现

聚合各模块数据，提供首页总览信息
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.ebook import EBook
from app.models.music import Music, MusicFile
from app.models.manga_series_local import MangaSeriesLocal
from app.models.tts_job import TTSJob
from app.models.music_download_job import MusicDownloadJob
from app.models.user_novel_reading_progress import UserNovelReadingProgress
from app.models.user_audiobook_progress import UserAudiobookProgress
from app.models.manga_reading_progress import MangaReadingProgress

from app.schemas.home_dashboard import (
    HomeDashboardResponse,
    HomeQuickStat,
    HomeUpNextItem,
    HomeRecentItem,
    HomeRunnerStatus,
    HomeTaskSummary,
)

logger = logging.getLogger(__name__)


async def get_home_dashboard(
    current_user: User,
    db: AsyncSession,
) -> HomeDashboardResponse:
    """
    获取首页仪表盘数据
    
    聚合各模块的统计、进度、最近新增等信息
    """
    user_id = current_user.id
    
    # 并行获取各部分数据
    stats = await _get_quick_stats(db, user_id)
    up_next = await _get_up_next(db, user_id)
    recent_items = await _get_recent_items(db)
    runners = await _get_runner_status(db)
    tasks = await _get_task_summary(db, user_id)
    
    return HomeDashboardResponse(
        stats=stats,
        up_next=up_next,
        recent_items=recent_items,
        runners=runners,
        tasks=tasks,
    )


async def _get_quick_stats(db: AsyncSession, user_id: int) -> List[HomeQuickStat]:
    """获取快速统计"""
    stats = []
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    try:
        # 小说数量
        result = await db.execute(select(func.count()).select_from(EBook))
        novel_count = result.scalar() or 0
        stats.append(HomeQuickStat(
            label="小说/电子书",
            value=novel_count,
            icon="mdi-book-open-page-variant",
            color="primary"
        ))
    except Exception as e:
        logger.warning(f"获取小说统计失败: {e}")
        stats.append(HomeQuickStat(label="小说/电子书", value=0, icon="mdi-book-open-page-variant", color="primary"))
    
    try:
        # 漫画系列数量
        result = await db.execute(select(func.count()).select_from(MangaSeriesLocal))
        manga_count = result.scalar() or 0
        stats.append(HomeQuickStat(
            label="漫画系列",
            value=manga_count,
            icon="mdi-book-open-variant",
            color="warning"
        ))
    except Exception as e:
        logger.warning(f"获取漫画统计失败: {e}")
        stats.append(HomeQuickStat(label="漫画系列", value=0, icon="mdi-book-open-variant", color="warning"))
    
    try:
        # 音乐数量
        result = await db.execute(select(func.count()).select_from(Music))
        music_count = result.scalar() or 0
        stats.append(HomeQuickStat(
            label="音乐作品",
            value=music_count,
            icon="mdi-music",
            color="success"
        ))
    except Exception as e:
        logger.warning(f"获取音乐统计失败: {e}")
        stats.append(HomeQuickStat(label="音乐作品", value=0, icon="mdi-music", color="success"))
    
    try:
        # 最近7天活动数（阅读进度更新）
        activity_count = 0
        
        # 小说阅读活动
        result = await db.execute(
            select(func.count()).select_from(UserNovelReadingProgress).where(
                and_(
                    UserNovelReadingProgress.user_id == user_id,
                    UserNovelReadingProgress.last_read_at >= seven_days_ago
                )
            )
        )
        activity_count += result.scalar() or 0
        
        # 有声书活动
        result = await db.execute(
            select(func.count()).select_from(UserAudiobookProgress).where(
                and_(
                    UserAudiobookProgress.user_id == user_id,
                    or_(
                        UserAudiobookProgress.last_played_at >= seven_days_ago,
                        UserAudiobookProgress.updated_at >= seven_days_ago
                    )
                )
            )
        )
        activity_count += result.scalar() or 0
        
        # 漫画阅读活动
        result = await db.execute(
            select(func.count()).select_from(MangaReadingProgress).where(
                and_(
                    MangaReadingProgress.user_id == user_id,
                    MangaReadingProgress.last_read_at >= seven_days_ago
                )
            )
        )
        activity_count += result.scalar() or 0
        
        stats.append(HomeQuickStat(
            label="最近7天活动",
            value=activity_count,
            icon="mdi-chart-line",
            color="info"
        ))
    except Exception as e:
        logger.warning(f"获取活动统计失败: {e}")
        stats.append(HomeQuickStat(label="最近7天活动", value=0, icon="mdi-chart-line", color="info"))
    
    return stats


async def _get_up_next(db: AsyncSession, user_id: int) -> List[HomeUpNextItem]:
    """获取继续阅读/收听列表"""
    items = []
    
    try:
        # 小说阅读进度
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
            .limit(5)
        )
        result = await db.execute(stmt)
        rows = result.all()
        
        for progress, ebook in rows:
            total = progress.total_chapters or 1
            current = progress.current_chapter_index or 0
            percent = int(current / total * 100) if total > 0 else 0
            
            cover_url = None
            if ebook.cover_url:
                cover_url = ebook.cover_url if ebook.cover_url.startswith('http') else f"/media/{ebook.cover_url}"
            
            items.append(HomeUpNextItem(
                media_type="novel",
                title=ebook.title,
                sub_title=ebook.author,
                cover_url=cover_url,
                progress_percent=percent,
                last_activity_at=progress.last_read_at,
                route_name="NovelReader",
                route_params={"ebookId": ebook.id}
            ))
    except Exception as e:
        logger.warning(f"获取小说进度失败: {e}")
    
    try:
        # 有声书进度
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
            .limit(5)
        )
        result = await db.execute(stmt)
        rows = result.all()
        
        for progress, ebook in rows:
            total = progress.total_duration_seconds or 1
            current = progress.position_seconds or 0
            percent = int(current / total * 100) if total > 0 else 0
            
            cover_url = None
            if ebook.cover_url:
                cover_url = ebook.cover_url if ebook.cover_url.startswith('http') else f"/media/{ebook.cover_url}"
            
            items.append(HomeUpNextItem(
                media_type="audiobook",
                title=ebook.title,
                sub_title=ebook.author,
                cover_url=cover_url,
                progress_percent=percent,
                last_activity_at=progress.last_played_at or progress.updated_at,
                route_name="WorkDetail",
                route_params={"ebookId": ebook.id}
            ))
    except Exception as e:
        logger.warning(f"获取有声书进度失败: {e}")
    
    try:
        # 漫画阅读进度
        stmt = (
            select(MangaReadingProgress, MangaSeriesLocal)
            .join(MangaSeriesLocal, MangaReadingProgress.series_id == MangaSeriesLocal.id)
            .where(
                and_(
                    MangaReadingProgress.user_id == user_id,
                    MangaReadingProgress.is_finished == False  # noqa: E712
                )
            )
            .order_by(desc(MangaReadingProgress.last_read_at))
            .limit(5)
        )
        result = await db.execute(stmt)
        rows = result.all()
        
        for progress, series in rows:
            cover_url = f"/media/{series.cover_path}" if series.cover_path else None
            
            items.append(HomeUpNextItem(
                media_type="manga",
                title=series.title,
                sub_title=series.author if hasattr(series, 'author') else None,
                cover_url=cover_url,
                progress_percent=None,  # 漫画进度较难计算
                last_activity_at=progress.last_read_at,
                route_name="MangaReaderPage",
                route_params={"series_id": series.id}
            ))
    except Exception as e:
        logger.warning(f"获取漫画进度失败: {e}")
    
    # 按最近活动时间排序
    items.sort(key=lambda x: x.last_activity_at or datetime.min, reverse=True)
    return items[:10]


async def _get_recent_items(db: AsyncSession) -> List[HomeRecentItem]:
    """获取最近新增项目"""
    items = []
    
    try:
        # 最近新增的小说
        stmt = (
            select(EBook)
            .order_by(desc(EBook.created_at))
            .limit(5)
        )
        result = await db.execute(stmt)
        ebooks = result.scalars().all()
        
        for ebook in ebooks:
            cover_url = None
            if ebook.cover_url:
                cover_url = ebook.cover_url if ebook.cover_url.startswith('http') else f"/media/{ebook.cover_url}"
            
            items.append(HomeRecentItem(
                media_type="novel",
                title=ebook.title,
                sub_title=ebook.author,
                cover_url=cover_url,
                created_at=ebook.created_at,
                route_name="WorkDetail",
                route_params={"ebookId": ebook.id}
            ))
    except Exception as e:
        logger.warning(f"获取最近小说失败: {e}")
    
    try:
        # 最近新增的漫画
        stmt = (
            select(MangaSeriesLocal)
            .order_by(desc(MangaSeriesLocal.created_at))
            .limit(5)
        )
        result = await db.execute(stmt)
        series_list = result.scalars().all()
        
        for series in series_list:
            cover_url = f"/media/{series.cover_path}" if series.cover_path else None
            
            items.append(HomeRecentItem(
                media_type="manga",
                title=series.title,
                sub_title=series.author if hasattr(series, 'author') else None,
                cover_url=cover_url,
                created_at=series.created_at,
                route_name="MangaReaderPage",
                route_params={"series_id": series.id}
            ))
    except Exception as e:
        logger.warning(f"获取最近漫画失败: {e}")
    
    try:
        # 最近新增的音乐
        stmt = (
            select(Music)
            .order_by(desc(Music.created_at))
            .limit(5)
        )
        result = await db.execute(stmt)
        musics = result.scalars().all()
        
        for music in musics:
            items.append(HomeRecentItem(
                media_type="music",
                title=music.title,
                sub_title=music.artist,
                cover_url=None,  # 音乐暂无封面
                created_at=music.created_at,
                route_name="MusicCenter",
                route_params={}
            ))
    except Exception as e:
        logger.warning(f"获取最近音乐失败: {e}")
    
    # 按创建时间排序
    items.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
    return items[:10]


async def _get_runner_status(db: AsyncSession) -> List[HomeRunnerStatus]:
    """获取 Runner 状态"""
    # 目前没有 runner 心跳表，返回预定义的 runner 列表
    runners = [
        HomeRunnerStatus(
            name="TTS 生成服务",
            key="tts_worker",
            last_run_at=None,
            last_status="unknown",
            last_message="请配置 systemd timer 或手动运行"
        ),
        HomeRunnerStatus(
            name="TTS 清理服务",
            key="tts_cleanup",
            last_run_at=None,
            last_status="unknown",
            last_message="请配置 systemd timer 或手动运行"
        ),
        HomeRunnerStatus(
            name="漫画追更同步",
            key="manga_follow",
            last_run_at=None,
            last_status="unknown",
            last_message="请配置 systemd timer 或手动运行"
        ),
        HomeRunnerStatus(
            name="音乐榜单同步",
            key="music_chart_sync",
            last_run_at=None,
            last_status="unknown",
            last_message="请配置 systemd timer 或手动运行"
        ),
        HomeRunnerStatus(
            name="音乐下载服务",
            key="music_download",
            last_run_at=None,
            last_status="unknown",
            last_message="请配置 systemd timer 或手动运行"
        ),
    ]
    
    return runners


async def _get_task_summary(db: AsyncSession, user_id: int) -> HomeTaskSummary:
    """获取任务汇总"""
    total_running = 0
    total_failed_recent = 0
    total_waiting = 0
    
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    try:
        # TTS 任务统计
        # running
        result = await db.execute(
            select(func.count()).select_from(TTSJob).where(TTSJob.status == "running")
        )
        total_running += result.scalar() or 0
        
        # queued (waiting)
        result = await db.execute(
            select(func.count()).select_from(TTSJob).where(TTSJob.status == "queued")
        )
        total_waiting += result.scalar() or 0
        
        # failed (recent)
        result = await db.execute(
            select(func.count()).select_from(TTSJob).where(
                and_(
                    TTSJob.status == "failed",
                    TTSJob.updated_at >= seven_days_ago
                )
            )
        )
        total_failed_recent += result.scalar() or 0
    except Exception as e:
        logger.warning(f"获取 TTS 任务统计失败: {e}")
    
    try:
        # 音乐下载任务统计
        # running (searching, downloading, importing)
        result = await db.execute(
            select(func.count()).select_from(MusicDownloadJob).where(
                MusicDownloadJob.status.in_(["searching", "downloading", "importing"])
            )
        )
        total_running += result.scalar() or 0
        
        # waiting (pending, found, submitted)
        result = await db.execute(
            select(func.count()).select_from(MusicDownloadJob).where(
                MusicDownloadJob.status.in_(["pending", "found", "submitted"])
            )
        )
        total_waiting += result.scalar() or 0
        
        # failed (recent)
        result = await db.execute(
            select(func.count()).select_from(MusicDownloadJob).where(
                and_(
                    MusicDownloadJob.status == "failed",
                    MusicDownloadJob.updated_at >= seven_days_ago
                )
            )
        )
        total_failed_recent += result.scalar() or 0
    except Exception as e:
        logger.warning(f"获取音乐下载任务统计失败: {e}")
    
    return HomeTaskSummary(
        total_running=total_running,
        total_failed_recent=total_failed_recent,
        total_waiting=total_waiting,
    )
