"""
我的书架聚合 Schema

用于"我的书架"页面的聚合数据展示
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class MyShelfWorkSummary(BaseModel):
    """作品摘要"""
    ebook_id: int
    title: str
    original_title: Optional[str] = None
    author: Optional[str] = None
    series: Optional[str] = None
    language: Optional[str] = None
    cover_url: Optional[str] = None  # 如有封面，按项目现有字段填
    updated_at: datetime


class MyShelfReadingProgress(BaseModel):
    """阅读进度"""
    has_progress: bool
    is_finished: bool
    progress_percent: float  # 0.0 ~ 100.0
    current_chapter_index: Optional[int] = None
    current_chapter_title: Optional[str] = None
    last_read_at: Optional[datetime] = None


class MyShelfListeningProgress(BaseModel):
    """听书进度"""
    has_progress: bool
    is_finished: bool
    progress_percent: float  # 0.0 ~ 100.0
    current_file_id: Optional[int] = None
    current_chapter_title: Optional[str] = None
    last_listened_at: Optional[datetime] = None


class MyShelfTTSStatus(BaseModel):
    """TTS 状态"""
    has_audiobook: bool
    has_tts_audiobook: bool
    last_job_status: Optional[str] = None  # queued/running/success/partial/failed
    last_job_at: Optional[datetime] = None


class MyShelfItem(BaseModel):
    """我的书架聚合项"""
    work: MyShelfWorkSummary
    reading: MyShelfReadingProgress
    listening: MyShelfListeningProgress
    tts: MyShelfTTSStatus


class MyShelfListResponse(BaseModel):
    """我的书架列表响应"""
    items: List[MyShelfItem]
    total: int
    page: int
    page_size: int
    total_pages: int

