"""
Chain 管理器
统一管理所有Chain实例
"""

from typing import Optional
from loguru import logger

from app.chain.base import ChainBase
from app.chain.storage import StorageChain
from app.chain.subscribe import SubscribeChain
from app.chain.download import DownloadChain
from app.chain.search import SearchChain
from app.chain.workflow import WorkflowChain
from app.chain.site import SiteChain
from app.chain.music import MusicChain
from app.chain.dashboard import DashboardChain


class ChainManager:
    """Chain管理器"""
    
    def __init__(self):
        self._storage_chain: Optional[StorageChain] = None
        self._subscribe_chain: Optional[SubscribeChain] = None
        self._download_chain: Optional[DownloadChain] = None
        self._search_chain: Optional[SearchChain] = None
        self._workflow_chain: Optional[WorkflowChain] = None
        self._site_chain: Optional[SiteChain] = None
        self._music_chain: Optional[MusicChain] = None
        self._dashboard_chain: Optional[DashboardChain] = None
    
    @property
    def storage(self) -> StorageChain:
        """获取StorageChain实例"""
        if self._storage_chain is None:
            self._storage_chain = StorageChain()
        return self._storage_chain
    
    @property
    def subscribe(self) -> SubscribeChain:
        """获取SubscribeChain实例"""
        if self._subscribe_chain is None:
            self._subscribe_chain = SubscribeChain()
        return self._subscribe_chain
    
    @property
    def download(self) -> DownloadChain:
        """获取DownloadChain实例"""
        if self._download_chain is None:
            self._download_chain = DownloadChain()
        return self._download_chain
    
    @property
    def search(self) -> SearchChain:
        """获取SearchChain实例"""
        if self._search_chain is None:
            self._search_chain = SearchChain()
        return self._search_chain
    
    @property
    def workflow(self) -> WorkflowChain:
        """获取WorkflowChain实例"""
        if self._workflow_chain is None:
            self._workflow_chain = WorkflowChain()
        return self._workflow_chain
    
    @property
    def site(self) -> SiteChain:
        """获取SiteChain实例"""
        if self._site_chain is None:
            self._site_chain = SiteChain()
        return self._site_chain
    
    @property
    def music(self) -> MusicChain:
        """获取MusicChain实例"""
        if self._music_chain is None:
            self._music_chain = MusicChain()
        return self._music_chain
    
    @property
    def dashboard(self) -> DashboardChain:
        """获取DashboardChain实例"""
        if self._dashboard_chain is None:
            self._dashboard_chain = DashboardChain()
        return self._dashboard_chain
    
    def clear_cache(self, chain_type: Optional[str] = None):
        """
        清除缓存
        
        Args:
            chain_type: Chain类型（storage, subscribe, download, search, workflow, site, music, dashboard），如果为None则清除所有
        """
        if chain_type is None:
            # 清除所有Chain的缓存
            if self._storage_chain:
                self._storage_chain._cache.clear()
            if self._subscribe_chain:
                self._subscribe_chain._cache.clear()
            if self._download_chain:
                self._download_chain._cache.clear()
            if self._search_chain:
                self._search_chain._cache.clear()
            if self._workflow_chain:
                self._workflow_chain._cache.clear()
            if self._site_chain:
                self._site_chain._cache.clear()
            if self._music_chain:
                self._music_chain._cache.clear()
            if self._dashboard_chain:
                self._dashboard_chain._cache.clear()
            logger.info("已清除所有Chain缓存")
        else:
            # 清除特定Chain的缓存
            chain_map = {
                "storage": self._storage_chain,
                "subscribe": self._subscribe_chain,
                "download": self._download_chain,
                "search": self._search_chain,
                "workflow": self._workflow_chain,
                "site": self._site_chain,
                "music": self._music_chain,
                "dashboard": self._dashboard_chain
            }
            chain = chain_map.get(chain_type)
            if chain:
                chain._cache.clear()
                logger.info(f"已清除{chain_type}Chain缓存")
            else:
                logger.warning(f"未知的Chain类型: {chain_type}")


# 全局Chain管理器实例
_chain_manager: Optional[ChainManager] = None


def get_chain_manager() -> ChainManager:
    """
    获取全局Chain管理器实例
    
    Returns:
        ChainManager实例
    """
    global _chain_manager
    if _chain_manager is None:
        _chain_manager = ChainManager()
    return _chain_manager


# 便捷函数
def get_storage_chain() -> StorageChain:
    """获取StorageChain实例"""
    return get_chain_manager().storage


def get_subscribe_chain() -> SubscribeChain:
    """获取SubscribeChain实例"""
    return get_chain_manager().subscribe


def get_download_chain() -> DownloadChain:
    """获取DownloadChain实例"""
    return get_chain_manager().download


def get_search_chain() -> SearchChain:
    """获取SearchChain实例"""
    return get_chain_manager().search


def get_workflow_chain() -> WorkflowChain:
    """获取WorkflowChain实例"""
    return get_chain_manager().workflow


def get_site_chain() -> SiteChain:
    """获取SiteChain实例"""
    return get_chain_manager().site


def get_music_chain() -> MusicChain:
    """获取MusicChain实例"""
    return get_chain_manager().music


def get_dashboard_chain() -> DashboardChain:
    """获取DashboardChain实例"""
    return get_chain_manager().dashboard

