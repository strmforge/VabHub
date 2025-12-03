"""
A/B测试框架
支持推荐算法的A/B测试和效果评估
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from loguru import logger
import math

from app.modules.recommendation.algorithms import RecommendationResult


class ExperimentStatus(Enum):
    """实验状态"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class ExperimentVariant:
    """实验变体"""
    name: str
    algorithm: str
    config: Dict[str, Any]
    traffic_percentage: float  # 流量分配百分比（0-100）
    description: Optional[str] = None


@dataclass
class ExperimentMetrics:
    """实验指标"""
    variant_name: str
    user_count: int = 0
    recommendation_count: int = 0
    click_count: int = 0
    like_count: int = 0
    subscribe_count: int = 0
    skip_count: int = 0
    avg_score: float = 0.0
    precision_at_k: Dict[int, float] = field(default_factory=dict)
    recall_at_k: Dict[int, float] = field(default_factory=dict)
    ndcg_at_k: Dict[int, float] = field(default_factory=dict)
    hit_rate: float = 0.0
    ctr: float = 0.0  # Click-Through Rate
    conversion_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class Experiment:
    """A/B测试实验"""
    experiment_id: str
    name: str
    description: Optional[str]
    variants: List[ExperimentVariant]
    status: ExperimentStatus
    start_time: datetime
    end_time: Optional[datetime]
    min_sample_size: int = 100
    significance_level: float = 0.05
    metrics: Dict[str, ExperimentMetrics] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_total_traffic(self) -> float:
        """获取总流量分配"""
        return sum(variant.traffic_percentage for variant in self.variants)
    
    def is_valid(self) -> bool:
        """检查实验是否有效"""
        total = self.get_total_traffic()
        return 99.0 <= total <= 101.0  # 允许1%的误差


class ABTestingFramework:
    """A/B测试框架"""
    
    def __init__(
        self,
        min_sample_size: int = 100,
        significance_level: float = 0.05,
        evaluation_k: int = 10
    ):
        """
        初始化A/B测试框架
        
        Args:
            min_sample_size: 最小样本量
            significance_level: 显著性水平（默认0.05）
            evaluation_k: 评估时的Top-K值
        """
        self.experiments: Dict[str, Experiment] = {}
        self.user_assignments: Dict[str, Dict[str, str]] = {}  # {experiment_id: {user_id: variant_name}}
        self.min_sample_size = min_sample_size
        self.significance_level = significance_level
        self.evaluation_k = evaluation_k
        
        # 用户交互记录（用于计算指标）
        self.user_interactions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    async def create_experiment(
        self,
        experiment_id: str,
        name: str,
        variants: List[ExperimentVariant],
        description: Optional[str] = None,
        min_sample_size: Optional[int] = None,
        significance_level: Optional[float] = None
    ) -> Experiment:
        """
        创建A/B测试实验
        
        Args:
            experiment_id: 实验ID
            name: 实验名称
            variants: 实验变体列表
            description: 实验描述
            min_sample_size: 最小样本量
            significance_level: 显著性水平
        
        Returns:
            创建的实验对象
        """
        try:
            # 验证变体
            total_traffic = sum(v.traffic_percentage for v in variants)
            if not (99.0 <= total_traffic <= 101.0):
                raise ValueError(f"Total traffic allocation must be 100%, got {total_traffic}%")
            
            experiment = Experiment(
                experiment_id=experiment_id,
                name=name,
                description=description,
                variants=variants,
                status=ExperimentStatus.DRAFT,
                start_time=datetime.now(),
                end_time=None,
                min_sample_size=min_sample_size or self.min_sample_size,
                significance_level=significance_level or self.significance_level
            )
            
            # 初始化指标
            for variant in variants:
                experiment.metrics[variant.name] = ExperimentMetrics(
                    variant_name=variant.name
                )
            
            self.experiments[experiment_id] = experiment
            self.user_assignments[experiment_id] = {}
            
            logger.info(f"Created experiment: {experiment_id} ({name})")
            
            return experiment
            
        except Exception as e:
            logger.error(f"Failed to create experiment: {e}")
            raise
    
    async def start_experiment(self, experiment_id: str):
        """启动实验"""
        try:
            if experiment_id not in self.experiments:
                raise ValueError(f"Experiment {experiment_id} not found")
            
            experiment = self.experiments[experiment_id]
            
            if not experiment.is_valid():
                raise ValueError("Experiment traffic allocation is invalid")
            
            experiment.status = ExperimentStatus.RUNNING
            experiment.start_time = datetime.now()
            
            logger.info(f"Started experiment: {experiment_id}")
            
        except Exception as e:
            logger.error(f"Failed to start experiment: {e}")
            raise
    
    async def assign_user_to_variant(
        self,
        experiment_id: str,
        user_id: str
    ) -> Optional[str]:
        """
        将用户分配到实验变体
        
        Args:
            experiment_id: 实验ID
            user_id: 用户ID
        
        Returns:
            变体名称，如果实验不存在或未运行则返回None
        """
        try:
            if experiment_id not in self.experiments:
                return None
            
            experiment = self.experiments[experiment_id]
            
            if experiment.status != ExperimentStatus.RUNNING:
                return None
            
            # 检查是否已经分配
            if experiment_id in self.user_assignments:
                if user_id in self.user_assignments[experiment_id]:
                    return self.user_assignments[experiment_id][user_id]
            
            # 根据流量分配随机分配
            import random
            random_value = random.random() * 100
            
            cumulative = 0.0
            for variant in experiment.variants:
                cumulative += variant.traffic_percentage
                if random_value <= cumulative:
                    # 分配用户到该变体
                    if experiment_id not in self.user_assignments:
                        self.user_assignments[experiment_id] = {}
                    self.user_assignments[experiment_id][user_id] = variant.name
                    
                    logger.debug(
                        f"Assigned user {user_id} to variant {variant.name} "
                        f"in experiment {experiment_id}"
                    )
                    
                    return variant.name
            
            # 默认分配到第一个变体
            if experiment.variants:
                variant_name = experiment.variants[0].name
                if experiment_id not in self.user_assignments:
                    self.user_assignments[experiment_id] = {}
                self.user_assignments[experiment_id][user_id] = variant_name
                return variant_name
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to assign user to variant: {e}")
            return None
    
    async def record_interaction(
        self,
        experiment_id: str,
        user_id: str,
        interaction_type: str,
        item_id: Optional[str] = None,
        value: Optional[float] = None
    ):
        """
        记录用户交互
        
        Args:
            experiment_id: 实验ID
            user_id: 用户ID
            interaction_type: 交互类型（click, like, subscribe等）
            item_id: 物品ID
            value: 交互值（如评分）
        """
        try:
            if experiment_id not in self.experiments:
                return
            
            experiment = self.experiments[experiment_id]
            
            if experiment.status != ExperimentStatus.RUNNING:
                return
            
            # 获取用户分配的变体
            variant_name = await self.assign_user_to_variant(experiment_id, user_id)
            if not variant_name:
                return
            
            # 更新指标
            if variant_name in experiment.metrics:
                metrics = experiment.metrics[variant_name]
                metrics.user_count = len(
                    self.user_assignments.get(experiment_id, {})
                )
                
                if interaction_type == "click":
                    metrics.click_count += 1
                elif interaction_type == "like":
                    metrics.like_count += 1
                elif interaction_type == "subscribe":
                    metrics.subscribe_count += 1
                elif interaction_type == "skip":
                    metrics.skip_count += 1
                
                metrics.last_updated = datetime.now()
                
                # 计算CTR和转化率
                if metrics.recommendation_count > 0:
                    metrics.ctr = metrics.click_count / metrics.recommendation_count
                    metrics.conversion_rate = (
                        (metrics.like_count + metrics.subscribe_count) / 
                        metrics.recommendation_count
                    )
            
            # 记录交互
            interaction_key = f"{experiment_id}:{user_id}"
            self.user_interactions[interaction_key].append({
                "interaction_type": interaction_type,
                "item_id": item_id,
                "value": value,
                "variant": variant_name,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to record interaction: {e}")
    
    async def record_recommendation(
        self,
        experiment_id: str,
        user_id: str,
        recommendations: List[RecommendationResult]
    ):
        """
        记录推荐结果
        
        Args:
            experiment_id: 实验ID
            user_id: 用户ID
            recommendations: 推荐结果列表
        """
        try:
            if experiment_id not in self.experiments:
                return
            
            experiment = self.experiments[experiment_id]
            
            if experiment.status != ExperimentStatus.RUNNING:
                return
            
            # 获取用户分配的变体
            variant_name = await self.assign_user_to_variant(experiment_id, user_id)
            if not variant_name:
                return
            
            # 更新指标
            if variant_name in experiment.metrics:
                metrics = experiment.metrics[variant_name]
                metrics.recommendation_count += len(recommendations)
                
                if recommendations:
                    metrics.avg_score = (
                        (metrics.avg_score * (metrics.recommendation_count - len(recommendations)) +
                         sum(r.score for r in recommendations)) / 
                        metrics.recommendation_count
                    )
                
                metrics.last_updated = datetime.now()
            
        except Exception as e:
            logger.error(f"Failed to record recommendation: {e}")
    
    async def evaluate_experiment(
        self,
        experiment_id: str
    ) -> Dict[str, Any]:
        """
        评估实验效果
        
        Args:
            experiment_id: 实验ID
        
        Returns:
            评估结果
        """
        try:
            if experiment_id not in self.experiments:
                raise ValueError(f"Experiment {experiment_id} not found")
            
            experiment = self.experiments[experiment_id]
            
            if experiment.status != ExperimentStatus.RUNNING:
                raise ValueError("Experiment is not running")
            
            # 检查样本量
            for variant_name, metrics in experiment.metrics.items():
                if metrics.user_count < experiment.min_sample_size:
                    return {
                        "status": "insufficient_samples",
                        "message": f"Variant {variant_name} has insufficient samples",
                        "required": experiment.min_sample_size,
                        "current": metrics.user_count
                    }
            
            # 计算统计显著性
            significance_results = await self._calculate_significance(experiment)
            
            # 找出最佳变体
            best_variant = self._find_best_variant(experiment)
            
            return {
                "status": "completed",
                "experiment_id": experiment_id,
                "metrics": {
                    variant_name: {
                        "user_count": metrics.user_count,
                        "recommendation_count": metrics.recommendation_count,
                        "click_count": metrics.click_count,
                        "like_count": metrics.like_count,
                        "subscribe_count": metrics.subscribe_count,
                        "ctr": metrics.ctr,
                        "conversion_rate": metrics.conversion_rate,
                        "avg_score": metrics.avg_score
                    }
                    for variant_name, metrics in experiment.metrics.items()
                },
                "significance": significance_results,
                "best_variant": best_variant
            }
            
        except Exception as e:
            logger.error(f"Failed to evaluate experiment: {e}")
            raise
    
    async def _calculate_significance(
        self,
        experiment: Experiment
    ) -> Dict[str, Any]:
        """计算统计显著性"""
        try:
            # 简化的统计显著性计算
            # 实际应用中可以使用t-test、chi-square test等
            
            variants = list(experiment.metrics.keys())
            if len(variants) < 2:
                return {}
            
            # 比较CTR
            ctr_values = {
                name: metrics.ctr 
                for name, metrics in experiment.metrics.items()
            }
            
            # 比较转化率
            conversion_values = {
                name: metrics.conversion_rate 
                for name, metrics in experiment.metrics.items()
            }
            
            # 简化的显著性判断（实际应使用统计检验）
            control_variant = variants[0]
            control_ctr = ctr_values.get(control_variant, 0)
            control_conversion = conversion_values.get(control_variant, 0)
            
            significance = {}
            
            for variant_name in variants[1:]:
                variant_ctr = ctr_values.get(variant_name, 0)
                variant_conversion = conversion_values.get(variant_name, 0)
                
                # 计算提升百分比
                ctr_lift = (
                    (variant_ctr - control_ctr) / control_ctr * 100 
                    if control_ctr > 0 else 0
                )
                conversion_lift = (
                    (variant_conversion - control_conversion) / control_conversion * 100 
                    if control_conversion > 0 else 0
                )
                
                # 简化的显著性判断（实际应使用统计检验）
                is_significant = (
                    abs(ctr_lift) > 5.0 or abs(conversion_lift) > 5.0
                )  # 5%提升认为显著
                
                significance[variant_name] = {
                    "ctr_lift": ctr_lift,
                    "conversion_lift": conversion_lift,
                    "is_significant": is_significant,
                    "p_value": 0.05 if is_significant else 0.1  # 占位值
                }
            
            return significance
            
        except Exception as e:
            logger.error(f"Failed to calculate significance: {e}")
            return {}
    
    def _find_best_variant(self, experiment: Experiment) -> Optional[str]:
        """找出最佳变体"""
        try:
            if not experiment.metrics:
                return None
            
            # 综合评分：CTR权重0.4，转化率权重0.4，平均分权重0.2
            variant_scores = {}
            
            for variant_name, metrics in experiment.metrics.items():
                score = (
                    metrics.ctr * 0.4 +
                    metrics.conversion_rate * 0.4 +
                    metrics.avg_score * 0.2
                )
                variant_scores[variant_name] = score
            
            if variant_scores:
                return max(variant_scores, key=variant_scores.get)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find best variant: {e}")
            return None
    
    async def stop_experiment(self, experiment_id: str):
        """停止实验"""
        try:
            if experiment_id not in self.experiments:
                raise ValueError(f"Experiment {experiment_id} not found")
            
            experiment = self.experiments[experiment_id]
            experiment.status = ExperimentStatus.COMPLETED
            experiment.end_time = datetime.now()
            
            logger.info(f"Stopped experiment: {experiment_id}")
            
        except Exception as e:
            logger.error(f"Failed to stop experiment: {e}")
            raise
    
    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """获取实验"""
        return self.experiments.get(experiment_id)
    
    def list_experiments(
        self,
        status: Optional[ExperimentStatus] = None
    ) -> List[Experiment]:
        """列出实验"""
        experiments = list(self.experiments.values())
        
        if status:
            experiments = [e for e in experiments if e.status == status]
        
        return experiments
    
    def get_status(self) -> Dict[str, Any]:
        """获取框架状态"""
        return {
            'total_experiments': len(self.experiments),
            'running_experiments': len([
                e for e in self.experiments.values() 
                if e.status == ExperimentStatus.RUNNING
            ]),
            'min_sample_size': self.min_sample_size,
            'significance_level': self.significance_level
        }

