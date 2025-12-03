"""
统一媒体库预览 Schema
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel


class WorkFormats(BaseModel):
    """作品形态概览"""
    has_ebook: bool = False
    has_audiobook: bool = False
    has_comic: bool = False
    has_music: bool = False  # 预留，当前暂不实现


class LibraryPreviewItem(BaseModel):
    """统一媒体预览项"""
    
    id: int
    media_type: str  # "movie", "tv", "anime", "ebook" 等
    title: str
    year: Optional[int] = None
    cover_url: Optional[str] = None
    created_at: datetime
    extra: Optional[Dict[str, Any]] = None  # 媒体类型特有的额外信息
    work_formats: Optional[WorkFormats] = None  # 作品形态概览（仅对 ebook 类型有意义）
    
    class Config:
        from_attributes = True


class LibraryPreviewResponse(BaseModel):
    """统一媒体库预览响应"""
    
    items: List[LibraryPreviewItem]
    total: int
    page: int
    page_size: int


# ========== Library Settings Schema ==========

class InboxSettings(BaseModel):
    """收件箱设置"""
    inbox_root: str
    enabled: bool
    enabled_media_types: List[str]
    detection_min_score: float
    scan_max_items: int
    last_run_at: Optional[str] = None  # ISO 格式字符串
    last_run_status: str  # "never" | "success" | "partial" | "failed" | "empty"
    last_run_summary: Optional[str] = None
    pending_warning: Optional[str] = None  # "never_run" | "last_run_failed" | "too_long_without_run" | null


class LibraryRootsSettings(BaseModel):
    """媒体库根目录设置"""
    movie: str
    tv: str
    anime: str
    short_drama: Optional[str] = None
    ebook: str
    comic: Optional[str] = None
    music: Optional[str] = None


class LibrarySettingsResponse(BaseModel):
    """媒体库设置响应"""
    inbox: InboxSettings
    library_roots: LibraryRootsSettings

