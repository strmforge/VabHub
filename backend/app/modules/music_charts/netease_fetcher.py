"""
网易云音乐榜单抓取器

支持从网易云音乐 API 获取榜单数据。
注意：需要配置 API 代理或使用第三方 API（如 NeteaseCloudMusicApi）。

配置示例：
{
    "api_base": "http://localhost:3000",  # NeteaseCloudMusicApi 服务地址
    "playlist_id": "19723756"  # 飙升榜
}

常用榜单 ID：
- 19723756: 飙升榜
- 3779629: 新歌榜
- 2884035: 原创榜
- 3778678: 热歌榜
"""

from typing import List, Optional
from datetime import datetime

import httpx
from loguru import logger

from app.modules.music_charts.base import BaseChartFetcher, ChartItemData, ChartFetchResult
from app.models.music_chart import MusicChart


class NeteaseChartFetcher(BaseChartFetcher):
    """
    网易云音乐榜单抓取器
    
    依赖 NeteaseCloudMusicApi 项目提供的 API 服务
    https://github.com/Binaryify/NeteaseCloudMusicApi
    """
    
    async def fetch_chart_items(self, chart: MusicChart) -> ChartFetchResult:
        """
        抓取网易云榜单
        
        config 需要包含:
        - api_base: API 服务地址
        - playlist_id: 榜单/歌单 ID
        """
        config = chart.source.config if chart.source else {}
        api_base = config.get("api_base", "http://localhost:3000")
        playlist_id = config.get("playlist_id") or chart.chart_key
        
        if not playlist_id:
            return ChartFetchResult(
                success=False,
                items=[],
                error_message="未配置 playlist_id",
            )
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 获取歌单详情
                url = f"{api_base}/playlist/detail"
                response = await client.get(url, params={"id": playlist_id})
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("code") != 200:
                    return ChartFetchResult(
                        success=False,
                        items=[],
                        error_message=f"API 返回错误: {data.get('msg', 'Unknown')}",
                    )
                
                playlist = data.get("playlist", {})
                tracks = playlist.get("tracks", [])
                
                items = []
                for idx, track in enumerate(tracks[:chart.max_items], start=1):
                    # 解析艺术家
                    artists = track.get("ar", [])
                    artist_name = ", ".join([a.get("name", "") for a in artists]) if artists else "Unknown"
                    
                    # 解析专辑
                    album = track.get("al", {})
                    album_name = album.get("name")
                    cover_url = album.get("picUrl")
                    
                    # 时长（毫秒转秒）
                    duration_ms = track.get("dt", 0)
                    duration_seconds = duration_ms // 1000 if duration_ms else None
                    
                    item = ChartItemData(
                        rank=idx,
                        title=track.get("name", "Unknown"),
                        artist_name=artist_name,
                        album_name=album_name,
                        duration_seconds=duration_seconds,
                        external_id=str(track.get("id")),
                        external_url=f"https://music.163.com/#/song?id={track.get('id')}",
                        cover_url=cover_url,
                        extra_data={
                            "netease_id": track.get("id"),
                            "popularity": track.get("pop"),
                            "mv_id": track.get("mv"),
                        },
                    )
                    items.append(item)
                
                logger.info(f"网易云榜单 {playlist_id} 抓取成功: {len(items)} 首")
                
                return ChartFetchResult(
                    success=True,
                    items=items,
                    fetched_at=datetime.utcnow(),
                )
                
        except httpx.HTTPError as e:
            logger.error(f"网易云 API 请求失败: {e}")
            return ChartFetchResult(
                success=False,
                items=[],
                error_message=f"API 请求失败: {str(e)}",
            )
        except Exception as e:
            logger.error(f"网易云榜单抓取失败: {e}")
            return ChartFetchResult(
                success=False,
                items=[],
                error_message=str(e),
            )


# 注册抓取器
def register():
    """注册到工厂"""
    from app.modules.music_charts.factory import register_fetcher
    register_fetcher("netease", NeteaseChartFetcher)
