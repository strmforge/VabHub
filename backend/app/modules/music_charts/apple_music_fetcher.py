"""
Apple Music 榜单抓取器

从 Apple Music API 抓取榜单数据。
"""

from datetime import datetime
from typing import Optional

from loguru import logger

from app.models.music_chart import MusicChart
from app.modules.music_charts.base import (
    BaseChartFetcher,
    MusicChartItemPayload,
    ChartFetchResult,
)


class AppleMusicChartFetcher(BaseChartFetcher):
    """
    Apple Music 榜单抓取器
    
    从 Apple Music API 抓取榜单数据。
    
    配置项（source.config）：
    - api_base_url: API 基础 URL（默认为 Apple Music API）
    - storefront: 地区代码（如 cn, us, jp）
    - developer_token: Apple Music API 开发者令牌（可选）
    - timeout: 请求超时时间（秒）
    
    注意：Apple Music API 需要开发者令牌才能访问完整数据。
    如果没有令牌，此抓取器将返回模拟数据。
    """
    
    async def fetch_chart_items(self, chart: MusicChart) -> ChartFetchResult:
        """从 Apple Music API 抓取榜单数据"""
        
        developer_token = self.get_config_value("developer_token")
        
        if not developer_token:
            # 没有令牌，返回模拟数据
            logger.warning("Apple Music API 未配置 developer_token，返回模拟数据")
            return self._get_mock_data(chart)
        
        try:
            import httpx
        except ImportError:
            return ChartFetchResult(
                success=False,
                error_message="缺少依赖: httpx",
            )
        
        storefront = self.get_config_value("storefront", chart.region or "cn")
        api_base_url = self.get_config_value(
            "api_base_url", 
            "https://api.music.apple.com/v1"
        )
        timeout = self.get_config_value("timeout", 30)
        
        # 构建 API URL
        # chart_key 应该是 Apple Music 的 playlist ID 或 chart ID
        api_url = f"{api_base_url}/catalog/{storefront}/charts"
        
        headers = {
            "Authorization": f"Bearer {developer_token}",
            "Content-Type": "application/json",
        }
        
        params = {
            "types": "songs",
            "chart": chart.chart_key,
            "limit": min(chart.max_items or 100, 200),
        }
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(api_url, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                items = []
                songs = data.get("results", {}).get("songs", [])
                
                for idx, song_data in enumerate(songs, start=1):
                    for song in song_data.get("data", []):
                        attrs = song.get("attributes", {})
                        
                        item = MusicChartItemPayload(
                            rank=idx,
                            title=attrs.get("name", "Unknown"),
                            artist_name=attrs.get("artistName", "Unknown"),
                            album_name=attrs.get("albumName"),
                            duration_seconds=attrs.get("durationInMillis", 0) // 1000 if attrs.get("durationInMillis") else None,
                            cover_url=attrs.get("artwork", {}).get("url", "").replace("{w}", "300").replace("{h}", "300") if attrs.get("artwork") else None,
                            external_url=attrs.get("url"),
                            external_ids={
                                "apple_music_id": song.get("id"),
                                "isrc": attrs.get("isrc"),
                            },
                        )
                        items.append(item)
                        idx += 1
                
                return ChartFetchResult(
                    success=True,
                    items=items[:chart.max_items or 100],
                    fetched_at=datetime.utcnow().isoformat(),
                )
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Apple Music API 请求失败: {e}")
            return ChartFetchResult(
                success=False,
                error_message=f"HTTP 错误: {e.response.status_code}",
            )
        except Exception as e:
            logger.error(f"Apple Music 抓取异常: {e}")
            return ChartFetchResult(
                success=False,
                error_message=str(e),
            )
    
    def _get_mock_data(self, chart: MusicChart) -> ChartFetchResult:
        """返回模拟的 Apple Music 榜单数据"""
        mock_items = [
            MusicChartItemPayload(
                rank=1,
                title="APT.",
                artist_name="ROSÉ & Bruno Mars",
                album_name="APT.",
                duration_seconds=170,
                external_ids={"apple_music_id": "1234567890"},
            ),
            MusicChartItemPayload(
                rank=2,
                title="Die With A Smile",
                artist_name="Lady Gaga & Bruno Mars",
                album_name="Die With A Smile",
                duration_seconds=252,
                external_ids={"apple_music_id": "1234567891"},
            ),
            MusicChartItemPayload(
                rank=3,
                title="Birds of a Feather",
                artist_name="Billie Eilish",
                album_name="HIT ME HARD AND SOFT",
                duration_seconds=210,
                external_ids={"apple_music_id": "1234567892"},
            ),
            MusicChartItemPayload(
                rank=4,
                title="Espresso",
                artist_name="Sabrina Carpenter",
                album_name="Short n' Sweet",
                duration_seconds=175,
                external_ids={"apple_music_id": "1234567893"},
            ),
            MusicChartItemPayload(
                rank=5,
                title="Good Luck, Babe!",
                artist_name="Chappell Roan",
                album_name="Good Luck, Babe!",
                duration_seconds=218,
                external_ids={"apple_music_id": "1234567894"},
            ),
        ]
        
        return ChartFetchResult(
            success=True,
            items=mock_items[:chart.max_items or 100],
            fetched_at=datetime.utcnow().isoformat(),
        )
