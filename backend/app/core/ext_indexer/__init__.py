"""
外部索引桥接模块

提供统一的接口，用于集成外部 PT 索引引擎的搜索能力。
支持动态加载外部模块，优雅降级，不影响主流程。
"""

from app.core.ext_indexer.models import (
    ExternalTorrentResult,
    ExternalTorrentDetail,
    ExternalSiteConfig,
)
from app.core.ext_indexer.interfaces import (
    ExternalSiteAdapter,
    ExternalIndexerRuntime,
    ExternalAuthBridge,
)
from app.core.ext_indexer.registry import (
    register_site_adapter,
    get_site_adapter,
    list_registered_sites,
    set_runtime,
    get_runtime,
    set_auth_bridge,
    get_auth_bridge,
)
from app.core.ext_indexer.runtime import DynamicModuleRuntime
from app.core.ext_indexer.auth_bridge import (
    ExternalAuthState,
    NoopExternalAuthBridge,
)
from app.core.ext_indexer.site_importer import (
    load_all_site_configs,
    get_site_config,
)
from app.core.ext_indexer.search_provider import ExternalIndexerSearchProvider

__all__ = [
    # 数据模型
    "ExternalTorrentResult",
    "ExternalTorrentDetail",
    "ExternalSiteConfig",
    # 接口协议
    "ExternalSiteAdapter",
    "ExternalIndexerRuntime",
    "ExternalAuthBridge",
    # 注册表
    "register_site_adapter",
    "get_site_adapter",
    "list_registered_sites",
    "set_runtime",
    "get_runtime",
    "set_auth_bridge",
    "get_auth_bridge",
    # 运行时
    "DynamicModuleRuntime",
    # 授权桥
    "ExternalAuthState",
    "NoopExternalAuthBridge",
    # 站点配置
    "load_all_site_configs",
    "get_site_config",
    # 搜索提供者
    "ExternalIndexerSearchProvider",
]

