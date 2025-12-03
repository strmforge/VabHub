"""
做种统计服务
提供做种数据的统计分析功能
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
from app.core.cache import get_cache

from app.models.download import DownloadTask
from app.models.hnr import HNRTask


class SeedingStatistics:
    """做种统计服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache = get_cache()
    
    async def get_daily_statistics(
        self,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        获取每日做种统计
        
        Args:
            days: 查询天数（默认7天）
            
        Returns:
            每日统计列表
        """
        try:
            # 生成缓存键
            cache_key = self.cache.generate_key("seeding_daily_statistics", days=days)
            
            # 尝试从缓存获取
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            statistics = []
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # 获取每日完成的下载任务
            for i in range(days):
                date = datetime.utcnow() - timedelta(days=i)
                date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
                date_end = date_start + timedelta(days=1)
                
                # 查询该日完成的下载任务
                result = await self.db.execute(
                    select(func.count(DownloadTask.id), func.sum(DownloadTask.size_gb))
                    .where(
                        DownloadTask.status == "completed",
                        DownloadTask.completed_at >= date_start,
                        DownloadTask.completed_at < date_end
                    )
                )
                count, total_size = result.first() or (0, 0)
                
                statistics.append({
                    "date": date_start.date().isoformat(),
                    "completed_tasks": count or 0,
                    "total_size_gb": float(total_size or 0)
                })
            
            # 反转列表（从最早到最新）
            statistics.reverse()
            
            # 缓存结果（1小时）
            await self.cache.set(cache_key, statistics, ttl=3600)
            
            return statistics
            
        except Exception as e:
            logger.error(f"获取每日做种统计失败: {e}")
            return []
    
    async def get_hnr_statistics(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        获取HNR相关做种统计
        
        Args:
            days: 查询天数（默认7天）
            
        Returns:
            HNR统计信息
        """
        try:
            # 生成缓存键
            cache_key = self.cache.generate_key("seeding_hnr_statistics", days=days)
            
            # 尝试从缓存获取
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # 获取HNR任务统计
            result = await self.db.execute(
                select(
                    func.count(HNRTask.id).label("total_tasks"),
                    func.avg(HNRTask.current_ratio).label("avg_ratio"),
                    func.avg(HNRTask.seed_time_hours).label("avg_seed_time"),
                    func.sum(
                        case(
                            (
                                and_(
                                    HNRTask.current_ratio >= HNRTask.required_ratio,
                                    HNRTask.seed_time_hours >= HNRTask.required_seed_time_hours
                                ),
                                1
                            ),
                            else_=0
                        )
                    ).label("completed_tasks")
                )
                .where(HNRTask.created_at >= cutoff_date)
            )
            
            stats = result.first()
            
            statistics = {
                "total_tasks": stats.total_tasks or 0,
                "completed_tasks": stats.completed_tasks or 0,
                "average_ratio": float(stats.avg_ratio or 0.0),
                "average_seed_time_hours": float(stats.avg_seed_time or 0.0),
                "completion_rate": 0.0
            }
            
            # 计算完成率
            if statistics["total_tasks"] > 0:
                statistics["completion_rate"] = statistics["completed_tasks"] / statistics["total_tasks"]
            
            # 缓存结果（1小时）
            await self.cache.set(cache_key, statistics, ttl=3600)
            
            return statistics
            
        except Exception as e:
            logger.error(f"获取HNR做种统计失败: {e}")
            return {
                "total_tasks": 0,
                "completed_tasks": 0,
                "average_ratio": 0.0,
                "average_seed_time_hours": 0.0,
                "completion_rate": 0.0
            }
    
    async def get_top_seeding_tasks(
        self,
        limit: int = 10,
        sort_by: str = "uploaded"
    ) -> List[Dict[str, Any]]:
        """
        获取顶级做种任务
        
        Args:
            limit: 限制数量（默认10）
            sort_by: 排序方式（uploaded, ratio, speed）
            
        Returns:
            顶级做种任务列表
        """
        try:
            # 这里需要从下载器获取实时数据
            # 简化实现：返回空列表
            # 实际应该调用SeedingService.get_seeding_tasks并排序
            return []
            
        except Exception as e:
            logger.error(f"获取顶级做种任务失败: {e}")
            return []

