"""
有声书播放进度服务

提供用户有声书播放进度的读取和更新功能
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.user_audiobook_progress import UserAudiobookProgress
from app.utils.time import utcnow


async def get_progress_for_work(
    db: AsyncSession,
    user_id: int,
    ebook_id: int,
) -> Optional[UserAudiobookProgress]:
    """
    获取用户对指定作品的播放进度
    
    Args:
        db: 数据库会话
        user_id: 用户 ID
        ebook_id: 作品 ID
    
    Returns:
        播放进度记录，如果不存在则返回 None
    """
    try:
        stmt = select(UserAudiobookProgress).where(
            UserAudiobookProgress.user_id == user_id,
            UserAudiobookProgress.ebook_id == ebook_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Failed to get progress for work: {e}", exc_info=True)
        return None


async def upsert_progress(
    db: AsyncSession,
    user_id: int,
    ebook_id: int,
    audiobook_file_id: int,
    position_seconds: int,
    duration_seconds: Optional[int] = None,
) -> UserAudiobookProgress:
    """
    更新或创建播放进度
    
    Args:
        db: 数据库会话
        user_id: 用户 ID
        ebook_id: 作品 ID
        audiobook_file_id: 当前播放到的章节文件 ID
        position_seconds: 当前章节播放到的秒数
        duration_seconds: 当前章节总时长（可选）
    
    Returns:
        更新后的播放进度记录
    """
    now = utcnow()
    
    # 查询现有记录
    existing = await get_progress_for_work(db, user_id, ebook_id)
    
    if existing:
        # 更新现有记录
        existing.audiobook_file_id = audiobook_file_id
        existing.position_seconds = position_seconds
        existing.duration_seconds = duration_seconds
        existing.last_played_at = now
        existing.updated_at = now
        # 如果播放位置接近结束，标记为已完成
        if duration_seconds and position_seconds >= duration_seconds * 0.95:
            existing.is_finished = True
        else:
            existing.is_finished = False
    else:
        # 创建新记录
        existing = UserAudiobookProgress(
            user_id=user_id,
            ebook_id=ebook_id,
            audiobook_file_id=audiobook_file_id,
            position_seconds=position_seconds,
            duration_seconds=duration_seconds,
            last_played_at=now,
            is_finished=False
        )
        db.add(existing)
    
    try:
        await db.commit()
        await db.refresh(existing)
        return existing
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to upsert progress: {e}", exc_info=True)
        raise


async def mark_finished(
    db: AsyncSession,
    user_id: int,
    ebook_id: int,
) -> Optional[UserAudiobookProgress]:
    """
    标记作品为已听完
    
    Args:
        db: 数据库会话
        user_id: 用户 ID
        ebook_id: 作品 ID
    
    Returns:
        更新后的播放进度记录，如果不存在则返回 None
    """
    progress = await get_progress_for_work(db, user_id, ebook_id)
    if not progress:
        return None
    
    progress.is_finished = True
    progress.updated_at = utcnow()
    
    try:
        await db.commit()
        await db.refresh(progress)
        return progress
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to mark finished: {e}", exc_info=True)
        raise

