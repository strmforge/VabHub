"""
性能监控API
提供性能指标查询接口
"""

from fastapi import APIRouter, Query, Request
from typing import Optional
from loguru import logger

from app.core.schemas import BaseResponse, success_response

router = APIRouter(prefix="/performance", tags=["performance"])


def get_performance_middleware(request: Request):
    """从应用实例获取性能监控中间件"""
    from app.core.middleware import PerformanceMonitoringMiddleware
    
    # 方法1: 从app.state获取
    if hasattr(request.app.state, 'performance_middleware'):
        return request.app.state.performance_middleware
    
    # 方法2: 从类变量获取（单例）
    if PerformanceMonitoringMiddleware._instance:
        return PerformanceMonitoringMiddleware._instance
    
    return None


@router.get("/metrics", response_model=BaseResponse)
async def get_performance_metrics(
    request: Request,
    path: Optional[str] = Query(None, description="API路径"),
    method: Optional[str] = Query(None, description="HTTP方法")
):
    """
    获取性能指标
    
    Args:
        path: API路径（可选）
        method: HTTP方法（可选）
    
    Returns:
        性能指标数据
    """
    try:
        middleware = get_performance_middleware(request)
        
        if not middleware:
            # 如果找不到中间件，返回空数据
            return success_response(
                data={
                    "summary": {
                        "total_requests": 0,
                        "total_errors": 0,
                        "error_rate": 0,
                        "avg_response_time": 0
                    },
                    "endpoints": {}
                },
                message="性能监控中间件未启用"
            )
        
        if path and method:
            stats = middleware.get_metrics(path=path, method=method)
            return success_response(
                data=stats,
                message="获取性能指标成功"
            )
        else:
            summary = middleware.get_summary()
            all_stats = middleware.get_metrics()
            
            return success_response(
                data={
                    "summary": summary,
                    "endpoints": all_stats
                },
                message="获取性能指标成功"
            )
            
    except Exception as e:
        logger.error(f"获取性能指标失败: {e}", exc_info=True)
        from app.core.schemas import error_response
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取性能指标失败: {str(e)}"
            ).model_dump()
        )


@router.post("/metrics/reset", response_model=BaseResponse)
async def reset_performance_metrics(request: Request):
    """
    重置性能指标
    
    Returns:
        重置结果
    """
    try:
        middleware = get_performance_middleware(request)
        
        if not middleware:
            return success_response(
                data={"status": "not_available"},
                message="性能监控中间件未启用"
            )
        
        # 重置指标
        middleware._metrics = {
            "request_count": {},
            "response_times": {},
            "error_count": {},
            "status_codes": {}
        }
        
        return success_response(
            data={"status": "reset"},
            message="性能指标已重置"
        )
        
    except Exception as e:
        logger.error(f"重置性能指标失败: {e}", exc_info=True)
        from app.core.schemas import error_response
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"重置性能指标失败: {str(e)}"
            ).model_dump()
        )
