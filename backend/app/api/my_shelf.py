"""
我的书架聚合 API

提供"我的书架"页面所需的聚合数据（用户有阅读/听书进度的作品）
"""
from typing import Optional, Dict, List, Set
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
from app.models.user_novel_reading_progress import UserNovelReadingProgress
from app.schemas.my_shelf import (
    MyShelfListResponse,
    MyShelfItem,
    MyShelfWorkSummary,
    MyShelfReadingProgress,
    MyShelfListeningProgress,
    MyShelfTTSStatus,
)
from app.schemas.reading_status import validate_reading_filter_status
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


@router.get("/my-shelf", response_model=MyShelfListResponse, summary="获取我的书架列表（聚合）")
async def get_my_shelf(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态过滤：active（进行中）/ finished（已完成）/ all（全部）"),
    keyword: Optional[str] = Query(None, description="搜索关键词（匹配标题/作者）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取我的书架聚合列表
    
    只返回当前用户有阅读进度或听书进度的作品
    """
    try:
        # 验证状态参数
        validated_status = validate_reading_filter_status(status)
        # 1. 查询用户的阅读进度和听书进度
        reading_progress_stmt = (
            select(UserNovelReadingProgress.ebook_id)
            .where(UserNovelReadingProgress.user_id == current_user.id)
        )
        reading_result = await db.execute(reading_progress_stmt)
        reading_ebook_ids: Set[int] = set(reading_result.scalars().all())
        
        listening_progress_stmt = (
            select(UserAudiobookProgress.ebook_id)
            .where(UserAudiobookProgress.user_id == current_user.id)
        )
        listening_result = await db.execute(listening_progress_stmt)
        listening_ebook_ids: Set[int] = set(listening_result.scalars().all())
        
        # 取并集：有阅读或听书进度的所有作品
        all_ebook_ids: Set[int] = reading_ebook_ids | listening_ebook_ids
        
        if not all_ebook_ids:
            return MyShelfListResponse(
                items=[],
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0
            )
        
        # 2. 根据 status 过滤
        filtered_ebook_ids: Set[int] = set()
        
        if validated_status == "active":
            # 进行中：阅读或听书至少有一项未完成
            for ebook_id in all_ebook_ids:
                reading_progress = None
                listening_progress = None
                
                if ebook_id in reading_ebook_ids:
                    reading_stmt = (
                        select(UserNovelReadingProgress)
                        .where(
                            UserNovelReadingProgress.user_id == current_user.id,
                            UserNovelReadingProgress.ebook_id == ebook_id
                        )
                    )
                    reading_progress = (await db.execute(reading_stmt)).scalar_one_or_none()
                
                if ebook_id in listening_ebook_ids:
                    listening_stmt = (
                        select(UserAudiobookProgress)
                        .where(
                            UserAudiobookProgress.user_id == current_user.id,
                            UserAudiobookProgress.ebook_id == ebook_id
                        )
                    )
                    listening_progress = (await db.execute(listening_stmt)).scalar_one_or_none()
                
                # 至少有一项未完成
                reading_finished = reading_progress and reading_progress.is_finished
                listening_finished = listening_progress and getattr(listening_progress, 'is_finished', False)
                
                if not reading_finished or not listening_finished:
                    filtered_ebook_ids.add(ebook_id)
        elif validated_status == "finished":
            # 已完成：阅读或听书至少有一项完成
            for ebook_id in all_ebook_ids:
                reading_progress = None
                listening_progress = None
                
                if ebook_id in reading_ebook_ids:
                    reading_stmt = (
                        select(UserNovelReadingProgress)
                        .where(
                            UserNovelReadingProgress.user_id == current_user.id,
                            UserNovelReadingProgress.ebook_id == ebook_id
                        )
                    )
                    reading_progress = (await db.execute(reading_stmt)).scalar_one_or_none()
                
                if ebook_id in listening_ebook_ids:
                    listening_stmt = (
                        select(UserAudiobookProgress)
                        .where(
                            UserAudiobookProgress.user_id == current_user.id,
                            UserAudiobookProgress.ebook_id == ebook_id
                        )
                    )
                    listening_progress = (await db.execute(listening_stmt)).scalar_one_or_none()
                
                # 至少有一项完成
                reading_finished = reading_progress and reading_progress.is_finished
                listening_finished = listening_progress and getattr(listening_progress, 'is_finished', False)
                
                if reading_finished or listening_finished:
                    filtered_ebook_ids.add(ebook_id)
        else:
            # all：不做额外过滤
            filtered_ebook_ids = all_ebook_ids
        
        if not filtered_ebook_ids:
            return MyShelfListResponse(
                items=[],
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0
            )
        
        # 3. 查询 EBook 信息（支持 keyword 过滤）
        ebook_stmt = select(EBook).where(EBook.id.in_(filtered_ebook_ids))
        
        if keyword:
            keyword_pattern = f"%{keyword}%"
            ebook_stmt = ebook_stmt.where(
                or_(
                    EBook.title.ilike(keyword_pattern),
                    EBook.author.ilike(keyword_pattern),
                    EBook.original_title.ilike(keyword_pattern)
                )
            )
        
        # 获取总数
        count_stmt = select(func.count(EBook.id)).where(EBook.id.in_(filtered_ebook_ids))
        if keyword:
            keyword_pattern = f"%{keyword}%"
            count_stmt = count_stmt.where(
                or_(
                    EBook.title.ilike(keyword_pattern),
                    EBook.author.ilike(keyword_pattern),
                    EBook.original_title.ilike(keyword_pattern)
                )
            )
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()
        
        # 分页
        ebook_stmt = ebook_stmt.order_by(EBook.updated_at.desc())
        ebook_stmt = ebook_stmt.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(ebook_stmt)
        ebooks = result.scalars().all()
        
        if not ebooks:
            return MyShelfListResponse(
                items=[],
                total=total,
                page=page,
                page_size=page_size,
                total_pages=(total + page_size - 1) // page_size if total > 0 else 0
            )
        
        ebook_ids = [ebook.id for ebook in ebooks]
        
        # 4. 批量查询阅读进度
        reading_progress_map = await get_reading_progress_map(db, current_user.id, ebook_ids)
        
        # 5. 批量查询听书进度
        listening_progress_stmt = (
            select(UserAudiobookProgress)
            .where(
                UserAudiobookProgress.user_id == current_user.id,
                UserAudiobookProgress.ebook_id.in_(ebook_ids)
            )
        )
        listening_progress_result = await db.execute(listening_progress_stmt)
        listening_progress_records = listening_progress_result.scalars().all()
        listening_progress_map: Dict[int, UserAudiobookProgress] = {
            p.ebook_id: p for p in listening_progress_records
        }
        
        # 6. 批量查询章节标题（用于听书进度）
        chapter_file_ids = [
            p.audiobook_file_id for p in listening_progress_records
            if p.audiobook_file_id is not None
        ]
        chapter_map: Dict[int, str] = {}
        if chapter_file_ids:
            chapter_stmt = (
                select(AudiobookFile.id, AudiobookFile.narrator, AudiobookFile.file_path)
                .where(AudiobookFile.id.in_(chapter_file_ids))
            )
            chapter_result = await db.execute(chapter_stmt)
            chapter_files = chapter_result.all()
            for file in chapter_files:
                if file.narrator:
                    chapter_map[file.id] = file.narrator
                elif file.file_path:
                    import os
                    filename = os.path.basename(file.file_path)
                    chapter_title = os.path.splitext(filename)[0]
                    chapter_map[file.id] = chapter_title
        
        # 7. 批量获取章节列表（用于计算阅读进度）
        chapters_map = await get_chapters_map(db, ebooks)
        
        # 8. 批量查询有声书存在情况
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
        
        audiobook_map: Dict[int, Dict[str, bool]] = {}
        for row in audiobook_rows:
            ebook_id = row.ebook_id
            if ebook_id not in audiobook_map:
                audiobook_map[ebook_id] = {"has_audiobook": False, "has_tts_audiobook": False}
            
            audiobook_map[ebook_id]["has_audiobook"] = True
            if row.is_tts_generated:
                audiobook_map[ebook_id]["has_tts_audiobook"] = True
        
        # 9. 批量查询 TTS Job 状态
        job_stmt = (
            select(TTSJob)
            .where(TTSJob.ebook_id.in_(ebook_ids))
            .order_by(TTSJob.ebook_id, desc(TTSJob.requested_at))
        )
        job_result = await db.execute(job_stmt)
        all_jobs = job_result.scalars().all()
        
        job_map: Dict[int, TTSJob] = {}
        for job in all_jobs:
            if job.ebook_id not in job_map:
                job_map[job.ebook_id] = job
        
        # 10. 组装响应
        items: List[MyShelfItem] = []
        
        for ebook in ebooks:
            ebook_id = ebook.id
            
            # 作品基本信息
            work_summary = MyShelfWorkSummary(
                ebook_id=ebook.id,
                title=ebook.title,
                original_title=ebook.original_title,
                author=ebook.author,
                series=ebook.series,
                language=ebook.language,
                cover_url=getattr(ebook, 'cover_url', None),  # 如果 EBook 模型有 cover_url 字段
                updated_at=ebook.updated_at
            )
            
            # 阅读进度
            reading_progress_record = reading_progress_map.get(ebook_id)
            chapters = chapters_map.get(ebook_id, [])
            reading_data = calculate_reading_progress(reading_progress_record, chapters, ebook_id)
            reading = MyShelfReadingProgress(
                has_progress=reading_data["has_progress"],
                is_finished=reading_data["is_finished"],
                progress_percent=reading_data["progress_percent"],
                current_chapter_index=reading_data["current_chapter_index"],
                current_chapter_title=reading_data["current_chapter_title"],
                last_read_at=reading_data["last_read_at"]
            )
            
            # 听书进度
            listening_progress_record = listening_progress_map.get(ebook_id)
            if listening_progress_record:
                progress_percent = 0.0
                if listening_progress_record.duration_seconds and listening_progress_record.duration_seconds > 0:
                    progress_percent = (listening_progress_record.position_seconds / listening_progress_record.duration_seconds) * 100
                    progress_percent = min(100.0, max(0.0, progress_percent))
                
                current_chapter_title = None
                if listening_progress_record.audiobook_file_id and listening_progress_record.audiobook_file_id in chapter_map:
                    current_chapter_title = chapter_map[listening_progress_record.audiobook_file_id]
                
                is_finished = getattr(listening_progress_record, 'is_finished', False)
                last_listened_at = getattr(listening_progress_record, 'last_played_at', None) or getattr(listening_progress_record, 'updated_at', None)
                
                listening = MyShelfListeningProgress(
                    has_progress=True,
                    is_finished=is_finished,
                    progress_percent=progress_percent,
                    current_file_id=listening_progress_record.audiobook_file_id,
                    current_chapter_title=current_chapter_title,
                    last_listened_at=last_listened_at
                )
            else:
                listening = MyShelfListeningProgress(
                    has_progress=False,
                    is_finished=False,
                    progress_percent=0.0,
                    current_file_id=None,
                    current_chapter_title=None,
                    last_listened_at=None
                )
            
            # TTS 状态
            audiobook_info = audiobook_map.get(ebook_id, {"has_audiobook": False, "has_tts_audiobook": False})
            last_job = job_map.get(ebook_id)
            last_tts_job_status = None
            last_tts_job_at = None
            if last_job:
                if last_job.status in ["queued", "running", "partial", "success", "failed"]:
                    last_tts_job_status = last_job.status
                last_tts_job_at = last_job.requested_at
            
            tts = MyShelfTTSStatus(
                has_audiobook=audiobook_info["has_audiobook"],
                has_tts_audiobook=audiobook_info["has_tts_audiobook"],
                last_job_status=last_tts_job_status,
                last_job_at=last_tts_job_at
            )
            
            # 组装 Item
            item = MyShelfItem(
                work=work_summary,
                reading=reading,
                listening=listening,
                tts=tts
            )
            items.append(item)
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return MyShelfListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"获取我的书架列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )

