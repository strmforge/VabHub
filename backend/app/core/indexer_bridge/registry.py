"""
Adapter registry for the Indexer Bridge.
"""

from typing import Dict, Optional, List
from loguru import logger

from app.core.indexer_bridge.interfaces import ExternalIndexerSiteAdapter

_ADAPTERS: Dict[str, ExternalIndexerSiteAdapter] = {}


def register_site_adapter(site_id: str, adapter: ExternalIndexerSiteAdapter) -> None:
    if site_id in _ADAPTERS:
        logger.warning("Overwriting existing adapter for site_id=%s", site_id)
    _ADAPTERS[site_id] = adapter
    logger.info("Registered external indexer adapter for %s", site_id)


def unregister_site_adapter(site_id: str) -> None:
    if site_id in _ADAPTERS:
        _ADAPTERS.pop(site_id, None)
        logger.info("Unregistered external indexer adapter for %s", site_id)


def list_registered_sites() -> List[str]:
    return list(_ADAPTERS.keys())


def get_site_adapter(site_id: str) -> Optional[ExternalIndexerSiteAdapter]:
    return _ADAPTERS.get(site_id)


def register_default_adapters() -> None:
    """
    Hook for future default adapters. Currently there is no baked-in backend,
    so this method simply logs the absence of defaults.
    """
    if not _ADAPTERS:
        logger.debug("No default external indexer adapters configured")

