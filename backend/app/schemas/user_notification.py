"""
用户通知Schema
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class UserNotificationBase(BaseModel):
    """通知基础Schema"""
    title: str
    message: Optional[str] = None
    type: str = "info"
    media_type: Optional[str] = None
    target_id: Optional[int] = None
    sub_target_id: Optional[int] = None
    payload: Optional[dict] = None


class UserNotificationCreate(UserNotificationBase):
    """创建通知Schema"""
    user_id: int


class UserNotificationUpdate(BaseModel):
    """更新通知Schema"""
    is_read: Optional[bool] = None


class UserNotification(UserNotificationBase):
    """通知响应Schema"""
    id: int
    user_id: int
    is_read: bool
    created_at: datetime
    updated_at: datetime
    read_at: Optional[datetime]

    model_config = {
        "from_attributes": True
    }


class UserNotificationListResponseLegacy(BaseModel):
    """通知列表响应Schema（旧版本）"""
    items: List[UserNotification]
    total: int
    unread_count: int