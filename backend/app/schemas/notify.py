"""
用户通知 Schema
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

# Import the new category system
from app.core.notification_categories import NotificationCategory


class UserNotificationItem(BaseModel):
    """用户通知项"""
    id: int
    type: str
    category: NotificationCategory  # 新增：通知分类
    media_type: Optional[str] = None
    ebook_id: Optional[int] = None
    tts_job_id: Optional[int] = None
    title: str
    message: Optional[str] = None
    severity: str
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserNotificationListResponse(BaseModel):
    """用户通知列表响应"""
    items: List[UserNotificationItem]
    total: int
    unread_count: int


class UserNotificationListQuery(BaseModel):
    """用户通知列表查询参数"""
    limit: Optional[int] = 20
    offset: Optional[int] = 0
    type: Optional[str] = None
    category: Optional[NotificationCategory] = None  # 新增：按分类过滤
    media_type: Optional[str] = None
    is_read: Optional[bool] = None
    level: Optional[str] = None  # 严重程度筛选：info/success/warning/error


class MarkReadRequest(BaseModel):
    """标记已读请求"""
    ids: Optional[List[int]] = None  # None = mark all as read
    category: Optional[NotificationCategory] = None  # 新增：按分类批量标记已读


class MarkReadResponse(BaseModel):
    """标记已读响应"""
    success: bool
    updated: int


class DeleteResponse(BaseModel):
    """删除响应"""
    success: bool
    deleted: int


class UnreadCountResponse(BaseModel):
    """未读数量响应"""
    unread_count: int

