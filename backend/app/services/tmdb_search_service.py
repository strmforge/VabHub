"""
TMDB搜索服务
TG-BOT-TMDB-SEARCH P1实现
"""

from typing import List, Literal
from pydantic import BaseModel
from loguru import logger

from app.core.config import settings
from app.utils.http_client import create_httpx_client


class TmdbSearchItem(BaseModel):
    """TMDB搜索结果项"""
    tmdb_id: int
    title: str
    original_title: str | None = None
    year: int | None = None
    media_type: Literal["movie", "tv"]
    overview: str | None = None


TMDB_API_BASE = "https://api.themoviedb.org/3"
DEFAULT_LANGUAGE = "zh-CN"  # 默认使用中文，后续可配置化


async def search_tmdb(
    query: str,
    *,
    media_type: Literal["movie", "tv", "multi"] = "multi",
    language: str | None = None,
    limit: int = 5,
) -> List[TmdbSearchItem]:
    """
    使用TMDB API按关键词模糊搜索电影/剧集
    
    Args:
        query: 搜索关键词
        media_type: movie/tv/multi
        language: 可选，按系统默认语言或TMDB配置走
        limit: 返回最多N条结果（默认5条）
    
    Returns:
        TmdbSearchItem列表，如果搜索失败或无结果则返回空列表
    
    Raises:
        ValueError: 如果TMDB_API_KEY未配置
    """
    if not query.strip():
        return []
    
    # 检查TMDB API Key配置
    if not settings.TMDB_API_KEY:
        logger.error("TMDB_API_KEY not configured")
        raise ValueError("TMDB_API_KEY not configured")
    
    # 使用默认语言或指定语言
    search_language = language or DEFAULT_LANGUAGE
    
    try:
        async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
            # 根据媒体类型选择不同的端点
            if media_type == "multi":
                # 多类型搜索：需要分别搜索movie和tv
                movie_results = await _search_single_type(client, "movie", query, search_language, limit)
                tv_results = await _search_single_type(client, "tv", query, search_language, limit)
                
                # 合并结果，按相关性排序（简单的交替合并）
                all_results = []
                for i in range(max(len(movie_results), len(tv_results))):
                    if i < len(movie_results):
                        all_results.append(movie_results[i])
                    if i < len(tv_results):
                        all_results.append(tv_results[i])
                
                return all_results[:limit]
            else:
                # 单类型搜索
                return await _search_single_type(client, media_type, query, search_language, limit)
                
    except Exception as e:
        logger.error(f"TMDB search failed for query '{query}': {e}")
        return []


async def _search_single_type(
    client,
    media_type: Literal["movie", "tv"],
    query: str,
    language: str,
    limit: int,
) -> List[TmdbSearchItem]:
    """
    搜索单一类型的媒体内容
    """
    endpoint = f"{TMDB_API_BASE}/search/{media_type}"
    params = {
        "api_key": settings.TMDB_API_KEY,
        "query": query,
        "language": language,
    }
    
    response = await client.get(endpoint, params=params)
    response.raise_for_status()
    result = response.json()
    
    if not result.get("results"):
        return []
    
    items = []
    for media_item in result["results"][:limit]:
        # 提取年份
        if media_type == "movie":
            title = media_item.get("title", "")
            original_title = media_item.get("original_title")
            release_date = media_item.get("release_date", "")
            year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None
        else:  # tv
            title = media_item.get("name", "")
            original_title = media_item.get("original_name")
            first_air_date = media_item.get("first_air_date", "")
            year = int(first_air_date[:4]) if first_air_date and len(first_air_date) >= 4 else None
        
        # 限制概述长度
        overview = media_item.get("overview", "")
        if overview and len(overview) > 200:
            overview = overview[:200] + "..."
        
        items.append(TmdbSearchItem(
            tmdb_id=media_item["id"],
            title=title,
            original_title=original_title,
            year=year,
            media_type=media_type,
            overview=overview
        ))
    
    return items


async def get_tmdb_details(tmdb_id: int, media_type: Literal["movie", "tv"]) -> dict:
    """
    获取TMDB详细信息（用于创建订阅时的补充信息）
    
    Args:
        tmdb_id: TMDB ID
        media_type: movie/tv
    
    Returns:
        TMDB详细信息字典，失败时返回空字典
    """
    if not settings.TMDB_API_KEY:
        logger.error("TMDB_API_KEY not configured")
        return {}
    
    try:
        async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
            endpoint = f"{TMDB_API_BASE}/{media_type}/{tmdb_id}"
            params = {
                "api_key": settings.TMDB_API_KEY,
                "language": DEFAULT_LANGUAGE,
            }
            
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logger.error(f"Get TMDB details failed for {media_type}/{tmdb_id}: {e}")
        return {}
