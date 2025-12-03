"""
流式推荐计算处理器
处理实时用户交互流，动态调整推荐结果
"""

import asyncio
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import threading

from app.modules.recommendation.algorithms import RecommendationResult


class InteractionType(Enum):
    """交互类型枚举"""
    VIEW = "view"
    CLICK = "click"
    LIKE = "like"
    DISLIKE = "dislike"
    SHARE = "share"
    BOOKMARK = "bookmark"
    PURCHASE = "purchase"
    RATING = "rating"
    SKIP = "skip"
    DWELL_TIME = "dwell_time"
    SUBSCRIBE = "subscribe"  # VabHub特有：订阅行为


@dataclass
class RealTimeInteraction:
    """实时交互数据"""
    user_id: str
    item_id: str
    interaction_type: InteractionType
    value: Optional[float] = None  # 评分、停留时间等
    context: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "item_id": self.item_id,
            "interaction_type": self.interaction_type.value,
            "value": self.value,
            "context": self.context,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class UserSession:
    """用户会话"""
    user_id: str
    session_id: str
    interactions: List[RealTimeInteraction] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def add_interaction(self, interaction: RealTimeInteraction):
        """添加交互"""
        self.interactions.append(interaction)
        self.last_activity = interaction.timestamp
    
    def get_session_duration(self) -> float:
        """获取会话持续时间（秒）"""
        return (self.last_activity - self.start_time).total_seconds()
    
    def is_active(self, timeout_minutes: int = 30) -> bool:
        """检查会话是否活跃"""
        timeout = datetime.now() - timedelta(minutes=timeout_minutes)
        return self.last_activity > timeout


class InteractionBuffer:
    """交互缓冲区（线程安全）"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)
        self.user_buffers = defaultdict(lambda: deque(maxlen=1000))
        self.lock = threading.Lock()
    
    def add_interaction(self, interaction: RealTimeInteraction):
        """添加交互到缓冲区"""
        with self.lock:
            self.buffer.append(interaction)
            self.user_buffers[interaction.user_id].append(interaction)
    
    def get_recent_interactions(self, minutes: int = 60) -> List[RealTimeInteraction]:
        """获取最近的交互"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self.lock:
            return [
                interaction for interaction in self.buffer
                if interaction.timestamp > cutoff_time
            ]
    
    def get_user_interactions(self, user_id: str, minutes: int = 60) -> List[RealTimeInteraction]:
        """获取用户最近的交互"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self.lock:
            if user_id not in self.user_buffers:
                return []
            return [
                interaction for interaction in self.user_buffers[user_id]
                if interaction.timestamp > cutoff_time
            ]
    
    def clear_old_interactions(self, hours: int = 24):
        """清理旧的交互数据"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            # 清理全局缓冲区
            while self.buffer and self.buffer[0].timestamp < cutoff_time:
                self.buffer.popleft()
            
            # 清理用户缓冲区
            for user_id in list(self.user_buffers.keys()):
                user_buffer = self.user_buffers[user_id]
                while user_buffer and user_buffer[0].timestamp < cutoff_time:
                    user_buffer.popleft()
                
                # 如果用户缓冲区为空，删除它
                if not user_buffer:
                    del self.user_buffers[user_id]


class StreamProcessor:
    """流式推荐计算处理器"""
    
    def __init__(
        self,
        buffer_size: int = 10000,
        session_timeout_minutes: int = 30,
        interaction_weights: Optional[Dict[str, float]] = None,
        time_decay_factor: float = 0.95
    ):
        """
        初始化流式处理器
        
        Args:
            buffer_size: 缓冲区大小
            session_timeout_minutes: 会话超时时间（分钟）
            interaction_weights: 交互权重配置
            time_decay_factor: 时间衰减因子
        """
        self.interaction_buffer = InteractionBuffer(buffer_size)
        self.user_sessions: Dict[str, UserSession] = {}
        self.session_timeout = session_timeout_minutes
        
        # 交互权重（默认值）
        self.interaction_weights = interaction_weights or {
            InteractionType.VIEW.value: 0.1,
            InteractionType.CLICK.value: 0.3,
            InteractionType.LIKE.value: 0.8,
            InteractionType.DISLIKE.value: -0.5,
            InteractionType.SHARE.value: 1.0,
            InteractionType.BOOKMARK.value: 0.9,
            InteractionType.PURCHASE.value: 1.5,
            InteractionType.RATING.value: 1.0,
            InteractionType.SKIP.value: -0.2,
            InteractionType.SUBSCRIBE.value: 1.2  # VabHub特有：订阅权重较高
        }
        
        self.time_decay_factor = time_decay_factor
        self.running = True
    
    async def record_interaction(self, interaction: RealTimeInteraction):
        """记录用户交互"""
        try:
            # 添加到缓冲区
            self.interaction_buffer.add_interaction(interaction)
            
            # 更新用户会话
            await self._update_user_session(interaction)
            
            logger.debug(
                f"Recorded interaction: {interaction.user_id} -> {interaction.item_id} "
                f"({interaction.interaction_type.value})"
            )
            
        except Exception as e:
            logger.error(f"Failed to record interaction: {e}")
    
    async def _update_user_session(self, interaction: RealTimeInteraction):
        """更新用户会话"""
        user_id = interaction.user_id
        
        # 检查是否有活跃会话
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            if session.is_active(self.session_timeout):
                session.add_interaction(interaction)
                return
        
        # 创建新会话
        import time
        session_id = f"{user_id}_{int(time.time())}"
        self.user_sessions[user_id] = UserSession(
            user_id=user_id,
            session_id=session_id,
            interactions=[interaction],
            start_time=interaction.timestamp,
            last_activity=interaction.timestamp,
            context=interaction.context or {}
        )
    
    def get_user_interactions(
        self, 
        user_id: str, 
        minutes: int = 60
    ) -> List[RealTimeInteraction]:
        """获取用户最近的交互"""
        return self.interaction_buffer.get_user_interactions(user_id, minutes)
    
    def get_user_session(self, user_id: str) -> Optional[UserSession]:
        """获取用户会话"""
        session = self.user_sessions.get(user_id)
        if session and session.is_active(self.session_timeout):
            return session
        return None
    
    async def apply_realtime_adjustments(
        self,
        recommendations: List[RecommendationResult],
        user_id: str,
        minutes: int = 30
    ) -> List[RecommendationResult]:
        """
        应用实时调整到推荐结果
        
        Args:
            recommendations: 基础推荐结果
            user_id: 用户ID
            minutes: 考虑最近多少分钟的交互
        
        Returns:
            调整后的推荐结果
        """
        try:
            # 获取用户最近的交互
            recent_interactions = self.get_user_interactions(user_id, minutes)
            
            if not recent_interactions:
                return recommendations
            
            # 计算实时偏好
            recent_items: Set[str] = set()
            negative_items: Set[str] = set()
            category_preferences = defaultdict(float)
            
            for interaction in recent_interactions:
                # 记录交互过的物品
                if interaction.interaction_type in [
                    InteractionType.DISLIKE, 
                    InteractionType.SKIP
                ]:
                    negative_items.add(interaction.item_id)
                else:
                    recent_items.add(interaction.item_id)
                
                # 更新类别偏好
                if interaction.context:
                    weight = self.interaction_weights.get(
                        interaction.interaction_type.value, 
                        0.1
                    )
                    for key, value in interaction.context.items():
                        if key.startswith('category_') or key.startswith('genre_'):
                            category_preferences[value] += weight
            
            # 调整推荐分数
            adjusted_recommendations = []
            
            for rec in recommendations:
                # 跳过用户最近不喜欢的物品
                if rec.media_id in negative_items:
                    continue
                
                # 跳过用户最近已经交互过的物品
                if rec.media_id in recent_items:
                    continue
                
                # 应用类别偏好调整
                category_boost = 0.0
                if rec.media_type:
                    # 简单的类别匹配（可以根据实际需求扩展）
                    category_boost = category_preferences.get(rec.media_type, 0.0) * 0.1
                
                # 计算调整后的分数
                adjusted_score = rec.score * (1 + category_boost)
                
                # 创建调整后的推荐结果
                adjusted_rec = RecommendationResult(
                    media_id=rec.media_id,
                    score=adjusted_score,
                    reason=f"{rec.reason} (实时调整: +{category_boost:.3f})",
                    confidence=min(rec.confidence * (1 + category_boost * 0.1), 1.0),
                    recommendation_type="realtime_adjusted",
                    media_type=rec.media_type,
                    title=rec.title
                )
                
                adjusted_recommendations.append(adjusted_rec)
            
            # 重新排序
            adjusted_recommendations.sort(key=lambda x: x.score, reverse=True)
            
            return adjusted_recommendations
            
        except Exception as e:
            logger.error(f"Failed to apply realtime adjustments: {e}")
            return recommendations
    
    async def calculate_preference_adjustments(
        self,
        interactions: List[RealTimeInteraction]
    ) -> Dict[str, float]:
        """
        计算偏好调整
        
        Args:
            interactions: 交互列表
        
        Returns:
            偏好调整字典 {item_id: adjustment_score}
        """
        try:
            adjustments = defaultdict(float)
            current_time = datetime.now()
            
            for interaction in interactions:
                # 计算时间衰减
                time_diff = (current_time - interaction.timestamp).total_seconds() / 3600  # 小时
                time_weight = self.time_decay_factor ** time_diff
                
                # 获取交互权重
                interaction_weight = self.interaction_weights.get(
                    interaction.interaction_type.value, 
                    0.1
                )
                
                # 计算最终权重
                final_weight = interaction_weight * time_weight
                
                # 如果有评分值，使用它
                if interaction.value is not None:
                    final_weight *= interaction.value
                
                # 更新物品偏好
                adjustments[interaction.item_id] += final_weight
                
                # 如果有上下文信息，更新类别偏好
                if interaction.context:
                    for key, value in interaction.context.items():
                        if key.startswith('category_') or key.startswith('genre_'):
                            adjustments[f"context_{key}_{value}"] += final_weight * 0.5
            
            return dict(adjustments)
            
        except Exception as e:
            logger.error(f"Failed to calculate preference adjustments: {e}")
            return {}
    
    async def analyze_session_patterns(
        self, 
        session: UserSession
    ) -> Dict[str, Any]:
        """分析会话行为模式"""
        try:
            patterns = {
                'dominant_interaction_type': None,
                'interaction_frequency': 0,
                'category_focus': {},
                'engagement_level': 0
            }
            
            if not session.interactions:
                return patterns
            
            # 分析主要交互类型
            interaction_counts = defaultdict(int)
            for interaction in session.interactions:
                interaction_counts[interaction.interaction_type] += 1
            
            if interaction_counts:
                patterns['dominant_interaction_type'] = max(
                    interaction_counts, 
                    key=interaction_counts.get
                ).value
            
            # 计算交互频率
            session_duration = session.get_session_duration()
            if session_duration > 0:
                patterns['interaction_frequency'] = len(session.interactions) / (session_duration / 60)  # 每分钟
            
            # 分析类别关注度
            category_interactions = defaultdict(int)
            for interaction in session.interactions:
                if interaction.context and 'category' in interaction.context:
                    category_interactions[interaction.context['category']] += 1
            
            if category_interactions:
                total_interactions = sum(category_interactions.values())
                patterns['category_focus'] = {
                    cat: count / total_interactions 
                    for cat, count in category_interactions.items()
                }
            
            # 计算参与度
            positive_interactions = sum(
                1 for interaction in session.interactions
                if interaction.interaction_type in [
                    InteractionType.LIKE, 
                    InteractionType.SHARE, 
                    InteractionType.BOOKMARK, 
                    InteractionType.PURCHASE,
                    InteractionType.SUBSCRIBE
                ]
            )
            if len(session.interactions) > 0:
                patterns['engagement_level'] = positive_interactions / len(session.interactions)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to analyze session patterns: {e}")
            return {}
    
    async def cleanup_old_data(self, hours: int = 24):
        """清理旧数据"""
        try:
            # 清理旧的交互数据
            self.interaction_buffer.clear_old_interactions(hours)
            
            # 清理过期的会话
            expired_sessions = []
            for user_id, session in self.user_sessions.items():
                if not session.is_active(self.session_timeout):
                    expired_sessions.append(user_id)
            
            for user_id in expired_sessions:
                del self.user_sessions[user_id]
            
            logger.info(f"Cleanup completed: removed {len(expired_sessions)} expired sessions")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取处理器状态"""
        return {
            'buffer_size': len(self.interaction_buffer.buffer),
            'active_sessions': len(self.user_sessions),
            'session_timeout_minutes': self.session_timeout,
            'interaction_weights': self.interaction_weights,
            'time_decay_factor': self.time_decay_factor
        }

