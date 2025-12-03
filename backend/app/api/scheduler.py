"""
定时任务管理API
使用统一响应模型
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Dict, Optional
from pydantic import BaseModel
from loguru import logger

from app.core.scheduler import get_scheduler
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.scheduler.monitor import SchedulerMonitor
from app.core.schemas import (
    BaseResponse,
    NotFoundResponse,
    success_response,
    error_response
)

router = APIRouter()


class JobResponse(BaseModel):
    """任务响应"""
    id: str
    name: str
    next_run_time: str | None
    trigger: str


@router.get("/jobs", response_model=BaseResponse)
async def list_jobs(
    status: Optional[str] = Query(None, description="任务状态过滤"),
    enabled: Optional[bool] = Query(None, description="是否启用"),
    task_type: Optional[str] = Query(None, description="任务类型过滤"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有定时任务（包含数据库中的详细信息）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [JobResponse, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        # 同步任务到数据库
        monitor = SchedulerMonitor(db)
        await monitor.sync_tasks()
        
        # 从数据库获取任务列表
        tasks = await monitor.get_tasks(status=status, enabled=enabled, task_type=task_type)
        
        # 格式化任务数据
        job_list = []
        for task in tasks:
            job_list.append({
                "id": task.job_id,
                "name": task.name,
                "task_type": task.task_type,
                "status": task.status,
                "trigger_type": task.trigger_type,
                "trigger_config": task.trigger_config,
                "next_run_time": task.next_run_time.isoformat() if task.next_run_time else None,
                "last_run_time": task.last_run_time.isoformat() if task.last_run_time else None,
                "run_count": task.run_count,
                "success_count": task.success_count,
                "fail_count": task.fail_count,
                "enabled": task.enabled,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat()
            })
        
        return success_response(data=job_list, message="获取成功")
    except Exception as e:
        logger.error(f"获取定时任务列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取定时任务列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/jobs/{job_id}", response_model=BaseResponse)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取任务详情（包含统计信息）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": JobResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        monitor = SchedulerMonitor(db)
        statistics = await monitor.get_task_statistics(job_id)
        
        if not statistics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"任务不存在 (ID: {job_id})"
                ).model_dump()
            )
        
        return success_response(data=statistics, message="获取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取任务详情时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/jobs/{job_id}/run", response_model=BaseResponse)
async def run_job(job_id: str):
    """
    立即执行任务
    
    返回统一响应格式：
    {
        "success": true,
        "message": "任务执行成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        scheduler = get_scheduler()
        job = scheduler.scheduler.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"任务不存在 (ID: {job_id})"
                ).model_dump()
            )
        
        # 立即执行任务
        await job.func()
        return success_response(message=f"任务 {job_id} 执行成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"任务执行失败: {str(e)}"
            ).model_dump()
        )


@router.delete("/jobs/{job_id}", response_model=BaseResponse)
async def remove_job(job_id: str):
    """
    移除任务
    
    返回统一响应格式：
    {
        "success": true,
        "message": "任务已移除",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        scheduler = get_scheduler()
        job = scheduler.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"任务不存在 (ID: {job_id})"
                ).model_dump()
            )
        
        scheduler.remove_job(job_id)
        return success_response(message=f"任务 {job_id} 已移除")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移除任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"移除任务时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/jobs/{job_id}/executions", response_model=BaseResponse)
async def get_job_executions(
    job_id: str,
    status: Optional[str] = Query(None, description="执行状态过滤"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数限制"),
    db: AsyncSession = Depends(get_db)
):
    """获取任务执行历史"""
    try:
        monitor = SchedulerMonitor(db)
        executions = await monitor.get_execution_history(job_id=job_id, status=status, limit=limit)
        
        return success_response(
            data=[{
                "id": e.id,
                "job_id": e.job_id,
                "status": e.status,
                "started_at": e.started_at.isoformat(),
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "duration": e.duration,
                "result": e.result,
                "error_message": e.error_message
            } for e in executions],
            message="获取执行历史成功"
        )
    except Exception as e:
        logger.error(f"获取任务执行历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取任务执行历史时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/statistics", response_model=BaseResponse)
async def get_scheduler_statistics(
    db: AsyncSession = Depends(get_db)
):
    """获取调度器统计信息"""
    try:
        monitor = SchedulerMonitor(db)
        statistics = await monitor.get_overall_statistics()
        
        return success_response(data=statistics, message="获取统计信息成功")
    except Exception as e:
        logger.error(f"获取调度器统计信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取调度器统计信息时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/sync", response_model=BaseResponse)
async def sync_tasks(
    db: AsyncSession = Depends(get_db)
):
    """同步任务到数据库"""
    try:
        monitor = SchedulerMonitor(db)
        await monitor.sync_tasks()
        
        return success_response(message="同步任务成功")
    except Exception as e:
        logger.error(f"同步任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"同步任务时发生错误: {str(e)}"
            ).model_dump()
        )

