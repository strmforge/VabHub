"""
订阅刷新引擎
实现增量刷新和智能刷新策略
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.media_types import MEDIA_TYPE_MOVIE, is_tv_like
from app.models.subscription import Subscription


class SubscriptionRefreshEngine:
    """订阅刷新引擎"""
    
    def __init__(self, db: AsyncSession):
        """
        初始化刷新引擎
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    async def get_subscriptions_to_refresh(
        self,
        max_count: Optional[int] = None,
        priority: bool = True
    ) -> List[Subscription]:
        """
        获取需要刷新的订阅列表
        
        Args:
            max_count: 最大数量（None表示不限制）
            priority: 是否按优先级排序
            
        Returns:
            需要刷新的订阅列表
        """
        try:
            # 构建查询条件
            query = select(Subscription).where(
                Subscription.status == "active",
                Subscription.auto_download == True
            )
            
            # 根据刷新策略筛选订阅
            # 1. 从未搜索过的订阅
            # 2. 上次搜索时间超过刷新间隔的订阅
            # 3. 下次搜索时间已到的订阅
            
            now = datetime.utcnow()
            
            # 条件1: 从未搜索过（last_search为None）
            # 条件2: 下次搜索时间已到（next_search <= now）
            # 条件3: 上次搜索时间超过默认刷新间隔（last_search < now - 默认间隔）
            
            default_refresh_interval = timedelta(hours=6)  # 默认6小时刷新一次
            
            from sqlalchemy import or_
            
            # 构建刷新条件
            # 1. 从未搜索过（last_search IS NULL）
            # 2. 下次搜索时间已到或为空（next_search IS NULL OR next_search <= now）
            # 3. 上次搜索时间超过默认刷新间隔（last_search < now - 默认间隔）
            conditions = [
                Subscription.last_search.is_(None),  # 从未搜索过
                or_(
                    Subscription.next_search.is_(None),  # 下次搜索时间为空
                    Subscription.next_search <= now  # 下次搜索时间已到
                ),
                and_(
                    Subscription.last_search.isnot(None),
                    Subscription.last_search < now - default_refresh_interval
                )  # 上次搜索时间超过默认间隔
            ]
            
            # 使用OR组合条件
            query = query.where(or_(*conditions))
            
            # 按优先级排序
            if priority:
                # 优先级排序规则：
                # 1. 从未搜索过的优先
                # 2. 下次搜索时间最早的优先
                # 3. 创建时间最早的优先
                query = query.order_by(
                    Subscription.last_search.nulls_first(),  # 从未搜索过的优先
                    Subscription.next_search.asc(),  # 下次搜索时间最早的优先
                    Subscription.created_at.asc()  # 创建时间最早的优先
                )
            else:
                query = query.order_by(Subscription.created_at.desc())
            
            # 限制数量
            if max_count:
                query = query.limit(max_count)
            
            result = await self.db.execute(query)
            subscriptions = list(result.scalars().all())
            
            # Phase 8: Local Intel 感知 - 过滤被限流的站点订阅
            filtered_subscriptions = []
            skipped_count = 0
            
            try:
                from app.core.config import settings
                from app.modules.settings.service import SettingsService
                
                # 检查是否启用 Local Intel 订阅感知
                settings_service = SettingsService(self.db)
                intel_enabled = await settings_service.get_setting("intel_enabled", True)
                intel_subscription_respect_site_guard = await settings_service.get_setting(
                    "intel_subscription_respect_site_guard", True
                )
                
                if settings.INTEL_ENABLED and intel_enabled and intel_subscription_respect_site_guard:
                    from app.core.intel_local.scheduler_hooks import before_pt_scan
                    from app.models.intel_local import SiteGuardEvent as SiteGuardEventModel
                    from sqlalchemy import select, func
                    
                    # 检查每个订阅关联的站点是否被限流
                    for subscription in subscriptions:
                        subscription_sites = subscription.sites or []
                        if not subscription_sites:
                            # 没有指定站点，不过滤
                            filtered_subscriptions.append(subscription)
                            continue
                        
                        # 检查是否有站点被限流
                        all_sites_throttled = True
                        for site_name in subscription_sites:
                            try:
                                # 使用 Site Guard 检查站点状态
                                budget = await before_pt_scan(site_name)
                                if not budget.get("blocked", False):
                                    all_sites_throttled = False
                                    break
                            except Exception as e:
                                logger.debug(f"LocalIntel: 检查站点 {site_name} 状态失败: {e}，继续处理")
                                all_sites_throttled = False  # 检查失败时不过滤
                                break
                        
                        if all_sites_throttled:
                            skipped_count += 1
                            logger.info(
                                f"LocalIntel: 订阅 {subscription.title} (ID: {subscription.id}) "
                                f"关联的站点均被限流，跳过本次刷新"
                            )
                        else:
                            filtered_subscriptions.append(subscription)
                else:
                    # Local Intel 未启用或订阅感知未启用，不过滤
                    filtered_subscriptions = subscriptions
                    
            except Exception as e:
                logger.warning(f"LocalIntel: 订阅刷新时检查站点状态失败: {e}，不过滤订阅")
                filtered_subscriptions = subscriptions
            
            if skipped_count > 0:
                logger.info(f"LocalIntel: 共跳过 {skipped_count} 个被限流站点的订阅")
            
            logger.info(f"找到 {len(filtered_subscriptions)} 个需要刷新的订阅（共 {len(subscriptions)} 个，跳过 {skipped_count} 个）")
            return filtered_subscriptions
            
        except Exception as e:
            logger.error(f"获取需要刷新的订阅列表失败: {e}")
            return []
    
    async def should_refresh_subscription(
        self,
        subscription: Subscription,
        force: bool = False
    ) -> bool:
        """
        判断订阅是否需要刷新
        
        Args:
            subscription: 订阅对象
            force: 是否强制刷新
            
        Returns:
            是否需要刷新
        """
        if force:
            return True
        
        if subscription.status != "active":
            return False
        
        if not subscription.auto_download:
            return False
        
        now = datetime.utcnow()
        
        # 从未搜索过，需要刷新
        if subscription.last_search is None:
            return True
        
        # 下次搜索时间已到，需要刷新
        if subscription.next_search and subscription.next_search <= now:
            return True
        
        # 检查是否超过默认刷新间隔
        default_refresh_interval = timedelta(hours=6)
        if subscription.last_search < now - default_refresh_interval:
            return True
        
        return False
    
    def calculate_next_refresh_time(
        self,
        subscription: Subscription,
        refresh_interval_hours: Optional[int] = None
    ) -> datetime:
        """
        计算下次刷新时间
        
        Args:
            subscription: 订阅对象
            refresh_interval_hours: 刷新间隔（小时），如果为None则使用默认值
            
        Returns:
            下次刷新时间
        """
        now = datetime.utcnow()
        
        # 如果指定了刷新间隔，使用指定值
        if refresh_interval_hours:
            interval = timedelta(hours=refresh_interval_hours)
        else:
            # 根据订阅类型和状态确定刷新间隔
            interval = self._get_refresh_interval(subscription)
        
        # 如果订阅从未搜索过，立即刷新（5分钟后，给系统一些时间）
        if subscription.last_search is None:
            return now + timedelta(minutes=5)
        
        # 如果有next_search时间，优先使用它
        if subscription.next_search and subscription.next_search > now:
            return subscription.next_search
        
        # 计算下次刷新时间（基于上次搜索时间）
        next_refresh = subscription.last_search + interval
        
        # 确保下次刷新时间不早于现在
        if next_refresh < now:
            next_refresh = now + timedelta(minutes=5)  # 至少5分钟后
        
        return next_refresh
    
    def _get_refresh_interval(self, subscription: Subscription) -> timedelta:
        """
        根据订阅类型和状态获取刷新间隔
        
        Args:
            subscription: 订阅对象
            
        Returns:
            刷新间隔
        """
        # 默认刷新间隔：6小时
        default_interval = timedelta(hours=6)
        
        # 根据媒体类型调整刷新间隔
        if is_tv_like(subscription.media_type):
            # 电视剧：更频繁刷新（3小时），因为新集发布更频繁
            return timedelta(hours=3)
        elif subscription.media_type == MEDIA_TYPE_MOVIE:
            # 电影：较频繁刷新（6小时）
            return timedelta(hours=6)
        else:
            # 其他类型：使用默认间隔
            return default_interval
    
    async def refresh_subscription(
        self,
        subscription_id: int,
        force: bool = False,
        trigger_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        刷新单个订阅（带状态监控和历史记录）
        
        Args:
            subscription_id: 订阅ID
            force: 是否强制刷新
            trigger_type: 触发类型（auto/manual/scheduled）
        
        Returns:
            刷新结果
        """
        from app.modules.subscription.service import SubscriptionService
        from app.modules.subscription.refresh_monitor import SubscriptionRefreshMonitor
        import time
        
        monitor = SubscriptionRefreshMonitor(self.db)
        refresh_history = None
        start_time = time.time()
        
        try:
            subscription_service = SubscriptionService(self.db)
            
            # 获取订阅
            subscription = await subscription_service.get_subscription(subscription_id)
            if not subscription:
                return {
                    "success": False,
                    "error": "订阅不存在"
                }
            
            # 检查是否需要刷新
            if not force and not await self.should_refresh_subscription(subscription):
                return {
                    "success": False,
                    "error": "订阅无需刷新",
                    "next_refresh_time": subscription.next_search.isoformat() if subscription.next_search else None
                }
            
            # 开始刷新记录
            refresh_history = await monitor.start_refresh(
                subscription_id=subscription_id,
                subscription_title=subscription.title,
                trigger_type=trigger_type
            )
            
            search_start_time = time.time()
            
            # 执行搜索（execute_search内部已经更新了last_search和next_search）
            search_result = await subscription_service.execute_search(subscription_id)
            
            search_duration_ms = int((time.time() - search_start_time) * 1000)
            
            # 重新获取订阅以获取最新的刷新时间
            updated_subscription = await subscription_service.get_subscription(subscription_id)
            
            if not updated_subscription:
                logger.warning(f"刷新订阅后无法获取订阅信息: {subscription_id}")
                # 记录失败
                await monitor.complete_refresh(
                    refresh_id=refresh_history.id,
                    status="failed",
                    error_message="刷新后无法获取订阅信息",
                    search_duration_ms=search_duration_ms
                )
                return {
                    "success": True,
                    "subscription_id": subscription_id,
                    "subscription_title": subscription.title,
                    "search_result": search_result,
                    "last_search": None,
                    "next_search": None
                }
            
            # 判断刷新是否成功
            refresh_status = "success"
            error_message = None
            if search_result.get("error"):
                refresh_status = "failed"
                error_message = search_result.get("error")
            
            # 完成刷新记录
            await monitor.complete_refresh(
                refresh_id=refresh_history.id,
                status=refresh_status,
                results_count=search_result.get("results_count", 0),
                downloaded_count=search_result.get("downloaded_count", 0),
                skipped_count=search_result.get("skipped_count", 0),
                error_count=search_result.get("error_count", 0),
                error_message=error_message,
                search_duration_ms=search_duration_ms,
                matched_rules=search_result.get("matched_rules")
            )
            
            logger.info(
                f"订阅刷新完成: {updated_subscription.title} (ID: {subscription_id}), "
                f"找到 {search_result.get('results_count', 0)} 个结果, "
                f"下载 {search_result.get('downloaded_count', 0)} 个"
            )
            
            return {
                "success": True,
                "subscription_id": subscription_id,
                "subscription_title": updated_subscription.title,
                "refresh_id": refresh_history.id,
                "search_result": search_result,
                "last_search": updated_subscription.last_search.isoformat() if updated_subscription.last_search else None,
                "next_search": updated_subscription.next_search.isoformat() if updated_subscription.next_search else None
            }
            
        except Exception as e:
            logger.error(f"刷新订阅失败: {subscription_id}, 错误: {e}")
            
            # 如果已创建刷新记录，标记为失败
            if refresh_history:
                try:
                    await monitor.complete_refresh(
                        refresh_id=refresh_history.id,
                        status="failed",
                        error_message=str(e),
                        error_details={"exception_type": type(e).__name__}
                    )
                except Exception as e2:
                    logger.error(f"记录刷新失败状态时出错: {e2}")
            
            await self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def refresh_subscriptions_batch(
        self,
        max_count: Optional[int] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        批量刷新订阅
        
        Args:
            max_count: 最大刷新数量（None表示不限制）
            force: 是否强制刷新
            
        Returns:
            批量刷新结果
        """
        try:
            # 获取需要刷新的订阅列表
            subscriptions = await self.get_subscriptions_to_refresh(max_count=max_count)
            
            if not subscriptions:
                return {
                    "success": True,
                    "refreshed_count": 0,
                    "total_count": 0,
                    "results": []
                }
            
            results = []
            success_count = 0
            error_count = 0
            
            # 逐个刷新订阅
            for subscription in subscriptions:
                try:
                    result = await self.refresh_subscription(
                        subscription.id,
                        force=force
                    )
                    results.append(result)
                    
                    if result.get("success"):
                        success_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"刷新订阅失败: {subscription.id}, 错误: {e}")
                    error_count += 1
                    results.append({
                        "success": False,
                        "subscription_id": subscription.id,
                        "error": str(e)
                    })
            
            logger.info(
                f"批量刷新完成: 总计 {len(subscriptions)} 个订阅, "
                f"成功 {success_count} 个, 失败 {error_count} 个"
            )
            
            return {
                "success": True,
                "refreshed_count": success_count,
                "error_count": error_count,
                "total_count": len(subscriptions),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"批量刷新订阅失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "refreshed_count": 0,
                "total_count": 0,
                "results": []
            }
    
    async def update_refresh_schedule(
        self,
        subscription_id: int,
        refresh_interval_hours: Optional[int] = None
    ) -> bool:
        """
        更新订阅的刷新计划
        
        Args:
            subscription_id: 订阅ID
            refresh_interval_hours: 刷新间隔（小时）
            
        Returns:
            是否成功
        """
        try:
            from app.modules.subscription.service import SubscriptionService
            
            subscription_service = SubscriptionService(self.db)
            subscription = await subscription_service.get_subscription(subscription_id)
            
            if not subscription:
                return False
            
            # 计算下次刷新时间
            subscription.next_search = self.calculate_next_refresh_time(
                subscription,
                refresh_interval_hours
            )
            
            await self.db.commit()
            await self.db.refresh(subscription)
            
            logger.info(
                f"更新订阅刷新计划: {subscription.title} (ID: {subscription_id}), "
                f"下次刷新时间: {subscription.next_search}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"更新订阅刷新计划失败: {subscription_id}, 错误: {e}")
            await self.db.rollback()
            return False

