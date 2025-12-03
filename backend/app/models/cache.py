"""
缓存数据模型
用于L3数据库缓存
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Index
from sqlalchemy.sql import func
from datetime import datetime, timedelta

from app.core.database import Base


class CacheEntry(Base):
    """缓存条目表（L3数据库缓存）"""
    __tablename__ = "cache_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(500), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)  # JSON序列化的值
    ttl = Column(Integer, nullable=False, default=3600)  # 过期时间（秒）
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # 索引优化（PostgreSQL和SQLite都支持）
    __table_args__ = (
        Index('idx_cache_key', 'key'),
        Index('idx_cache_expires_at', 'expires_at'),
    )
    
    def is_expired(self) -> bool:
        """检查缓存是否过期"""
        if self.expires_at is None:
            return False
        # 处理时区问题
        if self.expires_at.tzinfo is None:
            expires_at_naive = self.expires_at
        else:
            expires_at_naive = self.expires_at.replace(tzinfo=None)
        return datetime.utcnow() > expires_at_naive

