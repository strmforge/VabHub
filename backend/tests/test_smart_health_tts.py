"""
TTS 健康检查测试
"""

import pytest
from unittest.mock import patch, MagicMock
from app.api.smart_health import get_tts_health, smart_health
from app.core.config import Settings
from app.models.tts_voice_preset import TTSVoicePreset
from app.models.tts_work_profile import TTSWorkProfile
from app.models.ebook import EBook
from app.models.audiobook import AudiobookFile


@pytest.mark.asyncio
async def test_smart_health_tts_disabled_by_default(db_session):
    """测试默认情况下 TTS 被禁用"""
    settings = Settings()
    # 确保默认配置
    settings.SMART_TTS_ENABLED = False
    
    tts_status = await get_tts_health(settings, db_session)
    
    # 断言
    assert tts_status["enabled"] is False
    assert tts_status["status"] == "disabled"
    assert tts_status["provider"] is not None  # 即使禁用，也应该有默认值
    assert tts_status["output_root"] is not None
    assert tts_status["max_chapters"] > 0
    assert tts_status["strategy"] is not None
    assert tts_status["last_used_at"] is None
    assert tts_status["last_error"] is None


@pytest.mark.asyncio
async def test_smart_health_tts_enabled_ok_when_engine_loads(db_session):
    """测试启用 TTS 且引擎加载成功时状态为 ok"""
    settings = Settings()
    settings.SMART_TTS_ENABLED = True
    settings.SMART_TTS_PROVIDER = "dummy"
    settings.SMART_TTS_OUTPUT_ROOT = "./data/tts_output"
    settings.SMART_TTS_MAX_CHAPTERS = 200
    settings.SMART_TTS_CHAPTER_STRATEGY = "per_chapter"
    
    # 直接测试，因为 dummy provider 应该能正常工作
    tts_status = await get_tts_health(settings, db_session)
    
    # 断言
    assert tts_status["enabled"] is True
    assert tts_status["status"] == "ok"  # dummy provider 应该能正常加载
    assert tts_status["provider"] == "dummy"
    assert tts_status["last_error"] is None


@pytest.mark.asyncio
async def test_smart_health_tts_enabled_degraded_when_factory_raises(db_session):
    """测试启用 TTS 但工厂函数抛异常时状态为 degraded"""
    settings = Settings()
    settings.SMART_TTS_ENABLED = True
    settings.SMART_TTS_PROVIDER = "dummy"
    
    # 使用 monkeypatch 让 get_tts_engine 抛出异常
    # 需要 patch get_tts_health 内部导入的模块路径
    with patch("app.modules.tts.factory.get_tts_engine") as mock_get_engine:
        mock_get_engine.side_effect = Exception("TTS 引擎初始化失败")
        
        tts_status = await get_tts_health(settings, db_session)
        
        # 断言
        assert tts_status["enabled"] is True
        assert tts_status["status"] == "degraded"
        assert tts_status["last_error"] is not None
        assert len(tts_status["last_error"]) > 0
        assert "TTS 引擎初始化失败" in tts_status["last_error"]


@pytest.mark.asyncio
async def test_smart_health_tts_block_is_present_in_smart_health_root(db_session):
    """测试 /api/smart/health 返回 JSON 中包含 features.tts"""
    # 直接调用 smart_health 函数，避免需要 TestClient
    result = await smart_health(db_session)
    
    # 检查 features.tts 存在
    assert "features" in result
    assert "tts" in result["features"]
    
    # 检查关键字段存在
    tts_block = result["features"]["tts"]
    assert "enabled" in tts_block
    assert "provider" in tts_block
    assert "status" in tts_block
    assert "output_root" in tts_block
    assert "max_chapters" in tts_block
    assert "strategy" in tts_block
    assert "last_used_at" in tts_block
    assert "last_error" in tts_block


@pytest.mark.asyncio
async def test_smart_health_tts_does_not_break_other_features(db_session):
    """测试 TTS 健康检查不影响其他功能"""
    # 直接调用 smart_health 函数
    result = await smart_health(db_session)
    
    # 确认原有 features 仍然存在
    assert "features" in result
    assert "local_intel" in result["features"]
    assert "external_indexer" in result["features"]
    assert "ai_site_adapter" in result["features"]
    assert "ebook_metadata" in result["features"]
    assert "inbox" in result["features"]
    assert "library" in result["features"]
    assert "tts" in result["features"]
    
    # 确认整体 ok 字段存在
    assert "ok" in result
    assert isinstance(result["ok"], bool)


@pytest.mark.asyncio
async def test_smart_health_tts_rate_limit_block_present(db_session):
    """测试健康检查中包含限流信息"""
    from app.modules.tts.rate_limiter import reset
    
    reset()
    
    settings = Settings()
    settings.SMART_TTS_ENABLED = True
    settings.SMART_TTS_PROVIDER = "dummy"
    settings.SMART_TTS_RATE_LIMIT_ENABLED = True
    settings.SMART_TTS_MAX_DAILY_REQUESTS = 1000
    settings.SMART_TTS_MAX_DAILY_CHARACTERS = 500000
    settings.SMART_TTS_MAX_REQUESTS_PER_RUN = 50
    
    tts_status = await get_tts_health(settings, db_session)
    
    # 断言
    assert tts_status["rate_limit_enabled"] is True
    assert tts_status["rate_limit_info"] is not None
    rate_limit_info = tts_status["rate_limit_info"]
    assert rate_limit_info["max_daily_requests"] == 1000
    assert rate_limit_info["max_daily_characters"] == 500000
    assert rate_limit_info["max_requests_per_run"] == 50


@pytest.mark.asyncio
async def test_smart_health_tts_last_limited_info_exposed(db_session):
    """测试健康检查中暴露最近限流信息"""
    from app.modules.tts.rate_limiter import reset, should_allow, record_request
    
    reset()
    
    settings = Settings()
    settings.SMART_TTS_ENABLED = True
    settings.SMART_TTS_PROVIDER = "dummy"
    settings.SMART_TTS_RATE_LIMIT_ENABLED = True
    settings.SMART_TTS_MAX_DAILY_REQUESTS = 1
    settings.SMART_TTS_MAX_DAILY_CHARACTERS = 0
    settings.SMART_TTS_MAX_REQUESTS_PER_RUN = 0
    
    # 记录一次请求，触发限流
    assert should_allow(100, settings=settings) is True
    record_request(100, settings=settings)
    
    # 第二次应该被限流
    assert should_allow(100, settings=settings) is False
    
    # 检查健康检查
    tts_status = await get_tts_health(settings, db_session)
    
    # 断言
    assert tts_status["rate_limit_enabled"] is True
    assert tts_status["rate_limit_info"] is not None
    rate_limit_info = tts_status["rate_limit_info"]
    assert rate_limit_info["last_limited_at"] is not None
    assert rate_limit_info["last_limited_reason"] == "daily_requests_exceeded"


@pytest.mark.asyncio
async def test_smart_health_tts_last_used_and_last_error_default_null(db_session):
    """测试没有任何 TTS 调用时，last_used_at 和 last_error 为 null"""
    from app.modules.tts.usage_tracker import reset
    
    # 重置 tracker 状态
    reset()
    
    settings = Settings()
    settings.SMART_TTS_ENABLED = True
    settings.SMART_TTS_PROVIDER = "dummy"
    
    tts_status = await get_tts_health(settings, db_session)
    
    # 断言
    assert tts_status["last_used_at"] is None
    assert tts_status["last_error"] is None


@pytest.mark.asyncio
async def test_smart_health_tts_last_used_updates_after_success(db_session):
    """测试成功调用 TTS 后，last_used_at 会被更新"""
    from app.modules.tts.usage_tracker import reset, record_success
    
    # 重置 tracker 状态
    reset()
    
    # 模拟一次成功的 TTS 调用
    record_success("dummy")
    
    settings = Settings()
    settings.SMART_TTS_ENABLED = True
    settings.SMART_TTS_PROVIDER = "dummy"
    
    tts_status = await get_tts_health(settings, db_session)
    
    # 断言
    assert tts_status["last_used_at"] is not None
    assert isinstance(tts_status["last_used_at"], str)
    # 验证是 ISO 格式（包含 "T"）
    assert "T" in tts_status["last_used_at"] or "-" in tts_status["last_used_at"]


@pytest.mark.asyncio
async def test_smart_health_tts_last_error_updates_after_failure(db_session):
    """测试失败调用 TTS 后，last_error 会被更新"""
    from app.modules.tts.usage_tracker import reset, record_error
    
    # 重置 tracker 状态
    reset()
    
    # 模拟一次失败的 TTS 调用
    exc = RuntimeError("simulated error")
    record_error(exc, "dummy")
    
    settings = Settings()
    settings.SMART_TTS_ENABLED = True
    settings.SMART_TTS_PROVIDER = "dummy"
    
    tts_status = await get_tts_health(settings, db_session)
    
    # 断言
    assert tts_status["last_error"] is not None
    assert isinstance(tts_status["last_error"], str)
    assert "simulated error" in tts_status["last_error"]
    # 验证包含时间戳（ISO 格式）
    assert "T" in tts_status["last_error"] or "[" in tts_status["last_error"]


@pytest.mark.asyncio
async def test_smart_health_tts_preset_anomaly_summary_present(db_session):
    """测试 smart_health 中包含预设异常统计"""
    # 创建测试预设
    preset1 = TTSVoicePreset(id=1, name="预设1", provider="dummy", is_default=False)
    preset2 = TTSVoicePreset(id=2, name="预设2", provider="dummy", is_default=False)
    preset3 = TTSVoicePreset(id=3, name="预设3", provider="dummy", is_default=False)
    
    db_session.add_all([preset1, preset2, preset3])
    await db_session.commit()
    
    # 创建测试 EBook - 需要足够多的 ebook 来支持测试
    ebooks = [EBook(id=i, title=f"测试{i}", author=f"作者{i}", language="zh-CN") for i in range(1, 30)]
    db_session.add_all(ebooks)
    await db_session.commit()
    
    # 预设1：绑定但从未使用（bound_but_never_used）
    profile1 = TTSWorkProfile(ebook_id=1, preset_id=1, enabled=True)
    db_session.add(profile1)
    
    # 预设2：高绑定低使用（high_bound_low_usage）
    # 绑定 ebook_id 从 2 到 24（共23个）
    for i in range(2, 25):
        profile = TTSWorkProfile(ebook_id=i, preset_id=2, enabled=True)
        db_session.add(profile)
    
    # 预设2：只生成5个（使用率 < 0.3，23个中只生成5个，约21.7%）
    for i in range(2, 7):
        audiobook = AudiobookFile(
            ebook_id=i,
            file_path=f"/test_preset2_{i}.wav",
            format="wav",
            is_tts_generated=True,
            tts_provider="dummy"
        )
        db_session.add(audiobook)

    # 预设3：正常使用（不应计入异常）- 使用 ebook_id=25，避免与预设2冲突
    profile3 = TTSWorkProfile(ebook_id=25, preset_id=3, enabled=True)
    audiobook3 = AudiobookFile(
        ebook_id=25,
        file_path="/test_preset3_25.wav",
        format="wav",
        is_tts_generated=True,
        tts_provider="dummy"
    )
    db_session.add_all([profile3, audiobook3])
    await db_session.commit()
    
    # 调用 smart_health
    result = await smart_health(db_session)
    
    # 断言
    assert "features" in result
    assert "tts" in result["features"]
    tts_block = result["features"]["tts"]
    assert "preset_anomaly_summary" in tts_block
    
    anomaly_summary = tts_block["preset_anomaly_summary"]
    assert anomaly_summary is not None
    assert "bound_but_never_used" in anomaly_summary
    assert "high_bound_low_usage" in anomaly_summary
    assert anomaly_summary["bound_but_never_used"] >= 1  # 至少预设1
    assert anomaly_summary["high_bound_low_usage"] >= 1  # 至少预设2


@pytest.mark.asyncio
async def test_smart_health_tts_preset_anomaly_summary_resilient_to_errors(db_session):
    """测试预设异常统计在出错时不影响整体健康检查"""
    # 使用 mock 让数据库查询抛出异常
    with patch("app.api.smart_health.select") as mock_select:
        mock_select.side_effect = Exception("模拟数据库错误")
        
        # 调用 smart_health
        result = await smart_health(db_session)
        
        # 断言：接口仍返回 200 结构，preset_anomaly_summary 为 None 或缺失
        assert "features" in result
        assert "tts" in result["features"]
        tts_block = result["features"]["tts"]
        
        # preset_anomaly_summary 应该为 None 或缺失，但不影响其他字段
        if "preset_anomaly_summary" in tts_block:
            assert tts_block["preset_anomaly_summary"] is None
        
        # 其他字段应该正常
        assert "enabled" in tts_block
        assert "provider" in tts_block
        assert "status" in tts_block
        
        # 整体 ok 字段应该存在
        assert "ok" in result
        assert isinstance(result["ok"], bool)


@pytest.mark.asyncio
async def test_smart_health_tts_storage_block_present_when_root_exists(db_session, monkeypatch, tmp_path):
    """测试当 TTS enabled 且输出目录存在时，features.tts.storage 存在"""
    # 创建临时目录
    test_root = tmp_path / "tts_output"
    test_root.mkdir()
    (test_root / "test.mp3").write_bytes(b"test")
    
    settings = Settings()
    settings.SMART_TTS_ENABLED = True
    settings.SMART_TTS_PROVIDER = "dummy"
    settings.SMART_TTS_OUTPUT_ROOT = str(test_root)
    settings.SMART_TTS_STORAGE_WARN_SIZE_GB = 10.0
    settings.SMART_TTS_STORAGE_CRITICAL_SIZE_GB = 30.0
    
    tts_status = await get_tts_health(settings, db_session)
    
    # 断言 storage 块存在
    assert "storage" in tts_status
    storage_block = tts_status["storage"]
    assert storage_block is not None
    assert "root" in storage_block
    assert "total_files" in storage_block
    assert "total_size_bytes" in storage_block
    assert "by_category" in storage_block
    assert "warning" in storage_block
    assert storage_block["total_files"] >= 1


@pytest.mark.asyncio
async def test_smart_health_tts_storage_warning_levels_by_size(db_session, monkeypatch, tmp_path):
    """测试根据存储大小返回不同的 warning 级别"""
    test_root = tmp_path / "tts_output"
    test_root.mkdir()
    
    settings = Settings()
    settings.SMART_TTS_ENABLED = True
    settings.SMART_TTS_PROVIDER = "dummy"
    settings.SMART_TTS_OUTPUT_ROOT = str(test_root)
    settings.SMART_TTS_STORAGE_WARN_SIZE_GB = 10.0
    settings.SMART_TTS_STORAGE_CRITICAL_SIZE_GB = 30.0
    
    # 测试小于 warn 阈值
    tts_status = await get_tts_health(settings, db_session)
    assert tts_status["storage"]["warning"] == "ok"
    
    # 测试大于 warn 但小于 critical（创建约 15GB 的文件）
    # 注意：实际测试中创建大文件可能很慢，这里用 mock 更合适
    from unittest.mock import patch
    from app.modules.tts.storage_service import TTSStorageOverview
    
    # Mock build_overview 返回不同大小
    # build_overview 是在 get_tts_health 函数内部导入的，需要 patch 原始模块
    with patch("app.modules.tts.storage_service.build_overview") as mock_build:
        # 测试 high_usage（15GB）
        mock_build.return_value = TTSStorageOverview(
            root=test_root,
            total_files=100,
            total_size_bytes=int(15 * 1024**3),  # 15GB
            by_category={
                "job": {"files": 50, "size_bytes": int(7.5 * 1024**3)},
                "playground": {"files": 30, "size_bytes": int(4.5 * 1024**3)},
                "other": {"files": 20, "size_bytes": int(3 * 1024**3)}
            }
        )
        tts_status = await get_tts_health(settings, db_session)
        assert tts_status["storage"]["warning"] == "high_usage"
        
        # 测试 critical（35GB）
        mock_build.return_value = TTSStorageOverview(
            root=test_root,
            total_files=200,
            total_size_bytes=int(35 * 1024**3),  # 35GB
            by_category={
                "job": {"files": 100, "size_bytes": int(17.5 * 1024**3)},
                "playground": {"files": 60, "size_bytes": int(10.5 * 1024**3)},
                "other": {"files": 40, "size_bytes": int(7 * 1024**3)}
            }
        )
        tts_status = await get_tts_health(settings, db_session)
        assert tts_status["storage"]["warning"] == "critical"


@pytest.mark.asyncio
async def test_smart_health_tts_storage_no_root_sets_no_root_warning(db_session, monkeypatch, tmp_path):
    """测试当根目录不存在时，warning 为 no_root"""
    # 使用不存在的目录
    non_existent_root = tmp_path / "non_existent"
    
    settings = Settings()
    settings.SMART_TTS_ENABLED = True
    settings.SMART_TTS_PROVIDER = "dummy"
    settings.SMART_TTS_OUTPUT_ROOT = str(non_existent_root)
    
    tts_status = await get_tts_health(settings, db_session)
    
    # 断言 storage 块存在且 warning 为 no_root
    assert "storage" in tts_status
    storage_block = tts_status["storage"]
    assert storage_block["warning"] == "no_root"
    assert storage_block["total_files"] == 0
    assert storage_block["total_size_bytes"] == 0

