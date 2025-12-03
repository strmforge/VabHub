"""
媒体搜索API
提供TMDB搜索功能，用于手动整理时的媒体识别
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from loguru import logger
from datetime import datetime

from app.core.database import get_db
from app.core.schemas import BaseResponse, success_response, error_response
from app.core.config import settings
from app.modules.media_renamer.identifier import MediaIdentifier

router = APIRouter(prefix="/media", tags=["媒体搜索"])


class TmdbSearchResult(BaseModel):
    """TMDB搜索结果"""
    id: int = Field(..., description="TMDB ID")
    title: str = Field(..., description="标题")
    original_title: Optional[str] = Field(None, description="原始标题")
    year: Optional[int] = Field(None, description="年份")
    media_type: Literal["movie", "tv"] = Field(..., description="媒体类型")
    overview: Optional[str] = Field(None, description="简介")
    poster_url: Optional[str] = Field(None, description="海报URL")
    backdrop_url: Optional[str] = Field(None, description="背景图URL")
    release_date: Optional[str] = Field(None, description="发布日期")
    first_air_date: Optional[str] = Field(None, description="首播日期")
    vote_average: Optional[float] = Field(None, description="评分")
    popularity: Optional[float] = Field(None, description="热度")
    
    class Config:
        from_attributes = False


class TmdbSearchResponse(BaseModel):
    """TMDB搜索响应"""
    results: List[TmdbSearchResult]
    total_results: int
    total_pages: int
    page: int


# 简单的内存缓存
_search_cache = {}
_cache_expire_time = 300  # 5分钟缓存


def _get_cache_key(query: str, media_type: Optional[str], year: Optional[int]) -> str:
    """生成缓存键"""
    return f"{query}_{media_type or 'all'}_{year or 'all'}"


def _get_from_cache(cache_key: str) -> Optional[TmdbSearchResponse]:
    """从缓存获取结果"""
    if cache_key in _search_cache:
        cached_data, timestamp = _search_cache[cache_key]
        if datetime.now().timestamp() - timestamp < _cache_expire_time:
            return cached_data
        else:
            # 缓存过期，删除
            del _search_cache[cache_key]
    return None


def _save_to_cache(cache_key: str, data: TmdbSearchResponse):
    """保存到缓存"""
    _search_cache[cache_key] = (data, datetime.now().timestamp())
    
    # 简单的缓存清理：如果缓存项超过50个，清理最旧的10个
    if len(_search_cache) > 50:
        oldest_keys = sorted(
            _search_cache.keys(),
            key=lambda k: _search_cache[k][1]
        )[:10]
        for key in oldest_keys:
            del _search_cache[key]


@router.get("/search-tmdb", response_model=BaseResponse)
async def search_tmdb(
    q: str = Query(..., min_length=1, max_length=100, description="搜索关键词"),
    type: Optional[Literal["movie", "tv"]] = Query(None, description="媒体类型过滤"),
    year: Optional[int] = Query(None, ge=1900, le=2030, description="年份过滤"),
    page: int = Query(1, ge=1, le=20, description="页码"),
    db = Depends(get_db)
):
    """
    搜索TMDB数据库
    
    根据关键词搜索电影和电视剧，支持类型和年份过滤
    
    Args:
        q: 搜索关键词
        type: 媒体类型过滤（movie/tv）
        year: 年份过滤
        page: 页码（1-20）
    
    Returns:
        TMDB搜索结果列表
    """
    try:
        # 检查缓存
        cache_key = _get_cache_key(q, type, year)
        cached_result = _get_from_cache(cache_key)
        if cached_result:
            logger.debug(f"TMDB搜索命中缓存: {cache_key}")
            return success_response(
                data=cached_result.model_dump(),
                message="搜索成功（缓存）"
            )
        
        # 获取TMDB API密钥
        tmdb_api_key = getattr(settings, 'TMDB_API_KEY', None)
        if not tmdb_api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(
                    error_code="TMDB_API_KEY_MISSING",
                    error_message="TMDB API密钥未配置"
                ).model_dump()
            )
        
        # 创建MediaIdentifier实例
        identifier = MediaIdentifier(tmdb_api_key)
        
        # 执行搜索
        search_results = await identifier.search_tmdb_multi(
            query=q,
            media_type=type,
            year=year,
            page=page
        )
        
        # 转换为响应格式
        tmdb_results = []
        for item in search_results.get("results", []):
            # 处理电影和电视剧的不同字段
            if item.get("media_type") == "movie":
                title = item.get("title", "")
                original_title = item.get("original_title")
                release_date = item.get("release_date")
                year_from_date = int(release_date[:4]) if release_date else None
            else:  # tv
                title = item.get("name", "")
                original_title = item.get("original_name")
                release_date = item.get("first_air_date")
                year_from_date = int(release_date[:4]) if release_date else None
            
            # 构建海报URL
            poster_path = item.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            
            # 构建背景图URL
            backdrop_path = item.get("backdrop_path")
            backdrop_url = f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else None
            
            tmdb_result = TmdbSearchResult(
                id=item.get("id"),
                title=title,
                original_title=original_title,
                year=year_from_date,
                media_type=item.get("media_type"),
                overview=item.get("overview"),
                poster_url=poster_url,
                backdrop_url=backdrop_url,
                release_date=release_date,
                first_air_date=item.get("first_air_date") if item.get("media_type") == "tv" else None,
                vote_average=item.get("vote_average"),
                popularity=item.get("popularity")
            )
            tmdb_results.append(tmdb_result)
        
        # 构建响应
        response = TmdbSearchResponse(
            results=tmdb_results,
            total_results=search_results.get("total_results", 0),
            total_pages=search_results.get("total_pages", 0),
            page=search_results.get("page", page)
        )
        
        # 保存到缓存
        _save_to_cache(cache_key, response)
        
        return success_response(
            data=response.model_dump(),
            message=f"搜索完成，找到 {len(tmdb_results)} 个结果"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TMDB搜索失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="TMDB_SEARCH_ERROR",
                error_message=f"TMDB搜索时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/tmdb/{tmdb_id}", response_model=BaseResponse)
async def get_tmdb_details(
    tmdb_id: int,
    media_type: Literal["movie", "tv"] = Query(..., description="媒体类型"),
    db = Depends(get_db)
):
    """
    获取TMDB详细信息
    
    根据TMDB ID获取电影或电视剧的详细信息
    
    Args:
        tmdb_id: TMDB ID
        media_type: 媒体类型（movie/tv）
    
    Returns:
        TMDB详细信息
    """
    try:
        # 获取TMDB API密钥
        tmdb_api_key = getattr(settings, 'TMDB_API_KEY', None)
        if not tmdb_api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(
                    error_code="TMDB_API_KEY_MISSING",
                    error_message="TMDB API密钥未配置"
                ).model_dump()
            )
        
        # 创建MediaIdentifier实例
        identifier = MediaIdentifier(tmdb_api_key)
        
        # 获取详细信息
        details = await identifier.get_tmdb_details(tmdb_id, media_type)
        
        if not details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="TMDB_NOT_FOUND",
                    error_message="未找到指定的TMDB项目"
                ).model_dump()
            )
        
        # 转换为响应格式
        if media_type == "movie":
            title = details.get("title", "")
            original_title = details.get("original_title")
            release_date = details.get("release_date")
            year_from_date = int(release_date[:4]) if release_date else None
        else:  # tv
            title = details.get("name", "")
            original_title = details.get("original_name")
            release_date = details.get("first_air_date")
            year_from_date = int(release_date[:4]) if release_date else None
        
        # 构建海报URL
        poster_path = details.get("poster_path")
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
        
        # 构建背景图URL
        backdrop_path = details.get("backdrop_path")
        backdrop_url = f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else None
        
        tmdb_result = TmdbSearchResult(
            id=details.get("id"),
            title=title,
            original_title=original_title,
            year=year_from_date,
            media_type=media_type,
            overview=details.get("overview"),
            poster_url=poster_url,
            backdrop_url=backdrop_url,
            release_date=release_date,
            first_air_date=details.get("first_air_date") if media_type == "tv" else None,
            vote_average=details.get("vote_average"),
            popularity=details.get("popularity")
        )
        
        return success_response(
            data=tmdb_result.model_dump(),
            message="获取TMDB详细信息成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取TMDB详细信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="TMDB_DETAILS_ERROR",
                error_message=f"获取TMDB详细信息时发生错误: {str(e)}"
            ).model_dump()
        )
