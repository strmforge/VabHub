"""
Indexer Bridge public exports.

This module exposes a neutral set of helpers that allow VabHub to bridge to
external PT indexer engines without hard‑coding a specific vendor.
"""

from app.core.indexer_bridge.interfaces import ExternalIndexerSiteAdapter
from app.core.indexer_bridge.models import (
    ExternalIndexerTorrentResult,
    ExternalIndexerTorrentDetail,
    ExternalIndexerSiteConfig,
)
from app.core.indexer_bridge.registry import (
    register_site_adapter,
    unregister_site_adapter,
    list_registered_sites,
    get_site_adapter,
    register_default_adapters,
)
from app.core.indexer_bridge.runtime import ExternalIndexerRuntime, get_default_runtime
from app.core.indexer_bridge.search_provider import ExternalIndexerSearchProvider
from app.core.indexer_bridge.auth_bridge import (
    ExternalIndexerAuthBridge,
    ExternalIndexerSessionState,
)

__all__ = [
    "ExternalIndexerSiteAdapter",
    "ExternalIndexerTorrentResult",
    "ExternalIndexerTorrentDetail",
    "ExternalIndexerSiteConfig",
    "register_site_adapter",
    "unregister_site_adapter",
    "list_registered_sites",
    "get_site_adapter",
    "register_default_adapters",
    "ExternalIndexerRuntime",
    "get_default_runtime",
    "ExternalIndexerSearchProvider",
    "ExternalIndexerAuthBridge",
    "ExternalIndexerSessionState",
]

