"""
Local Intel AI 回退测试
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# 延迟导入以避免循环导入问题
from app.models.ai_site_adapter import AISiteAdapter
from app.core.site_ai_adapter.models import (
    ParsedAISiteAdapterConfig,
    ParsedAISiteSearchConfig,
    ParsedAISiteDetailConfig,
    ParsedAISiteHRConfig,
    ParsedAISiteAuthConfig,
)


@pytest.mark.asyncio
async def test_ai_fallback_creates_profile(db_session, test_site, test_ai_adapter_record):
    """
    测试 AI 正常回退：当没有手工配置时，从 AI 配置生成 profile
    """
    from app.core.intel_local.site_profiles import get_site_profile_with_ai_fallback, IntelSiteProfile
    
    # 确保没有手工配置（通过 mock get_site_profile 返回 None）
    from app.core.intel_local import site_profiles
    original_get_site_profile = site_profiles.get_site_profile
    site_profiles.get_site_profile = lambda x: None
    
    # Mock load_parsed_config 返回 AI 配置
    mock_ai_config = ParsedAISiteAdapterConfig(
        site_id=str(test_site.id),
        engine="nexusphp",
        search=ParsedAISiteSearchConfig(
            url="/torrents.php",
            query_params={"search": "{keyword}"},
        ),
        detail=ParsedAISiteDetailConfig(url="/details.php?id={id}"),
        hr=ParsedAISiteHRConfig(enabled=True, page_path="hr.php"),
        auth=ParsedAISiteAuthConfig(),
        confidence_score=80,
    )
    
    from app.core.site_ai_adapter import load_parsed_config as original_load_parsed_config
    from unittest.mock import patch, AsyncMock
    
    with patch("app.core.site_ai_adapter.load_parsed_config", new_callable=AsyncMock) as mock_load:
        mock_load.return_value = mock_ai_config
        
        # 调用回退函数
        profile = await get_site_profile_with_ai_fallback(
            site=test_site.name.lower().strip(),
            site_obj=test_site,
            db=db_session,
        )
        
        # 验证结果
        assert profile is not None
        assert isinstance(profile, IntelSiteProfile)
        assert profile.site == test_site.name.lower().strip()
        assert profile.hr.enabled is True  # AI 配置中 HR 是启用的
    
    # 恢复原始函数
    site_profiles.get_site_profile = original_get_site_profile


@pytest.mark.asyncio
async def test_ai_disabled_no_fallback(db_session, test_site):
    """
    测试 AI 被 disabled 时不进行回退
    """
    from app.core.intel_local.site_profiles import get_site_profile_with_ai_fallback
    
    # 创建一个 disabled=True 的 AI 记录
    disabled_record = AISiteAdapter(
        site_id=str(test_site.id),
        engine="nexusphp",
        config_json={"search": {"url": "/torrents.php"}},
        raw_model_output="test",
        version=1,
        disabled=True,  # Phase AI-4: 禁用标志
    )
    db_session.add(disabled_record)
    await db_session.commit()
    
    # 确保没有手工配置
    from app.core.intel_local import site_profiles
    original_get_site_profile = site_profiles.get_site_profile
    site_profiles.get_site_profile = lambda x: None
    
    try:
        # 调用回退函数
        profile = await get_site_profile_with_ai_fallback(
            site=test_site.name.lower().strip(),
            site_obj=test_site,
            db=db_session,
        )
        
        # 验证结果：应该返回 None，因为 AI 被禁用
        assert profile is None
    finally:
        # 恢复原始函数
        site_profiles.get_site_profile = original_get_site_profile


@pytest.mark.asyncio
async def test_manual_profile_preferred(db_session, test_site, test_ai_adapter_record):
    """
    测试手工优先：当存在手工配置且 manual_profile_preferred=True 时，优先使用手工配置
    """
    from app.core.intel_local.site_profiles import get_site_profile_with_ai_fallback, IntelSiteProfile
    
    # 创建一个手工 profile（带特殊标记）
    manual_profile = IntelSiteProfile(
        site=test_site.name.lower().strip(),
        hr=MagicMock(enabled=False),  # 手工配置中 HR 是禁用的
    )
    manual_profile.special_marker = "MANUAL_PROFILE_MARKER"  # 特殊标记
    
    # Mock get_site_profile 返回手工配置
    from app.core.intel_local import site_profiles
    original_get_site_profile = site_profiles.get_site_profile
    site_profiles.get_site_profile = lambda x: manual_profile if x == test_site.name.lower().strip() else None
    
    try:
        # 设置 manual_profile_preferred=True
        test_ai_adapter_record.manual_profile_preferred = True
        await db_session.commit()
        
        # 调用回退函数
        profile = await get_site_profile_with_ai_fallback(
            site=test_site.name.lower().strip(),
            site_obj=test_site,
            db=db_session,
        )
        
        # 验证结果：应该返回手工配置
        assert profile is not None
        assert hasattr(profile, "special_marker")
        assert profile.special_marker == "MANUAL_PROFILE_MARKER"
        assert profile.hr.enabled is False  # 使用手工配置的值
    finally:
        # 恢复原始函数
        site_profiles.get_site_profile = original_get_site_profile


@pytest.mark.asyncio
async def test_manual_profile_exists_but_not_preferred(db_session, test_site, test_ai_adapter_record):
    """
    测试：存在手工配置但 manual_profile_preferred=False 时，仍然使用手工配置
    """
    from app.core.intel_local.site_profiles import get_site_profile_with_ai_fallback, IntelSiteProfile
    
    # 创建一个手工 profile
    manual_profile = IntelSiteProfile(
        site=test_site.name.lower().strip(),
        hr=MagicMock(enabled=False),
    )
    
    # Mock get_site_profile 返回手工配置
    from app.core.intel_local import site_profiles
    original_get_site_profile = site_profiles.get_site_profile
    site_profiles.get_site_profile = lambda x: manual_profile if x == test_site.name.lower().strip() else None
    
    try:
        # 设置 manual_profile_preferred=False
        test_ai_adapter_record.manual_profile_preferred = False
        await db_session.commit()
        
        # 调用回退函数
        profile = await get_site_profile_with_ai_fallback(
            site=test_site.name.lower().strip(),
            site_obj=test_site,
            db=db_session,
        )
        
        # 验证结果：应该返回手工配置（因为优先使用手工配置是默认行为）
        assert profile is not None
        assert profile.hr.enabled is False  # 使用手工配置的值
    finally:
        # 恢复原始函数
        site_profiles.get_site_profile = original_get_site_profile


@pytest.mark.asyncio
async def test_no_manual_no_ai_returns_none(db_session, test_site):
    """
    测试：既没有手工配置也没有 AI 配置时返回 None
    """
    from app.core.intel_local.site_profiles import get_site_profile_with_ai_fallback
    
    # 确保没有手工配置和 AI 配置
    from app.core.intel_local import site_profiles
    from app.core.site_ai_adapter import load_parsed_config as original_load_parsed_config
    from unittest.mock import patch, AsyncMock
    
    original_get_site_profile = site_profiles.get_site_profile
    site_profiles.get_site_profile = lambda x: None
    
    with patch("app.core.site_ai_adapter.load_parsed_config", new_callable=AsyncMock, return_value=None):
        # 调用回退函数
        profile = await get_site_profile_with_ai_fallback(
            site=test_site.name.lower().strip(),
            site_obj=test_site,
            db=db_session,
        )
        
        # 验证结果
        assert profile is None
    
    # 恢复原始函数
    site_profiles.get_site_profile = original_get_site_profile

