"""
多模态分析优化API
提供缓存优化和并发优化功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List
from pydantic import BaseModel, Field
from loguru import logger

from app.core.database import get_db
from app.modules.multimodal.cache_optimizer import CacheOptimizer
from app.modules.multimodal.concurrency_optimizer import ConcurrencyOptimizer
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter()


class WarmupCacheRequest(BaseModel):
    """缓存预热请求"""
    file_paths: List[str] = Field(..., description="文件路径列表")
    operation: str = Field(default="video_analysis", description="操作类型（video_analysis, audio_analysis）")


@router.get("/cache/performance", response_model=BaseResponse)
async def analyze_cache_performance(
    db = Depends(get_db)
):
    """分析缓存性能"""
    try:
        optimizer = CacheOptimizer()
        analysis = await optimizer.analyze_cache_performance()
        return success_response(data=analysis, message="分析缓存性能成功")
    except Exception as e:
        logger.error(f"分析缓存性能失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"分析缓存性能时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/cache/optimize-ttl", response_model=BaseResponse)
async def optimize_cache_ttl(
    operation: str = Query(..., description="操作类型"),
    target_hit_rate: float = Query(0.8, ge=0.0, le=1.0, description="目标缓存命中率（0-1）"),
    db = Depends(get_db)
):
    """优化缓存TTL"""
    try:
        optimizer = CacheOptimizer()
        optimization = await optimizer.optimize_cache_ttl(operation, target_hit_rate)
        return success_response(data=optimization, message="优化缓存TTL成功")
    except Exception as e:
        logger.error(f"优化缓存TTL失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"优化缓存TTL时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/cache/warmup", response_model=BaseResponse)
async def warmup_cache(
    request: WarmupCacheRequest,
    db = Depends(get_db)
):
    """缓存预热"""
    try:
        optimizer = CacheOptimizer()
        result = await optimizer.warmup_cache(request.file_paths, request.operation)
        return success_response(data=result, message="缓存预热成功")
    except Exception as e:
        logger.error(f"缓存预热失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"缓存预热时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/concurrency/performance", response_model=BaseResponse)
async def analyze_concurrency_performance(
    operation: str = Query(..., description="操作类型"),
    db = Depends(get_db)
):
    """分析并发性能"""
    try:
        optimizer = ConcurrencyOptimizer()
        analysis = await optimizer.analyze_concurrency_performance(operation)
        return success_response(data=analysis, message="分析并发性能成功")
    except Exception as e:
        logger.error(f"分析并发性能失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"分析并发性能时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/concurrency/optimize", response_model=BaseResponse)
async def optimize_concurrency(
    operation: str = Query(..., description="操作类型"),
    target_avg_duration: float = Query(1.0, ge=0.1, le=10.0, description="目标平均响应时间（秒）"),
    db = Depends(get_db)
):
    """优化并发数"""
    try:
        optimizer = ConcurrencyOptimizer()
        optimization = await optimizer.optimize_concurrency(operation, target_avg_duration)
        return success_response(data=optimization, message="优化并发数成功")
    except Exception as e:
        logger.error(f"优化并发数失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"优化并发数时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/concurrency/monitor", response_model=BaseResponse)
async def monitor_concurrency(
    operation: str = Query(..., description="操作类型"),
    duration: int = Query(60, ge=10, le=300, description="监控时长（秒，10-300）"),
    db = Depends(get_db)
):
    """监控并发性能"""
    try:
        optimizer = ConcurrencyOptimizer()
        result = await optimizer.monitor_concurrency(operation, duration)
        return success_response(data=result, message="监控并发性能成功")
    except Exception as e:
        logger.error(f"监控并发性能失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"监控并发性能时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/concurrency/optimal", response_model=BaseResponse)
async def get_optimal_concurrency(
    operation: str = Query(..., description="操作类型"),
    db = Depends(get_db)
):
    """获取最优并发数"""
    try:
        optimizer = ConcurrencyOptimizer()
        optimal = await optimizer.get_optimal_concurrency(operation)
        return success_response(data={"operation": operation, "optimal_concurrency": optimal}, message="获取最优并发数成功")
    except Exception as e:
        logger.error(f"获取最优并发数失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取最优并发数时发生错误: {str(e)}"
            ).model_dump()
        )

