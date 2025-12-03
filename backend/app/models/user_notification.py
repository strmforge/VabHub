"""
用户通知模型

用于记录用户可见的系统通知（如漫画更新通知、TTS Job 完成通知等）
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums.notification_type import NotificationType
from app.models.enums.reading_media_type import ReadingMediaType


class UserNotification(Base):
    """用户通知"""
    __tablename__ = "user_notifications"

    id = Column(Integer, primary_key=True, index=True)
    
    # 用户关联
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 通知类型
    type = Column(String(50), nullable=False, index=True)  # NotificationType枚举
    
    # 媒体类型（用 ReadingMediaType，方便前端路由）
    media_type = Column(String(20), nullable=True)  # ReadingMediaType枚举
    
    # 目标资源：如漫画系列/章节、小说、有声书等
    target_id = Column(Integer, nullable=True)
    # 可选的"子资源"，比如某一章节ID
    sub_target_id = Column(Integer, nullable=True)
    
    # TTS 相关字段
    ebook_id = Column(Integer, ForeignKey("ebooks.id"), nullable=True, index=True)
    tts_job_id = Column(Integer, ForeignKey("tts_jobs.id"), nullable=True, index=True)
    
    # 文本内容（已经适合直接展示）
    title = Column(String(256), nullable=False)         # 通知标题
    message = Column(Text, nullable=True)                # 详细说明，可选
    
    # 额外数据，供前端灵活使用，如路由名、参数等
    payload = Column(JSON, nullable=True)

    # 通知状态
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)

    # 可选关系（不强制加载）
    # ebook = relationship("EBook", backref="notifications")
    # tts_job = relationship("TTSJob", backref="notifications")

