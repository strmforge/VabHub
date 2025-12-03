"""用户漫画追更关系模型"""
from datetime import datetime

from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, String, UniqueConstraint, Index

from app.core.database import Base


class UserMangaFollow(Base):
    """用户-漫画追更关系

    记录用户对本地漫画系列的追更状态，用于漫画更新检测和未读统计。

    注意：
    - series_id 指向 MangaSeriesLocal.id
    - 不直接存 remote_series_id，避免与源耦合过深；源信息可从 MangaSeriesLocal 关联获取
    - 支持两种模式：本地导入（downloaded_chapters > 0）和纯远程追更（downloaded_chapters == 0）
    """

    __tablename__ = "user_manga_follow"

    id = Column(Integer, primary_key=True, index=True)

    # 用户与系列关联
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    series_id = Column(Integer, ForeignKey("manga_series_local.id", ondelete="CASCADE"), nullable=False, index=True)

    # 最近一次同步到的章节（用于追更 Runner 判断起点）
    last_synced_chapter_id = Column(Integer, ForeignKey("manga_chapter_local.id"), nullable=True)

    # 用户最近一次看到的章节（用于未读数计算与清零）
    last_seen_chapter_id = Column(Integer, ForeignKey("manga_chapter_local.id"), nullable=True)

    # 最近一次看到的远程章节ID（用于纯远程追更模式）
    last_remote_chapter_id = Column(String, nullable=True)

    # 未读章节数（相对 last_seen_chapter_id 统计的逻辑字段）
    unread_chapter_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        # 一个用户对同一系列只允许一条追更记录
        UniqueConstraint("user_id", "series_id", name="uq_user_manga_follow_user_series"),
        Index("ix_user_manga_follow_user_series", "user_id", "series_id"),
    )
