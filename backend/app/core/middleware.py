"""
中间件系统
包含请求日志、性能监控、错误处理等中间件
"""

import time
import json
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from loguru import logger
from datetime import datetime

from app.core.exceptions import VabHubException


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并记录日志"""
        start_time = time.time()
        
        # 记录请求信息
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        
        logger.info(
            f"请求开始: {method} {path}",
            extra={
                "client_ip": client_ip,
                "method": method,
                "path": path,
                "query_params": query_params
            }
        )
        
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            logger.info(
                f"请求完成: {method} {path} - {response.status_code} ({process_time:.3f}s)",
                extra={
                    "client_ip": client_ip,
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "process_time": process_time
                }
            )
            
            # 添加处理时间到响应头
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"请求失败: {method} {path} - {str(e)} ({process_time:.3f}s)",
                extra={
                    "client_ip": client_ip,
                    "method": method,
                    "path": path,
                    "error": str(e),
                    "process_time": process_time
                },
                exc_info=True
            )
            raise


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """性能监控中间件（增强版）"""
    
    _instance = None  # 类变量，存储单例实例
    
    def __init__(self, app, slow_request_threshold: float = 1.0, exclude_paths: list = None):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/metrics",
        ]
        # 性能指标存储
        self._metrics = {
            "request_count": {},
            "response_times": {},
            "error_count": {},
            "status_codes": {}
        }
        
        # 存储实例到类变量和app.state
        PerformanceMonitoringMiddleware._instance = self
        if hasattr(app, 'state'):
            app.state.performance_middleware = self
    
    def _record_metric(self, path: str, method: str, duration: float, status_code: int):
        """记录性能指标"""
        key = f"{method} {path}"
        
        # 请求计数
        if key not in self._metrics["request_count"]:
            self._metrics["request_count"][key] = 0
            self._metrics["response_times"][key] = []
            self._metrics["error_count"][key] = 0
        
        self._metrics["request_count"][key] += 1
        self._metrics["response_times"][key].append(duration)
        
        # 状态码统计
        if status_code not in self._metrics["status_codes"]:
            self._metrics["status_codes"][status_code] = 0
        self._metrics["status_codes"][status_code] += 1
        
        # 错误计数
        if status_code >= 400:
            self._metrics["error_count"][key] += 1
        
        # 只保留最近1000条记录
        if len(self._metrics["response_times"][key]) > 1000:
            self._metrics["response_times"][key] = self._metrics["response_times"][key][-1000:]
    
    def get_metrics(self, path: str = None, method: str = None) -> dict:
        """获取性能指标"""
        if path and method:
            key = f"{method} {path}"
            if key not in self._metrics["response_times"]:
                return {}
            
            times = self._metrics["response_times"][key]
            if not times:
                return {}
            
            return {
                "path": path,
                "method": method,
                "request_count": self._metrics["request_count"][key],
                "error_count": self._metrics["error_count"][key],
                "error_rate": self._metrics["error_count"][key] / self._metrics["request_count"][key] if self._metrics["request_count"][key] > 0 else 0,
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
            for key in self._metrics["request_count"].keys():
                method, path = key.split(" ", 1)
                stats[key] = self.get_metrics(path, method)
            return stats
    
    def get_summary(self) -> dict:
        """获取汇总统计"""
        total_requests = sum(self._metrics["request_count"].values())
        total_errors = sum(self._metrics["error_count"].values())
        
        all_times = []
        for times in self._metrics["response_times"].values():
            all_times.extend(times)
        
        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            "avg_response_time": sum(all_times) / len(all_times) if all_times else 0,
            "min_response_time": min(all_times) if all_times else 0,
            "max_response_time": max(all_times) if all_times else 0,
            "status_codes": dict(self._metrics["status_codes"]),
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """监控请求性能"""
        # 跳过排除的路径
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # 记录性能指标
            self._record_metric(
                path=request.url.path,
                method=request.method,
                duration=process_time,
                status_code=response.status_code
            )
            
            # 如果处理时间超过阈值，记录警告
            if process_time > self.slow_request_threshold:
                logger.warning(
                    f"慢请求检测: {request.method} {request.url.path} - {process_time:.3f}s",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "process_time": process_time,
                        "threshold": self.slow_request_threshold
                    }
                )
            
            # 添加性能指标到响应头
            response.headers["X-Process-Time"] = f"{process_time:.3f}s"
            response.headers["X-Response-Time"] = f"{process_time:.3f}s"
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # 记录错误
            self._record_metric(
                path=request.url.path,
                method=request.method,
                duration=process_time,
                status_code=500
            )
            
            logger.error(
                f"请求错误: {request.method} {request.url.path} - {process_time:.3f}s, 错误: {str(e)}",
                exc_info=True
            )
            
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """错误处理中间件（统一错误响应格式）"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """统一错误处理"""
        try:
            response = await call_next(request)
            return response
        except VabHubException as e:
            # VabHub自定义异常，已经使用统一响应格式
            logger.error(
                f"VabHub异常: {request.method} {request.url.path} - {e.error_code}: {e.error_message}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error_code": e.error_code,
                    "error_message": e.error_message,
                    "status_code": e.status_code
                }
            )
            # VabHubException的detail已经是统一响应格式，直接返回
            if isinstance(e.detail, dict) and "success" in e.detail:
                return JSONResponse(
                    status_code=e.status_code,
                    content=e.detail
                )
            else:
                # 兼容旧格式
                return JSONResponse(
                    status_code=e.status_code,
                    content={
                        "success": False,
                        "error_code": e.error_code,
                        "error_message": e.error_message,
                        "details": e.details,
                        "timestamp": datetime.now().isoformat()
                    }
                )
        except RequestValidationError as e:
            # FastAPI请求验证错误
            logger.warning(
                f"请求验证错误: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "errors": e.errors()
                }
            )
            # 格式化验证错误
            error_details = []
            for error in e.errors():
                error_details.append({
                    "field": " -> ".join(str(loc) for loc in error.get("loc", [])),
                    "message": error.get("msg", "Validation error"),
                    "type": error.get("type", "unknown")
                })
            
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "error_code": "VALIDATION_ERROR",
                    "error_message": "请求参数验证失败",
                    "details": {
                        "errors": error_details
                    },
                    "timestamp": datetime.now().isoformat()
                }
            )
        except HTTPException as e:
            # FastAPI HTTP异常
            try:
                # 记录日志时，将detail转换为字符串，避免在extra中传递复杂对象
                if isinstance(e.detail, dict):
                    # 如果detail是字典，需要处理datetime对象
                    detail_copy = {}
                    for k, v in e.detail.items():
                        if isinstance(v, datetime):
                            detail_copy[k] = v.isoformat()
                        else:
                            detail_copy[k] = v
                    detail_str = json.dumps(detail_copy, ensure_ascii=False)
                else:
                    detail_str = str(e.detail)
                
                logger.error(
                    f"HTTP异常: {request.method} {request.url.path} - {e.status_code}: {detail_str}",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": e.status_code,
                        "detail": detail_str
                    }
                )
                detail = e.detail
                
                # 检查是否已经是统一响应格式（从API端点返回的）
                if isinstance(detail, dict):
                    # 如果已经是统一响应格式，需要处理datetime对象以便JSON序列化
                    if "success" in detail and "error_code" in detail:
                        # 使用model_dump(mode='json')来确保datetime被正确序列化
                        # 如果detail是从Pydantic模型来的，它应该已经是可以序列化的
                        # 否则我们需要手动处理datetime对象
                        try:
                            # 尝试直接返回，FastAPI的JSONResponse应该能处理datetime
                            return JSONResponse(status_code=e.status_code, content=detail)
                        except (TypeError, ValueError):
                            # 如果序列化失败，手动处理datetime对象
                            serializable_detail = {}
                            for k, v in detail.items():
                                if isinstance(v, datetime):
                                    serializable_detail[k] = v.isoformat()
                                elif hasattr(v, 'isoformat'):  # 处理其他日期时间类型
                                    serializable_detail[k] = v.isoformat()
                                else:
                                    serializable_detail[k] = v
                            return JSONResponse(status_code=e.status_code, content=serializable_detail)
                    # 如果是其他字典格式，包装成统一格式
                    else:
                        return JSONResponse(
                            status_code=e.status_code,
                            content={
                                "success": False,
                                "error_code": detail.get("error_code", f"HTTP_{e.status_code}"),
                                "error_message": detail.get("error_message", detail.get("detail", str(detail))),
                                "details": detail.get("details", {}),
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                else:
                    # 字符串格式，转换为统一格式
                    # 根据状态码确定错误代码
                    error_codes = {
                        400: "BAD_REQUEST",
                        401: "UNAUTHORIZED",
                        403: "FORBIDDEN",
                        404: "NOT_FOUND",
                        409: "CONFLICT",
                        422: "VALIDATION_ERROR",
                        500: "INTERNAL_SERVER_ERROR",
                        503: "SERVICE_UNAVAILABLE"
                    }
                    error_code = error_codes.get(e.status_code, f"HTTP_{e.status_code}")
                    
                    return JSONResponse(
                        status_code=e.status_code,
                        content={
                            "success": False,
                            "error_code": error_code,
                            "error_message": str(detail),
                            "timestamp": datetime.now().isoformat()
                        }
                    )
            except Exception as inner_e:
                # 如果处理HTTPException时发生错误，记录并返回通用错误
                logger.error(
                    f"处理HTTPException时发生错误: {type(inner_e).__name__}: {str(inner_e)}",
                    exc_info=True
                )
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "error_code": "INTERNAL_SERVER_ERROR",
                        "error_message": f"处理HTTP异常时发生错误: {str(inner_e)}",
                        "timestamp": datetime.now().isoformat()
                    }
                )
        except Exception as e:
            # 其他未处理的异常
            logger.error(
                f"未处理的异常: {request.method} {request.url.path} - {type(e).__name__}: {str(e)}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            
            # 检查是否是调试模式
            from app.core.config import settings
            is_debug = settings.DEBUG
            
            # 返回统一的错误响应
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "error_message": str(e) if is_debug else "内部服务器错误，请稍后重试",
                    "details": {
                        "error_type": type(e).__name__
                    } if is_debug else {},
                    "timestamp": datetime.now().isoformat()
                }
            )


class CORSMiddleware:
    """CORS中间件（简化版，FastAPI已有，这里作为示例）"""
    pass

