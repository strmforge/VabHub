"""
TTS Settings API 测试
"""

import pytest
from datetime import datetime, timedelta
from app.api.admin_tts_settings import get_tts_settings, get_tts_usage_stats, _compute_preset_usage, classify_preset_heat
from app.models.audiobook import AudiobookFile
from app.models.ebook import EBook
from app.models.tts_voice_preset import TTSVoicePreset
from app.models.tts_work_profile import TTSWorkProfile
from app.core.config import Settings
from app.modules.tts.rate_limiter import reset, should_allow, record_request


@pytest.mark.asyncio
async def test_get_tts_settings_basic_structure(db_session):
    """测试无数据时，返回字段完整，usage_stats.total_tts_audiobooks == 0"""
    result = await get_tts_settings(db_session)
    
    # 断言基本字段存在
    assert hasattr(result, "enabled")
    assert hasattr(result, "provider")
    assert hasattr(result, "status")
    assert hasattr(result, "rate_limit_enabled")
    assert hasattr(result, "usage_stats")
    
    # 断言使用统计为空
    assert result.usage_stats.total_tts_audiobooks == 0
    assert result.usage_stats.by_provider == {}


@pytest.mark.asyncio
async def test_tts_settings_usage_stats_counts_from_db(db_session):
    """测试使用统计从数据库正确统计"""
    # 创建测试 EBook
    test_ebook = EBook(
        id=1,
        title="测试小说",
        author="测试作者",
        language="zh-CN"
    )
    db_session.add(test_ebook)
    await db_session.commit()
    
    # 创建几条 TTS 生成的 AudiobookFile
    tts_file1 = AudiobookFile(
        ebook_id=1,
        file_path="/test1.wav",
        format="wav",
        is_tts_generated=True,
        tts_provider="dummy"
    )
    tts_file2 = AudiobookFile(
        ebook_id=1,
        file_path="/test2.wav",
        format="wav",
        is_tts_generated=True,
        tts_provider="dummy"
    )
    tts_file3 = AudiobookFile(
        ebook_id=1,
        file_path="/test3.wav",
        format="wav",
        is_tts_generated=True,
        tts_provider="http"
    )
    tts_file4 = AudiobookFile(
        ebook_id=1,
        file_path="/test4.wav",
        format="wav",
        is_tts_generated=True,
        tts_provider=None  # None 应该归类为 "unknown"
    )
    
    # 创建几条非 TTS 生成的 AudiobookFile（不应该被统计）
    non_tts_file = AudiobookFile(
        ebook_id=1,
        file_path="/test5.wav",
        format="wav",
        is_tts_generated=False,
        tts_provider=None
    )
    
    db_session.add_all([tts_file1, tts_file2, tts_file3, tts_file4, non_tts_file])
    await db_session.commit()
    
    # 获取统计
    stats = await get_tts_usage_stats(db_session)
    
    # 断言
    assert stats.total_tts_audiobooks == 4  # 只有 is_tts_generated=True 的 4 个
    assert stats.by_provider["dummy"] == 2
    assert stats.by_provider["http"] == 1
    assert stats.by_provider["unknown"] == 1


@pytest.mark.asyncio
async def test_tts_settings_rate_limit_info_when_disabled(db_session, monkeypatch):
    """测试限流未启用时，rate_limit_enabled=False，rate_limit_info is None"""
    # 使用 monkeypatch 设置限流未启用
    monkeypatch.setattr("app.api.admin_tts_settings.settings.SMART_TTS_RATE_LIMIT_ENABLED", False)
    
    result = await get_tts_settings(db_session)
    
    # 断言
    assert result.rate_limit_enabled is False
    assert result.rate_limit_info is None


@pytest.mark.asyncio
async def test_tts_settings_rate_limit_info_when_enabled(db_session, monkeypatch):
    """测试限流启用时，正确反映配置和状态"""
    reset()
    
    # 使用 monkeypatch 设置限流配置
    monkeypatch.setattr("app.api.admin_tts_settings.settings.SMART_TTS_RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr("app.api.admin_tts_settings.settings.SMART_TTS_MAX_DAILY_REQUESTS", 2)
    monkeypatch.setattr("app.api.admin_tts_settings.settings.SMART_TTS_MAX_DAILY_CHARACTERS", 1000)
    monkeypatch.setattr("app.api.admin_tts_settings.settings.SMART_TTS_MAX_REQUESTS_PER_RUN", 10)
    
    # 创建测试用的 settings 对象
    test_settings = Settings()
    test_settings.SMART_TTS_RATE_LIMIT_ENABLED = True
    test_settings.SMART_TTS_MAX_DAILY_REQUESTS = 2
    test_settings.SMART_TTS_MAX_DAILY_CHARACTERS = 1000
    test_settings.SMART_TTS_MAX_REQUESTS_PER_RUN = 10
    
    # 触发一次限流（记录 2 次请求，第 3 次会被限流）
    assert should_allow(100, settings=test_settings) is True
    record_request(100, settings=test_settings)
    assert should_allow(100, settings=test_settings) is True
    record_request(100, settings=test_settings)
    assert should_allow(100, settings=test_settings) is False  # 被限流
    
    # 获取设置
    result = await get_tts_settings(db_session)
    
    # 断言
    assert result.rate_limit_enabled is True
    assert result.rate_limit_info is not None
    assert result.rate_limit_info.max_daily_requests == 2
    assert result.rate_limit_info.max_daily_characters == 1000
    assert result.rate_limit_info.max_requests_per_run == 10
    assert result.rate_limit_info.last_limited_at is not None
    assert result.rate_limit_info.last_limited_reason == "daily_requests_exceeded"


@pytest.mark.asyncio
async def test_tts_settings_exposes_health_status(db_session, monkeypatch):
    """测试正确暴露健康状态"""
    # 使用 monkeypatch 设置 TTS 启用
    monkeypatch.setattr("app.api.admin_tts_settings.settings.SMART_TTS_ENABLED", True)
    monkeypatch.setattr("app.api.admin_tts_settings.settings.SMART_TTS_PROVIDER", "dummy")
    
    result = await get_tts_settings(db_session)
    
    # 断言
    assert result.enabled is True
    assert result.provider == "dummy"
    assert result.status in ["ok", "degraded"]  # 根据引擎初始化结果


@pytest.mark.asyncio
async def test_preset_usage_has_heat_fields(db_session):
    """测试预设使用统计包含热度字段"""
    # 创建测试预设
    preset1 = TTSVoicePreset(
        id=1,
        name="热门预设",
        provider="dummy",
        language="zh-CN",
        voice="zh-CN-female-1",
        is_default=False
    )
    preset2 = TTSVoicePreset(
        id=2,
        name="沉睡预设",
        provider="dummy",
        language="zh-CN",
        voice="zh-CN-male-1",
        is_default=False
    )
    preset3 = TTSVoicePreset(
        id=3,
        name="冷门预设",
        provider="dummy",
        language="en-US",
        voice="en-US-female-1",
        is_default=False
    )
    
    db_session.add_all([preset1, preset2, preset3])
    await db_session.commit()
    
    # 创建测试 EBook
    ebook1 = EBook(id=1, title="测试1", author="作者1", language="zh-CN")
    ebook2 = EBook(id=2, title="测试2", author="作者2", language="zh-CN")
    ebook3 = EBook(id=3, title="测试3", author="作者3", language="zh-CN")
    ebook4 = EBook(id=4, title="测试4", author="作者4", language="zh-CN")
    ebook5 = EBook(id=5, title="测试5", author="作者5", language="zh-CN")
    ebook6 = EBook(id=6, title="测试6", author="作者6", language="zh-CN")
    ebook7 = EBook(id=7, title="测试7", author="作者7", language="en-US")
    
    db_session.add_all([ebook1, ebook2, ebook3, ebook4, ebook5, ebook6, ebook7])
    await db_session.commit()
    
    # 创建 Work Profile（绑定预设）
    # 预设1：绑定15个，生成12个（热门）
    for i in range(1, 16):
        profile = TTSWorkProfile(
            ebook_id=i,
            preset_id=1,
            enabled=True
        )
        db_session.add(profile)
    
    # 预设2：绑定10个，生成0个（沉睡）
    for i in range(1, 11):
        profile = TTSWorkProfile(
            ebook_id=i + 20,
            preset_id=2,
            enabled=True
        )
        db_session.add(profile)
    
    # 预设3：绑定2个，生成1个（冷门）
    profile3_1 = TTSWorkProfile(ebook_id=30, preset_id=3, enabled=True)
    profile3_2 = TTSWorkProfile(ebook_id=31, preset_id=3, enabled=True)
    db_session.add_all([profile3_1, profile3_2])
    await db_session.commit()
    
    # 创建 AudiobookFile（已生成 TTS）
    # 预设1：12个已生成
    now = datetime.utcnow()
    for i in range(1, 13):
        audiobook = AudiobookFile(
            ebook_id=i,
            file_path=f"/test{i}.wav",
            format="wav",
            is_tts_generated=True,
            tts_provider="dummy",
            created_at=now - timedelta(days=10)  # 10天前使用
        )
        db_session.add(audiobook)
    
    # 预设3：1个已生成
    audiobook3 = AudiobookFile(
        ebook_id=30,
        file_path="/test30.wav",
        format="wav",
        is_tts_generated=True,
        tts_provider="dummy",
        created_at=now - timedelta(days=5)
    )
    db_session.add(audiobook3)
    await db_session.commit()
    
    # 获取预设使用统计
    usages = await _compute_preset_usage(db_session)
    
    # 找到对应的预设
    usage1 = next((u for u in usages if u.id == 1), None)
    usage2 = next((u for u in usages if u.id == 2), None)
    usage3 = next((u for u in usages if u.id == 3), None)
    
    # 断言字段存在
    assert usage1 is not None
    assert hasattr(usage1, 'usage_ratio')
    assert hasattr(usage1, 'heat_level')
    assert hasattr(usage1, 'is_hot')
    assert hasattr(usage1, 'is_sleeping')
    assert hasattr(usage1, 'is_cold')
    
    # 断言预设1是热门
    assert usage1.bound_works_count == 15
    assert usage1.tts_generated_works_count == 12
    assert usage1.usage_ratio == pytest.approx(12 / 15, abs=0.01)
    assert usage1.is_hot is True
    assert usage1.heat_level == "hot"
    
    # 断言预设2是沉睡
    assert usage2 is not None
    assert usage2.bound_works_count == 10
    assert usage2.tts_generated_works_count == 0
    assert usage2.is_sleeping is True
    assert usage2.heat_level == "sleeping"
    
    # 断言预设3是冷门
    assert usage3 is not None
    assert usage3.bound_works_count == 2
    assert usage3.tts_generated_works_count == 1
    assert usage3.is_cold is True
    assert usage3.heat_level == "cold"


@pytest.mark.asyncio
async def test_preset_heat_levels_are_mutually_exclusive(db_session):
    """测试热度状态互斥：同一预设只能有一个状态为 True"""
    # 创建测试预设
    preset = TTSVoicePreset(
        id=100,
        name="测试预设",
        provider="dummy",
        is_default=False
    )
    db_session.add(preset)
    await db_session.commit()
    
    # 获取预设使用统计
    usages = await _compute_preset_usage(db_session)
    usage = next((u for u in usages if u.id == 100), None)
    
    if usage:
        # 断言最多只有一个状态为 True
        true_count = sum([
            usage.is_hot,
            usage.is_sleeping,
            usage.is_cold
        ])
        assert true_count <= 1, f"预设 {usage.id} 有多个热度状态为 True: hot={usage.is_hot}, sleeping={usage.is_sleeping}, cold={usage.is_cold}"
        
        # 断言 heat_level 与 bool 字段一致
        if usage.is_hot:
            assert usage.heat_level == "hot"
        elif usage.is_sleeping:
            assert usage.heat_level == "sleeping"
        elif usage.is_cold:
            assert usage.heat_level == "cold"
        else:
            assert usage.heat_level == "normal"


@pytest.mark.asyncio
async def test_classify_preset_heat_logic():
    """测试热度分类逻辑"""
    now = datetime.utcnow()
    
    # 测试热门：绑定 >= 10, usage_ratio >= 0.6, 最近30天有使用
    heat_level, is_hot, is_sleeping, is_cold = classify_preset_heat(
        bound_works_count=15,
        tts_generated_works_count=12,
        last_used_at=now - timedelta(days=10),
        usage_ratio=0.8
    )
    assert heat_level == "hot"
    assert is_hot is True
    assert is_sleeping is False
    assert is_cold is False
    
    # 测试沉睡：绑定 > 0, 30天未使用
    heat_level, is_hot, is_sleeping, is_cold = classify_preset_heat(
        bound_works_count=10,
        tts_generated_works_count=5,
        last_used_at=now - timedelta(days=35),
        usage_ratio=0.5
    )
    assert heat_level == "sleeping"
    assert is_hot is False
    assert is_sleeping is True
    assert is_cold is False
    
    # 测试从未使用（last_used_at 为 None）
    heat_level, is_hot, is_sleeping, is_cold = classify_preset_heat(
        bound_works_count=10,
        tts_generated_works_count=0,
        last_used_at=None,
        usage_ratio=0.0
    )
    assert heat_level == "sleeping"
    assert is_sleeping is True
    
    # 测试冷门：绑定 <= 2, 生成 <= 1
    heat_level, is_hot, is_sleeping, is_cold = classify_preset_heat(
        bound_works_count=2,
        tts_generated_works_count=1,
        last_used_at=now - timedelta(days=5),
        usage_ratio=0.5
    )
    assert heat_level == "cold"
    assert is_hot is False
    assert is_sleeping is False
    assert is_cold is True
    
    # 测试普通：不满足以上条件
    heat_level, is_hot, is_sleeping, is_cold = classify_preset_heat(
        bound_works_count=5,
        tts_generated_works_count=3,
        last_used_at=now - timedelta(days=15),
        usage_ratio=0.6
    )
    assert heat_level == "normal"
    assert is_hot is False
    assert is_sleeping is False
    assert is_cold is False


@pytest.mark.asyncio
async def test_tts_settings_includes_storage_overview(db_session, monkeypatch, tmp_path):
    """测试 TTS Settings API 返回中包含 storage_overview"""
    # 创建临时目录
    test_root = tmp_path / "tts_output"
    test_root.mkdir()
    (test_root / "test.mp3").write_bytes(b"test")
    
    monkeypatch.setattr("app.api.admin_tts_settings.settings.SMART_TTS_OUTPUT_ROOT", str(test_root))
    
    result = await get_tts_settings(db_session)
    
    # 断言 storage_overview 存在
    assert hasattr(result, "storage_overview")
    assert result.storage_overview is not None
    assert result.storage_overview.root == str(test_root)
    assert result.storage_overview.total_files >= 1
    assert "warning" in result.storage_overview.model_dump()


@pytest.mark.asyncio
async def test_tts_settings_storage_overview_warning_matches_threshold(db_session, monkeypatch, tmp_path):
    """测试 storage_overview 的 warning 根据阈值正确设置"""
    test_root = tmp_path / "tts_output"
    test_root.mkdir()
    
    monkeypatch.setattr("app.api.admin_tts_settings.settings.SMART_TTS_OUTPUT_ROOT", str(test_root))
    monkeypatch.setattr("app.api.admin_tts_settings.settings.SMART_TTS_STORAGE_WARN_SIZE_GB", 10.0)
    monkeypatch.setattr("app.api.admin_tts_settings.settings.SMART_TTS_STORAGE_CRITICAL_SIZE_GB", 30.0)
    
    # Mock build_overview 返回大体积
    from unittest.mock import patch
    from app.modules.tts.storage_service import TTSStorageOverview
    
    with patch("app.api.admin_tts_settings.build_overview") as mock_build:
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
        
        result = await get_tts_settings(db_session)
        assert result.storage_overview is not None
        assert result.storage_overview.warning == "high_usage"
        
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
        
        result = await get_tts_settings(db_session)
        assert result.storage_overview is not None
        assert result.storage_overview.warning == "critical"

