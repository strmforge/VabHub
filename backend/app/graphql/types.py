from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import strawberry
from strawberry.scalars import JSON


@strawberry.type
class SiteType:
    id: int
    name: str
    url: Optional[str]
    enabled: bool


@strawberry.type
class SubscriptionNode:
    id: int
    title: str
    media_type: str
    status: str
    created_at: Optional[datetime]


@strawberry.type
class SubscriptionConnection:
    items: List[SubscriptionNode]
    total: int
    page: int
    page_size: int
    total_pages: int


@strawberry.type
class DownloadTaskType:
    id: int
    title: str
    status: str
    progress: float
    size_gb: float
    downloaded_gb: float
    downloader: str
    speed_mbps: Optional[float]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    media_type: Optional[str]
    extra_metadata: Optional[JSON]


@strawberry.type
class DashboardStatsType:
    total_subscriptions: int
    active_downloads: int
    music_subscriptions: int
    hnr_risks: int


@strawberry.type
class MusicSubscriptionType:
    id: int
    name: str
    type: str
    platform: str
    status: str
    subscription_id: Optional[int]
    created_at: Optional[datetime]


@strawberry.type
class MusicChartEntryType:
    id: Optional[int]
    rank: Optional[int]
    title: str
    artist: str
    album: Optional[str]
    platform: str
    chart_type: str
    region: str
    external_url: Optional[str]
    cover_url: Optional[str]


@strawberry.type
class MusicChartBatchType:
    batch_id: str
    captured_at: Optional[datetime]
    platform: str
    chart_type: str
    region: str
    entries: List[MusicChartEntryType]


@strawberry.type
class MusicSubscriptionMutationPayload:
    ok: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    subscription: Optional[MusicSubscriptionType] = None


@strawberry.type
class SubscriptionMutationPayload:
    ok: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    subscription: Optional[SubscriptionNode] = None


@strawberry.type
class MusicAutoDownloadPayload:
    ok: bool
    mode: Optional[str] = None
    message: Optional[str] = None
    preview_queries: Optional[List[str]] = None
    downloaded_count: Optional[int] = None
    subscription_id: Optional[int] = None
    music_subscription_id: Optional[int] = None


@strawberry.type
class SchedulerTaskType:
    job_id: str
    name: str
    task_type: str
    status: str
    trigger_type: str
    next_run_time: Optional[datetime]
    last_run_time: Optional[datetime]
    enabled: bool


@strawberry.type
class RSSHubSubscriptionHealthType:
    user_id: int
    username: Optional[str]
    target_id: str
    target_type: str
    target_name: Optional[str]
    enabled: bool
    is_legacy_placeholder: bool
    last_error_code: Optional[str]
    last_error_message: Optional[str]
    last_error_at: Optional[str]
    last_checked_at: Optional[str]
    updated_at: Optional[str]
    health_status: Optional[str]


@strawberry.type
class LogStreamType:
    name: str
    description: Optional[str]


@strawberry.input
class MusicSubscriptionOptionsInput:
    name: Optional[str] = None
    type: Optional[str] = None
    target_id: Optional[str] = None
    auto_download: Optional[bool] = None
    quality: Optional[str] = None
    sites: Optional[List[str]] = None
    downloader: Optional[str] = None
    save_path: Optional[str] = None
    min_seeders: Optional[int] = None
    include: Optional[str] = None
    exclude: Optional[str] = None
    search_keywords: Optional[List[str]] = None


@strawberry.input
class CreateMusicSubscriptionFromChartInput:
    entry_id: int
    options: Optional[MusicSubscriptionOptionsInput] = None


@strawberry.input
class ToggleSubscriptionInput:
    subscription_id: int
    enabled: bool


@strawberry.input
class DecisionCandidateInput:
    title: str
    subtitle: Optional[str] = None
    media_type: Optional[str] = None
    quality: Optional[str] = None
    resolution: Optional[str] = None
    effect: Optional[str] = None
    seeders: Optional[int] = None
    size_gb: Optional[float] = None
    site: Optional[str] = None
    release_group: Optional[str] = None
    raw: Optional[JSON] = None


@strawberry.type
class DecisionResultType:
    should_download: bool
    reason: str
    message: Optional[str] = None
    score: Optional[float] = None
    selected_quality: Optional[str] = None
    normalized_quality: Optional[str] = None
    hnr_verdict: Optional[str] = None
    debug_context: Optional[JSON] = None


@strawberry.type
class DecisionDryRunPayload:
    ok: bool
    subscription: Optional[SubscriptionNode] = None
    result: Optional[DecisionResultType] = None
    error_message: Optional[str] = None


@strawberry.type
class SelfCheckOptionalDependencyType:
    name: str
    status: str
    enabled: bool
    message: Optional[str] = None
    details: Optional[JSON] = None


@strawberry.type
class SelfCheckSchemaStepType:
    id: str
    title: str
    status: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class SelfCheckSchemaStatusType:
    status: str
    checked_at: Optional[str]
    steps: List[SelfCheckSchemaStepType]


@strawberry.type
class SelfCheckTestResultType:
    script: str
    args: List[str]
    duration_seconds: float
    warnings: List[str]


@strawberry.type
class SelfCheckTestSkipType:
    script: str
    reason: str


@strawberry.type
class SelfCheckTestReportType:
    status: str
    path: Optional[str]
    generated_at: Optional[str]
    updated_at: Optional[str]
    warnings: Optional[List[str]]
    skipped: Optional[List[SelfCheckTestSkipType]]
    results: Optional[List[SelfCheckTestResultType]]


@strawberry.type
class SystemSelfCheckType:
    generated_at: Optional[str]
    optional_dependencies: List[SelfCheckOptionalDependencyType]
    schema_checks: SelfCheckSchemaStatusType
    test_report: Optional[SelfCheckTestReportType]

