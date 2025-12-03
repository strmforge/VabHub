"""
目录配置数据模型
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from app.core.database import Base


class Directory(Base):
    """目录配置表"""
    __tablename__ = "directories"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 目录路径
    download_path = Column(String(512), nullable=True, comment="下载目录路径")
    library_path = Column(String(512), nullable=True, comment="媒体库目录路径")
    
    # 存储类型
    storage = Column(String(50), default="local", comment="源存储类型（local/115/123等）")
    library_storage = Column(String(50), default="local", comment="目标存储类型（local/115/123等）")
    
    # 监控类型（决定文件操作模式）
    # "downloader": 下载器监控（定时扫描下载器中的任务）
    # "directory": 目录监控（文件系统实时监控）
    # null: 不监控（手动整理或不整理）
    monitor_type = Column(String(50), nullable=True, comment="监控类型: downloader(下载器监控) | directory(目录监控) | null(不监控)")
    
    # 整理方式（transfer_type）
    # "copy": 复制
    # "move": 移动
    # "link": 硬链接（仅本地存储到本地存储）
    # "softlink": 软链接（仅本地存储到本地存储）
    transfer_type = Column(String(50), nullable=True, comment="整理方式: copy(复制) | move(移动) | link(硬链接) | softlink(软链接)")
    
    # 媒体类型和类别
    media_type = Column(String(50), nullable=True, comment="媒体类型: movie(电影) | tv(电视剧) | anime(动漫)")
    media_category = Column(String(100), nullable=True, comment="媒体类别（自定义分类）")
    
    # 优先级（数字越小优先级越高）
    priority = Column(Integer, default=0, comment="优先级（数字越小优先级越高）")
    
    # 是否启用
    enabled = Column(Boolean, default=True, comment="是否启用此目录配置")
    
    # STRM 支持
    enable_strm = Column(Boolean, default=False, comment="是否启用 STRM 模式（仅对支持的媒体类型有效）")
    
    # 创建时间和更新时间
    created_at = Column(String(50), nullable=True, comment="创建时间")
    updated_at = Column(String(50), nullable=True, comment="更新时间")
    
    # 索引
    __table_args__ = (
        Index('idx_monitor_type', 'monitor_type'),
        Index('idx_storage', 'storage'),
        Index('idx_media_type', 'media_type'),
        Index('idx_priority', 'priority'),
        Index('idx_enabled', 'enabled'),
    )

