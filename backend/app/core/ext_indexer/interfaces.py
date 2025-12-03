"""
外部索引桥接接口协议

定义外部索引引擎需要实现的接口。
"""

from typing import Protocol, Optional, List, Dict, Any
from datetime import datetime

from app.core.ext_indexer.models import (
    ExternalTorrentResult,
    ExternalTorrentDetail,
)


class ExternalSiteAdapter(Protocol):
    """
    单站适配器协议
    
    每个站点需要实现此协议，提供搜索、RSS、详情等功能。
    """
    
    async def search(
        self,
        keyword: str,
        *,
        media_type: Optional[str] = None,
        categories: Optional[List[str]] = None,
        page: int = 1,
    ) -> List[ExternalTorrentResult]:
        """
        搜索种子
        
        Args:
            keyword: 搜索关键词
            media_type: 媒体类型（如 movie/tv）
            categories: 分类列表
            page: 页码（从 1 开始）
            
        Returns:
            搜索结果列表
        """
        ...
    
    async def fetch_rss(
        self,
        *,
        limit: int = 100,
    ) -> List[ExternalTorrentResult]:
        """
        获取 RSS 种子列表
        
        Args:
            limit: 返回数量限制
            
        Returns:
            RSS 种子列表
        """
        ...
    
    async def get_detail(
        self,
        torrent_id: str,
    ) -> Optional[ExternalTorrentDetail]:
        """
        获取种子详细信息
        
        Args:
            torrent_id: 种子 ID
            
        Returns:
            种子详细信息，如果不存在则返回 None
        """
        ...
    
    async def get_download_link(
        self,
        torrent_id: str,
    ) -> Optional[str]:
        """
        获取种子下载链接
        
        Args:
            torrent_id: 种子 ID
            
        Returns:
            下载链接（磁力或种子 URL），如果获取失败则返回 None
        """
        ...
    
    async def check_login(self) -> bool:
        """
        检查站点登录状态
        
        Returns:
            是否已登录
        """
        ...
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """
        获取用户统计信息
        
        Returns:
            用户统计信息字典（如上传量、下载量、分享率等）
        """
        ...


class ExternalIndexerRuntime(Protocol):
    """
    外部索引运行时协议
    
    外部索引引擎需要实现此协议，提供统一的搜索接口。
    """
    
    async def search_torrents(
        self,
        site_id: str,
        keyword: str,
        *,
        media_type: Optional[str] = None,
        categories: Optional[List[str]] = None,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        搜索种子
        
        Args:
            site_id: 站点 ID
            keyword: 搜索关键词
            media_type: 媒体类型
            categories: 分类列表
            page: 页码
            
        Returns:
            搜索结果字典列表
        """
        ...
    
    async def fetch_rss(
        self,
        site_id: str,
        *,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        获取 RSS 种子列表
        
        Args:
            site_id: 站点 ID
            limit: 返回数量限制
            
        Returns:
            RSS 种子字典列表
        """
        ...
    
    async def get_detail(
        self,
        site_id: str,
        torrent_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        获取种子详细信息
        
        Args:
            site_id: 站点 ID
            torrent_id: 种子 ID
            
        Returns:
            种子详细信息字典，如果不存在则返回 None
        """
        ...
    
    async def get_download_link(
        self,
        site_id: str,
        torrent_id: str,
    ) -> Optional[str]:
        """
        获取种子下载链接
        
        Args:
            site_id: 站点 ID
            torrent_id: 种子 ID
            
        Returns:
            下载链接，如果获取失败则返回 None
        """
        ...


class ExternalAuthBridge(Protocol):
    """
    外部授权桥接协议
    
    用于检查站点登录状态和风控状态。
    """
    
    async def get_auth_state(
        self,
        site_id: str,
    ) -> "ExternalAuthState":
        """
        获取站点授权状态
        
        Args:
            site_id: 站点 ID
            
        Returns:
            授权状态对象
        """
        ...

