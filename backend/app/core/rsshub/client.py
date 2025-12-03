"""
RSSHub客户端封装
"""

import os
import httpx
from typing import Optional
from loguru import logger

from app.core.config import settings


class RSSHubClient:
    """RSSHub客户端"""
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        """
        初始化RSSHub客户端
        
        Args:
            base_url: RSSHub基础URL，默认从环境变量RSSHUB_BASE_URL获取
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url or settings.RSSHUB_BASE_URL
        self.timeout = timeout
    
    async def fetch_rss(self, path: str) -> str:
        """
        获取RSS Feed
        
        Args:
            path: RSSHub路径（如 /douban/movie/ustop）
            
        Returns:
            RSS XML字符串
            
        Raises:
            httpx.HTTPStatusError: HTTP错误
            httpx.TimeoutException: 请求超时
        """
        # 确保路径以/开头
        if not path.startswith('/'):
            path = '/' + path
        
        url = f"{self.base_url}{path}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                return response.text
        except httpx.TimeoutException as e:
            logger.error(f"RSSHub请求超时: {url}, 超时时间: {self.timeout}秒")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"RSSHub请求失败: {url}, 状态码: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"RSSHub请求异常: {url}, 错误: {e}")
            raise
    
    async def fetch_rss_items(self, path: str, limit: Optional[int] = None) -> list:
        """
        获取RSS Feed并解析为项列表（用于预览）
        
        Args:
            path: RSSHub路径
            limit: 限制返回的项数量
            
        Returns:
            RSS项列表，格式: [{"title": "...", "link": "...", "pub_date": "...", "description": "..."}, ...]
        """
        import feedparser
        
        rss_xml = await self.fetch_rss(path)
        feed = feedparser.parse(rss_xml)
        
        items = []
        for entry in feed.entries[:limit] if limit else feed.entries:
            items.append({
                "title": entry.get('title', ''),
                "link": entry.get('link', ''),
                "pub_date": entry.get('published', ''),
                "description": entry.get('description', '')[:200]  # 限制描述长度
            })
        
        return items


# 全局客户端实例
_rsshub_client: Optional[RSSHubClient] = None


def get_rsshub_client() -> RSSHubClient:
    """获取RSSHub客户端单例"""
    global _rsshub_client
    if _rsshub_client is None:
        _rsshub_client = RSSHubClient()
    return _rsshub_client

