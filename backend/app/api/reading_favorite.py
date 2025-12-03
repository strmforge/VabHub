"""
阅读收藏 API
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.enums.reading_media_type import ReadingMediaType
from app.schemas.user_favorite_media import UserFavoriteMediaCreate, UserFavoriteMediaRead
from app.schemas.reading_hub import ReadingShelfItem
from app.services.reading_favorite_service import (
    add_favorite,
    remove_favorite,
    is_favorite,
    list_favorites,
)

router = APIRouter()


@router.post("/", response_model=UserFavoriteMediaRead)
async def add_favorite_endpoint(
    data: UserFavoriteMediaCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """收藏媒体"""
    try:
        return await add_favorite(db, current_user.id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"收藏失败: {str(e)}")


@router.delete("/")
async def remove_favorite_endpoint(
    media_type: ReadingMediaType = Query(..., description="媒体类型"),
    target_id: int = Query(..., description="目标资源ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消收藏"""
    try:
        await remove_favorite(db, current_user.id, media_type, target_id)
        return {"ok": True, "message": "取消收藏成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"取消收藏失败: {str(e)}")


@router.get("/exists")
async def check_favorite_exists(
    media_type: ReadingMediaType = Query(..., description="媒体类型"),
    target_id: int = Query(..., description="目标资源ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """检查是否收藏"""
    try:
        is_fav = await is_favorite(db, current_user.id, media_type, target_id)
        return {"is_favorite": is_fav}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"检查收藏状态失败: {str(e)}")


@router.get("/", response_model=List[ReadingShelfItem])
async def list_favorites_endpoint(
    media_type: Optional[ReadingMediaType] = Query(None, description="媒体类型筛选"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取收藏列表"""
    try:
        return await list_favorites(db, current_user.id, media_type, limit, offset)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取收藏列表失败: {str(e)}")