"""
用户通知静音/Snooze 模型
NOTIFY-UX-1 实现

管理用户的全局静音和临时静音（Snooze）状态
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, func

from app.core.database import Base


class UserNotifySnooze(Base):
    """用户通知静音状态"""
    __tablename__ = "user_notify_snooze"

    id = Column(Integer, primary_key=True, index=True)
    
    # 用户关联（每用户一条记录）
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # 全局静音标志
    muted = Column(Boolean, nullable=False, default=False)

    # Snooze 结束时间（UTC）
    # 当前时间 < snooze_until 时视为"临时静音"
    snooze_until = Column(DateTime, nullable=True)

    # 仅保留高优先级事件
    # 为 True 时：静音期间仍允许发送 SYSTEM_MESSAGE 等重要通知
    allow_critical_only = Column(Boolean, nullable=False, default=False)

    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<UserNotifySnooze user={self.user_id} muted={self.muted}>"
    
    def is_snoozed(self) -> bool:
        """检查是否处于 Snooze 状态"""
        if self.muted:
            return True
        if self.snooze_until and datetime.utcnow() < self.snooze_until:
            return True
        return False
