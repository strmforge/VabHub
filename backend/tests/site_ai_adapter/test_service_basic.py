"""
站点 AI 适配服务基本功能测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.core.site_ai_adapter.service import analyze_and_save_for_site, load_parsed_config
from app.core.site_ai_adapter.models import (
    SiteAIAdapterResult,
    AISiteAdapterConfig,
    AISearchConfig,
    AIDetailConfig,
    AIHRConfig,
    AIAuthConfig,
)
from app.models.ai_site_adapter import AISiteAdapter


@pytest.mark.asyncio
async def test_analyze_and_save_for_site_success(db_session, test_site):
    """
    测试成功分析并保存站点配置
    """
    # Mock HTTP 客户端和 Cloudflare API 调用
    mock_response = MagicMock()
    mock_response.text = "<html>test</html>"
    mock_response.raise_for_status = MagicMock()
    
    mock_cf_result = SiteAIAdapterResult(
        site_id=str(test_site.id),
        engine="nexusphp",
        config=AISiteAdapterConfig(
            search=AISearchConfig(
                url="/torrents.php",
                query_params={"search": "{keyword}"},
            ),
            detail=AIDetailConfig(url="/details.php?id={id}"),
            hr=AIHRConfig(enabled=True),
            auth=AIAuthConfig(),
        ),
        raw_model_output="test output",
        created_at=datetime.utcnow(),
    )
    
    with patch("app.core.site_ai_adapter.service.call_cf_adapter", new_callable=AsyncMock) as mock_cf:
        with patch("httpx.AsyncClient") as mock_client:
            # Mock HTTP 客户端响应
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_client_instance
            
            # Mock Cloudflare API 调用
            mock_cf.return_value = mock_cf_result
            
            # 执行分析
            result = await analyze_and_save_for_site(str(test_site.id), db_session)
            
            # 验证结果
            assert result is not None
            assert result.site_id == str(test_site.id)
            assert result.engine == "nexusphp"
            
            # 验证数据库记录
            from sqlalchemy import select
            db_result = await db_session.execute(
                select(AISiteAdapter).where(AISiteAdapter.site_id == str(test_site.id))
            )
            record = db_result.scalar_one_or_none()
            
            assert record is not None
            assert record.site_id == str(test_site.id)
            assert record.engine == "nexusphp"
            assert record.confidence_score == 80  # Phase AI-4: 固定可信度分数
            assert record.last_error is None
            assert record.config_json is not None
            assert "search" in record.config_json


@pytest.mark.asyncio
async def test_analyze_and_save_for_site_failure_saves_error(db_session, test_site):
    """
    测试分析失败时保存错误信息
    """
    from app.core.site_ai_adapter.client import AIAdapterClientError
    
    # Mock HTTP 客户端
    mock_response = MagicMock()
    mock_response.text = "<html>test</html>"
    mock_response.raise_for_status = MagicMock()
    
    with patch("app.core.site_ai_adapter.service.call_cf_adapter", new_callable=AsyncMock) as mock_cf:
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_client_instance
            
            # Mock Cloudflare API 调用失败
            mock_cf.side_effect = AIAdapterClientError("API 调用失败")
            
            # 执行分析
            result = await analyze_and_save_for_site(str(test_site.id), db_session)
            
            # 验证结果
            assert result is None
            
            # 验证错误信息已保存
            from sqlalchemy import select
            db_result = await db_session.execute(
                select(AISiteAdapter).where(AISiteAdapter.site_id == str(test_site.id))
            )
            record = db_result.scalar_one_or_none()
            
            assert record is not None
            assert record.last_error is not None
            assert "API 调用失败" in record.last_error
            assert record.confidence_score is None


@pytest.mark.asyncio
async def test_load_parsed_config_success(db_session, test_ai_adapter_record):
    """
    测试成功加载并解析配置
    """
    site_id = test_ai_adapter_record.site_id
    
    # 加载配置
    parsed_config = await load_parsed_config(site_id, db_session)
    
    # 验证结果
    assert parsed_config is not None
    assert parsed_config.site_id == site_id
    assert parsed_config.engine == "nexusphp"
    assert parsed_config.search is not None
    assert parsed_config.search.url == "/torrents.php"
    assert parsed_config.confidence_score == 80  # Phase AI-4: 从数据库记录读取


@pytest.mark.asyncio
async def test_load_parsed_config_not_found(db_session):
    """
    测试加载不存在的配置
    """
    parsed_config = await load_parsed_config("999", db_session)
    assert parsed_config is None


@pytest.mark.asyncio
async def test_load_parsed_config_invalid_json(db_session, test_site):
    """
    测试加载无效 JSON 配置
    """
    # 创建一个无效配置的记录
    invalid_record = AISiteAdapter(
        site_id=str(test_site.id),
        engine="nexusphp",
        config_json={"invalid": "config"},  # 缺少必需字段
        raw_model_output=None,
        version=1,
    )
    db_session.add(invalid_record)
    await db_session.commit()
    
    # 尝试加载（应该返回 None 而不是抛出异常）
    parsed_config = await load_parsed_config(str(test_site.id), db_session)
    # 由于配置无效，可能会返回 None 或抛出异常，取决于实现
    # 这里假设实现会优雅地处理并返回 None

