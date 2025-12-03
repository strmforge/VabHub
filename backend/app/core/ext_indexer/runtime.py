"""
外部索引运行时实现

通过动态加载外部模块来调用外部索引引擎。
"""

import importlib
from typing import Optional, List, Dict, Any
from loguru import logger

from app.core.ext_indexer.interfaces import ExternalIndexerRuntime


class DynamicModuleRuntime:
    """
    动态模块运行时
    
    通过模块路径动态加载外部索引引擎模块，并调用其约定的函数。
    """
    
    def __init__(self, module_path: str):
        """
        初始化动态模块运行时
        
        Args:
            module_path: 外部模块路径（如 "external_indexer_engine.core"）
        """
        self.module_path = module_path
        self._module = None
        self._loaded = False
        
        try:
            self._module = importlib.import_module(module_path)
            self._loaded = True
            logger.info(f"外部索引模块已加载: {module_path}")
        except ImportError as e:
            logger.warning(f"无法加载外部索引模块 {module_path}: {e}")
            logger.warning("外部索引功能将被禁用")
        except Exception as e:
            logger.error(f"加载外部索引模块时发生错误: {e}")
            logger.warning("外部索引功能将被禁用")
    
    @property
    def is_loaded(self) -> bool:
        """检查模块是否已成功加载"""
        return self._loaded and self._module is not None
    
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
        if not self.is_loaded:
            logger.debug("外部索引模块未加载，返回空结果")
            return []
        
        try:
            # 调用外部模块的 search_torrents 函数
            if hasattr(self._module, "search_torrents"):
                result = await self._module.search_torrents(
                    site_id=site_id,
                    keyword=keyword,
                    media_type=media_type,
                    categories=categories,
                    page=page,
                )
                return result if isinstance(result, list) else []
            else:
                logger.warning(f"外部模块 {self.module_path} 未实现 search_torrents 函数")
                return []
        except Exception as e:
            logger.warning(f"调用外部索引搜索失败: {e}")
            return []
    
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
        if not self.is_loaded:
            logger.debug("外部索引模块未加载，返回空结果")
            return []
        
        try:
            # 调用外部模块的 fetch_rss 函数
            if hasattr(self._module, "fetch_rss"):
                result = await self._module.fetch_rss(
                    site_id=site_id,
                    limit=limit,
                )
                return result if isinstance(result, list) else []
            else:
                logger.warning(f"外部模块 {self.module_path} 未实现 fetch_rss 函数")
                return []
        except Exception as e:
            logger.warning(f"调用外部索引 RSS 失败: {e}")
            return []
    
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
        if not self.is_loaded:
            logger.debug("外部索引模块未加载，返回 None")
            return None
        
        try:
            # 调用外部模块的 get_detail 函数
            if hasattr(self._module, "get_detail"):
                result = await self._module.get_detail(
                    site_id=site_id,
                    torrent_id=torrent_id,
                )
                return result if isinstance(result, dict) else None
            else:
                logger.warning(f"外部模块 {self.module_path} 未实现 get_detail 函数")
                return None
        except Exception as e:
            logger.warning(f"调用外部索引详情失败: {e}")
            return None
    
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
        if not self.is_loaded:
            logger.debug("外部索引模块未加载，返回 None")
            return None
        
        try:
            # 调用外部模块的 get_download_link 函数
            if self._module and hasattr(self._module, "get_download_link"):
                result = await self._module.get_download_link(
                    site_id=site_id,
                    torrent_id=torrent_id,
                )
                return result if isinstance(result, str) else None
            else:
                logger.warning(f"外部模块 {self.module_path} 未实现 get_download_link 函数")
                return None
        except Exception as e:
            logger.warning(f"调用外部索引下载链接失败: {e}")
            return None

