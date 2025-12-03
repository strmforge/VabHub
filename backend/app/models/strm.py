"""
STRM文件生成系统数据模型
"""

from sqlalchemy import Column, Integer, String, Float, BigInteger, Text, JSON, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.core.database import Base


class STRMWorkflowTask(Base):
    """STRM工作流任务"""
    __tablename__ = 'strm_workflow_tasks'
    
    id = Column(Integer, primary_key=True, index=True)
    download_task_id = Column(Integer, ForeignKey('download_tasks.id'), nullable=True, index=True)
    media_file_path = Column(String(1000), nullable=False)
    subtitle_files = Column(JSON, nullable=True)  # 字幕文件列表
    upload_mode = Column(String(20), nullable=False, default='copy')  # copy/move
    cloud_storage = Column(String(50), nullable=False)  # 115/123
    cloud_path = Column(String(1000), nullable=True)  # 云存储路径
    cloud_file_id = Column(String(100), nullable=True)  # 云存储文件ID
    strm_path = Column(String(1000), nullable=True)  # STRM文件路径
    status = Column(String(50), nullable=False, default='pending', index=True)  # pending/running/completed/failed
    progress = Column(Float, nullable=False, default=0.0)  # 进度（0-100）
    error_message = Column(Text, nullable=True)  # 错误信息
    extra_metadata = Column(JSON, nullable=True)  # 媒体元数据（避免使用metadata保留字）
    created_at = Column(BigInteger, nullable=False, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = Column(BigInteger, nullable=False, default=lambda: int(datetime.utcnow().timestamp()), onupdate=lambda: int(datetime.utcnow().timestamp()))
    
    # 关联关系（单方向，避免循环导入）
    # download_task = relationship('DownloadTask', back_populates='strm_workflow_tasks')
    strm_files = relationship('STRMFile', foreign_keys='STRMFile.workflow_task_id')
    
    __table_args__ = (
        Index('idx_strm_workflow_task_status', 'status'),
        Index('idx_strm_workflow_task_download_id', 'download_task_id'),
    )


class STRMFile(Base):
    """STRM文件记录"""
    __tablename__ = 'strm_files'
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_task_id = Column(Integer, ForeignKey('strm_workflow_tasks.id'), nullable=True, index=True)
    media_file_id = Column(Integer, ForeignKey('media_files.id'), nullable=True, index=True)
    strm_path = Column(String(1000), nullable=False, unique=True, index=True)
    cloud_file_id = Column(String(100), nullable=False, index=True)
    cloud_storage = Column(String(50), nullable=False)  # 115/123
    cloud_path = Column(String(1000), nullable=False)
    media_type = Column(String(20), nullable=False)  # movie/tv/anime
    title = Column(String(500), nullable=False)
    year = Column(Integer, nullable=True)
    season = Column(Integer, nullable=True)  # 季（电视剧）
    episode = Column(Integer, nullable=True)  # 集（电视剧）
    subtitle_files = Column(JSON, nullable=True)  # 字幕文件列表
    nfo_path = Column(String(1000), nullable=True)  # NFO文件路径
    created_at = Column(BigInteger, nullable=False, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = Column(BigInteger, nullable=False, default=lambda: int(datetime.utcnow().timestamp()), onupdate=lambda: int(datetime.utcnow().timestamp()))
    
    # 关联关系（单方向，避免循环导入）
    # workflow_task = relationship('STRMWorkflowTask', back_populates='strm_files')
    # media_file = relationship('MediaFile', back_populates='strm_files')
    
    __table_args__ = (
        Index('idx_strm_file_cloud_file_id', 'cloud_file_id'),
        Index('idx_strm_file_cloud_storage', 'cloud_storage'),
        Index('idx_strm_file_media_type', 'media_type'),
    )


class STRMFileTree(Base):
    """STRM文件树记录"""
    __tablename__ = 'strm_file_tree'
    
    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(1000), nullable=False, unique=True, index=True)  # 文件路径（唯一）
    file_id = Column(Integer, nullable=True)  # 文件ID
    parent_id = Column(Integer, nullable=True, index=True)  # 父目录ID
    file_name = Column(String(500), nullable=False)  # 文件名
    file_type = Column(String(20), nullable=False)  # file/folder
    file_size = Column(BigInteger, nullable=True)  # 文件大小
    sha1 = Column(String(40), nullable=True)  # 文件SHA1
    cloud_file_id = Column(String(100), nullable=True, index=True)  # 云存储文件ID
    cloud_storage = Column(String(50), nullable=False, index=True)  # 云存储类型
    update_time = Column(BigInteger, nullable=True)  # 更新时间
    create_time = Column(BigInteger, nullable=True)  # 创建时间
    
    __table_args__ = (
        Index('idx_strm_file_tree_path', 'path'),
        Index('idx_strm_file_tree_parent_id', 'parent_id'),
        Index('idx_strm_file_tree_file_type', 'file_type'),
        Index('idx_strm_file_tree_cloud_storage', 'cloud_storage'),
    )


class STRMLifeEvent(Base):
    """STRM生命周期事件"""
    __tablename__ = 'strm_life_events'
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(Integer, nullable=False, index=True)  # 事件类型：1-创建，2-更新，3-删除
    file_id = Column(Integer, nullable=True, index=True)  # 文件ID
    parent_id = Column(Integer, nullable=True, index=True)  # 父目录ID
    file_name = Column(String(500), nullable=True)  # 文件名
    file_category = Column(Integer, nullable=False)  # 文件分类
    file_type = Column(Integer, nullable=False, index=True)  # 文件类型
    file_size = Column(BigInteger, nullable=True)  # 文件大小
    sha1 = Column(String(40), nullable=True)  # 文件SHA1
    pick_code = Column(String(50), nullable=True)  # 云存储pick_code
    update_time = Column(BigInteger, nullable=True)  # 更新时间
    create_time = Column(BigInteger, nullable=True)  # 创建时间
    
    __table_args__ = (
        Index('idx_strm_life_event_type', 'type'),
        Index('idx_strm_life_event_file_id', 'file_id'),
        Index('idx_strm_life_event_parent_id', 'parent_id'),
        Index('idx_strm_life_event_file_type', 'file_type'),
    )


class STRMConfig(Base):
    """STRM系统配置"""
    __tablename__ = 'strm_config'
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), nullable=False, unique=True, index=True)
    value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(BigInteger, nullable=False, default=lambda: int(datetime.utcnow().timestamp()), onupdate=lambda: int(datetime.utcnow().timestamp()))

