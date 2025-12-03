"""
TTS 存储清理日志模型

记录每次存储清理操作的执行情况（自动/手动）
"""
from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

from app.core.database import Base
from app.utils.time import utcnow


class TTSStorageCleanupLog(Base):
    """TTS 存储清理日志"""
    __tablename__ = "tts_storage_cleanup_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, nullable=False, index=True)
    finished_at = Column(DateTime, nullable=True, index=True)
    
    # "auto" / "manual"
    mode = Column(String(16), nullable=False, index=True)
    
    # "policy" / "manual_params"
    strategy = Column(String(32), nullable=False)
    
    # 与 storage_service/filter/plan 中保持一致
    scope = Column(String(32), nullable=False)  # "all"/"playground_only"/"job_only"/"other_only"
    
    deleted_files_count = Column(Integer, nullable=False, default=0)
    freed_bytes = Column(BigInteger, nullable=False, default=0)
    
    dry_run = Column(Boolean, nullable=False, default=False)
    
    status = Column(String(16), nullable=False, default="success")  # "success" / "skipped" / "failed" / "running"
    
    reason = Column(String(255), nullable=True)  # e.g. "auto_disabled", "too_soon", "below_warn", "nothing_to_clean"
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=utcnow, index=True)

