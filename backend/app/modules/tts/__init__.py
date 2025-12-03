"""
TTS（文本转语音）模块

提供可插拔的 TTS 适配层，支持多种 TTS 提供商。
"""

from .factory import get_tts_engine
from .base import TTSRequest, TTSResult, TTSEngine

__all__ = ["get_tts_engine", "TTSRequest", "TTSResult", "TTSEngine"]

