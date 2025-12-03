"""
Local Intel 站点 HTTP 客户端实现（Phase 4）
基于 httpx + Site 模型
"""

from __future__ import annotations

import httpx
from typing import Any, Mapping
from loguru import logger

from .http_clients import SiteHttpClient
from .site_profiles import IntelSiteProfile


class HttpxSiteHttpClient:
    """基于 httpx 的站点 HTTP 客户端实现。"""

    def __init__(
        self,
        site_id: str,
        site_url: str,
        cookies: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        初始化客户端。

        Args:
            site_id: 站点标识（如 "hdsky", "ttg"）
            site_url: 站点基础 URL（如 "https://hdsky.me"）
            cookies: Cookie 字符串（格式：key1=value1; key2=value2）
            user_agent: User-Agent 字符串（可选）
        """
        self.site_id = site_id
        self.site_url = site_url.rstrip("/")
        self.cookies = self._parse_cookies(cookies) if cookies else {}
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self._client: httpx.AsyncClient | None = None

    def _parse_cookies(self, cookie_str: str) -> dict[str, str]:
        """解析 Cookie 字符串为字典。"""
        cookies = {}
        if not cookie_str:
            return cookies

        for item in cookie_str.split(";"):
            item = item.strip()
            if "=" in item:
                key, value = item.split("=", 1)
                cookies[key.strip()] = value.strip()

        return cookies

    async def _ensure_client(self) -> httpx.AsyncClient:
        """确保 HTTP 客户端已创建。"""
        if self._client is None:
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
            self._client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers=headers,
                cookies=self.cookies,
            )
        return self._client

    async def close(self) -> None:
        """关闭 HTTP 客户端。"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def fetch(
        self,
        path_or_url: str,
        *,
        method: str = "GET",
        params: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> str:
        """
        发送 HTTP 请求并返回响应文本。

        Args:
            path_or_url: 路径（相对于 site_url）或完整 URL
            method: HTTP 方法
            params: URL 查询参数
            data: 请求体数据（用于 POST）

        Returns:
            响应 HTML 文本

        Raises:
            httpx.HTTPError: 请求失败
        """
        client = await self._ensure_client()

        # 构建完整 URL
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            url = path_or_url
        else:
            url = f"{self.site_url}/{path_or_url.lstrip('/')}"

        try:
            if method.upper() == "POST":
                response = await client.post(url, params=params, data=data)
            else:
                response = await client.get(url, params=params)

            response.raise_for_status()
            return response.text

        except httpx.HTTPStatusError as e:
            logger.error(
                f"LocalIntel: 站点 {self.site_id} HTTP {method} {url} 失败: "
                f"status={e.response.status_code}"
            )
            raise
        except httpx.RequestError as e:
            logger.error(f"LocalIntel: 站点 {self.site_id} 请求失败: {e}")
            raise

    async def fetch_hr_page(self, profile: IntelSiteProfile) -> str:
        """
        获取 HR 页面 HTML。

        Args:
            profile: 站点配置（包含 HR 页面路径）

        Returns:
            HR 页面 HTML
        """
        if not profile.hr or not profile.hr.enabled:
            raise ValueError(f"站点 {self.site_id} 的 HR 功能未启用")
        
        hr_path = profile.hr.page_path or "hr.php"
        return await self.fetch(hr_path)

    async def fetch_inbox_page(
        self,
        profile: IntelSiteProfile,
        *,
        page: int = 1,
    ) -> str:
        """
        获取站内信页面 HTML。

        Args:
            profile: 站点配置（包含站内信页面路径）
            page: 页码（从 1 开始）

        Returns:
            站内信页面 HTML
        """
        if not profile.inbox or not profile.inbox.enabled:
            raise ValueError(f"站点 {self.site_id} 的站内信功能未启用")

        inbox_path = profile.inbox.page_path or "messages.php"
        # 支持分页参数（各站点格式可能不同，这里用通用格式）
        params = {"page": page} if page > 1 else None
        return await self.fetch(inbox_path, params=params)

