"""
有声书中心聚合 Schema
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class AudiobookCenterWorkSummary(BaseModel):
    """有声书中心作品摘要"""
    ebook_id: int
    title: str
    original_title: Optional[str] = None
    author: Optional[str] = None
    series: Optional[str] = None
    language: Optional[str] = None
    updated_at: datetime


class AudiobookCenterListeningProgress(BaseModel):
    """听书进度"""
    has_progress: bool
    is_finished: bool
    progress_percent: float  # 0.0 ~ 100.0
    last_played_at: Optional[datetime] = None
    current_file_id: Optional[int] = None
    current_chapter_title: Optional[str] = None


class AudiobookCenterReadingProgress(BaseModel):
    """阅读进度"""
    has_progress: bool
    is_finished: bool
    progress_percent: float  # 0.0 ~ 100.0
    current_chapter_index: Optional[int] = None
    current_chapter_title: Optional[str] = None
    last_read_at: Optional[datetime] = None


class AudiobookCenterTTSStatus(BaseModel):
    """TTS 状态"""
    has_audiobook: bool  # 是否有任何 AudiobookFile
    has_tts_audiobook: bool  # 是否有 TTS 生成的 AudiobookFile
    last_job_status: Optional[str] = None  # queued/running/success/partial/failed
    last_job_at: Optional[datetime] = None


class AudiobookCenterItem(BaseModel):
    """有声书中心聚合项"""
    work: AudiobookCenterWorkSummary
    tts: AudiobookCenterTTSStatus
    listening: AudiobookCenterListeningProgress
    reading: AudiobookCenterReadingProgress  # 阅读进度


class AudiobookCenterListResponse(BaseModel):
    """有声书中心列表响应"""
    items: List[AudiobookCenterItem]
    total: int
    page: int
    page_size: int
    total_pages: int

