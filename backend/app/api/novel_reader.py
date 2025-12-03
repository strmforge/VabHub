"""
小说阅读器 API

提供章节列表、章节正文、阅读进度等功能
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.core.database import get_db
from app.api.auth import oauth2_scheme
from app.core.security import decode_access_token
from app.models.user import User
from app.models.ebook import EBook
from app.models.user_novel_reading_progress import UserNovelReadingProgress
from app.schemas.novel_reader import (
    NovelChapterSummary,
    NovelChapterTextResponse,
    UserNovelReadingProgressResponse,
    UpdateNovelReadingProgressRequest,
    NovelSearchHit,
)
from app.modules.novel.reader_service import get_chapters_from_ebook, get_chapter_content
from app.modules.novel.search_service import search_novel
from app.utils.time import utcnow

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


@router.get("/novels/{ebook_id}/chapters", response_model=List[NovelChapterSummary], summary="获取小说章节列表")
async def get_novel_chapters(
    ebook_id: int = Path(..., description="作品 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取指定小说的章节列表
    """
    try:
        # 查询 EBook
        stmt = select(EBook).where(EBook.id == ebook_id)
        result = await db.execute(stmt)
        ebook = result.scalar_one_or_none()
        
        if not ebook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"EBook {ebook_id} not found"
            )
        
        # 获取章节列表
        chapters = await get_chapters_from_ebook(ebook)
        
        # 转换为响应格式
        summaries = []
        for idx, chapter in enumerate(chapters):
            summaries.append(NovelChapterSummary(
                index=idx,  # API 使用从 0 开始的索引
                title=chapter.title,
                length=len(chapter.content) if chapter.content else None
            ))
        
        return summaries
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节列表失败 (ebook_id={ebook_id}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取章节列表失败: {str(e)}"
        )


@router.get("/novels/{ebook_id}/chapters/{chapter_index}", response_model=NovelChapterTextResponse, summary="获取章节正文")
async def get_novel_chapter_text(
    ebook_id: int = Path(..., description="作品 ID"),
    chapter_index: int = Path(..., ge=0, description="章节索引（从 0 开始）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取指定章节的正文内容
    """
    try:
        # 查询 EBook
        stmt = select(EBook).where(EBook.id == ebook_id)
        result = await db.execute(stmt)
        ebook = result.scalar_one_or_none()
        
        if not ebook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"EBook {ebook_id} not found"
            )
        
        # 获取章节内容
        chapter = await get_chapter_content(ebook, chapter_index)
        
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter {chapter_index} not found for EBook {ebook_id}"
            )
        
        return NovelChapterTextResponse(
            ebook_id=ebook_id,
            chapter_index=chapter_index,
            title=chapter.title,
            content=chapter.content or ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节正文失败 (ebook_id={ebook_id}, chapter_index={chapter_index}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取章节正文失败: {str(e)}"
        )


@router.get("/user/novels/reading-progress/by-ebook/{ebook_id}", response_model=UserNovelReadingProgressResponse, summary="获取阅读进度")
async def get_reading_progress_for_ebook(
    ebook_id: int = Path(..., description="作品 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取指定作品的阅读进度
    """
    try:
        # 查询阅读进度
        stmt = (
            select(UserNovelReadingProgress)
            .where(
                UserNovelReadingProgress.user_id == current_user.id,
                UserNovelReadingProgress.ebook_id == ebook_id
            )
        )
        result = await db.execute(stmt)
        progress = result.scalar_one_or_none()
        
        # 如果没有记录，返回默认值
        if not progress:
            return UserNovelReadingProgressResponse(
                ebook_id=ebook_id,
                current_chapter_index=0,
                chapter_offset=0,
                is_finished=False,
                last_read_at=utcnow()
            )
        
        return UserNovelReadingProgressResponse(
            ebook_id=progress.ebook_id,
            current_chapter_index=progress.current_chapter_index,
            chapter_offset=progress.chapter_offset,
            is_finished=progress.is_finished,
            last_read_at=progress.last_read_at
        )
        
    except Exception as e:
        logger.error(f"获取阅读进度失败 (ebook_id={ebook_id}, user_id={current_user.id}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取阅读进度失败: {str(e)}"
        )


@router.post("/user/novels/reading-progress/by-ebook/{ebook_id}", response_model=UserNovelReadingProgressResponse, summary="更新阅读进度")
async def update_reading_progress_for_ebook(
    ebook_id: int = Path(..., description="作品 ID"),
    req: UpdateNovelReadingProgressRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新阅读进度
    """
    try:
        # 查询现有进度
        stmt = (
            select(UserNovelReadingProgress)
            .where(
                UserNovelReadingProgress.user_id == current_user.id,
                UserNovelReadingProgress.ebook_id == ebook_id
            )
        )
        result = await db.execute(stmt)
        progress = result.scalar_one_or_none()
        
        now = utcnow()
        
        # 如果没有记录，创建新记录
        if not progress:
            progress = UserNovelReadingProgress(
                user_id=current_user.id,
                ebook_id=ebook_id,
                current_chapter_index=req.current_chapter_index,
                chapter_offset=req.chapter_offset,
                is_finished=req.is_finished or False,
                last_read_at=now
            )
            db.add(progress)
        else:
            # 更新现有记录
            progress.current_chapter_index = req.current_chapter_index
            progress.chapter_offset = req.chapter_offset
            if req.is_finished is not None:
                progress.is_finished = req.is_finished
                # 如果标记为已完成，将 offset 视为末尾（可以设为一个很大的值或章节长度）
                if req.is_finished:
                    progress.chapter_offset = 999999  # 表示已读完
            progress.last_read_at = now
        
        await db.commit()
        await db.refresh(progress)
        
        return UserNovelReadingProgressResponse(
            ebook_id=progress.ebook_id,
            current_chapter_index=progress.current_chapter_index,
            chapter_offset=progress.chapter_offset,
            is_finished=progress.is_finished,
            last_read_at=progress.last_read_at
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"更新阅读进度失败 (ebook_id={ebook_id}, user_id={current_user.id}): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新阅读进度失败: {str(e)}"
        )


@router.get(
    "/novels/{ebook_id}/search",
    response_model=List[NovelSearchHit],
    summary="书内搜索"
)
async def search_in_novel(
    ebook_id: int = Path(..., description="作品 ID"),
    q: str = Query(..., min_length=1, description="搜索关键字"),
    max_hits: int = Query(50, ge=1, le=200, description="最多返回的命中数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    在指定小说中搜索关键字
    
    返回命中的章节和片段列表
    """
    try:
        # 校验 EBook 是否存在
        stmt = select(EBook).where(EBook.id == ebook_id)
        result = await db.execute(stmt)
        ebook = result.scalar_one_or_none()
        
        if not ebook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"EBook {ebook_id} not found"
            )
        
        # 执行搜索
        hits = await search_novel(
            db=db,
            ebook_id=ebook_id,
            query=q,
            max_hits=max_hits,
            max_hits_per_chapter=5,
        )
        
        return hits
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"书内搜索失败 (ebook_id={ebook_id}, query='{q}'): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}"
        )

