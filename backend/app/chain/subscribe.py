"""
订阅处理链
统一处理订阅相关操作
"""

from typing import List, Optional, Dict, Any
from app.chain.base import ChainBase
from app.core.database import AsyncSessionLocal
from loguru import logger


class SubscribeChain(ChainBase):
    """订阅处理链"""
    
    def __init__(self):
        super().__init__()
    
    def _get_service(self, session):
        """
        获取订阅服务实例
        
        Args:
            session: 数据库会话
        
        Returns:
            SubscriptionService 实例
        """
        from app.modules.subscription.service import SubscriptionService
        return SubscriptionService(session)
    
    # ========== 订阅配置管理 ==========
    
    async def list_subscriptions(
        self,
        media_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        列出订阅
        
        Args:
            media_type: 媒体类型（movie, tv）
            status: 状态（active, paused, completed）
        
        Returns:
            订阅列表
        """
        # 检查缓存
        cache_key = self._get_cache_key("list_subscriptions", media_type, status)
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"从缓存获取订阅列表: media_type={media_type}, status={status}")
            return cached_result
        
        # 执行操作
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            subscriptions = await service.list_subscriptions(media_type, status)
            
            # 转换为字典
            result = [self._subscription_to_dict(sub) for sub in subscriptions]
            
            # 缓存结果（1分钟）
            await self._set_to_cache(cache_key, result, ttl=60)
            
            return result
    
    async def get_subscription(self, subscription_id: int) -> Optional[Dict[str, Any]]:
        """
        获取订阅详情
        
        Args:
            subscription_id: 订阅ID
        
        Returns:
            订阅详情
        """
        # 检查缓存
        cache_key = self._get_cache_key("get_subscription", subscription_id)
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"从缓存获取订阅详情: subscription_id={subscription_id}")
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
    
    async def create_subscription(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建订阅
        
        Args:
            subscription_data: 订阅数据
        
        Returns:
            创建的订阅
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            subscription = await service.create_subscription(subscription_data)
            
            # 清除订阅列表缓存
            await self._clear_subscription_cache()
            
            return self._subscription_to_dict(subscription)
    
    async def update_subscription(
        self,
        subscription_id: int,
        subscription_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        更新订阅
        
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
                await self._clear_subscription_cache(subscription_id)
                return self._subscription_to_dict(subscription)
            
            return None
    
    async def delete_subscription(self, subscription_id: int) -> bool:
        """
        删除订阅
        
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
                await self._clear_subscription_cache(subscription_id)
            
            return success
    
    async def enable_subscription(self, subscription_id: int) -> Optional[Dict[str, Any]]:
        """
        启用订阅
        
        Args:
            subscription_id: 订阅ID
        
        Returns:
            更新后的订阅
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            subscription = await service.enable_subscription(subscription_id)
            
            if subscription:
                # 清除相关缓存
                await self._clear_subscription_cache(subscription_id)
                return self._subscription_to_dict(subscription)
            
            return None
    
    async def disable_subscription(self, subscription_id: int) -> Optional[Dict[str, Any]]:
        """
        禁用订阅
        
        Args:
            subscription_id: 订阅ID
        
        Returns:
            更新后的订阅
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            subscription = await service.disable_subscription(subscription_id)
            
            if subscription:
                # 清除相关缓存
                await self._clear_subscription_cache(subscription_id)
                return self._subscription_to_dict(subscription)
            
            return None
    
    # ========== 订阅操作 ==========
    
    async def execute_search(self, subscription_id: int) -> Dict[str, Any]:
        """
        执行订阅搜索
        
        Args:
            subscription_id: 订阅ID
        
        Returns:
            搜索结果
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            result = await service.execute_search(subscription_id)
            
            # 清除订阅详情缓存（因为搜索后状态可能改变）
            await self._clear_subscription_cache(subscription_id)
            
            return result
    
    # ========== 辅助方法 ==========
    
    def _subscription_to_dict(self, subscription) -> Dict[str, Any]:
        """将订阅对象转换为字典"""
        return {
            "id": subscription.id,
            "title": subscription.title,
            "original_title": subscription.original_title,
            "year": subscription.year,
            "media_type": subscription.media_type,
            "tmdb_id": subscription.tmdb_id,
            "tvdb_id": subscription.tvdb_id,
            "imdb_id": subscription.imdb_id,
            "poster": subscription.poster,
            "backdrop": subscription.backdrop,
            "status": subscription.status,
            "season": subscription.season,
            "total_episode": subscription.total_episode,
            "start_episode": subscription.start_episode,
            "episode_group": subscription.episode_group,
            "quality": subscription.quality,
            "resolution": subscription.resolution,
            "effect": subscription.effect,
            "sites": subscription.sites,
            "downloader": subscription.downloader,
            "save_path": subscription.save_path,
            "min_seeders": subscription.min_seeders,
            "auto_download": subscription.auto_download,
            "best_version": subscription.best_version,
            "search_imdbid": subscription.search_imdbid,
            "include": subscription.include,
            "exclude": subscription.exclude,
            "filter_groups": subscription.filter_groups,
            "search_rules": subscription.search_rules,
            "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
            "updated_at": subscription.updated_at.isoformat() if subscription.updated_at else None,
            "last_search": subscription.last_search.isoformat() if subscription.last_search else None,
            "next_search": subscription.next_search.isoformat() if subscription.next_search else None,
        }
    
    async def _clear_subscription_cache(self, subscription_id: Optional[int] = None):
        """
        清除订阅缓存
        
        Args:
            subscription_id: 订阅ID（如果指定，只清除该订阅的缓存；否则清除所有缓存）
        """
        if subscription_id:
            # 清除特定订阅的缓存
            cache_key = self._get_cache_key("get_subscription", subscription_id)
            if cache_key in self._cache:
                del self._cache[cache_key]
        else:
            # 清除所有订阅相关缓存
            keys_to_remove = [
                key for key in self._cache.keys()
                if "list_subscriptions" in key or "get_subscription" in key
            ]
            for key in keys_to_remove:
                del self._cache[key]
        
        logger.debug(f"已清除订阅缓存: subscription_id={subscription_id}")
