"""
HTTP TTS Provider 测试
"""

import pytest
import json
import base64
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from tempfile import TemporaryDirectory

import httpx

from app.modules.tts.http_provider import HttpTTSEngine
from app.modules.tts.base import TTSRequest, TTSResult
from app.core.config import Settings


@pytest.fixture
def http_tts_settings():
    """创建 HTTP TTS 配置"""
    settings = Settings()
    settings.SMART_TTS_ENABLED = True
    settings.SMART_TTS_PROVIDER = "http"
    settings.SMART_TTS_HTTP_BASE_URL = "https://example.com/tts"
    settings.SMART_TTS_HTTP_METHOD = "POST"
    settings.SMART_TTS_HTTP_TIMEOUT = 15
    settings.SMART_TTS_HTTP_HEADERS = None
    settings.SMART_TTS_HTTP_BODY_TEMPLATE = None
    settings.SMART_TTS_HTTP_RESPONSE_MODE = "binary"
    settings.SMART_TTS_HTTP_RESPONSE_AUDIO_FIELD = "audio"
    settings.SMART_TTS_OUTPUT_ROOT = "./data/tts_output"
    return settings


@pytest.mark.asyncio
async def test_http_tts_binary_success(http_tts_settings):
    """测试 binary 模式成功场景"""
    engine = HttpTTSEngine(settings=http_tts_settings)
    
    fake_audio = b"FAKEAUDIO"
    
    with TemporaryDirectory() as tmpdir:
        target_path = Path(tmpdir) / "test_output.wav"
        
        request = TTSRequest(
            text="测试文本",
            language="zh-CN",
            voice="zh-CN-female-1"
        )
        
        # Mock httpx.AsyncClient
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = fake_audio
        mock_response.raise_for_status = MagicMock()
        
        with patch("app.modules.tts.http_provider.httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_client_instance
            
            result = await engine.synthesize(request, target_path)
            
            # 断言
            assert result.audio_path == target_path
            assert target_path.exists()
            assert target_path.read_bytes() == fake_audio
            assert result.duration_seconds is None
            
            # 验证请求参数
            mock_client_instance.post.assert_called_once()
            call_args = mock_client_instance.post.call_args
            assert call_args[0][0] == "https://example.com/tts"
            assert "json" in call_args[1]
            assert call_args[1]["json"]["text"] == "测试文本"
            assert call_args[1]["json"]["language"] == "zh-CN"
            assert call_args[1]["json"]["voice"] == "zh-CN-female-1"


@pytest.mark.asyncio
async def test_http_tts_json_base64_success(http_tts_settings):
    """测试 json_base64 模式成功场景"""
    http_tts_settings.SMART_TTS_HTTP_RESPONSE_MODE = "json_base64"
    http_tts_settings.SMART_TTS_HTTP_RESPONSE_AUDIO_FIELD = "audio"
    
    engine = HttpTTSEngine(settings=http_tts_settings)
    
    fake_audio = b"FAKEAUDIO"
    fake_audio_base64 = base64.b64encode(fake_audio).decode()
    
    with TemporaryDirectory() as tmpdir:
        target_path = Path(tmpdir) / "test_output.wav"
        
        request = TTSRequest(text="测试文本")
        
        # Mock httpx.AsyncClient
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"audio": fake_audio_base64})
        mock_response.raise_for_status = MagicMock()
        
        with patch("app.modules.tts.http_provider.httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_client_instance
            
            result = await engine.synthesize(request, target_path)
            
            # 断言
            assert result.audio_path == target_path
            assert target_path.exists()
            assert target_path.read_bytes() == fake_audio


@pytest.mark.asyncio
async def test_http_tts_raises_on_non_200(http_tts_settings):
    """测试非 200 状态码时抛出异常"""
    engine = HttpTTSEngine(settings=http_tts_settings)
    
    with TemporaryDirectory() as tmpdir:
        target_path = Path(tmpdir) / "test_output.wav"
        request = TTSRequest(text="测试文本")
        
        # Mock httpx.AsyncClient 返回 500
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_response
        ))
        
        with patch("app.modules.tts.http_provider.httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_client_instance
            
            with pytest.raises(RuntimeError) as exc_info:
                await engine.synthesize(request, target_path)
            
            assert "TTS HTTP request failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_http_tts_raises_when_no_audio_field(http_tts_settings):
    """测试 json_base64 模式但响应中没有音频字段时抛出异常"""
    http_tts_settings.SMART_TTS_HTTP_RESPONSE_MODE = "json_base64"
    http_tts_settings.SMART_TTS_HTTP_RESPONSE_AUDIO_FIELD = "audio"
    
    engine = HttpTTSEngine(settings=http_tts_settings)
    
    with TemporaryDirectory() as tmpdir:
        target_path = Path(tmpdir) / "test_output.wav"
        request = TTSRequest(text="测试文本")
        
        # Mock httpx.AsyncClient 返回没有 audio 字段的 JSON
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"message": "success"})
        mock_response.raise_for_status = MagicMock()
        
        with patch("app.modules.tts.http_provider.httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_client_instance
            
            with pytest.raises(RuntimeError) as exc_info:
                await engine.synthesize(request, target_path)
            
            assert "Audio field 'audio' not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_http_tts_with_custom_headers_and_body_template(http_tts_settings):
    """测试自定义 headers 和 body 模板"""
    http_tts_settings.SMART_TTS_HTTP_HEADERS = '{"Authorization": "Bearer token123", "Content-Type": "application/json"}'
    http_tts_settings.SMART_TTS_HTTP_BODY_TEMPLATE = '{"text": "{text}", "lang": "{language}", "voice_id": "{voice}"}'
    
    engine = HttpTTSEngine(settings=http_tts_settings)
    
    fake_audio = b"FAKEAUDIO"
    
    with TemporaryDirectory() as tmpdir:
        target_path = Path(tmpdir) / "test_output.wav"
        
        request = TTSRequest(
            text="测试文本",
            language="zh-CN",
            voice="zh-CN-female-1"
        )
        
        # Mock httpx.AsyncClient
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = fake_audio
        mock_response.raise_for_status = MagicMock()
        
        with patch("app.modules.tts.http_provider.httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_client_instance
            
            await engine.synthesize(request, target_path)
            
            # 验证 headers 和 body
            call_args = mock_client_instance.post.call_args
            assert call_args[1]["headers"]["Authorization"] == "Bearer token123"
            assert call_args[1]["json"]["text"] == "测试文本"
            assert call_args[1]["json"]["lang"] == "zh-CN"
            assert call_args[1]["json"]["voice_id"] == "zh-CN-female-1"


@pytest.mark.asyncio
async def test_http_tts_timeout(http_tts_settings):
    """测试超时异常"""
    engine = HttpTTSEngine(settings=http_tts_settings)
    
    with TemporaryDirectory() as tmpdir:
        target_path = Path(tmpdir) / "test_output.wav"
        request = TTSRequest(text="测试文本")
        
        # Mock httpx.AsyncClient 抛出超时异常
        with patch("app.modules.tts.http_provider.httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.post = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
            mock_client.return_value = mock_client_instance
            
            with pytest.raises(RuntimeError) as exc_info:
                await engine.synthesize(request, target_path)
            
            assert "timeout" in str(exc_info.value).lower()


def test_http_tts_init_raises_when_no_base_url():
    """测试初始化时缺少 BASE_URL 抛出异常"""
    settings = Settings()
    settings.SMART_TTS_HTTP_BASE_URL = None
    
    with pytest.raises(RuntimeError) as exc_info:
        HttpTTSEngine(settings=settings)
    
    assert "SMART_TTS_HTTP_BASE_URL is not configured" in str(exc_info.value)

