"""
性能监控中间件
记录API响应时间、错误率等指标
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from collections import defaultdict
from datetime import datetime, timedelta
import json

from app.core.database import AsyncSessionLocal
from sqlalchemy import text


class PerformanceMetrics:
    """性能指标收集器"""
    
    def __init__(self):
        self.request_count = defaultdict(int)
        self.response_times = defaultdict(list)
        self.error_count = defaultdict(int)
        self.status_codes = defaultdict(int)
        self._lock = None  # 单线程环境，不需要锁
    
    def record_request(self, path: str, method: str, duration: float, status_code: int):
        """记录请求指标"""
        key = f"{method} {path}"
        self.request_count[key] += 1
        self.response_times[key].append(duration)
        self.status_codes[status_code] += 1
        
        # 只保留最近1000条记录
        if len(self.response_times[key]) > 1000:
            self.response_times[key] = self.response_times[key][-1000:]
        
        # 记录错误
        if status_code >= 400:
            self.error_count[key] += 1
    
    def get_stats(self, path: str = None, method: str = None) -> dict:
        """获取统计信息"""
        if path and method:
            key = f"{method} {path}"
            if key not in self.response_times:
                return {}
            
            times = self.response_times[key]
            if not times:
                return {}
            
            return {
                "path": path,
                "method": method,
                "request_count": self.request_count[key],
                "error_count": self.error_count[key],
                "error_rate": self.error_count[key] / self.request_count[key] if self.request_count[key] > 0 else 0,
                "avg_response_time": sum(times) / len(times),
                "min_response_time": min(times),
                "max_response_time": max(times),
                "p50": sorted(times)[len(times) // 2] if times else 0,
                "p95": sorted(times)[int(len(times) * 0.95)] if times else 0,
                "p99": sorted(times)[int(len(times) * 0.99)] if times else 0,
            }
        else:
            # 返回所有统计
            stats = {}
            for key in self.request_count.keys():
                method, path = key.split(" ", 1)
                stats[key] = self.get_stats(path, method)
            return stats
    
    def get_summary(self) -> dict:
        """获取汇总统计"""
        total_requests = sum(self.request_count.values())
        total_errors = sum(self.error_count.values())
        
        all_times = []
        for times in self.response_times.values():
            all_times.extend(times)
        
        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            "avg_response_time": sum(all_times) / len(all_times) if all_times else 0,
            "min_response_time": min(all_times) if all_times else 0,
            "max_response_time": max(all_times) if all_times else 0,
            "status_codes": dict(self.status_codes),
        }
    
    def reset(self):
        """重置统计"""
        self.request_count.clear()
        self.response_times.clear()
        self.error_count.clear()
        self.status_codes.clear()


# 全局性能指标实例
_metrics = PerformanceMetrics()


def get_metrics() -> PerformanceMetrics:
    """获取性能指标实例"""
    return _metrics


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/metrics",
        ]
        self.metrics = get_metrics()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 跳过排除的路径
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算响应时间
            duration = time.time() - start_time
            
            # 记录指标
            self.metrics.record_request(
                path=request.url.path,
                method=request.method,
                duration=duration,
                status_code=response.status_code
            )
            
            # 添加响应头
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            
            # 记录慢请求（超过1秒）
            if duration > 1.0:
                logger.warning(
                    f"慢请求: {request.method} {request.url.path} "
                    f"耗时 {duration:.3f}s, 状态码: {response.status_code}"
                )
            
            return response
            
        except Exception as e:
            # 记录错误
            duration = time.time() - start_time
            self.metrics.record_request(
                path=request.url.path,
                method=request.method,
                duration=duration,
                status_code=500
            )
            
            logger.error(
                f"请求错误: {request.method} {request.url.path} "
                f"耗时 {duration:.3f}s, 错误: {str(e)}",
                exc_info=True
            )
            
            raise

