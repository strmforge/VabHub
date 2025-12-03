"""
TTS 声线预设模型

定义可复用的 TTS 参数组合（provider / language / voice / speed / pitch）
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class TTSVoicePreset(Base):
    """TTS 声线预设"""
    __tablename__ = "tts_voice_presets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)  # 预设名称，唯一
    
    # TTS 参数
    provider = Column(String(50), nullable=True)  # 为空：使用全局 SMART_TTS_PROVIDER
    language = Column(String(20), nullable=True)  # 如 "zh-CN", "en-US"
    voice = Column(String(100), nullable=True)  # 具体 voice id
    speed = Column(Float, nullable=True)  # 0.5~2.0；空则用 provider 默认
    pitch = Column(Float, nullable=True)  # -10~10；空则用 provider 默认
    
    # 控制字段
    is_default = Column(Boolean, default=False, nullable=False)  # 是否为默认预设
    notes = Column(Text, nullable=True)  # 备注
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系：被哪些 Profile 引用
    profiles = relationship("TTSWorkProfile", back_populates="preset", lazy="dynamic")
    
    __table_args__ = (
        UniqueConstraint('name', name='uq_tts_voice_preset_name'),
    )

