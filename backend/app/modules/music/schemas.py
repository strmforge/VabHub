"""
音乐领域数据模型（Pydantic）
为服务层、API、GraphQL 等提供统一的结构
"""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class MusicTrackSchema(BaseModel):
    """标准化的音乐曲目结构"""

    id: Optional[str] = None
    title: str
    artist: str
    album: Optional[str] = None
    duration: Optional[int] = Field(
        default=None, description="时长（秒）"
    )
    release_date: Optional[str] = None
    genre: List[str] = Field(default_factory=list)
    platform: Optional[str] = None
    external_url: Optional[str] = None
    preview_url: Optional[str] = None
    cover_url: Optional[str] = None
    popularity: Optional[float] = None


class MusicAlbumSchema(BaseModel):
    """音乐专辑结构"""

    id: Optional[str] = None
    title: str
    artist: Optional[str] = None
    platform: Optional[str] = None
    cover_url: Optional[str] = None
    release_date: Optional[str] = None
    track_count: Optional[int] = None


class MusicChartEntry(BaseModel):
    """音乐榜单条目"""

    id: Optional[str] = None
    title: str
    artist: str
    album: Optional[str] = None
    platform: str
    rank: Optional[int] = None
    external_url: Optional[str] = None
    cover_url: Optional[str] = None
    duration: Optional[int] = None
    popularity: Optional[float] = None

    def to_keyword(self) -> str:
        """生成默认的 PT 搜索关键词"""
        parts = [self.artist.strip(), self.title.strip()]
        if self.album:
            parts.append(self.album.strip())
        return " - ".join(filter(None, parts))


class MusicSubscriptionPreview(BaseModel):
    """音乐订阅触发的搜索预览"""

    subscription_id: int
    subscription_title: str
    platform: Optional[str] = None
    preview_queries: List[str] = Field(default_factory=list)
    results_count: int = 0
    generated_at: datetime = Field(default_factory=datetime.utcnow)


