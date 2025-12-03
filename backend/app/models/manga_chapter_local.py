"""
本地漫画章节模型
"""
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Float,
    Text,
    ForeignKey,
    Enum as SAEnum,
    func,
)

from app.core.database import Base
import enum


class MangaChapterStatus(str, enum.Enum):
    """章节状态"""
    PENDING = "PENDING"
    DOWNLOADING = "DOWNLOADING"
    READY = "READY"
    FAILED = "FAILED"


class MangaChapterLocal(Base):
    """本地漫画章节"""
    __tablename__ = "manga_chapter_local"

    id = Column(Integer, primary_key=True)

    series_id = Column(Integer, ForeignKey("manga_series_local.id"), nullable=False, index=True)

    # 远程标识
    remote_chapter_id = Column(String(256), nullable=False, index=True)
    # 可选：指向 MangaSource.id，便于调试和追踪来源
    source_id = Column(Integer, nullable=True, index=True)

    # 展示信息
    title = Column(String(512), nullable=False)
    number = Column(Float, nullable=True)  # 支持 1.5
    volume = Column(Integer, nullable=True)
    published_at = Column(DateTime, nullable=True)

    # 下载/文件信息
    file_path = Column(String(1024), nullable=True)  # 例如 cbz 或 目录路径
    page_count = Column(Integer, nullable=True)

    # 状态
    status = Column(
        SAEnum(MangaChapterStatus),
        default=MangaChapterStatus.PENDING,
        nullable=False,
    )
    last_error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

