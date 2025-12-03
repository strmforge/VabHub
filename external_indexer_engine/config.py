"""
外部索引引擎配置管理

从环境变量读取配置，提供带缓存的配置获取函数。
"""

import os
from typing import Optional
from functools import lru_cache
from pydantic import BaseSettings, Field


class EngineSettings(BaseSettings):
    """
    外部索引引擎配置
    """
    base_url: str = Field(
        default="",
        env="EXTERNAL_INDEXER_ENGINE_BASE_URL",
        description="外部索引服务基础 URL（如 http://127.0.0.1:9000）",
    )
    timeout_seconds: int = Field(
        default=15,
        env="EXTERNAL_INDEXER_ENGINE_HTTP_TIMEOUT",
        description="HTTP 请求超时时间（秒）",
    )
    api_key: Optional[str] = Field(
        default=None,
        env="EXTERNAL_INDEXER_ENGINE_API_KEY",
        description="API 密钥（如果设置，会作为 Header 发送）",
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置缓存
_settings: Optional[EngineSettings] = None


@lru_cache(maxsize=1)
def get_engine_settings() -> EngineSettings:
    """
    获取外部索引引擎配置（带缓存）
    
    Returns:
        引擎配置对象
    """
    global _settings
    if _settings is None:
        _settings = EngineSettings()
    return _settings


def clear_settings_cache() -> None:
    """
    清除配置缓存（用于测试或热重载）
    """
    global _settings
    _settings = None
    get_engine_settings.cache_clear()

