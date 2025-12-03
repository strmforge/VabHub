"""
仪表盘处理链
统一处理仪表盘相关操作
"""

from typing import Optional, Dict, Any
from app.chain.base import ChainBase
from app.core.database import AsyncSessionLocal
from loguru import logger


class DashboardChain(ChainBase):
    """仪表盘处理链"""
    
    def __init__(self):
        super().__init__()
    
    def _get_service(self, session):
        """
        获取仪表盘服务实例
        
        Args:
            session: 数据库会话
        
        Returns:
            DashboardService 实例
        """
        from app.modules.dashboard.service import DashboardService
        return DashboardService(session)
    
    # ========== 仪表盘数据 ==========
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """
        获取仪表盘数据
        
        Returns:
            仪表盘数据
        """
        # 检查缓存（DashboardService内部已有缓存，但Chain层也可以添加额外缓存）
        cache_key = self._get_cache_key("get_dashboard_data")
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug("从缓存获取仪表盘数据")
            return cached_result
        
        # 执行操作
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            data = await service.get_dashboard_data()
            
            # 缓存结果（30秒，仪表盘数据更新频繁）
            await self._set_to_cache(cache_key, data, ttl=30)
            
            return data
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """
        获取系统统计
        
        Returns:
            系统统计
        """
        # 检查缓存
        cache_key = self._get_cache_key("get_system_stats")
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug("从缓存获取系统统计")
            return cached_result
        
        # 执行操作
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            stats = await service.get_system_stats()
            
            # 缓存结果（10秒，系统统计更新频繁）
            await self._set_to_cache(cache_key, stats, ttl=10)
            
            return stats
    
    async def get_media_stats(self) -> Dict[str, Any]:
        """
        获取媒体统计
        
        Returns:
            媒体统计
        """
        # 检查缓存
        cache_key = self._get_cache_key("get_media_stats")
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug("从缓存获取媒体统计")
            return cached_result
        
        # 执行操作
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            stats = await service.get_media_stats()
            
            # 缓存结果（1分钟）
            await self._set_to_cache(cache_key, stats, ttl=60)
            
            return stats
    
    async def get_download_stats(self) -> Dict[str, Any]:
        """
        获取下载统计
        
        Returns:
            下载统计
        """
        # 检查缓存
        cache_key = self._get_cache_key("get_download_stats")
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug("从缓存获取下载统计")
            return cached_result
        
        # 执行操作
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            stats = await service.get_download_stats()
            
            # 缓存结果（30秒，下载状态更新频繁）
            await self._set_to_cache(cache_key, stats, ttl=30)
            
            return stats
    
    async def get_active_subscriptions_count(self) -> int:
        """
        获取活跃订阅数量
        
        Returns:
            活跃订阅数量
        """
        # 检查缓存
        cache_key = self._get_cache_key("get_active_subscriptions_count")
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug("从缓存获取活跃订阅数量")
            return cached_result
        
        # 执行操作
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            count = await service.get_active_subscriptions_count()
            
            # 缓存结果（1分钟）
            await self._set_to_cache(cache_key, count, ttl=60)
            
            return count

