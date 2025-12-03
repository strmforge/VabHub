"""
External Indexer AI 回退测试
"""
import pytest
from unittest.mock import patch, AsyncMock

from app.core.ext_indexer.site_importer import get_site_config_with_ai_fallback
from app.core.ext_indexer.models import ExternalSiteConfig
from app.models.ai_site_adapter import AISiteAdapter
from app.core.site_ai_adapter.models import (
    ParsedAISiteAdapterConfig,
    ParsedAISiteSearchConfig,
    ParsedAISiteDetailConfig,
    ParsedAISiteHRConfig,
    ParsedAISiteAuthConfig,
)


@pytest.mark.asyncio
async def test_ai_fallback_creates_config(db_session, test_site, test_ai_adapter_record):
    """
    测试 AI 正常回退：当没有手工配置时，从 AI 配置生成 external site config
    """
    # 确保没有手工配置（通过 mock get_site_config 返回 None）
    with patch("app.core.ext_indexer.site_importer.get_site_config", return_value=None):
        # Mock load_parsed_config 返回 AI 配置
        mock_ai_config = ParsedAISiteAdapterConfig(
            site_id=str(test_site.id),
            engine="nexusphp",
            search=ParsedAISiteSearchConfig(
                url="/torrents.php",
                query_params={"search": "{keyword}"},
            ),
            detail=ParsedAISiteDetailConfig(url="/details.php?id={id}"),
            hr=ParsedAISiteHRConfig(enabled=True),
            auth=ParsedAISiteAuthConfig(),
            confidence_score=80,
        )
        
        with patch("app.core.site_ai_adapter.load_parsed_config", new_callable=AsyncMock, return_value=mock_ai_config):
            # 调用回退函数
            config = await get_site_config_with_ai_fallback(
                site_id=str(test_site.id),
                site_obj=test_site,
                db=db_session,
            )
            
            # 验证结果
            assert config is not None
            assert isinstance(config, ExternalSiteConfig)
            assert config.site_id == str(test_site.id)
            assert config.name == test_site.name
            assert config.base_url == test_site.url.rstrip("/")
            assert "search" in config.capabilities  # AI 配置中有 search


@pytest.mark.asyncio
async def test_ai_disabled_no_fallback(db_session, test_site):
    """
    测试 AI 被 disabled 时不进行回退
    """
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
    with patch("app.core.ext_indexer.site_importer.get_site_config", return_value=None):
        # 调用回退函数
        config = await get_site_config_with_ai_fallback(
            site_id=str(test_site.id),
            site_obj=test_site,
            db=db_session,
        )
        
        # 验证结果：应该返回 None，因为 AI 被禁用
        assert config is None


@pytest.mark.asyncio
async def test_manual_config_preferred(db_session, test_site, test_ai_adapter_record):
    """
    测试手工优先：当存在手工配置且 manual_profile_preferred=True 时，优先使用手工配置
    """
    # 创建一个手工 config（带特殊标记）
    manual_config = ExternalSiteConfig(
        site_id=str(test_site.id),
        name="Manual Config",
        base_url="https://manual.example.com",
        framework="manual",
        enabled=True,
        capabilities=["search", "detail"],
        search_path="/manual_search.php",
    )
    # 注意：ExternalSiteConfig 是 Pydantic 模型，不能直接设置额外属性
    # 我们通过比较 name 字段来验证是否使用了手工配置
    
    # Mock get_site_config 返回手工配置
    with patch("app.core.ext_indexer.site_importer.get_site_config", return_value=manual_config):
        # 设置 manual_profile_preferred=True
        test_ai_adapter_record.manual_profile_preferred = True
        await db_session.commit()
        
        # 调用回退函数
        config = await get_site_config_with_ai_fallback(
            site_id=str(test_site.id),
            site_obj=test_site,
            db=db_session,
        )
        
        # 验证结果：应该返回手工配置
        assert config is not None
        assert config.name == "Manual Config"  # 使用手工配置的值
        assert config.base_url == "https://manual.example.com"  # 验证是手工配置


@pytest.mark.asyncio
async def test_no_manual_no_ai_returns_none(db_session, test_site):
    """
    测试：既没有手工配置也没有 AI 配置时返回 None
    """
    # 确保没有手工配置和 AI 配置
    with patch("app.core.ext_indexer.site_importer.get_site_config", return_value=None):
        with patch("app.core.site_ai_adapter.load_parsed_config", new_callable=AsyncMock, return_value=None):
            # 调用回退函数
            config = await get_site_config_with_ai_fallback(
                site_id=str(test_site.id),
                site_obj=test_site,
                db=db_session,
            )
            
            # 验证结果
            assert config is None

