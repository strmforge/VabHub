"""
插件 HTTP 客户端

PLUGIN-SDK-1 实现
"""

from typing import Any, Optional
import httpx
from loguru import logger

from app.plugin_sdk.context import PluginContext


class HttpClient:
    """
    插件专用 HTTP 客户端
    
    封装 httpx，提供统一的 UA、超时、代理设置。
    
    Example:
        async with sdk.http as client:
            response = await client.get("https://api.example.com/data")
            data = response.json()
    """
    
    DEFAULT_TIMEOUT = 30.0
    USER_AGENT_TEMPLATE = "VabHub-Plugin/{plugin_id} (VabHub/{app_version})"
    
    def __init__(self, ctx: PluginContext):
        """
        初始化 HTTP 客户端
        
        Args:
            ctx: 插件上下文
        """
        self._ctx = ctx
        self._user_agent = self.USER_AGENT_TEMPLATE.format(
            plugin_id=ctx.plugin_id,
            app_version=ctx.app_version or "unknown"
        )
        self._client: Optional[httpx.AsyncClient] = None
    
    def _get_default_headers(self) -> dict[str, str]:
        """获取默认请求头"""
        return {
            "User-Agent": self._user_agent,
            "Accept": "application/json",
        }
    
    def _get_proxy_config(self) -> Optional[str]:
        """获取代理配置"""
        try:
            from app.core.config import settings
            return getattr(settings, "PROXY", None)
        except Exception:
            return None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            proxy = self._get_proxy_config()
            self._client = httpx.AsyncClient(
                headers=self._get_default_headers(),
                timeout=self.DEFAULT_TIMEOUT,
                proxy=proxy,
                follow_redirects=True,
            )
        return self._client
    
    async def get(
        self,
        url: str,
        *,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        """
        发送 GET 请求
        
        Args:
            url: 请求 URL
            params: 查询参数
            headers: 额外请求头
            timeout: 超时时间（秒）
            
        Returns:
            httpx.Response 对象
        """
        client = await self._get_client()
        return await client.get(
            url,
            params=params,
            headers=headers,
            timeout=timeout or self.DEFAULT_TIMEOUT,
        )
    
    async def post(
        self,
        url: str,
        *,
        data: Optional[dict[str, Any]] = None,
        json: Optional[Any] = None,
        headers: Optional[dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        """
        发送 POST 请求
        
        Args:
            url: 请求 URL
            data: 表单数据
            json: JSON 数据
            headers: 额外请求头
            timeout: 超时时间（秒）
            
        Returns:
            httpx.Response 对象
        """
        client = await self._get_client()
        return await client.post(
            url,
            data=data,
            json=json,
            headers=headers,
            timeout=timeout or self.DEFAULT_TIMEOUT,
        )
    
    async def put(
        self,
        url: str,
        *,
        data: Optional[dict[str, Any]] = None,
        json: Optional[Any] = None,
        headers: Optional[dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        """发送 PUT 请求"""
        client = await self._get_client()
        return await client.put(
            url,
            data=data,
            json=json,
            headers=headers,
            timeout=timeout or self.DEFAULT_TIMEOUT,
        )
    
    async def delete(
        self,
        url: str,
        *,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        """发送 DELETE 请求"""
        client = await self._get_client()
        return await client.delete(
            url,
            params=params,
            headers=headers,
            timeout=timeout or self.DEFAULT_TIMEOUT,
        )
    
    async def close(self) -> None:
        """关闭 HTTP 客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self) -> "HttpClient":
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """异步上下文管理器退出"""
        await self.close()
