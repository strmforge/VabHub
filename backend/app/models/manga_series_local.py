"""
本地漫画系列模型
"""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    JSON,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class MangaSeriesLocal(Base):
    """本地漫画系列"""
    __tablename__ = "manga_series_local"

    id = Column(Integer, primary_key=True)

    # 关联远程源
    source_id = Column(Integer, ForeignKey("manga_sources.id"), nullable=False, index=True)
    remote_series_id = Column(String(256), nullable=False, index=True)

    # 基本信息（从 RemoteMangaSeries 拷贝）
    title = Column(String(512), nullable=False)
    alt_titles = Column(JSON, nullable=True)
    cover_path = Column(String(1024), nullable=True)  # 本地封面路径（相对路径）
    summary = Column(Text, nullable=True)
    authors = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    status = Column(String(64), nullable=True)  # 连载中 / 已完结等
    language = Column(String(32), nullable=True)
    # 调试用途：保留一份裁剪后的远端原始元数据
    remote_meta = Column(JSON, nullable=True)

    # 本地状态
    is_favorite = Column(Boolean, default=False, nullable=False)
    is_hidden = Column(Boolean, default=False, nullable=False)

    # 统计 & 同步信息
    total_chapters = Column(Integer, nullable=True)
    downloaded_chapters = Column(Integer, nullable=True)
    new_chapter_count = Column(Integer, default=0, nullable=False)  # 未读新章节数
    last_sync_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # 关联关系
    download_jobs = relationship("MangaDownloadJob", back_populates="target_local_series")

