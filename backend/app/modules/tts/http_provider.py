"""
HTTP TTS 引擎实现

通用 HTTP TTS 提供者，支持通过配置接入任意 HTTP TTS 服务。
"""

import json
import base64
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
import httpx

from app.core.config import Settings
from .base import TTSEngine, TTSRequest, TTSResult
from .usage_tracker import record_success, record_error


class HttpTTSEngine:
    """HTTP TTS 引擎"""
    
    def __init__(self, settings: Settings):
        """
        初始化 HTTP TTS 引擎
        
        Args:
            settings: 应用配置
        """
        self.settings = settings
        
        # 验证必要配置
        if not settings.SMART_TTS_HTTP_BASE_URL:
            raise RuntimeError("SMART_TTS_HTTP_BASE_URL is not configured")
    
    async def synthesize(self, request: TTSRequest, target_path: Path) -> TTSResult:
        """
        通过 HTTP 请求合成语音
        
        Args:
            request: TTS 请求
            target_path: 目标音频文件路径
        
        Returns:
            TTSResult: 包含音频路径和时长（可选）
        """
        # 1. 解析配置
        base_url = self.settings.SMART_TTS_HTTP_BASE_URL
        method = self.settings.SMART_TTS_HTTP_METHOD.upper()
        timeout = self.settings.SMART_TTS_HTTP_TIMEOUT
        
        # 2. 解析 headers
        headers_dict: Dict[str, str] = {}
        if self.settings.SMART_TTS_HTTP_HEADERS:
            try:
                headers_dict = json.loads(self.settings.SMART_TTS_HTTP_HEADERS)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Invalid SMART_TTS_HTTP_HEADERS JSON: {e}")
        
        # 3. 解析 body 模板并填入 TTSRequest 数据
        body: Dict[str, Any] = {}
        if self.settings.SMART_TTS_HTTP_BODY_TEMPLATE:
            try:
                body_template_str = self.settings.SMART_TTS_HTTP_BODY_TEMPLATE
                # 先替换占位符，再解析 JSON
                body_template_str = body_template_str.replace("{text}", request.text)
                if request.language:
                    body_template_str = body_template_str.replace("{language}", request.language)
                if request.voice:
                    body_template_str = body_template_str.replace("{voice}", request.voice)
                if request.speed is not None:
                    body_template_str = body_template_str.replace("{speed}", str(request.speed))
                if request.pitch is not None:
                    body_template_str = body_template_str.replace("{pitch}", str(request.pitch))
                
                body = json.loads(body_template_str)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Invalid SMART_TTS_HTTP_BODY_TEMPLATE JSON: {e}")
        else:
            # 默认 body 结构
            body = {
                "text": request.text
            }
            if request.language:
                body["language"] = request.language
            if request.voice:
                body["voice"] = request.voice
            if request.speed is not None:
                body["speed"] = request.speed
            if request.pitch is not None:
                body["pitch"] = request.pitch
        
        # 4. 发送 HTTP 请求
        try:
            timeout_config = httpx.Timeout(timeout, connect=timeout)
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                if method == "POST":
                    resp = await client.post(base_url, headers=headers_dict, json=body)
                elif method == "GET":
                    resp = await client.get(base_url, headers=headers_dict, params=body)
                else:
                    raise RuntimeError(f"Unsupported HTTP method: {method}")
                
                # 检查状态码
                resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP TTS request failed with status {e.response.status_code}: {e}")
            error = RuntimeError(f"TTS HTTP request failed: {e.response.status_code} {e.response.text[:200]}")
            record_error(error, provider="http")
            raise error
        except httpx.TimeoutException as e:
            logger.error(f"HTTP TTS request timeout: {e}")
            error = RuntimeError(f"TTS HTTP request timeout after {timeout}s")
            record_error(error, provider="http")
            raise error
        except httpx.RequestError as e:
            logger.error(f"HTTP TTS request error: {e}")
            error = RuntimeError(f"TTS HTTP request error: {str(e)}")
            record_error(error, provider="http")
            raise error
        
        # 5. 解析响应 -> audio_bytes
        mode = self.settings.SMART_TTS_HTTP_RESPONSE_MODE
        audio_bytes: bytes
        
        if mode == "binary":
            audio_bytes = resp.content
        elif mode == "json_base64":
            try:
                data = resp.json()
                field = self.settings.SMART_TTS_HTTP_RESPONSE_AUDIO_FIELD or "audio"
                if field not in data:
                    raise RuntimeError(f"Audio field '{field}' not found in TTS response JSON")
                audio_base64 = data[field]
                audio_bytes = base64.b64decode(audio_base64)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Failed to parse TTS response as JSON: {e}")
            except base64.binascii.Error as e:
                raise RuntimeError(f"Failed to decode base64 audio from TTS response: {e}")
        else:
            raise RuntimeError(f"Unsupported TTS response mode: {mode}")
        
        if not audio_bytes:
            raise RuntimeError("TTS response contains empty audio data")
        
        # 6. 确保目标目录存在
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 7. 写入音频文件
        try:
            target_path.write_bytes(audio_bytes)
            logger.debug(f"HTTP TTS audio saved to: {target_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to write TTS audio file: {e}")
        
        # 8. 返回结果（duration_seconds 暂时为 None，由 AudiobookImporter 再 probe）
        return TTSResult(
            audio_path=target_path,
            duration_seconds=None
        )

