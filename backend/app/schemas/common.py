"""
通用Pydantic Schema定义
"""

from typing import Generic, TypeVar, List, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """通用API响应格式"""
    success: bool = Field(description="请求是否成功")
    data: Optional[T] = Field(None, description="响应数据")
    message: str = Field(description="响应消息")
    code: Optional[int] = Field(None, description="业务状态码")


class PaginationResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    items: List[T] = Field(description="数据列表")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    size: int = Field(description="每页大小")
    pages: int = Field(description="总页数")


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, ge=1, description="页码，从1开始")
    size: int = Field(20, ge=1, le=100, description="每页大小，1-100")


class ErrorResponse(BaseModel):
    """错误响应格式"""
    success: bool = Field(False, description="请求是否成功")
    error: str = Field(description="错误类型")
    message: str = Field(description="错误消息")
    details: Optional[dict] = Field(None, description="错误详情")


class SuccessResponse(BaseModel, Generic[T]):
    """成功响应格式"""
    success: bool = Field(True, description="请求是否成功")
    data: T = Field(description="响应数据")
    message: str = Field("操作成功", description="响应消息")


class BatchOperationResult(BaseModel):
    """批量操作结果"""
    success: bool = Field(description="批量操作是否成功")
    total: int = Field(description="总操作数")
    success_count: int = Field(description="成功数量")
    error_count: int = Field(description="失败数量")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")


class HealthCheckResult(BaseModel):
    """健康检查结果"""
    status: str = Field(description="健康状态：healthy/unhealthy")
    timestamp: str = Field(description="检查时间")
    services: dict = Field(description="各服务状态")
    version: Optional[str] = Field(None, description="系统版本")


class ConfigValidationResult(BaseModel):
    """配置验证结果"""
    valid: bool = Field(description="配置是否有效")
    errors: List[str] = Field(default_factory=list, description="验证错误列表")
    warnings: List[str] = Field(default_factory=list, description="验证警告列表")
