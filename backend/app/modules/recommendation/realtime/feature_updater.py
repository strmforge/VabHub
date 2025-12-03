"""
实时特征更新器
根据用户交互实时更新用户画像和物品特征
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
from loguru import logger

from app.modules.recommendation.realtime.stream_processor import (
    RealTimeInteraction,
    InteractionType
)
from app.core.cache import get_cache


class FeatureUpdater:
    """实时特征更新器"""
    
    def __init__(
        self,
        update_interval_minutes: int = 5,
        batch_size: int = 100,
        cache_ttl: int = 3600
    ):
        """
        初始化特征更新器
        
        Args:
            update_interval_minutes: 更新间隔（分钟）
            batch_size: 批量更新大小
            cache_ttl: 缓存TTL（秒）
        """
        self.update_interval = update_interval_minutes
        self.batch_size = batch_size
        self.cache = get_cache()
        self.cache_ttl = cache_ttl
        
        # 用户特征缓存
        self.user_features_cache: Dict[str, Dict[str, Any]] = {}
        
        # 物品特征缓存
        self.item_features_cache: Dict[str, Dict[str, Any]] = {}
        
        self.running = True
    
    async def update_user_features(
        self,
        user_id: str,
        interactions: List[RealTimeInteraction]
    ) -> Dict[str, Any]:
        """
        更新用户特征
        
        Args:
            user_id: 用户ID
            interactions: 用户交互列表
        
        Returns:
            更新后的用户特征
        """
        try:
            # 获取现有特征
            current_features = await self.get_user_features(user_id)
            
            # 计算特征更新
            feature_updates = await self._calculate_feature_updates(
                interactions,
                current_features
            )
            
            # 合并特征
            updated_features = {
                **current_features,
                **feature_updates,
                "last_updated": datetime.now().isoformat()
            }
            
            # 更新缓存
            await self._update_user_features_cache(user_id, updated_features)
            
            logger.debug(f"Updated features for user {user_id}")
            
            return updated_features
            
        except Exception as e:
            logger.error(f"Failed to update user features: {e}")
            return {}
    
    async def _calculate_feature_updates(
        self,
        interactions: List[RealTimeInteraction],
        current_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算特征更新"""
        try:
            updates = defaultdict(float)
            
            # 交互类型统计
            interaction_counts = defaultdict(int)
            for interaction in interactions:
                interaction_counts[interaction.interaction_type.value] += 1
            
            # 更新交互频率
            total_interactions = len(interactions)
            if total_interactions > 0:
                updates["interaction_frequency"] = total_interactions
                updates["recent_interaction_count"] = total_interactions
            
            # 更新类别偏好
            category_preferences = defaultdict(float)
            for interaction in interactions:
                if interaction.context:
                    weight = self._get_interaction_weight(interaction.interaction_type)
                    for key, value in interaction.context.items():
                        if key.startswith('category_') or key.startswith('genre_'):
                            category_preferences[value] += weight
            
            if category_preferences:
                # 归一化类别偏好
                total_pref = sum(category_preferences.values())
                if total_pref > 0:
                    updates["category_preferences"] = {
                        cat: pref / total_pref 
                        for cat, pref in category_preferences.items()
                    }
            
            # 更新活跃度
            if "activity_level" in current_features:
                # 平滑更新
                old_activity = current_features["activity_level"]
                new_activity = min(total_interactions / 10.0, 1.0)  # 归一化
                updates["activity_level"] = 0.7 * old_activity + 0.3 * new_activity
            else:
                updates["activity_level"] = min(total_interactions / 10.0, 1.0)
            
            # 更新偏好强度
            positive_interactions = sum(
                1 for interaction in interactions
                if interaction.interaction_type in [
                    InteractionType.LIKE,
                    InteractionType.SHARE,
                    InteractionType.BOOKMARK,
                    InteractionType.PURCHASE,
                    InteractionType.SUBSCRIBE
                ]
            )
            if total_interactions > 0:
                updates["preference_strength"] = positive_interactions / total_interactions
            
            return dict(updates)
            
        except Exception as e:
            logger.error(f"Failed to calculate feature updates: {e}")
            return {}
    
    def _get_interaction_weight(self, interaction_type: InteractionType) -> float:
        """获取交互权重"""
        weights = {
            InteractionType.VIEW: 0.1,
            InteractionType.CLICK: 0.3,
            InteractionType.LIKE: 0.8,
            InteractionType.DISLIKE: -0.5,
            InteractionType.SHARE: 1.0,
            InteractionType.BOOKMARK: 0.9,
            InteractionType.PURCHASE: 1.5,
            InteractionType.RATING: 1.0,
            InteractionType.SKIP: -0.2,
            InteractionType.SUBSCRIBE: 1.2
        }
        return weights.get(interaction_type, 0.1)
    
    async def get_user_features(self, user_id: str) -> Dict[str, Any]:
        """获取用户特征"""
        try:
            # 先检查内存缓存
            if user_id in self.user_features_cache:
                return self.user_features_cache[user_id]
            
            # 检查Redis缓存
            cache_key = f"user_features:{user_id}"
            cached_features = await self.cache.get(cache_key)
            
            if cached_features:
                self.user_features_cache[user_id] = cached_features
                return cached_features
            
            # 返回默认特征
            default_features = {
                "interaction_frequency": 0,
                "activity_level": 0.0,
                "preference_strength": 0.0,
                "category_preferences": {},
                "last_updated": None
            }
            
            return default_features
            
        except Exception as e:
            logger.error(f"Failed to get user features: {e}")
            return {}
    
    async def _update_user_features_cache(
        self,
        user_id: str,
        features: Dict[str, Any]
    ):
        """更新用户特征缓存"""
        try:
            # 更新内存缓存
            self.user_features_cache[user_id] = features
            
            # 更新Redis缓存
            cache_key = f"user_features:{user_id}"
            await self.cache.set(cache_key, features, ttl=self.cache_ttl)
            
        except Exception as e:
            logger.error(f"Failed to update user features cache: {e}")
    
    async def update_item_features(
        self,
        item_id: str,
        interactions: List[RealTimeInteraction]
    ) -> Dict[str, Any]:
        """
        更新物品特征
        
        Args:
            item_id: 物品ID
            interactions: 物品相关的交互列表
        
        Returns:
            更新后的物品特征
        """
        try:
            # 获取现有特征
            current_features = await self.get_item_features(item_id)
            
            # 计算特征更新
            feature_updates = await self._calculate_item_feature_updates(
                interactions,
                current_features
            )
            
            # 合并特征
            updated_features = {
                **current_features,
                **feature_updates,
                "last_updated": datetime.now().isoformat()
            }
            
            # 更新缓存
            await self._update_item_features_cache(item_id, updated_features)
            
            logger.debug(f"Updated features for item {item_id}")
            
            return updated_features
            
        except Exception as e:
            logger.error(f"Failed to update item features: {e}")
            return {}
    
    async def _calculate_item_feature_updates(
        self,
        interactions: List[RealTimeInteraction],
        current_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算物品特征更新"""
        try:
            updates = defaultdict(float)
            
            # 交互统计
            interaction_counts = defaultdict(int)
            for interaction in interactions:
                interaction_counts[interaction.interaction_type.value] += 1
            
            total_interactions = len(interactions)
            
            # 更新流行度
            if "popularity" in current_features:
                old_popularity = current_features["popularity"]
                new_popularity = min(total_interactions / 100.0, 1.0)
                updates["popularity"] = 0.8 * old_popularity + 0.2 * new_popularity
            else:
                updates["popularity"] = min(total_interactions / 100.0, 1.0)
            
            # 更新评分
            ratings = [
                interaction.value 
                for interaction in interactions 
                if interaction.interaction_type == InteractionType.RATING 
                and interaction.value is not None
            ]
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                if "average_rating" in current_features:
                    old_rating = current_features["average_rating"]
                    rating_count = current_features.get("rating_count", 0)
                    new_count = rating_count + len(ratings)
                    updates["average_rating"] = (
                        (old_rating * rating_count + avg_rating * len(ratings)) / new_count
                    )
                    updates["rating_count"] = new_count
                else:
                    updates["average_rating"] = avg_rating
                    updates["rating_count"] = len(ratings)
            
            # 更新参与度
            positive_count = sum(
                1 for interaction in interactions
                if interaction.interaction_type in [
                    InteractionType.LIKE,
                    InteractionType.SHARE,
                    InteractionType.BOOKMARK,
                    InteractionType.PURCHASE,
                    InteractionType.SUBSCRIBE
                ]
            )
            if total_interactions > 0:
                updates["engagement_rate"] = positive_count / total_interactions
            
            return dict(updates)
            
        except Exception as e:
            logger.error(f"Failed to calculate item feature updates: {e}")
            return {}
    
    async def get_item_features(self, item_id: str) -> Dict[str, Any]:
        """获取物品特征"""
        try:
            # 先检查内存缓存
            if item_id in self.item_features_cache:
                return self.item_features_cache[item_id]
            
            # 检查Redis缓存
            cache_key = f"item_features:{item_id}"
            cached_features = await self.cache.get(cache_key)
            
            if cached_features:
                self.item_features_cache[item_id] = cached_features
                return cached_features
            
            # 返回默认特征
            default_features = {
                "popularity": 0.0,
                "average_rating": 0.0,
                "rating_count": 0,
                "engagement_rate": 0.0,
                "last_updated": None
            }
            
            return default_features
            
        except Exception as e:
            logger.error(f"Failed to get item features: {e}")
            return {}
    
    async def _update_item_features_cache(
        self,
        item_id: str,
        features: Dict[str, Any]
    ):
        """更新物品特征缓存"""
        try:
            # 更新内存缓存
            self.item_features_cache[item_id] = features
            
            # 更新Redis缓存
            cache_key = f"item_features:{item_id}"
            await self.cache.set(cache_key, features, ttl=self.cache_ttl)
            
        except Exception as e:
            logger.error(f"Failed to update item features cache: {e}")
    
    async def batch_update_features(
        self,
        user_interactions: Dict[str, List[RealTimeInteraction]],
        item_interactions: Dict[str, List[RealTimeInteraction]]
    ):
        """批量更新特征"""
        try:
            # 批量更新用户特征
            user_tasks = [
                self.update_user_features(user_id, interactions)
                for user_id, interactions in user_interactions.items()
            ]
            
            # 批量更新物品特征
            item_tasks = [
                self.update_item_features(item_id, interactions)
                for item_id, interactions in item_interactions.items()
            ]
            
            # 并发执行
            await asyncio.gather(*user_tasks, *item_tasks, return_exceptions=True)
            
            logger.info(
                f"Batch update completed: {len(user_interactions)} users, "
                f"{len(item_interactions)} items"
            )
            
        except Exception as e:
            logger.error(f"Batch update failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取更新器状态"""
        return {
            'update_interval_minutes': self.update_interval,
            'batch_size': self.batch_size,
            'cached_users': len(self.user_features_cache),
            'cached_items': len(self.item_features_cache),
            'cache_ttl': self.cache_ttl
        }

