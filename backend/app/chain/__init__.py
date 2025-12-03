"""
Chain 模式模块
提供统一的处理链接口
"""

from app.chain.base import ChainBase

from typing import TYPE_CHECKING, Optional, Type, Callable

if TYPE_CHECKING:
    from app.chain.storage import StorageChain as StorageChainType
    from app.chain.subscribe import SubscribeChain as SubscribeChainType
    from app.chain.download import DownloadChain as DownloadChainType
    from app.chain.search import SearchChain as SearchChainType
    from app.chain.workflow import WorkflowChain as WorkflowChainType
    from app.chain.site import SiteChain as SiteChainType
    from app.chain.music import MusicChain as MusicChainType
    from app.chain.dashboard import DashboardChain as DashboardChainType
    from app.chain.manager import (
        ChainManager as ChainManagerType,
        get_chain_manager as GetChainManagerType,
        get_storage_chain as GetStorageChainType,
        get_subscribe_chain as GetSubscribeChainType,
        get_download_chain as GetDownloadChainType,
        get_search_chain as GetSearchChainType,
        get_workflow_chain as GetWorkflowChainType,
        get_site_chain as GetSiteChainType,
        get_music_chain as GetMusicChainType,
        get_dashboard_chain as GetDashboardChainType,
    )
else:
    # 运行时赋值为 None，避免循环依赖
    StorageChain: Optional[Type] = None
    SubscribeChain: Optional[Type] = None
    DownloadChain: Optional[Type] = None
    SearchChain: Optional[Type] = None
    WorkflowChain: Optional[Type] = None
    SiteChain: Optional[Type] = None
    MusicChain: Optional[Type] = None
    DashboardChain: Optional[Type] = None
    ChainManager: Optional[Type] = None
    get_chain_manager: Optional[Callable] = None
    get_storage_chain: Optional[Callable] = None
    get_subscribe_chain: Optional[Callable] = None
    get_download_chain: Optional[Callable] = None
    get_search_chain: Optional[Callable] = None
    get_workflow_chain: Optional[Callable] = None
    get_site_chain: Optional[Callable] = None
    get_music_chain: Optional[Callable] = None
    get_dashboard_chain: Optional[Callable] = None

# 注意：所有Chain类已实现，但在导入失败时会设置为None
# 这允许代码在部分Chain未实现时也能正常运行

__all__ = [
    "ChainBase",
    "StorageChain",
    "SubscribeChain",
    "DownloadChain",
    "SearchChain",
    "WorkflowChain",
    "SiteChain",
    "MusicChain",
    "DashboardChain",
    "ChainManager",
    "get_chain_manager",
    "get_storage_chain",
    "get_subscribe_chain",
    "get_download_chain",
    "get_search_chain",
    "get_workflow_chain",
    "get_site_chain",
    "get_music_chain",
    "get_dashboard_chain",
]

