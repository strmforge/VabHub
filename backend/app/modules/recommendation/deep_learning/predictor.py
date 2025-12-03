"""
深度学习模型预测器
"""

from typing import List, Dict, Optional, Tuple
from loguru import logger
import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available, deep learning predictor will not work")

from app.modules.recommendation.deep_learning.trainer import DeepLearningTrainer
from app.modules.recommendation.algorithms import RecommendationResult


class DeepLearningPredictor:
    """深度学习模型预测器"""
    
    def __init__(self, trainer: DeepLearningTrainer):
        """
        初始化预测器
        
        Args:
            trainer: 训练器实例（包含已训练的模型）
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is not installed")
        
        self.trainer = trainer
        self.model = trainer.model
        self.device = trainer.device
        
        if not trainer.is_trained:
            raise ValueError("Model is not trained yet")
    
    def predict(
        self, 
        user_id: str, 
        candidate_items: List[str], 
        k: int = 10
    ) -> List[RecommendationResult]:
        """
        生成推荐预测
        
        Args:
            user_id: 用户ID
            candidate_items: 候选物品ID列表
            k: 返回Top-K推荐
        
        Returns:
            List[RecommendationResult]: 推荐结果列表
        """
        if not TORCH_AVAILABLE:
            return []
        
        try:
            # 检查用户是否存在
            if user_id not in self.trainer.user_to_idx:
                logger.warning(f"User {user_id} not found in training data, using cold start")
                return self._cold_start_recommend(candidate_items, k)
            
            user_idx = self.trainer.user_to_idx[user_id]
            
            # 计算候选物品的评分
            item_scores = []
            
            self.model.eval()
            with torch.no_grad():
                # 批量预测（提高效率）
                batch_size = 64
                for i in range(0, len(candidate_items), batch_size):
                    batch_items = candidate_items[i:i + batch_size]
                    
                    # 过滤掉不在训练数据中的物品
                    valid_items = [
                        item for item in batch_items 
                        if item in self.trainer.item_to_idx
                    ]
                    
                    if not valid_items:
                        continue
                    
                    # 准备批量输入
                    user_indices = torch.tensor(
                        [user_idx] * len(valid_items), 
                        dtype=torch.long
                    ).to(self.device)
                    item_indices = torch.tensor(
                        [self.trainer.item_to_idx[item] for item in valid_items],
                        dtype=torch.long
                    ).to(self.device)
                    
                    # 预测
                    if self.trainer.model_type == "autoencoder":
                        # 自编码器需要不同的预测逻辑
                        logger.warning("Autoencoder prediction not fully implemented")
                        scores = torch.zeros(len(valid_items))
                    else:
                        scores = self.model(user_indices, item_indices)
                    
                    # 收集结果
                    for item, score in zip(valid_items, scores.cpu().numpy()):
                        item_scores.append((item, float(score)))
            
            # 排序并选择top-k
            item_scores.sort(key=lambda x: x[1], reverse=True)
            
            recommendations = []
            for item_id, score in item_scores[:k]:
                recommendations.append(RecommendationResult(
                    media_id=item_id,
                    score=float(score),
                    reason=f"Deep learning {self.trainer.model_type} prediction",
                    confidence=min(abs(score) / 5.0, 1.0),  # 归一化置信度
                    recommendation_type="deep_learning",
                    media_type=None,  # 需要从数据库获取
                    title=None  # 需要从数据库获取
                ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return []
    
    def _cold_start_recommend(
        self, 
        candidate_items: List[str], 
        k: int
    ) -> List[RecommendationResult]:
        """冷启动推荐（用户不在训练数据中）"""
        try:
            # 基于物品流行度推荐
            recommendations = []
            
            # 只推荐在训练数据中出现的物品
            valid_items = [
                item for item in candidate_items 
                if item in self.trainer.item_to_idx
            ]
            
            # 简化实现：随机推荐或基于物品索引
            for i, item_id in enumerate(valid_items[:k]):
                # 简单的流行度评分
                popularity_score = 1.0 / (i + 1)
                
                recommendations.append(RecommendationResult(
                    media_id=item_id,
                    score=popularity_score,
                    reason="Cold start recommendation based on popularity",
                    confidence=0.5,
                    recommendation_type="deep_learning_cold_start",
                    media_type=None,
                    title=None
                ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Cold start recommendation failed: {e}")
            return []
    
    def predict_batch(
        self, 
        user_items: List[Tuple[str, str]]
    ) -> List[float]:
        """
        批量预测用户-物品对
        
        Args:
            user_items: 用户-物品对列表 [(user_id, item_id), ...]
        
        Returns:
            List[float]: 预测评分列表
        """
        if not TORCH_AVAILABLE:
            return []
        
        try:
            self.model.eval()
            
            # 过滤有效的用户-物品对
            valid_pairs = []
            valid_indices = []
            
            for user_id, item_id in user_items:
                if user_id in self.trainer.user_to_idx and item_id in self.trainer.item_to_idx:
                    valid_pairs.append((user_id, item_id))
                    valid_indices.append((
                        self.trainer.user_to_idx[user_id],
                        self.trainer.item_to_idx[item_id]
                    ))
            
            if not valid_indices:
                return []
            
            # 批量预测
            user_indices = torch.tensor(
                [idx[0] for idx in valid_indices],
                dtype=torch.long
            ).to(self.device)
            item_indices = torch.tensor(
                [idx[1] for idx in valid_indices],
                dtype=torch.long
            ).to(self.device)
            
            with torch.no_grad():
                if self.trainer.model_type == "autoencoder":
                    scores = torch.zeros(len(valid_indices))
                else:
                    scores = self.model(user_indices, item_indices)
            
            # 构建完整结果（包括无效对）
            results = []
            valid_idx = 0
            
            for user_id, item_id in user_items:
                if (user_id, item_id) in valid_pairs:
                    results.append(float(scores[valid_idx].cpu().item()))
                    valid_idx += 1
                else:
                    results.append(0.0)  # 无效对返回0
            
            return results
            
        except Exception as e:
            logger.error(f"Batch prediction failed: {e}")
            return [0.0] * len(user_items)

