"""
External indexer runtime abstraction.

The runtime is intentionally lightweight – it simply tracks availability of
external adapters and can be extended later if a concrete backend is plugged in.
"""

from __future__ import annotations

from typing import Optional, Any, List
from loguru import logger

from app.core.indexer_bridge.models import ExternalIndexerTorrentResult


class ExternalIndexerRuntime:
    """Placeholder runtime that can be expanded with real integrations."""

    def __init__(self) -> None:
        self.available = False  # will be toggled if a concrete backend is added
        logger.debug("ExternalIndexerRuntime initialized (no external backend configured)")

    def configure(self, **kwargs: Any) -> None:
        """Optionally configure runtime details."""
        self.available = kwargs.get("available", False)

    async def search(
        self,
        site_id: str,
        query: str,
        *,
        category: Optional[str] = None,
        page: int = 0,
        **kwargs: Any,
    ) -> List[ExternalIndexerTorrentResult]:
        logger.debug(
            "External search requested (site=%s, query=%s, category=%s, page=%s) "
            "but no backend is configured",
            site_id,
            query,
            category,
            page,
        )
        return []


_default_runtime: Optional[ExternalIndexerRuntime] = None


def get_default_runtime() -> ExternalIndexerRuntime:
    global _default_runtime
    if _default_runtime is None:
        _default_runtime = ExternalIndexerRuntime()
    return _default_runtime

