"""
TTS Work Profile 模型和服务测试
"""

import pytest
from datetime import datetime

from app.models.tts_work_profile import TTSWorkProfile
from app.models.ebook import EBook
from app.modules.tts.profile_service import resolve_tts_profile_for_ebook, ResolvedTTSProfile
from app.core.config import Settings


@pytest.mark.asyncio
async def test_create_and_get_profile_for_ebook(db_session):
    """测试创建和获取作品 Profile"""
    # 创建测试 EBook
    ebook = EBook(
        id=1,
        title="测试小说",
        author="测试作者",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.commit()
    
    # 创建 Profile
    profile = TTSWorkProfile(
        ebook_id=1,
        provider="http",
        language="zh-CN",
        voice="zh-CN-female-1",
        speed=1.2,
        pitch=0.5,
        enabled=True,
        notes="测试配置"
    )
    db_session.add(profile)
    await db_session.commit()
    
    # 验证
    assert profile.id > 0
    assert profile.ebook_id == 1
    assert profile.provider == "http"
    assert profile.voice == "zh-CN-female-1"


@pytest.mark.asyncio
async def test_resolve_tts_profile_uses_profile_when_exists(db_session):
    """测试当 Profile 存在时使用 Profile 配置"""
    # 创建测试 EBook
    ebook = EBook(
        id=2,
        title="测试小说2",
        author="测试作者",
        language="en-US"
    )
    db_session.add(ebook)
    
    # 创建 Profile
    profile = TTSWorkProfile(
        ebook_id=2,
        provider="http",
        language="zh-CN",
        voice="zh-CN-female-1",
        speed=1.5,
        pitch=1.0,
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
    
    # 验证：使用 Profile 中的配置
    assert resolved.provider == "http"  # 来自 Profile
    assert resolved.language == "zh-CN"  # 来自 Profile
    assert resolved.voice == "zh-CN-female-1"  # 来自 Profile
    assert resolved.speed == 1.5  # 来自 Profile
    assert resolved.pitch == 1.0  # 来自 Profile


@pytest.mark.asyncio
async def test_resolve_tts_profile_falls_back_to_settings_and_ebook_language(db_session):
    """测试没有 Profile 时回退到全局配置和 EBook 语言"""
    # 创建测试 EBook（没有 Profile）
    ebook = EBook(
        id=3,
        title="测试小说3",
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
    assert resolved.voice is None  # 默认 None
    assert resolved.speed is None  # 默认 None
    assert resolved.pitch is None  # 默认 None


@pytest.mark.asyncio
async def test_resolve_tts_profile_respects_enabled_flag(db_session):
    """测试 Profile 的 enabled 标志"""
    # 创建测试 EBook
    ebook = EBook(
        id=4,
        title="测试小说4",
        author="测试作者",
        language="zh-CN"
    )
    db_session.add(ebook)
    
    # 创建 disabled Profile
    profile = TTSWorkProfile(
        ebook_id=4,
        provider="http",
        language="en-US",
        enabled=False  # 禁用
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
    
    # 验证：disabled Profile 应该被忽略，使用默认配置
    assert resolved.provider == "dummy"  # 来自 settings（Profile 被忽略）
    assert resolved.language == "zh-CN"  # 来自 ebook.language


@pytest.mark.asyncio
async def test_resolve_tts_profile_partial_fields(db_session):
    """测试 Profile 部分字段为空时的回退逻辑"""
    # 创建测试 EBook
    ebook = EBook(
        id=5,
        title="测试小说5",
        author="测试作者",
        language="zh-CN"
    )
    db_session.add(ebook)
    
    # 创建部分字段的 Profile
    profile = TTSWorkProfile(
        ebook_id=5,
        provider=None,  # 为空，应使用 settings
        language=None,  # 为空，应使用 ebook.language
        voice="zh-CN-female-1",  # 有值
        speed=None,  # 为空
        pitch=0.5,  # 有值
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
    
    # 验证：部分字段回退
    assert resolved.provider == "dummy"  # 回退到 settings
    assert resolved.language == "zh-CN"  # 回退到 ebook.language
    assert resolved.voice == "zh-CN-female-1"  # 来自 Profile
    assert resolved.speed is None  # Profile 中为 None
    assert resolved.pitch == 0.5  # 来自 Profile

