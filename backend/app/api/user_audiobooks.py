"""
用户有声书播放进度 API

提供用户有声书播放进度的查询和更新功能
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from app.core.database import get_db
from app.api.auth import oauth2_scheme
from app.core.security import decode_access_token
from app.models.user import User
from app.models.ebook import EBook
from app.models.audiobook import AudiobookFile
from app.modules.audiobook.progress_service import (
    get_progress_for_work,
    upsert_progress,
)
from app.schemas.audiobook import (
    UserWorkAudiobookStatus,
    UserAudiobookChapter,
    UpdateAudiobookProgressRequest,
)

router = APIRouter()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户对象"""
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


def _format_duration(seconds: int) -> str:
    """格式化时长为 HH:MM:SS 或 MM:SS"""
    if seconds < 0:
        return "00:00"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


@router.get("/progress/by-ebook/{ebook_id}", response_model=UserWorkAudiobookStatus, summary="获取作品有声书状态")
async def get_work_audiobook_status(
    ebook_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户对指定作品的有声书播放状态
    
    包括章节列表、当前播放位置等信息。
    """
    try:
        # 验证作品存在
        ebook_stmt = select(EBook).where(EBook.id == ebook_id)
        ebook_result = await db.execute(ebook_stmt)
        ebook = ebook_result.scalar_one_or_none()
        
        if not ebook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="EBook not found"
            )
        
        # 查询该作品的所有有声书文件
        files_stmt = select(AudiobookFile).where(
            AudiobookFile.ebook_id == ebook_id,
            AudiobookFile.is_deleted == False
        ).order_by(AudiobookFile.id)  # 按 ID 排序，后续可以改为按 track_number
        
        files_result = await db.execute(files_stmt)
        audiobook_files = files_result.scalars().all()
        
        if not audiobook_files:
            return UserWorkAudiobookStatus(
                has_audiobook=False,
                current_file_id=None,
                current_position_seconds=0,
                current_duration_seconds=None,
                progress_percent=None,
                chapters=[]
            )
        
        # 构建章节列表
        chapters: List[UserAudiobookChapter] = []
        for idx, file in enumerate(audiobook_files):
            # 生成章节标题（如果没有其他标题字段，使用默认格式）
            title = f"第 {idx + 1} 章"
            # 如果有其他标题字段，可以在这里使用
            
            chapters.append(UserAudiobookChapter(
                file_id=file.id,
                title=title,
                duration_seconds=file.duration_seconds,
                is_tts_generated=file.is_tts_generated or False,
                tts_provider=file.tts_provider,
                order=idx + 1
            ))
        
        # 查询播放进度
        progress = await get_progress_for_work(db, current_user.id, ebook_id)
        
        # 确定当前文件 ID 和位置
        if progress and progress.audiobook_file_id:
            # 验证该文件确实属于这个作品
            current_file = next((f for f in audiobook_files if f.id == progress.audiobook_file_id), None)
            if current_file:
                current_file_id = progress.audiobook_file_id
                current_position_seconds = progress.position_seconds
                current_duration_seconds = progress.duration_seconds or current_file.duration_seconds
            else:
                # 如果进度中的文件不存在，使用第一章
                current_file_id = chapters[0].file_id if chapters else None
                current_position_seconds = 0
                current_duration_seconds = chapters[0].duration_seconds if chapters else None
        else:
            # 没有进度记录，默认第一章
            current_file_id = chapters[0].file_id if chapters else None
            current_position_seconds = 0
            current_duration_seconds = chapters[0].duration_seconds if chapters else None
        
        # 计算进度百分比
        progress_percent = None
        if current_duration_seconds and current_duration_seconds > 0:
            progress_percent = (current_position_seconds / current_duration_seconds) * 100
            progress_percent = min(100.0, max(0.0, progress_percent))
        
        return UserWorkAudiobookStatus(
            has_audiobook=True,
            current_file_id=current_file_id,
            current_position_seconds=current_position_seconds,
            current_duration_seconds=current_duration_seconds,
            progress_percent=progress_percent,
            chapters=chapters
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get work audiobook status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audiobook status: {str(e)}"
        )


@router.post("/progress/by-ebook/{ebook_id}", response_model=UserWorkAudiobookStatus, summary="更新作品有声书进度")
async def update_work_audiobook_progress(
    ebook_id: int,
    req: UpdateAudiobookProgressRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    更新用户对指定作品的播放进度
    
    需要验证 audiobook_file_id 确实属于该 ebook_id。
    """
    try:
        # 验证作品存在
        ebook_stmt = select(EBook).where(EBook.id == ebook_id)
        ebook_result = await db.execute(ebook_stmt)
        ebook = ebook_result.scalar_one_or_none()
        
        if not ebook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="EBook not found"
            )
        
        # 验证文件属于该作品
        file_stmt = select(AudiobookFile).where(
            AudiobookFile.id == req.audiobook_file_id,
            AudiobookFile.ebook_id == ebook_id,
            AudiobookFile.is_deleted == False
        )
        file_result = await db.execute(file_stmt)
        audiobook_file = file_result.scalar_one_or_none()
        
        if not audiobook_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audiobook file does not belong to this ebook"
            )
        
        # 更新进度
        await upsert_progress(
            db=db,
            user_id=current_user.id,
            ebook_id=ebook_id,
            audiobook_file_id=req.audiobook_file_id,
            position_seconds=req.position_seconds,
            duration_seconds=req.duration_seconds,
        )
        
        # 返回更新后的状态（复用 get_work_audiobook_status 的逻辑）
        return await get_work_audiobook_status(ebook_id, current_user, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update work audiobook progress: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update progress: {str(e)}"
        )

