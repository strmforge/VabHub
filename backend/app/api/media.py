"""
媒体搜索和TMDB API集成
使用统一响应模型
"""
from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import List, Optional
from pydantic import BaseModel
import httpx
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from app.core.config import settings
from app.core.cache import get_cache
from app.core.database import get_db
from app.models.media import Media, MediaFile
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response,
    NotFoundResponse
)

router = APIRouter()

# TMDB API基础URL
TMDB_API_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p"

# 获取缓存实例
cache = get_cache()


async def search_tmdb_movie(query: str, api_key: str) -> List[dict]:
    """搜索TMDB电影（带缓存）"""
    # 生成缓存键
    cache_key = cache.generate_key("tmdb_search_movie", query=query)
    
    # 尝试从缓存获取
    cached_result = await cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    # 调用API（使用代理）
    from app.utils.http_client import create_httpx_client
    async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
        url = f"{TMDB_API_BASE}/search/movie"
        params = {
            "api_key": api_key,
            "query": query,
            "language": "zh-CN",
            "region": "CN"
        }
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
    
    # 缓存结果（1小时）
    await cache.set(cache_key, results, ttl=3600)
    return results


async def search_tmdb_tv(query: str, api_key: str) -> List[dict]:
    """搜索TMDB电视剧（带缓存）"""
    # 生成缓存键
    cache_key = cache.generate_key("tmdb_search_tv", query=query)
    
    # 尝试从缓存获取
    cached_result = await cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    # 调用API（使用代理）
    from app.utils.http_client import create_httpx_client
    async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
        url = f"{TMDB_API_BASE}/search/tv"
        params = {
            "api_key": api_key,
            "query": query,
            "language": "zh-CN"
        }
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
    
    # 缓存结果（1小时）
    await cache.set(cache_key, results, ttl=3600)
    return results


async def get_tmdb_movie_details(tmdb_id: int, api_key: str) -> dict:
    """获取TMDB电影详情（带缓存）"""
    # 生成缓存键
    cache_key = cache.generate_key("tmdb_movie_details", tmdb_id=tmdb_id)
    
    # 尝试从缓存获取
    cached_result = await cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    # 调用API（使用代理）
    from app.utils.http_client import create_httpx_client
    async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
        url = f"{TMDB_API_BASE}/movie/{tmdb_id}"
        params = {
            "api_key": api_key,
            "language": "zh-CN",
            "append_to_response": "images"
        }
        response = await client.get(url, params=params)
        response.raise_for_status()
        result = response.json()
    
    # 缓存结果（24小时，详情数据变化不频繁）
    await cache.set(cache_key, result, ttl=86400)
    return result


async def get_tmdb_tv_details(tmdb_id: int, api_key: str) -> dict:
    """获取TMDB电视剧详情（带缓存）"""
    # 生成缓存键
    cache_key = cache.generate_key("tmdb_tv_details", tmdb_id=tmdb_id)
    
    # 尝试从缓存获取
    cached_result = await cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    # 调用API（使用代理）
    from app.utils.http_client import create_httpx_client
    async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
        url = f"{TMDB_API_BASE}/tv/{tmdb_id}"
        params = {
            "api_key": api_key,
            "language": "zh-CN",
            "append_to_response": "images"
        }
        response = await client.get(url, params=params)
        response.raise_for_status()
        result = response.json()
    
    # 缓存结果（24小时，详情数据变化不频繁）
    await cache.set(cache_key, result, ttl=86400)
    return result


@router.get("/search", response_model=BaseResponse)
async def search_media(
    query: str = Query(..., description="搜索关键词"),
    type: str = Query("movie", description="媒体类型: movie 或 tv")
):
    """
    搜索媒体
    
    返回统一响应格式：
    {
        "success": true,
        "message": "搜索成功",
        "data": [MediaItem, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    api_key = settings.TMDB_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="TMDB_API_KEY_NOT_CONFIGURED",
                error_message="TMDB API Key未配置，请在环境变量或设置中配置TMDB_API_KEY"
            ).model_dump()
        )
    
    try:
        if type == "movie":
            results = await search_tmdb_movie(query, api_key)
        elif type == "tv":
            results = await search_tmdb_tv(query, api_key)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="INVALID_MEDIA_TYPE",
                    error_message="类型必须是 movie 或 tv"
                ).model_dump()
            )
        
        # 格式化结果
        formatted_results = []
        for item in results:
            formatted_results.append({
                "id": item.get("id"),
                "title": item.get("title") or item.get("name"),
                "original_title": item.get("original_title") or item.get("original_name"),
                "overview": item.get("overview"),
                "release_date": item.get("release_date") or item.get("first_air_date"),
                "poster_path": item.get("poster_path"),
                "backdrop_path": item.get("backdrop_path"),
                "vote_average": item.get("vote_average"),
                "tmdb_id": item.get("id"),
                "year": int(item.get("release_date", item.get("first_air_date", "")).split("-")[0]) if item.get("release_date") or item.get("first_air_date") else None
            })
        
        return success_response(data=formatted_results, message="搜索成功")
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        logger.error(f"TMDB API错误: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=error_response(
                error_code="TMDB_API_ERROR",
                error_message=f"TMDB API错误: {e.response.text}"
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"搜索媒体失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"搜索失败: {str(e)}"
            ).model_dump()
        )


@router.get("/details/{tmdb_id}", response_model=BaseResponse)
async def get_media_details(
    tmdb_id: int,
    type: str = Query("movie", description="媒体类型: movie 或 tv")
):
    """
    获取媒体详情（包括海报、背景图等）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": MediaDetails,
        "timestamp": "2025-01-XX..."
    }
    """
    api_key = settings.TMDB_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="TMDB_API_KEY_NOT_CONFIGURED",
                error_message="TMDB API Key未配置，请在环境变量或设置中配置TMDB_API_KEY"
            ).model_dump()
        )
    
    try:
        if type == "movie":
            details = await get_tmdb_movie_details(tmdb_id, api_key)
        elif type == "tv":
            details = await get_tmdb_tv_details(tmdb_id, api_key)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="INVALID_MEDIA_TYPE",
                    error_message="类型必须是 movie 或 tv"
                ).model_dump()
            )
        
        # 格式化详情
        images = details.get("images", {})
        poster_path = details.get("poster_path")
        backdrop_path = details.get("backdrop_path")
        
        # 获取最佳海报和背景图
        if images.get("posters"):
            poster_path = images["posters"][0].get("file_path") if images["posters"] else poster_path
        if images.get("backdrops"):
            backdrop_path = images["backdrops"][0].get("file_path") if images["backdrops"] else backdrop_path
        
        media_details = {
            "tmdb_id": details.get("id"),
            "title": details.get("title") or details.get("name"),
            "original_title": details.get("original_title") or details.get("original_name"),
            "overview": details.get("overview"),
            "release_date": details.get("release_date") or details.get("first_air_date"),
            "year": int((details.get("release_date") or details.get("first_air_date", "")).split("-")[0]) if details.get("release_date") or details.get("first_air_date") else None,
            "poster": f"{TMDB_IMAGE_BASE}/w500{poster_path}" if poster_path else None,
            "backdrop": f"{TMDB_IMAGE_BASE}/original{backdrop_path}" if backdrop_path else None,
            "poster_path": poster_path,
            "backdrop_path": backdrop_path,
            "vote_average": details.get("vote_average"),
            "runtime": details.get("runtime") or (details.get("episode_run_time", [0])[0] if details.get("episode_run_time") else None),
            "genres": [g.get("name") for g in details.get("genres", [])],
            "imdb_id": details.get("imdb_id"),
            "tvdb_id": details.get("external_ids", {}).get("tvdb_id") if type == "tv" else None
        }
        
        return success_response(data=media_details, message="获取成功")
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        logger.error(f"TMDB API错误: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=error_response(
                error_code="TMDB_API_ERROR",
                error_message=f"TMDB API错误: {e.response.text}"
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"获取媒体详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取详情失败: {str(e)}"
            ).model_dump()
        )


async def get_tmdb_tv_seasons(tmdb_id: int, api_key: str) -> List[dict]:
    """获取TMDB电视剧的所有季信息（带缓存）"""
    # 生成缓存键
    cache_key = cache.generate_key("tmdb_tv_seasons", tmdb_id=tmdb_id)
    
    # 尝试从缓存获取
    cached_result = await cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    # 调用API（使用代理）
    from app.utils.http_client import create_httpx_client
    async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
        url = f"{TMDB_API_BASE}/tv/{tmdb_id}"
        params = {
            "api_key": api_key,
            "language": "zh-CN",
            "append_to_response": "images"
        }
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        seasons = data.get("seasons", [])
    
    # 缓存结果（12小时）
    await cache.set(cache_key, seasons, ttl=43200)
    return seasons


@router.get("/seasons/{tmdb_id}", response_model=BaseResponse)
async def get_tv_seasons(tmdb_id: int):
    """
    获取电视剧的所有季信息
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [SeasonInfo, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    api_key = settings.TMDB_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="TMDB_API_KEY_NOT_CONFIGURED",
                error_message="TMDB API Key未配置"
            ).model_dump()
        )
    
    try:
        seasons = await get_tmdb_tv_seasons(tmdb_id, api_key)
        
        # 格式化季信息
        formatted_seasons = []
        for season in seasons:
            if season.get("season_number", 0) >= 0:  # 排除季0（特辑等）
                formatted_seasons.append({
                    "season_number": season.get("season_number"),
                    "name": season.get("name"),
                    "overview": season.get("overview"),
                    "episode_count": season.get("episode_count"),
                    "air_date": season.get("air_date"),
                    "poster_path": season.get("poster_path"),
                    "vote_average": season.get("vote_average")
                })
        
        # 按季数排序
        formatted_seasons.sort(key=lambda x: x["season_number"])
        
        return success_response(data=formatted_seasons, message="获取成功")
    except httpx.HTTPStatusError as e:
        logger.error(f"TMDB API错误: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=error_response(
                error_code="TMDB_API_ERROR",
                error_message=f"TMDB API错误: {e.response.text}"
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"获取季信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取季信息失败: {str(e)}"
            ).model_dump()
        )


async def get_tmdb_credits(tmdb_id: int, media_type: str, api_key: str) -> dict:
    """获取TMDB演职员表（带缓存）"""
    cache_key = cache.generate_key("tmdb_credits", tmdb_id=tmdb_id, media_type=media_type)
    
    cached_result = await cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    from app.utils.http_client import create_httpx_client
    async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
        url = f"{TMDB_API_BASE}/{media_type}/{tmdb_id}/credits"
        params = {
            "api_key": api_key,
            "language": "zh-CN"
        }
        response = await client.get(url, params=params)
        response.raise_for_status()
        result = response.json()
    
    await cache.set(cache_key, result, ttl=86400)
    return result


async def get_tmdb_person_details(person_id: int, api_key: str) -> dict:
    """获取TMDB人物详情（带缓存）"""
    cache_key = cache.generate_key("tmdb_person_details", person_id=person_id)
    
    cached_result = await cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    from app.utils.http_client import create_httpx_client
    async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
        url = f"{TMDB_API_BASE}/person/{person_id}"
        params = {
            "api_key": api_key,
            "language": "zh-CN",
            "append_to_response": "images,movie_credits,tv_credits"
        }
        response = await client.get(url, params=params)
        response.raise_for_status()
        result = response.json()
    
    await cache.set(cache_key, result, ttl=86400)
    return result


async def get_tmdb_similar(tmdb_id: int, media_type: str, api_key: str) -> List[dict]:
    """获取TMDB类似内容（带缓存）"""
    cache_key = cache.generate_key("tmdb_similar", tmdb_id=tmdb_id, media_type=media_type)
    
    cached_result = await cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    from app.utils.http_client import create_httpx_client
    async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
        url = f"{TMDB_API_BASE}/{media_type}/{tmdb_id}/similar"
        params = {
            "api_key": api_key,
            "language": "zh-CN"
        }
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
    
    await cache.set(cache_key, results, ttl=86400)
    return results


async def get_tmdb_recommendations(tmdb_id: int, media_type: str, api_key: str) -> List[dict]:
    """获取TMDB推荐内容（带缓存）"""
    cache_key = cache.generate_key("tmdb_recommendations", tmdb_id=tmdb_id, media_type=media_type)
    
    cached_result = await cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    from app.utils.http_client import create_httpx_client
    async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
        url = f"{TMDB_API_BASE}/{media_type}/{tmdb_id}/recommendations"
        params = {
            "api_key": api_key,
            "language": "zh-CN"
        }
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
    
    await cache.set(cache_key, results, ttl=86400)
    return results


@router.get("/credits/{tmdb_id}", response_model=BaseResponse)
async def get_media_credits(
    tmdb_id: int,
    type: str = Query("movie", description="媒体类型: movie 或 tv")
):
    """
    获取媒体演职员表
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "cast": [...],
            "crew": {...}
        },
        "timestamp": "2025-01-XX..."
    }
    """
    api_key = settings.TMDB_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="TMDB_API_KEY_NOT_CONFIGURED",
                error_message="TMDB API Key未配置"
            ).model_dump()
        )
    
    try:
        media_type = "movie" if type == "movie" else "tv"
        credits = await get_tmdb_credits(tmdb_id, media_type, api_key)
        
        # 格式化演职员表
        cast = []
        for actor in credits.get("cast", [])[:20]:  # 限制前20个
            cast.append({
                "id": actor.get("id"),
                "name": actor.get("name"),
                "character": actor.get("character"),
                "profile_path": f"{TMDB_IMAGE_BASE}/w185{actor.get('profile_path')}" if actor.get("profile_path") else None,
                "order": actor.get("order")
            })
        
        crew = {}
        # 按部门分组
        for member in credits.get("crew", []):
            dept = member.get("department", "Other")
            if dept not in crew:
                crew[dept] = []
            crew[dept].append({
                "id": member.get("id"),
                "name": member.get("name"),
                "job": member.get("job"),
                "profile_path": f"{TMDB_IMAGE_BASE}/w185{member.get('profile_path')}" if member.get("profile_path") else None
            })
        
        return success_response(
            data={
                "cast": cast,
                "crew": crew
            },
            message="获取成功"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"TMDB API错误: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=error_response(
                error_code="TMDB_API_ERROR",
                error_message=f"TMDB API错误: {e.response.text}"
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"获取演职员表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取演职员表失败: {str(e)}"
            ).model_dump()
        )


@router.get("/person/{person_id}", response_model=BaseResponse)
async def get_person_details(person_id: int):
    """
    获取人物详情
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": PersonDetails,
        "timestamp": "2025-01-XX..."
    }
    """
    api_key = settings.TMDB_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="TMDB_API_KEY_NOT_CONFIGURED",
                error_message="TMDB API Key未配置"
            ).model_dump()
        )
    
    try:
        person = await get_tmdb_person_details(person_id, api_key)
        
        # 格式化人物详情
        images = person.get("images", {}).get("profiles", [])
        profile_path = person.get("profile_path")
        if images:
            profile_path = images[0].get("file_path") if images else profile_path
        
        movie_credits = person.get("movie_credits", {})
        tv_credits = person.get("tv_credits", {})
        
        person_details = {
            "id": person.get("id"),
            "name": person.get("name"),
            "biography": person.get("biography"),
            "birthday": person.get("birthday"),
            "deathday": person.get("deathday"),
            "place_of_birth": person.get("place_of_birth"),
            "profile_path": f"{TMDB_IMAGE_BASE}/w500{profile_path}" if profile_path else None,
            "known_for_department": person.get("known_for_department"),
            "popularity": person.get("popularity"),
            "movies": [
                {
                    "id": m.get("id"),
                    "title": m.get("title"),
                    "character": m.get("character"),
                    "release_date": m.get("release_date"),
                    "poster_path": f"{TMDB_IMAGE_BASE}/w185{m.get('poster_path')}" if m.get("poster_path") else None
                }
                for m in movie_credits.get("cast", [])[:10]
            ],
            "tv_shows": [
                {
                    "id": t.get("id"),
                    "name": t.get("name"),
                    "character": t.get("character"),
                    "first_air_date": t.get("first_air_date"),
                    "poster_path": f"{TMDB_IMAGE_BASE}/w185{t.get('poster_path')}" if t.get("poster_path") else None
                }
                for t in tv_credits.get("cast", [])[:10]
            ]
        }
        
        return success_response(data=person_details, message="获取成功")
    except httpx.HTTPStatusError as e:
        logger.error(f"TMDB API错误: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=error_response(
                error_code="TMDB_API_ERROR",
                error_message=f"TMDB API错误: {e.response.text}"
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"获取人物详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取人物详情失败: {str(e)}"
            ).model_dump()
        )


@router.get("/similar/{tmdb_id}", response_model=BaseResponse)
async def get_similar_media(
    tmdb_id: int,
    type: str = Query("movie", description="媒体类型: movie 或 tv")
):
    """
    获取类似媒体
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [MediaItem, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    api_key = settings.TMDB_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="TMDB_API_KEY_NOT_CONFIGURED",
                error_message="TMDB API Key未配置"
            ).model_dump()
        )
    
    try:
        media_type = "movie" if type == "movie" else "tv"
        similar = await get_tmdb_similar(tmdb_id, media_type, api_key)
        
        formatted_results = []
        for item in similar[:20]:  # 限制20个
            formatted_results.append({
                "id": item.get("id"),
                "title": item.get("title") or item.get("name"),
                "original_title": item.get("original_title") or item.get("original_name"),
                "overview": item.get("overview"),
                "release_date": item.get("release_date") or item.get("first_air_date"),
                "poster_path": f"{TMDB_IMAGE_BASE}/w500{item.get('poster_path')}" if item.get("poster_path") else None,
                "backdrop_path": f"{TMDB_IMAGE_BASE}/original{item.get('backdrop_path')}" if item.get("backdrop_path") else None,
                "vote_average": item.get("vote_average"),
                "tmdb_id": item.get("id")
            })
        
        return success_response(data=formatted_results, message="获取成功")
    except httpx.HTTPStatusError as e:
        logger.error(f"TMDB API错误: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=error_response(
                error_code="TMDB_API_ERROR",
                error_message=f"TMDB API错误: {e.response.text}"
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"获取类似媒体失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取类似媒体失败: {str(e)}"
            ).model_dump()
        )


@router.get("/recommendations/{tmdb_id}", response_model=BaseResponse)
async def get_recommended_media(
    tmdb_id: int,
    type: str = Query("movie", description="媒体类型: movie 或 tv")
):
    """
    获取推荐媒体
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [MediaItem, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    api_key = settings.TMDB_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="TMDB_API_KEY_NOT_CONFIGURED",
                error_message="TMDB API Key未配置"
            ).model_dump()
        )
    
    try:
        media_type = "movie" if type == "movie" else "tv"
        recommendations = await get_tmdb_recommendations(tmdb_id, media_type, api_key)
        
        formatted_results = []
        for item in recommendations[:20]:  # 限制20个
            formatted_results.append({
                "id": item.get("id"),
                "title": item.get("title") or item.get("name"),
                "original_title": item.get("original_title") or item.get("original_name"),
                "overview": item.get("overview"),
                "release_date": item.get("release_date") or item.get("first_air_date"),
                "poster_path": f"{TMDB_IMAGE_BASE}/w500{item.get('poster_path')}" if item.get("poster_path") else None,
                "backdrop_path": f"{TMDB_IMAGE_BASE}/original{item.get('backdrop_path')}" if item.get("backdrop_path") else None,
                "vote_average": item.get("vote_average"),
                "tmdb_id": item.get("id")
            })
        
        return success_response(data=formatted_results, message="获取成功")
    except httpx.HTTPStatusError as e:
        logger.error(f"TMDB API错误: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=error_response(
                error_code="TMDB_API_ERROR",
                error_message=f"TMDB API错误: {e.response.text}"
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"获取推荐媒体失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取推荐媒体失败: {str(e)}"
            ).model_dump()
        )


# 媒体管理CRUD端点
class MediaCreate(BaseModel):
    """创建媒体请求"""
    title: str
    original_title: Optional[str] = None
    year: Optional[int] = None
    media_type: str  # movie, tv, anime
    tmdb_id: Optional[int] = None
    tvdb_id: Optional[int] = None
    imdb_id: Optional[str] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    overview: Optional[str] = None


class MediaUpdate(BaseModel):
    """更新媒体请求"""
    title: Optional[str] = None
    original_title: Optional[str] = None
    year: Optional[int] = None
    media_type: Optional[str] = None
    tmdb_id: Optional[int] = None
    tvdb_id: Optional[int] = None
    imdb_id: Optional[str] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    overview: Optional[str] = None


class MediaResponse(BaseModel):
    """媒体响应"""
    id: int
    title: str
    original_title: Optional[str] = None
    year: Optional[int] = None
    media_type: str
    tmdb_id: Optional[int] = None
    tvdb_id: Optional[int] = None
    imdb_id: Optional[str] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    overview: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


@router.get("/", response_model=BaseResponse)
async def list_media(
    media_type: Optional[str] = Query(None, description="媒体类型过滤: movie, tv, anime"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取媒体列表
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "items": [MediaResponse, ...],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from sqlalchemy import func
        
        # 构建查询
        query = select(Media)
        count_query = select(func.count(Media.id))
        
        if media_type:
            query = query.where(Media.media_type == media_type)
            count_query = count_query.where(Media.media_type == media_type)
        
        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 分页
        query = query.order_by(Media.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        # 执行查询
        result = await db.execute(query)
        media_list = result.scalars().all()
        
        # 转换为响应格式
        media_responses = [
            MediaResponse(
                id=media.id,
                title=media.title,
                original_title=media.original_title,
                year=media.year,
                media_type=media.media_type,
                tmdb_id=media.tmdb_id,
                tvdb_id=media.tvdb_id,
                imdb_id=media.imdb_id,
                poster_url=media.poster_url,
                backdrop_url=media.backdrop_url,
                overview=media.overview,
                created_at=media.created_at.isoformat() if media.created_at else "",
                updated_at=media.updated_at.isoformat() if media.updated_at else ""
            )
            for media in media_list
        ]
        
        total_pages = (total + page_size - 1) // page_size
        
        return success_response(
            data={
                "items": [media.model_dump() for media in media_responses],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            },
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取媒体列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取媒体列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{media_id}", response_model=BaseResponse)
async def get_media(
    media_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取媒体详情
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": MediaResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        result = await db.execute(
            select(Media).where(Media.id == media_id)
        )
        media = result.scalar_one_or_none()
        
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"媒体不存在 (ID: {media_id})"
                ).model_dump()
            )
        
        media_response = MediaResponse(
            id=media.id,
            title=media.title,
            original_title=media.original_title,
            year=media.year,
            media_type=media.media_type,
            tmdb_id=media.tmdb_id,
            tvdb_id=media.tvdb_id,
            imdb_id=media.imdb_id,
            poster_url=media.poster_url,
            backdrop_url=media.backdrop_url,
            overview=media.overview,
            created_at=media.created_at.isoformat() if media.created_at else "",
            updated_at=media.updated_at.isoformat() if media.updated_at else ""
        )
        
        return success_response(
            data=media_response.model_dump(),
            message="获取成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取媒体详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取媒体详情时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_media(
    media: MediaCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建媒体记录
    
    返回统一响应格式：
    {
        "success": true,
        "message": "创建成功",
        "data": MediaResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from datetime import datetime
        
        new_media = Media(
            title=media.title,
            original_title=media.original_title,
            year=media.year,
            media_type=media.media_type,
            tmdb_id=media.tmdb_id,
            tvdb_id=media.tvdb_id,
            imdb_id=media.imdb_id,
            poster_url=media.poster_url,
            backdrop_url=media.backdrop_url,
            overview=media.overview,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_media)
        await db.commit()
        await db.refresh(new_media)
        
        media_response = MediaResponse(
            id=new_media.id,
            title=new_media.title,
            original_title=new_media.original_title,
            year=new_media.year,
            media_type=new_media.media_type,
            tmdb_id=new_media.tmdb_id,
            tvdb_id=new_media.tvdb_id,
            imdb_id=new_media.imdb_id,
            poster_url=new_media.poster_url,
            backdrop_url=new_media.backdrop_url,
            overview=new_media.overview,
            created_at=new_media.created_at.isoformat() if new_media.created_at else "",
            updated_at=new_media.updated_at.isoformat() if new_media.updated_at else ""
        )
        
        return success_response(
            data=media_response.model_dump(),
            message="创建成功"
        )
    except Exception as e:
        logger.error(f"创建媒体记录失败: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"创建媒体记录时发生错误: {str(e)}"
            ).model_dump()
        )


@router.put("/{media_id}", response_model=BaseResponse)
async def update_media(
    media_id: int,
    media: MediaUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新媒体记录
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": MediaResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from datetime import datetime
        
        result = await db.execute(
            select(Media).where(Media.id == media_id)
        )
        existing_media = result.scalar_one_or_none()
        
        if not existing_media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"媒体不存在 (ID: {media_id})"
                ).model_dump()
            )
        
        # 更新字段
        update_data = media.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(existing_media, key, value)
        
        existing_media.updated_at = datetime.utcnow()
        
        db.add(existing_media)
        await db.commit()
        await db.refresh(existing_media)
        
        media_response = MediaResponse(
            id=existing_media.id,
            title=existing_media.title,
            original_title=existing_media.original_title,
            year=existing_media.year,
            media_type=existing_media.media_type,
            tmdb_id=existing_media.tmdb_id,
            tvdb_id=existing_media.tvdb_id,
            imdb_id=existing_media.imdb_id,
            poster_url=existing_media.poster_url,
            backdrop_url=existing_media.backdrop_url,
            overview=existing_media.overview,
            created_at=existing_media.created_at.isoformat() if existing_media.created_at else "",
            updated_at=existing_media.updated_at.isoformat() if existing_media.updated_at else ""
        )
        
        return success_response(
            data=media_response.model_dump(),
            message="更新成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新媒体记录失败: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新媒体记录时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/{media_id}", response_model=BaseResponse)
async def delete_media(
    media_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除媒体记录
    
    返回统一响应格式：
    {
        "success": true,
        "message": "删除成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        result = await db.execute(
            select(Media).where(Media.id == media_id)
        )
        media = result.scalar_one_or_none()
        
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"媒体不存在 (ID: {media_id})"
                ).model_dump()
            )
        
        # 删除关联的媒体文件
        await db.execute(
            delete(MediaFile).where(MediaFile.media_id == media_id)
        )
        
        # 删除媒体记录
        await db.execute(
            delete(Media).where(Media.id == media_id)
        )
        await db.commit()
        
        return success_response(message="删除成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除媒体记录失败: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除媒体记录时发生错误: {str(e)}"
            ).model_dump()
        )

