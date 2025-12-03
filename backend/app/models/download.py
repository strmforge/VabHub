"""
下载模型
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean
from datetime import datetime
from app.core.database import Base


class DownloadTask(Base):
    """下载任务模型"""
    __tablename__ = "download_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    status = Column(String(20), default="downloading")  # downloading, paused, completed, failed
    progress = Column(Float, default=0.0)
    size_gb = Column(Float, nullable=False)
    downloaded_gb = Column(Float, default=0.0)
    speed_mbps = Column(Float, nullable=True)
    eta = Column(Integer, nullable=True)  # 秒
    downloader = Column(String(50), nullable=False)  # qbittorrent, transmission
    magnet_link = Column(Text, nullable=True)
    torrent_url = Column(Text, nullable=True)
    downloader_hash = Column(String(100), nullable=True)  # 下载器中的hash/id
    media_type = Column(String(32), nullable=True, index=True, default="unknown")
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # DOWNLOAD-CENTER-UI-2 新增字段
    organize_status = Column(String(20), default="NONE", index=True)  # NONE, AUTO_OK, AUTO_FAILED, MANUAL_PENDING, MANUAL_DONE

