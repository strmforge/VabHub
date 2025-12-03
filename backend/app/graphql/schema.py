from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import strawberry
from sqlalchemy import func, select
from strawberry.types import Info

from app.core.database import AsyncSession
from app.core.plugins.hot_reload import get_hot_reload_manager
from app.graphql.types import (
    CreateMusicSubscriptionFromChartInput,
    DashboardStatsType,
    DecisionCandidateInput,
    DecisionDryRunPayload,
    DecisionResultType,
    DownloadTaskType,
    LogStreamType,
    MusicAutoDownloadPayload,
    MusicChartBatchType,
    MusicChartEntryType,
    MusicSubscriptionMutationPayload,
    MusicSubscriptionOptionsInput,
    MusicSubscriptionType,
    RSSHubSubscriptionHealthType,
    SchedulerTaskType,
    SelfCheckOptionalDependencyType,
    SelfCheckSchemaStatusType,
    SelfCheckSchemaStepType,
    SelfCheckTestReportType,
    SelfCheckTestResultType,
    SelfCheckTestSkipType,
    SiteType,
    SubscriptionConnection,
    SubscriptionMutationPayload,
    SubscriptionNode,
    SystemSelfCheckType,
    ToggleSubscriptionInput,
)
from app.models.download import DownloadTask
from app.models.hnr import HNRDetection
from app.models.music import MusicSubscription
from app.models.scheduler_task import SchedulerTask
from app.models.site import Site
from app.models.subscription import Subscription
from app.modules.log_center.service import LogSource
from app.modules.music.service import MusicService
from app.modules.rsshub.service import RSSHubService, RSSHubDisabledError
from app.modules.subscription.service import SubscriptionService
from app.modules.system_selfcheck.service import SystemSelfCheckService
from app.modules.decision.models import DecisionResult as DecisionResultModel


@asynccontextmanager
async def _session(info: Info):
    session_factory = info.context["session_factory"]
    async with session_factory() as db:
        yield db


def _map_subscription_node(sub: Subscription) -> SubscriptionNode:
    return SubscriptionNode(
        id=sub.id,
        title=sub.title,
        media_type=sub.media_type,
        status=sub.status,
        created_at=sub.created_at,
    )


def _map_decision_result(
    result: DecisionResultModel,
    *,
    include_debug: bool,
) -> DecisionResultType:
    return DecisionResultType(
        should_download=result.should_download,
        reason=result.reason.value,
        message=result.message,
        score=result.score,
        selected_quality=result.selected_quality,
        normalized_quality=result.normalized_quality,
        hnr_verdict=result.hnr_verdict,
        debug_context=result.debug_context if include_debug else None,
    )


def _map_music_subscription(sub: MusicSubscription) -> MusicSubscriptionType:
    return MusicSubscriptionType(
        id=sub.id,
        name=sub.name,
        type=sub.type,
        platform=sub.platform,
        status=sub.status,
        subscription_id=sub.subscription_id,
        created_at=sub.created_at,
    )


def _map_system_self_check(payload: Dict[str, Any]) -> SystemSelfCheckType:
    optional = [
        SelfCheckOptionalDependencyType(
            name=item.get("name", ""),
            status=item.get("status", "unknown"),
            enabled=bool(item.get("enabled", True)),
            message=item.get("message"),
            details=item.get("details"),
        )
        for item in payload.get("optional_dependencies", [])
    ]

    schema_section = payload.get("schema_checks") or {}
    schema_steps = [
        SelfCheckSchemaStepType(
            id=step.get("id", ""),
            title=step.get("title", ""),
            status=step.get("status", "unknown"),
            started_at=step.get("started_at"),
            finished_at=step.get("finished_at"),
            error=step.get("error"),
        )
        for step in schema_section.get("steps", [])
    ]
    schema_checks = SelfCheckSchemaStatusType(
        status=schema_section.get("status", "unknown"),
        checked_at=schema_section.get("checked_at"),
        steps=schema_steps,
    )

    report_section = payload.get("test_report")
    test_report: Optional[SelfCheckTestReportType] = None
    if report_section:
        skipped = [
            SelfCheckTestSkipType(
                script=item.get("script", ""),
                reason=item.get("reason", ""),
            )
            for item in report_section.get("skipped", [])
        ]
        results = [
            SelfCheckTestResultType(
                script=item.get("script", ""),
                args=item.get("args") or [],
                duration_seconds=float(item.get("duration_seconds") or 0.0),
                warnings=item.get("warnings") or [],
            )
            for item in report_section.get("results", [])
        ]
        test_report = SelfCheckTestReportType(
            status=report_section.get("status", "unknown"),
            path=report_section.get("path"),
            generated_at=report_section.get("generated_at"),
            updated_at=report_section.get("updated_at"),
            warnings=report_section.get("warnings"),
            skipped=skipped or None,
            results=results or None,
        )

    return SystemSelfCheckType(
        generated_at=payload.get("generated_at"),
        optional_dependencies=optional,
        schema_checks=schema_checks,
        test_report=test_report,
    )


def _decision_candidate_input_to_dict(candidate: DecisionCandidateInput) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "title": candidate.title,
        "subtitle": candidate.subtitle,
        "media_type": candidate.media_type,
        "quality": candidate.quality,
        "resolution": candidate.resolution,
        "effect": candidate.effect,
        "seeders": candidate.seeders,
        "size_gb": candidate.size_gb,
        "site": candidate.site,
        "release_group": candidate.release_group,
    }
    if candidate.raw:
        payload["raw"] = candidate.raw
    return payload


@strawberry.type
class QueryBase:
    @strawberry.field(description="获取已配置站点列表")
    async def sites(self, info: Info) -> List[SiteType]:
        async with _session(info) as db:
            result = await db.execute(select(Site).order_by(Site.id))
            return [
                SiteType(id=site.id, name=site.name, url=site.url, enabled=site.enabled)
                for site in result.scalars().all()
            ]

    @strawberry.field(description="分页订阅列表")
    async def subscriptions(
        self,
        info: Info,
        page: int = 1,
        page_size: int = 20,
        media_type: Optional[str] = None,
    ) -> SubscriptionConnection:
        async with _session(info) as db:
            count_stmt = select(func.count(Subscription.id))
            query_stmt = select(Subscription)
            if media_type:
                count_stmt = count_stmt.where(Subscription.media_type == media_type)
                query_stmt = query_stmt.where(Subscription.media_type == media_type)

            total = (await db.execute(count_stmt)).scalar() or 0
            query_stmt = (
                query_stmt.order_by(Subscription.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            result = await db.execute(query_stmt)

            items = [_map_subscription_node(sub) for sub in result.scalars().all()]

        total_pages = (total + page_size - 1) // page_size if page_size else 1
        return SubscriptionConnection(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @strawberry.field(description="当前下载任务")
    async def download_tasks(
        self,
        info: Info,
        limit: int = 20,
    ) -> List[DownloadTaskType]:
        async with _session(info) as db:
            query = (
                select(DownloadTask)
                .order_by(DownloadTask.created_at.desc())
                .limit(limit)
            )
            result = await db.execute(query)
            return [
                DownloadTaskType(
                    id=task.id,
                    title=task.title,
                    status=task.status,
                    progress=task.progress,
                    size_gb=task.size_gb,
                    downloaded_gb=task.downloaded_gb,
                    downloader=task.downloader,
                    speed_mbps=task.speed_mbps,
                    created_at=task.created_at,
                    updated_at=task.updated_at,
                    media_type=task.media_type,
                    extra_metadata=task.extra_metadata or {},
                )
                for task in result.scalars().all()
            ]

    @strawberry.field(description="仪表盘统计信息")
    async def dashboard_stats(self, info: Info) -> DashboardStatsType:
        async with _session(info) as db:
            subs_result = await db.execute(select(func.count(Subscription.id)))
            downloads_result = await db.execute(
                select(func.count(DownloadTask.id)).where(DownloadTask.status == "downloading")
            )
            music_result = await db.execute(select(func.count(MusicSubscription.id)))
            hnr_result = await db.execute(
                select(func.count(HNRDetection.id)).where(HNRDetection.verdict != "pass")
            )

            return DashboardStatsType(
                total_subscriptions=subs_result.scalar() or 0,
                active_downloads=downloads_result.scalar() or 0,
                music_subscriptions=music_result.scalar() or 0,
                hnr_risks=hnr_result.scalar() or 0,
            )

    @strawberry.field(description="最新的音乐订阅列表")
    async def music_subscriptions(
        self,
        info: Info,
        platform: Optional[str] = None,
        limit: int = 20,
    ) -> List[MusicSubscriptionType]:
        async with _session(info) as db:
            query = select(MusicSubscription).order_by(MusicSubscription.created_at.desc()).limit(limit)
            if platform:
                query = query.where(MusicSubscription.platform == platform)
            result = await db.execute(query)
            return [_map_music_subscription(item) for item in result.scalars().all()]

    @strawberry.field(description="音乐榜单历史记录")
    async def music_charts(
        self,
        info: Info,
        platform: Optional[str] = None,
        chart_type: Optional[str] = None,
        region: Optional[str] = None,
        batches: int = 3,
    ) -> List[MusicChartBatchType]:
        async with _session(info) as db:
            service = MusicService(db)
            history = await service.get_chart_history(
                platform=platform,
                chart_type=chart_type,
                region=region,
                batches=batches,
            )
            response: List[MusicChartBatchType] = []
            for batch in history:
                entries = [
                    MusicChartEntryType(
                        id=entry.get("id"),
                        rank=entry.get("rank"),
                        title=entry.get("title"),
                        artist=entry.get("artist"),
                        album=entry.get("album"),
                        platform=entry.get("platform"),
                        chart_type=entry.get("chart_type"),
                        region=entry.get("region"),
                        external_url=entry.get("external_url"),
                        cover_url=entry.get("cover_url"),
                    )
                    for entry in batch.get("entries", [])
                ]
                response.append(
                    MusicChartBatchType(
                        batch_id=batch.get("batch_id"),
                        captured_at=batch.get("captured_at"),
                        platform=batch.get("platform"),
                        chart_type=batch.get("chart_type"),
                        region=batch.get("region"),
                        entries=entries,
                    )
                )
            return response

    @strawberry.field(description="调度任务概览")
    async def scheduler_tasks(
        self,
        info: Info,
        limit: int = 20,
    ) -> List[SchedulerTaskType]:
        async with _session(info) as db:
            result = await db.execute(
                select(SchedulerTask)
                    .order_by(SchedulerTask.updated_at.desc())
                    .limit(limit)
            )
            tasks = result.scalars().all()
            return [
                SchedulerTaskType(
                    job_id=task.job_id,
                    name=task.name,
                    task_type=task.task_type,
                    status=task.status,
                    trigger_type=task.trigger_type,
                    next_run_time=task.next_run_time,
                    last_run_time=task.last_run_time,
                    enabled=task.enabled,
                )
                for task in tasks
            ]

    @strawberry.field(description="RSSHub 订阅健康状态")
    async def rsshub_subscription_health(
        self,
        info: Info,
        user_id: Optional[int] = None,
        target_type: Optional[str] = None,
        only_legacy: bool = False,
        limit: int = 50,
    ) -> List[RSSHubSubscriptionHealthType]:
        async with _session(info) as db:
            try:
                service = RSSHubService(db)
                items = await service.list_subscription_health(
                    user_id=user_id,
                    target_type=target_type,
                    only_legacy=only_legacy,
                    limit=limit,
                )
            except RSSHubDisabledError:
                return []
            return [
                RSSHubSubscriptionHealthType(
                    user_id=item["user_id"],
                    username=item.get("username"),
                    target_id=item["target_id"],
                    target_type=item["target_type"],
                    target_name=item.get("target_name"),
                    enabled=item["enabled"],
                    is_legacy_placeholder=item["is_legacy_placeholder"],
                    last_error_code=item.get("last_error_code"),
                    last_error_message=item.get("last_error_message"),
                    last_error_at=item.get("last_error_at"),
                    last_checked_at=item.get("last_checked_at"),
                    updated_at=item.get("updated_at"),
                    health_status=item.get("health_status"),
                )
                for item in items
            ]

    @strawberry.field(description="可用日志来源")
    async def log_streams(self, info: Info) -> List[LogStreamType]:
        return [
            LogStreamType(
                name=source.value,
                description=f"{source.value} 相关的实时日志",
            )
            for source in LogSource
        ]

    @strawberry.field(description="系统自检结果（依赖/Schema/自测报告）")
    async def system_self_check(self, info: Info) -> SystemSelfCheckType:
        async with _session(info) as db:
            service = SystemSelfCheckService(db)
            payload = await service.gather()
        return _map_system_self_check(payload)


@strawberry.type
class MutationBase:
    @strawberry.mutation(description="下载决策 Dry-run 调试")
    async def decision_dry_run(
        self,
        info: Info,
        subscription_id: int,
        candidate: DecisionCandidateInput,
        debug: bool = False,
    ) -> DecisionDryRunPayload:
        async with _session(info) as db:
            service = SubscriptionService(db)
            subscription = await service.get_subscription(subscription_id)
            if not subscription:
                return DecisionDryRunPayload(
                    ok=False,
                    error_message="订阅不存在",
                )

            decision_candidate = _decision_candidate_input_to_dict(candidate)
            decision_result = await service.evaluate_candidate_with_decision(
                subscription,
                decision_candidate,
                debug=debug,
            )
            subscription_node = _map_subscription_node(subscription)

        if decision_result is None:
            return DecisionDryRunPayload(
                ok=False,
                subscription=subscription_node,
                error_message="决策层暂不可用",
            )

        return DecisionDryRunPayload(
            ok=True,
            subscription=subscription_node,
            result=_map_decision_result(decision_result, include_debug=debug),
        )

    @strawberry.mutation(description="切换订阅启用状态")
    async def toggle_subscription(
        self,
        info: Info,
        payload: ToggleSubscriptionInput,
    ) -> SubscriptionMutationPayload:
        async with _session(info) as db:
            service = SubscriptionService(db)
            subscription = await service.get_subscription(payload.subscription_id)
            if not subscription:
                return SubscriptionMutationPayload(
                    ok=False,
                    error_code="NOT_FOUND",
                    error_message="订阅不存在",
                )

            updated = (
                await service.enable_subscription(payload.subscription_id)
                if payload.enabled
                else await service.disable_subscription(payload.subscription_id)
            )

            if not updated:
                return SubscriptionMutationPayload(
                    ok=False,
                    error_code="UPDATE_FAILED",
                    error_message="更新订阅状态失败",
                )

            return SubscriptionMutationPayload(
                ok=True,
                subscription=_map_subscription_node(updated),
            )

    @strawberry.mutation(description="基于榜单条目创建音乐订阅")
    async def create_music_subscription_from_chart(
        self,
        info: Info,
        payload: CreateMusicSubscriptionFromChartInput,
    ) -> MusicSubscriptionMutationPayload:
        async with _session(info) as db:
            service = MusicService(db)
            record = await service.get_chart_entry_by_id(payload.entry_id)
            if not record:
                return MusicSubscriptionMutationPayload(
                    ok=False,
                    error_code="NOT_FOUND",
                    error_message="未找到对应的榜单条目",
                )

            options = payload.options or MusicSubscriptionOptionsInput()
            raw_data = record.raw_data or {}
            target_id = (
                options.target_id
                or raw_data.get("id")
                or raw_data.get("song_id")
                or f"chart_entry_{record.id}"
            )

            keywords = options.search_keywords or [f"{record.artist} - {record.title}"]
            subscription_payload = {
                "name": options.name or f"{record.title} - {record.artist}",
                "type": options.type or "track",
                "platform": record.platform,
                "target_id": target_id,
                "target_name": record.title,
                "auto_download": options.auto_download if options.auto_download is not None else True,
                "quality": options.quality,
                "sites": options.sites,
                "downloader": options.downloader,
                "save_path": options.save_path,
                "min_seeders": options.min_seeders,
                "include": options.include,
                "exclude": options.exclude,
                "search_keywords": keywords,
                "chart_entry": {
                    "entry_id": record.id,
                    "batch_id": record.batch_id,
                    "rank": record.rank,
                    "platform": record.platform,
                    "chart_type": record.chart_type,
                    "region": record.region,
                },
            }

            try:
                music_subscription = await service.create_subscription(subscription_payload)
            except Exception as exc:
                return MusicSubscriptionMutationPayload(
                    ok=False,
                    error_code="CREATE_FAILED",
                    error_message=str(exc),
                )

            return MusicSubscriptionMutationPayload(
                ok=True,
                subscription=_map_music_subscription(music_subscription),
            )

    @strawberry.mutation(description="触发音乐订阅执行")
    async def trigger_music_subscription_run(
        self,
        info: Info,
        music_subscription_id: int,
        preview_only: bool = True,
        limit: int = 5,
    ) -> MusicAutoDownloadPayload:
        async with _session(info) as db:
            service = MusicService(db)
            result = await service.auto_download_subscription(
                music_subscription_id,
                preview_only=preview_only,
                limit=limit,
            )
            ok = result.get("success", False)
            result_body = result.get("result", {})

            return MusicAutoDownloadPayload(
                ok=ok,
                mode=result.get("mode"),
                message=result_body.get("message") or result.get("message"),
                preview_queries=result.get("preview_queries"),
                downloaded_count=result_body.get("downloaded_count"),
                subscription_id=result.get("subscription_id"),
                music_subscription_id=result.get("music_subscription_id"),
            )


def _collect_plugin_mixins():
    manager = get_hot_reload_manager()
    mixins_map = manager.get_graphql_mixins()
    query_mixins: List[type] = []
    mutation_mixins: List[type] = []
    for plugin_name in sorted(mixins_map.keys()):
        payload = mixins_map[plugin_name]
        query_mixins.extend(payload.get("query") or [])
        mutation_mixins.extend(payload.get("mutation") or [])
    return query_mixins, mutation_mixins


def _build_graphql_types():
    query_mixins, mutation_mixins = _collect_plugin_mixins()
    query_bases = tuple(query_mixins) + (QueryBase,)
    mutation_bases = tuple(mutation_mixins) + (MutationBase,)
    QueryType = strawberry.type(type("Query", query_bases, {}))
    MutationType = strawberry.type(type("Mutation", mutation_bases, {}))
    return QueryType, MutationType


Query, Mutation = _build_graphql_types()
schema = strawberry.Schema(query=Query, mutation=Mutation)
