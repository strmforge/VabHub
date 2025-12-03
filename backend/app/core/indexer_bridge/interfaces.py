"""
Protocol definitions for the Indexer Bridge layer.
"""

from typing import List, Optional, Protocol, Any

from app.core.indexer_bridge.models import (
    ExternalIndexerTorrentResult,
    ExternalIndexerTorrentDetail,
    ExternalIndexerSiteConfig,
)


class ExternalIndexerSiteAdapter(Protocol):
    """
    External indexer site adapter interface.

    Implementations should wrap a remote PT indexer provider and expose a
    predictable coroutine based API for VabHub to consume.
    """

    async def search(
        self,
        query: str,
        *,
        site_id: str,
        category: Optional[str] = None,
        page: int = 0,
        **kwargs: Any,
    ) -> List[ExternalIndexerTorrentResult]:
        ...

    async def fetch_rss(
        self,
        *,
        site_id: str,
        category: Optional[str] = None,
        limit: int = 100,
        **kwargs: Any,
    ) -> List[ExternalIndexerTorrentResult]:
        ...

    async def get_detail(
        self,
        torrent_id: str,
        *,
        site_id: str,
        **kwargs: Any,
    ) -> Optional[ExternalIndexerTorrentDetail]:
        ...

    async def get_download_link(
        self,
        torrent_id: str,
        *,
        site_id: str,
        **kwargs: Any,
    ) -> Optional[str]:
        ...

    async def check_login(
        self,
        *,
        site_id: str,
        **kwargs: Any,
    ) -> bool:
        ...

    async def get_user_data(
        self,
        *,
        site_id: str,
        **kwargs: Any,
    ) -> Optional[dict]:
        ...

    @property
    def site_config(self) -> ExternalIndexerSiteConfig:
        ...

