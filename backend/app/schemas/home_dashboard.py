"""
首页仪表盘 Schema
HOME-1 实现
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel


class HomeQuickStat(BaseModel):
    """首页快速统计项"""
    label: str
    value: int
    icon: Optional[str] = None  # 前端图标用，mdi- 开头
    color: Optional[str] = None  # primary / secondary / success / error / info / warning


class HomeUpNextItem(BaseModel):
    """继续阅读/观看项"""
    media_type: str  # "movie" | "series" | "novel" | "audiobook" | "manga" | "music"
    title: str
    sub_title: Optional[str] = None  # 作者 / 艺人 / 系列
    cover_url: Optional[str] = None
    progress_percent: Optional[int] = None
    last_activity_at: Optional[datetime] = None
    route_name: Optional[str] = None
    route_params: Optional[dict] = None


class HomeRecentItem(BaseModel):
    """最近新增项"""
    media_type: str
    title: str
    sub_title: Optional[str] = None
    cover_url: Optional[str] = None
    created_at: Optional[datetime] = None
    route_name: Optional[str] = None
    route_params: Optional[dict] = None


class HomeRunnerStatus(BaseModel):
    """Runner 状态"""
    name: str            # "Novel TTS Runner"
    key: str             # "tts_worker", "tts_cleanup", "manga_follow", "music_chart_sync", ...
    last_run_at: Optional[datetime] = None
    last_status: Optional[str] = None  # "success" | "failed" | "unknown"
    last_message: Optional[str] = None


class HomeTaskSummary(BaseModel):
    """任务汇总"""
    total_running: int
    total_failed_recent: int
    total_waiting: int


class HomeDashboardResponse(BaseModel):
    """首页仪表盘响应"""
    stats: List[HomeQuickStat]
    up_next: List[HomeUpNextItem]
    recent_items: List[HomeRecentItem]
    runners: List[HomeRunnerStatus]
    tasks: HomeTaskSummary
