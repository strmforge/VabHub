"""
用户有声书播放进度模型

记录用户对每本作品的播放进度
"""
from sqlalchemy import Column, Integer, BigInteger, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.utils.time import utcnow


class UserAudiobookProgress(Base):
    """用户有声书播放进度"""
    __tablename__ = "user_audiobook_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ebook_id = Column(Integer, ForeignKey("ebooks.id"), nullable=False, index=True)
    audiobook_file_id = Column(Integer, ForeignKey("audiobook_files.id"), nullable=True, index=True)
    
    position_seconds = Column(Integer, nullable=False, default=0)  # 当前章节播放到的秒数
    duration_seconds = Column(Integer, nullable=True)  # 当前章节总时长快照
    
    is_finished = Column(Boolean, nullable=False, default=False)  # 是否听完
    last_played_at = Column(DateTime, nullable=True)  # 最近播放时间
    
    updated_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow, index=True)
    
    # 唯一约束：1 用户对 1 作品最多一条记录
    __table_args__ = (
        UniqueConstraint('user_id', 'ebook_id', name='uq_user_ebook_progress'),
    )
    
    # 关系（可选，用于查询）
    user = relationship("User", backref="audiobook_progresses")
    ebook = relationship("EBook", backref="audiobook_progresses")
    audiobook_file = relationship("AudiobookFile", backref="user_progresses")

