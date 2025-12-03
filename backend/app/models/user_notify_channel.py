"""
用户通知渠道模型
NOTIFY-CORE 实现

与 OPS 的 AlertChannel 区分：
- AlertChannel: 系统级告警渠道（给管理员用）
- UserNotifyChannel: 用户级通知渠道（给每个用户自己配置）
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums.user_notify_channel_type import UserNotifyChannelType


class UserNotifyChannel(Base):
    """用户通知渠道配置"""
    __tablename__ = "user_notify_channel"

    id = Column(Integer, primary_key=True, index=True)
    
    # 用户关联
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 渠道类型
    channel_type = Column(SAEnum(UserNotifyChannelType), nullable=False, index=True)

    # 渠道配置（JSON）
    # Telegram: {"chat_id": 123456789, "username": "xxx", "language_code": "zh"}
    # Webhook: {"url": "https://...", "secret": "xxx"}
    # Bark: {"server": "https://api.day.app/xxx", "sound": "alarm", "group": "VabHub"}
    config = Column(JSON, nullable=False, default=dict)

    # 状态
    is_enabled = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)  # 是否已验证（如 Telegram 绑定成功）

    # 显示名称（用户自定义）
    display_name = Column(String(128), nullable=True)

    # 最近测试时间 & 结果
    last_test_at = Column(DateTime, nullable=True)
    last_test_ok = Column(Boolean, nullable=True)
    last_error = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<UserNotifyChannel {self.id} user={self.user_id} type={self.channel_type}>"
