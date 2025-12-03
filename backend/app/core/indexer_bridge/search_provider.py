"""
Search provider that aggregates results from registered external adapters.
"""

from typing import List, Optional, Any
import asyncio
from loguru import logger

from app.core.indexer_bridge import (
    list_registered_sites,
    get_site_adapter,
)
from app.core.indexer_bridge.converters import external_result_to_search_item
from app.schemas.search import SearchResultItem


class ExternalIndexerSearchProvider:
    def __init__(
        self,
        *,
        site_ids: Optional[List[str]] = None,
        max_sites: int = 5,
        timeout: int = 15,
    ) -> None:
        self.site_ids = site_ids
        self.max_sites = max_sites
        self.timeout = timeout

    def _resolve_sites(self) -> List[str]:
        sites = self.site_ids or list_registered_sites()
        if self.max_sites and len(sites) > self.max_sites:
            sites = sites[: self.max_sites]
        return sites

    async def search(
        self,
        query: str,
        *,
        category: Optional[str] = None,
        limit: int = 50,
        **kwargs: Any,
    ) -> List[SearchResultItem]:
        sites = self._resolve_sites()
        if not sites:
            logger.debug("No external indexer adapters are registered")
            return []

        results = await self._gather_results(sites, query, category, limit, **kwargs)

        items: List[SearchResultItem] = []
        for payload in results:
            try:
                items.append(SearchResultItem(**payload))
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to instantiate SearchResultItem: %s", exc)
        items.sort(key=lambda item: item.seeders, reverse=True)
        return items[:limit]

    async def _gather_results(
        self,
        sites: List[str],
        query: str,
        category: Optional[str],
        limit: int,
        **kwargs: Any,
    ) -> List[dict]:
        async def _search_site(site_id: str) -> List[dict]:
            adapter = get_site_adapter(site_id)
            if not adapter:
                logger.debug("No adapter registered for site_id=%s", site_id)
                return []
            try:
                adapter_results = await adapter.search(
                    query=query,
                    site_id=site_id,
                    category=category,
                    page=0,
                    **kwargs,
                )
                return [
                    external_result_to_search_item(result) for result in adapter_results
                ][:limit]
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("External search failed for %s: %s", site_id, exc)
                return []

        tasks = [_search_site(site_id) for site_id in sites]
        try:
            gathered = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=False), timeout=self.timeout
            )
        except asyncio.TimeoutError:
            logger.warning("External indexer search timed out after %ss", self.timeout)
            return []

        flattened: List[dict] = []
        for chunk in gathered:
            flattened.extend(chunk)
        return flattened

