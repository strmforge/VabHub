"""
小说中心聚合 Schema

用于小说中心页面的聚合数据展示
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class NovelCenterEBookSummary(BaseModel):
    """EBook 的精简信息（列表用）"""
    id: int
    title: str
    original_title: Optional[str] = None
    author: Optional[str] = None
    series: Optional[str] = None
    language: Optional[str] = None
    updated_at: datetime


class NovelCenterListeningProgress(BaseModel):
    """听书进度"""
    has_progress: bool
    is_finished: bool
    progress_percent: float  # 0.0 ~ 100.0
    current_file_id: Optional[int] = None
    current_chapter_title: Optional[str] = None
    last_played_at: Optional[datetime] = None


class NovelCenterReadingProgress(BaseModel):
    """阅读进度"""
    has_progress: bool
    is_finished: bool
    progress_percent: float  # 0.0 ~ 100.0
    current_chapter_index: Optional[int] = None
    current_chapter_title: Optional[str] = None
    last_read_at: Optional[datetime] = None


class NovelCenterItem(BaseModel):
    """小说中心聚合项"""
    ebook: NovelCenterEBookSummary
    
    # 有声书 / TTS
    has_audiobook: bool
    has_tts_audiobook: bool
    
    # TTS 状态（简化版）
    last_tts_job_status: Optional[str] = None  # queued/running/success/partial/failed
    last_tts_job_at: Optional[datetime] = None
    
    # 用户听书进度
    listening: NovelCenterListeningProgress
    
    # 用户阅读进度
    reading: NovelCenterReadingProgress


class NovelCenterListResponse(BaseModel):
    """小说中心列表响应"""
    items: List[NovelCenterItem]
    total: int
    page: int
    page_size: int
    total_pages: int

