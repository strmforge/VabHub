"""
实时推荐服务
集成流式处理器、特征更新器和A/B测试框架
"""

from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.modules.recommendation.realtime.stream_processor import (
    StreamProcessor,
    RealTimeInteraction,
    InteractionType
)
from app.modules.recommendation.realtime.feature_updater import FeatureUpdater
from app.modules.recommendation.realtime.ab_testing import (
    ABTestingFramework,
    Experiment,
    ExperimentVariant,
    ExperimentStatus
)
from app.modules.recommendation.service import RecommendationService
from app.modules.recommendation.algorithms import RecommendationResult
from app.core.config import settings


class RealtimeRecommendationService:
    """实时推荐服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.base_service = RecommendationService(db)
        
        # 初始化实时组件
        self.stream_processor = None
        self.feature_updater = None
        self.ab_testing = None
        self._initialized = False
    
    async def _initialize(self):
        """初始化实时推荐组件"""
        if self._initialized:
            return
        
        try:
            if not settings.REALTIME_RECOMMENDATION_ENABLED:
                logger.info("Realtime recommendation is disabled by configuration")
                return
            
            # 初始化流式处理器
            self.stream_processor = StreamProcessor(
                buffer_size=settings.REALTIME_BUFFER_SIZE,
                session_timeout_minutes=settings.REALTIME_SESSION_TIMEOUT_MINUTES,
                time_decay_factor=settings.REALTIME_TIME_DECAY_FACTOR
            )
            
            # 初始化特征更新器
            self.feature_updater = FeatureUpdater(
                update_interval_minutes=settings.REALTIME_UPDATE_INTERVAL_MINUTES,
                batch_size=settings.REALTIME_BATCH_SIZE,
                cache_ttl=settings.REALTIME_FEATURE_CACHE_TTL
            )
            
            # 初始化A/B测试框架
            if settings.AB_TESTING_ENABLED:
                self.ab_testing = ABTestingFramework(
                    min_sample_size=settings.AB_TESTING_MIN_SAMPLE_SIZE,
                    significance_level=settings.AB_TESTING_SIGNIFICANCE_LEVEL,
                    evaluation_k=settings.AB_TESTING_EVALUATION_K
                )
            
            self._initialized = True
            logger.info("Realtime recommendation service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize realtime recommendation service: {e}")
    
    async def record_interaction(
        self,
        user_id: int,
        item_id: str,
        interaction_type: str,
        value: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        记录用户交互
        
        Args:
            user_id: 用户ID
            item_id: 物品ID（media_id格式）
            interaction_type: 交互类型
            value: 交互值（如评分）
            context: 上下文信息
        """
        await self._initialize()
        
        if self.stream_processor is None:
            return
        
        try:
            # 转换为InteractionType枚举
            try:
                interaction_enum = InteractionType(interaction_type.lower())
            except ValueError:
                logger.warning(f"Unknown interaction type: {interaction_type}")
                return
            
            # 创建交互对象
            interaction = RealTimeInteraction(
                user_id=str(user_id),
                item_id=item_id,
                interaction_type=interaction_enum,
                value=value,
                context=context
            )
            
            # 记录交互
            await self.stream_processor.record_interaction(interaction)
            
            # 更新特征
            if self.feature_updater:
                user_interactions = self.stream_processor.get_user_interactions(
                    str(user_id), 
                    minutes=60
                )
                await self.feature_updater.update_user_features(
                    str(user_id),
                    user_interactions
                )
            
            # 记录A/B测试交互
            if self.ab_testing:
                await self.ab_testing.record_interaction(
                    experiment_id="default",  # 默认实验，实际应从配置获取
                    user_id=str(user_id),
                    interaction_type=interaction_type,
                    item_id=item_id,
                    value=value
                )
            
        except Exception as e:
            logger.error(f"Failed to record interaction: {e}")
    
    async def get_realtime_recommendations(
        self,
        user_id: int,
        limit: int = 20,
        algorithm: str = "hybrid",
        experiment_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取实时推荐
        
        Args:
            user_id: 用户ID
            limit: 推荐数量
            algorithm: 推荐算法
            experiment_id: A/B测试实验ID（可选）
        
        Returns:
            推荐结果列表
        """
        await self._initialize()
        
        try:
            # 获取基础推荐
            base_recommendations = await self.base_service.get_recommendations(
                user_id=user_id,
                limit=limit * 2,
                algorithm=algorithm
            )
            
            # 转换为RecommendationResult对象
            recommendation_results = []
            for rec_dict in base_recommendations:
                recommendation_results.append(RecommendationResult(
                    media_id=rec_dict["media_id"],
                    score=rec_dict["score"],
                    reason=rec_dict["reason"],
                    confidence=rec_dict["confidence"],
                    recommendation_type=rec_dict["recommendation_type"],
                    media_type=rec_dict.get("media_type"),
                    title=rec_dict.get("title")
                ))
            
            # 应用实时调整
            if self.stream_processor:
                adjusted_recommendations = await self.stream_processor.apply_realtime_adjustments(
                    recommendation_results,
                    str(user_id),
                    minutes=30
                )
            else:
                adjusted_recommendations = recommendation_results
            
            # A/B测试分配
            variant_name = None
            if self.ab_testing and experiment_id:
                variant_name = await self.ab_testing.assign_user_to_variant(
                    experiment_id,
                    str(user_id)
                )
                
                # 如果分配到特定变体，可能需要使用不同的算法
                if variant_name:
                    experiment = self.ab_testing.get_experiment(experiment_id)
                    if experiment:
                        for variant in experiment.variants:
                            if variant.name == variant_name:
                                # 使用变体指定的算法
                                if variant.algorithm != algorithm:
                                    variant_recommendations = await self.base_service.get_recommendations(
                                        user_id=user_id,
                                        limit=limit * 2,
                                        algorithm=variant.algorithm
                                    )
                                    adjusted_recommendations = [
                                        RecommendationResult(
                                            media_id=r["media_id"],
                                            score=r["score"],
                                            reason=r["reason"],
                                            confidence=r["confidence"],
                                            recommendation_type=r["recommendation_type"],
                                            media_type=r.get("media_type"),
                                            title=r.get("title")
                                        )
                                        for r in variant_recommendations
                                    ]
                                
                                # 应用实时调整
                                if self.stream_processor:
                                    adjusted_recommendations = await self.stream_processor.apply_realtime_adjustments(
                                        adjusted_recommendations,
                                        str(user_id),
                                        minutes=30
                                    )
                                break
                
                # 记录推荐
                await self.ab_testing.record_recommendation(
                    experiment_id,
                    str(user_id),
                    adjusted_recommendations
                )
            
            # 转换为字典格式
            result = []
            for rec in adjusted_recommendations[:limit]:
                result.append({
                    "media_id": rec.media_id,
                    "score": rec.score,
                    "reason": rec.reason,
                    "confidence": rec.confidence,
                    "recommendation_type": rec.recommendation_type,
                    "media_type": rec.media_type,
                    "title": rec.title,
                    "variant": variant_name  # A/B测试变体信息
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get realtime recommendations: {e}")
            return []
    
    async def get_user_features(self, user_id: int) -> Dict[str, Any]:
        """获取用户特征"""
        await self._initialize()
        
        if self.feature_updater is None:
            return {}
        
        try:
            return await self.feature_updater.get_user_features(str(user_id))
        except Exception as e:
            logger.error(f"Failed to get user features: {e}")
            return {}
    
    async def get_item_features(self, item_id: str) -> Dict[str, Any]:
        """获取物品特征"""
        await self._initialize()
        
        if self.feature_updater is None:
            return {}
        
        try:
            return await self.feature_updater.get_item_features(item_id)
        except Exception as e:
            logger.error(f"Failed to get item features: {e}")
            return {}
    
    # A/B测试相关方法
    async def create_experiment(
        self,
        experiment_id: str,
        name: str,
        variants: List[Dict[str, Any]],
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建A/B测试实验"""
        await self._initialize()
        
        if self.ab_testing is None:
            raise ValueError("A/B testing is not enabled")
        
        try:
            experiment_variants = [
                ExperimentVariant(
                    name=v["name"],
                    algorithm=v["algorithm"],
                    config=v.get("config", {}),
                    traffic_percentage=v["traffic_percentage"],
                    description=v.get("description")
                )
                for v in variants
            ]
            
            experiment = await self.ab_testing.create_experiment(
                experiment_id=experiment_id,
                name=name,
                variants=experiment_variants,
                description=description
            )
            
            return {
                "experiment_id": experiment.experiment_id,
                "name": experiment.name,
                "status": experiment.status.value,
                "variants": [
                    {
                        "name": v.name,
                        "algorithm": v.algorithm,
                        "traffic_percentage": v.traffic_percentage
                    }
                    for v in experiment.variants
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to create experiment: {e}")
            raise
    
    async def start_experiment(self, experiment_id: str):
        """启动实验"""
        await self._initialize()
        
        if self.ab_testing is None:
            raise ValueError("A/B testing is not enabled")
        
        await self.ab_testing.start_experiment(experiment_id)
    
    async def evaluate_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """评估实验"""
        await self._initialize()
        
        if self.ab_testing is None:
            raise ValueError("A/B testing is not enabled")
        
        return await self.ab_testing.evaluate_experiment(experiment_id)
    
    async def stop_experiment(self, experiment_id: str):
        """停止实验"""
        await self._initialize()
        
        if self.ab_testing is None:
            raise ValueError("A/B testing is not enabled")
        
        await self.ab_testing.stop_experiment(experiment_id)
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        status = {
            "enabled": settings.REALTIME_RECOMMENDATION_ENABLED,
            "initialized": self._initialized
        }
        
        if self.stream_processor:
            status["stream_processor"] = self.stream_processor.get_status()
        
        if self.feature_updater:
            status["feature_updater"] = self.feature_updater.get_status()
        
        if self.ab_testing:
            status["ab_testing"] = self.ab_testing.get_status()
        
        return status

