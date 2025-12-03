"""
多模态分析历史数据和告警API
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from datetime import datetime, timedelta
from loguru import logger

from app.core.database import get_db
from app.modules.multimodal.metrics_storage import MetricsStorage
from app.modules.multimodal.alert_system import AlertSystem
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter()


@router.get("/history/metrics", response_model=BaseResponse)
async def get_history_metrics(
    operation: Optional[str] = Query(None, description="操作类型"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(1000, ge=1, le=10000, description="限制数量"),
    db = Depends(get_db)
):
    """获取历史性能指标"""
    try:
        storage = MetricsStorage(db)
        metrics = await storage.get_metrics(
            operation=operation,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        # 转换为字典
        metrics_list = []
        for metric in metrics:
            metrics_list.append({
                "id": metric.id,
                "operation": metric.operation,
                "timestamp": metric.timestamp.isoformat(),
                "cache_hit": metric.cache_hit,
                "duration": metric.duration,
                "error": metric.error,
                "concurrent": metric.concurrent,
                "metadata": metric.extra_metadata
            })
        
        return success_response(data=metrics_list, message="获取历史性能指标成功")
    except Exception as e:
        logger.error(f"获取历史性能指标失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取历史性能指标时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/history/statistics", response_model=BaseResponse)
async def get_history_statistics(
    operation: Optional[str] = Query(None, description="操作类型"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    db = Depends(get_db)
):
    """获取历史性能指标统计"""
    try:
        storage = MetricsStorage(db)
        statistics = await storage.get_metrics_statistics(
            operation=operation,
            start_time=start_time,
            end_time=end_time
        )
        return success_response(data=statistics, message="获取历史性能指标统计成功")
    except Exception as e:
        logger.error(f"获取历史性能指标统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取历史性能指标统计时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/alerts", response_model=BaseResponse)
async def get_alerts(
    operation: Optional[str] = Query(None, description="操作类型"),
    alert_type: Optional[str] = Query(None, description="告警类型"),
    resolved: Optional[bool] = Query(None, description="是否已解决"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    db = Depends(get_db)
):
    """获取告警列表"""
    try:
        alert_system = AlertSystem(db)
        alerts = await alert_system.get_alerts(
            operation=operation,
            alert_type=alert_type,
            resolved=resolved,
            limit=limit
        )
        
        # 转换为字典
        alerts_list = []
        for alert in alerts:
            alerts_list.append({
                "id": alert.id,
                "operation": alert.operation,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "threshold": alert.threshold,
                "actual_value": alert.actual_value,
                "timestamp": alert.timestamp.isoformat(),
                "resolved": alert.resolved,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                "resolved_by": alert.resolved_by,
                "metadata": alert.extra_metadata
            })
        
        return success_response(data=alerts_list, message="获取告警列表成功")
    except Exception as e:
        logger.error(f"获取告警列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取告警列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/alerts/check", response_model=BaseResponse)
async def check_alerts(
    operation: Optional[str] = Query(None, description="操作类型"),
    time_window: int = Query(300, ge=60, le=3600, description="时间窗口（秒）"),
    db = Depends(get_db)
):
    """检查告警"""
    try:
        alert_system = AlertSystem(db)
        alerts = await alert_system.check_alerts(
            operation=operation,
            time_window=time_window
        )
        
        # 转换为字典
        alerts_list = []
        for alert in alerts:
            alerts_list.append({
                "id": alert.id,
                "operation": alert.operation,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "threshold": alert.threshold,
                "actual_value": alert.actual_value,
                "timestamp": alert.timestamp.isoformat()
            })
        
        return success_response(data=alerts_list, message=f"检查告警成功，发现{len(alerts_list)}个告警")
    except Exception as e:
        logger.error(f"检查告警失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"检查告警时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/alerts/{alert_id}/resolve", response_model=BaseResponse)
async def resolve_alert(
    alert_id: int,
    resolved_by: str = Query("system", description="解决人"),
    db = Depends(get_db)
):
    """解决告警"""
    try:
        alert_system = AlertSystem(db)
        success = await alert_system.resolve_alert(alert_id, resolved_by)
        
        if success:
            return success_response(message="告警已解决")
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message="告警不存在"
                ).model_dump()
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解决告警失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"解决告警时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/history/cleanup", response_model=BaseResponse)
async def cleanup_history(
    days: int = Query(30, ge=1, le=365, description="保留天数"),
    db = Depends(get_db)
):
    """清理旧历史数据"""
    try:
        storage = MetricsStorage(db)
        count = await storage.cleanup_old_metrics(days)
        return success_response(data={"cleaned_count": count}, message=f"清理了{count}条旧历史数据")
    except Exception as e:
        logger.error(f"清理旧历史数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"清理旧历史数据时发生错误: {str(e)}"
            ).model_dump()
        )

