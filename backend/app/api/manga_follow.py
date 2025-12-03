"""漫画追更 API

提供最小追更能力：
- follow: 关注某个本地漫画系列
- unfollow: 取消关注
- list_following: 列出当前用户追更中的漫画
- mark_read: 标记某个系列为已读（清零未读数）
- remote_follow: 关注外部源漫画（不下载章节）
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Path as PathParam, Body
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.schemas import BaseResponse, success_response
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.manga_series_local import MangaSeriesLocal
from app.models.manga_source import MangaSource
from app.services.manga_follow_service import (
    follow_series,
    unfollow_series,
    list_following,
    mark_read,
    follow_remote_series,
)
from app.schemas.manga_follow import FollowedMangaItem


router = APIRouter(prefix="/api/manga/local", tags=["漫画追更"])


async def _ensure_series_exists(
    session: AsyncSession,
    series_id: int,
) -> MangaSeriesLocal:
    """内部工具：检查系列是否存在，不存在则抛 404。"""
    stmt = select(MangaSeriesLocal).where(MangaSeriesLocal.id == series_id)
    result = await session.execute(stmt)
    series = result.scalar_one_or_none()
    if not series:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"系列不存在 (ID: {series_id})",
        )
    return series


@router.post("/series/{series_id}/follow", response_model=BaseResponse, summary="关注漫画系列")
async def follow_manga_series(
    series_id: int = PathParam(..., description="系列 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """当前用户开始追更某个本地漫画系列。"""
    try:
        await _ensure_series_exists(db, series_id)

        follow = await follow_series(
            session=db,
            user_id=current_user.id,
            series_id=series_id,
        )
        return success_response(
            data=follow.model_dump(),
            message="关注成功",
        )
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"关注漫画系列失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"关注失败: {str(e)}",
        )


@router.post("/series/{series_id}/unfollow", response_model=BaseResponse, summary="取消关注漫画系列")
async def unfollow_manga_series(
    series_id: int = PathParam(..., description="系列 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """当前用户取消对某个漫画系列的追更。

    幂等：即使追更记录不存在也视为成功。
    """
    try:
        await _ensure_series_exists(db, series_id)

        removed = await unfollow_series(
            session=db,
            user_id=current_user.id,
            series_id=series_id,
        )
        if not removed:
            message = "未找到追更记录，视为已取消关注"
        else:
            message = "取消关注成功"
        return success_response(data={"removed": removed}, message=message)
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"取消关注漫画系列失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消关注失败: {str(e)}",
        )


@router.get("/following", response_model=BaseResponse, summary="列出当前用户追更中的漫画系列")
async def list_following_manga(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出当前用户所有追更中的漫画系列。"""
    try:
        items: list[FollowedMangaItem] = await list_following(
            session=db,
            user_id=current_user.id,
        )
        return success_response(
            data=[item.model_dump() for item in items],
            message="获取追更列表成功",
        )
    except Exception as e:  # noqa: BLE001
        logger.error(f"获取追更列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取追更列表失败: {str(e)}",
        )


@router.post("/series/{series_id}/mark_read", response_model=BaseResponse, summary="标记漫画系列为已读")
async def mark_manga_series_read(
    series_id: int = PathParam(..., description="系列 ID"),
    last_seen_chapter_id: Optional[int] = Body(None, description="最近阅读的章节 ID，可选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """标记某个系列为已读或更新 last_seen_chapter_id，并清零未读计数。"""
    try:
        await _ensure_series_exists(db, series_id)

        follow = await mark_read(
            session=db,
            user_id=current_user.id,
            series_id=series_id,
            last_seen_chapter_id=last_seen_chapter_id,
        )
        # 没有追更记录时视为幂等成功
        if not follow:
            return success_response(
                data=None,
                message="未找到追更记录，视为已标记",
            )

        return success_response(
            data=follow.model_dump(),
            message="标记已读成功",
        )
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"标记漫画系列为已读失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"标记失败: {str(e)}",
        )


@router.post("/remote/follow", response_model=BaseResponse, summary="关注外部源漫画系列")
async def follow_remote_manga_series(
    source_id: int = Body(..., description="漫画源 ID"),
    remote_series_id: str = Body(..., description="远程漫画系列 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    关注外部源漫画系列（不下载章节）
    
    创建MangaSeriesLocal记录（仅元数据）和UserMangaFollow追更记录
    """
    try:
        # 验证源存在且启用
        source_stmt = select(MangaSource).where(
            MangaSource.id == source_id,
            MangaSource.is_enabled == True  # noqa: E712
        )
        source_result = await db.execute(source_stmt)
        source = source_result.scalar_one_or_none()
        
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"漫画源不存在或未启用 (ID: {source_id})"
            )
        
        follow = await follow_remote_series(
            session=db,
            user_id=current_user.id,
            source_id=source_id,
            remote_series_id=remote_series_id,
        )
        
        return success_response(
            data=follow.model_dump(),
            message="关注外部漫画成功",
        )
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        logger.error(f"关注外部漫画系列失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"关注失败: {str(e)}",
        )
