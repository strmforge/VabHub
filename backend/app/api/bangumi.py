"""
Bangumi API端点
使用统一响应模型
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from loguru import logger

from app.core.bangumi_client import BangumiClient
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter()


@router.get("/search", response_model=BaseResponse)
async def search_bangumi(
    query: str = Query(..., description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100, description="返回数量")
):
    """
    搜索Bangumi动漫
    
    返回统一响应格式：
    {
        "success": true,
        "message": "搜索成功",
        "data": [AnimeItem, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        client = BangumiClient()
        results = await client.search_subject(query, limit=limit)
        
        return success_response(data=results, message="搜索成功")
    except Exception as e:
        logger.error(f"Bangumi搜索失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"搜索失败: {str(e)}"
            ).model_dump()
        )


@router.get("/subject/{subject_id}", response_model=BaseResponse)
async def get_bangumi_subject(subject_id: int):
    """
    获取Bangumi动漫详情
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": AnimeDetails,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        client = BangumiClient()
        result = await client.get_subject_detail(subject_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message=f"未找到ID为 {subject_id} 的动漫"
                ).model_dump()
            )
        
        return success_response(data=result, message="获取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取Bangumi动漫详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取详情失败: {str(e)}"
            ).model_dump()
        )


@router.get("/calendar", response_model=BaseResponse)
async def get_bangumi_calendar():
    """
    获取Bangumi每日放送日历
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [CalendarItem, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        client = BangumiClient()
        results = await client.get_calendar()
        
        return success_response(data=results, message="获取成功")
    except Exception as e:
        logger.error(f"获取Bangumi日历失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取日历失败: {str(e)}"
            ).model_dump()
        )


@router.get("/popular", response_model=BaseResponse)
async def get_bangumi_popular(
    limit: int = Query(20, ge=1, le=100, description="返回数量")
):
    """
    获取Bangumi热门动漫
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [AnimeItem, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        client = BangumiClient()
        results = await client.get_popular_anime(limit=limit)
        
        return success_response(data=results, message="获取成功")
    except Exception as e:
        logger.error(f"获取Bangumi热门动漫失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取热门动漫失败: {str(e)}"
            ).model_dump()
        )

