"""
Spotify 榜单抓取器（占位实现）

需要 Spotify Web API 访问权限。
https://developer.spotify.com/documentation/web-api

配置示例：
{
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "playlist_id": "37i9dQZEVXbMDoHDwVN2tF"  # Global Top 50
}

常用榜单 ID：
- 37i9dQZEVXbMDoHDwVN2tF: Global Top 50
- 37i9dQZEVXbLRQDuF5jeBp: USA Top 50
- 37i9dQZEVXbNxXF4SkHj9F: Korea Top 50
"""

from typing import List, Optional
from datetime import datetime

import httpx
from loguru import logger

from app.modules.music_charts.base import BaseChartFetcher, ChartItemData, ChartFetchResult
from app.models.music_chart import MusicChart


class SpotifyChartFetcher(BaseChartFetcher):
    """
    Spotify 榜单抓取器
    
    使用 Spotify Web API 获取播放列表数据
    """
    
    _access_token: Optional[str] = None
    _token_expires_at: Optional[datetime] = None
    
    async def _get_access_token(self, client_id: str, client_secret: str) -> Optional[str]:
        """
        获取 Spotify API 访问令牌
        
        使用 Client Credentials Flow
        """
        # 检查缓存的 token
        if self._access_token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at:
                return self._access_token
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://accounts.spotify.com/api/token",
                    data={"grant_type": "client_credentials"},
                    auth=(client_id, client_secret),
                )
                response.raise_for_status()
                
                data = response.json()
                self._access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)
                self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                
                return self._access_token
                
        except Exception as e:
            logger.error(f"获取 Spotify token 失败: {e}")
            return None
    
    async def fetch_chart_items(self, chart: MusicChart) -> ChartFetchResult:
        """
        抓取 Spotify 榜单
        
        config 需要包含:
        - client_id: Spotify App Client ID
        - client_secret: Spotify App Client Secret
        - playlist_id: 播放列表 ID
        """
        config = chart.source.config if chart.source else {}
        client_id = config.get("client_id")
        client_secret = config.get("client_secret")
        playlist_id = config.get("playlist_id") or chart.chart_key
        
        if not client_id or not client_secret:
            # 返回占位数据用于测试
            logger.warning("Spotify API 未配置，返回占位数据")
            return self._get_placeholder_result()
        
        if not playlist_id:
            return ChartFetchResult(
                success=False,
                items=[],
                error_message="未配置 playlist_id",
            )
        
        # 获取访问令牌
        token = await self._get_access_token(client_id, client_secret)
        if not token:
            return ChartFetchResult(
                success=False,
                items=[],
                error_message="无法获取 Spotify 访问令牌",
            )
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 获取播放列表
                url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
                headers = {"Authorization": f"Bearer {token}"}
                params = {"limit": min(chart.max_items, 100)}
                
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                tracks = data.get("items", [])
                
                items = []
                for idx, item in enumerate(tracks, start=1):
                    track = item.get("track", {})
                    if not track:
                        continue
                    
                    # 解析艺术家
                    artists = track.get("artists", [])
                    artist_name = ", ".join([a.get("name", "") for a in artists]) if artists else "Unknown"
                    
                    # 解析专辑
                    album = track.get("album", {})
                    album_name = album.get("name")
                    
                    # 封面
                    images = album.get("images", [])
                    cover_url = images[0].get("url") if images else None
                    
                    # 时长（毫秒转秒）
                    duration_ms = track.get("duration_ms", 0)
                    duration_seconds = duration_ms // 1000 if duration_ms else None
                    
                    chart_item = ChartItemData(
                        rank=idx,
                        title=track.get("name", "Unknown"),
                        artist_name=artist_name,
                        album_name=album_name,
                        duration_seconds=duration_seconds,
                        external_id=track.get("id"),
                        external_url=track.get("external_urls", {}).get("spotify"),
                        cover_url=cover_url,
                        extra_data={
                            "spotify_id": track.get("id"),
                            "popularity": track.get("popularity"),
                            "explicit": track.get("explicit"),
                            "preview_url": track.get("preview_url"),
                        },
                    )
                    items.append(chart_item)
                
                logger.info(f"Spotify 榜单 {playlist_id} 抓取成功: {len(items)} 首")
                
                return ChartFetchResult(
                    success=True,
                    items=items,
                    fetched_at=datetime.utcnow(),
                )
                
        except httpx.HTTPError as e:
            logger.error(f"Spotify API 请求失败: {e}")
            return ChartFetchResult(
                success=False,
                items=[],
                error_message=f"API 请求失败: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Spotify 榜单抓取失败: {e}")
            return ChartFetchResult(
                success=False,
                items=[],
                error_message=str(e),
            )
    
    def _get_placeholder_result(self) -> ChartFetchResult:
        """返回占位数据用于测试"""
        items = [
            ChartItemData(
                rank=1,
                title="Die With A Smile",
                artist_name="Lady Gaga, Bruno Mars",
                album_name="Die With A Smile",
                duration_seconds=251,
            ),
            ChartItemData(
                rank=2,
                title="APT.",
                artist_name="ROSÉ, Bruno Mars",
                album_name="APT.",
                duration_seconds=170,
            ),
            ChartItemData(
                rank=3,
                title="Birds of a Feather",
                artist_name="Billie Eilish",
                album_name="HIT ME HARD AND SOFT",
                duration_seconds=210,
            ),
        ]
        
        return ChartFetchResult(
            success=True,
            items=items,
            fetched_at=datetime.utcnow(),
        )


# 需要导入 timedelta
from datetime import timedelta


# 注册抓取器
def register():
    """注册到工厂"""
    from app.modules.music_charts.factory import register_fetcher
    register_fetcher("spotify", SpotifyChartFetcher)
