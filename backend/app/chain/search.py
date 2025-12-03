"""
搜索处理链
统一处理搜索相关操作
"""

from typing import List, Optional, Dict, Any
from app.chain.base import ChainBase
from app.core.database import AsyncSessionLocal
from loguru import logger


class SearchChain(ChainBase):
    """搜索处理链"""
    
    def __init__(self):
        super().__init__()
    
    def _get_service(self, session):
        """
        获取搜索服务实例
        
        Args:
            session: 数据库会话
        
        Returns:
            SearchService 实例
        """
        from app.modules.search.service import SearchService
        return SearchService(session)
    
    # ========== 搜索操作 ==========
    
    async def search(
        self,
        query: str,
        media_type: Optional[str] = None,
        year: Optional[int] = None,
        quality: Optional[str] = None,
        resolution: Optional[str] = None,
        min_size: Optional[float] = None,
        max_size: Optional[float] = None,
        min_seeders: Optional[int] = None,
        max_seeders: Optional[int] = None,
        include: Optional[str] = None,
        exclude: Optional[str] = None,
        sites: Optional[List[str]] = None,
        sort_by: str = "seeders",
        sort_order: str = "desc",
        save_history: bool = True,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        执行搜索
        
        Args:
            query: 搜索关键词
            media_type: 媒体类型
            year: 年份
            quality: 质量
            resolution: 分辨率
            min_size: 最小大小（GB）
            max_size: 最大大小（GB）
            min_seeders: 最小做种数
            max_seeders: 最大做种数
            include: 包含关键词
            exclude: 排除关键词
            sites: 站点列表
            sort_by: 排序字段
            sort_order: 排序顺序
            save_history: 是否保存搜索历史
            user_id: 用户ID
        
        Returns:
            搜索结果列表
        """
        # 检查缓存
        cache_key = self._get_cache_key(
            "search",
            query, media_type, year, quality, resolution,
            min_size, max_size, min_seeders, max_seeders,
            include, exclude, sites, sort_by, sort_order
        )
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"从缓存获取搜索结果: query={query}")
            return cached_result
        
        # 执行搜索
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            results = await service.search(
                query=query,
                media_type=media_type,
                year=year,
                quality=quality,
                resolution=resolution,
                min_size=min_size,
                max_size=max_size,
                min_seeders=min_seeders,
                max_seeders=max_seeders,
                include=include,
                exclude=exclude,
                sites=sites,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            # 保存搜索历史
            if save_history:
                try:
                    await service.save_search_history(
                        query=query,
                        result_count=len(results),
                        media_type=media_type,
                        filters={
                            "year": year,
                            "quality": quality,
                            "resolution": resolution,
                            "min_size": min_size,
                            "max_size": max_size,
                            "min_seeders": min_seeders,
                            "max_seeders": max_seeders,
                            "include": include,
                            "exclude": exclude,
                            "sites": sites
                        },
                        user_id=user_id
                    )
                except Exception as e:
                    logger.warning(f"保存搜索历史失败: {e}")
            
            # 缓存结果（5分钟）
            await self._set_to_cache(cache_key, results, ttl=300)
            
            return results
    
    async def get_search_history(
        self,
        user_id: Optional[int] = None,
        limit: int = 20,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取搜索历史
        
        Args:
            user_id: 用户ID
            limit: 返回数量限制
            query: 搜索关键词（可选）
        
        Returns:
            搜索历史列表
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            # SearchService的get_search_history返回的是字典列表
            history = await service.get_search_history(limit=limit, user_id=user_id, query=query)
            
            # 服务已经返回字典列表，直接返回
            return history
    
    async def get_suggestions(
        self,
        query: str,
        limit: int = 10
    ) -> List[str]:
        """
        获取搜索建议
        
        Args:
            query: 搜索关键词
            limit: 返回数量限制
        
        Returns:
            搜索建议列表
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            suggestions = await service.get_suggestions(query, limit)
            return suggestions
    
    async def delete_search_history(self, history_id: int) -> bool:
        """
        删除搜索历史
        
        Args:
            history_id: 搜索历史ID
        
        Returns:
            是否成功
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            return await service.delete_search_history(history_id)
    
    async def clear_search_history(self, user_id: Optional[int] = None) -> int:
        """
        清除搜索历史
        
        Args:
            user_id: 用户ID（如果为None，清除所有）
        
        Returns:
            清除的记录数
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            # SearchService的clear_search_history返回清除的记录数
            return await service.clear_search_history(user_id)
    
    # ========== 辅助方法 ==========
    
    async def clear_search_cache(self, query: Optional[str] = None):
        """
        清除搜索缓存
        
        Args:
            query: 搜索关键词（如果指定，只清除该查询的缓存；否则清除所有缓存）
        """
        if query:
            # 清除特定查询的缓存
            keys_to_remove = [
                key for key in self._cache.keys()
                if key.startswith(self._get_cache_key("search", query, "").split("_")[0])
            ]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            # 清除所有搜索缓存
            keys_to_remove = [
                key for key in self._cache.keys()
                if "search" in key
            ]
            for key in keys_to_remove:
                del self._cache[key]
        
        logger.debug(f"已清除搜索缓存: query={query}")

