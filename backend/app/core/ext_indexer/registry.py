"""
外部索引桥接注册表

管理站点适配器、运行时和授权桥接的注册。
"""

from typing import Dict, Optional
from threading import Lock
from loguru import logger

from app.core.ext_indexer.interfaces import (
    ExternalSiteAdapter,
    ExternalIndexerRuntime,
    ExternalAuthBridge,
)
from app.core.ext_indexer.auth_bridge import NoopExternalAuthBridge

# 全局注册表（线程安全）
_adapter_lock = Lock()
_ADAPTERS: Dict[str, ExternalSiteAdapter] = {}
_RUNTIME: Optional[ExternalIndexerRuntime] = None
_AUTH_BRIDGE: Optional[ExternalAuthBridge] = None

# 默认使用空操作授权桥接
_default_auth_bridge = NoopExternalAuthBridge()


def register_site_adapter(
    site_id: str,
    adapter: ExternalSiteAdapter,
) -> None:
    """
    注册站点适配器
    
    Args:
        site_id: 站点 ID
        adapter: 站点适配器实例
    """
    with _adapter_lock:
        if site_id in _ADAPTERS:
            logger.warning(f"站点适配器 {site_id} 已存在，将被覆盖")
        _ADAPTERS[site_id] = adapter
        logger.info(f"已注册站点适配器: {site_id}")


def get_site_adapter(
    site_id: str,
) -> Optional[ExternalSiteAdapter]:
    """
    获取站点适配器
    
    Args:
        site_id: 站点 ID
        
    Returns:
        站点适配器实例，如果不存在则返回 None
    """
    with _adapter_lock:
        return _ADAPTERS.get(site_id)


def list_registered_sites() -> list[str]:
    """
    列出所有已注册的站点 ID
    
    Returns:
        站点 ID 列表
    """
    with _adapter_lock:
        return list(_ADAPTERS.keys())


def set_runtime(runtime: Optional[ExternalIndexerRuntime]) -> None:
    """
    设置外部索引运行时
    
    Args:
        runtime: 外部索引运行时实例
    """
    global _RUNTIME
    _RUNTIME = runtime
    if runtime:
        logger.info("外部索引运行时已设置")
    else:
        logger.info("外部索引运行时已清除")


def get_runtime() -> Optional[ExternalIndexerRuntime]:
    """
    获取外部索引运行时
    
    Returns:
        外部索引运行时实例，如果未设置则返回 None
    """
    return _RUNTIME


def set_auth_bridge(bridge: Optional[ExternalAuthBridge]) -> None:
    """
    设置授权桥接
    
    Args:
        bridge: 授权桥接实例
    """
    global _AUTH_BRIDGE
    _AUTH_BRIDGE = bridge
    if bridge:
        logger.info("授权桥接已设置")
    else:
        logger.info("授权桥接已清除，使用默认空操作桥接")


def get_auth_bridge() -> ExternalAuthBridge:
    """
    获取授权桥接
    
    Returns:
        授权桥接实例，如果未设置则返回默认的空操作桥接
    """
    return _AUTH_BRIDGE if _AUTH_BRIDGE is not None else _default_auth_bridge

