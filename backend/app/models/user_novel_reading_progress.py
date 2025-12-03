"""
用户小说阅读进度模型

记录用户对每本小说的阅读进度
"""
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.utils.time import utcnow


class UserNovelReadingProgress(Base):
    """用户小说阅读进度"""
    __tablename__ = "user_novel_reading_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ebook_id = Column(Integer, ForeignKey("ebooks.id", ondelete="CASCADE"), nullable=False, index=True)
    
    current_chapter_index = Column(Integer, nullable=False, default=0)  # 当前阅读章节索引（从 0 开始）
    chapter_offset = Column(Integer, nullable=False, default=0)  # 章节内的偏移（按字符数或百分比，约定为字符数）
    is_finished = Column(Boolean, nullable=False, default=False)  # 是否已读完
    last_read_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow, index=True)  # 最后阅读时间
    
    # 唯一约束：1 用户对 1 作品最多一条记录
    __table_args__ = (
        UniqueConstraint('user_id', 'ebook_id', name='uniq_user_ebook_reading_progress'),
    )
    
    # 关系
    user = relationship("User", backref="novel_reading_progresses")
    ebook = relationship("EBook", backref="reading_progresses")

