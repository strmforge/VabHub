"""
RSS 榜单抓取器

从 RSS/Atom feed 抓取榜单数据（如 RSSHub 输出）。
"""

from datetime import datetime
from typing import Optional
import re

from loguru import logger

from app.models.music_chart import MusicChart
from app.modules.music_charts.base import (
    BaseChartFetcher,
    MusicChartItemPayload,
    ChartFetchResult,
)


class RSSChartFetcher(BaseChartFetcher):
    """
    RSS 榜单抓取器
    
    从 RSS/Atom feed 抓取榜单数据。
    
    配置项（source.config）：
    - rss_base_url: RSS 服务基础 URL（如 RSSHub 地址）
    - timeout: 请求超时时间（秒）
    """
    
    async def fetch_chart_items(self, chart: MusicChart) -> ChartFetchResult:
        """从 RSS feed 抓取榜单数据"""
        try:
            import httpx
            import feedparser
        except ImportError:
            return ChartFetchResult(
                success=False,
                error_message="缺少依赖: httpx 或 feedparser",
            )
        
        # 构建 RSS URL
        rss_base_url = self.get_config_value("rss_base_url", "https://rsshub.app")
        rss_url = f"{rss_base_url.rstrip('/')}/{chart.chart_key.lstrip('/')}"
        
        timeout = self.get_config_value("timeout", 30)
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(rss_url)
                response.raise_for_status()
                
                feed = feedparser.parse(response.text)
                
                if feed.bozo and not feed.entries:
                    return ChartFetchResult(
                        success=False,
                        error_message=f"RSS 解析失败: {feed.bozo_exception}",
                    )
                
                items = []
                for idx, entry in enumerate(feed.entries[:chart.max_items or 100], start=1):
                    # 尝试从标题解析艺术家和歌曲名
                    title, artist = self._parse_title(entry.get("title", ""))
                    
                    item = MusicChartItemPayload(
                        rank=idx,
                        title=title,
                        artist_name=artist,
                        album_name=None,
                        external_url=entry.get("link"),
                    )
                    items.append(item)
                
                return ChartFetchResult(
                    success=True,
                    items=items,
                    fetched_at=datetime.utcnow().isoformat(),
                )
                
        except httpx.HTTPStatusError as e:
            logger.error(f"RSS 请求失败: {e}")
            return ChartFetchResult(
                success=False,
                error_message=f"HTTP 错误: {e.response.status_code}",
            )
        except Exception as e:
            logger.error(f"RSS 抓取异常: {e}")
            return ChartFetchResult(
                success=False,
                error_message=str(e),
            )
    
    def _parse_title(self, raw_title: str) -> tuple[str, str]:
        """
        从 RSS 条目标题解析歌曲名和艺术家
        
        支持的格式：
        - "艺术家 - 歌曲名"
        - "歌曲名 - 艺术家"
        - "歌曲名"（艺术家为 Unknown）
        """
        if not raw_title:
            return "Unknown", "Unknown"
        
        # 尝试按 " - " 分割
        if " - " in raw_title:
            parts = raw_title.split(" - ", 1)
            # 假设第一部分是艺术家
            return parts[1].strip(), parts[0].strip()
        
        # 尝试按 "-" 分割
        if "-" in raw_title:
            parts = raw_title.split("-", 1)
            return parts[1].strip(), parts[0].strip()
        
        return raw_title.strip(), "Unknown"
