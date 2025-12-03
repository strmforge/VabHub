"""
统一的数据模型和响应格式
"""

from typing import Optional, Any, Dict, List, Generic, TypeVar
from datetime import datetime

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar('T')


def _current_timestamp() -> str:
    """生成 ISO8601 格式的时间戳"""
    return datetime.now().isoformat()


class BaseResponse(BaseModel, Generic[T]):
    """统一响应模型"""
    model_config = ConfigDict(
        json_schema_serialization_defaults_required=True,
        ser_json_timedelta='iso8601',
        ser_json_bytes='base64'
    )
    success: bool = True
    message: str = "success"
    data: Optional[T] = None
    timestamp: str = Field(default_factory=_current_timestamp)


class ErrorResponse(BaseModel):
    """统一错误响应模型"""
    model_config = ConfigDict(
        json_schema_serialization_defaults_required=True,
        ser_json_timedelta='iso8601',
        ser_json_bytes='base64'
    )
    success: bool = False
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=_current_timestamp)


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    meta: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int,
        *,
        meta: Optional[Dict[str, Any]] = None,
    ):
        """创建分页响应"""
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            meta=meta,
        )


class SuccessResponse(BaseResponse):
    """成功响应"""
    success: bool = True
    message: str = "success"


class ErrorDetail(BaseModel):
    """错误详情"""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ValidationErrorResponse(ErrorResponse):
    """验证错误响应"""
    success: bool = False
    error_code: str = "VALIDATION_ERROR"
    errors: List[ErrorDetail] = []


class NotFoundResponse(ErrorResponse):
    """未找到响应"""
    success: bool = False
    error_code: str = "NOT_FOUND"
    error_message: str = "Resource not found"


class UnauthorizedResponse(ErrorResponse):
    """未授权响应"""
    success: bool = False
    error_code: str = "UNAUTHORIZED"
    error_message: str = "Unauthorized"


class ForbiddenResponse(ErrorResponse):
    """禁止访问响应"""
    success: bool = False
    error_code: str = "FORBIDDEN"
    error_message: str = "Forbidden"


class InternalServerErrorResponse(ErrorResponse):
    """内部服务器错误响应"""
    success: bool = False
    error_code: str = "INTERNAL_SERVER_ERROR"
    error_message: str = "Internal server error"


# ========== 辅助函数 ==========

def success_response(data: Any = None, message: str = "success") -> dict:
    """
    创建成功响应
    
    Args:
        data: 响应数据
        message: 响应消息
    
    Returns:
        BaseResponse实例
    """
    encoded_data = jsonable_encoder(data) if data is not None else None
    response = BaseResponse(success=True, message=message, data=encoded_data)
    return response.model_dump(mode="json")


def error_response(
    error_code: str,
    error_message: str,
    details: Optional[Dict[str, Any]] = None
) -> ErrorResponse:
    """
    创建错误响应
    
    Args:
        error_code: 错误代码
        error_message: 错误消息
        details: 错误详情
    
    Returns:
        ErrorResponse实例
    """
    encoded_details = jsonable_encoder(details) if details is not None else None
    return ErrorResponse(
        success=False,
        error_code=error_code,
        error_message=error_message,
        details=encoded_details
    )

