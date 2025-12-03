"""
订阅刷新监控服务
用于记录和查询订阅刷新历史、监控刷新状态
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, update
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger

from app.models.subscription_refresh import SubscriptionRefreshHistory, SubscriptionRefreshStatus
from app.models.subscription import Subscription


class SubscriptionRefreshMonitor:
    """订阅刷新监控服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def start_refresh(
        self,
        subscription_id: int,
        subscription_title: Optional[str] = None,
        trigger_type: str = "auto",
        search_query: Optional[str] = None,
        search_sites: Optional[List[int]] = None
    ) -> SubscriptionRefreshHistory:
        """
        开始刷新记录
        
        Args:
            subscription_id: 订阅ID
            subscription_title: 订阅标题
            trigger_type: 触发类型（auto/manual/scheduled）
            search_query: 搜索查询
            search_sites: 搜索的站点列表
        
        Returns:
            SubscriptionRefreshHistory对象
        """
        try:
            # 如果没有提供标题，从数据库获取
            if not subscription_title:
                subscription = await self.db.get(Subscription, subscription_id)
                subscription_title = subscription.title if subscription else None
            
            # 创建刷新记录
            history = SubscriptionRefreshHistory(
                subscription_id=subscription_id,
                subscription_title=subscription_title,
                status="running",
                trigger_type=trigger_type,
                start_time=datetime.utcnow(),
                search_query=search_query,
                search_sites=search_sites
            )
            
            self.db.add(history)
            await self.db.flush()  # 获取ID
            
            # 更新状态表
            await self._update_status(
                subscription_id=subscription_id,
                status="running",
                current_refresh_id=history.id
            )
            
            await self.db.commit()
            await self.db.refresh(history)
            
            logger.info(f"开始刷新记录: 订阅ID={subscription_id}, 刷新ID={history.id}")
            return history
            
        except Exception as e:
            logger.error(f"创建刷新记录失败: {e}")
            await self.db.rollback()
            raise
    
    async def complete_refresh(
        self,
        refresh_id: int,
        status: str = "success",
        results_count: int = 0,
        downloaded_count: int = 0,
        skipped_count: int = 0,
        error_count: int = 0,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        search_duration_ms: Optional[int] = None,
        download_duration_ms: Optional[int] = None,
        matched_rules: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SubscriptionRefreshHistory:
        """
        完成刷新记录
        
        Args:
            refresh_id: 刷新记录ID
            status: 状态（success/failed/cancelled）
            results_count: 找到的结果数量
            downloaded_count: 下载的数量
            skipped_count: 跳过的数量
            error_count: 错误数量
            error_message: 错误信息
            error_details: 错误详情
            search_duration_ms: 搜索耗时
            download_duration_ms: 下载耗时
            matched_rules: 匹配的规则
            metadata: 其他元数据
        
        Returns:
            SubscriptionRefreshHistory对象
        """
        try:
            history = await self.db.get(SubscriptionRefreshHistory, refresh_id)
            if not history:
                raise ValueError(f"刷新记录不存在: {refresh_id}")
            
            # 更新记录
            history.status = status
            history.end_time = datetime.utcnow()
            history.results_count = results_count
            history.downloaded_count = downloaded_count
            history.skipped_count = skipped_count
            history.error_count = error_count
            history.error_message = error_message
            history.error_details = error_details
            history.search_duration_ms = search_duration_ms
            history.download_duration_ms = download_duration_ms
            history.matched_rules = matched_rules
            history.extra_metadata = metadata
            
            # 计算总耗时
            if history.start_time and history.end_time:
                duration = (history.end_time - history.start_time).total_seconds() * 1000
                history.duration_ms = int(duration)
                history.total_duration_ms = int(duration)
            
            await self.db.flush()
            
            # 更新状态表
            await self._update_status(
                subscription_id=history.subscription_id,
                status="idle" if status == "success" else "error",
                current_refresh_id=None,
                last_refresh_time=history.end_time,
                last_success_time=history.end_time if status == "success" else None,
                last_error_time=history.end_time if status == "failed" else None,
                success=status == "success",
                duration_ms=history.duration_ms
            )
            
            await self.db.commit()
            await self.db.refresh(history)
            
            logger.info(
                f"完成刷新记录: 刷新ID={refresh_id}, 状态={status}, "
                f"结果={results_count}, 下载={downloaded_count}, 耗时={history.duration_ms}ms"
            )
            
            return history
            
        except Exception as e:
            logger.error(f"完成刷新记录失败: {e}")
            await self.db.rollback()
            raise
    
    async def _update_status(
        self,
        subscription_id: int,
        status: str,
        current_refresh_id: Optional[int] = None,
        last_refresh_time: Optional[datetime] = None,
        next_refresh_time: Optional[datetime] = None,
        last_success_time: Optional[datetime] = None,
        last_error_time: Optional[datetime] = None,
        success: Optional[bool] = None,
        duration_ms: Optional[int] = None
    ):
        """更新状态表"""
        try:
            # 获取或创建状态记录
            status_record = await self.db.get(SubscriptionRefreshStatus, subscription_id)
            if not status_record:
                status_record = SubscriptionRefreshStatus(
                    subscription_id=subscription_id,
                    status="idle"
                )
                self.db.add(status_record)
            
            # 更新状态
            status_record.status = status
            if current_refresh_id is not None:
                status_record.current_refresh_id = current_refresh_id
            if last_refresh_time:
                status_record.last_refresh_time = last_refresh_time
            if next_refresh_time:
                status_record.next_refresh_time = next_refresh_time
            if last_success_time:
                status_record.last_success_time = last_success_time
            if last_error_time:
                status_record.last_error_time = last_error_time
            
            # 更新统计信息
            if success is not None:
                status_record.total_refreshes += 1
                if success:
                    status_record.total_successes += 1
                    status_record.consecutive_failures = 0
                else:
                    status_record.total_failures += 1
                    status_record.consecutive_failures += 1
                
                # 计算成功率
                if status_record.total_refreshes > 0:
                    status_record.success_rate = int(
                        (status_record.total_successes / status_record.total_refreshes) * 100
                    )
            
            # 更新平均耗时（简单移动平均）
            if duration_ms is not None:
                if status_record.avg_duration_ms is None:
                    status_record.avg_duration_ms = duration_ms
                else:
                    # 使用加权平均（新值权重0.3，旧值权重0.7）
                    status_record.avg_duration_ms = int(
                        status_record.avg_duration_ms * 0.7 + duration_ms * 0.3
                    )
            
            status_record.updated_at = datetime.utcnow()
            
            await self.db.flush()
            
        except Exception as e:
            logger.error(f"更新刷新状态失败: {e}")
            raise
    
    async def get_refresh_history(
        self,
        subscription_id: Optional[int] = None,
        status: Optional[str] = None,
        trigger_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SubscriptionRefreshHistory]:
        """
        获取刷新历史记录
        
        Args:
            subscription_id: 订阅ID过滤
            status: 状态过滤
            trigger_type: 触发类型过滤
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            刷新历史记录列表
        """
        try:
            query = select(SubscriptionRefreshHistory)
            
            conditions = []
            if subscription_id:
                conditions.append(SubscriptionRefreshHistory.subscription_id == subscription_id)
            if status:
                conditions.append(SubscriptionRefreshHistory.status == status)
            if trigger_type:
                conditions.append(SubscriptionRefreshHistory.trigger_type == trigger_type)
            if start_date:
                conditions.append(SubscriptionRefreshHistory.created_at >= start_date)
            if end_date:
                conditions.append(SubscriptionRefreshHistory.created_at <= end_date)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.order_by(desc(SubscriptionRefreshHistory.created_at))
            query = query.limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"获取刷新历史失败: {e}")
            raise
    
    async def get_refresh_status(
        self,
        subscription_id: Optional[int] = None
    ) -> List[SubscriptionRefreshStatus]:
        """
        获取刷新状态
        
        Args:
            subscription_id: 订阅ID（如果为None，返回所有状态）
        
        Returns:
            刷新状态列表
        """
        try:
            query = select(SubscriptionRefreshStatus)
            
            if subscription_id:
                query = query.where(SubscriptionRefreshStatus.subscription_id == subscription_id)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"获取刷新状态失败: {e}")
            raise
    
    async def get_refresh_statistics(
        self,
        subscription_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取刷新统计信息
        
        Args:
            subscription_id: 订阅ID过滤
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            统计信息字典
        """
        try:
            query = select(SubscriptionRefreshHistory)
            
            conditions = []
            if subscription_id:
                conditions.append(SubscriptionRefreshHistory.subscription_id == subscription_id)
            if start_date:
                conditions.append(SubscriptionRefreshHistory.created_at >= start_date)
            if end_date:
                conditions.append(SubscriptionRefreshHistory.created_at <= end_date)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            result = await self.db.execute(query)
            records = list(result.scalars().all())
            
            if not records:
                return {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "cancelled": 0,
                    "success_rate": 0.0,
                    "avg_duration_ms": 0,
                    "total_results": 0,
                    "total_downloaded": 0,
                    "by_status": {},
                    "by_trigger_type": {}
                }
            
            # 计算统计信息
            total = len(records)
            success_count = sum(1 for r in records if r.status == "success")
            failed_count = sum(1 for r in records if r.status == "failed")
            cancelled_count = sum(1 for r in records if r.status == "cancelled")
            success_rate = (success_count / total * 100) if total > 0 else 0.0
            
            # 平均耗时
            durations = [r.duration_ms for r in records if r.duration_ms is not None]
            avg_duration_ms = sum(durations) / len(durations) if durations else 0
            
            # 总结果和下载数
            total_results = sum(r.results_count for r in records)
            total_downloaded = sum(r.downloaded_count for r in records)
            
            # 按状态统计
            by_status = {}
            for record in records:
                status = record.status
                if status not in by_status:
                    by_status[status] = {"count": 0, "total_results": 0, "total_downloaded": 0}
                by_status[status]["count"] += 1
                by_status[status]["total_results"] += record.results_count
                by_status[status]["total_downloaded"] += record.downloaded_count
            
            # 按触发类型统计
            by_trigger_type = {}
            for record in records:
                trigger = record.trigger_type
                if trigger not in by_trigger_type:
                    by_trigger_type[trigger] = {"count": 0, "success": 0, "failed": 0}
                by_trigger_type[trigger]["count"] += 1
                if record.status == "success":
                    by_trigger_type[trigger]["success"] += 1
                elif record.status == "failed":
                    by_trigger_type[trigger]["failed"] += 1
            
            return {
                "total": total,
                "success": success_count,
                "failed": failed_count,
                "cancelled": cancelled_count,
                "success_rate": round(success_rate, 2),
                "avg_duration_ms": round(avg_duration_ms, 2),
                "total_results": total_results,
                "total_downloaded": total_downloaded,
                "by_status": by_status,
                "by_trigger_type": by_trigger_type
            }
            
        except Exception as e:
            logger.error(f"获取刷新统计失败: {e}")
            raise
    
    async def cleanup_old_history(self, days: int = 30) -> int:
        """
        清理旧的刷新历史记录
        
        Args:
            days: 保留最近N天的记录
        
        Returns:
            删除的记录数
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            from sqlalchemy import delete
            query = delete(SubscriptionRefreshHistory).where(
                SubscriptionRefreshHistory.created_at < cutoff_date
            )
            
            result = await self.db.execute(query)
            await self.db.commit()
            
            deleted_count = result.rowcount
            logger.info(f"清理了 {deleted_count} 条旧的刷新历史记录（保留最近 {days} 天）")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理刷新历史失败: {e}")
            await self.db.rollback()
            raise

