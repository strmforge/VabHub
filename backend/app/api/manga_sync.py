"""
漫画同步 API（追更）
"""
from fastapi import APIRouter, Depends, HTTPException, status, Path as PathParam, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from app.core.database import get_db
from app.core.schemas import BaseResponse, success_response
from app.core.dependencies import get_current_user, get_current_admin_user
from app.models.user import User
from app.services.manga_sync_service import (
    sync_series_from_remote,
    sync_all_favorite_series,
)

router = APIRouter(prefix="/api/manga/local/sync", tags=["漫画同步"])


@router.post("/series/{series_id}", response_model=BaseResponse, summary="同步单个系列")
async def sync_single_series(
    series_id: int = PathParam(..., description="系列 ID"),
    download_new: bool = Body(False, description="是否自动下载新章节"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    对单个系列执行追更
    
    从远程源同步新增章节，创建本地 PENDING 记录
    """
    try:
        sync_result = await sync_series_from_remote(
            session=db,
            series_id=series_id,
            download_new=download_new
        )
        
        new_chapters = sync_result.get("new_chapters", 0) if isinstance(sync_result, dict) else sync_result
        message = f"同步完成，新增 {new_chapters} 个章节"
        
        return success_response(
            data=sync_result if isinstance(sync_result, dict) else {"new_chapters": sync_result},
            message=message
        )
    except Exception as e:
        logger.error(f"同步系列失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"同步失败: {str(e)}"
        )


@router.get("/series/{series_id}/status", response_model=BaseResponse, summary="查询系列同步状态")
async def get_series_sync_status(
    series_id: int = PathParam(..., description="系列 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取指定系列的最近同步状态
    
    返回上次同步时间、新章节数量等信息
    """
    try:
        from sqlalchemy import select
        from app.models.manga_series_local import MangaSeriesLocal
        
        stmt = select(MangaSeriesLocal).where(MangaSeriesLocal.id == series_id)
        result = await db.execute(stmt)
        series = result.scalar_one_or_none()
        
        if not series:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="系列不存在"
            )
        
        # 计算未读章节总数
        from app.models.manga_chapter_local import MangaChapterLocal, MangaChapterStatus
        stmt = select(func.count(MangaChapterLocal.id)).where(
            MangaChapterLocal.series_id == series_id,
            MangaChapterLocal.status.in_([MangaChapterStatus.PENDING, MangaChapterStatus.DOWNLOADING])
        )
        result = await db.execute(stmt)
        pending_chapters = result.scalar() or 0
        
        return success_response(
            data={
                "series_id": series.id,
                "series_title": series.title,
                "last_sync_at": series.last_sync_at.isoformat() if series.last_sync_at else None,
                "total_chapters": series.total_chapters or 0,
                "downloaded_chapters": series.downloaded_chapters or 0,
                "new_chapter_count": series.new_chapter_count or 0,
                "pending_chapters": pending_chapters,
                "has_updates": (series.new_chapter_count or 0) > 0 or pending_chapters > 0
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询系列同步状态失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )


@router.get("/favorites/overview", response_model=BaseResponse, summary="获取收藏漫画追更概览")
async def get_favorites_sync_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户收藏漫画的同步状态概览
    
    返回有多少收藏系列有更新、上次同步时间等
    """
    try:
        from sqlalchemy import select, func, and_
        from app.models.user_favorite_media import UserFavoriteMedia
        from app.models.manga_series_local import MangaSeriesLocal
        from app.models.enums.reading_media_type import ReadingMediaType
        
        # 获取用户收藏的漫画系列
        stmt = select(MangaSeriesLocal).join(
            UserFavoriteMedia, 
            and_(
                UserFavoriteMedia.target_id == MangaSeriesLocal.id,
                UserFavoriteMedia.media_type == ReadingMediaType.MANGA,
                UserFavoriteMedia.user_id == current_user.id
            )
        )
        result = await db.execute(stmt)
        favorite_series = result.scalars().all()
        
        total_favorites = len(favorite_series)
        series_with_updates = 0
        total_new_chapters = 0
        recent_sync_count = 0
        
        from datetime import datetime, timedelta
        one_day_ago = datetime.now() - timedelta(days=1)
        
        for series in favorite_series:
            if (series.new_chapter_count or 0) > 0:
                series_with_updates += 1
                total_new_chapters += series.new_chapter_count or 0
            
            if series.last_sync_at and series.last_sync_at > one_day_ago:
                recent_sync_count += 1
        
        return success_response(
            data={
                "total_favorites": total_favorites,
                "series_with_updates": series_with_updates,
                "total_new_chapters": total_new_chapters,
                "recent_sync_count": recent_sync_count,
                "last_sync_time": max((s.last_sync_at for s in favorite_series if s.last_sync_at), default=None)
            }
        )
    except Exception as e:
        logger.error(f"获取收藏漫画概览失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )


@router.post("/favorites", response_model=BaseResponse, summary="同步所有收藏系列")
async def sync_favorites(
    download_new: bool = Body(False, description="是否自动下载新章节"),
    limit: int = Body(20, description="最多同步的系列数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    对所有收藏的系列执行批量追更
    
    仅管理员可访问，避免普通用户一键刷全库
    """
    try:
        sync_result = await sync_all_favorite_series(
            session=db,
            limit=limit,
            download_new=download_new
        )
        
        return success_response(
            data=sync_result,
            message=f"批量同步完成"
        )
    except Exception as e:
        logger.error(f"批量同步失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量同步失败: {str(e)}"
        )

