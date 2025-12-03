"""
告警渠道 Pydantic Schema
OPS-2A 实现
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel

from app.models.enums.alert_channel_type import AlertChannelType
from app.models.enums.alert_severity import AlertSeverity


class AlertChannelBase(BaseModel):
    """告警渠道基础模型"""
    name: str
    channel_type: AlertChannelType
    is_enabled: bool = True
    min_severity: AlertSeverity = AlertSeverity.WARNING
    config: dict[str, Any] = {}
    include_checks: Optional[list[str]] = None
    exclude_checks: Optional[list[str]] = None


class AlertChannelCreate(AlertChannelBase):
    """创建告警渠道"""
    pass


class AlertChannelUpdate(BaseModel):
    """更新告警渠道"""
    name: Optional[str] = None
    is_enabled: Optional[bool] = None
    min_severity: Optional[AlertSeverity] = None
    config: Optional[dict[str, Any]] = None
    include_checks: Optional[list[str]] = None
    exclude_checks: Optional[list[str]] = None


class AlertChannelRead(AlertChannelBase):
    """读取告警渠道"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertChannelTestRequest(BaseModel):
    """测试告警请求"""
    message: Optional[str] = None
