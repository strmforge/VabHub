"""
小说中心聚合 API

提供小说中心页面所需的聚合数据（EBook + TTS 状态 + 听书进度）
"""
from typing import Optional, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_, or_
from loguru import logger

from app.core.database import get_db
from app.api.auth import oauth2_scheme
from app.core.security import decode_access_token
from app.models.user import User
from app.models.ebook import EBook
from app.models.audiobook import AudiobookFile
from app.models.tts_job import TTSJob
from app.models.user_audiobook_progress import UserAudiobookProgress
from app.schemas.novel_center import (
    NovelCenterListResponse,
    NovelCenterItem,
    NovelCenterEBookSummary,
    NovelCenterListeningProgress,
    NovelCenterReadingProgress,
)
from app.modules.novel.reading_progress_service import (
    get_reading_progress_map,
    get_chapters_map,
    calculate_reading_progress,
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


@router.get("/list", response_model=NovelCenterListResponse, summary="获取小说中心列表（聚合）")
async def get_novel_center_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词（匹配标题/作者）"),
    author: Optional[str] = Query(None, description="作者过滤"),
    series: Optional[str] = Query(None, description="系列名过滤"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取小说中心聚合列表
    
    一次返回 EBook 基本信息、TTS 状态、听书进度等聚合数据
    """
    try:
        # 1. 构建 EBook 查询（复用 /api/ebooks 的逻辑）
        stmt = select(EBook)
        conditions = []
        
        if keyword:
            keyword_pattern = f"%{keyword}%"
            conditions.append(
                or_(
                    EBook.title.ilike(keyword_pattern),
                    EBook.author.ilike(keyword_pattern),
                    EBook.original_title.ilike(keyword_pattern)
                )
            )
        
        if author:
            conditions.append(EBook.author.ilike(f"%{author}%"))
        
        if series:
            conditions.append(EBook.series.ilike(f"%{series}%"))
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # 获取总数
        count_stmt = select(func.count(EBook.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()
        
        # 分页
        stmt = stmt.order_by(EBook.updated_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        
        # 执行查询
        result = await db.execute(stmt)
        ebooks = result.scalars().all()
        
        if not ebooks:
            return NovelCenterListResponse(
                items=[],
                total=total,
                page=page,
                page_size=page_size,
                total_pages=(total + page_size - 1) // page_size if total > 0 else 0
            )
        
        ebook_ids = [ebook.id for ebook in ebooks]
        
        # 2. 批量查询有声书存在情况
        audiobook_stmt = (
            select(
                AudiobookFile.ebook_id,
                AudiobookFile.is_tts_generated,
                func.count(AudiobookFile.id).label("count")
            )
            .where(
                AudiobookFile.ebook_id.in_(ebook_ids),
                AudiobookFile.is_deleted == False
            )
            .group_by(AudiobookFile.ebook_id, AudiobookFile.is_tts_generated)
        )
        audiobook_result = await db.execute(audiobook_stmt)
        audiobook_rows = audiobook_result.all()
        
        # 聚合有声书信息
        audiobook_map: Dict[int, Dict[str, bool]] = {}
        for row in audiobook_rows:
            ebook_id = row.ebook_id
            if ebook_id not in audiobook_map:
                audiobook_map[ebook_id] = {"has_audiobook": False, "has_tts_audiobook": False}
            
            audiobook_map[ebook_id]["has_audiobook"] = True
            if row.is_tts_generated:
                audiobook_map[ebook_id]["has_tts_audiobook"] = True
        
        # 3. 批量查询 TTS Job 状态（每本书最新的 Job）
        # 使用窗口函数或子查询获取每本书最新的 Job
        # 简化版：先查询所有相关 Job，然后在 Python 中筛选
        job_stmt = (
            select(TTSJob)
            .where(TTSJob.ebook_id.in_(ebook_ids))
            .order_by(TTSJob.ebook_id, desc(TTSJob.requested_at))
        )
        job_result = await db.execute(job_stmt)
        all_jobs = job_result.scalars().all()
        
        # 按 ebook_id 分组，取每个 ebook_id 最新的 Job
        job_map: Dict[int, TTSJob] = {}
        for job in all_jobs:
            if job.ebook_id not in job_map:
                job_map[job.ebook_id] = job
        
        # 4. 批量查询听书进度
        progress_stmt = (
            select(UserAudiobookProgress)
            .where(
                UserAudiobookProgress.user_id == current_user.id,
                UserAudiobookProgress.ebook_id.in_(ebook_ids)
            )
        )
        progress_result = await db.execute(progress_stmt)
        progress_records = progress_result.scalars().all()
        
        # 构建进度映射
        progress_map: Dict[int, UserAudiobookProgress] = {
            p.ebook_id: p for p in progress_records
        }
        
        # 5. 批量查询当前章节标题（如果有进度）
        chapter_file_ids = [
            p.audiobook_file_id for p in progress_records
            if p.audiobook_file_id is not None
        ]
        chapter_map: Dict[int, str] = {}
        if chapter_file_ids:
            chapter_stmt = (
                select(AudiobookFile.id, AudiobookFile.file_path, AudiobookFile.narrator)
                .where(AudiobookFile.id.in_(chapter_file_ids))
            )
            chapter_result = await db.execute(chapter_stmt)
            chapter_files = chapter_result.all()
            # 从文件路径提取章节标题（简化版，可以后续优化）
            for file in chapter_files:
                # 优先使用 narrator，否则使用文件名
                if file.narrator:
                    chapter_map[file.id] = file.narrator
                elif file.file_path:
                    import os
                    filename = os.path.basename(file.file_path)
                    # 移除扩展名
                    chapter_title = os.path.splitext(filename)[0]
                    chapter_map[file.id] = chapter_title
        
        # 6. 批量查询阅读进度
        reading_progress_map = await get_reading_progress_map(db, current_user.id, ebook_ids)
        
        # 7. 批量获取章节列表（用于计算阅读进度）
        chapters_map = await get_chapters_map(db, ebooks)
        
        # 8. 组装响应
        items: List[NovelCenterItem] = []
        
        for ebook in ebooks:
            ebook_id = ebook.id
            
            # EBook 基本信息
            ebook_summary = NovelCenterEBookSummary(
                id=ebook.id,
                title=ebook.title,
                original_title=ebook.original_title,
                author=ebook.author,
                series=ebook.series,
                language=ebook.language,
                updated_at=ebook.updated_at
            )
            
            # 有声书信息
            audiobook_info = audiobook_map.get(ebook_id, {"has_audiobook": False, "has_tts_audiobook": False})
            has_audiobook = audiobook_info["has_audiobook"]
            has_tts_audiobook = audiobook_info["has_tts_audiobook"]
            
            # TTS Job 状态
            last_job = job_map.get(ebook_id)
            last_tts_job_status = None
            last_tts_job_at = None
            if last_job:
                if last_job.status in ["queued", "running", "partial", "success", "failed"]:
                    last_tts_job_status = last_job.status
                last_tts_job_at = last_job.requested_at
            
            # 听书进度
            progress = progress_map.get(ebook_id)
            if progress:
                # 计算进度百分比
                progress_percent = 0.0
                if progress.duration_seconds and progress.duration_seconds > 0:
                    progress_percent = (progress.position_seconds / progress.duration_seconds) * 100
                    progress_percent = min(100.0, max(0.0, progress_percent))
                
                # 获取章节标题
                current_chapter_title = None
                if progress.audiobook_file_id and progress.audiobook_file_id in chapter_map:
                    current_chapter_title = chapter_map[progress.audiobook_file_id]
                
                listening = NovelCenterListeningProgress(
                    has_progress=True,
                    is_finished=progress.is_finished,
                    progress_percent=progress_percent,
                    current_file_id=progress.audiobook_file_id,
                    current_chapter_title=current_chapter_title,
                    last_played_at=progress.last_played_at
                )
            else:
                listening = NovelCenterListeningProgress(
                    has_progress=False,
                    is_finished=False,
                    progress_percent=0.0,
                    current_file_id=None,
                    current_chapter_title=None,
                    last_played_at=None
                )
            
            # 阅读进度
            reading_progress_record = reading_progress_map.get(ebook_id)
            chapters = chapters_map.get(ebook_id, [])
            reading_data = calculate_reading_progress(reading_progress_record, chapters, ebook_id)
            reading = NovelCenterReadingProgress(
                has_progress=reading_data["has_progress"],
                is_finished=reading_data["is_finished"],
                progress_percent=reading_data["progress_percent"],
                current_chapter_index=reading_data["current_chapter_index"],
                current_chapter_title=reading_data["current_chapter_title"],
                last_read_at=reading_data["last_read_at"]
            )
            
            # 组装 Item
            item = NovelCenterItem(
                ebook=ebook_summary,
                has_audiobook=has_audiobook,
                has_tts_audiobook=has_tts_audiobook,
                last_tts_job_status=last_tts_job_status,
                last_tts_job_at=last_tts_job_at,
                listening=listening,
                reading=reading
            )
            items.append(item)
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return NovelCenterListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"获取小说中心列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )

