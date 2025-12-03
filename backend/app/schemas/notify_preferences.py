"""
通知偏好 Schema
NOTIFY-UX-1 实现
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.enums.notification_type import NotificationType
from app.models.enums.reading_media_type import ReadingMediaType


# ============== UserNotifyPreference Schema ==============

class UserNotifyPreferenceBase(BaseModel):
    """通知偏好基础 Schema"""
    notification_type: NotificationType
    media_type: Optional[ReadingMediaType] = None
    target_id: Optional[int] = None
    enable_web: bool = True
    enable_telegram: bool = True
    enable_webhook: bool = True
    enable_bark: bool = True
    muted: bool = False
    digest_only: bool = False


class UserNotifyPreferenceCreate(UserNotifyPreferenceBase):
    """创建通知偏好"""
    pass


class UserNotifyPreferenceUpdate(BaseModel):
    """更新通知偏好"""
    notification_type: NotificationType
    media_type: Optional[ReadingMediaType] = None
    target_id: Optional[int] = None
    enable_web: Optional[bool] = None
    enable_telegram: Optional[bool] = None
    enable_webhook: Optional[bool] = None
    enable_bark: Optional[bool] = None
    muted: Optional[bool] = None
    digest_only: Optional[bool] = None


class UserNotifyPreferenceRead(UserNotifyPreferenceBase):
    """读取通知偏好"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== UserNotifySnooze Schema ==============

class UserNotifySnoozeBase(BaseModel):
    """通知静音基础 Schema"""
    muted: bool = False
    snooze_until: Optional[datetime] = None
    allow_critical_only: bool = False


class UserNotifySnoozeUpdate(BaseModel):
    """更新静音状态"""
    muted: Optional[bool] = None
    snooze_until: Optional[datetime] = None
    allow_critical_only: Optional[bool] = None


class UserNotifySnoozeRead(UserNotifySnoozeBase):
    """读取静音状态"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== 聚合 DTO ==============

class NotificationTypeInfo(BaseModel):
    """通知类型信息"""
    type: NotificationType
    name: str  # 显示名称
    description: str  # 描述
    group: str  # 分组（manga/novel/music/system/task）
    is_critical: bool = False  # 是否为重要通知


class UserNotifyPreferenceMatrix(BaseModel):
    """用户通知偏好矩阵（聚合）"""
    preferences: list[UserNotifyPreferenceRead]
    snooze: Optional[UserNotifySnoozeRead] = None
    available_notification_types: list[NotificationTypeInfo]


# ============== 投递决策 ==============

class NotificationDeliveryDecision(BaseModel):
    """通知投递决策"""
    allowed_web: bool = True
    allowed_telegram: bool = True
    allowed_webhook: bool = True
    allowed_bark: bool = True
    store_in_user_notification: bool = True  # 是否写入 UserNotification 表
    reason: Optional[str] = None  # 决策原因（调试用）


# ============== 快捷操作 ==============

class MuteNotificationTypeRequest(BaseModel):
    """静音某类通知请求"""
    notification_type: NotificationType
    media_type: Optional[ReadingMediaType] = None
    target_id: Optional[int] = None


class SnoozeRequest(BaseModel):
    """Snooze 请求"""
    duration_minutes: Optional[int] = Field(None, ge=5, le=1440, description="静音时长（分钟），5-1440")
    until: Optional[datetime] = Field(None, description="静音到指定时间")
    allow_critical_only: bool = False
