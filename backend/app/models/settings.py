"""
系统设置模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from datetime import datetime
from app.core.database import Base


class SystemSetting(Base):
    """系统设置模型"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)  # JSON字符串
    category = Column(String(50), nullable=False, index=True)  # basic, downloader, notification, tmdb, advanced
    description = Column(Text, nullable=True)
    is_encrypted = Column(Boolean, default=False)  # 是否为加密字段（如密码、API Key）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

