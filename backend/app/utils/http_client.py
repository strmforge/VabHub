"""
HTTP客户端工具
统一管理代理配置，用于TMDB、Github等需要代理的服务
HTTP客户端封装
"""

from typing import Optional, Dict, Any
import httpx
from loguru import logger
from app.core.config import settings


def get_proxy_config() -> Optional[str]:
    """
    获取代理配置（用于httpx）
    
    Returns:
        代理URL字符串，格式：http://proxy:port 或 socks5://proxy:port
        如果未配置代理，返回None
    """
    return settings.PROXY_HOST


def create_httpx_client(
    timeout: float = 30.0,
    follow_redirects: bool = True,
    use_proxy: bool = True
) -> httpx.AsyncClient:
    """
    创建httpx异步客户端（自动应用代理配置）
    
    Args:
        timeout: 超时时间（秒）
        follow_redirects: 是否跟随重定向
        use_proxy: 是否使用代理（如果配置了）
    
    Returns:
        httpx.AsyncClient实例
    """
    proxy_config = None
    if use_proxy:
        proxy_config = get_proxy_config()
        if proxy_config:
            logger.debug(f"TMDB请求使用代理: {proxy_config}")
    
    return httpx.AsyncClient(
        timeout=httpx.Timeout(timeout),
        follow_redirects=follow_redirects,
        proxy=proxy_config  # httpx使用proxy参数（单数）
    )


def create_httpx_sync_client(
    timeout: float = 30.0,
    follow_redirects: bool = True,
    use_proxy: bool = True
) -> httpx.Client:
    """
    创建httpx同步客户端（自动应用代理配置）
    
    Args:
        timeout: 超时时间（秒）
        follow_redirects: 是否跟随重定向
        use_proxy: 是否使用代理（如果配置了）
    
    Returns:
        httpx.Client实例
    """
    proxy_config = None
    if use_proxy:
        proxy_config = get_proxy_config()
        if proxy_config:
            logger.debug(f"使用代理: {proxy_config}")
    
    return httpx.Client(
        timeout=httpx.Timeout(timeout),
        follow_redirects=follow_redirects,
        proxy=proxy_config  # httpx使用proxy参数（单数）
    )

