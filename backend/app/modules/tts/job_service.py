"""
TTS Job 服务

负责创建和执行 TTS 生成任务
"""

from typing import Optional
from datetime import datetime
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.tts_job import TTSJob
from app.models.ebook import EBook
from app.modules.tts.work_regen_service import regenerate_tts_for_ebook
from app.modules.tts.factory import get_tts_engine
from app.modules.audiobook.importer import AudiobookImporter
from app.modules.novel.pipeline import NovelToEbookPipeline
from app.modules.novel.epub_builder import EpubBuilder
from app.modules.ebook.importer import EBookImporter
from app.modules.tts.rate_limiter import get_state as get_rate_limit_state
from app.core.config import Settings


async def create_job_for_ebook(
    db: AsyncSession,
    ebook_id: int,
    created_by: str = "dev-api",
    strategy: Optional[str] = None,
) -> TTSJob:
    """
    为指定 EBook 创建 TTS Job
    
    Args:
        db: 数据库会话
        ebook_id: 电子书 ID
        created_by: 创建者标识
        strategy: TTS 策略（可选）
    
    Returns:
        TTSJob: 创建的 Job 对象
    """
    # 检查 EBook 是否存在
    result = await db.execute(select(EBook).where(EBook.id == ebook_id))
    ebook = result.scalar_one_or_none()
    
    if not ebook:
        raise ValueError(f"EBook {ebook_id} not found")
    
    # 创建 Job
    job = TTSJob(
        ebook_id=ebook_id,
        status="queued",
        strategy=strategy,
        requested_at=datetime.utcnow(),
        processed_chapters=0,
        created_files_count=0,
        error_count=0,
        created_by=created_by
    )
    
    db.add(job)
    await db.flush()
    
    logger.info(f"Created TTS job {job.id} for ebook {ebook_id}")
    return job


async def run_job(
    db: AsyncSession,
    settings: Settings,
    job_id: int,
) -> TTSJob:
    """
    执行一个 TTS Job
    
    Args:
        db: 数据库会话
        settings: 应用配置
        job_id: Job ID
    
    Returns:
        TTSJob: 更新后的 Job 对象
    """
    # 加载 Job
    result = await db.execute(select(TTSJob).where(TTSJob.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise ValueError(f"TTSJob {job_id} not found")
    
    if job.status not in ["queued", "partial"]:
        raise ValueError(f"TTSJob {job_id} is not in queued or partial status (current: {job.status})")
    
    # 更新状态为 running
    job.status = "running"
    job.started_at = datetime.utcnow()
    await db.flush()
    
    logger.info(f"Starting TTS job {job_id} for ebook {job.ebook_id}")
    
    try:
        # 检查 TTS 是否启用
        if not settings.SMART_TTS_ENABLED:
            job.status = "failed"
            job.finished_at = datetime.utcnow()
            job.last_error = "TTS 当前未启用"
            await db.flush()
            return job
        
        # 获取 TTS 引擎
        tts_engine = get_tts_engine(settings=settings)
        if not tts_engine:
            job.status = "failed"
            job.finished_at = datetime.utcnow()
            job.last_error = "TTS 引擎不可用"
            await db.flush()
            return job
        
        # 获取 EBook
        ebook_result = await db.execute(select(EBook).where(EBook.id == job.ebook_id))
        ebook = ebook_result.scalar_one_or_none()
        
        if not ebook:
            job.status = "failed"
            job.finished_at = datetime.utcnow()
            job.last_error = f"EBook {job.ebook_id} not found"
            await db.flush()
            return job
        
        # 记录限流快照（可选）
        try:
            from app.modules.tts.rate_limiter import get_state as get_rate_limit_state
            rate_limit_state = get_rate_limit_state()
            job.rate_limit_snapshot = {
                "daily_requests": rate_limit_state.daily_requests,
                "daily_characters": rate_limit_state.daily_characters,
                "last_limited_at": rate_limit_state.last_limited_at.isoformat() if rate_limit_state.last_limited_at else None,
                "last_limited_reason": rate_limit_state.last_limited_reason
            }
        except Exception as e:
            logger.warning(f"Failed to snapshot rate limit state: {e}")
        
        # 创建必要的组件
        audiobook_importer = AudiobookImporter(db=db)
        epub_builder = EpubBuilder()
        ebook_importer = EBookImporter(db=db)
        
        pipeline = NovelToEbookPipeline(
            db=db,
            ebook_importer=ebook_importer,
            epub_builder=epub_builder,
            tts_engine=tts_engine,
            audiobook_importer=audiobook_importer,
            settings=settings
        )
        
        # 从 job.details 中读取断点信息
        resume_from_chapter = None
        previous_generated = 0
        if job.details and "tts" in job.details:
            tts_details = job.details["tts"]
            resume_from_chapter = tts_details.get("resume_from_chapter_index")
            previous_generated = tts_details.get("generated_chapters", 0)
            if resume_from_chapter:
                logger.info(f"Job {job_id} 将从第 {resume_from_chapter} 章继续")
        
        # 调用重新生成服务
        regen_result = await regenerate_tts_for_ebook(
            ebook=ebook,
            db=db,
            settings=settings,
            tts_engine=tts_engine,
            audiobook_importer=audiobook_importer,
            pipeline=pipeline,
            resume_from_chapter_index=resume_from_chapter
        )
        
        # 更新 Job 状态
        job.finished_at = datetime.utcnow()
        job.created_files_count += regen_result.created_count  # 累加本次创建的文件数
        job.error_count = regen_result.skipped_count  # 使用 skipped_count 作为错误计数
        
        # 根据结果确定状态
        if regen_result.status == "ok":
            # 如果有 TTS 汇总信息，使用它来更新状态
            if regen_result.tts_summary:
                tts_summary = regen_result.tts_summary
                total_chapters = tts_summary.total_chapters
                generated_this_run = tts_summary.generated_chapters
                total_generated = previous_generated + generated_this_run
                rate_limited = tts_summary.rate_limited_chapters
                
                # 更新 job.details
                if job.details is None:
                    job.details = {}
                
                if rate_limited > 0:
                    # 本次仍然被限流
                    job.status = "partial"
                    resume_from = tts_summary.first_rate_limited_chapter_index
                    job.details["tts"] = {
                        "total_chapters": total_chapters,
                        "generated_chapters": total_generated,
                        "rate_limited_chapters": rate_limited,
                        "resume_from_chapter_index": resume_from,
                        "last_run_at": datetime.utcnow().isoformat() + "Z",
                        "last_run_status": "rate_limited"
                    }
                    logger.info(
                        f"Job {job_id} 部分完成: 总计 {total_chapters} 章，"
                        f"已生成 {total_generated} 章，下次从第 {resume_from} 章继续"
                    )
                elif total_generated >= total_chapters:
                    # 所有章节都完成了
                    job.status = "success"
                    # 清除断点信息
                    if "tts" in job.details:
                        job.details["tts"]["resume_from_chapter_index"] = None
                        job.details["tts"]["last_run_at"] = datetime.utcnow().isoformat() + "Z"
                        job.details["tts"]["last_run_status"] = "completed"
                    logger.info(f"Job {job_id} 全部完成: 总计 {total_chapters} 章，已生成 {total_generated} 章")
                else:
                    # 没有限流但也没完成（理论上不应该发生，但保留处理）
                    job.status = "partial"
                    job.details["tts"] = {
                        "total_chapters": total_chapters,
                        "generated_chapters": total_generated,
                        "rate_limited_chapters": 0,
                        "resume_from_chapter_index": total_generated + 1,
                        "last_run_at": datetime.utcnow().isoformat() + "Z",
                        "last_run_status": "incomplete"
                    }
            else:
                # 没有 TTS 汇总信息，使用原有逻辑
                if regen_result.created_count > 0 and regen_result.skipped_count == 0:
                    job.status = "success"
                elif regen_result.created_count > 0 and regen_result.skipped_count > 0:
                    job.status = "partial"
                else:
                    job.status = "failed"
                    job.last_error = "未创建任何文件"
        else:
            job.status = "failed"
            job.last_error = regen_result.error_message or f"状态: {regen_result.status}"
        
        # 记录 provider
        job.provider = settings.SMART_TTS_PROVIDER
        
        await db.flush()
        logger.info(f"TTS job {job_id} completed with status: {job.status}")
        
        # 创建用户通知（不影响主流程）
        try:
            from app.modules.tts.notification_service import create_tts_job_notification
            
            # 提取摘要信息
            summary = None
            if job.details and "tts" in job.details:
                tts_details = job.details["tts"]
                summary = {
                    "generated_chapters": tts_details.get("generated_chapters"),
                    "total_chapters": tts_details.get("total_chapters"),
                    "rate_limited_chapters": tts_details.get("rate_limited_chapters", 0)
                }
            
            await create_tts_job_notification(
                db=db,
                job=job,
                ebook=ebook,
                status=job.status,
                summary=summary
            )
            await db.flush()
        except Exception as notify_err:
            logger.warning(f"Failed to create notification for TTS job {job_id}: {notify_err}", exc_info=True)
            # 不影响主流程，继续执行
        
        return job
        
    except Exception as e:
        logger.exception(f"TTS job {job_id} failed: {e}")
        
        # 更新 Job 为失败状态
        job.status = "failed"
        job.finished_at = datetime.utcnow()
        job.last_error = str(e)[:500]  # 截断错误信息
        await db.flush()
        
        # 创建失败通知（不影响主流程）
        try:
            from app.modules.tts.notification_service import create_tts_job_notification
            
            # 尝试加载 ebook（如果之前没有加载）
            if 'ebook' not in locals() or ebook is None:
                ebook_result = await db.execute(select(EBook).where(EBook.id == job.ebook_id))
                ebook = ebook_result.scalar_one_or_none()
            
            await create_tts_job_notification(
                db=db,
                job=job,
                ebook=ebook,
                status="failed",
                summary=None
            )
            await db.flush()
        except Exception as notify_err:
            logger.warning(f"Failed to create notification for failed TTS job {job_id}: {notify_err}", exc_info=True)
        
        return job


async def find_next_queued_job(
    db: AsyncSession,
) -> Optional[TTSJob]:
    """
    找到下一个待执行的 Job（按 requested_at ASC）
    
    包含 queued 和 partial 状态的 Job，优先处理 partial（断点续跑）
    
    Args:
        db: 数据库会话
    
    Returns:
        Optional[TTSJob]: 下一个待执行的 Job，如果没有则返回 None
    """
    result = await db.execute(
        select(TTSJob)
        .where(TTSJob.status.in_(["queued", "partial"]))
        .order_by(TTSJob.requested_at.asc())
        .limit(1)
    )
    return result.scalar_one_or_none()

