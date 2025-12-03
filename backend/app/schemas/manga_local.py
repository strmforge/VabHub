"""
本地漫画库 Schema
"""
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, HttpUrl

from app.models.manga_chapter_local import MangaChapterStatus


class MangaSeriesLocalRead(BaseModel):
    """本地漫画系列读取 Schema"""
    id: int
    source_id: int
    remote_series_id: str
    title: str
    alt_titles: Optional[List[str]] = None
    cover_url: Optional[str] = None  # 后端拼好的可访问 URL
    summary: Optional[str] = None
    authors: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    language: Optional[str] = None
    remote_meta: Optional[dict[str, Any]] = None
    is_favorite: bool
    is_hidden: bool
    total_chapters: Optional[int] = None
    downloaded_chapters: Optional[int] = None
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MangaChapterLocalRead(BaseModel):
    """本地漫画章节读取 Schema"""
    id: int
    series_id: int
    remote_chapter_id: str
    title: str
    number: Optional[float] = None
    volume: Optional[int] = None
    published_at: Optional[datetime] = None
    status: MangaChapterStatus
    page_count: Optional[int] = None
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LocalMangaPageRead(BaseModel):
    """本地漫画页面读取 Schema"""
    index: int
    image_url: str  # 相对静态路径，前端可直接使用

