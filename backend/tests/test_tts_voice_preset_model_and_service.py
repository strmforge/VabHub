"""
TTS Voice Preset 模型和服务测试
"""

import pytest
from datetime import datetime

from app.models.tts_voice_preset import TTSVoicePreset
from app.models.tts_work_profile import TTSWorkProfile
from app.models.ebook import EBook
from app.modules.tts.profile_service import resolve_tts_profile_for_ebook, ResolvedTTSProfile
from app.core.config import Settings


@pytest.mark.asyncio
async def test_create_preset_and_mark_default(db_session):
    """测试创建预设并标记为默认"""
    # 创建预设
    preset1 = TTSVoicePreset(
        name="中文女声",
        provider="http",
        language="zh-CN",
        voice="zh-CN-female-1",
        speed=1.2,
        pitch=0.5,
        is_default=True
    )
    db_session.add(preset1)
    await db_session.commit()
    
    assert preset1.id > 0
    assert preset1.is_default is True
    assert preset1.name == "中文女声"


@pytest.mark.asyncio
async def test_only_one_default_preset(db_session):
    """测试只能有一个默认预设"""
    # 创建第一个默认预设
    preset1 = TTSVoicePreset(
        name="预设1",
        is_default=True
    )
    db_session.add(preset1)
    await db_session.commit()
    
    # 创建第二个默认预设
    preset2 = TTSVoicePreset(
        name="预设2",
        is_default=True
    )
    db_session.add(preset2)
    await db_session.commit()
    
    # 验证：两个预设都可以存在，但后端逻辑应该确保只有一个 is_default=True
    # 这里只测试模型层面，API 层面的逻辑在 API 测试中验证
    assert preset1.is_default is True
    assert preset2.is_default is True


@pytest.mark.asyncio
async def test_profile_resolves_with_preset_then_profile_override(db_session):
    """测试 Profile 使用预设，然后 Profile 字段覆盖预设"""
    # 创建预设
    preset = TTSVoicePreset(
        name="测试预设",
        provider="http",
        language="zh-CN",
        voice="zh-CN-female-1",
        speed=1.2,
        pitch=0.5
    )
    db_session.add(preset)
    
    # 创建 EBook
    ebook = EBook(
        id=1,
        title="测试小说",
        author="测试作者",
        language="en-US"
    )
    db_session.add(ebook)
    
    # 先提交 preset 以获取 ID
    await db_session.flush()
    
    # 创建 Profile（引用预设，但覆盖 voice）
    profile = TTSWorkProfile(
        ebook_id=1,
        preset_id=preset.id,
        voice="zh-CN-male-1",  # 覆盖预设的 voice
        enabled=True
    )
    db_session.add(profile)
    await db_session.commit()
    
    # 刷新以确保关联已建立
    await db_session.refresh(profile)
    
    # 解析配置
    settings = Settings()
    settings.SMART_TTS_PROVIDER = "dummy"
    
    resolved = await resolve_tts_profile_for_ebook(
        db=db_session,
        ebook=ebook,
        settings=settings
    )
    
    # 验证：使用预设的参数，但 voice 被 Profile 覆盖
    assert resolved.provider == "http"  # 来自 preset
    assert resolved.language == "zh-CN"  # 来自 preset
    assert resolved.voice == "zh-CN-male-1"  # 来自 profile（覆盖 preset）
    assert resolved.speed == 1.2  # 来自 preset
    assert resolved.pitch == 0.5  # 来自 preset
    assert resolved.preset_name == "测试预设"


@pytest.mark.asyncio
async def test_profile_resolves_without_preset_falls_back_to_settings(db_session):
    """测试没有预设时回退到全局配置"""
    # 创建 EBook（没有 Profile）
    ebook = EBook(
        id=2,
        title="测试小说2",
        author="测试作者",
        language="en-US"
    )
    db_session.add(ebook)
    await db_session.commit()
    
    # 解析配置
    settings = Settings()
    settings.SMART_TTS_PROVIDER = "dummy"
    
    resolved = await resolve_tts_profile_for_ebook(
        db=db_session,
        ebook=ebook,
        settings=settings
    )
    
    # 验证：使用默认配置
    assert resolved.provider == "dummy"  # 来自 settings
    assert resolved.language == "en-US"  # 来自 ebook.language
    assert resolved.voice is None
    assert resolved.speed is None
    assert resolved.pitch is None
    assert resolved.preset_name is None


@pytest.mark.asyncio
async def test_profile_with_invalid_preset_id_ignores_preset(db_session):
    """测试 Profile 引用了无效的 preset_id 时忽略预设"""
    # 创建 EBook
    ebook = EBook(
        id=3,
        title="测试小说3",
        author="测试作者",
        language="zh-CN"
    )
    db_session.add(ebook)
    
    # 创建 Profile（引用不存在的 preset_id）
    profile = TTSWorkProfile(
        ebook_id=3,
        preset_id=99999,  # 不存在的 preset_id
        provider="http",
        language="zh-CN",
        enabled=True
    )
    db_session.add(profile)
    await db_session.commit()
    
    # 解析配置
    settings = Settings()
    settings.SMART_TTS_PROVIDER = "dummy"
    
    resolved = await resolve_tts_profile_for_ebook(
        db=db_session,
        ebook=ebook,
        settings=settings
    )
    
    # 验证：忽略无效的 preset_id，使用 Profile 自己的字段
    assert resolved.provider == "http"  # 来自 profile
    assert resolved.language == "zh-CN"  # 来自 profile
    assert resolved.preset_name is None  # 预设无效

