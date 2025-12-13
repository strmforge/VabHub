"""
发现页聚合服务

统一聚合 TMDB / 豆瓣 / Bangumi 数据源，支持公共 key fallback

Created: 0.0.3 DISCOVER-MUSIC-HOME P2
"""

import asyncio
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from loguru import logger

from app.core.cache import get_cache
from app.core.public_metadata_config import (
    get_tmdb_key_for_discover,
    get_discover_key_source,
    is_douban_available,
    is_bangumi_available,
)


class DiscoverItem(BaseModel):
    """发现页内容项（统一格式）"""
    id: str
    title: str
    subtitle: Optional[str] = None  # 年份/分数等
    poster_url: Optional[str] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    media_type: str  # movie / tv / anime / music
    source: str  # tmdb / douban / bangumi
    external_url: Optional[str] = None  # 外部链接
    extra: Optional[Dict[str, Any]] = None  # 额外信息


class DiscoverSection(BaseModel):
    """发现页区块"""
    id: str
    title: str
    source: str  # tmdb / douban / bangumi / rsshub
    items: List[DiscoverItem] = Field(default_factory=list)
    error: Optional[str] = None  # 错误信息（用于单源失败时提示）


class DiscoverHomeResponse(BaseModel):
    """发现页首页响应"""
    sections: List[DiscoverSection] = Field(default_factory=list)
    has_public_keys: bool = False
    has_private_keys: bool = False
    key_source: str = "none"  # public / private / none
    message: Optional[str] = None


# TMDB API 基础 URL
TMDB_API_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


class DiscoverService:
    """发现页聚合服务"""
    
    def __init__(self):
        self.cache = get_cache()
        self.timeout = 10.0
    
    async def get_home(self) -> DiscoverHomeResponse:
        """
        获取发现页首页内容
        
        聚合多个数据源，单源失败不影响整体
        """
        sections: List[DiscoverSection] = []
        
        # 获取 key 状态
        key_source = get_discover_key_source()
        has_public_keys = key_source == "public"
        has_private_keys = key_source == "private"
        
        # 并行获取各数据源
        tasks = []
        
        # TMDB 数据
        tmdb_key = get_tmdb_key_for_discover()
        if tmdb_key:
            tasks.append(self._fetch_tmdb_sections(tmdb_key))
        else:
            tasks.append(asyncio.coroutine(lambda: [])())
        
        # 豆瓣数据
        if is_douban_available():
            tasks.append(self._fetch_douban_sections())
        else:
            tasks.append(asyncio.coroutine(lambda: [])())
        
        # Bangumi 数据
        if is_bangumi_available():
            tasks.append(self._fetch_bangumi_sections())
        else:
            tasks.append(asyncio.coroutine(lambda: [])())
        
        # 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并结果
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"发现页数据源获取失败: {result}")
                continue
            if isinstance(result, list):
                sections.extend(result)
        
        # 构建消息
        message = None
        if key_source == "none" and not sections:
            message = "未配置任何数据源，请在设置中配置 TMDB API Key 以获取热门内容"
        elif key_source == "public":
            message = "当前使用公共数据源"
        elif key_source == "private":
            message = "当前使用您的个人 API Key"
        
        return DiscoverHomeResponse(
            sections=sections,
            has_public_keys=has_public_keys,
            has_private_keys=has_private_keys,
            key_source=key_source,
            message=message,
        )
    
    async def _fetch_tmdb_sections(self, api_key: str) -> List[DiscoverSection]:
        """获取 TMDB 数据区块"""
        sections = []
        
        try:
            # 并行获取热门电影和剧集
            trending_movies = await self._fetch_tmdb_trending("movie", api_key)
            trending_tv = await self._fetch_tmdb_trending("tv", api_key)
            
            if trending_movies:
                sections.append(DiscoverSection(
                    id="tmdb_trending_movie",
                    title="本周热门电影",
                    source="tmdb",
                    items=trending_movies,
                ))
            
            if trending_tv:
                sections.append(DiscoverSection(
                    id="tmdb_trending_tv",
                    title="本周热门剧集",
                    source="tmdb",
                    items=trending_tv,
                ))
                
        except Exception as e:
            logger.warning(f"TMDB 数据获取失败: {e}")
            sections.append(DiscoverSection(
                id="tmdb_error",
                title="TMDB 热门",
                source="tmdb",
                items=[],
                error="TMDB 数据暂时不可用",
            ))
        
        return sections
    
    async def _fetch_tmdb_trending(self, media_type: str, api_key: str) -> List[DiscoverItem]:
        """获取 TMDB 热门内容"""
        cache_key = self.cache.generate_key("discover_tmdb_trending", media_type=media_type)
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return [DiscoverItem(**item) for item in cached]
        
        try:
            from app.utils.http_client import create_httpx_client
            async with create_httpx_client(timeout=self.timeout, use_proxy=True) as client:
                url = f"{TMDB_API_BASE}/trending/{media_type}/week"
                params = {
                    "api_key": api_key,
                    "language": "zh-CN"
                }
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            items = []
            for item in data.get("results", [])[:12]:
                if media_type == "movie":
                    title = item.get("title", "")
                    release_date = item.get("release_date", "")
                else:
                    title = item.get("name", "")
                    release_date = item.get("first_air_date", "")
                
                year = release_date[:4] if release_date else None
                poster_path = item.get("poster_path")
                
                items.append(DiscoverItem(
                    id=f"tmdb_{item.get('id')}",
                    title=title,
                    subtitle=year,
                    poster_url=f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None,
                    rating=item.get("vote_average"),
                    rating_count=item.get("vote_count"),
                    media_type=media_type,
                    source="tmdb",
                    external_url=f"https://www.themoviedb.org/{media_type}/{item.get('id')}",
                    extra={"tmdb_id": item.get("id")},
                ))
            
            # 缓存 30 分钟
            await self.cache.set(cache_key, [item.model_dump() for item in items], ttl=1800)
            return items
            
        except Exception as e:
            logger.warning(f"TMDB trending {media_type} 获取失败: {e}")
            return []
    
    async def _fetch_douban_sections(self) -> List[DiscoverSection]:
        """获取豆瓣数据区块"""
        sections = []
        
        try:
            from app.modules.douban.client import DoubanClient
            client = DoubanClient()
            
            # 获取热门电影
            try:
                hot_movies = await client.get_movie_hot(0, 12)
                items = self._transform_douban_items(hot_movies, "movie")
                if items:
                    sections.append(DiscoverSection(
                        id="douban_hot_movie",
                        title="豆瓣热门电影",
                        source="douban",
                        items=items,
                    ))
            except Exception as e:
                logger.warning(f"豆瓣热门电影获取失败: {e}")
            
            # 获取热门电视剧
            try:
                hot_tv = await client.get_tv_hot(0, 12)
                items = self._transform_douban_items(hot_tv, "tv")
                if items:
                    sections.append(DiscoverSection(
                        id="douban_hot_tv",
                        title="豆瓣热门剧集",
                        source="douban",
                        items=items,
                    ))
            except Exception as e:
                logger.warning(f"豆瓣热门剧集获取失败: {e}")
                
        except Exception as e:
            logger.warning(f"豆瓣数据获取失败: {e}")
            sections.append(DiscoverSection(
                id="douban_error",
                title="豆瓣热门",
                source="douban",
                items=[],
                error="豆瓣数据暂时不可用",
            ))
        
        return sections
    
    def _transform_douban_items(self, data: dict, media_type: str) -> List[DiscoverItem]:
        """转换豆瓣数据格式"""
        items = []
        raw_items = data.get("subject_collection_items", []) or data.get("items", [])
        
        for item in raw_items[:12]:
            subject = item.get("subject", item)
            douban_id = subject.get("id", "")
            
            rating_data = subject.get("rating", {})
            rating = rating_data.get("value") if isinstance(rating_data, dict) else None
            rating_count = rating_data.get("count") if isinstance(rating_data, dict) else None
            
            pic_data = subject.get("pic", {})
            poster_url = pic_data.get("normal") if isinstance(pic_data, dict) else pic_data
            
            items.append(DiscoverItem(
                id=f"douban_{douban_id}",
                title=subject.get("title", ""),
                subtitle=str(subject.get("year", "")) if subject.get("year") else None,
                poster_url=poster_url,
                rating=rating,
                rating_count=rating_count,
                media_type=media_type,
                source="douban",
                external_url=f"https://movie.douban.com/subject/{douban_id}/",
                extra={"douban_id": douban_id},
            ))
        
        return items
    
    async def _fetch_bangumi_sections(self) -> List[DiscoverSection]:
        """获取 Bangumi 数据区块"""
        sections = []
        
        try:
            from app.core.bangumi_client import BangumiClient
            client = BangumiClient()
            
            # 获取热门动漫
            try:
                popular = await client.get_popular_anime(limit=12)
                items = self._transform_bangumi_items(popular)
                if items:
                    sections.append(DiscoverSection(
                        id="bangumi_popular",
                        title="Bangumi 热门番剧",
                        source="bangumi",
                        items=items,
                    ))
            except Exception as e:
                logger.warning(f"Bangumi 热门动漫获取失败: {e}")
                
        except Exception as e:
            logger.warning(f"Bangumi 数据获取失败: {e}")
            sections.append(DiscoverSection(
                id="bangumi_error",
                title="Bangumi 热门",
                source="bangumi",
                items=[],
                error="Bangumi 数据暂时不可用",
            ))
        
        return sections
    
    def _transform_bangumi_items(self, data: list) -> List[DiscoverItem]:
        """转换 Bangumi 数据格式"""
        items = []
        
        for item in data[:12]:
            bgm_id = item.get("id", "")
            images = item.get("images", {})
            poster_url = images.get("large") or images.get("medium") or images.get("small")
            
            rating_data = item.get("rating", {})
            rating = rating_data.get("score") if isinstance(rating_data, dict) else None
            rating_count = rating_data.get("total") if isinstance(rating_data, dict) else None
            
            items.append(DiscoverItem(
                id=f"bangumi_{bgm_id}",
                title=item.get("name_cn") or item.get("name", ""),
                subtitle=item.get("date"),
                poster_url=poster_url,
                rating=rating,
                rating_count=rating_count,
                media_type="anime",
                source="bangumi",
                external_url=f"https://bgm.tv/subject/{bgm_id}",
                extra={"bangumi_id": bgm_id},
            ))
        
        return items


# 全局服务实例
_discover_service: Optional[DiscoverService] = None


def get_discover_service() -> DiscoverService:
    """获取发现页聚合服务实例"""
    global _discover_service
    if _discover_service is None:
        _discover_service = DiscoverService()
    return _discover_service
