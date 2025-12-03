"""
小说 Inbox 相关 Schema
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class NovelInboxLogItem(BaseModel):
    """小说 Inbox 导入日志项"""
    id: int
    original_path: str
    status: str
    reason: Optional[str] = None
    error_message: Optional[str] = None
    ebook_id: Optional[int] = None
    ebook_title: Optional[str] = None
    ebook_author: Optional[str] = None
    file_size: Optional[int] = None
    file_mtime: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class NovelInboxLogListResponse(BaseModel):
    """小说 Inbox 日志列表响应"""
    items: List[NovelInboxLogItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class NovelInboxScanResult(BaseModel):
    """小说 Inbox 扫描结果"""
    scanned_files: int
    imported_count: int
    skipped_already_imported: int
    skipped_failed_before: int
    skipped_unsupported: int
    tts_jobs_created: int
    failed_count: int

