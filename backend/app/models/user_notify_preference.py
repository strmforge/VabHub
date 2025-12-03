"""
用户通知偏好模型
NOTIFY-UX-1 实现

控制用户对每类通知的接收偏好：
- 是否接收（muted）
- 通过哪些渠道接收（enable_web/telegram/webhook/bark）
- 针对全局事件类型或单个作品
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, Boolean, DateTime, ForeignKey, Index,
    Enum as SAEnum, func
)

from app.core.database import Base
from app.models.enums.notification_type import NotificationType
from app.models.enums.reading_media_type import ReadingMediaType


class UserNotifyPreference(Base):
    """用户通知偏好"""
    __tablename__ = "user_notify_preference"

    id = Column(Integer, primary_key=True, index=True)
    
    # 用户关联
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 粒度：事件类型（必填）
    notification_type = Column(SAEnum(NotificationType), nullable=False)

    # 媒体作用域（可选）：针对特定作品静音
    media_type = Column(SAEnum(ReadingMediaType), nullable=True)
    target_id = Column(Integer, nullable=True)  # 具体作品 ID

    # 渠道设定：为 True 表示允许该类型事件通过该渠道发送
    enable_web = Column(Boolean, nullable=False, default=True)
    enable_telegram = Column(Boolean, nullable=False, default=True)
    enable_webhook = Column(Boolean, nullable=False, default=True)
    enable_bark = Column(Boolean, nullable=False, default=True)

    # 行为策略
    muted = Column(Boolean, nullable=False, default=False)  # 完全静音
    digest_only = Column(Boolean, nullable=False, default=False)  # 仅摘要模式

    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        # 唯一索引：(user_id, notification_type, media_type, target_id)
        Index(
            "ix_user_notify_pref_unique",
            "user_id",
            "notification_type",
            "media_type",
            "target_id",
            unique=True,
        ),
    )

    def __repr__(self):
        return f"<UserNotifyPreference {self.id} user={self.user_id} type={self.notification_type}>"
