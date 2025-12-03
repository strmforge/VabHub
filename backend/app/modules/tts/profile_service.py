"""
TTS Profile Service

负责解析作品级 TTS 配置，合成最终的 TTS 参数
"""

from dataclasses import dataclass
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.ebook import EBook
from app.models.tts_work_profile import TTSWorkProfile
from app.models.tts_voice_preset import TTSVoicePreset
from app.core.config import Settings
from loguru import logger


@dataclass
class ResolvedTTSProfile:
    """解析后的 TTS 配置"""
    provider: str
    language: str
    voice: Optional[str] = None
    speed: Optional[float] = None
    pitch: Optional[float] = None
    preset_name: Optional[str] = None  # 可选，用于调试/日志


async def resolve_tts_profile_for_ebook(
    db: AsyncSession,
    ebook: EBook,
    settings: Settings,
) -> ResolvedTTSProfile:
    """
    解析作品级 TTS 配置
    
    决策逻辑（按优先级从低到高）：
    1. 全局默认：global_provider, ebook.language, None voice/speed/pitch
    2. 若 TTSWorkProfile.preset_id 存在且 preset 有效：
       - 使用 preset 的参数覆盖全局默认
    3. 再用 TTSWorkProfile 自己的字段覆盖 preset
    
    最终构造 ResolvedTTSProfile 返回。
    
    Args:
        db: 数据库会话
        ebook: 电子书对象
        settings: 应用配置
    
    Returns:
        ResolvedTTSProfile: 解析后的 TTS 配置
    """
    # 1. 全局默认值
    provider = settings.SMART_TTS_PROVIDER or "dummy"
    language = ebook.language or "zh-CN"
    voice = None
    speed = None
    pitch = None
    preset_name = None
    
    # 2. 查找作品级 Profile（并加载关联的 preset）
    result = await db.execute(
        select(TTSWorkProfile)
        .options(joinedload(TTSWorkProfile.preset))
        .where(TTSWorkProfile.ebook_id == ebook.id)
    )
    profile = result.scalar_one_or_none()
    
    if profile and profile.enabled:
        # 3. 如果 Profile 引用了预设，先应用预设的参数
        if profile.preset_id and profile.preset:
            preset = profile.preset
            logger.debug(f"EBook {ebook.id} 使用预设: {preset.name}")
            
            # 应用预设参数（只覆盖非空字段）
            if preset.provider is not None:
                provider = preset.provider
            if preset.language is not None:
                language = preset.language
            if preset.voice is not None:
                voice = preset.voice
            if preset.speed is not None:
                speed = preset.speed
            if preset.pitch is not None:
                pitch = preset.pitch
            preset_name = preset.name
        elif profile.preset_id:
            # preset_id 存在但 preset 无效（可能被删除）
            logger.warning(f"EBook {ebook.id} 的 Profile 引用了无效的 preset_id={profile.preset_id}，将忽略预设")
        
        # 4. 再用 Profile 自己的字段覆盖预设（只覆盖非空字段）
        if profile.provider is not None:
            provider = profile.provider
        if profile.language is not None:
            language = profile.language
        if profile.voice is not None:
            voice = profile.voice
        if profile.speed is not None:
            speed = profile.speed
        if profile.pitch is not None:
            pitch = profile.pitch
    
    logger.debug(
        f"EBook {ebook.id} 最终 TTS 配置: provider={provider}, language={language}, "
        f"voice={voice}, speed={speed}, pitch={pitch}, preset={preset_name}"
    )
    
    return ResolvedTTSProfile(
        provider=provider,
        language=language,
        voice=voice,
        speed=speed,
        pitch=pitch,
        preset_name=preset_name
    )

