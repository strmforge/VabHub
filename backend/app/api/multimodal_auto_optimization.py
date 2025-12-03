"""
多模态分析自动化优化API
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from typing import Optional, Dict, Any
from loguru import logger
from pydantic import BaseModel

from app.core.database import get_db
from app.modules.multimodal.auto_optimizer import AutoOptimizer
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter()


class OptimizationConfig(BaseModel):
    """优化配置"""
    cache_ttl: Optional[Dict[str, Any]] = None
    concurrency: Optional[Dict[str, Any]] = None


@router.post("/optimize/all", response_model=BaseResponse)
async def optimize_all(
    db = Depends(get_db)
):
    """优化所有操作"""
    try:
        optimizer = AutoOptimizer(db)
        results = await optimizer.optimize_all()
        return success_response(data=results, message="优化完成")
    except Exception as e:
        logger.error(f"优化所有操作失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"优化所有操作时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/optimize/cache-ttl", response_model=BaseResponse)
async def optimize_cache_ttl(
    operation: str = Query(..., description="操作类型"),
    db = Depends(get_db)
):
    """优化缓存TTL"""
    try:
        optimizer = AutoOptimizer(db)
        result = await optimizer.optimize_cache_ttl(operation)
        if result:
            return success_response(data=result, message="优化缓存TTL成功")
        else:
            return success_response(data=None, message="无需优化")
    except Exception as e:
        logger.error(f"优化缓存TTL失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"优化缓存TTL时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/optimize/concurrency", response_model=BaseResponse)
async def optimize_concurrency(
    operation: str = Query(..., description="操作类型"),
    db = Depends(get_db)
):
    """优化并发数"""
    try:
        optimizer = AutoOptimizer(db)
        result = await optimizer.optimize_concurrency(operation)
        if result:
            return success_response(data=result, message="优化并发数成功")
        else:
            return success_response(data=None, message="无需优化")
    except Exception as e:
        logger.error(f"优化并发数失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"优化并发数时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/config", response_model=BaseResponse)
async def get_config(
    db = Depends(get_db)
):
    """获取当前配置"""
    try:
        optimizer = AutoOptimizer(db)
        config = optimizer.get_current_config()
        return success_response(data=config, message="获取配置成功")
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取配置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/config", response_model=BaseResponse)
async def update_config(
    config: OptimizationConfig,
    db = Depends(get_db)
):
    """更新配置"""
    try:
        optimizer = AutoOptimizer(db)
        optimizer.update_config(config.model_dump(exclude_none=True))
        return success_response(message="更新配置成功")
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新配置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/optimization/history", response_model=BaseResponse)
async def get_optimization_history(
    operation: Optional[str] = Query(None, description="操作类型"),
    optimization_type: Optional[str] = Query(None, description="优化类型"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    db = Depends(get_db)
):
    """获取优化历史"""
    try:
        from sqlalchemy import select, and_, desc
        from app.models.multimodal_metrics import MultimodalOptimizationHistory
        
        query = select(MultimodalOptimizationHistory)
        
        conditions = []
        if operation:
            conditions.append(MultimodalOptimizationHistory.operation == operation)
        if optimization_type:
            conditions.append(MultimodalOptimizationHistory.optimization_type == optimization_type)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(MultimodalOptimizationHistory.timestamp)).limit(limit)
        
        result = await db.execute(query)
        history = result.scalars().all()
        
        # 转换为字典
        history_list = []
        for item in history:
            history_list.append({
                "id": item.id,
                "operation": item.operation,
                "optimization_type": item.optimization_type,
                "old_value": item.old_value,
                "new_value": item.new_value,
                "reason": item.reason,
                "timestamp": item.timestamp.isoformat(),
                "improvement": item.improvement,
                "before_metrics": item.before_metrics,
                "after_metrics": item.after_metrics,
                "metadata": item.extra_metadata
            })
        
        return success_response(data=history_list, message="获取优化历史成功")
    except Exception as e:
        logger.error(f"获取优化历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取优化历史时发生错误: {str(e)}"
            ).model_dump()
        )

