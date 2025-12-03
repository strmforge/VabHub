"""
全局规则设置模型
SETTINGS-RULES-1: GlobalRuleSettings 数据模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from datetime import datetime
from app.core.database import Base
from app.models.enums.global_rules import (
    HRPolicy, HRMode, ResolutionTier, ResolutionPolicy,
    SourceQualityPolicy, HdrPolicy, CodecPolicy,
    SubtitlePolicy, AudioLangPolicy, ExtraFeaturePolicy
)


class GlobalRuleSettings(Base):
    """全局规则设置模型（单行表）"""
    __tablename__ = "global_rule_settings"
    
    id = Column(Integer, primary_key=True, index=True, default=1)  # 单行表，固定ID为1
    
    # HR 策略和模式
    hr_policy = Column(String(20), default=HRPolicy.SAFE_SKIP.value, nullable=False)
    hr_mode = Column(String(20), default=HRMode.B_BALANCED.value, nullable=False)

    # 分辨率设置
    resolution_policy = Column(String(20), default=ResolutionPolicy.AUTO.value, nullable=False)
    resolution_tier = Column(String(20), default=ResolutionTier.MID_1080P.value, nullable=False)

    # 源质量和HDR
    source_quality_policy = Column(String(20), default=SourceQualityPolicy.NO_TRASH.value, nullable=False)
    hdr_policy = Column(String(20), default=HdrPolicy.ANY.value, nullable=False)
    codec_policy = Column(String(20), default=CodecPolicy.ANY.value, nullable=False)

    # 字幕和音轨
    subtitle_policy = Column(String(20), default=SubtitlePolicy.ANY.value, nullable=False)
    audio_lang_policy = Column(String(20), default=AudioLangPolicy.ANY.value, nullable=False)

    # 额外功能（3D等）
    extra_feature_policy = Column(String(20), default=ExtraFeaturePolicy.FORBID_3D.value, nullable=False)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(100), nullable=True)  # 创建者（可选）
    updated_by = Column(String(100), nullable=True)  # 更新者（可选）

    def __repr__(self):
        return f"<GlobalRuleSettings(id={self.id}, hr_mode={self.hr_mode}, hr_policy={self.hr_policy})>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "hr_policy": self.hr_policy,
            "hr_mode": self.hr_mode,
            "resolution_policy": self.resolution_policy,
            "resolution_tier": self.resolution_tier,
            "source_quality_policy": self.source_quality_policy,
            "hdr_policy": self.hdr_policy,
            "codec_policy": self.codec_policy,
            "subtitle_policy": self.subtitle_policy,
            "audio_lang_policy": self.audio_lang_policy,
            "extra_feature_policy": self.extra_feature_policy,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by
        }

    @classmethod
    def get_default_settings(cls):
        """获取默认设置的字典"""
        return {
            "hr_policy": HRPolicy.SAFE_SKIP.value,
            "hr_mode": HRMode.B_BALANCED.value,
            "resolution_policy": ResolutionPolicy.AUTO.value,
            "resolution_tier": ResolutionTier.MID_1080P.value,
            "source_quality_policy": SourceQualityPolicy.NO_TRASH.value,
            "hdr_policy": HdrPolicy.ANY.value,
            "codec_policy": CodecPolicy.ANY.value,
            "subtitle_policy": SubtitlePolicy.ANY.value,
            "audio_lang_policy": AudioLangPolicy.ANY.value,
            "extra_feature_policy": ExtraFeaturePolicy.FORBID_3D.value
        }

    def is_c_pro_mode(self):
        """检查是否为C档老司机模式"""
        return self.hr_mode == HRMode.C_PRO.value

    def is_a_safe_mode(self):
        """检查是否为A档安全模式"""
        return self.hr_mode == HRMode.A_SAFE.value

    def is_b_balanced_mode(self):
        """检查是否为B档平衡模式"""
        return self.hr_mode == HRMode.B_BALANCED.value
