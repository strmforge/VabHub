"""
音乐库相关 Schema 定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MusicArtistRead(BaseModel):
    """艺术家信息"""
    id: int
    name: str
    alt_names: Optional[List[str]] = None
    country: Optional[str] = None
    album_count: int = 0
    track_count: int = 0
    
    class Config:
        from_attributes = True


class MusicAlbumRead(BaseModel):
    """专辑信息"""
    id: int
    title: str
    artist_id: Optional[int] = None
    artist_name: Optional[str] = None
    year: Optional[int] = None
    cover_url: Optional[str] = None
    track_count: int = 0
    total_duration_seconds: Optional[int] = None
    genre: Optional[str] = None
    
    class Config:
        from_attributes = True


class MusicTrackRead(BaseModel):
    """曲目信息"""
    id: int
    title: str
    artist_id: Optional[int] = None
    artist_name: Optional[str] = None
    album_id: Optional[int] = None
    album_title: Optional[str] = None
    track_number: Optional[int] = None
    disc_number: Optional[int] = None
    duration_seconds: Optional[int] = None
    bitrate_kbps: Optional[int] = None
    format: Optional[str] = None
    file_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class MusicFileRead(BaseModel):
    """音乐文件信息"""
    id: int
    music_id: int
    file_path: str
    file_size_bytes: Optional[int] = None
    file_size_mb: Optional[float] = None
    format: str
    duration_seconds: Optional[int] = None
    bitrate_kbps: Optional[int] = None
    sample_rate_hz: Optional[int] = None
    channels: Optional[int] = None
    track_number: Optional[int] = None
    disc_number: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class MusicAlbumDetail(BaseModel):
    """专辑详情（包含曲目列表）"""
    id: int
    title: str
    artist_id: Optional[int] = None
    artist_name: Optional[str] = None
    album_artist: Optional[str] = None
    year: Optional[int] = None
    cover_url: Optional[str] = None
    genre: Optional[str] = None
    track_count: int = 0
    total_duration_seconds: Optional[int] = None
    tracks: List[MusicTrackRead] = []
    
    class Config:
        from_attributes = True


class MusicListResponse(BaseModel):
    """音乐列表响应"""
    items: List[MusicAlbumRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class MusicArtistListResponse(BaseModel):
    """艺术家列表响应"""
    items: List[MusicArtistRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class MusicTrackListResponse(BaseModel):
    """曲目列表响应"""
    items: List[MusicTrackRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class MusicStatsResponse(BaseModel):
    """音乐库统计"""
    total_artists: int
    total_albums: int
    total_tracks: int
    total_files: int
    total_size_mb: float
    total_duration_seconds: Optional[int] = None


# ========== MC2: 榜单相关 Schema ==========

class MusicChartSourceCreate(BaseModel):
    """创建榜单源"""
    platform: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    config: Optional[dict] = None
    is_enabled: bool = True
    icon_url: Optional[str] = None


class MusicChartSourceUpdate(BaseModel):
    """更新榜单源"""
    display_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    config: Optional[dict] = None
    is_enabled: Optional[bool] = None
    icon_url: Optional[str] = None


class MusicChartSourceRead(BaseModel):
    """榜单源信息"""
    id: int
    platform: str
    display_name: str
    description: Optional[str] = None
    config: Optional[dict] = None
    is_enabled: bool
    icon_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MusicChartSourceListResponse(BaseModel):
    """榜单源列表响应"""
    items: List[MusicChartSourceRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class MusicChartCreate(BaseModel):
    """创建榜单"""
    source_id: int
    chart_key: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    region: Optional[str] = "CN"
    chart_type: Optional[str] = "hot"
    is_enabled: bool = True
    fetch_interval_minutes: int = 60
    max_items: int = 100


class MusicChartUpdate(BaseModel):
    """更新榜单"""
    display_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    region: Optional[str] = None
    chart_type: Optional[str] = None
    is_enabled: Optional[bool] = None
    fetch_interval_minutes: Optional[int] = None
    max_items: Optional[int] = None


class MusicChartRead(BaseModel):
    """榜单信息"""
    id: int
    source_id: int
    chart_key: str
    display_name: str
    description: Optional[str] = None
    region: Optional[str] = None
    chart_type: Optional[str] = None
    is_enabled: bool
    last_fetched_at: Optional[datetime] = None
    fetch_interval_minutes: int
    max_items: int
    created_at: datetime
    updated_at: datetime
    # 关联信息
    source_platform: Optional[str] = None
    source_display_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class MusicChartListResponse(BaseModel):
    """榜单列表响应"""
    items: List[MusicChartRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class MusicChartItemRead(BaseModel):
    """榜单条目信息"""
    id: int
    chart_id: int
    rank: Optional[int] = None
    title: str
    artist_name: str
    album_name: Optional[str] = None
    external_ids: Optional[dict] = None
    duration_seconds: Optional[int] = None
    cover_url: Optional[str] = None
    external_url: Optional[str] = None
    first_seen_at: datetime
    last_seen_at: datetime
    
    class Config:
        from_attributes = True


class MusicChartItemListResponse(BaseModel):
    """榜单条目列表响应"""
    items: List[MusicChartItemRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class MusicChartDetailRead(BaseModel):
    """榜单详情（包含条目）"""
    id: int
    source_id: int
    chart_key: str
    display_name: str
    description: Optional[str] = None
    region: Optional[str] = None
    chart_type: Optional[str] = None
    is_enabled: bool
    last_fetched_at: Optional[datetime] = None
    source_platform: Optional[str] = None
    source_display_name: Optional[str] = None
    items: List[MusicChartItemRead] = []
    
    class Config:
        from_attributes = True


# ========== MC2: 用户订阅相关 Schema ==========

class UserMusicSubscriptionCreate(BaseModel):
    """创建用户音乐订阅"""
    subscription_type: str = Field(default="chart", description="订阅类型: chart/keyword")
    
    # 榜单订阅字段（仅chart类型使用）
    chart_id: Optional[int] = Field(None, description="榜单ID（仅chart类型）")
    
    # 关键字订阅字段（仅keyword类型使用）
    music_query: Optional[str] = Field(None, description="搜索关键字（仅keyword类型）")
    music_site: Optional[str] = Field(None, description="指定站点（可选）")
    music_quality: Optional[str] = Field(None, description="质量偏好（FLAC/MP3/320等）")
    
    # 通用字段
    auto_search: bool = True
    auto_download: bool = False
    max_new_tracks_per_run: int = Field(default=10, ge=1, le=100)
    quality_preference: Optional[str] = "flac"
    preferred_sites: Optional[str] = None
    
    # 安全策略字段
    allow_hr: bool = Field(default=False, description="是否允许 HR/H&R")
    allow_h3h5: bool = Field(default=False, description="是否允许 H3/H5 等扩展规则")
    strict_free_only: bool = Field(default=False, description="只下载 free/促销种")


class UserMusicSubscriptionUpdate(BaseModel):
    """更新用户音乐订阅"""
    subscription_type: Optional[str] = Field(None, description="订阅类型: chart/keyword")
    
    # 榜单订阅字段（仅chart类型使用）
    chart_id: Optional[int] = Field(None, description="榜单ID（仅chart类型）")
    
    # 关键字订阅字段（仅keyword类型使用）
    music_query: Optional[str] = Field(None, description="搜索关键字（仅keyword类型）")
    music_site: Optional[str] = Field(None, description="指定站点（可选）")
    music_quality: Optional[str] = Field(None, description="质量偏好（FLAC/MP3/320等）")
    
    # 通用字段
    status: Optional[str] = None  # active / paused
    auto_search: Optional[bool] = None
    auto_download: Optional[bool] = None
    max_new_tracks_per_run: Optional[int] = Field(None, ge=1, le=100)
    quality_preference: Optional[str] = None
    preferred_sites: Optional[str] = None
    
    # 安全策略字段
    allow_hr: Optional[bool] = Field(None, description="是否允许 HR/H&R")
    allow_h3h5: Optional[bool] = Field(None, description="是否允许 H3/H5 等扩展规则")
    strict_free_only: Optional[bool] = Field(None, description="只下载 free/促销种")


class UserMusicSubscriptionRead(BaseModel):
    """用户音乐订阅信息"""
    id: int
    user_id: int
    subscription_type: str  # chart/keyword
    
    # 榜单订阅字段（仅chart类型使用）
    chart_id: Optional[int] = None
    
    # 关键字订阅字段（仅keyword类型使用）
    music_query: Optional[str] = None
    music_site: Optional[str] = None
    music_quality: Optional[str] = None
    
    # 通用字段
    status: str
    auto_search: bool
    auto_download: bool
    max_new_tracks_per_run: int
    quality_preference: Optional[str] = None
    preferred_sites: Optional[str] = None
    
    # 安全策略字段
    allow_hr: bool = False
    allow_h3h5: bool = False
    strict_free_only: bool = False
    
    last_run_at: Optional[datetime] = None
    last_run_new_count: Optional[int] = None
    last_run_search_count: Optional[int] = None
    last_run_download_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    # 关联信息
    chart_display_name: Optional[str] = None
    source_platform: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserMusicSubscriptionListResponse(BaseModel):
    """用户音乐订阅列表响应"""
    items: List[UserMusicSubscriptionRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class SubscriptionRunResult(BaseModel):
    """订阅运行结果（原有格式）"""
    subscription_id: int
    new_items_count: int
    search_count: int
    download_count: int
    failed_count: int
    errors: List[str] = []


class MusicAutoLoopResult(BaseModel):
    """音乐订阅自动拉种结果（MUSIC-AUTOLOOP-2 扩展格式）"""
    subscription_id: int
    found_total: int = 0           # 搜到多少候选
    filtered_out: Dict[str, int] = {}  # {"hr": 2, "non_free": 3, ...}
    skipped_existing: int = 0      # 已有任务/已入库跳过的数量
    created_tasks: int = 0         # 新建 DownloadTask 数量
    errors: List[str] = []
    
    # 兼容性字段（映射到原有格式）
    @property
    def search_count(self) -> int:
        return self.found_total
    
    @property
    def new_items_count(self) -> int:
        return self.created_tasks
    
    @property
    def download_count(self) -> int:
        return self.created_tasks
    
    @property
    def failed_count(self) -> int:
        return len(self.errors)


class MusicSubscriptionRunResponse(BaseModel):
    """音乐订阅运行响应（API返回格式）"""
    subscription_id: int
    found_total: int
    filtered_out: Dict[str, int]
    skipped_existing: int
    created_tasks: int
    errors: List[str] = []


class MusicSubscriptionBatchRunResponse(BaseModel):
    """音乐订阅批量运行响应"""
    total_subscriptions: int
    runs: List[MusicSubscriptionRunResponse]
    summary: Dict[str, Any] = {}
    
    class Config:
        extra = "allow"


# ========== MC2/MC3: 下载任务相关 Schema ==========

class MusicDownloadJobRead(BaseModel):
    """音乐下载任务信息（Phase 3 扩展）"""
    id: int
    subscription_id: Optional[int] = None
    chart_item_id: Optional[int] = None
    user_id: int
    search_query: str
    status: str
    
    # PT 搜索结果
    matched_site: Optional[str] = None
    matched_torrent_id: Optional[str] = None
    matched_torrent_name: Optional[str] = None
    matched_torrent_size_bytes: Optional[int] = None
    matched_seeders: Optional[int] = None
    matched_leechers: Optional[int] = None
    matched_free_percent: Optional[int] = None
    quality_score: Optional[float] = None
    search_candidates_count: Optional[int] = None
    
    # 下载相关
    download_client: Optional[str] = None
    download_task_id: Optional[int] = None
    downloader_hash: Optional[str] = None
    downloaded_path: Optional[str] = None
    
    # 导入结果
    music_file_id: Optional[int] = None
    music_id: Optional[int] = None
    is_duplicate: bool = False
    
    # 错误和重试
    last_error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # 时间戳
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 关联信息（前端展示用）
    chart_item_title: Optional[str] = None
    chart_item_artist: Optional[str] = None
    subscription_name: Optional[str] = None
    
    class Config:
        from_attributes = True
    
    @property
    def matched_torrent_size_mb(self) -> Optional[float]:
        """兼容旧字段"""
        if self.matched_torrent_size_bytes:
            return round(self.matched_torrent_size_bytes / (1024 * 1024), 2)
        return None


class MusicDownloadJobListResponse(BaseModel):
    """音乐下载任务列表响应"""
    items: List[MusicDownloadJobRead]
    total: int
    page: int
    page_size: int
    total_pages: int


# ========== MC3: 订阅覆盖统计 ==========

class SubscriptionCoverageStats(BaseModel):
    """订阅覆盖统计"""
    subscription_id: int
    chart_id: int
    total_items: int
    ready_count: int  # 已入库
    downloading_count: int  # 下载中
    queued_count: int  # 已排队（found/submitted）
    not_queued_count: int  # 未处理
    failed_count: int  # 失败
    
    @property
    def coverage_percent(self) -> float:
        if self.total_items == 0:
            return 0.0
        return round(self.ready_count / self.total_items * 100, 1)
