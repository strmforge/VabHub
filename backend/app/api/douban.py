"""
豆瓣API集成
使用统一响应模型
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from loguru import logger
from pydantic import BaseModel
from typing import List, Optional

from app.constants.media_types import MEDIA_TYPE_SHORT_DRAMA, MEDIA_TYPE_TV
from app.core.database import get_db
from app.core.schemas import BaseResponse, error_response, success_response
from app.modules.douban.client import DoubanClient

router = APIRouter()


def _map_douban_media_type(media_type: str) -> str:
    """短剧走豆瓣电视剧接口。"""
    return MEDIA_TYPE_TV if media_type == MEDIA_TYPE_SHORT_DRAMA else media_type


class DoubanSearchResponse(BaseModel):
    """豆瓣搜索响应"""
    id: str
    title: str
    original_title: Optional[str] = None
    year: Optional[int] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    poster: Optional[str] = None
    type: str  # movie, tv
    genres: Optional[List[str]] = None
    directors: Optional[List[str]] = None
    actors: Optional[List[str]] = None


class DoubanDetailResponse(BaseModel):
    """豆瓣详情响应"""
    id: str
    title: str
    original_title: Optional[str] = None
    year: Optional[int] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    poster: Optional[str] = None
    backdrop: Optional[str] = None
    type: str
    genres: Optional[List[str]] = None
    countries: Optional[List[str]] = None
    directors: Optional[List[str]] = None
    actors: Optional[List[str]] = None
    summary: Optional[str] = None
    episodes: Optional[int] = None
    seasons: Optional[int] = None


@router.get("/search", response_model=BaseResponse)
async def search_douban(
    query: str = Query(..., description="搜索关键词"),
    media_type: str = Query("movie", description="媒体类型: movie, tv, short_drama"),
    start: int = Query(0, ge=0, description="起始位置"),
    count: int = Query(20, ge=1, le=100, description="返回数量")
):
    """
    搜索豆瓣媒体
    
    返回统一响应格式：
    {
        "success": true,
        "message": "搜索成功",
        "data": {
            "total": 100,
            "items": [DoubanSearchResponse, ...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        client = DoubanClient()
        normalized_media_type = _map_douban_media_type(media_type)
        
        if normalized_media_type == MEDIA_TYPE_TV:
            result = await client.search_tv(query, start, count)
        else:
            result = await client.search_movie(query, start, count)
        
        # 转换响应格式
        items = result.get("items", []) or result.get("subjects", [])
        total = result.get("total", len(items))
        
        search_results = []
        for item in items:
            search_results.append({
                "id": str(item.get("id", "")),
                "title": item.get("title", ""),
                "original_title": item.get("original_title"),
                "year": item.get("year"),
                "rating": item.get("rating", {}).get("value") if isinstance(item.get("rating"), dict) else item.get("rating"),
                "rating_count": item.get("rating", {}).get("count") if isinstance(item.get("rating"), dict) else item.get("rating_count"),
                "poster": item.get("pic", {}).get("normal") if isinstance(item.get("pic"), dict) else item.get("pic"),
                "type": media_type,
                "genres": item.get("genres", []),
                "directors": [d.get("name", "") for d in item.get("directors", [])] if item.get("directors") else [],
                "actors": [a.get("name", "") for a in item.get("actors", [])[:5]] if item.get("actors") else []
            })
        
        return success_response(
            data={
                "total": total,
                "items": search_results
            },
            message="搜索成功"
        )
    except Exception as e:
        logger.error(f"搜索豆瓣媒体失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"搜索豆瓣媒体时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.get("/detail/{douban_id}", response_model=BaseResponse)
async def get_douban_detail(
    douban_id: str,
    media_type: str = Query("movie", description="媒体类型: movie, tv, short_drama"),
    db = Depends(get_db)
):
    """
    获取豆瓣媒体详情（兼容性端点）
    
    支持 {douban_id} 和 {subject_id} 两种参数名
    """
    return await get_douban_detail_by_subject_id(douban_id, media_type, db)


@router.get("/detail/{subject_id}", response_model=BaseResponse)
async def get_douban_detail_by_subject_id(
    subject_id: str,
    media_type: str = Query("movie", description="媒体类型: movie, tv, short_drama"),
    db = Depends(get_db)
):
    """
    获取豆瓣媒体详情
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": DoubanDetailResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        client = DoubanClient()
        normalized_media_type = _map_douban_media_type(media_type)
        
        # 使用 douban_id（与 subject_id 相同）
        if normalized_media_type == MEDIA_TYPE_TV:
            detail = await client.get_tv_detail(douban_id)
            rating = await client.get_tv_rating(douban_id)
        else:
            detail = await client.get_movie_detail(douban_id)
            rating = await client.get_movie_rating(douban_id)
        
        # 转换响应格式
        detail_response = {
            "id": str(detail.get("id", douban_id)),
            "title": detail.get("title", ""),
            "original_title": detail.get("original_title"),
            "year": detail.get("year"),
            "rating": rating.get("value") if rating and isinstance(rating, dict) else detail.get("rating", {}).get("value") if isinstance(detail.get("rating"), dict) else None,
            "rating_count": rating.get("count") if rating and isinstance(rating, dict) else detail.get("rating", {}).get("count") if isinstance(detail.get("rating"), dict) else None,
            "poster": detail.get("pic", {}).get("large") if isinstance(detail.get("pic"), dict) else detail.get("pic"),
            "backdrop": detail.get("pic", {}).get("raw") if isinstance(detail.get("pic"), dict) else None,
            "type": media_type,
            "genres": detail.get("genres", []),
            "countries": detail.get("countries", []),
            "directors": [d.get("name", "") for d in detail.get("directors", [])] if detail.get("directors") else [],
            "actors": [a.get("name", "") for a in detail.get("actors", [])[:10]] if detail.get("actors") else [],
            "summary": detail.get("intro", "") or detail.get("summary", ""),
            "episodes": detail.get("episodes_count") if normalized_media_type == MEDIA_TYPE_TV else None,
            "seasons": detail.get("season_count") if normalized_media_type == MEDIA_TYPE_TV else None
        }
        
        return success_response(
            data=detail_response,
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取豆瓣媒体详情失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取豆瓣媒体详情时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.get("/rating/{douban_id}", response_model=BaseResponse)
async def get_douban_rating(
    douban_id: str,
    media_type: str = Query("movie", description="媒体类型: movie, tv, short_drama"),
    db = Depends(get_db)
):
    """
    获取豆瓣评分
    
    支持 {douban_id} 参数名（FastAPI路由参数名不影响URL匹配，{douban_id} 和 {subject_id} 在URL层面是一样的）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "rating": 8.5,
            "rating_count": 10000,
            "stars": {
                "5": 0.3,
                "4": 0.4,
                "3": 0.2,
                "2": 0.08,
                "1": 0.02
            }
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        client = DoubanClient()
        normalized_media_type = _map_douban_media_type(media_type)
        # 使用 douban_id（与 subject_id 相同）
        rating = await client.get_subject_rating(douban_id, normalized_media_type)
        
        if not rating:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message="未找到评分信息"
                ).model_dump(mode='json')
            )
        
        return success_response(
            data={
                "rating": rating.get("value"),
                "rating_count": rating.get("count"),
                "stars": rating.get("stars", {})
            },
            message="获取成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取豆瓣评分失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取豆瓣评分时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.get("/top250", response_model=BaseResponse)
async def get_douban_top250(
    start: int = Query(0, ge=0, description="起始位置"),
    count: int = Query(20, ge=1, le=100, description="返回数量"),
    db = Depends(get_db)
):
    """
    获取豆瓣电影TOP250
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "total": 250,
            "items": [DoubanSearchResponse, ...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        client = DoubanClient()
        result = await client.get_movie_top250(start, count)
        
        items = result.get("subject_collection_items", []) or result.get("items", [])
        total = result.get("total", 250)
        
        top250_results = []
        for item in items:
            subject = item.get("subject", item)
            top250_results.append({
                "id": str(subject.get("id", "")),
                "title": subject.get("title", ""),
                "original_title": subject.get("original_title"),
                "year": subject.get("year"),
                "rating": subject.get("rating", {}).get("value") if isinstance(subject.get("rating"), dict) else subject.get("rating"),
                "rating_count": subject.get("rating", {}).get("count") if isinstance(subject.get("rating"), dict) else None,
                "poster": subject.get("pic", {}).get("normal") if isinstance(subject.get("pic"), dict) else subject.get("pic"),
                "type": "movie",
                "genres": subject.get("genres", []),
                "directors": [d.get("name", "") for d in subject.get("directors", [])] if subject.get("directors") else [],
                "actors": [a.get("name", "") for a in subject.get("actors", [])[:5]] if subject.get("actors") else []
            })
        
        return success_response(
            data={
                "total": total,
                "items": top250_results
            },
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取豆瓣TOP250失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取豆瓣TOP250时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.get("/hot/movie", response_model=BaseResponse)
async def get_douban_hot_movies(
    start: int = Query(0, ge=0, description="起始位置"),
    count: int = Query(20, ge=1, le=100, description="返回数量"),
    db = Depends(get_db)
):
    """
    获取豆瓣热门电影
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "total": 100,
            "items": [DoubanSearchResponse, ...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        client = DoubanClient()
        result = await client.get_movie_hot(start, count)
        
        items = result.get("subject_collection_items", []) or result.get("items", [])
        total = result.get("total", len(items))
        
        hot_results = []
        for item in items:
            subject = item.get("subject", item)
            hot_results.append({
                "id": str(subject.get("id", "")),
                "title": subject.get("title", ""),
                "original_title": subject.get("original_title"),
                "year": subject.get("year"),
                "rating": subject.get("rating", {}).get("value") if isinstance(subject.get("rating"), dict) else subject.get("rating"),
                "rating_count": subject.get("rating", {}).get("count") if isinstance(subject.get("rating"), dict) else None,
                "poster": subject.get("pic", {}).get("normal") if isinstance(subject.get("pic"), dict) else subject.get("pic"),
                "type": "movie",
                "genres": subject.get("genres", []),
                "directors": [d.get("name", "") for d in subject.get("directors", [])] if subject.get("directors") else [],
                "actors": [a.get("name", "") for a in subject.get("actors", [])[:5]] if subject.get("actors") else []
            })
        
        return success_response(
            data={
                "total": total,
                "items": hot_results
            },
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取豆瓣热门电影失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取豆瓣热门电影时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.get("/hot/tv", response_model=BaseResponse)
async def get_douban_hot_tv(
    start: int = Query(0, ge=0, description="起始位置"),
    count: int = Query(20, ge=1, le=100, description="返回数量"),
    db = Depends(get_db)
):
    """
    获取豆瓣热门电视剧
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "total": 100,
            "items": [DoubanSearchResponse, ...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        client = DoubanClient()
        result = await client.get_tv_hot(start, count)
        
        items = result.get("subject_collection_items", []) or result.get("items", [])
        total = result.get("total", len(items))
        
        hot_results = []
        for item in items:
            subject = item.get("subject", item)
            hot_results.append({
                "id": str(subject.get("id", "")),
                "title": subject.get("title", ""),
                "original_title": subject.get("original_title"),
                "year": subject.get("year"),
                "rating": subject.get("rating", {}).get("value") if isinstance(subject.get("rating"), dict) else subject.get("rating"),
                "rating_count": subject.get("rating", {}).get("count") if isinstance(subject.get("rating"), dict) else None,
                "poster": subject.get("pic", {}).get("normal") if isinstance(subject.get("pic"), dict) else subject.get("pic"),
                "type": "tv",
                "genres": subject.get("genres", []),
                "directors": [d.get("name", "") for d in subject.get("directors", [])] if subject.get("directors") else [],
                "actors": [a.get("name", "") for a in subject.get("actors", [])[:5]] if subject.get("actors") else []
            })
        
        return success_response(
            data={
                "total": total,
                "items": hot_results
            },
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取豆瓣热门电视剧失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取豆瓣热门电视剧时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )

