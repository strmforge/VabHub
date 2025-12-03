"""
备份系统数据模型
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, Text
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime
from typing import Dict, Any, Optional


class BackupRecord(Base):
    """备份记录"""
    __tablename__ = "backup_records"
    
    id = Column(Integer, primary_key=True, index=True)
    backup_id = Column(String(100), unique=True, index=True, nullable=False)
    backup_path = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    database_version = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)  # 字节
    checksum = Column(String(64), nullable=False)  # MD5校验和
    compressed = Column(Boolean, default=True, nullable=False)
    encrypted = Column(Boolean, default=False, nullable=False)
    tables_count = Column(JSON, nullable=False)  # 表记录数统计
    status = Column(String(20), default="completed", nullable=False)  # completed, failed, corrupted
    error_message = Column(Text, nullable=True)  # 错误信息
    extra_metadata = Column(JSON, nullable=True)  # 额外元数据（避免使用metadata保留字）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "backup_id": self.backup_id,
            "backup_path": self.backup_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "database_version": self.database_version,
            "file_size": self.file_size,
            "checksum": self.checksum,
            "compressed": self.compressed,
            "encrypted": self.encrypted,
            "tables_count": self.tables_count,
            "status": self.status,
            "error_message": self.error_message,
            "extra_metadata": self.extra_metadata
        }

