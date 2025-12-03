"""
外部索引引擎 HTTP 客户端

使用 httpx 封装对远程索引服务的 HTTP 请求。
"""

from typing import Optional, List
import httpx
import logging
from urllib.parse import urljoin

from external_indexer_engine.config import get_engine_settings
from external_indexer_engine.models import RemoteTorrentItem, RemoteTorrentDetail

logger = logging.getLogger(__name__)

# 全局 HTTP 客户端实例（懒加载）
_client: Optional["ExternalIndexerHttpClient"] = None


class ExternalIndexerHttpClient:
    """
    外部索引引擎 HTTP 客户端
    """
    
    def __init__(self, base_url: str, timeout: int, api_key: Optional[str] = None):
        """
        初始化 HTTP 客户端
        
        Args:
            base_url: 服务基础 URL
            timeout: 超时时间（秒）
            api_key: API 密钥（可选）
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """
        获取或创建 HTTP 客户端实例（懒加载）
        
        Returns:
            httpx.AsyncClient 实例
        """
        if self._client is None:
            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=headers,
            )
        return self._client
    
    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def search_torrents(
        self,
        site_id: str,
        keyword: str,
        media_type: Optional[str] = None,
        categories: Optional[List[str]] = None,
        page: int = 1,
    ) -> List[RemoteTorrentItem]:
        """
        搜索种子
        
        Args:
            site_id: 站点 ID
            keyword: 搜索关键词
            media_type: 媒体类型
            categories: 分类列表
            page: 页码
            
        Returns:
            种子项列表
        """
        try:
            client = await self._get_client()
            
            # 构建查询参数
            params = {
                "site_id": site_id,
                "q": keyword,
                "page": page,
            }
            if media_type:
                params["media_type"] = media_type
            if categories:
                params["categories"] = ",".join(categories)
            
            # 发送请求
            url = urljoin(self.base_url, "/api/ext-index/search")
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            # 解析 JSON
            data = response.json()
            
            # 处理响应数据（可能是列表或包含 results 字段的字典）
            if isinstance(data, dict) and "results" in data:
                items = data["results"]
            elif isinstance(data, list):
                items = data
            else:
                logger.warning(f"意外的响应格式: {type(data)}")
                return []
            
            # 转换为模型列表
            result = []
            for item in items:
                try:
                    result.append(RemoteTorrentItem(**item))
                except Exception as e:
                    logger.warning(f"解析种子项失败: {e}, item: {item}")
                    continue
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.warning(f"搜索种子 HTTP 错误: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.RequestError as e:
            logger.warning(f"搜索种子请求错误: {e}")
            return []
        except Exception as e:
            logger.warning(f"搜索种子失败: {e}", exc_info=True)
            return []
    
    async def fetch_rss(
        self,
        site_id: str,
        limit: int = 100,
    ) -> List[RemoteTorrentItem]:
        """
        获取 RSS 种子列表
        
        Args:
            site_id: 站点 ID
            limit: 返回数量限制
            
        Returns:
            种子项列表
        """
        try:
            client = await self._get_client()
            
            # 构建查询参数
            params = {
                "site_id": site_id,
                "limit": limit,
            }
            
            # 发送请求
            url = urljoin(self.base_url, "/api/ext-index/rss")
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            # 解析 JSON
            data = response.json()
            
            # 处理响应数据
            if isinstance(data, dict) and "results" in data:
                items = data["results"]
            elif isinstance(data, list):
                items = data
            else:
                logger.warning(f"意外的响应格式: {type(data)}")
                return []
            
            # 转换为模型列表
            result = []
            for item in items:
                try:
                    result.append(RemoteTorrentItem(**item))
                except Exception as e:
                    logger.warning(f"解析 RSS 项失败: {e}, item: {item}")
                    continue
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.warning(f"获取 RSS HTTP 错误: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.RequestError as e:
            logger.warning(f"获取 RSS 请求错误: {e}")
            return []
        except Exception as e:
            logger.warning(f"获取 RSS 失败: {e}", exc_info=True)
            return []
    
    async def get_detail(
        self,
        site_id: str,
        torrent_id: str,
    ) -> Optional[RemoteTorrentDetail]:
        """
        获取种子详细信息
        
        Args:
            site_id: 站点 ID
            torrent_id: 种子 ID
            
        Returns:
            种子详细信息，如果不存在则返回 None
        """
        try:
            client = await self._get_client()
            
            # 构建查询参数
            params = {
                "site_id": site_id,
                "torrent_id": torrent_id,
            }
            
            # 发送请求
            url = urljoin(self.base_url, "/api/ext-index/detail")
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            # 解析 JSON
            data = response.json()
            
            # 转换为模型
            return RemoteTorrentDetail(**data)
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"种子详情不存在: {site_id}/{torrent_id}")
                return None
            logger.warning(f"获取详情 HTTP 错误: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            logger.warning(f"获取详情请求错误: {e}")
            return None
        except Exception as e:
            logger.warning(f"获取详情失败: {e}", exc_info=True)
            return None
    
    async def get_download_link(
        self,
        site_id: str,
        torrent_id: str,
    ) -> Optional[dict]:
        """
        获取种子下载链接
        
        Args:
            site_id: 站点 ID
            torrent_id: 种子 ID
            
        Returns:
            下载链接字典（如 {"download_url": "..."}），如果获取失败则返回 None
        """
        try:
            client = await self._get_client()
            
            # 构建查询参数
            params = {
                "site_id": site_id,
                "torrent_id": torrent_id,
            }
            
            # 发送请求
            url = urljoin(self.base_url, "/api/ext-index/download")
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            # 解析 JSON
            data = response.json()
            
            # 如果返回的是字符串，包装成字典
            if isinstance(data, str):
                return {"download_url": data}
            elif isinstance(data, dict):
                return data
            else:
                logger.warning(f"意外的下载链接格式: {type(data)}")
                return None
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"下载链接不存在: {site_id}/{torrent_id}")
                return None
            logger.warning(f"获取下载链接 HTTP 错误: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            logger.warning(f"获取下载链接请求错误: {e}")
            return None
        except Exception as e:
            logger.warning(f"获取下载链接失败: {e}", exc_info=True)
            return None


def get_http_client() -> ExternalIndexerHttpClient:
    """
    获取 HTTP 客户端单例（懒加载）
    
    Returns:
        ExternalIndexerHttpClient 实例
    """
    global _client
    if _client is None:
        settings = get_engine_settings()
        _client = ExternalIndexerHttpClient(
            base_url=settings.base_url,
            timeout=settings.timeout_seconds,
            api_key=settings.api_key,
        )
    return _client


async def close_http_client() -> None:
    """
    关闭 HTTP 客户端（用于清理资源）
    """
    global _client
    if _client:
        await _client.close()
        _client = None

