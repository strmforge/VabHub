"""
用户版 TTS Flow API

提供用户视角的 TTS 有声书生成接口
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from loguru import logger

from app.core.config import settings
from app.core.deps import DbSessionDep
from app.schemas.tts import (
    UserWorkTTSStatus,
    UserTTSJobEnqueueResponse,
    UserTTSJobOverviewItem,
    UserTTSJobStatus
)
from app.models.ebook import EBook
from app.models.tts_job import TTSJob
from app.models.audiobook import AudiobookFile
from app.modules.tts.job_service import create_job_for_ebook

router = APIRouter()


def _check_tts_enabled():
    """检查 TTS 是否启用"""
    if not settings.SMART_TTS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TTS is disabled"
        )


@router.post("/jobs/enqueue-for-work/{ebook_id}", response_model=UserTTSJobEnqueueResponse)
async def enqueue_tts_job_for_work(
    ebook_id: int,
    db: DbSessionDep
):
    """
    为用户作品创建 TTS Job
    
    如果该作品已有活跃的 Job（queued/running/partial），则复用现有 Job
    """
    _check_tts_enabled()
    
    # 检查 EBook 是否存在
    ebook_result = await db.execute(select(EBook).where(EBook.id == ebook_id))
    ebook = ebook_result.scalar_one_or_none()
    
    if not ebook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"EBook {ebook_id} not found"
        )
    
    # 检查是否存在活跃的 Job
    active_statuses = ["queued", "running", "partial"]
    existing_job_result = await db.execute(
        select(TTSJob)
        .where(TTSJob.ebook_id == ebook_id)
        .where(TTSJob.status.in_(active_statuses))
        .order_by(desc(TTSJob.requested_at))
        .limit(1)
    )
    existing_job = existing_job_result.scalar_one_or_none()
    
    if existing_job:
        # 复用现有 Job
        logger.info(f"Reusing existing TTS job {existing_job.id} for ebook {ebook_id}")
        return UserTTSJobEnqueueResponse(
            success=True,
            job_id=existing_job.id,
            ebook_id=ebook_id,
            status=existing_job.status,
            message="已有活跃的 TTS 任务，将复用现有任务",
            already_exists=True
        )
    
    # 创建新 Job
    try:
        job = await create_job_for_ebook(
            db=db,
            ebook_id=ebook_id,
            created_by="user-flow",
            strategy=None  # 使用默认策略
        )
        await db.commit()
        
        logger.info(f"Created new TTS job {job.id} for ebook {ebook_id} via user flow")
        
        return UserTTSJobEnqueueResponse(
            success=True,
            job_id=job.id,
            ebook_id=ebook_id,
            status=job.status,
            message="已创建 TTS 任务，等待执行",
            already_exists=False
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create TTS job for ebook {ebook_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create TTS job"
        )


@router.get("/jobs/status/by-ebook/{ebook_id}", response_model=UserWorkTTSStatus)
async def get_tts_status_by_ebook(
    ebook_id: int,
    db: DbSessionDep
):
    """
    查询指定作品的 TTS 状态
    
    用于 WorkDetail 页面显示
    """
    # 检查 EBook 是否存在
    ebook_result = await db.execute(select(EBook).where(EBook.id == ebook_id))
    ebook = ebook_result.scalar_one_or_none()
    
    if not ebook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"EBook {ebook_id} not found"
        )
    
    # 检查是否存在 TTS 生成的有声书
    audiobook_result = await db.execute(
        select(func.count(AudiobookFile.id))
        .where(AudiobookFile.ebook_id == ebook_id)
        .where(AudiobookFile.is_tts_generated == True)
    )
    has_tts_audiobook = (audiobook_result.scalar() or 0) > 0
    
    # 查询最近的 TTSJob
    job_result = await db.execute(
        select(TTSJob)
        .where(TTSJob.ebook_id == ebook_id)
        .order_by(desc(TTSJob.requested_at))
        .limit(1)
    )
    last_job = job_result.scalar_one_or_none()
    
    # 组装响应
    status_obj = UserWorkTTSStatus(
        ebook_id=ebook_id,
        has_tts_audiobook=has_tts_audiobook
    )
    
    if last_job:
        status_obj.last_job_status = UserTTSJobStatus(last_job.status) if last_job.status in ["queued", "running", "partial", "success", "failed"] else None
        status_obj.last_job_requested_at = last_job.requested_at
        status_obj.last_job_finished_at = last_job.finished_at
        
        # 从 last_error 或 details 中提取消息
        if last_job.last_error:
            status_obj.last_job_message = last_job.last_error
        elif last_job.details and isinstance(last_job.details, dict):
            tts_details = last_job.details.get("tts", {})
            if isinstance(tts_details, dict):
                message_parts = []
                if tts_details.get("generated_chapters"):
                    message_parts.append(f"成功 {tts_details['generated_chapters']} 章")
                if tts_details.get("total_chapters"):
                    message_parts.append(f"共 {tts_details['total_chapters']} 章")
                if tts_details.get("rate_limited_chapters", 0) > 0:
                    message_parts.append(f"因限流暂停，可从第 {tts_details.get('resume_from_chapter_index', '?')} 章继续")
                if message_parts:
                    status_obj.last_job_message = "生成完成：" + "，".join(message_parts)
        
        # 章节统计
        if last_job.details and isinstance(last_job.details, dict):
            tts_details = last_job.details.get("tts", {})
            if isinstance(tts_details, dict):
                status_obj.total_chapters = tts_details.get("total_chapters")
                status_obj.generated_chapters = tts_details.get("generated_chapters")
    
    return status_obj


@router.get("/jobs/overview", response_model=List[UserTTSJobOverviewItem])
async def get_tts_jobs_overview(
    db: DbSessionDep,
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态过滤，逗号分隔，如: queued,running,partial")
):
    """
    获取用户版 TTS Job 概览列表
    
    用于 TTS 有声书中心页面
    """
    # 解析状态过滤
    statuses = None
    if status_filter:
        statuses = [s.strip() for s in status_filter.split(",") if s.strip()]
    else:
        # 默认只显示活跃状态
        statuses = ["queued", "running", "partial"]
    
    # 查询 TTSJob
    query = select(TTSJob).order_by(desc(TTSJob.requested_at)).limit(limit)
    
    if statuses:
        query = query.where(TTSJob.status.in_(statuses))
    
    jobs_result = await db.execute(query)
    jobs = jobs_result.scalars().all()
    
    if not jobs:
        return []
    
    # 批量查询 EBook（避免 N+1）
    ebook_ids = [job.ebook_id for job in jobs]
    ebooks_result = await db.execute(
        select(EBook).where(EBook.id.in_(ebook_ids))
    )
    ebooks = {ebook.id: ebook for ebook in ebooks_result.scalars().all()}
    
    # 组装响应
    overview_items = []
    for job in jobs:
        ebook = ebooks.get(job.ebook_id)
        if not ebook:
            continue
        
        # 提取进度信息
        progress = None
        if job.details and isinstance(job.details, dict):
            tts_details = job.details.get("tts", {})
            if isinstance(tts_details, dict):
                progress = {
                    "generated_chapters": tts_details.get("generated_chapters"),
                    "total_chapters": tts_details.get("total_chapters")
                }
        
        # 提取消息
        last_message = None
        if job.last_error:
            last_message = job.last_error
        elif job.details and isinstance(job.details, dict):
            tts_details = job.details.get("tts", {})
            if isinstance(tts_details, dict):
                message_parts = []
                if tts_details.get("generated_chapters"):
                    message_parts.append(f"成功 {tts_details['generated_chapters']} 章")
                if tts_details.get("total_chapters"):
                    message_parts.append(f"共 {tts_details['total_chapters']} 章")
                if message_parts:
                    last_message = "，".join(message_parts)
        
        overview_items.append(
            UserTTSJobOverviewItem(
                job_id=job.id,
                ebook_id=job.ebook_id,
                ebook_title=ebook.title,
                ebook_author=ebook.author,
                status=job.status,
                requested_at=job.requested_at,
                finished_at=job.finished_at,
                progress=progress,
                last_message=last_message
            )
        )
    
    return overview_items

