"""
媒体模型
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from datetime import datetime
from app.core.database import Base


class Media(Base):
    """媒体模型"""
    __tablename__ = "media"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    original_title = Column(String(255), nullable=True)
    year = Column(Integer, nullable=True)
    media_type = Column(String(20), nullable=False)  # movie, tv, anime
    tmdb_id = Column(Integer, nullable=True)
    tvdb_id = Column(Integer, nullable=True)
    imdb_id = Column(String(20), nullable=True)
    poster_url = Column(String(500), nullable=True)
    backdrop_url = Column(String(500), nullable=True)
    overview = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)  # 附加元数据（短剧等）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MediaFile(Base):
    """媒体文件模型"""
    __tablename__ = "media_files"
    
    id = Column(Integer, primary_key=True, index=True)
    media_id = Column(Integer, ForeignKey("media.id"), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size_gb = Column(Float, nullable=False)
    quality = Column(String(20), nullable=True)  # 4K, 1080p, 720p
    resolution = Column(String(20), nullable=True)
    codec = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

