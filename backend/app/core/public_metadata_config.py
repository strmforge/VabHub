"""
公共 Metadata Key 配置层

用于发现页/榜单展示的公共 key 配置，与用户私有 key 完全分离。

策略说明：
- PUBLIC_*_KEY: 用于发现页热门/榜单展示，不用于刮削
- 私有 Key (TMDB_API_KEY 等): 用于元数据刮削和库内数据完整性
- 豆瓣/Bangumi: 无需 API Key，使用公共 API

优先级：
1. 公共 key 可用时，发现页使用公共 key
2. 公共 key 不可用但私有 key 可用时，允许用私有 key 做 discover
3. 都没有时，对应源返回空数据

Created: 0.0.3 DISCOVER-MUSIC-HOME
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from loguru import logger


class PublicMetadataKeys(BaseModel):
    """
    公共 Metadata Key 配置
    
    用于发现页/榜单展示，与用户私有 key 完全分离
    """
    # TMDB 公共发现 key（仅用于热门/流行列表，不用于刮削）
    tmdb_discover_key: Optional[str] = Field(
        default=None,
        description="TMDB 公共发现 key，用于发现页热门内容"
    )
    
    # 豆瓣公共配置（豆瓣无需 key，这里用于可能的 RSSHub 源配置）
    douban_rsshub_base: Optional[str] = Field(
        default=None,
        description="豆瓣 RSSHub 源地址（可选，默认使用直接 API）"
    )
    
    # Bangumi 公共配置（Bangumi 无需 key，这里预留扩展）
    bangumi_enabled: bool = Field(
        default=True,
        description="是否启用 Bangumi 数据源"
    )
    
    # 总开关
    enabled: bool = Field(
        default=True,
        description="是否启用公共 Metadata Key 功能"
    )


# 全局配置实例（懒加载）
_public_metadata_keys: Optional[PublicMetadataKeys] = None


def get_public_metadata_keys() -> PublicMetadataKeys:
    """
    获取公共 Metadata Key 配置
    
    来源优先级：
    1. 环境变量
    2. 默认值
    """
    global _public_metadata_keys
    
    if _public_metadata_keys is None:
        _public_metadata_keys = PublicMetadataKeys(
            tmdb_discover_key=os.getenv("PUBLIC_TMDB_DISCOVER_KEY"),
            douban_rsshub_base=os.getenv("PUBLIC_DOUBAN_RSSHUB_BASE"),
            bangumi_enabled=os.getenv("PUBLIC_BANGUMI_ENABLED", "true").lower() == "true",
            enabled=os.getenv("ENABLE_PUBLIC_METADATA_KEYS", "true").lower() == "true",
        )
        
        # 日志输出配置状态（不输出 key 值）
        logger.info(
            f"公共 Metadata 配置加载完成: "
            f"enabled={_public_metadata_keys.enabled}, "
            f"tmdb_discover_key={'已配置' if _public_metadata_keys.tmdb_discover_key else '未配置'}, "
            f"bangumi_enabled={_public_metadata_keys.bangumi_enabled}"
        )
    
    return _public_metadata_keys


def get_tmdb_key_for_discover() -> Optional[str]:
    """
    获取用于发现页的 TMDB Key
    
    优先级：
    1. 公共 key (PUBLIC_TMDB_DISCOVER_KEY)
    2. 私有 key (TMDB_API_KEY)
    3. 返回 None
    
    Returns:
        TMDB API Key 或 None
    """
    public_config = get_public_metadata_keys()
    
    # 如果公共配置被禁用，直接使用私有 key
    if not public_config.enabled:
        from app.core.config import settings
        return settings.TMDB_API_KEY or None
    
    # 优先使用公共 key
    if public_config.tmdb_discover_key:
        return public_config.tmdb_discover_key
    
    # 其次使用私有 key
    from app.core.config import settings
    return settings.TMDB_API_KEY or None


def get_discover_key_source() -> str:
    """
    获取当前发现页使用的 key 来源
    
    Returns:
        "public" | "private" | "none"
    """
    public_config = get_public_metadata_keys()
    
    if not public_config.enabled:
        from app.core.config import settings
        return "private" if settings.TMDB_API_KEY else "none"
    
    if public_config.tmdb_discover_key:
        return "public"
    
    from app.core.config import settings
    if settings.TMDB_API_KEY:
        return "private"
    
    return "none"


def is_douban_available() -> bool:
    """
    检查豆瓣数据源是否可用
    
    豆瓣无需 API Key，始终可用（除非被显式禁用）
    """
    public_config = get_public_metadata_keys()
    return public_config.enabled


def is_bangumi_available() -> bool:
    """
    检查 Bangumi 数据源是否可用
    
    Bangumi 无需 API Key，但可以通过配置禁用
    """
    public_config = get_public_metadata_keys()
    return public_config.enabled and public_config.bangumi_enabled


def get_douban_rsshub_base() -> Optional[str]:
    """
    获取豆瓣 RSSHub 源地址
    
    Returns:
        RSSHub 源地址或 None（使用默认直接 API）
    """
    public_config = get_public_metadata_keys()
    return public_config.douban_rsshub_base
