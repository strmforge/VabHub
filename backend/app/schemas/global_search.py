"""
全局搜索 Schema
SEARCH-1 实现
"""
from typing import Optional, List
from pydantic import BaseModel


class GlobalSearchItem(BaseModel):
    """全局搜索结果项"""
    media_type: str  # movie/series/novel/audiobook/manga/music
    id: str
    title: str
    sub_title: Optional[str] = None
    cover_url: Optional[str] = None
    route_name: Optional[str] = None
    route_params: Optional[dict] = None
    score: Optional[float] = None


class GlobalSearchResponse(BaseModel):
    """全局搜索响应"""
    items: List[GlobalSearchItem]
