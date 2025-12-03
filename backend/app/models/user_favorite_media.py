"""
用户收藏媒体模型
"""

from sqlalchemy import Column, Integer, DateTime, String, Enum, ForeignKey, UniqueConstraint, Index, func
from datetime import datetime

from app.core.database import Base
from app.models.enums.reading_media_type import ReadingMediaType


class UserFavoriteMedia(Base):
    """用户收藏媒体模型"""
    __tablename__ = "user_favorite_media"

    id = Column(Integer, primary_key=True, index=True)

    # 用户关联
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 媒体类型：复用 ReadingMediaType
    media_type = Column(
        Enum(ReadingMediaType, name="reading_media_type"),
        nullable=False,
    )

    # 目标资源 ID：
    # 如果 media_type = NOVEL，则指向 EBook.id
    # 如果 media_type = AUDIOBOOK，则指向 EBook.id（因为有声书也关联到 EBook）
    # 如果 media_type = MANGA，则指向 MangaSeriesLocal.id
    target_id = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "media_type", "target_id", name="uq_user_fav_media"),
        Index("ix_user_fav_media_user_last", "user_id", "created_at"),
    )