"""
小说 Inbox 导入日志模型

记录从 Inbox 导入的小说文件，用于防重复和追踪
"""
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base
from app.utils.time import utcnow


class NovelInboxStatus(str, enum.Enum):
    """小说 Inbox 导入状态"""
    PENDING = "pending"
    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"


class NovelInboxImportLog(Base):
    """小说 Inbox 导入日志"""
    __tablename__ = "novel_inbox_import_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    original_path = Column(String(1000), nullable=False, index=True)  # 原始文件路径（用于防重复）
    ebook_id = Column(Integer, ForeignKey("ebooks.id", ondelete="SET NULL"), nullable=True, index=True)  # 关联的 EBook ID
    
    status = Column(
        Enum(NovelInboxStatus, name="novel_inbox_status"),
        nullable=False,
        default=NovelInboxStatus.PENDING,
        index=True
    )
    reason = Column(String(255), nullable=True)  # 跳过/失败原因，如 'already_imported', 'unsupported_ext' 等
    error_message = Column(Text, nullable=True)  # 错误详情
    
    file_size = Column(BigInteger, nullable=True)  # 文件大小（字节）
    file_mtime = Column(DateTime, nullable=True)  # 文件修改时间
    
    created_at = Column(DateTime, nullable=False, default=utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow, index=True)
    
    # 关系
    ebook = relationship("EBook", backref="novel_inbox_logs")

