"""
深度学习推荐算法
集成到现有推荐系统
"""

from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import pandas as pd
import asyncio
from datetime import datetime

from app.modules.recommendation.algorithms import RecommendationResult
from app.modules.recommendation.deep_learning.trainer import DeepLearningTrainer
from app.modules.recommendation.deep_learning.predictor import DeepLearningPredictor
from app.modules.recommendation.deep_learning.gpu_utils import check_gpu_available, get_device_info
from app.core.config import settings
from app.models.subscription import Subscription
from sqlalchemy import select


class DeepLearningRecommender:
    """深度学习推荐算法"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.trainer = None
        self.predictor = None
        self._initialized = False
    
    async def _initialize(self):
        """初始化训练器和预测器"""
        if self._initialized:
            return
        
        try:
            # 检查是否启用深度学习
            if not settings.DEEP_LEARNING_ENABLED:
                logger.info("Deep learning is disabled by configuration")
                return
            
            # 检查PyTorch是否可用
            try:
                import torch
            except ImportError:
                logger.warning("PyTorch is not installed, deep learning recommender will not work")
                return
            
            # 解析隐藏层维度
            hidden_dims = [
                int(dim.strip()) 
                for dim in settings.DEEP_LEARNING_HIDDEN_DIMS.split(",")
            ]
            
            # 创建训练器
            self.trainer = DeepLearningTrainer(
                model_type=settings.DEEP_LEARNING_MODEL_TYPE,
                embedding_dim=settings.DEEP_LEARNING_EMBEDDING_DIM,
                hidden_dims=hidden_dims,
                dropout_rate=settings.DEEP_LEARNING_DROPOUT_RATE,
                learning_rate=settings.DEEP_LEARNING_LEARNING_RATE,
                batch_size=settings.DEEP_LEARNING_BATCH_SIZE,
                epochs=settings.DEEP_LEARNING_EPOCHS,
                early_stopping_patience=settings.DEEP_LEARNING_EARLY_STOPPING_PATIENCE,
                enable_gpu=settings.DEEP_LEARNING_GPU_ENABLED
            )
            
            # 尝试加载已训练的模型
            import os
            model_path = settings.DEEP_LEARNING_MODEL_PATH
            model_file = os.path.join(model_path, f"{settings.DEEP_LEARNING_MODEL_TYPE}.pth")
            
            if os.path.exists(model_file):
                try:
                    self.trainer.load_model(model_file)
                    self.predictor = DeepLearningPredictor(self.trainer)
                    logger.info(f"Loaded trained model from {model_file}")
                except Exception as e:
                    logger.warning(f"Failed to load model from {model_file}: {e}")
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize deep learning recommender: {e}")
    
    async def get_recommendations(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[RecommendationResult]:
        """
        获取深度学习推荐
        
        Args:
            user_id: 用户ID
            limit: 推荐数量
        
        Returns:
            List[RecommendationResult]: 推荐结果列表
        """
        await self._initialize()
        
        if self.predictor is None:
            logger.debug("Deep learning predictor not available, returning empty list")
            return []
        
        try:
            # 获取用户订阅历史
            user_subscriptions = await self._get_user_subscriptions(user_id)
            
            if not user_subscriptions:
                logger.debug(f"User {user_id} has no subscription history")
                return []
            
            # 获取所有可推荐的内容
            all_subscriptions = await self._get_all_subscriptions()
            user_media_ids = {sub["media_id"] for sub in user_subscriptions}
            
            # 过滤出用户未订阅的内容
            candidate_items = [
                sub["media_id"] for sub in all_subscriptions
                if sub["media_id"] not in user_media_ids
            ]
            
            if not candidate_items:
                logger.debug("No candidate items for recommendation")
                return []
            
            # 使用深度学习模型预测
            user_id_str = str(user_id)
            recommendations = self.predictor.predict(user_id_str, candidate_items, limit * 2)
            
            # 补充媒体信息
            media_info_map = {
                sub["media_id"]: {
                    "media_type": sub["media_type"],
                    "title": sub["title"]
                }
                for sub in all_subscriptions
            }
            
            # 更新推荐结果的媒体信息
            for rec in recommendations:
                media_info = media_info_map.get(rec.media_id, {})
                rec.media_type = media_info.get("media_type")
                rec.title = media_info.get("title")
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Deep learning recommendation failed: {e}")
            return []
    
    async def _get_user_subscriptions(self, user_id: int) -> List[Dict]:
        """获取用户订阅历史"""
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
                    "user_id": str(user_id)
                }
                for sub in subscriptions
            ]
        except Exception as e:
            logger.error(f"Failed to get user subscriptions: {e}")
            return []
    
    async def _get_all_subscriptions(self) -> List[Dict]:
        """获取所有订阅数据"""
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
                    "title": sub.title
                }
                for sub in subscriptions
            ]
        except Exception as e:
            logger.error(f"Failed to get all subscriptions: {e}")
            return []
    
    async def prepare_training_data(self) -> pd.DataFrame:
        """准备训练数据"""
        try:
            # 获取所有订阅数据
            result = await self.db.execute(
                select(Subscription).where(
                    Subscription.status.in_(["active", "completed"])
                )
            )
            subscriptions = result.scalars().all()
            
            # 构建交互数据
            # 当前系统为单用户，使用用户ID=0
            interactions = []
            for sub in subscriptions:
                interactions.append({
                    "user_id": "0",  # 单用户系统
                    "item_id": f"{sub.media_type}_{sub.tmdb_id}",
                    "rating": 5.0,  # 默认评分，实际可以从用户评分数据获取
                    "timestamp": sub.created_at.isoformat() if sub.created_at else datetime.now().isoformat()
                })
            
            df = pd.DataFrame(interactions)
            return df
            
        except Exception as e:
            logger.error(f"Failed to prepare training data: {e}")
            return pd.DataFrame()
    
    async def train_model(self):
        """训练模型"""
        await self._initialize()
        
        if self.trainer is None:
            raise ValueError("Deep learning trainer is not initialized")
        
        try:
            # 准备训练数据
            logger.info("Preparing training data...")
            interactions = await self.prepare_training_data()
            
            if len(interactions) == 0:
                logger.warning("No training data available")
                return
            
            logger.info(f"Training data prepared: {len(interactions)} interactions")
            
            # 划分训练集和验证集（80/20）
            train_size = int(len(interactions) * 0.8)
            train_data = interactions[:train_size]
            val_data = interactions[train_size:] if len(interactions) > train_size else pd.DataFrame()
            
            # 训练模型
            logger.info("Starting model training...")
            await self.trainer.train(train_data, val_data)
            
            # 保存模型
            import os
            model_path = settings.DEEP_LEARNING_MODEL_PATH
            os.makedirs(model_path, exist_ok=True)
            
            model_file = os.path.join(model_path, f"{settings.DEEP_LEARNING_MODEL_TYPE}.pth")
            self.trainer.save_model(model_file)
            
            # 创建预测器
            self.predictor = DeepLearningPredictor(self.trainer)
            
            logger.info("Model training completed successfully")
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            raise
    
    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        await self._initialize()
        
        if self.trainer is None:
            return {
                "enabled": False,
                "reason": "Deep learning is disabled or PyTorch is not available"
            }
        
        info = self.trainer.get_model_info()
        info["enabled"] = True
        from app.modules.recommendation.deep_learning.gpu_utils import get_device_info
        info["device_info"] = get_device_info()
        
        return info

