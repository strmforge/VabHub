"""
115 远程视频播放 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.api.auth import oauth2_scheme
from app.core.security import decode_access_token
from app.models.user import User
from app.schemas.remote_115 import (
    Remote115VideoPlayOptions,
    Update115VideoProgressRequest,
)
from app.modules.remote_playback.remote_115_service import Remote115PlaybackService
from app.core.schemas import BaseResponse, success_response, error_response

router = APIRouter()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户对象"""
    from fastapi import HTTPException, status
    
    payload = decode_access_token(token)
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user = await User.get_by_username(db, username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


@router.get(
    "/remote/115/videos/{work_id}/play-options",
    response_model=BaseResponse,
    summary="获取 115 视频播放选项"
)
async def get_115_video_play_options(
    work_id: int = Path(..., description="作品 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取指定作品的 115 视频播放选项
    
    包括播放地址、清晰度列表、字幕列表、观看进度等
    """
    try:
        service = Remote115PlaybackService(db)
        result = await service.get_115_video_play_options(work_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("message", "未找到该作品的 115 绑定")
            )
        
        # 转换为响应格式
        play_options = Remote115VideoPlayOptions(
            work_id=result["work_id"],
            pick_code=result["pick_code"],
            file_name=result["file_name"],
            duration=result["duration"],
            qualities=result["qualities"],
            subtitles=result["subtitles"],
            progress=result.get("progress")
        )
        
        return success_response(data=play_options.model_dump(), message="获取播放选项成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 115 视频播放选项失败 (work_id={work_id}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取播放选项失败: {str(e)}"
        )


@router.post(
    "/remote/115/videos/{work_id}/progress",
    response_model=BaseResponse,
    summary="更新 115 视频观看进度"
)
async def update_115_video_progress(
    work_id: int = Path(..., description="作品 ID"),
    req: Update115VideoProgressRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新指定作品的 115 视频观看进度
    """
    try:
        service = Remote115PlaybackService(db)
        result = await service.update_115_video_progress(
            work_id,
            req.position,
            req.finished
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "更新观看进度失败")
            )
        
        return success_response(message="更新观看进度成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新 115 视频观看进度失败 (work_id={work_id}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新观看进度失败: {str(e)}"
        )

