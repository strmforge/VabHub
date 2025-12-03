"""
系统监控API
提供系统资源监控和API性能监控的接口
"""

from fastapi import APIRouter, Depends, Request, Query
from typing import Optional
from loguru import logger

from app.core.database import get_db
from app.modules.monitoring.system_monitor import get_system_monitor
from app.modules.monitoring.api_monitor import get_api_monitor
from app.core.schemas import BaseResponse, success_response, error_response
from fastapi import HTTPException, status as http_status

router = APIRouter(prefix="/monitoring", tags=["系统监控"])


@router.get("/system/resources", response_model=BaseResponse)
async def get_system_resources(db = Depends(get_db)):
    """
    获取系统资源使用情况
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "timestamp": "2025-01-XX...",
            "cpu": {...},
            "memory": {...},
            "disk": {...},
            "network": {...}
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        monitor = get_system_monitor(db)
        resources = await monitor.get_system_resources()
        
        return success_response(data=resources, message="获取成功")
    except Exception as e:
        logger.error(f"获取系统资源失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取系统资源失败: {str(e)}"
            ).model_dump()
        )


@router.get("/system/history", response_model=BaseResponse)
async def get_system_history(
    resource_type: Optional[str] = Query(None, description="资源类型: cpu, memory, disk, network, all"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    db = Depends(get_db)
):
    """
    获取系统资源历史记录
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "cpu": [...],
            "memory": [...],
            "disk": [...],
            "network": [...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        monitor = get_system_monitor(db)
        
        if resource_type == "cpu":
            history = {"cpu": monitor.get_cpu_history(limit)}
        elif resource_type == "memory":
            history = {"memory": monitor.get_memory_history(limit)}
        elif resource_type == "disk":
            history = {"disk": monitor.get_disk_history(limit)}
        elif resource_type == "network":
            history = {"network": monitor.get_network_history(limit)}
        else:
            history = monitor.get_all_history(limit)
        
        return success_response(data=history, message="获取成功")
    except Exception as e:
        logger.error(f"获取系统资源历史失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取系统资源历史失败: {str(e)}"
            ).model_dump()
        )


@router.get("/system/statistics", response_model=BaseResponse)
async def get_system_statistics(db = Depends(get_db)):
    """
    获取系统资源统计信息
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "cpu": {"avg": 10.5, "min": 5.0, "max": 20.0},
            "memory": {"avg": 50.0, "min": 30.0, "max": 70.0},
            "disk": {"avg": 60.0, "min": 55.0, "max": 65.0}
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        monitor = get_system_monitor(db)
        statistics = monitor.get_statistics()
        
        return success_response(data=statistics, message="获取成功")
    except Exception as e:
        logger.error(f"获取系统资源统计失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取系统资源统计失败: {str(e)}"
            ).model_dump()
        )


@router.get("/api/performance", response_model=BaseResponse)
async def get_api_performance(
    request: Request,
    endpoint: Optional[str] = Query(None, description="端点路径（可选，用于过滤）")
):
    """
    获取API性能指标
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "timestamp": "2025-01-XX...",
            "summary": {...},
            "endpoints": {...}
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.core.middleware import PerformanceMonitoringMiddleware
        
        # 获取性能监控中间件
        middleware = None
        if hasattr(request.app.state, 'performance_middleware'):
            middleware = request.app.state.performance_middleware
        elif PerformanceMonitoringMiddleware._instance:
            middleware = PerformanceMonitoringMiddleware._instance
        
        api_monitor = get_api_monitor()
        metrics = api_monitor.get_performance_metrics(middleware, endpoint)
        
        return success_response(data=metrics, message="获取成功")
    except Exception as e:
        logger.error(f"获取API性能指标失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取API性能指标失败: {str(e)}"
            ).model_dump()
        )


@router.get("/api/history", response_model=BaseResponse)
async def get_api_history(
    endpoint: Optional[str] = Query(None, description="端点路径（可选）"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量")
):
    """
    获取API性能历史记录
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "response_times": {...},
            "errors": [...],
            "request_counts": {...}
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        api_monitor = get_api_monitor()
        
        history = {
            "response_times": api_monitor.get_response_time_history(endpoint, limit),
            "errors": api_monitor.get_error_history(limit),
            "request_counts": api_monitor.get_request_count_history(endpoint, limit)
        }
        
        return success_response(data=history, message="获取成功")
    except Exception as e:
        logger.error(f"获取API性能历史失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取API性能历史失败: {str(e)}"
            ).model_dump()
        )


@router.get("/api/slow-endpoints", response_model=BaseResponse)
async def get_slow_endpoints(
    threshold: float = Query(1.0, ge=0.1, description="响应时间阈值（秒）"),
    limit: int = Query(10, ge=1, le=50, description="返回数量")
):
    """
    获取慢端点列表
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [
            {
                "endpoint": "/api/search",
                "avg_response_time": 1.5,
                "count": 100,
                "timestamp": "2025-01-XX..."
            },
            ...
        ],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        api_monitor = get_api_monitor()
        slow_endpoints = api_monitor.get_slow_endpoints(threshold, limit)
        
        return success_response(data=slow_endpoints, message="获取成功")
    except Exception as e:
        logger.error(f"获取慢端点列表失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取慢端点列表失败: {str(e)}"
            ).model_dump()
        )


@router.get("/api/error-endpoints", response_model=BaseResponse)
async def get_error_endpoints(
    limit: int = Query(10, ge=1, le=50, description="返回数量")
):
    """
    获取错误端点列表
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [
            {
                "timestamp": "2025-01-XX...",
                "error_count": 5,
                "error_rate": 0.05
            },
            ...
        ],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        api_monitor = get_api_monitor()
        error_endpoints = api_monitor.get_error_endpoints(limit)
        
        return success_response(data=error_endpoints, message="获取成功")
    except Exception as e:
        logger.error(f"获取错误端点列表失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取错误端点列表失败: {str(e)}"
            ).model_dump()
        )

