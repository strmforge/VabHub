"""
影视榜单服务 - 整合TMDB和豆瓣
基于VabHub1.4版的实现
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.modules.settings.service import SettingsService
from app.core.cache import get_cache
from app.modules.charts.providers.netflix_top10 import NetflixTop10Provider
from app.modules.charts.providers.imdb_datasets import IMDBDatasetsProvider

logger = logging.getLogger(__name__)


class VideoChartsService:
    """影视榜单服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache = get_cache()  # 使用统一缓存系统
        self.cache_ttl = 3600  # 1小时缓存
        
        # TMDB配置
        self.tmdb_base_url = "https://api.themoviedb.org/3/"
        self.tmdb_image_base_url = "https://image.tmdb.org/t/p/"
        
        # 豆瓣配置
        self.douban_base_url = "https://frodo.douban.com/api/v2/"
        self.douban_api_key = "0ac44ae016490db2204ce0a042db2916"
        
        # 支持的榜单类型
        self.supported_charts = {
            "tmdb": {
                "trending_all": "全部流行趋势",
                "trending_movies": "电影流行趋势",
                "trending_tv": "电视剧流行趋势",
                "movie_popular": "热门电影",
                "movie_top_rated": "高分电影",
                "movie_now_playing": "正在热映",
                "movie_upcoming": "即将上映",
                "tv_popular": "热门电视剧",
                "tv_top_rated": "高分电视剧",
                "tv_on_the_air": "正在播出",
                "tv_airing_today": "今日播出"
            },
            "douban": {
                "movie_showing": "正在热映",
                "movie_hot": "热门电影",
                "movie_top250": "电影TOP250",
                "tv_hot": "热门电视剧",
                "tv_variety": "综艺节目"
            },
            "netflix": {
                "top10_global": "Netflix全球Top 10",
                "top10_movies": "Netflix电影Top 10",
                "top10_tv": "Netflix电视剧Top 10"
            },
            "imdb": {
                "top_rated_movies": "IMDb高分电影",
                "top_rated_tv": "IMDb高分电视剧",
                "popular_movies": "IMDb热门电影"
            }
        }
        
        # 初始化数据提供者
        self.netflix_provider = NetflixTop10Provider()
        self.imdb_provider = IMDBDatasetsProvider()
    
    async def get_tmdb_api_key(self) -> Optional[str]:
        """获取TMDB API密钥"""
        try:
            settings_service = SettingsService(self.db)
            tmdb_setting = await settings_service.get_setting("tmdb_api_key")
            api_key = tmdb_setting.get("value") if tmdb_setting else None
            
            if not api_key:
                import os
                api_key = os.getenv("TMDB_API_KEY", "")
            
            # 如果没有配置，使用默认密钥（VabHub1.4版中的默认密钥）
            if not api_key:
                api_key = "db55373b1b8f4f6a8654d6a0c1d37a8f"
            
            return api_key
        except Exception as e:
            logger.error(f"获取TMDB API密钥失败: {e}")
            return "db55373b1b8f4f6a8654d6a0c1d37a8f"  # 默认密钥
    
    async def get_charts(
        self,
        source: str,
        chart_type: str,
        region: str = "CN",
        limit: int = 20,
        week: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取影视榜单"""
        try:
            # 生成缓存键（使用统一缓存系统的键生成器）
            cache_key = self.cache.generate_key(
                "video_charts",
                source=source,
                chart_type=chart_type,
                region=region,
                limit=limit,
                week=week or ""
            )
            
            # 尝试从缓存获取
            cached_data = await self.cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"从缓存获取影视榜单: {source}:{chart_type}")
                return cached_data
            
            # 根据数据源获取榜单
            if source == "tmdb":
                charts = await self._get_tmdb_charts(chart_type, region, limit)
            elif source == "douban":
                charts = await self._get_douban_charts(chart_type, limit)
            elif source == "netflix":
                charts = await self._get_netflix_charts(chart_type, limit, week)
            elif source == "imdb":
                charts = await self._get_imdb_charts(chart_type, limit)
            else:
                raise ValueError(f"不支持的数据源: {source}")
            
            # 缓存结果（使用统一缓存系统）
            await self.cache.set(cache_key, charts, ttl=self.cache_ttl)
            logger.debug(f"影视榜单数据已缓存: {source}:{chart_type}")
            
            return charts
            
        except Exception as e:
            logger.error(f"获取影视榜单失败 {source}:{chart_type}: {e}")
            return []
    
    async def _get_tmdb_charts(
        self,
        chart_type: str,
        region: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """获取TMDB榜单 - 基于VabHub1.4版的实现"""
        try:
            api_key = await self.get_tmdb_api_key()
            
            # 构建API端点
            endpoints = {
                "trending_all": "trending/all/day",
                "trending_movies": "trending/movie/day",
                "trending_tv": "trending/tv/day",
                "movie_popular": "movie/popular",
                "movie_top_rated": "movie/top_rated",
                "movie_now_playing": "movie/now_playing",
                "movie_upcoming": "movie/upcoming",
                "tv_popular": "tv/popular",
                "tv_top_rated": "tv/top_rated",
                "tv_on_the_air": "tv/on_the_air",
                "tv_airing_today": "tv/airing_today"
            }
            
            endpoint = endpoints.get(chart_type)
            if not endpoint:
                raise ValueError(f"不支持的榜单类型: {chart_type}")
            
            url = f"{self.tmdb_base_url}{endpoint}"
            params = {
                "api_key": api_key,
                "language": "zh-CN",
                "region": region,
                "page": 1
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            # 处理数据
            charts = []
            for i, item in enumerate(data.get("results", [])[:limit]):
                chart_item = {
                    "rank": i + 1,
                    "id": item.get("id"),
                    "title": item.get("title") or item.get("name"),
                    "original_title": item.get("original_title") or item.get("original_name"),
                    "type": "movie" if "title" in item else "tv",
                    "popularity": item.get("popularity"),
                    "vote_average": item.get("vote_average"),
                    "vote_count": item.get("vote_count"),
                    "release_date": item.get("release_date") or item.get("first_air_date"),
                    "overview": item.get("overview", ""),
                    "poster_url": f"{self.tmdb_image_base_url}w500{item.get('poster_path', '')}" if item.get("poster_path") else "",
                    "backdrop_url": f"{self.tmdb_image_base_url}w780{item.get('backdrop_path', '')}" if item.get("backdrop_path") else "",
                    "source": "tmdb"
                }
                charts.append(chart_item)
            
            return charts
            
        except Exception as e:
            logger.error(f"获取TMDB榜单失败: {e}")
            return []
    
    async def _get_douban_charts(
        self,
        chart_type: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """获取豆瓣榜单 - 基于VabHub1.4版的实现"""
        try:
            # 构建API端点
            endpoints = {
                "movie_showing": "subject_collection/movie_showing/items",
                "movie_hot": "subject_collection/movie_hot_gaia/items",
                "movie_top250": "subject_collection/movie_top250/items",
                "tv_hot": "subject_collection/tv_hot/items",
                "tv_variety": "subject_collection/tv_variety_show/items"
            }
            
            endpoint = endpoints.get(chart_type)
            if not endpoint:
                raise ValueError(f"不支持的榜单类型: {chart_type}")
            
            url = f"{self.douban_base_url}{endpoint}"
            params = {
                "apikey": self.douban_api_key,
                "start": 0,
                "count": min(limit, 50)
            }
            
            headers = {
                "User-Agent": "api-client/1 com.douban.frodo/7.22.0.beta9(230) Android/23 product/Mate 40 vendor/HUAWEI model/Mate 40 brand/HUAWEI",
                "Accept": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
            
            # 处理数据
            charts = []
            items = data.get("subject_collection_items", [])[:limit]
            
            for i, item in enumerate(items):
                rating_info = item.get("rating", {})
                pic_info = item.get("pic", {})
                
                chart_item = {
                    "rank": i + 1,
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "original_title": item.get("original_title"),
                    "type": "movie" if chart_type.startswith("movie") else "tv",
                    "score": rating_info.get("value", 0),
                    "rating_count": rating_info.get("count", 0),
                    "release_date": item.get("release_date") or item.get("pubdate"),
                    "year": item.get("year"),
                    "genres": item.get("genres", []),
                    "summary": item.get("intro", ""),
                    "poster_url": pic_info.get("large") or pic_info.get("normal") or "",
                    "actors": [actor.get("name") for actor in item.get("actors", [])[:5]],
                    "directors": [director.get("name") for director in item.get("directors", [])],
                    "source": "douban"
                }
                charts.append(chart_item)
            
            return charts
            
        except Exception as e:
            logger.error(f"获取豆瓣榜单失败: {e}")
            return []
    
    async def _get_netflix_charts(
        self,
        chart_type: str,
        limit: int,
        week: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取Netflix Top 10榜单"""
        try:
            # 根据榜单类型确定过滤条件
            region = "global"
            # 如果未指定周数，使用最新一周
            
            # 获取数据
            charts_data = await self.netflix_provider.fetch_data(
                region=region,
                week=week,
                limit=limit
            )
            
            # 转换为统一格式
            charts = []
            for item in charts_data:
                # 根据chart_type过滤
                if chart_type == "top10_movies" and item.get("type") != "movie":
                    continue
                if chart_type == "top10_tv" and item.get("type") != "tv":
                    continue
                
                chart_item = {
                    "rank": item.get("rank", 0),
                    "id": item.get("id", ""),
                    "title": item.get("title", ""),
                    "original_title": item.get("title", ""),
                    "type": item.get("type", "movie"),
                    "popularity": item.get("popularity", 0),
                    "vote_average": None,
                    "vote_count": None,
                    "release_date": None,
                    "overview": "",
                    "poster_url": item.get("poster_url"),
                    "backdrop_url": None,
                    "source": "netflix",
                    "weekly_hours_viewed": item.get("weekly_hours_viewed", 0),
                    "cumulative_weeks_in_top_10": item.get("cumulative_weeks_in_top_10", 0),
                    "week": item.get("week", "")
                }
                charts.append(chart_item)
            
            return charts
            
        except Exception as e:
            logger.error(f"获取Netflix Top 10榜单失败: {e}")
            return []
    
    async def _get_imdb_charts(
        self,
        chart_type: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """获取IMDb榜单"""
        try:
            # 根据榜单类型确定过滤条件
            title_type = None
            if chart_type == "top_rated_movies":
                title_type = "movie"
            elif chart_type == "top_rated_tv":
                title_type = "tvSeries"
            
            # 获取数据
            charts_data = await self.imdb_provider.fetch_data(
                join_basics=True,
                min_votes=10000,
                top_n=limit,
                title_type=title_type
            )
            
            # 转换为统一格式
            charts = []
            for item in charts_data:
                chart_item = {
                    "rank": item.get("rank", 0),
                    "id": item.get("id", ""),
                    "title": item.get("title", ""),
                    "original_title": item.get("original_title", ""),
                    "type": item.get("type", "movie"),
                    "popularity": item.get("rating", 0) * item.get("votes", 0) / 1000,  # 计算热度
                    "vote_average": item.get("rating", 0),
                    "vote_count": item.get("votes", 0),
                    "release_date": str(item.get("year", "")) if item.get("year") else None,
                    "overview": "",
                    "poster_url": item.get("poster_url"),
                    "backdrop_url": None,
                    "source": "imdb",
                    "year": item.get("year"),
                    "genres": item.get("genres", []),
                    "runtime_minutes": item.get("runtime_minutes")
                }
                charts.append(chart_item)
            
            return charts
            
        except Exception as e:
            logger.error(f"获取IMDb榜单失败: {e}")
            return []
    
    async def get_supported_charts(self) -> Dict[str, Any]:
        """获取支持的榜单类型"""
        return {
            "tmdb": self.supported_charts["tmdb"],
            "douban": self.supported_charts["douban"],
            "netflix": self.supported_charts["netflix"],
            "imdb": self.supported_charts["imdb"]
        }

