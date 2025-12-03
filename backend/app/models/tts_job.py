"""
TTS Job 模型

用于管理 TTS 生成任务的状态和进度
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Index
from datetime import datetime
from app.core.database import Base


class TTSJob(Base):
    """
    TTS 生成任务模型
    
    用于追踪和管理 TTS 有声书生成任务的状态、进度和结果。
    """
    __tablename__ = "tts_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    ebook_id = Column(Integer, ForeignKey("ebooks.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)  # "queued" | "running" | "success" | "partial" | "failed"
    provider = Column(String(50), nullable=True)  # 当前使用的 provider（dummy/http/edge_tts…）
    strategy = Column(String(50), nullable=True)  # 预留：per_chapter/single_file 等
    
    requested_at = Column(DateTime, nullable=False, index=True)  # 创建时间
    started_at = Column(DateTime, nullable=True)  # 开始执行时间
    finished_at = Column(DateTime, nullable=True)  # 完成时间
    
    total_chapters = Column(Integer, nullable=True)  # 总章节数
    processed_chapters = Column(Integer, nullable=False, default=0)  # 已处理章节数
    created_files_count = Column(Integer, nullable=False, default=0)  # 创建的文件数
    error_count = Column(Integer, nullable=False, default=0)  # 错误数
    
    last_error = Column(Text, nullable=True)  # 最后一次错误信息（截断）
    rate_limit_snapshot = Column(JSON, nullable=True)  # 可选，记录当时限流配置/状态
    details = Column(JSON, nullable=True)  # 扩展信息，用于存储断点续跑信息等
    
    created_by = Column(String(100), nullable=True)  # 触发者（"dev-api" / future 用户ID）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 注意：索引已在 Column 定义时通过 index=True 设置，不需要在 __table_args__ 中重复定义

