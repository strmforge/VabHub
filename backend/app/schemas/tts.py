"""
TTS 设置 Schema
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class TTSRateLimitInfo(BaseModel):
    """TTS 限流信息"""
    max_daily_requests: int
    max_daily_characters: int
    max_requests_per_run: int
    last_limited_at: Optional[datetime] = None
    last_limited_reason: Optional[str] = None


class TTSUsageStats(BaseModel):
    """TTS 使用统计"""
    total_tts_audiobooks: int
    by_provider: Dict[str, int]  # {"dummy": 10, "http": 5}


class TTSJobStatus(str, Enum):
    """TTS Job 状态"""
    queued = "queued"
    running = "running"
    success = "success"
    partial = "partial"
    failed = "failed"


class TTSJobResponse(BaseModel):
    """TTS Job 响应"""
    id: int
    ebook_id: int
    status: TTSJobStatus
    provider: Optional[str] = None
    strategy: Optional[str] = None
    requested_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    total_chapters: Optional[int] = None
    processed_chapters: int
    created_files_count: int
    error_count: int
    last_error: Optional[str] = None
    created_by: Optional[str] = None
    details: Optional[Dict[str, Any]] = None  # 断点续跑信息等
    
    class Config:
        from_attributes = True


class RunBatchJobsRequest(BaseModel):
    """批量执行 Job 请求"""
    max_jobs: Optional[int] = None  # 最多处理的 Job 数量，None 表示使用后端默认值


class TTSBatchJobsResponse(BaseModel):
    """批量执行 Job 响应"""
    total_jobs: int
    run_jobs: int
    succeeded_jobs: int
    partial_jobs: int
    failed_jobs: int
    last_job_id: Optional[int] = None
    message: str


class TTSWorkProfileBase(BaseModel):
    """TTS 作品级配置基础模型"""
    provider: Optional[str] = None
    language: Optional[str] = None
    voice: Optional[str] = None
    speed: Optional[float] = Field(None, ge=0.5, le=2.0)
    pitch: Optional[float] = Field(None, ge=-10.0, le=10.0)
    enabled: bool = True
    notes: Optional[str] = None


class TTSWorkProfileResponse(TTSWorkProfileBase):
    """TTS 作品级配置响应"""
    id: int
    ebook_id: int
    preset_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TTSVoicePresetBase(BaseModel):
    """TTS 声线预设基础模型"""
    name: str
    provider: Optional[str] = None
    language: Optional[str] = None
    voice: Optional[str] = None
    speed: Optional[float] = Field(None, ge=0.5, le=2.0)
    pitch: Optional[float] = Field(None, ge=-10.0, le=10.0)
    is_default: bool = False
    notes: Optional[str] = None


class TTSVoicePresetResponse(TTSVoicePresetBase):
    """TTS 声线预设响应"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UpsertTTSVoicePresetRequest(TTSVoicePresetBase):
    """创建/更新 TTS 声线预设请求"""
    id: Optional[int] = None  # 有 id 则更新，否则创建


class TTSWorkBatchFilter(BaseModel):
    """批量应用预设的筛选条件"""
    language: Optional[str] = None
    author_substring: Optional[str] = None
    series_substring: Optional[str] = None
    tag_keyword: Optional[str] = None
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None
    has_profile: Optional[bool] = None  # True / False / None


class TTSWorkBatchPreviewItem(BaseModel):
    """批量预览项"""
    ebook_id: int
    title: str
    author: Optional[str] = None
    series: Optional[str] = None
    language: Optional[str] = None
    created_at: datetime
    
    has_profile: bool
    profile_enabled: Optional[bool] = None
    profile_preset_id: Optional[int] = None
    profile_preset_name: Optional[str] = None


class TTSWorkBatchPreviewResponse(BaseModel):
    """批量预览响应"""
    total: int
    limit: int
    items: List[TTSWorkBatchPreviewItem]


class ApplyTTSWorkPresetRequest(BaseModel):
    """批量应用预设请求"""
    preset_id: int
    filter: TTSWorkBatchFilter
    override_existing: bool = False
    enable_profile: bool = True
    dry_run: bool = False  # 可选：仅统计，不实际写入


class ApplyTTSWorkPresetResult(BaseModel):
    """批量应用预设结果"""
    matched_ebooks: int
    created_profiles: int
    updated_profiles: int
    skipped_existing_profile: int


class TTSVoicePresetUsage(BaseModel):
    """声线预设使用情况"""
    id: int
    name: str
    provider: Optional[str] = None
    language: Optional[str] = None
    voice: Optional[str] = None
    is_default: bool = False
    
    bound_works_count: int = 0  # 有多少 TTSWorkProfile 使用了这个 preset
    tts_generated_works_count: int = 0  # 有多少作品已经生成过 TTS 有声书
    last_used_at: Optional[datetime] = None  # 最近一次生成 TTS 的时间
    
    # 热度指标
    usage_ratio: float = 0.0  # 0~1，生成/绑定，绑定为0时保持0.0
    heat_level: str = "normal"  # "hot" | "sleeping" | "cold" | "normal"
    is_hot: bool = False
    is_sleeping: bool = False
    is_cold: bool = False


class TTSWorkProfileSummary(BaseModel):
    """作品 Profile 总览"""
    works_total: int = 0  # 总 EBook 数量
    works_with_profile: int = 0  # 有 TTSWorkProfile 的作品数
    works_without_profile: int = 0  # 无 Profile 的作品数
    
    works_with_preset: int = 0  # 有 preset_id 的 Profile 对应的作品数
    works_without_preset: int = 0  # 有 Profile 但 preset_id 为空的作品数


class UpsertTTSWorkProfileRequest(TTSWorkProfileBase):
    """创建/更新 TTS 作品级配置请求"""
    ebook_id: int
    preset_id: Optional[int] = None  # 引用的预设 ID


class TTSSettingsResponse(BaseModel):
    """TTS 设置响应"""
    # 基础配置和健康状态
    enabled: bool
    provider: str
    status: str  # "disabled" / "ok" / "degraded"
    output_root: Optional[str] = None
    max_chapters: Optional[int] = None
    strategy: Optional[str] = None
    last_used_at: Optional[datetime] = None
    last_error: Optional[str] = None
    
    # 限流信息
    rate_limit_enabled: bool
    rate_limit_info: Optional[TTSRateLimitInfo] = None
    
    # 使用统计
    usage_stats: TTSUsageStats
    
    # 预设使用统计
    preset_usage: List[TTSVoicePresetUsage] = []
    
    # 作品 Profile 总览
    work_profile_summary: Optional[TTSWorkProfileSummary] = None
    
    # 存储概览（简化版）
    storage_overview: Optional["TTSStorageOverviewSummary"] = None


class TTSPlaygroundRequest(BaseModel):
    """TTS Playground 请求"""
    text: str
    language: Optional[str] = None
    voice: Optional[str] = None
    speed: Optional[float] = None
    pitch: Optional[float] = None
    ebook_id: Optional[int] = None  # 可选：按作品 Profile / Preset 解析
    provider: Optional[str] = None  # 可选覆盖 provider（不填则用当前全局/解析结果）
    # 可选：是否跳过 RateLimiter（默认为 False，正常走限流）
    skip_rate_limit: bool = False


class TTSPlaygroundResponse(BaseModel):
    """TTS Playground 响应"""
    success: bool
    message: str
    provider: Optional[str] = None
    language: Optional[str] = None
    voice: Optional[str] = None
    speed: Optional[float] = None
    pitch: Optional[float] = None
    char_count: int
    duration_seconds: Optional[float] = None
    # 返回一个可用于前端 <audio> 的相对 URL
    audio_url: Optional[str] = None
    # 是否被 RateLimiter 拦截
    rate_limited: bool = False
    rate_limit_reason: Optional[str] = None


# ========== 用户版 TTS Flow ==========

class UserTTSJobStatus(str, Enum):
    """用户视角的 TTS Job 状态"""
    queued = "queued"
    running = "running"
    partial = "partial"
    success = "success"
    failed = "failed"


class UserWorkTTSStatus(BaseModel):
    """用户视角的作品 TTS 状态"""
    ebook_id: int
    has_tts_audiobook: bool  # 是否存在 is_tts_generated=True 的 AudiobookFile
    last_job_status: Optional[UserTTSJobStatus] = None
    last_job_requested_at: Optional[datetime] = None
    last_job_finished_at: Optional[datetime] = None
    last_job_message: Optional[str] = None
    # 可选：章节数统计
    total_chapters: Optional[int] = None
    generated_chapters: Optional[int] = None


class UserTTSJobEnqueueResponse(BaseModel):
    """用户版创建 TTS Job 响应"""
    success: bool
    job_id: int
    ebook_id: int
    status: str
    message: str
    already_exists: bool = False  # 是否复用了已有 job


class UserTTSJobOverviewItem(BaseModel):
    """用户版 TTS Job 概览项"""
    job_id: int
    ebook_id: int
    ebook_title: str
    ebook_author: Optional[str] = None
    status: str
    requested_at: datetime
    finished_at: Optional[datetime] = None
    progress: Optional[Dict[str, Any]] = None  # {"generated_chapters": 50, "total_chapters": 120}
    last_message: Optional[str] = None
    
    class Config:
        from_attributes = True


# ========== 用户批量 TTS ==========

class UserTTSBatchFilter(BaseModel):
    """用户批量 TTS 筛选器"""
    language: Optional[str] = None  # 只选某种语言的 EBook（如 "zh-CN"）
    author_substring: Optional[str] = None
    series_substring: Optional[str] = None
    tag_keyword: Optional[str] = None
    # 是否只选"当前没有任何有声书"的作品
    only_without_audiobook: bool = True
    # 是否只选"当前没有活跃 Job（queued/running/partial）"的作品
    only_without_active_job: bool = True
    # 限制候选数量（防止查询过大）
    max_candidates: int = Field(200, ge=1, le=500)


class UserTTSBatchPreviewItem(BaseModel):
    """用户批量 TTS 预览项"""
    ebook_id: int
    title: str
    author: Optional[str] = None
    language: Optional[str] = None
    has_audiobook: bool  # 是否已有任何 AudiobookFile
    has_tts_audiobook: bool  # 是否已有 is_tts_generated=True 的 AudiobookFile
    active_job_status: Optional[str] = None  # 若有活跃 job，返回 queued/running/partial 等
    last_job_status: Optional[str] = None  # 最近一个 job 的最终状态（success/failed/partial等）


class UserTTSBatchPreviewResponse(BaseModel):
    """用户批量 TTS 预览响应"""
    total_candidates: int  # 匹配到的总数（在 max_candidates 限制内）
    items: List[UserTTSBatchPreviewItem]


class UserTTSBatchEnqueueRequest(BaseModel):
    """用户批量 TTS enqueue 请求"""
    filter: UserTTSBatchFilter
    # 防止一口气扔太多 Job，进一步保护
    max_new_jobs: int = Field(50, ge=1, le=200)
    # 是否跳过"已有 TTS 有声书"的作品（默认跳过）
    skip_if_has_tts: bool = True


class UserTTSBatchEnqueueResult(BaseModel):
    """用户批量 TTS enqueue 结果"""
    total_candidates: int
    skipped_has_audiobook: int
    skipped_has_tts: int
    skipped_has_active_job: int
    enqueued_new_jobs: int
    already_had_jobs: int


# ========== TTS 存储管理（Dev）==========

class TTSStorageCleanupScope(str, Enum):
    """TTS 存储清理范围"""
    all = "all"
    playground_only = "playground_only"
    job_only = "job_only"
    other_only = "other_only"


class TTSStorageCleanupPreviewRequest(BaseModel):
    """TTS 存储清理预览请求"""
    scope: TTSStorageCleanupScope = TTSStorageCleanupScope.all
    min_age_days: int = Field(ge=0, default=7)
    max_files: int = Field(ge=0, default=10000)  # 预览最多匹配条目数
    mode: str = Field(default="manual", description="清理模式：'manual' 手动参数模式，'policy' 按策略推荐模式")


class TTSStorageCleanupPreviewItem(BaseModel):
    """TTS 存储清理预览项"""
    path: str
    size_bytes: int
    mtime: datetime
    category: str  # "job" | "playground" | "other"


class TTSStorageCleanupPreviewResponse(BaseModel):
    """TTS 存储清理预览响应"""
    root: str
    total_matched_files: int
    total_freed_bytes: int
    sample: List[TTSStorageCleanupPreviewItem]  # 只返回前 N 条示例


class TTSStorageCleanupExecuteRequest(TTSStorageCleanupPreviewRequest):
    """TTS 存储清理执行请求"""
    dry_run: bool = False


class TTSStorageCleanupExecuteResponse(BaseModel):
    """TTS 存储清理执行响应"""
    root: str
    deleted_files: int
    freed_bytes: int
    dry_run: bool
    message: str


class TTSStorageCategoryStats(BaseModel):
    """TTS 存储分类统计"""
    files: int
    size_bytes: int


class TTSStorageOverviewResponse(BaseModel):
    """TTS 存储概览响应"""
    root: str
    total_files: int
    total_size_bytes: int
    by_category: Dict[str, TTSStorageCategoryStats]  # {"job": {...}, "playground": {...}, "other": {...}}


class TTSStorageOverviewSummary(BaseModel):
    """TTS 存储概览摘要（简化版，用于设置页面）"""
    root: str
    total_files: int
    total_size_bytes: int
    warning: str  # "ok" | "high_usage" | "critical" | "no_root" | "scan_error"
    
    class Config:
        from_attributes = True


# ========== TTS Storage Policy ==========

class TTSStorageCategoryPolicySchema(BaseModel):
    """单个类别的存储策略 Schema"""
    min_keep_days: int = Field(ge=0, description="至少保留多少天内的文件不删（0 表示不按天限制）")
    min_keep_files: int = Field(ge=0, description="至少保留多少个最新文件")
    max_keep_files: Optional[int] = Field(None, ge=0, description="最多允许保留多少个文件（None 表示不限制）")


class TTSStoragePolicyResponse(BaseModel):
    """TTS 存储策略响应"""
    name: str
    playground: TTSStorageCategoryPolicySchema
    job: TTSStorageCategoryPolicySchema
    other: TTSStorageCategoryPolicySchema


# ========== TTS Storage Auto Cleanup ==========

class TTSStorageAutoRunRequest(BaseModel):
    """TTS 存储自动清理运行请求"""
    dry_run: Optional[bool] = Field(None, description="覆盖配置中的 AUTO_DRY_RUN")
    force: bool = Field(False, description="是否忽略 min_interval / warning_level 等约束")


class TTSStorageAutoRunResponse(BaseModel):
    """TTS 存储自动清理运行响应"""
    success: bool
    status: str  # "success" / "skipped" / "failed"
    reason: Optional[str]
    deleted_files_count: int
    freed_bytes: int
    dry_run: bool
    started_at: datetime
    finished_at: datetime
    message: str

# 修复前向引用
TTSSettingsResponse.model_rebuild()

