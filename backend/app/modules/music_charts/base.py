"""
榜单抓取器基类

定义榜单抓取的抽象接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from app.models.music_chart_source import MusicChartSource
from app.models.music_chart import MusicChart


@dataclass
class MusicChartItemPayload:
    """榜单条目数据载体"""
    rank: Optional[int] = None
    title: str = ""
    artist_name: str = ""
    album_name: Optional[str] = None
    external_ids: Optional[Dict[str, Any]] = None
    duration_seconds: Optional[int] = None
    cover_url: Optional[str] = None
    external_url: Optional[str] = None
    
    def __post_init__(self):
        if self.external_ids is None:
            self.external_ids = {}


@dataclass
class ChartFetchResult:
    """榜单抓取结果"""
    success: bool = True
    items: List[MusicChartItemPayload] = field(default_factory=list)
    error_message: Optional[str] = None
    fetched_at: Optional[str] = None


class BaseChartFetcher(ABC):
    """
    榜单抓取器基类
    
    所有平台的榜单抓取器都应继承此类并实现 fetch_chart_items 方法。
    """
    
    def __init__(self, source: MusicChartSource):
        self.source = source
        self.config = source.config or {}
    
    @abstractmethod
    async def fetch_chart_items(self, chart: MusicChart) -> ChartFetchResult:
        """
        拉取单个榜单的最新条目
        
        Args:
            chart: 要抓取的榜单
            
        Returns:
            ChartFetchResult: 抓取结果，包含条目列表或错误信息
        """
        pass
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """从配置中获取值"""
        return self.config.get(key, default)
