"""
有声书中心聚合 API

提供以有声书为视角的总览数据
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
from app.schemas.audiobook_center import (
    AudiobookCenterListResponse,
    AudiobookCenterItem,
    AudiobookCenterWorkSummary,
    AudiobookCenterListeningProgress,
    AudiobookCenterTTSStatus,
    AudiobookCenterReadingProgress,
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


@router.get("/center/list", response_model=AudiobookCenterListResponse, summary="获取有声书中心列表（聚合）")
async def get_audiobook_center_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词（匹配标题/作者）"),
    tts_status: Optional[str] = Query(None, description="TTS 状态筛选：success/queued/running/failed/none"),
    progress_filter: Optional[str] = Query(None, description="听书进度筛选：not_started/in_progress/finished"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取有声书中心聚合列表
    
    一次返回有有声书或正在生成有声书的作品信息、TTS 状态、听书进度等
    """
    try:
        # 1. 找出有有声书或最近有 TTS Job 的作品 ID 集合
        # 1.1 从 AudiobookFile 获取有有声书的 ebook_id
        audiobook_ebook_stmt = (
            select(AudiobookFile.ebook_id)
            .where(AudiobookFile.is_deleted == False)
            .distinct()
        )
        audiobook_result = await db.execute(audiobook_ebook_stmt)
        audiobook_ebook_ids = set(audiobook_result.scalars().all())
        
        # 1.2 从 TTSJob 获取最近有任务的作品 ID（即使目前没有 AudiobookFile）
        recent_job_stmt = (
            select(TTSJob.ebook_id)
            .order_by(desc(TTSJob.requested_at))
            .limit(100)  # 限制最近 100 个任务
            .distinct()
        )
        recent_job_result = await db.execute(recent_job_stmt)
        recent_job_ebook_ids = set(recent_job_result.scalars().all())
        
        # 合并
        candidate_ebook_ids = audiobook_ebook_ids | recent_job_ebook_ids
        
        if not candidate_ebook_ids:
            return AudiobookCenterListResponse(
                items=[],
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0
            )
        
        # 2. 查询 EBook 信息（支持 keyword 筛选）
        ebook_stmt = select(EBook).where(EBook.id.in_(list(candidate_ebook_ids)))
        
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
        count_stmt = select(func.count(EBook.id))
        if keyword:
            keyword_pattern = f"%{keyword}%"
            count_stmt = count_stmt.where(
                and_(
                    EBook.id.in_(list(candidate_ebook_ids)),
                    or_(
                        EBook.title.ilike(keyword_pattern),
                        EBook.author.ilike(keyword_pattern),
                        EBook.original_title.ilike(keyword_pattern)
                    )
                )
            )
        else:
            count_stmt = count_stmt.where(EBook.id.in_(list(candidate_ebook_ids)))
        
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()
        
        # 分页
        ebook_stmt = ebook_stmt.order_by(desc(EBook.updated_at))
        ebook_stmt = ebook_stmt.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(ebook_stmt)
        ebooks = result.scalars().all()
        
        if not ebooks:
            return AudiobookCenterListResponse(
                items=[],
                total=total,
                page=page,
                page_size=page_size,
                total_pages=(total + page_size - 1) // page_size if total > 0 else 0
            )
        
        ebook_ids = [ebook.id for ebook in ebooks]
        
        # 3. 批量查询有声书存在情况
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
        
        # 4. 批量查询 TTS Job 状态（每本书最新的 Job）
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
        
        # 5. 批量查询听书进度
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
        
        # 6. 批量查询当前章节标题（如果有进度）
        chapter_file_ids = [
            p.audiobook_file_id for p in progress_records
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
        
        # 7. 批量查询阅读进度
        reading_progress_map = await get_reading_progress_map(db, current_user.id, ebook_ids)
        
        # 8. 批量获取章节列表（用于计算阅读进度）
        chapters_map = await get_chapters_map(db, ebooks)
        
        # 9. 组装数据（筛选在查询阶段已应用，这里只组装）
        filtered_items: List[AudiobookCenterItem] = []
        
        for ebook in ebooks:
            ebook_id = ebook.id
            
            # 应用 TTS 状态筛选（在 Python 层，因为需要聚合数据）
            if tts_status:
                audiobook_info = audiobook_map.get(ebook_id, {"has_audiobook": False, "has_tts_audiobook": False})
                last_job = job_map.get(ebook_id)
                
                if tts_status == "none" and audiobook_info["has_audiobook"]:
                    continue
                elif tts_status == "success" and not (last_job and last_job.status == "success"):
                    continue
                elif tts_status == "queued" and not (last_job and last_job.status == "queued"):
                    continue
                elif tts_status == "running" and not (last_job and last_job.status == "running"):
                    continue
                elif tts_status == "failed" and not (last_job and last_job.status == "failed"):
                    continue
            
            # 应用听书进度筛选
            if progress_filter:
                progress = progress_map.get(ebook_id)
                if progress_filter == "not_started":
                    if progress and progress.position_seconds > 0:
                        continue
                elif progress_filter == "in_progress":
                    if not progress or progress.is_finished:
                        continue
                    # 计算进度百分比
                    progress_percent = 0.0
                    if progress.duration_seconds and progress.duration_seconds > 0:
                        progress_percent = (progress.position_seconds / progress.duration_seconds) * 100
                    if progress_percent >= 99.9:
                        continue
                elif progress_filter == "finished":
                    if not progress:
                        continue
                    is_finished = getattr(progress, 'is_finished', False)
                    if not is_finished:
                        # 检查进度百分比
                        progress_percent = 0.0
                        if progress.duration_seconds and progress.duration_seconds > 0:
                            progress_percent = (progress.position_seconds / progress.duration_seconds) * 100
                        if progress_percent < 99.9:
                            continue
            
            # 组装数据
            work_summary = AudiobookCenterWorkSummary(
                ebook_id=ebook.id,
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
            
            tts_status_obj = AudiobookCenterTTSStatus(
                has_audiobook=has_audiobook,
                has_tts_audiobook=has_tts_audiobook,
                last_job_status=last_tts_job_status,
                last_job_at=last_tts_job_at
            )
            
            # 听书进度
            progress = progress_map.get(ebook_id)
            if progress:
                # 计算进度百分比
                progress_percent = 0.0
                if progress.duration_seconds and progress.duration_seconds > 0:
                    progress_percent = (progress.position_seconds / progress.duration_seconds) * 100
                    progress_percent = min(100.0, max(0.0, progress_percent))
                
                current_chapter_title = None
                if progress.audiobook_file_id and progress.audiobook_file_id in chapter_map:
                    current_chapter_title = chapter_map[progress.audiobook_file_id]
                
                is_finished = getattr(progress, 'is_finished', False)
                last_played_at = getattr(progress, 'last_played_at', progress.updated_at)
                
                listening = AudiobookCenterListeningProgress(
                    has_progress=True,
                    is_finished=is_finished,
                    progress_percent=progress_percent,
                    last_played_at=last_played_at,
                    current_file_id=progress.audiobook_file_id,
                    current_chapter_title=current_chapter_title
                )
            else:
                listening = AudiobookCenterListeningProgress(
                    has_progress=False,
                    is_finished=False,
                    progress_percent=0.0,
                    last_played_at=None,
                    current_file_id=None,
                    current_chapter_title=None
                )
            
            # 阅读进度
            reading_progress_record = reading_progress_map.get(ebook_id)
            chapters = chapters_map.get(ebook_id, [])
            reading_data = calculate_reading_progress(reading_progress_record, chapters, ebook_id)
            reading = AudiobookCenterReadingProgress(
                has_progress=reading_data["has_progress"],
                is_finished=reading_data["is_finished"],
                progress_percent=reading_data["progress_percent"],
                current_chapter_index=reading_data["current_chapter_index"],
                current_chapter_title=reading_data["current_chapter_title"],
                last_read_at=reading_data["last_read_at"]
            )
            
            # 组装 Item
            item = AudiobookCenterItem(
                work=work_summary,
                tts=tts_status_obj,
                listening=listening,
                reading=reading
            )
            filtered_items.append(item)
        
        # 重新计算总数（应用筛选后）
        # 注意：这里简化处理，实际应该在后端查询时就应用筛选
        # 但为了性能，可以先返回当前页的结果，总数可以近似
        total_pages = (len(filtered_items) + page_size - 1) // page_size if filtered_items else 0
        
        return AudiobookCenterListResponse(
            items=filtered_items,
            total=len(filtered_items),  # 简化：实际应该重新查询总数
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"获取有声书中心列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )

