"""
音乐处理链
统一处理音乐相关操作（VabHub特色功能）
"""

from typing import List, Optional, Dict, Any
from app.chain.base import ChainBase
from app.core.database import AsyncSessionLocal
from loguru import logger


class MusicChain(ChainBase):
    """音乐处理链（VabHub特色功能）"""
    
    def __init__(self):
        super().__init__()
    
    def _get_service(self, session):
        """
        获取音乐服务实例
        
        Args:
            session: 数据库会话
        
        Returns:
            MusicService 实例
        """
        from app.modules.music.service import MusicService
        return MusicService(session)
    
    # ========== 音乐搜索 ==========
    
    async def search_music(
        self,
        query: str,
        search_type: str = "all",
        platform: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        搜索音乐
        
        Args:
            query: 搜索关键词
            search_type: 搜索类型（all, track, album, artist, playlist）
            platform: 平台（spotify, qq_music, netease）
            limit: 返回数量限制
        
        Returns:
            搜索结果列表
        """
        # 检查缓存（MusicService已有缓存，但Chain层也可以添加额外缓存）
        cache_key = self._get_cache_key("search_music", query, search_type, platform, limit)
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"从缓存获取音乐搜索结果: query={query}")
            return cached_result
        
        # 执行搜索
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            results = await service.search_music(query, search_type, platform, limit)
            
            # 缓存结果（30分钟，MusicService内部已有缓存）
            await self._set_to_cache(cache_key, results, ttl=1800)
            
            return results
    
    async def get_charts(
        self,
        platform: str,
        chart_type: str = "hot",
        region: str = "CN",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取音乐榜单
        
        Args:
            platform: 平台（spotify, qq_music, netease, tme_youni, billboard_china）
            chart_type: 榜单类型（hot, new, trending等）
            region: 地区（CN, US等）
            limit: 返回数量限制
        
        Returns:
            榜单列表
        """
        # 检查缓存
        cache_key = self._get_cache_key("get_charts", platform, chart_type, region, limit)
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"从缓存获取音乐榜单: platform={platform}, chart_type={chart_type}")
            return cached_result
        
        # 执行操作
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            charts = await service.get_charts(platform, chart_type, region, limit)
            
            # 缓存结果（1小时，榜单更新不频繁）
            await self._set_to_cache(cache_key, charts, ttl=3600)
            
            return charts
    
    # ========== 音乐订阅管理 ==========
    
    async def list_music_subscriptions(
        self,
        platform: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        列出音乐订阅
        
        Args:
            platform: 平台（可选）
        
        Returns:
            音乐订阅列表
        """
        # 检查缓存
        cache_key = self._get_cache_key("list_music_subscriptions", platform)
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"从缓存获取音乐订阅列表: platform={platform}")
            return cached_result
        
        # 执行操作
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            subscriptions = await service.list_subscriptions(platform=platform)
            
            # 转换为字典
            result = [self._subscription_to_dict(sub) for sub in subscriptions]
            
            # 缓存结果（1分钟）
            await self._set_to_cache(cache_key, result, ttl=60)
            
            return result
    
    async def get_music_subscription(self, subscription_id: int) -> Optional[Dict[str, Any]]:
        """
        获取音乐订阅详情
        
        Args:
            subscription_id: 订阅ID
        
        Returns:
            音乐订阅详情
        """
        # 检查缓存
        cache_key = self._get_cache_key("get_music_subscription", subscription_id)
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"从缓存获取音乐订阅详情: subscription_id={subscription_id}")
            return cached_result
        
        # 执行操作
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            subscription = await service.get_subscription(subscription_id)
            
            if subscription:
                result = self._subscription_to_dict(subscription)
                # 缓存结果（1分钟）
                await self._set_to_cache(cache_key, result, ttl=60)
                return result
            
            return None
    
    async def create_music_subscription(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建音乐订阅
        
        Args:
            subscription_data: 订阅数据
        
        Returns:
            创建的订阅
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            subscription = await service.create_subscription(subscription_data)
            
            # 清除订阅列表缓存
            await self._clear_music_cache()
            
            return self._subscription_to_dict(subscription)
    
    async def update_music_subscription(
        self,
        subscription_id: int,
        subscription_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        更新音乐订阅
        
        Args:
            subscription_id: 订阅ID
            subscription_data: 订阅数据
        
        Returns:
            更新后的订阅
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            subscription = await service.update_subscription(subscription_id, subscription_data)
            
            if subscription:
                # 清除相关缓存
                await self._clear_music_cache(subscription_id)
                return self._subscription_to_dict(subscription)
            
            return None
    
    async def delete_music_subscription(self, subscription_id: int) -> bool:
        """
        删除音乐订阅
        
        Args:
            subscription_id: 订阅ID
        
        Returns:
            是否成功
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            success = await service.delete_subscription(subscription_id)
            
            if success:
                # 清除相关缓存
                await self._clear_music_cache(subscription_id)
            
            return success
    
    # ========== 音乐库统计 ==========
    
    async def get_library_stats(self) -> Dict[str, Any]:
        """
        获取音乐库统计
        
        Returns:
            音乐库统计
        """
        # 检查缓存
        cache_key = self._get_cache_key("get_library_stats")
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug("从缓存获取音乐库统计")
            return cached_result
        
        # 执行操作
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            stats = await service.get_library_stats()
            
            # 缓存结果（5分钟）
            await self._set_to_cache(cache_key, stats, ttl=300)
            
            return stats
    
    # ========== 辅助方法 ==========
    
    def _subscription_to_dict(self, subscription) -> Dict[str, Any]:
        """将音乐订阅对象转换为字典"""
        import json
        return {
            "id": subscription.id,
            "name": subscription.name,
            "type": subscription.type,
            "platform": subscription.platform,
            "platform_id": subscription.platform_id,
            "artist": subscription.artist,
            "album": subscription.album,
            "genre": json.loads(subscription.genre) if subscription.genre else [],
            "is_active": subscription.is_active,
            "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
            "updated_at": subscription.updated_at.isoformat() if subscription.updated_at else None,
        }
    
    async def _clear_music_cache(self, subscription_id: Optional[int] = None):
        """
        清除音乐缓存
        
        Args:
            subscription_id: 订阅ID（如果指定，只清除该订阅的缓存；否则清除所有缓存）
        """
        if subscription_id:
            # 清除特定订阅的缓存
            cache_key = self._get_cache_key("get_music_subscription", subscription_id)
            if cache_key in self._cache:
                del self._cache[cache_key]
        else:
            # 清除所有音乐相关缓存
            keys_to_remove = [
                key for key in self._cache.keys()
                if "music" in key or "subscription" in key
            ]
            for key in keys_to_remove:
                del self._cache[key]
        
        logger.debug(f"已清除音乐缓存: subscription_id={subscription_id}")

