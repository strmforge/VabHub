"""
通用响应模型和工具函数
"""

from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """基础响应模型"""
    success: bool = Field(description="请求是否成功")
    data: Optional[T] = Field(None, description="响应数据")
    message: str = Field(description="响应消息")
    code: Optional[int] = Field(None, description="业务状态码")


def success_response(data: Any, message: str = "操作成功", code: Optional[int] = None) -> BaseResponse:
    """
    生成成功响应
    
    Args:
        data: 响应数据
        message: 响应消息
        code: 业务状态码
        
    Returns:
        BaseResponse: 成功响应对象
    """
    return BaseResponse(
        success=True,
        data=data,
        message=message,
        code=code
    )


def error_response(message: str, code: Optional[int] = None, data: Optional[Any] = None) -> BaseResponse:
    """
    生成错误响应
    
    Args:
        message: 错误消息
        code: 业务状态码
        data: 错误数据
        
    Returns:
        BaseResponse: 错误响应对象
    """
    return BaseResponse(
        success=False,
        data=data,
        message=message,
        code=code
    )
