"""
订阅刷新API端点
提供刷新历史、状态监控、统计信息等功能
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, timedelta
from loguru import logger

from app.core.database import get_db
from app.modules.subscription.refresh_monitor import SubscriptionRefreshMonitor
from app.core.schemas import success_response, error_response

router = APIRouter(prefix="/subscription-refresh", tags=["订阅刷新"])


@router.get("/history")
async def get_refresh_history(
    subscription_id: Optional[int] = Query(None, description="订阅ID过滤"),
    status: Optional[str] = Query(None, description="状态过滤（running/success/failed/cancelled）"),
    trigger_type: Optional[str] = Query(None, description="触发类型过滤（auto/manual/scheduled）"),
    days: int = Query(30, ge=1, le=365, description="查询最近N天的记录"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取订阅刷新历史记录
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [
            {
                "id": 1,
                "subscription_id": 1,
                "subscription_title": "...",
                "status": "success",
                "trigger_type": "auto",
                "start_time": "2025-01-XX...",
                "end_time": "2025-01-XX...",
                "duration_ms": 1500,
                "results_count": 10,
                "downloaded_count": 5,
                ...
            },
            ...
        ],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        monitor = SubscriptionRefreshMonitor(db)
        
        start_date = datetime.utcnow() - timedelta(days=days)
        records = await monitor.get_refresh_history(
            subscription_id=subscription_id,
            status=status,
            trigger_type=trigger_type,
            start_date=start_date,
            limit=limit,
            offset=offset
        )
        
        # 转换为字典列表
        records_data = [
            {
                "id": r.id,
                "subscription_id": r.subscription_id,
                "subscription_title": r.subscription_title,
                "status": r.status,
                "trigger_type": r.trigger_type,
                "start_time": r.start_time.isoformat() if r.start_time else None,
                "end_time": r.end_time.isoformat() if r.end_time else None,
                "duration_ms": r.duration_ms,
                "results_count": r.results_count,
                "downloaded_count": r.downloaded_count,
                "skipped_count": r.skipped_count,
                "error_count": r.error_count,
                "error_message": r.error_message,
                "search_duration_ms": r.search_duration_ms,
                "download_duration_ms": r.download_duration_ms,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in records
        ]
        
        return success_response(
            data=records_data,
            message="获取刷新历史成功"
        )
    except Exception as e:
        logger.error(f"获取刷新历史失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取刷新历史失败: {str(e)}"
            ).model_dump()
        )


@router.get("/status")
async def get_refresh_status(
    subscription_id: Optional[int] = Query(None, description="订阅ID过滤"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取订阅刷新状态
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [
            {
                "subscription_id": 1,
                "status": "idle",
                "last_refresh_time": "2025-01-XX...",
                "next_refresh_time": "2025-01-XX...",
                "total_refreshes": 100,
                "total_successes": 95,
                "total_failures": 5,
                "success_rate": 95,
                "avg_duration_ms": 1500,
                ...
            },
            ...
        ],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        monitor = SubscriptionRefreshMonitor(db)
        statuses = await monitor.get_refresh_status(subscription_id=subscription_id)
        
        # 转换为字典列表
        statuses_data = [
            {
                "subscription_id": s.subscription_id,
                "status": s.status,
                "current_refresh_id": s.current_refresh_id,
                "last_refresh_time": s.last_refresh_time.isoformat() if s.last_refresh_time else None,
                "next_refresh_time": s.next_refresh_time.isoformat() if s.next_refresh_time else None,
                "last_success_time": s.last_success_time.isoformat() if s.last_success_time else None,
                "last_error_time": s.last_error_time.isoformat() if s.last_error_time else None,
                "consecutive_failures": s.consecutive_failures,
                "total_refreshes": s.total_refreshes,
                "total_successes": s.total_successes,
                "total_failures": s.total_failures,
                "success_rate": s.success_rate,
                "avg_duration_ms": s.avg_duration_ms,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None
            }
            for s in statuses
        ]
        
        return success_response(
            data=statuses_data,
            message="获取刷新状态成功"
        )
    except Exception as e:
        logger.error(f"获取刷新状态失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取刷新状态失败: {str(e)}"
            ).model_dump()
        )


@router.get("/statistics")
async def get_refresh_statistics(
    subscription_id: Optional[int] = Query(None, description="订阅ID过滤"),
    days: int = Query(30, ge=1, le=365, description="统计最近N天的数据"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取订阅刷新统计信息
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "total": 100,
            "success": 95,
            "failed": 5,
            "cancelled": 0,
            "success_rate": 95.0,
            "avg_duration_ms": 1500.5,
            "total_results": 1000,
            "total_downloaded": 500,
            "by_status": {...},
            "by_trigger_type": {...}
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        monitor = SubscriptionRefreshMonitor(db)
        
        start_date = datetime.utcnow() - timedelta(days=days)
        statistics = await monitor.get_refresh_statistics(
            subscription_id=subscription_id,
            start_date=start_date
        )
        
        return success_response(
            data=statistics,
            message="获取刷新统计成功"
        )
    except Exception as e:
        logger.error(f"获取刷新统计失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取刷新统计失败: {str(e)}"
            ).model_dump()
        )


@router.post("/cleanup")
async def cleanup_refresh_history(
    days: int = Query(30, ge=1, le=365, description="保留最近N天的记录"),
    db: AsyncSession = Depends(get_db)
):
    """
    清理旧的刷新历史记录
    
    返回统一响应格式：
    {
        "success": true,
        "message": "清理成功",
        "data": {
            "deleted_count": 100
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        monitor = SubscriptionRefreshMonitor(db)
        deleted_count = await monitor.cleanup_old_history(days=days)
        
        return success_response(
            data={"deleted_count": deleted_count},
            message=f"清理成功，删除了 {deleted_count} 条记录"
        )
    except Exception as e:
        logger.error(f"清理刷新历史失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"清理刷新历史失败: {str(e)}"
            ).model_dump()
        )

