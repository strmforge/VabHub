"""
漫画阅读进度 Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class MangaReadingProgressBase(BaseModel):
    """阅读进度基础 Schema"""
    series_id: int
    chapter_id: Optional[int] = None
    last_page_index: int = 1
    total_pages: Optional[int] = None
    is_finished: bool = False


class MangaReadingProgressUpdate(MangaReadingProgressBase):
    """更新阅读进度 Schema"""
    pass


class MangaReadingProgressRead(MangaReadingProgressBase):
    """读取阅读进度 Schema"""
    id: int
    last_read_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MangaReadingHistoryItem(BaseModel):
    """漫画阅读历史项 Schema"""
    series_id: int
    series_title: str
    series_cover_url: Optional[str] = None
    source_name: Optional[str] = None

    last_chapter_id: Optional[int] = None
    last_chapter_title: Optional[str] = None
    last_page_index: Optional[int] = None
    total_pages: Optional[int] = None
    is_finished: bool

    last_read_at: datetime

