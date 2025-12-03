"""
统一异常处理
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class VabHubException(HTTPException):
    """VabHub基础异常类"""
    
    def __init__(
        self,
        error_code: str,
        error_message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.error_message = error_message
        self.details = details or {}
        super().__init__(
            status_code=status_code,
            detail={
                "success": False,
                "error_code": error_code,
                "error_message": error_message,
                "details": self.details
            }
        )


class NotFoundError(VabHubException):
    """资源未找到异常"""
    
    def __init__(self, resource: str, resource_id: Optional[str] = None):
        error_message = f"{resource} not found"
        if resource_id:
            error_message += f": {resource_id}"
        super().__init__(
            error_code="NOT_FOUND",
            error_message=error_message,
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "resource_id": resource_id}
        )


class ValidationError(VabHubException):
    """验证错误异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="VALIDATION_ERROR",
            error_message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details or {}
        )


class UnauthorizedError(VabHubException):
    """未授权异常"""
    
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            error_code="UNAUTHORIZED",
            error_message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class ForbiddenError(VabHubException):
    """禁止访问异常"""
    
    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            error_code="FORBIDDEN",
            error_message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class ConflictError(VabHubException):
    """资源冲突异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="CONFLICT",
            error_message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details or {}
        )


class InternalServerError(VabHubException):
    """内部服务器错误异常"""
    
    def __init__(self, message: str = "Internal server error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="INTERNAL_SERVER_ERROR",
            error_message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details or {}
        )


class BadRequestError(VabHubException):
    """错误请求异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="BAD_REQUEST",
            error_message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details or {}
        )


class ServiceUnavailableError(VabHubException):
    """服务不可用异常"""
    
    def __init__(self, message: str = "Service unavailable", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="SERVICE_UNAVAILABLE",
            error_message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details or {}
        )

