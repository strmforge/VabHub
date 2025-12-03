"""
通知模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean
from datetime import datetime
from app.core.database import Base


class Notification(Base):
    """通知模型"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(20), nullable=False)  # info, warning, error, success
    level = Column(String(20), nullable=True)  # info, warning, error, critical (用于性能告警)
    channels = Column(Text, nullable=True)  # 通知渠道列表（JSON字符串，可选）
    status = Column(String(20), default="pending")  # pending, sent, failed
    is_read = Column(Boolean, default=False, nullable=False, index=True)  # 是否已读
    read_at = Column(DateTime, nullable=True)  # 阅读时间
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    extra_metadata = Column(JSON, nullable=True)  # 额外元数据（重命名以避免与SQLAlchemy保留字冲突）

