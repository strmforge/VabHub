"""
搜索相关 Schema（Phase 9）
定义 SearchQuery 和 SearchResultItem DTO
"""

from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """搜索查询参数"""
    keyword: Optional[str] = None
    category: Optional[str] = None
    media_type: Optional[str] = Field(None, description="媒体类型：movie/tv/anime/music/ebook")
    site_ids: Optional[List[str]] = None
    hr_filter: Literal["any", "exclude_hr", "hr_only"] = "any"
    min_seeders: Optional[int] = None
    max_seeders: Optional[int] = None
    min_size_gb: Optional[float] = None
    max_size_gb: Optional[float] = None
    sort: Literal["default", "seeders", "published_at", "size"] = "default"
    limit: int = 100
    offset: int = 0


class SearchResultItem(BaseModel):
    """搜索结果项"""
    site_id: str
    torrent_id: str
    title_raw: str
    size_bytes: Optional[int] = None
    size_gb: Optional[float] = None  # 计算字段
    seeders: int = 0
    leechers: int = 0
    published_at: Optional[datetime] = None
    is_hr: bool = False
    is_free: bool = False
    is_half_free: bool = False
    is_deleted: bool = False
    category: Optional[str] = None
    media_type: Optional[str] = Field(None, description="媒体类型：movie/tv/anime/music/ebook")
    
    # Local Intel 状态（可选）
    intel_site_status: Optional[str] = None  # OK, THROTTLED, ERROR, UNKNOWN
    intel_hr_status: Optional[str] = None  # SAFE, ACTIVE, RISK, UNKNOWN
    
    # 搜索结果来源（可选）
    source: Optional[Literal["local", "external"]] = Field(None, description="搜索结果来源：local=本地索引，external=外部索引")
    
    # 用于下载的字段（可选）
    magnet_link: Optional[str] = None
    torrent_url: Optional[str] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        # 自动计算 size_gb
        if self.size_bytes and not self.size_gb:
            self.size_gb = round(self.size_bytes / (1024 ** 3), 2)

