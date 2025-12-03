"""
TTS Playground API 测试
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

from app.core.config import Settings
from app.models.ebook import EBook
from app.models.tts_work_profile import TTSWorkProfile
from app.models.tts_voice_preset import TTSVoicePreset


@pytest.mark.asyncio
async def test_playground_synthesize_basic_dummy_success(db_session, monkeypatch):
    """测试基本的 dummy provider 合成成功"""
    from fastapi.testclient import TestClient
    
    # 设置 DEBUG=True
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_ENABLED", True)
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_PROVIDER", "dummy")
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_OUTPUT_ROOT", "./data/tts_output")
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_RATE_LIMIT_ENABLED", False)
    
    client = TestClient(app)
    response = client.post(
        "/api/dev/tts/playground/synthesize",
        json={
            "text": "这是一段测试文本。",
            "language": "zh-CN"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["audio_url"] is not None
    assert data["char_count"] == 9
    assert data["provider"] == "dummy"
    assert data["rate_limited"] is False


@pytest.mark.asyncio
async def test_playground_synthesize_rate_limited(db_session, monkeypatch):
    """测试 RateLimiter 生效"""
    from fastapi.testclient import TestClient
    
    # 设置 DEBUG=True 和非常小的限制
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_ENABLED", True)
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_PROVIDER", "dummy")
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_OUTPUT_ROOT", "./data/tts_output")
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_MAX_DAILY_CHARACTERS", 1)  # 非常小的限制
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_MAX_DAILY_REQUESTS", 1000)
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_MAX_REQUESTS_PER_RUN", 0)
    
    # 重置限流器状态
    from app.modules.tts.rate_limiter import reset
    reset()
    
    client = TestClient(app)
    response = client.post(
        "/api/dev/tts/playground/synthesize",
        json={
            "text": "这是一段超过限制的测试文本。",
            "skip_rate_limit": False
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["rate_limited"] is True
    assert data["rate_limit_reason"] is not None


@pytest.mark.asyncio
async def test_playground_synthesize_respects_ebook_profile(db_session, monkeypatch):
    """测试指定 ebook_id 时使用 Profile / Preset"""
    from fastapi.testclient import TestClient
    
    # 创建测试数据
    preset = TTSVoicePreset(
        id=1,
        name="测试预设",
        provider="dummy",
        language="zh-CN",
        voice="test_voice",
        speed=1.2,
        pitch=2.0,
        is_default=False
    )
    db_session.add(preset)
    
    ebook = EBook(
        id=1,
        title="测试小说",
        author="测试作者",
        language="zh-CN"
    )
    db_session.add(ebook)
    
    profile = TTSWorkProfile(
        ebook_id=1,
        preset_id=1,
        enabled=True
    )
    db_session.add(profile)
    await db_session.commit()
    
    # 设置 DEBUG=True
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_ENABLED", True)
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_PROVIDER", "dummy")
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_OUTPUT_ROOT", "./data/tts_output")
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_RATE_LIMIT_ENABLED", False)
    
    client = TestClient(app)
    response = client.post(
        "/api/dev/tts/playground/synthesize",
        json={
            "text": "测试文本",
            "ebook_id": 1
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["provider"] == "dummy"
    assert data["language"] == "zh-CN"
    assert data["voice"] == "test_voice"
    assert data["speed"] == 1.2
    assert data["pitch"] == 2.0


@pytest.mark.asyncio
async def test_playground_audio_endpoint_serves_file(db_session, monkeypatch):
    """测试音频文件端点能正确返回文件"""
    from fastapi.testclient import TestClient
    
    # 设置 DEBUG=True
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_ENABLED", True)
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_PROVIDER", "dummy")
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_OUTPUT_ROOT", "./data/tts_output")
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_RATE_LIMIT_ENABLED", False)
    
    client = TestClient(app)
    
    # 合成
    synthesize_response = client.post(
        "/api/dev/tts/playground/synthesize",
        json={
            "text": "测试音频文件",
            "language": "zh-CN"
        }
    )
    
    assert synthesize_response.status_code == 200
    synthesize_data = synthesize_response.json()
    assert synthesize_data["success"] is True
    assert synthesize_data["audio_url"] is not None
    
    # 提取文件名
    audio_url = synthesize_data["audio_url"]
    file_name = audio_url.split("/")[-1]
    
    # 获取音频文件
    audio_response = client.get(f"/api/dev/tts/playground/audio/{file_name}")
    
    assert audio_response.status_code == 200
    assert audio_response.headers["content-type"].startswith("audio/")


@pytest.mark.asyncio
async def test_playground_synthesize_requires_debug_mode(db_session, monkeypatch):
    """测试非 DEBUG 模式下返回 403"""
    from fastapi.testclient import TestClient
    
    monkeypatch.setattr("app.core.config.settings.DEBUG", False)
    
    client = TestClient(app)
    response = client.post(
        "/api/dev/tts/playground/synthesize",
        json={
            "text": "测试文本"
        }
    )
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_playground_synthesize_validates_text_length(db_session, monkeypatch):
    """测试文本长度验证"""
    from fastapi.testclient import TestClient
    
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_ENABLED", True)
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_PROVIDER", "dummy")
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_OUTPUT_ROOT", "./data/tts_output")
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_RATE_LIMIT_ENABLED", False)
    
    client = TestClient(app)
    
    # 测试空文本
    response = client.post(
        "/api/dev/tts/playground/synthesize",
        json={
            "text": ""
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "不能为空" in data["message"]
    
    # 测试超长文本
    long_text = "a" * 5001
    response = client.post(
        "/api/dev/tts/playground/synthesize",
        json={
            "text": long_text
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "5000" in data["message"]


@pytest.mark.asyncio
async def test_playground_audio_endpoint_handles_invalid_filename(db_session, monkeypatch):
    """测试音频端点处理无效文件名"""
    from fastapi.testclient import TestClient
    
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    
    client = TestClient(app)
    
    # 测试路径穿越尝试
    response = client.get("/api/dev/tts/playground/audio/../../../etc/passwd")
    
    assert response.status_code == 400
    
    # 测试不存在的文件
    response = client.get("/api/dev/tts/playground/audio/nonexistent_file.wav")
    
    assert response.status_code == 404

