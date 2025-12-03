"""
站点 AI 适配频率限制和标志测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from app.core.site_ai_adapter.service import maybe_auto_analyze_site
from app.models.ai_site_adapter import AISiteAdapter
from app.core.config import settings


@pytest.mark.asyncio
async def test_frequency_limit_prevents_reanalysis(db_session, test_site):
    """
    测试频率限制防止重复分析
    """
    # 创建一个已存在的记录，更新时间在限制时间内
    existing_record = AISiteAdapter(
        site_id=str(test_site.id),
        engine="nexusphp",
        config_json={"search": {"url": "/torrents.php"}},
        raw_model_output="test",
        version=1,
        updated_at=datetime.utcnow() - timedelta(minutes=5),  # 5 分钟前更新
    )
    db_session.add(existing_record)
    await db_session.commit()
    
    # Mock analyze_and_save_for_site 以跟踪调用次数
    call_count = 0
    
    async def mock_analyze(site_id, db):
        nonlocal call_count
        call_count += 1
        return None
    
    with patch("app.core.site_ai_adapter.service.analyze_and_save_for_site", side_effect=mock_analyze):
        with patch.object(settings, "AI_ADAPTER_MIN_REANALYZE_INTERVAL_MINUTES", 60):
            # 第一次调用应该被频率限制阻止
            result = await maybe_auto_analyze_site(str(test_site.id), db_session)
            
            assert result is None
            assert call_count == 0  # 不应该调用 analyze_and_save_for_site


@pytest.mark.asyncio
async def test_frequency_limit_allows_reanalysis_after_interval(db_session, test_site):
    """
    测试频率限制在间隔后允许重新分析
    """
    # 创建一个已存在的记录，更新时间在限制时间外
    existing_record = AISiteAdapter(
        site_id=str(test_site.id),
        engine="nexusphp",
        config_json={"search": {"url": "/torrents.php"}},
        raw_model_output="test",
        version=1,
        updated_at=datetime.utcnow() - timedelta(minutes=70),  # 70 分钟前更新
    )
    db_session.add(existing_record)
    await db_session.commit()
    
    # Mock analyze_and_save_for_site
    call_count = 0
    
    async def mock_analyze(site_id, db):
        nonlocal call_count
        call_count += 1
        return None
    
    with patch("app.core.site_ai_adapter.service.analyze_and_save_for_site", side_effect=mock_analyze):
        with patch.object(settings, "AI_ADAPTER_MIN_REANALYZE_INTERVAL_MINUTES", 60):
            # 应该允许重新分析
            result = await maybe_auto_analyze_site(str(test_site.id), db_session)
            
            assert call_count == 1  # 应该调用 analyze_and_save_for_site


@pytest.mark.asyncio
async def test_disabled_flag_prevents_analysis(db_session, test_site):
    """
    测试 disabled 标志阻止分析
    """
    # 创建一个 disabled=True 的记录
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
    
    # Mock analyze_and_save_for_site 以跟踪调用次数
    call_count = 0
    
    async def mock_analyze(site_id, db):
        nonlocal call_count
        call_count += 1
        return None
    
    with patch("app.core.site_ai_adapter.service.analyze_and_save_for_site", side_effect=mock_analyze):
        # 应该被 disabled 标志阻止
        result = await maybe_auto_analyze_site(str(test_site.id), db_session)
        
        assert result is None
        assert call_count == 0  # 不应该调用 analyze_and_save_for_site


@pytest.mark.asyncio
async def test_disabled_flag_preserves_existing_config(db_session, test_site):
    """
    测试 disabled 标志不会覆盖现有配置
    """
    # 创建一个 disabled=True 的记录，带有特殊标记
    special_marker = "PRESERVED_CONFIG_MARKER"
    disabled_record = AISiteAdapter(
        site_id=str(test_site.id),
        engine="nexusphp",
        config_json={"search": {"url": "/torrents.php"}, "marker": special_marker},
        raw_model_output="test",
        version=1,
        disabled=True,
    )
    db_session.add(disabled_record)
    await db_session.commit()
    
    # 尝试触发分析
    with patch("app.core.site_ai_adapter.service.analyze_and_save_for_site", new_callable=AsyncMock):
        await maybe_auto_analyze_site(str(test_site.id), db_session)
    
    # 验证配置未被覆盖
    from sqlalchemy import select
    db_result = await db_session.execute(
        select(AISiteAdapter).where(AISiteAdapter.site_id == str(test_site.id))
    )
    record = db_result.scalar_one_or_none()
    
    assert record is not None
    assert record.config_json.get("marker") == special_marker  # 标记仍然存在


@pytest.mark.asyncio
async def test_first_analysis_allowed(db_session, test_site):
    """
    测试首次分析允许执行
    """
    # 没有现有记录，应该允许分析
    call_count = 0
    
    async def mock_analyze(site_id, db):
        nonlocal call_count
        call_count += 1
        return None
    
    with patch("app.core.site_ai_adapter.service.analyze_and_save_for_site", side_effect=mock_analyze):
        result = await maybe_auto_analyze_site(str(test_site.id), db_session)
        
        assert call_count == 1  # 应该调用 analyze_and_save_for_site

