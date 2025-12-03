"""
漫画阅读进度 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Path as PathParam, Query
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.core.schemas import BaseResponse, success_response
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.manga_reading_progress import (
    MangaReadingProgressRead,
    MangaReadingProgressUpdate,
    MangaReadingHistoryItem,
)
from app.services.manga_progress_service import (
    get_progress_for_series,
    upsert_progress,
    list_reading_history,
)

router = APIRouter(prefix="/api/manga/local/progress", tags=["漫画阅读进度"])


@router.get("/series/{series_id}", response_model=BaseResponse, summary="获取某系列阅读进度")
async def get_series_progress(
    series_id: int = PathParam(..., description="系列 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户在某个系列上的阅读进度
    
    如果没有记录，返回 null
    """
    try:
        progress = await get_progress_for_series(
            session=db,
            user_id=current_user.id,
            series_id=series_id
        )
        
        return success_response(
            data=progress.model_dump() if progress else None,
            message="获取进度成功"
        )
    except Exception as e:
        logger.error(f"获取阅读进度失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取进度失败: {str(e)}"
        )


@router.post("/series/{series_id}", response_model=BaseResponse, summary="更新阅读进度")
async def update_series_progress(
    series_id: int = PathParam(..., description="系列 ID"),
    payload: MangaReadingProgressUpdate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新或创建阅读进度（Upsert）
    
    前端可在章节切换、翻页、离开阅读器时调用
    """
    try:
        # 确保 series_id 一致
        payload.series_id = series_id
        
        progress = await upsert_progress(
            session=db,
            user_id=current_user.id,
            data=payload
        )
        
        return success_response(
            data=progress.model_dump(),
            message="更新进度成功"
        )
    except Exception as e:
        logger.error(f"更新阅读进度失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新进度失败: {str(e)}"
        )


@router.get("/history", response_model=BaseResponse, summary="获取阅读历史")
async def get_reading_history(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取用户最近阅读的漫画列表
    
    按 last_read_at 降序排列
    """
    try:
        history = await list_reading_history(
            session=db,
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        
        return success_response(
            data=[item.model_dump() for item in history],
            message="获取阅读历史成功"
        )
    except Exception as e:
        logger.error(f"获取阅读历史失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取阅读历史失败: {str(e)}"
        )

