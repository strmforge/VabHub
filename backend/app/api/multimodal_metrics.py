"""
多模态分析性能监控API
提供性能指标查询和统计功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from loguru import logger

from app.core.database import get_db
from app.modules.multimodal.metrics import MultimodalMetrics
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter()


@router.get("/metrics", response_model=BaseResponse)
async def get_metrics(
    operation: Optional[str] = Query(None, description="操作类型（video_analysis, audio_analysis, text_analysis, feature_fusion, similarity_calculation）"),
    db = Depends(get_db)
):
    """获取性能指标"""
    try:
        metrics = MultimodalMetrics.get_metrics(operation)
        return success_response(data=metrics, message="获取性能指标成功")
    except Exception as e:
        logger.error(f"获取性能指标失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取性能指标时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/metrics/summary", response_model=BaseResponse)
async def get_performance_summary(
    db = Depends(get_db)
):
    """获取性能摘要"""
    try:
        summary = MultimodalMetrics.get_performance_summary()
        return success_response(data=summary, message="获取性能摘要成功")
    except Exception as e:
        logger.error(f"获取性能摘要失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取性能摘要时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/metrics/cache", response_model=BaseResponse)
async def get_cache_stats(
    db = Depends(get_db)
):
    """获取缓存统计信息"""
    try:
        stats = MultimodalMetrics.get_cache_stats()
        return success_response(data=stats, message="获取缓存统计信息成功")
    except Exception as e:
        logger.error(f"获取缓存统计信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取缓存统计信息时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/metrics/timeseries", response_model=BaseResponse)
async def get_time_series(
    operation: str = Query(..., description="操作类型"),
    minutes: int = Query(60, ge=1, le=1440, description="时间范围（分钟，默认60分钟）"),
    db = Depends(get_db)
):
    """获取时间序列数据"""
    try:
        time_series = MultimodalMetrics.get_time_series(operation, minutes)
        return success_response(data=time_series, message="获取时间序列数据成功")
    except Exception as e:
        logger.error(f"获取时间序列数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取时间序列数据时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/metrics/reset", response_model=BaseResponse)
async def reset_metrics(
    db = Depends(get_db)
):
    """重置所有性能指标"""
    try:
        MultimodalMetrics.reset_metrics()
        return success_response(message="重置性能指标成功")
    except Exception as e:
        logger.error(f"重置性能指标失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"重置性能指标时发生错误: {str(e)}"
            ).model_dump()
        )

