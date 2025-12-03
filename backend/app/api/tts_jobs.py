"""
TTS Jobs Dev API

提供 TTS Job 管理的 Dev 接口
"""

from fastapi import APIRouter, Depends, HTTPException, Path as PathParam, Query
from typing import Optional, List, Dict, Any
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.config import settings
from app.core.database import get_db
from app.models.tts_job import TTSJob
from app.models.ebook import EBook
from app.schemas.tts import TTSJobResponse, RunBatchJobsRequest, TTSBatchJobsResponse
from app.modules.tts.job_service import (
    create_job_for_ebook,
    run_job,
    find_next_queued_job
)
from app.modules.tts.job_runner import run_batch_jobs

router = APIRouter()


@router.post("/enqueue-for-work/{ebook_id}", response_model=TTSJobResponse, summary="为作品创建 TTS Job")
async def enqueue_job_for_work(
    ebook_id: int = PathParam(..., description="电子书 ID"),
    db: AsyncSession = Depends(get_db)
) -> TTSJobResponse:
    """
    为指定作品创建 TTS Job（入队）
    
    此接口仅在 Dev 模式下可用。
    
    Args:
        ebook_id: 电子书 ID
        db: 数据库会话
    
    Returns:
        TTSJobResponse: 创建的 Job 信息
    """
    # Dev guard
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="此接口仅在 DEBUG 模式下可用"
        )
    
    try:
        job = await create_job_for_ebook(
            db=db,
            ebook_id=ebook_id,
            created_by="dev-api"
        )
        await db.commit()
        
        return TTSJobResponse.model_validate(job)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to create TTS job for ebook {ebook_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"创建 Job 失败: {str(e)}")


@router.post("/run-next", summary="执行下一个待处理的 Job")
async def run_next_job(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    执行下一个待处理的 TTS Job
    
    此接口仅在 Dev 模式下可用。
    
    Args:
        db: 数据库会话
    
    Returns:
        Dict[str, Any]: 执行结果
    """
    # Dev guard
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="此接口仅在 DEBUG 模式下可用"
        )
    
    # 查找下一个待处理的 Job
    job = await find_next_queued_job(db)
    
    if not job:
        return {
            "success": False,
            "reason": "no_queued_job",
            "message": "没有待处理的 Job"
        }
    
    try:
        # 执行 Job
        updated_job = await run_job(
            db=db,
            settings=settings,
            job_id=job.id
        )
        await db.commit()
        
        return {
            "success": True,
            "job": TTSJobResponse.model_validate(updated_job)
        }
    except Exception as e:
        logger.exception(f"Failed to run TTS job {job.id}: {e}")
        await db.rollback()
        return {
            "success": False,
            "reason": "execution_error",
            "message": str(e)
        }


@router.get("", response_model=List[TTSJobResponse], summary="获取 TTS Job 列表")
async def list_jobs(
    status: Optional[str] = Query(None, description="按状态筛选"),
    ebook_id: Optional[int] = Query(None, description="按作品 ID 筛选"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    db: AsyncSession = Depends(get_db)
) -> List[TTSJobResponse]:
    """
    获取 TTS Job 列表
    
    此接口仅在 Dev 模式下可用。
    
    Args:
        status: 状态筛选（可选）
        ebook_id: 作品 ID 筛选（可选）
        limit: 返回数量限制
        db: 数据库会话
    
    Returns:
        List[TTSJobResponse]: Job 列表
    """
    # Dev guard
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="此接口仅在 DEBUG 模式下可用"
        )
    
    query = select(TTSJob)
    
    # 应用筛选条件
    if status:
        query = query.where(TTSJob.status == status)
    if ebook_id:
        query = query.where(TTSJob.ebook_id == ebook_id)
    
    # 按创建时间倒序排列
    query = query.order_by(desc(TTSJob.requested_at)).limit(limit)
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return [TTSJobResponse.model_validate(job) for job in jobs]


@router.get("/{job_id}", response_model=TTSJobResponse, summary="获取 TTS Job 详情")
async def get_job(
    job_id: int = PathParam(..., description="Job ID"),
    db: AsyncSession = Depends(get_db)
) -> TTSJobResponse:
    """
    获取 TTS Job 详情
    
    此接口仅在 Dev 模式下可用。
    
    Args:
        job_id: Job ID
        db: 数据库会话
    
    Returns:
        TTSJobResponse: Job 详情
    """
    # Dev guard
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="此接口仅在 DEBUG 模式下可用"
        )
    
    result = await db.execute(select(TTSJob).where(TTSJob.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail=f"TTSJob {job_id} not found")
    
    return TTSJobResponse.model_validate(job)


@router.post("/run-batch", response_model=TTSBatchJobsResponse, summary="批量执行 TTS Job")
async def run_batch_jobs_api(
    payload: RunBatchJobsRequest,
    db: AsyncSession = Depends(get_db)
) -> TTSBatchJobsResponse:
    """
    批量执行 TTS Job
    
    此接口仅在 Dev 模式下可用。
    
    Args:
        payload: 批量执行请求（包含 max_jobs）
        db: 数据库会话
        settings: 应用配置
    
    Returns:
        TTSBatchJobsResponse: 批量执行结果
    """
    # Dev guard
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="此接口仅在 DEBUG 模式下可用"
        )
    
    try:
        result = await run_batch_jobs(
            db=db,
            settings=settings,
            max_jobs=payload.max_jobs
        )
        
        # 生成人类可读的消息
        message_parts = []
        if result.total_jobs == 0:
            message = "没有待处理的 Job"
        else:
            message_parts.append(f"本次执行 {result.run_jobs} 个 Job")
            if result.succeeded_jobs > 0:
                message_parts.append(f"成功 {result.succeeded_jobs} 个")
            if result.partial_jobs > 0:
                message_parts.append(f"部分完成 {result.partial_jobs} 个")
            if result.failed_jobs > 0:
                message_parts.append(f"失败 {result.failed_jobs} 个")
            message = "，".join(message_parts)
        
        return TTSBatchJobsResponse(
            total_jobs=result.total_jobs,
            run_jobs=result.run_jobs,
            succeeded_jobs=result.succeeded_jobs,
            partial_jobs=result.partial_jobs,
            failed_jobs=result.failed_jobs,
            last_job_id=result.last_job_id,
            message=message
        )
    except Exception as e:
        logger.exception(f"批量执行 TTS Job 失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"批量执行失败: {str(e)}"
        )