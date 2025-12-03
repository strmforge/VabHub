"""
远程漫画数据 Schema
"""
from datetime import datetime
from typing import List, Optional, Dict

from pydantic import AnyHttpUrl, BaseModel

from app.models.enums.manga_source_type import MangaSourceType


class RemoteMangaSourceInfo(BaseModel):
    """远程漫画源信息（只读，不暴露敏感信息）"""
    id: int
    name: str
    type: MangaSourceType
    is_enabled: bool


class RemoteMangaSeries(BaseModel):
    """远程漫画系列信息"""
    source_id: int
    source_type: MangaSourceType
    remote_id: str  # 源内部 ID
    title: str
    alt_titles: Optional[List[str]] = None
    cover_url: Optional[AnyHttpUrl] = None
    status: Optional[str] = None  # 连载中/已完结等
    authors: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    summary: Optional[str] = None
    # 预载的章节数统计
    chapters_count: Optional[int] = None


class RemoteMangaChapter(BaseModel):
    """远程漫画章节信息"""
    source_id: int
    source_type: MangaSourceType
    series_remote_id: str
    remote_id: str  # 章节自身 ID
    title: str
    number: Optional[float] = None  # 用 float 支持 1.5 之类
    volume: Optional[int] = None
    published_at: Optional[datetime] = None


class RemoteMangaSearchResult(BaseModel):
    """远程漫画搜索结果"""
    total: int
    page: int
    page_size: int
    items: List[RemoteMangaSeries]


class RemoteMangaPage(BaseModel):
    """远程漫画页面信息"""
    index: int  # 从 1 开始
    image_url: Optional[AnyHttpUrl] = None
    # 某些源可能不暴露 URL，而提供内部 ID
    remote_page_id: Optional[str] = None


class SourceSearchResult(BaseModel):
    """单个源的搜索结果"""
    source_id: int
    source_name: str
    source_type: MangaSourceType
    success: bool
    error_message: Optional[str] = None
    result: Optional[RemoteMangaSearchResult] = None


class AggregatedSearchResult(BaseModel):
    """聚合搜索结果"""
    query: str
    total_sources: int
    successful_sources: int
    failed_sources: int
    results_by_source: List[SourceSearchResult]
    # 统计信息
    total_items: int
    # 是否有失败源
    has_failures: bool

