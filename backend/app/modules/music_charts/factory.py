"""
榜单抓取器工厂

根据 source.platform 创建对应的抓取器实例。
Phase 3 扩展：支持网易云、Spotify 等平台。
"""

from typing import Optional, Type

from app.models.music_chart_source import MusicChartSource
from app.modules.music_charts.base import BaseChartFetcher
from app.modules.music_charts.dummy_fetcher import DummyChartFetcher
from app.modules.music_charts.rss_fetcher import RSSChartFetcher
from app.modules.music_charts.apple_music_fetcher import AppleMusicChartFetcher
from app.modules.music_charts.netease_fetcher import NeteaseChartFetcher
from app.modules.music_charts.spotify_fetcher import SpotifyChartFetcher


# 平台到抓取器的映射
FETCHER_REGISTRY: dict[str, type[BaseChartFetcher]] = {
    "dummy": DummyChartFetcher,
    "apple_music": AppleMusicChartFetcher,
    "itunes": AppleMusicChartFetcher,  # iTunes 使用相同的抓取器
    "custom_rss": RSSChartFetcher,
    "rsshub": RSSChartFetcher,
    # Phase 3: 新增平台
    "netease": NeteaseChartFetcher,
    "spotify": SpotifyChartFetcher,
    # 占位平台
    "qqmusic": DummyChartFetcher,
}


def register_fetcher(platform: str, fetcher_class: Type[BaseChartFetcher]):
    """
    注册新的抓取器
    
    Args:
        platform: 平台标识
        fetcher_class: 抓取器类
    """
    FETCHER_REGISTRY[platform.lower()] = fetcher_class


def get_chart_fetcher(source: MusicChartSource) -> BaseChartFetcher:
    """
    根据榜单源创建对应的抓取器
    
    Args:
        source: 榜单源
        
    Returns:
        对应平台的抓取器实例
        
    Raises:
        ValueError: 如果平台不支持
    """
    platform = source.platform.lower()
    
    fetcher_class = FETCHER_REGISTRY.get(platform)
    
    if fetcher_class is None:
        # 未知平台，使用 Dummy 抓取器
        fetcher_class = DummyChartFetcher
    
    return fetcher_class(source)


def get_supported_platforms() -> list[str]:
    """获取支持的平台列表"""
    return list(FETCHER_REGISTRY.keys())
