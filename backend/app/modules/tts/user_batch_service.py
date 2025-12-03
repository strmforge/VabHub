"""
用户批量 TTS 服务

提供用户批量预览和批量创建 TTS Job 的功能
"""

from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, desc
from loguru import logger

from app.models.ebook import EBook
from app.models.audiobook import AudiobookFile
from app.models.tts_job import TTSJob
from app.schemas.tts import (
    UserTTSBatchFilter,
    UserTTSBatchPreviewItem,
    UserTTSBatchPreviewResponse,
    UserTTSBatchEnqueueResult
)
from app.modules.tts.job_service import create_job_for_ebook


async def preview_ebooks_for_user_batch(
    db: AsyncSession,
    filter: UserTTSBatchFilter,
) -> UserTTSBatchPreviewResponse:
    """
    根据筛选条件，从 EBook + AudiobookFile + TTSJob 三个表中查询候选列表。
    
    - 只返回最多 filter.max_candidates 条
    - 填充 has_audiobook / has_tts_audiobook / active_job_status / last_job_status
    """
    # 构建基础查询：只选 media_type=ebook 的 work（EBook 表本身只包含 ebook）
    query = select(EBook)
    
    # 应用筛选条件
    conditions = []
    
    if filter.language:
        conditions.append(EBook.language == filter.language)
    
    if filter.author_substring:
        conditions.append(EBook.author.contains(filter.author_substring))
    
    if filter.series_substring:
        conditions.append(EBook.series.contains(filter.series_substring))
    
    if filter.tag_keyword:
        # tags 可能是 JSON 字符串或逗号分隔的字符串
        conditions.append(
            or_(
                EBook.tags.contains(filter.tag_keyword),
                EBook.tags.like(f'%"{filter.tag_keyword}"%')  # JSON 格式
            )
        )
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # 限制数量
    query = query.limit(filter.max_candidates)
    query = query.order_by(desc(EBook.created_at))
    
    # 执行查询
    result = await db.execute(query)
    ebooks = result.scalars().all()
    
    if not ebooks:
        return UserTTSBatchPreviewResponse(
            total_candidates=0,
            items=[]
        )
    
    ebook_ids = [ebook.id for ebook in ebooks]
    
    # 批量查询 AudiobookFile（避免 N+1）
    # 先查询所有有声书
    all_audiobooks_result = await db.execute(
        select(AudiobookFile.ebook_id, AudiobookFile.is_tts_generated)
        .where(AudiobookFile.ebook_id.in_(ebook_ids))
        .where(AudiobookFile.is_deleted == False)
    )
    all_audiobooks = all_audiobooks_result.all()
    
    # 统计每个 ebook 的有声书情况
    audiobook_stats = {}
    for row in all_audiobooks:
        ebook_id = row.ebook_id
        if ebook_id not in audiobook_stats:
            audiobook_stats[ebook_id] = {
                'has_audiobook': False,
                'has_tts_audiobook': False
            }
        audiobook_stats[ebook_id]['has_audiobook'] = True
        if row.is_tts_generated:
            audiobook_stats[ebook_id]['has_tts_audiobook'] = True
    
    # 批量查询活跃的 TTSJob（queued/running/partial）
    active_statuses = ["queued", "running", "partial"]
    active_job_result = await db.execute(
        select(
            TTSJob.ebook_id,
            TTSJob.status
        )
        .where(TTSJob.ebook_id.in_(ebook_ids))
        .where(TTSJob.status.in_(active_statuses))
        .order_by(desc(TTSJob.requested_at))
    )
    active_jobs = {}
    for row in active_job_result.all():
        if row.ebook_id not in active_jobs:  # 只取最新的
            active_jobs[row.ebook_id] = row.status
    
    # 批量查询最近的 TTSJob（用于 last_job_status）
    last_job_result = await db.execute(
        select(
            TTSJob.ebook_id,
            TTSJob.status
        )
        .where(TTSJob.ebook_id.in_(ebook_ids))
        .order_by(desc(TTSJob.requested_at))
    )
    last_jobs = {}
    for row in last_job_result.all():
        if row.ebook_id not in last_jobs:  # 只取最新的
            last_jobs[row.ebook_id] = row.status
    
    # 组装预览项
    preview_items = []
    for ebook in ebooks:
        stats = audiobook_stats.get(ebook.id, {
            'has_audiobook': False,
            'has_tts_audiobook': False
        })
        
        # 应用 only_without_audiobook 筛选
        if filter.only_without_audiobook and stats['has_audiobook']:
            continue
        
        # 应用 only_without_active_job 筛选
        if filter.only_without_active_job and ebook.id in active_jobs:
            continue
        
        preview_items.append(
            UserTTSBatchPreviewItem(
                ebook_id=ebook.id,
                title=ebook.title,
                author=ebook.author,
                language=ebook.language,
                has_audiobook=stats['has_audiobook'],
                has_tts_audiobook=stats['has_tts_audiobook'],
                active_job_status=active_jobs.get(ebook.id),
                last_job_status=last_jobs.get(ebook.id)
            )
        )
    
    return UserTTSBatchPreviewResponse(
        total_candidates=len(preview_items),
        items=preview_items
    )


async def enqueue_tts_jobs_for_user_batch(
    db: AsyncSession,
    filter: UserTTSBatchFilter,
    max_new_jobs: int,
    skip_if_has_tts: bool,
    settings: Optional[Any] = None,  # 保留参数以兼容，但实际不使用
) -> UserTTSBatchEnqueueResult:
    """
    批量创建 TTS Job
    
    - 基于 preview 的同一套筛选
    - 遍历候选 ebook，根据 skip 规则决定是否创建 Job
    - 累计 enqueued_new_jobs，不超过 max_new_jobs
    - 返回统计信息
    """
    # 先获取预览列表
    preview = await preview_ebooks_for_user_batch(db, filter)
    
    # 统计变量
    skipped_has_audiobook = 0
    skipped_has_tts = 0
    skipped_has_active_job = 0
    enqueued_new_jobs = 0
    already_had_jobs = 0
    
    # 遍历预览项
    for item in preview.items:
        # 检查是否已达到最大数量
        if enqueued_new_jobs >= max_new_jobs:
            break
        
        # 检查是否已有活跃 Job
        if item.active_job_status:
            already_had_jobs += 1
            skipped_has_active_job += 1
            continue
        
        # 检查 only_without_audiobook
        if filter.only_without_audiobook and item.has_audiobook:
            skipped_has_audiobook += 1
            continue
        
        # 检查 skip_if_has_tts
        if skip_if_has_tts and item.has_tts_audiobook:
            skipped_has_tts += 1
            continue
        
        # 检查 only_without_active_job（双重检查，防止并发）
        if filter.only_without_active_job:
            # 再次查询是否有活跃 Job
            active_check = await db.execute(
                select(TTSJob)
                .where(TTSJob.ebook_id == item.ebook_id)
                .where(TTSJob.status.in_(["queued", "running", "partial"]))
                .limit(1)
            )
            if active_check.scalar_one_or_none():
                already_had_jobs += 1
                skipped_has_active_job += 1
                continue
        
        # 创建新 Job
        try:
            job = await create_job_for_ebook(
                db=db,
                ebook_id=item.ebook_id,
                created_by="user-batch",
                strategy=None
            )
            await db.flush()  # 不 commit，让调用方统一 commit
            enqueued_new_jobs += 1
            logger.info(f"Created TTS job {job.id} for ebook {item.ebook_id} via user batch")
        except Exception as e:
            logger.error(f"Failed to create TTS job for ebook {item.ebook_id}: {e}", exc_info=True)
            # 继续处理下一个，不中断整个批量操作
    
    return UserTTSBatchEnqueueResult(
        total_candidates=preview.total_candidates,
        skipped_has_audiobook=skipped_has_audiobook,
        skipped_has_tts=skipped_has_tts,
        skipped_has_active_job=skipped_has_active_job,
        enqueued_new_jobs=enqueued_new_jobs,
        already_had_jobs=already_had_jobs
    )

