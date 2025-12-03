"""
告警渠道模型
OPS-2A 实现
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Enum as SAEnum

from app.core.database import Base
from app.models.enums.alert_channel_type import AlertChannelType
from app.models.enums.alert_severity import AlertSeverity


class AlertChannel(Base):
    """告警渠道配置"""
    __tablename__ = "alert_channel"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # 显示名：如 "Telegram 群 A"
    channel_type = Column(SAEnum(AlertChannelType), nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)

    # 配置 JSON，如 token / chat_id / webhook_url / bark_base 等
    config = Column(JSON, nullable=False, default=dict)

    # 通知策略
    min_severity = Column(SAEnum(AlertSeverity), default=AlertSeverity.WARNING, nullable=False)
    include_checks = Column(JSON, nullable=True)   # 白名单：["db.default", "disk.*"]
    exclude_checks = Column(JSON, nullable=True)   # 黑名单

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AlertChannel {self.name} ({self.channel_type})>"
