"""
磁盘监控配置 Schema
OPS-2D 实现
"""

from typing import Optional
from pydantic import BaseModel, Field


class DiskPathConfig(BaseModel):
    """单个磁盘路径配置"""
    name: str = Field(..., description="磁盘名称标识，如 data, media1")
    path: str = Field(..., description="磁盘路径，如 /mnt/data")
    warn_percent: int = Field(default=20, ge=1, le=99, description="警告阈值（剩余空间百分比）")
    error_percent: int = Field(default=10, ge=1, le=99, description="错误阈值（剩余空间百分比）")


class DiskMonitorConfig(BaseModel):
    """磁盘监控配置"""
    paths: list[DiskPathConfig] = Field(default_factory=list, description="监控路径列表")


class DiskMonitorConfigUpdate(BaseModel):
    """磁盘监控配置更新"""
    paths: Optional[list[DiskPathConfig]] = None
