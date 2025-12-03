"""
阅读中心 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.core.schemas import BaseResponse, success_response
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.enums.reading_media_type import ReadingMediaType
from app.schemas.reading_hub import (
    ReadingOngoingItem,
    ReadingHistoryItem,
    ReadingStats,
)
from app.services.reading_hub_service import (
    list_ongoing_reading,
    list_reading_history,
    get_reading_stats,
    get_recent_activity,
)
from app.schemas.reading_hub import ReadingActivityItem

router = APIRouter(prefix="/api/reading", tags=["阅读中心"])


@router.get("/ongoing", response_model=BaseResponse, summary="获取正在进行的阅读列表")
async def get_ongoing_reading(
    limit_per_type: int = Query(10, ge=1, le=50, description="每种媒体类型最多返回数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户"正在进行"的阅读/收听项目
    
    聚合小说、有声书、漫画的未完成进度，按最后阅读时间降序排列
    """
    try:
        items = await list_ongoing_reading(
            session=db,
            user_id=current_user.id,
            limit_per_type=limit_per_type
        )
        
        return success_response(
            data=[item.model_dump() for item in items],
            message="获取正在进行列表成功"
        )
    except Exception as e:
        logger.error(f"获取正在进行列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取列表失败: {str(e)}"
        )


@router.get("/history", response_model=BaseResponse, summary="获取阅读历史")
async def get_reading_history(
    limit: int = Query(30, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    media_type: Optional[ReadingMediaType] = Query(None, description="媒体类型过滤"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取用户阅读历史
    
    聚合小说、有声书、漫画的历史记录，按最后阅读时间降序排列
    支持按媒体类型过滤
    """
    try:
        items = await list_reading_history(
            session=db,
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            media_type=media_type
        )
        
        return success_response(
            data=[item.model_dump() for item in items],
            message="获取阅读历史成功"
        )
    except Exception as e:
        logger.error(f"获取阅读历史失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取历史失败: {str(e)}"
        )


@router.get("/stats", response_model=BaseResponse, summary="获取阅读统计")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取阅读统计信息
    
    包括进行中数量、最近30天完成数量、各类型统计
    """
    try:
        stats = await get_reading_stats(
            session=db,
            user_id=current_user.id
        )
        
        return success_response(
            data=stats,
            message="获取统计信息成功"
        )
    except Exception as e:
        logger.error(f"获取阅读统计失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计失败: {str(e)}"
        )


@router.get("/recent_activity", response_model=BaseResponse, summary="获取最近阅读活动时间线")
async def get_recent_activity_api(
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取最近阅读活动时间线
    
    聚合小说、有声书、漫画的最近活动，按时间倒序排列
    用于阅读中心的时间线视图
    """
    try:
        items = await get_recent_activity(
            session=db,
            user_id=current_user.id,
            limit=limit
        )
        
        return success_response(
            data=[item.model_dump() for item in items],
            message="获取活动时间线成功"
        )
    except Exception as e:
        logger.error(f"获取活动时间线失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取活动时间线失败: {str(e)}"
        )
