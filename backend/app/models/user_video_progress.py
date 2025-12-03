"""
用户视频播放进度模型

记录用户对每个视频作品的播放进度
"""
from sqlalchemy import Column, Integer, BigInteger, Boolean, DateTime, ForeignKey, UniqueConstraint, Float, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.utils.time import utcnow


class UserVideoProgress(Base):
    """用户视频播放进度"""
    __tablename__ = "user_video_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    work_id = Column(Integer, nullable=False, index=True)  # 作品ID（对应player_wall的work.id）
    tmdb_id = Column(Integer, nullable=True, index=True)  # TMDB ID（可选，用于跨系统关联）
    
    # 播放进度信息
    position_seconds = Column(Float, nullable=False, default=0.0)  # 当前播放位置（秒）
    duration_seconds = Column(Float, nullable=True)  # 视频总时长（秒）
    
    # 进度状态
    is_finished = Column(Boolean, nullable=False, default=False)  # 是否看完
    progress_percent = Column(Float, nullable=False, default=0.0)  # 进度百分比(0-100)
    
    # 播放源信息
    source_type = Column(Integer, nullable=True)  # 播放源类型：1=本地，2=115
    last_play_url = Column(String(512), nullable=True)  # 最后播放的URL
    
    # 时间戳
    last_played_at = Column(DateTime, nullable=True)  # 最近播放时间
    updated_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow, index=True)
    
    # 唯一约束：1 用户对 1 作品最多一条记录
    __table_args__ = (
        UniqueConstraint('user_id', 'work_id', name='uq_user_work_video_progress'),
        # 可选：也可以基于tmdb_id的唯一约束
        # UniqueConstraint('user_id', 'tmdb_id', name='uq_user_tmdb_video_progress'),
    )
    
    # 关系（可选，用于查询）
    user = relationship("User", backref="video_progresses")
    
    def __repr__(self):
        return f"<UserVideoProgress(user_id={self.user_id}, work_id={self.work_id}, progress={self.progress_percent}%)>"
