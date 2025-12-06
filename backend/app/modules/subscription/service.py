"""
订阅服务
"""

from copy import deepcopy
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from loguru import logger
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.media_types import (
    MEDIA_TYPE_CHOICES,
    MEDIA_TYPE_MOVIE,
    MEDIA_TYPE_SHORT_DRAMA,
    is_tv_like,
    normalize_media_type,
)
from app.core.cache import get_cache
from app.models.download import DownloadTask
from app.models.subscription import Subscription
from app.models.subscription_history import SubscriptionHistory
from app.modules.filter_rule_group.service import FilterRuleGroupService
from app.modules.music import query_builder as music_query_builder
from app.modules.subscription.rule_engine import RuleEngine
from app.modules.decision import (
    DecisionCandidate,
    DecisionContext,
    DecisionExistingItem,
    DecisionSubscriptionInfo,
    get_decision_service,
)


class SubscriptionService:
    """订阅服务"""

    SHORT_DRAMA_META_FIELDS = (
        "episode_duration",
        "duration_unit",
        "total_episodes",
        "format_tag",
        "source_category",
    )

    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache = get_cache()  # 使用统一缓存系统
        self.rule_engine = RuleEngine()  # 规则引擎
        self.decision_service = get_decision_service()
        self.filter_rule_group_service = FilterRuleGroupService(db)  # 过滤规则组服务
    
    async def create_subscription(self, subscription: dict) -> Subscription:
        """创建订阅"""
        # 创建订阅对象
        normalized_media_type = normalize_media_type(
            subscription.get("media_type"),
            default=subscription.get("media_type") or MEDIA_TYPE_MOVIE,
        )

        # 确保 user_id 存在（CI/测试环境下使用默认值 1）
        user_id = subscription.get("user_id") or 1

        new_subscription = Subscription(
            user_id=user_id,
            title=subscription.get("title"),
            original_title=subscription.get("original_title"),
            year=subscription.get("year"),
            media_type=normalized_media_type,
            tmdb_id=subscription.get("tmdb_id"),
            tvdb_id=subscription.get("tvdb_id"),
            imdb_id=subscription.get("imdb_id"),
            poster=subscription.get("poster"),
            backdrop=subscription.get("backdrop"),
            # 电视剧相关
            season=subscription.get("season"),
            total_episode=subscription.get("total_episode"),
            start_episode=subscription.get("start_episode"),
            episode_group=subscription.get("episode_group"),
            # 基础规则
            quality=subscription.get("quality"),
            resolution=subscription.get("resolution"),
            effect=subscription.get("effect"),
            sites=subscription.get("sites"),
            downloader=subscription.get("downloader"),
            save_path=subscription.get("save_path"),
            min_seeders=subscription.get("min_seeders", 5),
            auto_download=subscription.get("auto_download", True),
            best_version=subscription.get("best_version", False),
            search_imdbid=subscription.get("search_imdbid", False),
            # 进阶规则
            include=subscription.get("include"),
            exclude=subscription.get("exclude"),
            filter_group_ids=subscription.get("filter_group_ids", []),
            # 其他
            search_rules=subscription.get("search_rules"),
            extra_metadata=self._build_extra_metadata(subscription),
            status="active"
        )
        
        # 初始化刷新时间（如果是新订阅且启用自动下载，立即刷新）
        if new_subscription.auto_download:
            # 从未搜索过，设置下次搜索时间为现在（立即刷新）
            new_subscription.last_search = None
            new_subscription.next_search = datetime.utcnow()
        else:
            # 如果未启用自动下载，设置一个较晚的刷新时间
            new_subscription.last_search = None
            new_subscription.next_search = datetime.utcnow() + timedelta(days=1)
        
        self.db.add(new_subscription)
        await self.db.commit()
        await self.db.refresh(new_subscription)
        
        # 记录创建历史
        await self._record_history(
            subscription_id=new_subscription.id,
            action="create",
            action_type="operation",
            description=f"创建订阅: {new_subscription.title}",
            new_value={
                "title": new_subscription.title,
                "media_type": new_subscription.media_type,
                "status": new_subscription.status
            }
        )
        
        # 使订阅列表缓存失效
        await self._invalidate_subscription_cache()
        
        return new_subscription
    
    async def list_subscriptions(
        self,
        media_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Subscription]:
        """获取订阅列表（带缓存）"""
        # 生成缓存键
        cache_key = f"subscriptions:list:{media_type or 'all'}:{status or 'all'}"
        
        # 尝试从缓存获取（10秒TTL，订阅列表变化不频繁但需要及时更新）
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"订阅列表缓存命中: {media_type}, {status}")
            return cached_result
        
        query = select(Subscription)
        
        # 应用过滤条件
        if media_type:
            query = query.where(Subscription.media_type == media_type)
        if status:
            query = query.where(Subscription.status == status)
        
        # 按创建时间倒序
        query = query.order_by(Subscription.created_at.desc())
        
        result = await self.db.execute(query)
        subscriptions = list(result.scalars().all())
        
        # 缓存结果（10秒）
        await self.cache.set(cache_key, subscriptions, ttl=10)
        
        return subscriptions
    
    async def _invalidate_subscription_cache(self):
        """使订阅列表缓存失效"""
        # 清除所有订阅列表相关的缓存
        cache_keys = []
        for media in ["all", *sorted(MEDIA_TYPE_CHOICES)]:
            cache_keys.append(f"subscriptions:list:{media}:all")
            cache_keys.append(f"subscriptions:list:{media}:active")
            cache_keys.append(f"subscriptions:list:{media}:inactive")
        for key in cache_keys:
            await self.cache.delete(key)
    
    async def get_subscription(self, subscription_id: int) -> Optional[Subscription]:
        """获取订阅详情"""
        result = await self.db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        return result.scalar_one_or_none()
    
    async def update_subscription(
        self, 
        subscription_id: int, 
        subscription: dict
    ) -> Optional[Subscription]:
        """更新订阅"""
        # 查找订阅
        existing = await self.get_subscription(subscription_id)
        if not existing:
            return None
        
        # 更新字段
        if "title" in subscription:
            existing.title = subscription["title"]
        if "original_title" in subscription:
            existing.original_title = subscription.get("original_title")
        if "year" in subscription:
            existing.year = subscription.get("year")
        if "media_type" in subscription:
            existing.media_type = normalize_media_type(
                subscription["media_type"],
                default=existing.media_type or MEDIA_TYPE_MOVIE,
            )
        if "tmdb_id" in subscription:
            existing.tmdb_id = subscription.get("tmdb_id")
        if "tvdb_id" in subscription:
            existing.tvdb_id = subscription.get("tvdb_id")
        if "imdb_id" in subscription:
            existing.imdb_id = subscription.get("imdb_id")
        if "poster" in subscription:
            existing.poster = subscription.get("poster")
        if "backdrop" in subscription:
            existing.backdrop = subscription.get("backdrop")
        if "season" in subscription:
            existing.season = subscription.get("season")
        if "total_episode" in subscription:
            existing.total_episode = subscription.get("total_episode")
        if "start_episode" in subscription:
            existing.start_episode = subscription.get("start_episode")
        if "episode_group" in subscription:
            existing.episode_group = subscription.get("episode_group")
        # 基础规则
        if "quality" in subscription:
            existing.quality = subscription.get("quality")
        if "resolution" in subscription:
            existing.resolution = subscription.get("resolution")
        if "effect" in subscription:
            existing.effect = subscription.get("effect")
        if "sites" in subscription:
            existing.sites = subscription.get("sites")
        if "downloader" in subscription:
            existing.downloader = subscription.get("downloader")
        if "save_path" in subscription:
            existing.save_path = subscription.get("save_path")
        if "min_seeders" in subscription:
            existing.min_seeders = subscription.get("min_seeders", 5)
        if "auto_download" in subscription:
            existing.auto_download = subscription.get("auto_download", True)
        if "best_version" in subscription:
            existing.best_version = subscription.get("best_version", False)
        if "search_imdbid" in subscription:
            existing.search_imdbid = subscription.get("search_imdbid", False)
        # 进阶规则
        if "include" in subscription:
            existing.include = subscription.get("include")
        if "exclude" in subscription:
            existing.exclude = subscription.get("exclude")
        if "filter_groups" in subscription:
            existing.filter_groups = subscription.get("filter_groups")
        # 其他
        if "search_rules" in subscription:
            existing.search_rules = subscription.get("search_rules")
        if (
            "extra_metadata" in subscription
            or "short_drama_metadata" in subscription
        ):
            existing.extra_metadata = self._build_extra_metadata(
                subscription,
                base=existing.extra_metadata,
            )
        
        # 记录变更历史
        old_value = {
            "title": existing.title,
            "status": existing.status,
            "quality": existing.quality,
            "resolution": existing.resolution,
            "auto_download": existing.auto_download
        }
        
        existing.updated_at = datetime.utcnow()
        
        self.db.add(existing)
        await self.db.commit()
        await self.db.refresh(existing)
        
        # 记录更新历史
        new_value = {
            "title": existing.title,
            "status": existing.status,
            "quality": existing.quality,
            "resolution": existing.resolution,
            "auto_download": existing.auto_download
        }
        
        await self._record_history(
            subscription_id=subscription_id,
            action="update",
            action_type="operation",
            description=f"更新订阅: {existing.title}",
            old_value=old_value,
            new_value=new_value
        )
        
        return existing
    
    async def delete_subscription(self, subscription_id: int) -> bool:
        """删除订阅"""
        # 先获取订阅信息用于历史记录
        subscription = await self.get_subscription(subscription_id)
        if not subscription:
            return False
        
        # 记录删除历史
        await self._record_history(
            subscription_id=subscription_id,
            action="delete",
            action_type="operation",
            description=f"删除订阅: {subscription.title}",
            old_value={
                "title": subscription.title,
                "media_type": subscription.media_type,
                "status": subscription.status
            }
        )
        
        result = await self.db.execute(
            delete(Subscription).where(Subscription.id == subscription_id)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def enable_subscription(self, subscription_id: int) -> Optional[Subscription]:
        """启用订阅"""
        subscription = await self.get_subscription(subscription_id)
        if not subscription:
            return None
        
        old_status = subscription.status
        subscription.status = "active"
        subscription.updated_at = datetime.utcnow()
        
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        
        # 记录启用历史
        await self._record_history(
            subscription_id=subscription_id,
            action="enable",
            action_type="operation",
            description=f"启用订阅: {subscription.title}",
            old_value={"status": old_status},
            new_value={"status": "active"}
        )
        
        return subscription
    
    async def disable_subscription(self, subscription_id: int) -> Optional[Subscription]:
        """禁用订阅"""
        subscription = await self.get_subscription(subscription_id)
        if not subscription:
            return None
        
        old_status = subscription.status
        subscription.status = "paused"
        subscription.updated_at = datetime.utcnow()
        
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        
        # 记录禁用历史
        await self._record_history(
            subscription_id=subscription_id,
            action="disable",
            action_type="operation",
            description=f"禁用订阅: {subscription.title}",
            old_value={"status": old_status},
            new_value={"status": "paused"}
        )
        
        return subscription
    
    async def execute_search(self, subscription_id: int, *, auto_download_override: Optional[bool] = None) -> Dict:
        """执行订阅搜索"""
        from app.modules.search.service import SearchService
        from app.modules.download.service import DownloadService
        from loguru import logger
        
        subscription = await self.get_subscription(subscription_id)
        if not subscription:
            return {
                "success": False,
                "message": "订阅不存在"
            }
        
        if subscription.status != "active":
            return {
                "success": False,
                "message": f"订阅状态为 {subscription.status}，无法执行搜索"
            }
        
        try:
            search_service = SearchService(self.db)
            download_service = DownloadService(self.db)
            
            preview_keywords: List[str] = []
            if subscription.media_type == "music":
                search_params, preview_keywords = music_query_builder.build_music_search_params(subscription)
                search_query = search_params.get("query", subscription.title)
            else:
                # 构建搜索查询
                search_query = subscription.title
                if subscription.year:
                    search_query += f" {subscription.year}"
                
                # 如果是电视剧，添加季数信息
                if is_tv_like(subscription.media_type) and subscription.season:
                    search_query += f" S{subscription.season:02d}"
                
                # 构建搜索参数
                search_params = {
                    "query": search_query,
                    "media_type": subscription.media_type,
                    "quality": subscription.quality,
                    "resolution": subscription.resolution,
                    "min_seeders": subscription.min_seeders or 5,
                }
                
                if subscription.year:
                    search_params["year"] = subscription.year
                if subscription.include:
                    search_params["include"] = subscription.include
                if subscription.exclude:
                    search_params["exclude"] = subscription.exclude
                if subscription.sites:
                    search_params["sites"] = subscription.sites
                preview_keywords = [search_query]
            
            # 执行搜索（Phase 9: 优先使用索引搜索）
            logger.info(f"执行订阅搜索: {subscription.title} (ID: {subscription_id})")
            
            # Phase 9: 如果启用 Local Intel，优先使用 IndexedSearchService
            from app.core.config import settings
            search_results = []
            
            if settings.INTEL_ENABLED:
                try:
                    from app.modules.search.indexed_search_service import IndexedSearchService
                    from app.schemas.search import SearchQuery as IndexedSearchQuery
                    
                    indexed_service = IndexedSearchService(self.db, fallback_service=search_service)
                    indexed_query = IndexedSearchQuery(
                        keyword=search_query,
                        category=subscription.media_type,
                        site_ids=subscription.sites,
                        hr_filter="any",  # 订阅选种不过滤 HR，由决策层处理
                        min_seeders=search_params.get("min_seeders"),
                        max_seeders=search_params.get("max_seeders"),
                        min_size_gb=search_params.get("min_size"),
                        max_size_gb=search_params.get("max_size"),
                        sort="seeders",
                        limit=100,  # 订阅搜索限制100条
                    )
                    
                    indexed_results = await indexed_service.search(indexed_query)
                    
                    # 转换为原有格式
                    for item in indexed_results:
                        search_results.append({
                            "title": item.title_raw,
                            "site": item.site_id,
                            "site_id": item.site_id,
                            "torrent_id": item.torrent_id,
                            "size_gb": item.size_gb or 0,
                            "seeders": item.seeders,
                            "leechers": item.leechers,
                            "upload_date": item.published_at,
                            "category": item.category,
                            "is_hr": item.is_hr,
                            "is_free": item.is_free,
                            "is_half_free": item.is_half_free,
                            "magnet_link": item.magnet_link,
                            "torrent_url": item.torrent_url,
                        })
                    
                    logger.info(f"订阅搜索: 从索引找到 {len(search_results)} 条结果")
                except Exception as e:
                    logger.warning(f"订阅搜索: 索引搜索失败，回退到原有搜索: {e}")
            
            # 如果索引搜索无结果或失败，使用原有搜索
            if not search_results:
                search_results = await search_service.search(**search_params)
            
            # 根据订阅规则过滤结果
            if subscription.media_type == "music":
                filtered_results = search_results
            else:
                filtered_results = await self._filter_search_results(search_results, subscription)
            
            # 应用全局规则过滤（在订阅规则之后，决策评估之前）
            try:
                from app.modules.global_rules import GlobalRulesService
                global_rules_service = GlobalRulesService(self.db)
                pre_global_rules_count = len(filtered_results)
                filtered_results = await global_rules_service.filter_torrents(filtered_results)
                logger.info(f"订阅全局规则过滤: {pre_global_rules_count} -> {len(filtered_results)}")
            except Exception as e:
                logger.warning(f"订阅全局规则过滤失败，使用订阅过滤结果: {e}")
                # 降级处理：继续使用订阅过滤结果
            
            # 如果启用自动下载，选择最佳结果并下载
            downloaded_count = 0
            download_result = None
            auto_download_enabled = subscription.auto_download if auto_download_override is None else auto_download_override
            if auto_download_enabled and filtered_results:
                # 选择最佳结果
                best_result = self._select_best_result(filtered_results, subscription)
                
                if best_result:
                    decision_result = await self.evaluate_candidate_with_decision(subscription, best_result)
                    decision_allowed = True
                    if decision_result:
                        decision_allowed = decision_result.should_download
                        logger.debug(
                            "[decision] 自动下载评估 -> %s (%s)",
                            decision_result.reason.value,
                            decision_result.message,
                        )
                        if not decision_allowed:
                            download_result = {
                                "skipped": True,
                                "decision_reason": decision_result.reason.value,
                                "decision_message": decision_result.message,
                            }
                            logger.info(
                                "订阅 %s(%s) 因决策结果被跳过: %s",
                                subscription.title,
                                subscription.id,
                                decision_result.reason.value,
                            )
                    else:
                        decision_allowed = True

                    try:
                        if decision_allowed:
                            # Phase 8: Local Intel 感知 - 检查 HR 风险
                            try:
                                from app.core.config import settings
                                from app.modules.settings.service import SettingsService
                                
                                settings_service = SettingsService(self.db)
                                intel_enabled = await settings_service.get_setting("intel_enabled", True)
                                intel_subscription_respect_site_guard = await settings_service.get_setting(
                                    "intel_subscription_respect_site_guard", True
                                )
                                
                                if settings.INTEL_ENABLED and intel_enabled and intel_subscription_respect_site_guard:
                                    from app.core.intel_local.repo import SqlAlchemyHRCasesRepository
                                    from app.core.intel_local.models import HRStatus
                                    from app.core.database import AsyncSessionLocal
                                    from datetime import datetime
                                    
                                    # 获取种子的站点和ID
                                    site_id = best_result.get("site") or best_result.get("site_id")
                                    torrent_id = best_result.get("torrent_id") or best_result.get("id")
                                    
                                    if site_id and torrent_id:
                                        # 检查是否有高风险 HR 记录
                                        hr_repo = SqlAlchemyHRCasesRepository(AsyncSessionLocal)
                                        has_hr_risk = False
                                        hr_risk_message = None
                                        
                                        async for hr_case in hr_repo.list_active_for_site(site_id):  # type: ignore[attr-defined]
                                            if hr_case.torrent_id == str(torrent_id):
                                                if hr_case.hr_status in (HRStatus.ACTIVE, HRStatus.UNKNOWN):
                                                    # 检查是否高风险
                                                    now = datetime.utcnow()
                                                    if hr_case.deadline:
                                                        remaining_hours = (hr_case.deadline - now).total_seconds() / 3600
                                                        if remaining_hours < 24:
                                                            has_hr_risk = True
                                                            hr_risk_message = (
                                                                f"该种子存在 HR 风险（剩余时间: {remaining_hours:.1f} 小时）"
                                                            )
                                                    elif not hr_case.seeded_hours or (
                                                        hr_case.required_seed_hours
                                                        and hr_case.seeded_hours < hr_case.required_seed_hours
                                                    ):
                                                        has_hr_risk = True
                                                        hr_risk_message = "该种子存在 HR 风险（未满足保种要求）"
                                                
                                                break
                                        
                                        if has_hr_risk:
                                            logger.warning(
                                                f"LocalIntel: 订阅 {subscription.title} (ID: {subscription_id}) "
                                                f"选择的种子 {best_result.get('title')} 存在 HR 风险: {hr_risk_message}"
                                            )
                            except Exception as e:
                                logger.debug(f"LocalIntel: 检查 HR 风险失败: {e}，继续下载")
                            
                            # 创建下载任务
                            download_data = {
                                "title": best_result.get("title", subscription.title),
                                "magnet_link": best_result.get("magnet_link") or best_result.get("magnetLink"),
                                "torrent_url": best_result.get("torrent_url") or best_result.get("torrentUrl"),
                                "size_gb": best_result.get("size_gb") or best_result.get("sizeGb", 0),
                                "downloader": subscription.downloader or "qBittorrent",
                                "save_path": subscription.save_path,
                                "media_type": subscription.media_type,
                                "extra_metadata": subscription.extra_metadata,
                            }
                            if decision_result:
                                download_data["extra_metadata"] = download_data.get("extra_metadata") or {}
                                download_data["extra_metadata"].setdefault("decision", {})
                                download_data["extra_metadata"]["decision"] = {
                                    "reason": decision_result.reason.value,
                                    "score": decision_result.score,
                                }
                            
                            # 确保 extra_metadata 包含站点和种子ID（用于后续 HR 保护）
                            if not download_data.get("extra_metadata"):
                                download_data["extra_metadata"] = {}
                            download_data["extra_metadata"]["site_id"] = best_result.get("site") or best_result.get("site_id")
                            download_data["extra_metadata"]["torrent_id"] = best_result.get("torrent_id") or best_result.get("id")
                            download_data["extra_metadata"]["user_id"] = subscription.user_id  # P2: 添加用户ID到元数据
                            
                            download_result = await download_service.create_download(download_data)
                            downloaded_count = 1
                            logger.info(f"订阅自动下载成功: {subscription.title} -> {best_result.get('title')}")
                            
                            # P2: 发送订阅命中通知
                            try:
                                from app.services.notification_service import notify_download_subscription_matched_for_user
                                from app.schemas.notification_download import DownloadSubscriptionMatchedPayload
                                
                                # 构建通知 payload
                                notification_payload = DownloadSubscriptionMatchedPayload(
                                    title=best_result.get("title", subscription.title),
                                    site_name=best_result.get("site") or best_result.get("site_id"),
                                    category_label=subscription.media_type,
                                    resolution=subscription.resolution,
                                    source_label="订阅引擎",
                                    route_name="download-tasks",
                                    route_params={"task_id": download_result.get("task_id")},
                                    subscription_id=subscription.id,
                                    subscription_name=subscription.title,
                                    torrent_id=best_result.get("torrent_id") or best_result.get("id"),
                                    rule_labels=[subscription.media_type, subscription.quality or "any"] if subscription.quality else [subscription.media_type]
                                ).dict()
                                
                                await notify_download_subscription_matched_for_user(
                                    session=self.db,
                                    user_id=subscription.user_id,
                                    payload=notification_payload
                                )
                                
                                logger.info(f"订阅命中通知已发送: 用户={subscription.user_id}, 订阅={subscription.title}")
                            except Exception as e:
                                logger.warning(f"发送订阅命中通知失败: {e}")
                                # 通知失败不影响下载流程
                    except Exception as e:
                        logger.error(f"订阅自动下载失败: {subscription.title} - {e}")
            
            # 更新订阅的最后搜索时间和下次搜索时间
            subscription.last_search = datetime.utcnow()
            # 使用刷新引擎计算下次搜索时间（根据订阅类型智能计算）
            from app.modules.subscription.refresh_engine import SubscriptionRefreshEngine
            refresh_engine = SubscriptionRefreshEngine(self.db)
            subscription.next_search = refresh_engine.calculate_next_refresh_time(subscription)
            
            self.db.add(subscription)
            await self.db.commit()
            
            # 记录搜索历史
            await self._record_history(
                subscription_id=subscription_id,
                action="search",
                action_type="search",
                description=f"执行订阅搜索: {subscription.title}",
                search_query=search_query,
                search_results_count=len(filtered_results),
                search_params={
                    **search_params,
                    "preview_keywords": preview_keywords
                },
                status="success" if filtered_results else "failed"
            )
            
            # 如果有下载，记录下载历史
            if downloaded_count > 0 and download_result:
                await self._record_history(
                    subscription_id=subscription_id,
                    action="download",
                    action_type="download",
                    description=f"自动下载: {download_result.get('title', 'Unknown')}",
                    download_task_id=str(download_result.get('task_id', '')),
                    download_title=download_result.get('title'),
                    download_size_gb=download_result.get('size_gb'),
                    status="success"
                )
            
            return {
                "success": True,
                "message": "搜索完成",
                "subscription_id": subscription_id,
                "subscription_title": subscription.title,
                "results_count": len(search_results),
                "filtered_count": len(filtered_results),
                "downloaded_count": downloaded_count,
                "download_result": download_result
            }
        except Exception as e:
            logger.error(f"订阅搜索执行失败: {subscription.title} (ID: {subscription_id}) - {e}")
            return {
                "success": False,
                "message": f"搜索失败: {str(e)}",
                "subscription_id": subscription_id
            }

    def _normalize_short_drama_metadata(self, payload: Dict) -> Optional[Dict]:
        """抽取短剧相关元数据，确保键一致。"""
        raw_meta = payload.get("short_drama_metadata") or payload.get("short_drama_meta")
        if not raw_meta:
            return None

        normalized = {
            "episode_duration": raw_meta.get("episode_duration")
            or raw_meta.get("episode_duration_minutes")
            or raw_meta.get("episode_duration_min"),
            "duration_unit": raw_meta.get("duration_unit") or "minute",
            "total_episodes": raw_meta.get("total_episodes") or raw_meta.get("episodes"),
            "format_tag": raw_meta.get("format_tag") or raw_meta.get("category"),
            "source_category": raw_meta.get("source_category"),
        }

        return {k: v for k, v in normalized.items() if v not in (None, "", [])} or None

    def _build_extra_metadata(
        self,
        payload: Dict,
        *,
        base: Optional[Dict] = None,
    ) -> Optional[Dict]:
        """组合 extra_metadata，并在短剧场景下补充专属字段。"""
        extra_metadata = deepcopy(base) if base else {}

        incoming_extra = payload.get("extra_metadata")
        if incoming_extra:
            extra_metadata.update(incoming_extra)

        normalized_type = normalize_media_type(payload.get("media_type"))
        if normalized_type == MEDIA_TYPE_SHORT_DRAMA:
            short_metadata = self._normalize_short_drama_metadata(payload) or {}
            merged_short_meta = {
                **(extra_metadata.get("short_drama") or {}),
                **short_metadata,
            }
            if merged_short_meta:
                extra_metadata["short_drama"] = merged_short_meta

        return extra_metadata or None

    async def evaluate_candidate_with_decision(
        self,
        subscription: Subscription,
        candidate: dict,
        *,
        debug: bool = False,
    ):
        """调用下载决策层，返回 DecisionResult 或 None（表示回退旧逻辑）。"""
        try:
            decision_candidate = self._build_decision_candidate(subscription, candidate)
            decision_context = await self._build_decision_context(
                subscription,
                debug=debug,
            )
            result = await self.decision_service.decide_download(
                decision_candidate,
                decision_context,
            )
            logger.info(
                "[decision] 订阅 %s(%s) 候选《%s》 -> %s: %s",
                subscription.title,
                subscription.id,
                decision_candidate.title,
                result.reason.value,
                result.message,
            )
            return result
        except Exception as exc:  # pragma: no cover - 决策层异常回退
            logger.warning(
                "[decision] 订阅 %s(%s) 调用决策层失败，使用旧逻辑: %s",
                subscription.title,
                subscription.id,
                exc,
            )
            return None

    def _build_decision_candidate(
        self,
        subscription: Subscription,
        candidate: dict,
    ) -> DecisionCandidate:
        """将搜索结果转换为决策候选。"""
        torrent_hash = candidate.get("hash") or candidate.get("torrent_hash")
        return DecisionCandidate(
            id=str(candidate.get("id") or torrent_hash or subscription.id),
            title=candidate.get("title") or subscription.title,
            subtitle=candidate.get("subtitle"),
            description=candidate.get("description"),
            media_type=subscription.media_type,
            quality=candidate.get("quality"),
            resolution=candidate.get("resolution"),
            effect=candidate.get("effect"),
            size_gb=candidate.get("size_gb") or candidate.get("sizeGb"),
            seeders=candidate.get("seeders") or candidate.get("peers") or 0,
            site=candidate.get("site") or candidate.get("site_id"),
            release_group=candidate.get("release_group"),
            hashes={"torrent": torrent_hash} if torrent_hash else {},
            raw=candidate,
        )

    async def _build_decision_context(
        self,
        subscription: Subscription,
        *,
        debug: bool = False,
    ) -> DecisionContext:
        existing_items = await self._collect_existing_items(subscription)
        return DecisionContext(
            subscription=self._build_decision_subscription_info(subscription),
            existing_items=existing_items,
            hnr_site=(subscription.sites or [None])[0] if subscription.sites else None,
            debug_enabled=debug,
        )

    def _build_decision_subscription_info(
        self,
        subscription: Subscription,
    ) -> DecisionSubscriptionInfo:
        return DecisionSubscriptionInfo(
            id=subscription.id,
            title=subscription.title,
            media_type=subscription.media_type,
            quality=subscription.quality,
            resolution=subscription.resolution,
            effect=subscription.effect,
            min_seeders=subscription.min_seeders,
            include=subscription.include,
            exclude=subscription.exclude,
            filter_groups=subscription.filter_groups,
            search_rules=subscription.search_rules,
            extra_metadata=subscription.extra_metadata or {},
        )

    async def _collect_existing_items(
        self,
        subscription: Subscription,
        limit: int = 5,
    ) -> List[DecisionExistingItem]:
        """收集最近的下载任务作为比较依据。"""
        query = (
            select(DownloadTask)
            .where(DownloadTask.media_type == subscription.media_type)
            .order_by(DownloadTask.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        items: List[DecisionExistingItem] = []
        for task in result.scalars().all():
            items.append(
                DecisionExistingItem(
                    title=task.title,
                    media_type=task.media_type,
                    quality=(task.extra_metadata or {}).get("quality"),
                    resolution=(task.extra_metadata or {}).get("resolution"),
                    effect=(task.extra_metadata or {}).get("effect"),
                    size_gb=task.size_gb,
                    status=task.status,
                    source="download_task",
                    extra={
                        "downloader": task.downloader,
                        "progress": task.progress,
                    },
                )
            )
        return items
    
    async def _filter_search_results(self, results: List[dict], subscription: Subscription) -> List[dict]:
        """根据订阅规则过滤搜索结果（使用规则引擎 + 安全策略 + 规则组）"""
        if subscription.media_type == "music":
            return results
        
        # 1. 应用安全策略过滤（VIDEO-AUTOLOOP-1）
        results = self._apply_security_filters(results, subscription)
        
        # 2. 解析规则组并合并过滤规则
        merged_include = subscription.include or ""
        merged_exclude = subscription.exclude or ""
        
        # 获取规则组并合并规则
        if subscription.filter_group_ids:
            try:
                rule_groups = await self.filter_rule_group_service.resolve_groups_for_subscription(
                    subscription.user_id, 
                    subscription.filter_group_ids, 
                    subscription.media_type
                )
                
                # 合并规则组的include/exclude规则
                for group in rule_groups:
                    if group.get('rules'):
                        rules = group['rules']
                        if rules.get('include'):
                            if merged_include:
                                merged_include += ","
                            merged_include += ",".join(rules['include']) if isinstance(rules['include'], list) else str(rules['include'])
                        if rules.get('exclude'):
                            if merged_exclude:
                                merged_exclude += ","
                            merged_exclude += ",".join(rules['exclude']) if isinstance(rules['exclude'], list) else str(rules['exclude'])
            except Exception as e:
                logger.warning(f"解析规则组失败，使用默认规则: {e}")
        
        # 3. 构建订阅规则字典
        subscription_dict = {
            "quality": subscription.quality,
            "resolution": subscription.resolution,
            "effect": subscription.effect,
            "min_seeders": subscription.min_seeders,
            "include": merged_include,
            "exclude": merged_exclude,
            "filter_groups": [],  # 规则组已在订阅服务中处理，传递空列表避免重复处理
            "media_type": subscription.media_type,
            "season": subscription.season,
            "start_episode": subscription.start_episode,
            "total_episode": subscription.total_episode,
            "min_size": None,  # 可以从search_rules中获取
            "max_size": None
        }
        
        # 4. 使用规则引擎过滤和排序
        filtered = self.rule_engine.filter_and_sort_results(
            results,
            subscription_dict,
            sort_by="score"
        )
        
        return filtered
    
    def _apply_security_filters(self, results: List[dict], subscription: Subscription) -> List[dict]:
        """应用安全策略过滤（VIDEO-AUTOLOOP-1）"""
        # 向后兼容：获取安全策略字段，默认为安全值
        allow_hr = getattr(subscription, 'allow_hr', False)
        allow_h3h5 = getattr(subscription, 'allow_h3h5', False)
        strict_free_only = getattr(subscription, 'strict_free_only', False)
        
        filtered = []
        
        for result in results:
            # HR/H&R 过滤
            if not allow_hr and result.get('is_hr', False):
                continue
            
            # H3/H5 过滤（TODO: 需要基于intel_hr_status精确判断，暂时用HR状态作为代理）
            if not allow_h3h5 and result.get('is_hr', False):
                continue
            
            # 严格只下free过滤
            if strict_free_only and not (result.get('is_free', False) or result.get('is_half_free', False)):
                continue
            
            filtered.append(result)
        
        # 记录安全过滤统计
        if len(filtered) < len(results):
            filtered_count = len(results) - len(filtered)
            logger.info(
                f"订阅 {subscription.id} 安全策略过滤: "
                f"过滤掉 {filtered_count} 个结果 "
                f"(allow_hr={allow_hr}, allow_h3h5={allow_h3h5}, strict_free_only={strict_free_only})"
            )
        
        return filtered
    
    def _select_best_result(self, results: List[dict], subscription: Subscription) -> Optional[dict]:
        """选择最佳搜索结果（使用规则引擎评分）"""
        if not results:
            return None
        
        if subscription.media_type == "music":
            return max(results, key=lambda x: x.get("seeders", 0))
        
        # 将Subscription对象转换为字典
        subscription_dict = {
            "quality": subscription.quality,
            "resolution": subscription.resolution,
            "effect": subscription.effect,
            "min_seeders": subscription.min_seeders,
            "include": subscription.include,
            "exclude": subscription.exclude,
            "filter_groups": subscription.filter_groups,
            "media_type": subscription.media_type,
            "season": subscription.season
        }
        
        if subscription.best_version:
            # 使用规则引擎评分选择最佳版本
            scored_results = []
            for result in results:
                score = self.rule_engine.score_result(result, subscription_dict)
                scored_results.append((score, result))
            
            # 按分数排序
            scored_results.sort(key=lambda x: x[0], reverse=True)
            return scored_results[0][1] if scored_results else None
        else:
            # 简单选择做种数最多的
            return max(results, key=lambda x: x.get("seeders", 0))

    async def _record_history(
        self,
        subscription_id: int,
        action: str,
        action_type: str,
        description: str,
        *,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        search_query: Optional[str] = None,
        search_results_count: Optional[int] = None,
        search_params: Optional[Dict] = None,
        download_task_id: Optional[str] = None,
        download_title: Optional[str] = None,
        download_size_gb: Optional[float] = None,
        status: Optional[str] = None,
        error_message: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Optional[SubscriptionHistory]:
        """
        订阅历史记录的通用内部方法。

        注意：
        - 这是一个“旁路日志”，失败时不会让主业务（创建订阅 / 搜索 / 下载）报错。
        - 所以这里捕获异常，只打日志，不向外抛出。
        """
        try:
            history = SubscriptionHistory(
                subscription_id=subscription_id,
                action=action,
                action_type=action_type,
                description=description,
                old_value=old_value,
                new_value=new_value,
                search_query=search_query,
                search_results_count=search_results_count,
                search_params=search_params,
                download_task_id=download_task_id,
                download_title=download_title,
                download_size_gb=download_size_gb,
                status=status,
                error_message=error_message,
                user_id=user_id,
            )

            self.db.add(history)
            await self.db.commit()
            await self.db.refresh(history)

            logger.debug(
                f"[SubscriptionHistory] 记录成功: "
                f"subscription_id={subscription_id}, action={action}, action_type={action_type}"
            )
            return history

        except Exception as e:
            # 日志记录即可，不影响主流程
            logger.error(
                f"[SubscriptionHistory] 记录失败: "
                f"subscription_id={subscription_id}, action={action}, error={e}"
            )
            try:
                await self.db.rollback()
            except Exception:
                # 防御性处理，避免 rollback 再次抛异常
                logger.exception("[SubscriptionHistory] rollback 失败")
            return None

