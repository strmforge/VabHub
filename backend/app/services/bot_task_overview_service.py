"""
Bot 任务汇总服务
BOT-TELEGRAM Phase 2

汇总用户的下载任务
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.user import User


@dataclass
class BotDownloadJobItem:
    """下载任务项"""
    id: int
    job_type: str  # pt_download / music_download / tts_job / ...
    title: str
    status: str  # queued / downloading / completed / failed
    progress: Optional[float] = None  # 0-100
    created_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    extra: Optional[dict] = None


async def list_user_download_jobs(
    session: AsyncSession,
    user: User,
    limit: int = 20,
    status: Optional[str] = None,
) -> list[BotDownloadJobItem]:
    """
    获取用户的下载任务列表
    
    Args:
        session: 数据库会话
        user: 用户对象
        limit: 返回数量限制
        status: 状态筛选
        
    Returns:
        下载任务列表
    """
    items: list[BotDownloadJobItem] = []
    
    # 1. PT 下载任务
    try:
        pt_items = await _get_pt_download_jobs(session, user.id, limit, status)
        items.extend(pt_items)
    except Exception as e:
        logger.warning(f"[bot-task] get pt downloads failed: {e}")
    
    # 2. TTS 任务
    try:
        tts_items = await _get_tts_jobs(session, user.id, limit, status)
        items.extend(tts_items)
    except Exception as e:
        logger.warning(f"[bot-task] get tts jobs failed: {e}")
    
    # 按创建时间排序
    items.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
    
    return items[:limit]


async def _get_pt_download_jobs(
    session: AsyncSession,
    user_id: int,
    limit: int,
    status: Optional[str],
) -> list[BotDownloadJobItem]:
    """获取 PT 下载任务"""
    items = []
    
    try:
        # 尝试从下载任务表获取
        from app.models.download_task import DownloadTask
        
        stmt = select(DownloadTask).where(
            DownloadTask.user_id == user_id
        ).order_by(desc(DownloadTask.created_at)).limit(limit)
        
        if status:
            status_map = {
                "queued": "pending",
                "downloading": "running",
                "completed": "completed",
                "failed": "failed",
            }
            db_status = status_map.get(status, status)
            stmt = stmt.where(DownloadTask.status == db_status)
        
        result = await session.execute(stmt)
        tasks = result.scalars().all()
        
        for task in tasks:
            status_map = {
                "pending": "queued",
                "running": "downloading",
                "completed": "completed",
                "failed": "failed",
            }
            
            items.append(BotDownloadJobItem(
                id=task.id,
                job_type="pt_download",
                title=getattr(task, "title", None) or f"下载任务 #{task.id}",
                status=status_map.get(task.status, task.status),
                progress=getattr(task, "progress", None),
                created_at=task.created_at,
                finished_at=getattr(task, "finished_at", None),
                error_message=getattr(task, "error_message", None),
            ))
    except ImportError:
        logger.debug("[bot-task] download task model not available")
    except Exception as e:
        logger.warning(f"[bot-task] query pt downloads failed: {e}")
    
    return items


async def _get_tts_jobs(
    session: AsyncSession,
    user_id: int,
    limit: int,
    status: Optional[str],
) -> list[BotDownloadJobItem]:
    """获取 TTS 任务"""
    items = []
    
    try:
        from app.models.tts_job import TTSJob
        
        stmt = select(TTSJob).where(
            TTSJob.user_id == user_id
        ).order_by(desc(TTSJob.created_at)).limit(limit)
        
        if status:
            stmt = stmt.where(TTSJob.status == status)
        
        result = await session.execute(stmt)
        jobs = result.scalars().all()
        
        for job in jobs:
            status_map = {
                "pending": "queued",
                "processing": "downloading",
                "completed": "completed",
                "failed": "failed",
            }
            
            items.append(BotDownloadJobItem(
                id=job.id,
                job_type="tts_job",
                title=getattr(job, "title", None) or f"TTS 任务 #{job.id}",
                status=status_map.get(job.status, job.status),
                progress=getattr(job, "progress", None),
                created_at=job.created_at,
                finished_at=getattr(job, "finished_at", None),
                error_message=getattr(job, "error_message", None),
            ))
    except ImportError:
        logger.debug("[bot-task] tts job model not available")
    except Exception as e:
        logger.warning(f"[bot-task] query tts jobs failed: {e}")
    
    return items


async def retry_job(
    session: AsyncSession,
    user: User,
    job_id: int,
    job_type: str,
) -> bool:
    """重试任务"""
    logger.info(f"[bot-task] retry job: type={job_type}, id={job_id}, user={user.id}")
    # TODO: 实现重试逻辑
    return True


async def cancel_job(
    session: AsyncSession,
    user: User,
    job_id: int,
    job_type: str,
) -> bool:
    """取消任务"""
    logger.info(f"[bot-task] cancel job: type={job_type}, id={job_id}, user={user.id}")
    # TODO: 实现取消逻辑
    return True
