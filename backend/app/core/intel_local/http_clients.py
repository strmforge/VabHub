"""
Local Intel 站点 HTTP 客户端注册表（Phase 3B）
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol

from .site_profiles import IntelSiteProfile


class SiteHttpClient(Protocol):
    """抽象 PT 站点 HTTP 客户端。"""

    async def fetch(
        self,
        path_or_url: str,
        *,
        method: str = "GET",
        params: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> str:
        ...

    async def fetch_hr_page(self, profile: IntelSiteProfile) -> str:
        ...

    async def fetch_inbox_page(
        self,
        profile: IntelSiteProfile,
        *,
        page: int = 1,
    ) -> str:
        ...


class SiteHttpClientRegistry:
    """站点 HTTP 客户端注册表。"""

    def __init__(self) -> None:
        self._clients: dict[str, SiteHttpClient] = {}

    def register(self, site: str, client: SiteHttpClient) -> None:
        self._clients[site] = client

    def get(self, site: str) -> SiteHttpClient:
        try:
            return self._clients[site]
        except KeyError:
            raise KeyError(f"No SiteHttpClient registered for site={site!r}")


_http_client_registry: SiteHttpClientRegistry | None = None


def set_http_client_registry(registry: SiteHttpClientRegistry) -> None:
    global _http_client_registry
    _http_client_registry = registry


def get_http_client_registry() -> SiteHttpClientRegistry:
    global _http_client_registry
    if _http_client_registry is None:
        _http_client_registry = SiteHttpClientRegistry()
    return _http_client_registry

