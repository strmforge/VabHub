"""
任务中心服务
TASK-1 实现

聚合各类任务（TTS、音乐下载等）到统一视图
"""
import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tts_job import TTSJob
from app.models.music_download_job import MusicDownloadJob
from app.models.ebook import EBook

from app.schemas.task_center import (
    TaskCenterItem,
    TaskCenterListResponse,
    TaskStatus,
)

logger = logging.getLogger(__name__)


def _map_tts_status(status: str) -> TaskStatus:
    """映射 TTS 任务状态"""
    mapping = {
        "queued": "pending",
        "running": "running",
        "success": "success",
        "partial": "success",  # 部分成功也算成功
        "failed": "failed",
    }
    return mapping.get(status, "pending")


def _map_music_download_status(status: str) -> TaskStatus:
    """映射音乐下载任务状态"""
    mapping = {
        "pending": "pending",
        "searching": "running",
        "found": "pending",
        "not_found": "failed",
        "submitted": "running",
        "downloading": "running",
        "importing": "running",
        "completed": "success",
        "failed": "failed",
        "skipped_duplicate": "skipped",
    }
    return mapping.get(status, "pending")


async def list_tasks(
    db: AsyncSession,
    *,
    media_type: Optional[str] = None,
    kind: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> TaskCenterListResponse:
    """
    获取任务列表
    
    聚合 TTS 任务和音乐下载任务
    """
    items: List[TaskCenterItem] = []
    
    # 1. TTS 任务
    if kind is None or kind == "tts":
        if media_type is None or media_type in ["novel", "audiobook"]:
            try:
                stmt = (
                    select(TTSJob, EBook)
                    .outerjoin(EBook, TTSJob.ebook_id == EBook.id)
                    .order_by(desc(TTSJob.updated_at))
                    .limit(100)
                )
                result = await db.execute(stmt)
                rows = result.all()
                
                for job, ebook in rows:
                    mapped_status = _map_tts_status(job.status)
                    
                    # 过滤状态
                    if status and mapped_status != status:
                        continue
                    
                    # 计算进度
                    progress = None
                    if job.total_chapters and job.total_chapters > 0:
                        progress = round(job.processed_chapters / job.total_chapters * 100, 1)
                    
                    items.append(TaskCenterItem(
                        id=f"tts:{job.id}",
                        kind="tts",
                        media_type="audiobook",
                        title=ebook.title if ebook else f"电子书 #{job.ebook_id}",
                        sub_title=f"TTS 生成 · {job.provider or 'unknown'}",
                        status=mapped_status,
                        progress=progress,
                        created_at=job.requested_at or job.created_at,
                        updated_at=job.updated_at,
                        last_error=job.last_error,
                        source="TTSJob",
                        route_name="DevTTSJobs",
                        route_params={}
                    ))
            except Exception as e:
                logger.warning(f"获取 TTS 任务失败: {e}")
    
    # 2. 音乐下载任务
    if kind is None or kind == "download":
        if media_type is None or media_type == "music":
            try:
                stmt = (
                    select(MusicDownloadJob)
                    .order_by(desc(MusicDownloadJob.updated_at))
                    .limit(100)
                )
                result = await db.execute(stmt)
                jobs = result.scalars().all()
                
                for job in jobs:
                    mapped_status = _map_music_download_status(job.status)
                    
                    # 过滤状态
                    if status and mapped_status != status:
                        continue
                    
                    items.append(TaskCenterItem(
                        id=f"music_dl:{job.id}",
                        kind="download",
                        media_type="music",
                        title=job.search_query,
                        sub_title=f"音乐下载 · {job.matched_site or '搜索中'}",
                        status=mapped_status,
                        progress=None,  # 音乐下载没有精确进度
                        created_at=job.created_at,
                        updated_at=job.updated_at,
                        last_error=job.last_error,
                        source="MusicDownloadJob",
                        route_name="MusicCenter",
                        route_params={}
                    ))
            except Exception as e:
                logger.warning(f"获取音乐下载任务失败: {e}")
    
    # 按更新时间排序
    items.sort(key=lambda x: x.updated_at or datetime.min, reverse=True)
    
    # 分页
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    paged_items = items[start:end]
    
    return TaskCenterListResponse(
        items=paged_items,
        total=total,
    )
