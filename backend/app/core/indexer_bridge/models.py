"""
Data models shared by the Indexer Bridge layer.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class ExternalIndexerTorrentResult:
    """Represents a single torrent row returned by an external indexer."""

    site_id: str
    torrent_id: str
    title: str
    description: Optional[str] = None
    imdb_id: Optional[str] = None
    douban_id: Optional[str] = None
    tmdb_id: Optional[str] = None
    size_bytes: Optional[int] = None
    seeders: int = 0
    leechers: int = 0
    completed: int = 0
    published_at: Optional[datetime] = None
    freedate: Optional[datetime] = None
    is_hr: bool = False
    is_free: bool = False
    is_half_free: bool = False
    category: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    download_url: Optional[str] = None
    page_url: Optional[str] = None
    upload_volume_factor: Optional[float] = None
    download_volume_factor: Optional[float] = None
    site_name: Optional[str] = None
    site_priority: int = 0
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def size_gb(self) -> Optional[float]:
        if self.size_bytes is None:
            return None
        return round(self.size_bytes / (1024 ** 3), 2)


@dataclass
class ExternalIndexerTorrentDetail(ExternalIndexerTorrentResult):
    """Extended information for a torrent row."""

    files: List[str] = field(default_factory=list)
    screenshots: List[str] = field(default_factory=list)


@dataclass
class ExternalIndexerSiteConfig:
    """External site metadata as seen by the bridge."""

    site_id: str
    name: str
    domain: Optional[str] = None
    url: Optional[str] = None
    cookie: Optional[str] = None
    api_key: Optional[str] = None
    token: Optional[str] = None
    user_agent: Optional[str] = None
    proxy_enabled: bool = False
    timeout: int = 15
    schema: Optional[str] = None
    parser: Optional[str] = None
    search_config: Dict[str, Any] = field(default_factory=dict)
    category_mapping: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    enabled: bool = True
    raw_config: Dict[str, Any] = field(default_factory=dict)

