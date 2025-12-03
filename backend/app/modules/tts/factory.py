"""
TTS 引擎工厂

根据配置选择对应的 TTS 提供商。
"""

from typing import Optional, TYPE_CHECKING
from loguru import logger

from app.core.config import Settings
from .base import TTSEngine
from .dummy import DummyTTSEngine

if TYPE_CHECKING:
    from .http_provider import HttpTTSEngine


def get_tts_engine(settings: Settings) -> Optional[TTSEngine]:
    """
    根据配置获取 TTS 引擎
    
    Args:
        settings: 应用配置
    
    Returns:
        Optional[TTSEngine]: TTS 引擎实例，如果未启用则返回 None
    
    Raises:
        ValueError: 如果 provider 不支持
        RuntimeError: 如果 HTTP provider 配置不完整
    """
    if not settings.SMART_TTS_ENABLED:
        return None
    
    provider = (settings.SMART_TTS_PROVIDER or "dummy").lower().strip()
    
    if provider == "dummy":
        return DummyTTSEngine()
    
    if provider == "http":
        # 延迟导入，避免循环依赖
        from .http_provider import HttpTTSEngine
        return HttpTTSEngine(settings=settings)
    
    # 未来可以扩展其它 provider
    # elif provider == "edge_tts":
    #     from .edge_tts_provider import EdgeTTSEngine
    #     return EdgeTTSEngine(settings=settings)
    
    raise ValueError(f"Unsupported TTS provider: {provider}")

