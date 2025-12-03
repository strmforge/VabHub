"""
视频播放进度API

提供视频进度的查询、更新、删除等接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from typing import List, Optional

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.user_video_progress import UserVideoProgress
from app.schemas.video_progress import (
    VideoProgressResponse,
    VideoProgressUpdate,
    VideoProgressListResponse
)
from app.utils.time import utcnow

router = APIRouter(prefix="/api/video-progress", tags=["video-progress"])


@router.get("/{work_id}", response_model=VideoProgressResponse)
async def get_video_progress(
    work_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取指定作品的播放进度"""
    try:
        # 查询用户对该作品的播放进度
        stmt = select(UserVideoProgress).filter(
            UserVideoProgress.user_id == current_user.id,
            UserVideoProgress.work_id == work_id
        )
        result = await db.execute(stmt)
        progress = result.scalar_one_or_none()
        
        if not progress:
            # 返回空进度
            return VideoProgressResponse(
                work_id=work_id,
                position_seconds=0.0,
                duration_seconds=None,
                progress_percent=0.0,
                is_finished=False,
                has_progress=False,
                source_type=None,
                last_played_at=None,
                updated_at=utcnow()
            )
        
        return VideoProgressResponse(
            work_id=progress.work_id,
            position_seconds=progress.position_seconds,
            duration_seconds=progress.duration_seconds,
            progress_percent=progress.progress_percent,
            is_finished=progress.is_finished,
            has_progress=True,
            source_type=progress.source_type,
            last_played_at=progress.last_played_at,
            updated_at=progress.updated_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取播放进度失败: {str(e)}")


@router.post("/{work_id}", response_model=VideoProgressResponse)
async def update_video_progress(
    work_id: int,
    progress_data: VideoProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新指定作品的播放进度"""
    try:
        # 查询现有进度
        stmt = select(UserVideoProgress).filter(
            UserVideoProgress.user_id == current_user.id,
            UserVideoProgress.work_id == work_id
        )
        result = await db.execute(stmt)
        progress = result.scalar_one_or_none()
        
        if not progress:
            # 创建新进度记录
            progress = UserVideoProgress(
                user_id=current_user.id,
                work_id=work_id,
                tmdb_id=progress_data.tmdb_id,
                position_seconds=progress_data.position_seconds,
                duration_seconds=progress_data.duration_seconds,
                progress_percent=progress_data.progress_percent,
                is_finished=progress_data.is_finished,
                source_type=progress_data.source_type,
                last_play_url=progress_data.last_play_url,
                last_played_at=utcnow()
            )
            db.add(progress)
        else:
            # 更新现有记录
            progress.position_seconds = progress_data.position_seconds
            progress.duration_seconds = progress_data.duration_seconds
            progress.progress_percent = progress_data.progress_percent
            progress.is_finished = progress_data.is_finished
            progress.source_type = progress_data.source_type
            progress.last_play_url = progress_data.last_play_url
            progress.last_played_at = utcnow()
            
            # 如果提供了TMDB ID，也更新
            if progress_data.tmdb_id:
                progress.tmdb_id = progress_data.tmdb_id
        
        await db.commit()
        await db.refresh(progress)
        
        return VideoProgressResponse(
            work_id=progress.work_id,
            position_seconds=progress.position_seconds,
            duration_seconds=progress.duration_seconds,
            progress_percent=progress.progress_percent,
            is_finished=progress.is_finished,
            has_progress=True,
            source_type=progress.source_type,
            last_played_at=progress.last_played_at,
            updated_at=progress.updated_at
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新播放进度失败: {str(e)}")


@router.delete("/{work_id}")
async def delete_video_progress(
    work_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除指定作品的播放进度"""
    try:
        # 查询进度记录
        stmt = select(UserVideoProgress).filter(
            UserVideoProgress.user_id == current_user.id,
            UserVideoProgress.work_id == work_id
        )
        result = await db.execute(stmt)
        progress = result.scalar_one_or_none()
        
        if not progress:
            raise HTTPException(status_code=404, detail="播放进度不存在")
        
        await db.delete(progress)
        await db.commit()
        
        return {"message": "播放进度已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除播放进度失败: {str(e)}")


@router.get("/", response_model=VideoProgressListResponse)
async def list_video_progress(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    only_finished: bool = Query(False, description="只显示已完成的"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的播放进度列表"""
    try:
        # 构建查询
        stmt = select(UserVideoProgress).filter(
            UserVideoProgress.user_id == current_user.id
        )
        
        if only_finished:
            stmt = stmt.filter(UserVideoProgress.is_finished == True)
        
        # 获取总数
        count_stmt = select(func.count()).select_from(
            stmt.subquery()
        )
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()
        
        # 分页查询
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await db.execute(stmt)
        items = result.scalars().all()
        
        return VideoProgressListResponse(
            items=[
                VideoProgressResponse(
                    work_id=item.work_id,
                    position_seconds=item.position_seconds,
                    duration_seconds=item.duration_seconds,
                    progress_percent=item.progress_percent,
                    is_finished=item.is_finished,
                    has_progress=True,
                    source_type=item.source_type,
                    last_played_at=item.last_played_at,
                    updated_at=item.updated_at
                )
                for item in items
            ],
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取播放进度列表失败: {str(e)}")
