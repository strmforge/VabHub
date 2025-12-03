"""
漫画阅读进度模型
"""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    ForeignKey,
    UniqueConstraint,
    func,
)

from app.core.database import Base


class MangaReadingProgress(Base):
    """漫画阅读进度"""
    __tablename__ = "manga_reading_progress"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    series_id = Column(Integer, ForeignKey("manga_series_local.id"), nullable=False, index=True)
    
    # 当前最后阅读的章节
    chapter_id = Column(Integer, ForeignKey("manga_chapter_local.id"), nullable=True, index=True)

    # 页码：从 1 开始
    last_page_index = Column(Integer, nullable=False, default=1)
    total_pages = Column(Integer, nullable=True)

    # 是否已读完（阅读器可以在看到最后一页时标记）
    is_finished = Column(Boolean, nullable=False, default=False)

    last_read_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "series_id", name="uq_manga_reading_progress_user_series"),
    )

