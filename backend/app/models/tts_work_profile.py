"""
TTS 作品级配置模型

为每个 EBook 作品提供独立的 TTS 参数配置（Voice / 语速 / Provider 覆盖）
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.tts_voice_preset import TTSVoicePreset


class TTSWorkProfile(Base):
    """TTS 作品级配置"""
    __tablename__ = "tts_work_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    ebook_id = Column(Integer, ForeignKey("ebooks.id"), nullable=False, unique=True, index=True)
    
    # 预设引用
    preset_id = Column(Integer, ForeignKey("tts_voice_presets.id"), nullable=True, index=True)
    
    # TTS 参数覆盖（会覆盖 preset 中的对应字段）
    provider = Column(String(50), nullable=True)  # 为空：使用全局 SMART_TTS_PROVIDER
    language = Column(String(20), nullable=True)  # 为空：使用 Ebook.language 或全局默认
    voice = Column(String(100), nullable=True)  # 例如 "zh-CN-female-1" / "en-US-male-2"
    speed = Column(Float, nullable=True)  # 1.0 默认，一般 0.5~2.0
    pitch = Column(Float, nullable=True)  # 0.0 默认
    
    # 控制字段
    enabled = Column(Boolean, default=True, nullable=False)  # 是否启用此配置
    notes = Column(Text, nullable=True)  # Dev notes，方便备注
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    ebook = relationship("EBook", backref="tts_profile")
    preset = relationship("TTSVoicePreset", back_populates="profiles", lazy="joined")
    
    __table_args__ = (
        UniqueConstraint('ebook_id', name='uq_tts_work_profile_ebook_id'),
    )

