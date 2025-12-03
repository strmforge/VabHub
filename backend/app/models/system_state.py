"""
系统状态模型
LAUNCH-1 L2-1 实现

存储系统级状态，如 Onboarding 完成状态
"""
from sqlalchemy import Column, Integer, Boolean, DateTime, String
from datetime import datetime

from app.core.database import Base


class SystemState(Base):
    """系统状态模型"""
    __tablename__ = "system_state"
    
    id = Column(Integer, primary_key=True, default=1)
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    onboarding_completed_at = Column(DateTime, nullable=True)
    onboarding_completed_by = Column(String(50), nullable=True)  # 完成 Onboarding 的用户名
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
