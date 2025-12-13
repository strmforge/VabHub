"""
发现页聚合 API

提供 TMDB / 豆瓣 / Bangumi 热门内容聚合，支持公共 key fallback

更新历史：
- 0.0.2: 初始实现，仅支持 TMDB
- 0.0.3: 多源聚合 + 公共 key 支持
"""
from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from loguru import logger

from app.core.config import settings
from app.core.cache import get_cache
from app.core.schemas import success_response, error_response
from app.core.public_metadata_config import get_tmdb_key_for_discover, get_discover_key_source
from app.services.discover_service import get_discover_service, DiscoverHomeResponse as ServiceResponse

router = APIRouter()

# TMDB API基础URL
TMDB_API_BASE = "https://api.themoviedb.org/3"

# 获取缓存实例
cache = get_cache()


class DiscoverItem(BaseModel):
    """发现页内容项"""
    id: int
    tmdb_id: int
    title: str
    original_title: Optional[str] = None
    overview: Optional[str] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    media_type: str  # movie / tv


class DiscoverSection(BaseModel):
    """发现页区块"""
    title: str
    items: List[DiscoverItem]
    more_link: Optional[str] = None


class DiscoverHomeResponse(BaseModel):
    """发现页首页响应"""
    tmdb_configured: bool
    tmdb_message: Optional[str] = None
    sections: List[DiscoverSection]


def _transform_tmdb_movie(item: dict) -> DiscoverItem:
    """转换 TMDB 电影数据"""
    return DiscoverItem(
        id=item.get("id", 0),
        tmdb_id=item.get("id", 0),
        title=item.get("title", ""),
        original_title=item.get("original_title"),
        overview=item.get("overview"),
        poster_path=item.get("poster_path"),
        backdrop_path=item.get("backdrop_path"),
        release_date=item.get("release_date"),
        vote_average=item.get("vote_average"),
        vote_count=item.get("vote_count"),
        media_type="movie"
    )


def _transform_tmdb_tv(item: dict) -> DiscoverItem:
    """转换 TMDB 电视剧数据"""
    return DiscoverItem(
        id=item.get("id", 0),
        tmdb_id=item.get("id", 0),
        title=item.get("name", ""),
        original_title=item.get("original_name"),
        overview=item.get("overview"),
        poster_path=item.get("poster_path"),
        backdrop_path=item.get("backdrop_path"),
        release_date=item.get("first_air_date"),
        vote_average=item.get("vote_average"),
        vote_count=item.get("vote_count"),
        media_type="tv"
    )


async def _fetch_tmdb_trending(media_type: str, time_window: str = "week") -> List[dict]:
    """获取 TMDB 热门内容"""
    api_key = settings.TMDB_API_KEY
    if not api_key:
        return []
    
    cache_key = cache.generate_key("tmdb_trending", media_type=media_type, time_window=time_window)
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached
    
    try:
        from app.utils.http_client import create_httpx_client
        async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
            url = f"{TMDB_API_BASE}/trending/{media_type}/{time_window}"
            params = {
                "api_key": api_key,
                "language": "zh-CN"
            }
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])[:12]  # 限制数量
        
        await cache.set(cache_key, results, ttl=1800)  # 缓存30分钟
        return results
    except Exception as e:
        logger.warning(f"获取 TMDB trending 失败: {e}")
        return []


async def _fetch_tmdb_popular(media_type: str) -> List[dict]:
    """获取 TMDB 流行内容"""
    api_key = settings.TMDB_API_KEY
    if not api_key:
        return []
    
    cache_key = cache.generate_key("tmdb_popular", media_type=media_type)
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached
    
    try:
        from app.utils.http_client import create_httpx_client
        async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
            url = f"{TMDB_API_BASE}/{media_type}/popular"
            params = {
                "api_key": api_key,
                "language": "zh-CN",
                "region": "CN"
            }
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])[:12]
        
        await cache.set(cache_key, results, ttl=1800)
        return results
    except Exception as e:
        logger.warning(f"获取 TMDB popular 失败: {e}")
        return []


@router.get("/home", summary="获取发现页首页内容")
async def get_discover_home():
    """
    获取发现页聚合内容 (0.0.3 多源版本)
    
    聚合 TMDB / 豆瓣 / Bangumi 热门内容：
    - 优先使用公共 key（PUBLIC_TMDB_DISCOVER_KEY）
    - 其次使用私有 key（TMDB_API_KEY）
    - 豆瓣/Bangumi 无需 key，始终可用
    - 单源失败不影响整体响应
    
    返回：
    - sections: 各数据源的热门内容区块
    - has_public_keys: 是否使用公共 key
    - has_private_keys: 是否使用私有 key
    - key_source: "public" | "private" | "none"
    - message: 状态提示
    """
    try:
        service = get_discover_service()
        result = await service.get_home()
        
        # 转换为兼容 0.0.2 的响应格式
        legacy_sections = []
        for section in result.sections:
            legacy_items = []
            for item in section.items:
                legacy_items.append(DiscoverItem(
                    id=hash(item.id) % (10**9),  # 转为数字 ID
                    tmdb_id=item.extra.get("tmdb_id", 0) if item.extra else 0,
                    title=item.title,
                    original_title=None,
                    overview=None,
                    poster_path=item.poster_url.replace("https://image.tmdb.org/t/p/w500", "") if item.poster_url and "tmdb" in item.poster_url else item.poster_url,
                    backdrop_path=None,
                    release_date=item.subtitle,
                    vote_average=item.rating,
                    vote_count=item.rating_count,
                    media_type=item.media_type,
                ))
            legacy_sections.append(DiscoverSection(
                title=section.title,
                items=legacy_items,
                more_link=f"/search?source={section.source}",
            ))
        
        # 兼容 0.0.2 的 tmdb_configured 字段
        tmdb_configured = result.key_source != "none"
        
        return {
            # 0.0.2 兼容字段
            "tmdb_configured": tmdb_configured,
            "tmdb_message": result.message,
            "sections": [s.model_dump() for s in legacy_sections],
            # 0.0.3 新增字段
            "has_public_keys": result.has_public_keys,
            "has_private_keys": result.has_private_keys,
            "key_source": result.key_source,
        }
        
    except Exception as e:
        logger.error(f"获取发现页内容失败: {e}")
        return {
            "tmdb_configured": False,
            "tmdb_message": f"获取内容失败: {str(e)}",
            "sections": [],
            "has_public_keys": False,
            "has_private_keys": False,
            "key_source": "none",
        }


@router.get("/trending/{media_type}", summary="获取 TMDB 热门内容")
async def get_trending(
    media_type: str,
    time_window: str = Query("week", description="时间窗口: day/week")
):
    """
    获取指定类型的热门内容
    
    - media_type: movie / tv / all
    - time_window: day / week
    """
    if media_type not in ["movie", "tv", "all"]:
        raise HTTPException(status_code=400, detail="media_type 必须是 movie/tv/all")
    
    api_key = settings.TMDB_API_KEY
    if not api_key:
        return success_response(
            data=[],
            message="未配置 TMDB API Key"
        )
    
    results = await _fetch_tmdb_trending(media_type, time_window)
    
    if media_type == "movie":
        items = [_transform_tmdb_movie(m) for m in results]
    elif media_type == "tv":
        items = [_transform_tmdb_tv(t) for t in results]
    else:
        items = []
        for item in results:
            if item.get("media_type") == "movie":
                items.append(_transform_tmdb_movie(item))
            elif item.get("media_type") == "tv":
                items.append(_transform_tmdb_tv(item))
    
    return success_response(data=items)
