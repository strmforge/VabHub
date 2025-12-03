"""
Torrent Index Repository Protocol and Record Types (Phase 9)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional, Protocol, List


@dataclass
class TorrentIndexRecord:
    """Torrent Index 记录"""
    id: int | None
    site_id: str
    torrent_id: str
    title_raw: str
    title_clean: str | None
    category: str | None
    is_hr: bool
    is_free: bool
    is_half_free: bool
    size_bytes: int | None
    seeders: int
    leechers: int
    completed: int | None
    published_at: datetime | None
    last_seen_at: datetime
    is_deleted: bool
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass
class TorrentIndexCreate:
    """用于创建/更新 Torrent Index 的数据结构"""
    site_id: str
    torrent_id: str
    title_raw: str
    title_clean: str | None = None
    category: str | None = None
    is_hr: bool = False
    is_free: bool = False
    is_half_free: bool = False
    size_bytes: int | None = None
    seeders: int = 0
    leechers: int = 0
    completed: int | None = None
    published_at: datetime | None = None
    last_seen_at: datetime | None = None


@dataclass
class TorrentSearchParams:
    """搜索参数"""
    keyword: str | None = None
    category: str | None = None
    site_ids: List[str] | None = None
    hr_filter: str = "any"  # "any", "exclude_hr", "hr_only"
    min_seeders: int | None = None
    max_seeders: int | None = None
    min_size_bytes: int | None = None
    max_size_bytes: int | None = None
    sort: str = "default"  # "default", "seeders", "published_at", "size"
    limit: int = 100
    offset: int = 0
    exclude_deleted: bool = True


class TorrentIndexRepository(Protocol):
    """Torrent Index Repository 协议"""
    
    async def upsert_many(self, rows: List[TorrentIndexCreate]) -> int:
        """
        批量插入或更新 Torrent Index 记录
        
        Args:
            rows: 要插入/更新的记录列表
            
        Returns:
            实际插入/更新的记录数
        """
        ...
    
    async def mark_deleted(
        self,
        site_id: str,
        torrent_id: str,
        deleted_at: datetime | None = None
    ) -> bool:
        """
        标记种子为已删除
        
        Args:
            site_id: 站点ID
            torrent_id: 种子ID
            deleted_at: 删除时间（如果为None，使用当前时间）
            
        Returns:
            是否成功标记
        """
        ...
    
    async def query_for_search(
        self,
        params: TorrentSearchParams
    ) -> List[TorrentIndexRecord]:
        """
        根据搜索参数查询 Torrent Index
        
        Args:
            params: 搜索参数
            
        Returns:
            匹配的记录列表
        """
        ...
    
    async def get_by_site_and_tid(
        self,
        site_id: str,
        torrent_id: str
    ) -> Optional[TorrentIndexRecord]:
        """
        根据站点ID和种子ID获取记录
        
        Args:
            site_id: 站点ID
            torrent_id: 种子ID
            
        Returns:
            记录或None
        """
        ...

