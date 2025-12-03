"""
用户通知渠道 Pydantic Schema
NOTIFY-CORE 实现
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field

from app.models.enums.user_notify_channel_type import UserNotifyChannelType


class UserNotifyChannelBase(BaseModel):
    """用户通知渠道基础模型"""
    channel_type: UserNotifyChannelType
    display_name: Optional[str] = None
    config: dict[str, Any] = Field(default_factory=dict)
    is_enabled: bool = True


class UserNotifyChannelCreate(UserNotifyChannelBase):
    """创建用户通知渠道"""
    pass


class UserNotifyChannelUpdate(BaseModel):
    """更新用户通知渠道"""
    display_name: Optional[str] = None
    config: Optional[dict[str, Any]] = None
    is_enabled: Optional[bool] = None


class UserNotifyChannelRead(UserNotifyChannelBase):
    """读取用户通知渠道"""
    id: int
    is_verified: bool
    last_test_at: Optional[datetime] = None
    last_test_ok: Optional[bool] = None
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserNotifyChannelTestResponse(BaseModel):
    """测试通知响应"""
    success: bool
    message: str
