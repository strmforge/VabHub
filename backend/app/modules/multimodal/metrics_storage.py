"""
多模态分析性能指标数据库存储
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload

from app.models.multimodal_metrics import (
    MultimodalPerformanceMetric,
    MultimodalPerformanceAlert,
    MultimodalOptimizationHistory
)
from app.modules.multimodal.metrics import MultimodalMetrics


class MetricsStorage:
    """性能指标数据库存储"""
    
    def __init__(self, db: AsyncSession):
        """
        初始化指标存储
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    async def save_metric(
        self,
        operation: str,
        cache_hit: bool,
        duration: float,
        error: bool,
        concurrent: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MultimodalPerformanceMetric:
        """
        保存性能指标
        
        Args:
            operation: 操作类型
            cache_hit: 是否缓存命中
            duration: 响应时间（秒）
            error: 是否发生错误
            concurrent: 并发数
            metadata: 额外元数据
            
        Returns:
            保存的性能指标记录
        """
        try:
            metric = MultimodalPerformanceMetric(
                operation=operation,
                timestamp=datetime.now(),
                cache_hit=cache_hit,
                duration=duration,
                error=error,
                concurrent=concurrent,
                extra_metadata=metadata or {}
            )
            self.db.add(metric)
            await self.db.flush()
            return metric
        except Exception as e:
            logger.error(f"保存性能指标失败: {e}")
            raise
    
    async def get_metrics(
        self,
        operation: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[MultimodalPerformanceMetric]:
        """
        获取性能指标
        
        Args:
            operation: 操作类型
            start_time: 开始时间
            end_time: 结束时间
            limit: 限制数量
            
        Returns:
            性能指标列表
        """
        try:
            query = select(MultimodalPerformanceMetric)
            
            conditions = []
            if operation:
                conditions.append(MultimodalPerformanceMetric.operation == operation)
            if start_time:
                conditions.append(MultimodalPerformanceMetric.timestamp >= start_time)
            if end_time:
                conditions.append(MultimodalPerformanceMetric.timestamp <= end_time)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.order_by(desc(MultimodalPerformanceMetric.timestamp)).limit(limit)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"获取性能指标失败: {e}")
            return []
    
    async def get_metrics_statistics(
        self,
        operation: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取性能指标统计信息
        
        Args:
            operation: 操作类型
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            统计信息字典
        """
        try:
            query = select(
                MultimodalPerformanceMetric.operation,
                func.count(MultimodalPerformanceMetric.id).label('total_count'),
                func.sum(func.cast(MultimodalPerformanceMetric.cache_hit, Integer)).label('cache_hits'),
                func.avg(MultimodalPerformanceMetric.duration).label('avg_duration'),
                func.min(MultimodalPerformanceMetric.duration).label('min_duration'),
                func.max(MultimodalPerformanceMetric.duration).label('max_duration'),
                func.sum(func.cast(MultimodalPerformanceMetric.error, Integer)).label('error_count'),
                func.max(MultimodalPerformanceMetric.concurrent).label('max_concurrent')
            )
            
            conditions = []
            if operation:
                conditions.append(MultimodalPerformanceMetric.operation == operation)
            if start_time:
                conditions.append(MultimodalPerformanceMetric.timestamp >= start_time)
            if end_time:
                conditions.append(MultimodalPerformanceMetric.timestamp <= end_time)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.group_by(MultimodalPerformanceMetric.operation)
            
            result = await self.db.execute(query)
            rows = result.all()
            
            statistics = {}
            for row in rows:
                op = row.operation
                total = row.total_count or 0
                cache_hits = row.cache_hits or 0
                cache_misses = total - cache_hits
                cache_hit_rate = cache_hits / total if total > 0 else 0.0
                error_count = row.error_count or 0
                error_rate = error_count / total if total > 0 else 0.0
                
                statistics[op] = {
                    "total_requests": total,
                    "cache_hits": cache_hits,
                    "cache_misses": cache_misses,
                    "cache_hit_rate": cache_hit_rate,
                    "avg_duration": float(row.avg_duration or 0.0),
                    "min_duration": float(row.min_duration or 0.0),
                    "max_duration": float(row.max_duration or 0.0),
                    "error_count": error_count,
                    "error_rate": error_rate,
                    "max_concurrent": row.max_concurrent or 0
                }
            
            return statistics
        except Exception as e:
            logger.error(f"获取性能指标统计信息失败: {e}")
            return {}
    
    async def cleanup_old_metrics(self, days: int = 30) -> int:
        """
        清理旧性能指标
        
        Args:
            days: 保留天数
            
        Returns:
            删除的记录数
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            
            query = select(MultimodalPerformanceMetric).where(
                MultimodalPerformanceMetric.timestamp < cutoff_time
            )
            
            result = await self.db.execute(query)
            old_metrics = result.scalars().all()
            
            count = len(old_metrics)
            for metric in old_metrics:
                await self.db.delete(metric)
            
            await self.db.flush()
            logger.info(f"清理了{count}条旧性能指标记录（{days}天前）")
            return count
        except Exception as e:
            logger.error(f"清理旧性能指标失败: {e}")
            return 0

