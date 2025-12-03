"""
存储监控模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Float, Index, Text
from datetime import datetime
from app.core.database import Base


class StorageDirectory(Base):
    """存储目录配置"""
    __tablename__ = "storage_directories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # 目录名称
    path = Column(String(512), nullable=False, unique=True, index=True)  # 目录路径
    enabled = Column(Boolean, default=True, index=True)  # 是否启用监控
    alert_threshold = Column(Float, default=80.0)  # 预警阈值（百分比）
    description = Column(Text, nullable=True)  # 描述
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_storage_directory_enabled', 'enabled'),
    )


class StorageUsageHistory(Base):
    """存储使用历史记录"""
    __tablename__ = "storage_usage_history"
    
    id = Column(Integer, primary_key=True, index=True)
    directory_id = Column(Integer, nullable=False, index=True)  # 目录ID
    path = Column(String(512), nullable=False, index=True)  # 目录路径（冗余字段，方便查询）
    total_bytes = Column(Integer, nullable=False)  # 总空间（字节）
    used_bytes = Column(Integer, nullable=False)  # 已用空间（字节）
    free_bytes = Column(Integer, nullable=False)  # 可用空间（字节）
    usage_percent = Column(Float, nullable=False)  # 使用率（百分比）
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)  # 记录时间
    
    __table_args__ = (
        Index('idx_storage_usage_history_directory_ts', 'directory_id', 'recorded_at'),
        Index('idx_storage_usage_history_path_ts', 'path', 'recorded_at'),
    )


class StorageAlert(Base):
    """存储空间预警记录"""
    __tablename__ = "storage_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    directory_id = Column(Integer, nullable=False, index=True)  # 目录ID
    path = Column(String(512), nullable=False)  # 目录路径
    alert_type = Column(String(50), nullable=False, index=True)  # 预警类型: threshold_exceeded, low_space, critical
    usage_percent = Column(Float, nullable=False)  # 使用率（百分比）
    threshold = Column(Float, nullable=False)  # 预警阈值
    message = Column(Text, nullable=True)  # 预警消息
    resolved = Column(Boolean, default=False, index=True)  # 是否已解决
    resolved_at = Column(DateTime, nullable=True)  # 解决时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)  # 创建时间
    
    __table_args__ = (
        Index('idx_storage_alert_directory_resolved', 'directory_id', 'resolved'),
        Index('idx_storage_alert_type_resolved', 'alert_type', 'resolved'),
    )

