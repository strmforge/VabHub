"""
推荐算法实现
独立实现协同过滤、内容过滤、混合推荐等算法
"""

from typing import List, Dict, Optional, Any, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass
from loguru import logger
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.models.subscription import Subscription
from app.models.download import DownloadTask


@dataclass
class RecommendationResult:
    """推荐结果"""
    media_id: str
    score: float
    reason: str
    confidence: float
    recommendation_type: str
    media_type: Optional[str] = None
    title: Optional[str] = None


class CollaborativeFilteringRecommender:
    """协同过滤推荐算法"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_recommendations(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[RecommendationResult]:
        """
        基于协同过滤的推荐
        
        算法思路：
        1. 找到与当前用户有相似观看历史的用户
        2. 推荐这些相似用户喜欢但当前用户未观看的内容
        
        注意：当前系统为单用户系统，协同过滤效果有限
        建议使用内容推荐或混合推荐算法
        """
        try:
            # 获取用户订阅历史
            user_subscriptions = await self._get_user_subscriptions(user_id)
            
            if not user_subscriptions:
                # 如果没有历史数据，返回空列表
                return []
            
            # 获取所有用户的订阅数据
            all_subscriptions = await self._get_all_subscriptions()
            
            # 单用户系统：如果只有一个用户，协同过滤效果有限
            if len(all_subscriptions) <= 1:
                logger.warning("单用户系统，协同过滤效果有限，建议使用内容推荐或混合推荐")
                # 返回空列表，让调用者使用其他算法
                return []
            
            # 计算用户相似度
            similar_users = self._find_similar_users(user_subscriptions, all_subscriptions)
            
            if not similar_users:
                # 没有相似用户，返回空列表
                return []
            
            # 基于相似用户推荐
            recommendations = await self._recommend_from_similar_users(
                user_id,
                user_subscriptions,
                similar_users,
                limit
            )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"协同过滤推荐失败: {e}")
            return []
    
    async def _get_user_subscriptions(self, user_id: int) -> List[Dict]:
        """获取用户订阅历史（当前系统为单用户，返回所有订阅）"""
        try:
            # 当前系统为单用户系统，返回所有活跃订阅作为用户订阅历史
            result = await self.db.execute(
                select(Subscription).where(
                    Subscription.status.in_(["active", "completed"])
                )
            )
            subscriptions = result.scalars().all()
            
            return [
                {
                    "media_id": f"{sub.media_type}_{sub.tmdb_id}",
                    "media_type": sub.media_type,
                    "title": sub.title,
                    "rating": 5.0  # 默认评分，实际可以从用户评分数据获取
                }
                for sub in subscriptions
            ]
        except Exception as e:
            logger.error(f"获取用户订阅历史失败: {e}")
            return []
    
    async def _get_all_subscriptions(self) -> Dict[int, List[Dict]]:
        """获取所有用户的订阅数据"""
        try:
            result = await self.db.execute(
                select(Subscription).where(
                    Subscription.status.in_(["active", "completed"])
                )
            )
            subscriptions = result.scalars().all()
            
            # 当前系统为单用户系统，将所有订阅视为同一用户的订阅
            # 为了模拟多用户场景，我们按订阅时间分组（简化处理）
            # 或者将所有订阅视为一个用户（user_id=0）
            user_subscriptions = defaultdict(list)
            for sub in subscriptions:
                user_id = 0  # 单用户系统，所有订阅视为同一用户
                user_subscriptions[user_id].append({
                    "media_id": f"{sub.media_type}_{sub.tmdb_id}",
                    "media_type": sub.media_type,
                    "title": sub.title,
                    "rating": 5.0
                })
            
            return dict(user_subscriptions)
        except Exception as e:
            logger.error(f"获取所有用户订阅数据失败: {e}")
            return {}
    
    def _find_similar_users(
        self,
        user_subscriptions: List[Dict],
        all_subscriptions: Dict[int, List[Dict]]
    ) -> List[Tuple[int, float]]:
        """找到相似用户"""
        if not user_subscriptions:
            return []
        
        # 构建用户订阅向量
        user_media_ids = {sub["media_id"] for sub in user_subscriptions}
        
        similar_users = []
        for other_user_id, other_subscriptions in all_subscriptions.items():
            if other_user_id == 0:  # 跳过系统用户
                continue
            
            # 计算Jaccard相似度
            other_media_ids = {sub["media_id"] for sub in other_subscriptions}
            
            intersection = len(user_media_ids & other_media_ids)
            union = len(user_media_ids | other_media_ids)
            
            if union == 0:
                continue
            
            similarity = intersection / union
            if similarity > 0:  # 有相似度才添加
                similar_users.append((other_user_id, similarity))
        
        # 按相似度排序
        similar_users.sort(key=lambda x: x[1], reverse=True)
        
        return similar_users[:10]  # 返回前10个最相似的用户
    
    async def _recommend_from_similar_users(
        self,
        user_id: int,
        user_subscriptions: List[Dict],
        similar_users: List[Tuple[int, float]],
        limit: int
    ) -> List[RecommendationResult]:
        """基于相似用户推荐"""
        if not similar_users:
            return []
        
        user_media_ids = {sub["media_id"] for sub in user_subscriptions}
        
        # 收集推荐候选项
        candidate_scores = defaultdict(float)
        candidate_details = {}
        
        # 获取所有用户的订阅数据
        all_subscriptions = await self._get_all_subscriptions()
        
        for similar_user_id, similarity in similar_users:
            if similar_user_id not in all_subscriptions:
                continue
            
            for sub in all_subscriptions[similar_user_id]:
                media_id = sub["media_id"]
                
                # 跳过用户已订阅的内容
                if media_id in user_media_ids:
                    continue
                
                # 计算推荐分数（相似度 * 用户评分）
                score = similarity * sub.get("rating", 5.0)
                candidate_scores[media_id] += score
                
                # 保存详细信息
                if media_id not in candidate_details:
                    candidate_details[media_id] = {
                        "media_type": sub.get("media_type"),
                        "title": sub.get("title")
                    }
        
        # 转换为推荐结果
        recommendations = []
        for media_id, score in sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True):
            details = candidate_details.get(media_id, {})
            recommendations.append(RecommendationResult(
                media_id=media_id,
                score=score,
                reason=f"相似用户推荐（相似度: {max([s for u, s in similar_users if media_id in [sub['media_id'] for sub in all_subscriptions.get(u, [])]], default=0.0):.2f}）",
                confidence=min(score / 10.0, 1.0),  # 归一化到0-1
                recommendation_type="collaborative",
                media_type=details.get("media_type"),
                title=details.get("title")
            ))
        
        return recommendations[:limit]


class ContentBasedRecommender:
    """基于内容的推荐算法"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_recommendations(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[RecommendationResult]:
        """
        基于内容的推荐
        
        算法思路：
        1. 分析用户已订阅内容的特征（类型、年份、标签等）
        2. 推荐具有相似特征的内容
        """
        try:
            # 获取用户订阅历史
            user_subscriptions = await self._get_user_subscriptions(user_id)
            
            if not user_subscriptions:
                return []
            
            # 提取用户偏好特征
            user_preferences = self._extract_user_preferences(user_subscriptions)
            
            # 获取所有可推荐的内容
            all_subscriptions = await self._get_all_subscriptions_flat()
            
            # 计算内容相似度
            recommendations = []
            user_media_ids = {sub["media_id"] for sub in user_subscriptions}
            
            for candidate in all_subscriptions:
                media_id = candidate["media_id"]
                
                # 跳过用户已订阅的内容
                if media_id in user_media_ids:
                    continue
                
                # 计算内容相似度
                similarity = self._calculate_content_similarity(user_preferences, candidate)
                
                if similarity > 0:
                    recommendations.append(RecommendationResult(
                        media_id=media_id,
                        score=similarity,
                        reason=f"内容相似推荐（基于{user_preferences.get('preferred_types', [])}类型）",
                        confidence=similarity,
                        recommendation_type="content_based",
                        media_type=candidate.get("media_type"),
                        title=candidate.get("title")
                    ))
            
            # 按相似度排序
            recommendations.sort(key=lambda x: x.score, reverse=True)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"基于内容的推荐失败: {e}")
            return []
    
    async def _get_user_subscriptions(self, user_id: int) -> List[Dict]:
        """获取用户订阅历史（当前系统为单用户，返回所有订阅）"""
        try:
            # 当前系统为单用户系统，返回所有活跃订阅作为用户订阅历史
            result = await self.db.execute(
                select(Subscription).where(
                    Subscription.status.in_(["active", "completed"])
                )
            )
            subscriptions = result.scalars().all()
            
            return [
                {
                    "media_id": f"{sub.media_type}_{sub.tmdb_id}",
                    "media_type": sub.media_type,
                    "title": sub.title,
                    "year": sub.year
                }
                for sub in subscriptions
            ]
        except Exception as e:
            logger.error(f"获取用户订阅历史失败: {e}")
            return []
    
    async def _get_all_subscriptions_flat(self) -> List[Dict]:
        """获取所有订阅数据（扁平列表）"""
        try:
            result = await self.db.execute(
                select(Subscription).where(
                    Subscription.status.in_(["active", "completed"])
                )
            )
            subscriptions = result.scalars().all()
            
            return [
                {
                    "media_id": f"{sub.media_type}_{sub.tmdb_id}",
                    "media_type": sub.media_type,
                    "title": sub.title,
                    "year": sub.year
                }
                for sub in subscriptions
            ]
        except Exception as e:
            logger.error(f"获取所有订阅数据失败: {e}")
            return []
    
    def _extract_user_preferences(self, user_subscriptions: List[Dict]) -> Dict[str, Any]:
        """提取用户偏好特征"""
        preferences = {
            "preferred_types": [],
            "preferred_years": [],
            "media_count": len(user_subscriptions)
        }
        
        # 统计类型偏好
        type_counter = Counter([sub.get("media_type") for sub in user_subscriptions])
        preferences["preferred_types"] = [media_type for media_type, count in type_counter.most_common(3)]
        
        # 统计年份偏好
        years = [sub.get("year") for sub in user_subscriptions if sub.get("year")]
        if years:
            avg_year = sum(years) / len(years)
            preferences["preferred_years"] = [int(avg_year - 2), int(avg_year), int(avg_year + 2)]
        
        return preferences
    
    def _calculate_content_similarity(
        self,
        user_preferences: Dict[str, Any],
        candidate: Dict
    ) -> float:
        """计算内容相似度"""
        similarity = 0.0
        
        # 类型相似度（权重：0.5）
        candidate_type = candidate.get("media_type")
        if candidate_type in user_preferences.get("preferred_types", []):
            similarity += 0.5
        
        # 年份相似度（权重：0.3）
        candidate_year = candidate.get("year")
        if candidate_year:
            preferred_years = user_preferences.get("preferred_years", [])
            if preferred_years:
                year_diff = min([abs(candidate_year - year) for year in preferred_years])
                year_similarity = max(0, 1 - year_diff / 10)  # 年份差越小，相似度越高
                similarity += year_similarity * 0.3
        
        # 其他特征相似度（权重：0.2）
        # 这里可以添加更多特征，如标签、演员等
        similarity += 0.2
        
        return min(similarity, 1.0)


class PopularityBasedRecommender:
    """基于流行度的推荐算法"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_recommendations(
        self,
        limit: int = 20
    ) -> List[RecommendationResult]:
        """
        基于流行度的推荐
        
        算法思路：
        1. 统计订阅数量最多的内容
        2. 推荐热门内容
        """
        try:
            # 统计订阅数量
            result = await self.db.execute(
                select(
                    Subscription.tmdb_id,
                    Subscription.media_type,
                    Subscription.title,
                    func.count(Subscription.id).label('subscription_count')
                ).where(
                    Subscription.status.in_(["active", "completed"])
                ).group_by(
                    Subscription.tmdb_id,
                    Subscription.media_type,
                    Subscription.title
                ).order_by(
                    func.count(Subscription.id).desc()
                ).limit(limit)
            )
            
            subscriptions = result.all()
            
            recommendations = []
            max_count = 0
            for sub in subscriptions:
                count = sub.subscription_count
                if count > max_count:
                    max_count = count
                
                recommendations.append(RecommendationResult(
                    media_id=f"{sub.media_type}_{sub.tmdb_id}",
                    score=count,
                    reason=f"热门推荐（{count}人订阅）",
                    confidence=min(count / max(max_count, 1), 1.0),
                    recommendation_type="popularity",
                    media_type=sub.media_type,
                    title=sub.title
                ))
            
            # 归一化分数
            if max_count > 0:
                for rec in recommendations:
                    rec.score = rec.score / max_count
            
            return recommendations
            
        except Exception as e:
            logger.error(f"基于流行度的推荐失败: {e}")
            return []


class HybridRecommender:
    """混合推荐算法"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cf_recommender = CollaborativeFilteringRecommender(db)
        self.cb_recommender = ContentBasedRecommender(db)
        self.pop_recommender = PopularityBasedRecommender(db)
        
        # 深度学习推荐器（延迟初始化）
        self.dl_recommender = None
        self._dl_initialized = False
        
        # 算法权重（可配置）
        self.weights = {
            "collaborative": 0.3,
            "content_based": 0.3,
            "popularity": 0.2,
            "deep_learning": 0.2  # 添加深度学习权重
        }
    
    async def _init_dl_recommender(self):
        """初始化深度学习推荐器"""
        if self._dl_initialized:
            return
        
        try:
            from app.core.config import settings
            if settings.DEEP_LEARNING_ENABLED:
                from app.modules.recommendation.deep_learning_recommender import DeepLearningRecommender
                self.dl_recommender = DeepLearningRecommender(self.db)
                await self.dl_recommender._initialize()
            self._dl_initialized = True
        except Exception as e:
            logger.warning(f"Failed to initialize deep learning recommender: {e}")
            self._dl_initialized = True  # 标记为已初始化，避免重复尝试
    
    async def get_recommendations(
        self,
        user_id: int,
        limit: int = 20,
        algorithm: str = "hybrid",
        weights: Optional[Dict[str, float]] = None
    ) -> List[RecommendationResult]:
        """
        混合推荐
        
        算法思路：
        1. 使用多种推荐算法获取推荐结果
        2. 根据权重合并推荐结果
        3. 返回综合推荐列表
        """
        try:
            # 使用自定义权重（如果提供）
            if weights:
                self.weights.update(weights)
            
            # 根据算法类型选择推荐方式
            if algorithm == "collaborative":
                return await self.cf_recommender.get_recommendations(user_id, limit)
            elif algorithm == "content_based":
                return await self.cb_recommender.get_recommendations(user_id, limit)
            elif algorithm == "popularity":
                return await self.pop_recommender.get_recommendations(limit)
            else:  # hybrid
                # 混合推荐：合并多种算法的结果
                return await self._hybrid_recommend(user_id, limit)
                
        except Exception as e:
            logger.error(f"混合推荐失败: {e}")
            return []
    
    async def _hybrid_recommend(
        self,
        user_id: int,
        limit: int
    ) -> List[RecommendationResult]:
        """混合推荐核心逻辑"""
        # 初始化深度学习推荐器
        await self._init_dl_recommender()
        
        # 并发获取各种推荐结果
        import asyncio
        
        tasks = [
            self.cf_recommender.get_recommendations(user_id, limit * 2),
            self.cb_recommender.get_recommendations(user_id, limit * 2),
            self.pop_recommender.get_recommendations(limit * 2)
        ]
        
        # 添加深度学习推荐任务（如果启用）
        if self.dl_recommender is not None:
            tasks.append(self.dl_recommender.get_recommendations(user_id, limit * 2))
        else:
            # 如果没有深度学习推荐器，创建一个返回空列表的协程
            async def empty_dl_recommendations():
                return []
            tasks.append(empty_dl_recommendations())
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        cf_results = results[0] if not isinstance(results[0], Exception) else []
        cb_results = results[1] if not isinstance(results[1], Exception) else []
        pop_results = results[2] if not isinstance(results[2], Exception) else []
        dl_results = results[3] if len(results) > 3 and not isinstance(results[3], Exception) else []
        
        if isinstance(cf_results, Exception):
            logger.error(f"协同过滤推荐失败: {cf_results}")
            cf_results = []
        if isinstance(cb_results, Exception):
            logger.error(f"内容推荐失败: {cb_results}")
            cb_results = []
        if isinstance(pop_results, Exception):
            logger.error(f"流行度推荐失败: {pop_results}")
            pop_results = []
        if isinstance(dl_results, Exception):
            logger.error(f"深度学习推荐失败: {dl_results}")
            dl_results = []
        
        # 调整权重
        adjusted_weights = self.weights.copy()
        
        # 如果某个算法没有结果，将权重重新分配
        if not cf_results:
            # 将协同过滤权重分配给其他算法
            cf_weight = adjusted_weights.pop("collaborative", 0)
            if cb_results:
                adjusted_weights["content_based"] += cf_weight * 0.4
            if pop_results:
                adjusted_weights["popularity"] += cf_weight * 0.3
            if dl_results:
                adjusted_weights["deep_learning"] += cf_weight * 0.3
        
        if not dl_results:
            # 将深度学习权重分配给其他算法
            dl_weight = adjusted_weights.pop("deep_learning", 0)
            if cb_results:
                adjusted_weights["content_based"] += dl_weight * 0.5
            if pop_results:
                adjusted_weights["popularity"] += dl_weight * 0.5
        
        # 归一化权重
        total_weight = sum(adjusted_weights.values())
        if total_weight > 0:
            adjusted_weights = {k: v / total_weight for k, v in adjusted_weights.items()}
        else:
            # 如果所有权重都为0，使用默认权重
            adjusted_weights = {
                "content_based": 0.5,
                "popularity": 0.5
            }
        
        # 合并推荐结果
        merged_scores = defaultdict(float)
        merged_reasons = defaultdict(list)
        merged_details = {}
        
        # 协同过滤结果（如果存在）
        if cf_results and "collaborative" in adjusted_weights:
            for rec in cf_results:
                merged_scores[rec.media_id] += rec.score * adjusted_weights["collaborative"]
                merged_reasons[rec.media_id].append("协同过滤")
                if rec.media_id not in merged_details:
                    merged_details[rec.media_id] = {
                        "media_type": rec.media_type,
                        "title": rec.title
                    }
        
        # 内容推荐结果
        if cb_results and "content_based" in adjusted_weights:
            for rec in cb_results:
                merged_scores[rec.media_id] += rec.score * adjusted_weights["content_based"]
                merged_reasons[rec.media_id].append("内容相似")
                if rec.media_id not in merged_details:
                    merged_details[rec.media_id] = {
                        "media_type": rec.media_type,
                        "title": rec.title
                    }
        
        # 流行度推荐结果
        if pop_results and "popularity" in adjusted_weights:
            for rec in pop_results:
                merged_scores[rec.media_id] += rec.score * adjusted_weights["popularity"]
                merged_reasons[rec.media_id].append("热门推荐")
                if rec.media_id not in merged_details:
                    merged_details[rec.media_id] = {
                        "media_type": rec.media_type,
                        "title": rec.title
                    }
        
        # 深度学习推荐结果（如果存在）
        if dl_results and "deep_learning" in adjusted_weights:
            for rec in dl_results:
                merged_scores[rec.media_id] += rec.score * adjusted_weights["deep_learning"]
                merged_reasons[rec.media_id].append("深度学习")
                if rec.media_id not in merged_details:
                    merged_details[rec.media_id] = {
                        "media_type": rec.media_type,
                        "title": rec.title
                    }
        
        # 转换为推荐结果
        recommendations = []
        for media_id, score in sorted(merged_scores.items(), key=lambda x: x[1], reverse=True):
            details = merged_details.get(media_id, {})
            reasons = merged_reasons.get(media_id, [])
            
            recommendations.append(RecommendationResult(
                media_id=media_id,
                score=score,
                reason=f"混合推荐（{', '.join(set(reasons))}）",
                confidence=min(score, 1.0),
                recommendation_type="hybrid",
                media_type=details.get("media_type"),
                title=details.get("title")
            ))
        
        return recommendations[:limit]

