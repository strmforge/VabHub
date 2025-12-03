"""
阅读中心统一 Schema
"""
from datetime import datetime
from typing import Optional, Dict, Any, Literal, List
from pydantic import BaseModel

from app.models.enums.reading_media_type import ReadingMediaType


# 阅读状态枚举
ReadingStatus = Literal['not_started', 'in_progress', 'finished']

# 活动类型枚举
ActivityType = Literal['read', 'listen', 'update']


class ReadingOngoingItem(BaseModel):
    """正在进行的阅读项（增强版）"""
    media_type: ReadingMediaType

    # 通用字段
    item_id: int  # 该类型下的主键：比如 ebook_id / audiobook_id / manga_series_id
    title: str
    sub_title: Optional[str] = None  # 作者/系列等
    cover_url: Optional[str] = None
    source_label: Optional[str] = None  # 来源/子系统，比如 "小说中心" / "有声书" / "漫画"

    # 进度 / 状态
    progress_label: str  # 如 "第 12 章 · 45%" / "第 3 集 · 12:34 / 30:00" / "第 5 话 · 第 8 页"
    progress_percent: Optional[float] = None  # 0-100 进度百分比
    status: ReadingStatus = 'in_progress'  # 阅读状态
    is_finished: bool
    last_read_at: datetime
    last_activity_at: Optional[datetime] = None  # 最近活动时间
    update_reason: Optional[str] = None  # 更新原因：new_chapter, new_audiobook, progress

    # 跳转信息
    route_name: str  # 前端路由名称，例如 "NovelReader" / "WorkDetail" / "MangaReaderPage"
    route_params: Dict[str, Any]  # 前端路由参数：{"ebookId": 1} / {"series_id": 2, "chapter_id": 20}


class ReadingHistoryItem(BaseModel):
    """阅读历史项（增强版）"""
    media_type: ReadingMediaType

    item_id: int
    title: str
    sub_title: Optional[str] = None
    cover_url: Optional[str] = None
    source_label: Optional[str] = None

    last_position_label: str  # 最后阅读位置描述
    progress_percent: Optional[float] = None  # 0-100 进度百分比
    status: ReadingStatus = 'in_progress'  # 阅读状态
    is_finished: bool
    last_read_at: datetime
    last_activity_at: Optional[datetime] = None

    # 跳转信息
    route_name: str
    route_params: Dict[str, Any]


class ReadingActivityItem(BaseModel):
    """阅读活动项（时间线用）"""
    media_type: ReadingMediaType
    
    item_id: int
    title: str
    sub_title: Optional[str] = None
    cover_url: Optional[str] = None
    
    status: ReadingStatus
    activity_type: ActivityType  # read / listen / update
    activity_label: str  # 活动描述，如 "阅读了第 12 章" / "收听了 30 分钟"
    occurred_at: datetime
    
    # 跳转信息
    route_name: str
    route_params: Dict[str, Any]


class ReadingStats(BaseModel):
    """阅读统计（增强版）"""
    ongoing_count: int
    finished_count: int  # 总完成数
    finished_count_recent_30d: int
    favorites_count: int  # 收藏数
    recent_activity_count: int  # 最近7天有活动的数量
    by_type: Dict[str, Dict[str, int]]  # {"NOVEL": {"ongoing": 3, "finished": 5, "recent_finished": 1}, ...}


class ReadingShelfItem(BaseModel):
    """书架项"""
    media_type: ReadingMediaType

    # 通用字段
    item_id: int
    title: str
    sub_title: Optional[str] = None
    cover_url: Optional[str] = None
    source_label: Optional[str] = None

    # 最近阅读信息（如果有）
    last_position_label: Optional[str] = None
    progress_percent: Optional[float] = None
    status: ReadingStatus = 'not_started'
    is_finished: bool = False
    last_read_at: Optional[datetime] = None

    # 跳转信息
    route_name: str
    route_params: Dict[str, Any]
