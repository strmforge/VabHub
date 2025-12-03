"""
TTS Factory 测试
"""

import pytest
from app.modules.tts.factory import get_tts_engine
from app.modules.tts.dummy import DummyTTSEngine
from app.modules.tts.http_provider import HttpTTSEngine
from app.core.config import Settings


def test_get_tts_engine_returns_dummy_by_default():
    """测试默认返回 dummy 引擎"""
    settings = Settings()
    settings.SMART_TTS_ENABLED = True
    settings.SMART_TTS_PROVIDER = "dummy"
    
    engine = get_tts_engine(settings)
    
    assert engine is not None
    assert isinstance(engine, DummyTTSEngine)


def test_get_tts_engine_returns_none_when_disabled():
    """测试未启用时返回 None"""
    settings = Settings()
    settings.SMART_TTS_ENABLED = False
    
    engine = get_tts_engine(settings)
    
    assert engine is None


def test_get_tts_engine_returns_http_engine():
    """测试返回 HTTP 引擎"""
    settings = Settings()
    settings.SMART_TTS_ENABLED = True
    settings.SMART_TTS_PROVIDER = "http"
    settings.SMART_TTS_HTTP_BASE_URL = "https://example.com/tts"
    
    engine = get_tts_engine(settings)
    
    assert engine is not None
    assert isinstance(engine, HttpTTSEngine)


def test_get_tts_engine_unsupported_provider():
    """测试不支持的 provider 抛出异常"""
    settings = Settings()
    settings.SMART_TTS_ENABLED = True
    settings.SMART_TTS_PROVIDER = "unknown"
    
    with pytest.raises(ValueError) as exc_info:
        get_tts_engine(settings)
    
    assert "Unsupported TTS provider" in str(exc_info.value)
    assert "unknown" in str(exc_info.value)


def test_get_tts_engine_http_provider_raises_when_no_base_url():
    """测试 HTTP provider 缺少 BASE_URL 时抛出异常"""
    settings = Settings()
    settings.SMART_TTS_ENABLED = True
    settings.SMART_TTS_PROVIDER = "http"
    settings.SMART_TTS_HTTP_BASE_URL = None
    
    with pytest.raises(RuntimeError) as exc_info:
        get_tts_engine(settings)
    
    assert "SMART_TTS_HTTP_BASE_URL is not configured" in str(exc_info.value)

