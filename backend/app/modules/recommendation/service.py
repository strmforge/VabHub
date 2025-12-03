"""
推荐服务 - 独立实现的推荐引擎
支持协同过滤、内容过滤、混合推荐等算法
"""

from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.core.cache import get_cache

from app.modules.recommendation.algorithms import (
    HybridRecommender,
    CollaborativeFilteringRecommender,
    ContentBasedRecommender,
    PopularityBasedRecommender,
    RecommendationResult
)
from app.core.bangumi_client import BangumiClient


class RecommendationService:
    """推荐服务 - 独立实现的推荐引擎"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache = get_cache()
        self.hybrid_recommender = HybridRecommender(db)
        self.cf_recommender = CollaborativeFilteringRecommender(db)
        self.cb_recommender = ContentBasedRecommender(db)
        self.pop_recommender = PopularityBasedRecommender(db)
        self.bangumi_client = BangumiClient()
    
    def _get_recommender(self, algorithm: str = "hybrid") -> Any:
        """获取推荐引擎实例"""
        if algorithm == "collaborative":
            return self.cf_recommender
        elif algorithm == "content_based":
            return self.cb_recommender
        elif algorithm == "popularity":
            return self.pop_recommender
        elif algorithm == "deep_learning":
            # 深度学习推荐器需要特殊处理（延迟初始化）
            from app.modules.recommendation.deep_learning_recommender import DeepLearningRecommender
            return DeepLearningRecommender(self.db)
        else:
            return self.hybrid_recommender
    
    async def get_recommendations(
        self,
        user_id: int,
        limit: int = 20,
        algorithm: str = "hybrid",
        preferences: Optional[Dict[str, Any]] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """获取用户推荐（独立实现）"""
        try:
            # 生成缓存键
            cache_key = self.cache.generate_key(
                "recommendations",
                user_id=user_id,
                algorithm=algorithm,
                limit=limit
            )
            
            # 尝试从缓存获取
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"从缓存获取推荐结果: 用户 {user_id}")
                return cached_result
            
            # 获取推荐引擎
            recommender = self._get_recommender(algorithm)
            
            # 获取推荐结果
            if algorithm == "deep_learning":
                # 深度学习推荐器需要先初始化
                if hasattr(recommender, '_initialize'):
                    await recommender._initialize()
                recommendations = await recommender.get_recommendations(
                    user_id=user_id,
                    limit=limit * 2
                )
            else:
                recommendations = await recommender.get_recommendations(
                    user_id=user_id,
                    limit=limit * 2,  # 获取更多结果以便过滤
                    algorithm=algorithm,
                    weights=weights
                )
            
            # 格式化结果
            formatted_results = []
            for rec in recommendations:
                # 应用偏好过滤（如果提供）
                if preferences:
                    media_type = rec.media_type or ""
                    if not preferences.get("includeMovies", True) and media_type == "movie":
                        continue
                    if not preferences.get("includeTVShows", True) and media_type in ["tv", "tv_show"]:
                        continue
                    if not preferences.get("includeAnime", True) and media_type == "anime":
                        continue
                
                formatted_results.append({
                    "media_id": rec.media_id,
                    "score": rec.score,
                    "reason": rec.reason,
                    "confidence": rec.confidence,
                    "recommendation_type": rec.recommendation_type,
                    "media_type": rec.media_type,
                    "title": rec.title
                })
            
            final_results = formatted_results[:limit]
            
            # 缓存结果（1小时）
            await self.cache.set(cache_key, final_results, ttl=3600)
            
            return final_results
            
        except Exception as e:
            logger.error(f"获取推荐失败: {e}")
            return []
    
    async def get_similar_content(
        self,
        media_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取相似内容推荐（基于内容推荐算法）"""
        try:
            # 使用内容推荐算法获取相似内容
            # 从media_id解析类型和ID
            parts = media_id.split("_")
            if len(parts) >= 2:
                media_type = parts[0]
                tmdb_id = parts[1]
                
                # 获取当前媒体的信息
                from app.models.subscription import Subscription
                from sqlalchemy import select
                
                result = await self.db.execute(
                    select(Subscription).where(
                        Subscription.tmdb_id == int(tmdb_id),
                        Subscription.media_type == media_type
                    ).limit(1)
                )
                current_sub = result.scalar_one_or_none()
                
                if not current_sub:
                    return []
                
                # 获取同类型的其他订阅
                result = await self.db.execute(
                    select(Subscription).where(
                        Subscription.media_type == media_type,
                        Subscription.tmdb_id != int(tmdb_id),
                        Subscription.status.in_(["active", "completed"])
                    )
                )
                similar_subs = result.scalars().all()
                
                # 计算相似度（基于年份、类型等）
                recommendations = []
                for sub in similar_subs:
                    similarity = 0.0
                    
                    # 年份相似度
                    if current_sub.year and sub.year:
                        year_diff = abs(current_sub.year - sub.year)
                        year_similarity = max(0, 1 - year_diff / 10)
                        similarity += year_similarity * 0.5
                    
                    # 类型相似度（相同类型）
                    similarity += 0.5
                    
                    recommendations.append({
                        "media_id": f"{sub.media_type}_{sub.tmdb_id}",
                        "similarity": similarity,
                        "reason": f"内容相似（类型: {sub.media_type}）",
                        "media_type": sub.media_type,
                        "title": sub.title
                    })
                
                # 按相似度排序
                recommendations.sort(key=lambda x: x["similarity"], reverse=True)
                
                return recommendations[:limit]
            
            return []
        except Exception as e:
            logger.error(f"获取相似内容失败: {e}")
            return []
    
    async def get_popular_recommendations(
        self,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取热门推荐（独立实现）"""
        try:
            # 生成缓存键
            cache_key = self.cache.generate_key("popular_recommendations", limit=limit)
            
            # 尝试从缓存获取
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                logger.debug("从缓存获取热门推荐")
                return cached_result
            
            # 使用流行度推荐算法
            recommendations = await self.pop_recommender.get_recommendations(limit)
            
            # 格式化结果
            formatted_results = []
            for rec in recommendations:
                formatted_results.append({
                    "media_id": rec.media_id,
                    "score": rec.score,
                    "reason": rec.reason,
                    "confidence": rec.confidence,
                    "recommendation_type": rec.recommendation_type,
                    "media_type": rec.media_type,
                    "title": rec.title
                })
            
            # 缓存结果（2小时）
            await self.cache.set(cache_key, formatted_results, ttl=7200)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"获取热门推荐失败: {e}")
            return []
    
    async def get_bangumi_recommendations(
        self,
        limit: int = 20,
        source: str = "calendar"  # calendar, popular
    ) -> List[Dict[str, Any]]:
        """
        获取Bangumi动漫推荐
        
        Args:
            limit: 返回数量限制
            source: 推荐来源（calendar=每日放送, popular=热门动漫）
        
        Returns:
            Bangumi推荐列表
        """
        try:
            if source == "calendar":
                # 获取每日放送
                bangumi_items = await self.bangumi_client.get_calendar()
            else:
                # 获取热门动漫
                bangumi_items = await self.bangumi_client.get_popular_anime(limit=limit)
            
            # 转换为推荐格式
            recommendations = []
            for item in bangumi_items[:limit]:
                rating = item.get("rating", {})
                score = rating.get("score", 0) if rating else 0
                
                recommendations.append({
                    "media_id": f"bangumi_{item.get('id')}",
                    "score": score,
                    "reason": f"Bangumi推荐（{source}）",
                    "confidence": 0.8 if score > 7 else 0.6,
                    "recommendation_type": "bangumi",
                    "media_type": "anime",
                    "title": item.get("name_cn") or item.get("name"),
                    "original_title": item.get("name"),
                    "summary": item.get("summary", ""),
                    "images": item.get("images", {}),
                    "rating": rating,
                    "url": item.get("url")
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"获取Bangumi推荐失败: {e}")
            return []
    
    async def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户推荐偏好设置
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户偏好设置
        """
        try:
            from app.modules.settings.service import SettingsService
            
            settings_service = SettingsService(self.db)
            
            # 从设置服务获取用户偏好
            preferences = {
                "includeMovies": await settings_service.get_setting(
                    "recommendation_include_movies",
                    category="recommendation",
                    default=True
                ),
                "includeTVShows": await settings_service.get_setting(
                    "recommendation_include_tv_shows",
                    category="recommendation",
                    default=True
                ),
                "includeAnime": await settings_service.get_setting(
                    "recommendation_include_anime",
                    category="recommendation",
                    default=True
                ),
                "preferredGenres": await settings_service.get_setting(
                    "recommendation_preferred_genres",
                    category="recommendation",
                    default=[]
                ),
                "minRating": await settings_service.get_setting(
                    "recommendation_min_rating",
                    category="recommendation",
                    default=0.0
                ),
                "algorithm": await settings_service.get_setting(
                    "recommendation_algorithm",
                    category="recommendation",
                    default="hybrid"
                ),
                "weights": await settings_service.get_setting(
                    "recommendation_weights",
                    category="recommendation",
                    default={
                        "collaborative": 30,
                        "content": 30,
                        "popularity": 20,
                        "deep_learning": 20
                    }
                )
            }
            
            return preferences
            
        except Exception as e:
            logger.error(f"获取用户偏好设置失败: {e}")
            return {
                "includeMovies": True,
                "includeTVShows": True,
                "includeAnime": True,
                "preferredGenres": [],
                "minRating": 0.0,
                "algorithm": "hybrid",
                "weights": {
                    "collaborative": 30,
                    "content": 30,
                    "popularity": 20,
                    "deep_learning": 20
                }
            }
    
    async def update_user_preferences(
        self,
        user_id: int,
        preferences: Dict[str, Any]
    ) -> bool:
        """
        更新用户推荐偏好设置
        
        Args:
            user_id: 用户ID
            preferences: 偏好设置字典
        
        Returns:
            是否成功
        """
        try:
            from app.modules.settings.service import SettingsService
            
            settings_service = SettingsService(self.db)
            
            # 更新各项设置
            if "includeMovies" in preferences:
                await settings_service.set_setting(
                    "recommendation_include_movies",
                    preferences["includeMovies"],
                    category="recommendation"
                )
            
            if "includeTVShows" in preferences:
                await settings_service.set_setting(
                    "recommendation_include_tv_shows",
                    preferences["includeTVShows"],
                    category="recommendation"
                )
            
            if "includeAnime" in preferences:
                await settings_service.set_setting(
                    "recommendation_include_anime",
                    preferences["includeAnime"],
                    category="recommendation"
                )
            
            if "preferredGenres" in preferences:
                await settings_service.set_setting(
                    "recommendation_preferred_genres",
                    preferences["preferredGenres"],
                    category="recommendation"
                )
            
            if "minRating" in preferences:
                await settings_service.set_setting(
                    "recommendation_min_rating",
                    preferences["minRating"],
                    category="recommendation"
                )
            
            if "algorithm" in preferences:
                await settings_service.set_setting(
                    "recommendation_algorithm",
                    preferences["algorithm"],
                    category="recommendation"
                )
            
            if "weights" in preferences:
                await settings_service.set_setting(
                    "recommendation_weights",
                    preferences["weights"],
                    category="recommendation"
                )
            
            await self.db.commit()
            
            logger.info(f"用户 {user_id} 的推荐偏好设置已更新")
            return True
            
        except Exception as e:
            logger.error(f"更新用户偏好设置失败: {e}")
            await self.db.rollback()
            return False

