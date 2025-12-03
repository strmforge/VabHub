"""
上传任务相关数据库模型
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class UploadTaskStatus(str, Enum):
    """上传任务状态"""
    PENDING = "pending"  # 等待中
    QUEUED = "queued"  # 已排队
    INITIALIZING = "initializing"  # 初始化中
    CALCULATING_HASH = "calculating_hash"  # 计算哈希中
    UPLOADING = "uploading"  # 上传中
    VERIFYING = "verifying"  # 验证中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消
    PAUSED = "paused"  # 已暂停
    RESUMING = "resuming"  # 恢复中


class UploadTask(Base):
    """上传任务模型"""
    __tablename__ = "upload_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=True, index=True)  # 用户ID（单用户系统可为空）
    
    # 文件信息
    file_path = Column(String(1024), nullable=False)  # 本地文件路径
    file_name = Column(String(512), nullable=False)  # 文件名
    file_size = Column(Integer, nullable=False)  # 文件大小（字节）
    file_sha1 = Column(String(64), nullable=True)  # 文件完整sha1值
    file_pre_sha1 = Column(String(64), nullable=True)  # 文件前128K sha1值
    
    # 目标信息
    target_parent_id = Column(String(64), nullable=False, default="0")  # 目标目录ID
    target_path = Column(String(1024), nullable=True)  # 目标路径
    
    # 上传信息
    upload_method = Column(String(32), nullable=True)  # 上传方式：instant（秒传）、upload（普通上传）、resume（断点续传）
    pick_code = Column(String(128), nullable=True)  # 上传任务key（用于断点续传）
    bucket = Column(String(128), nullable=True)  # OSS bucket名称
    object_key = Column(String(512), nullable=True)  # OSS object key
    upload_id = Column(String(128), nullable=True)  # 分片上传ID
    
    # 状态信息
    status = Column(String(32), nullable=False, default=UploadTaskStatus.PENDING.value, index=True)  # 任务状态
    progress = Column(Float, nullable=False, default=0.0)  # 上传进度（0.0-100.0）
    uploaded_bytes = Column(Integer, nullable=False, default=0)  # 已上传字节数
    total_bytes = Column(Integer, nullable=False, default=0)  # 总字节数
    
    # 分片信息
    part_size = Column(Integer, nullable=True)  # 分片大小（字节）
    total_parts = Column(Integer, nullable=True)  # 总分片数
    completed_parts = Column(Integer, nullable=True, default=0)  # 已完成分片数
    parts_info = Column(JSON, nullable=True)  # 分片信息列表（PartInfo）
    
    # 重试信息
    retry_count = Column(Integer, nullable=False, default=0)  # 重试次数
    max_retries = Column(Integer, nullable=False, default=3)  # 最大重试次数
    last_error = Column(Text, nullable=True)  # 最后一次错误信息
    error_history = Column(JSON, nullable=True)  # 错误历史记录
    
    # 验证信息
    etag = Column(String(128), nullable=True)  # 上传后的ETag
    verification_status = Column(String(32), nullable=True)  # 验证状态：pending、verified、failed
    verification_result = Column(JSON, nullable=True)  # 验证结果
    
    # 速度限制
    speed_limit = Column(Integer, nullable=True)  # 速度限制（字节/秒，None表示无限制）
    current_speed = Column(Float, nullable=True)  # 当前上传速度（字节/秒）
    
    # 元数据
    extra_metadata = Column(JSON, nullable=True)  # 额外元数据（避免使用metadata保留字）
    
    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)  # 开始时间
    completed_at = Column(DateTime, nullable=True)  # 完成时间
    
    # 索引
    __table_args__ = (
        Index('idx_upload_tasks_status', 'status'),
        Index('idx_upload_tasks_user_id_status', 'user_id', 'status'),
        Index('idx_upload_tasks_created_at', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_sha1": self.file_sha1,
            "file_pre_sha1": self.file_pre_sha1,
            "target_parent_id": self.target_parent_id,
            "target_path": self.target_path,
            "upload_method": self.upload_method,
            "pick_code": self.pick_code,
            "bucket": self.bucket,
            "object_key": self.object_key,
            "upload_id": self.upload_id,
            "status": self.status,
            "progress": self.progress,
            "uploaded_bytes": self.uploaded_bytes,
            "total_bytes": self.total_bytes,
            "part_size": self.part_size,
            "total_parts": self.total_parts,
            "completed_parts": self.completed_parts,
            "parts_info": self.parts_info,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "last_error": self.last_error,
            "error_history": self.error_history,
            "etag": self.etag,
            "verification_status": self.verification_status,
            "verification_result": self.verification_result,
            "speed_limit": self.speed_limit,
            "current_speed": self.current_speed,
            "extra_metadata": self.extra_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class UploadProgress(Base):
    """上传进度记录（用于持久化和恢复）"""
    __tablename__ = "upload_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("upload_tasks.id"), nullable=False, index=True)
    
    # 进度信息
    uploaded_bytes = Column(Integer, nullable=False, default=0)  # 已上传字节数
    total_bytes = Column(Integer, nullable=False)  # 总字节数
    progress = Column(Float, nullable=False, default=0.0)  # 进度百分比
    
    # 分片进度
    completed_parts = Column(Integer, nullable=False, default=0)  # 已完成分片数
    total_parts = Column(Integer, nullable=True)  # 总分片数
    parts_info = Column(JSON, nullable=True)  # 已完成分片信息
    
    # 速度信息
    current_speed = Column(Float, nullable=True)  # 当前速度（字节/秒）
    average_speed = Column(Float, nullable=True)  # 平均速度（字节/秒）
    
    # 时间信息
    elapsed_time = Column(Float, nullable=True)  # 已用时间（秒）
    estimated_remaining = Column(Float, nullable=True)  # 预计剩余时间（秒）
    
    # 时间戳
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # 索引
    __table_args__ = (
        Index('idx_upload_progress_task_id', 'task_id'),
        Index('idx_upload_progress_recorded_at', 'recorded_at'),
    )
    
    # 关系
    task = relationship("UploadTask", backref="progress_records")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "task_id": str(self.task_id),
            "uploaded_bytes": self.uploaded_bytes,
            "total_bytes": self.total_bytes,
            "progress": self.progress,
            "completed_parts": self.completed_parts,
            "total_parts": self.total_parts,
            "parts_info": self.parts_info,
            "current_speed": self.current_speed,
            "average_speed": self.average_speed,
            "elapsed_time": self.elapsed_time,
            "estimated_remaining": self.estimated_remaining,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }

