"""
小说阅读器相关 Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class NovelChapterSummary(BaseModel):
    """章节摘要"""
    index: int  # 章节索引（从 0 开始）
    title: str  # 章节标题
    length: Optional[int] = None  # 章节字数/长度（可选）


class NovelChapterTextResponse(BaseModel):
    """章节正文响应"""
    ebook_id: int
    chapter_index: int
    title: str
    content: str  # 纯文本内容


class UserNovelReadingProgressResponse(BaseModel):
    """用户阅读进度响应"""
    ebook_id: int
    current_chapter_index: int
    chapter_offset: int
    is_finished: bool
    last_read_at: datetime


class UpdateNovelReadingProgressRequest(BaseModel):
    """更新阅读进度请求"""
    current_chapter_index: int
    chapter_offset: int
    is_finished: Optional[bool] = None


class NovelSearchHit(BaseModel):
    """书内搜索结果命中"""
    chapter_index: int  # 章节索引（从 0 开始）
    chapter_title: Optional[str] = None  # 章节标题
    snippet: str  # 命中片段（前后各约 40 字，关键字居中）

