"""
Dummy 榜单抓取器

用于开发环境和测试，返回固定的模拟数据。
"""

from datetime import datetime
from typing import List

from app.models.music_chart import MusicChart
from app.modules.music_charts.base import (
    BaseChartFetcher,
    MusicChartItemPayload,
    ChartFetchResult,
)


class DummyChartFetcher(BaseChartFetcher):
    """
    Dummy 榜单抓取器
    
    返回固定的模拟数据，用于开发和测试。
    可以通过 source.config 中的 mock_data 字段自定义返回数据。
    """
    
    async def fetch_chart_items(self, chart: MusicChart) -> ChartFetchResult:
        """返回模拟的榜单数据"""
        
        # 检查是否有自定义 mock_data
        mock_data = self.get_config_value("mock_data")
        if mock_data and isinstance(mock_data, list):
            items = [
                MusicChartItemPayload(
                    rank=item.get("rank"),
                    title=item.get("title", "Unknown"),
                    artist_name=item.get("artist_name", "Unknown"),
                    album_name=item.get("album_name"),
                    duration_seconds=item.get("duration_seconds"),
                    cover_url=item.get("cover_url"),
                    external_url=item.get("external_url"),
                )
                for item in mock_data
            ]
            return ChartFetchResult(
                success=True,
                items=items,
                fetched_at=datetime.utcnow().isoformat(),
            )
        
        # 默认模拟数据
        default_items: List[MusicChartItemPayload] = [
            MusicChartItemPayload(
                rank=1,
                title="APT.",
                artist_name="ROSÉ & Bruno Mars",
                album_name="APT.",
                duration_seconds=170,
                external_ids={"isrc": "USUG12403456"},
            ),
            MusicChartItemPayload(
                rank=2,
                title="Die With A Smile",
                artist_name="Lady Gaga & Bruno Mars",
                album_name="Die With A Smile",
                duration_seconds=252,
                external_ids={"isrc": "USUG12403457"},
            ),
            MusicChartItemPayload(
                rank=3,
                title="Birds of a Feather",
                artist_name="Billie Eilish",
                album_name="HIT ME HARD AND SOFT",
                duration_seconds=210,
                external_ids={"isrc": "USUG12403458"},
            ),
            MusicChartItemPayload(
                rank=4,
                title="Espresso",
                artist_name="Sabrina Carpenter",
                album_name="Short n' Sweet",
                duration_seconds=175,
                external_ids={"isrc": "USUG12403459"},
            ),
            MusicChartItemPayload(
                rank=5,
                title="Good Luck, Babe!",
                artist_name="Chappell Roan",
                album_name="Good Luck, Babe!",
                duration_seconds=218,
                external_ids={"isrc": "USUG12403460"},
            ),
            MusicChartItemPayload(
                rank=6,
                title="Taste",
                artist_name="Sabrina Carpenter",
                album_name="Short n' Sweet",
                duration_seconds=157,
            ),
            MusicChartItemPayload(
                rank=7,
                title="LUTHER",
                artist_name="Kendrick Lamar & SZA",
                album_name="GNX",
                duration_seconds=199,
            ),
            MusicChartItemPayload(
                rank=8,
                title="That's So True",
                artist_name="Gracie Abrams",
                album_name="The Secret of Us",
                duration_seconds=185,
            ),
            MusicChartItemPayload(
                rank=9,
                title="Sailor Song",
                artist_name="Gigi Perez",
                album_name="Sailor Song",
                duration_seconds=203,
            ),
            MusicChartItemPayload(
                rank=10,
                title="A Bar Song (Tipsy)",
                artist_name="Shaboozey",
                album_name="Where I've Been, Isn't Where I'm Going",
                duration_seconds=179,
            ),
        ]
        
        # 根据 chart.max_items 限制返回数量
        max_items = chart.max_items or 100
        items = default_items[:max_items]
        
        return ChartFetchResult(
            success=True,
            items=items,
            fetched_at=datetime.utcnow().isoformat(),
        )
