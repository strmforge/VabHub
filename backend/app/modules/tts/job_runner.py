"""
TTS Job Runner

提供批量执行 TTS Job 的能力，用于 CLI / Cron / systemd 调用
"""

from dataclasses import dataclass
from typing import Optional
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tts.job_service import find_next_pending_job, run_job
from app.core.config import Settings


@dataclass
class TTSBatchResult:
    """批量执行 TTS Job 的结果"""
    total_jobs: int  # 本次尝试处理的 Job 数（实际拿到的 queued+partial）
    run_jobs: int  # 实际成功调用了 run_job() 的 Job 数
    succeeded_jobs: int  # 本次从 queued/partial → success 的 Job 数
    partial_jobs: int  # 仍为 partial 的 Job 数（说明还可以继续跑）
    failed_jobs: int  # 本次 run 之后变为 failed 的 Job 数
    last_job_id: Optional[int] = None  # 最后一个被处理的 job_id（方便日志定位）


async def run_batch_jobs(
    db: AsyncSession,
    settings: Settings,
    max_jobs: Optional[int] = None,
) -> TTSBatchResult:
    """
    批量执行 TTS Job
    
    Args:
        db: 数据库会话
        settings: 应用配置
        max_jobs: 最多处理的 Job 数量，如果为 None 则使用 settings.SMART_TTS_JOB_RUNNER_MAX_JOBS_PER_RUN
    
    Returns:
        TTSBatchResult: 批量执行结果
    """
    # 确定最大处理数量
    if max_jobs is None:
        max_jobs = settings.SMART_TTS_JOB_RUNNER_MAX_JOBS_PER_RUN
    
    if max_jobs <= 0:
        max_jobs = 5  # 默认值
    
    logger.info(f"开始批量执行 TTS Job，最多处理 {max_jobs} 个")
    
    result = TTSBatchResult(
        total_jobs=0,
        run_jobs=0,
        succeeded_jobs=0,
        partial_jobs=0,
        failed_jobs=0,
        last_job_id=None
    )
    
    # 跟踪已处理的 Job ID，避免在同一批次中重复处理
    processed_job_ids: set[int] = set()
    
    # 循环处理 Job
    for i in range(max_jobs):
        # 查找下一个待处理的 Job（排除已处理的）
        job = await find_next_pending_job(db, exclude_ids=processed_job_ids)
        
        if not job:
            # 没有更多 Job 了
            logger.debug(f"没有更多待处理的 Job，已处理 {result.total_jobs} 个")
            break
        
        result.total_jobs += 1
        initial_status = job.status  # 记录初始状态
        processed_job_ids.add(job.id)  # 标记为已处理
        
        try:
            # 执行 Job
            logger.info(f"执行 TTS Job {job.id} (ebook_id={job.ebook_id}, status={initial_status})")
            updated_job = await run_job(
                db=db,
                settings=settings,
                job_id=job.id
            )
            
            # 提交事务
            await db.commit()
            result.run_jobs += 1
            result.last_job_id = updated_job.id
            
            # 统计状态变化
            final_status = updated_job.status
            if final_status == "success":
                result.succeeded_jobs += 1
                logger.info(f"Job {job.id} 执行成功")
            elif final_status == "partial":
                result.partial_jobs += 1
                logger.info(f"Job {job.id} 部分完成（仍为 partial，可继续执行）")
            elif final_status == "failed":
                result.failed_jobs += 1
                logger.warning(f"Job {job.id} 执行失败: {updated_job.last_error}")
            else:
                # running 状态不应该出现（run_job 会更新状态）
                logger.warning(f"Job {job.id} 执行后状态异常: {final_status}")
        
        except Exception as e:
            # 执行失败，回滚事务
            logger.exception(f"执行 Job {job.id} 时出错: {e}")
            await db.rollback()
            result.failed_jobs += 1
            result.last_job_id = job.id
            # 继续处理下一个 Job，不中断批量执行
    
    # 生成汇总日志
    logger.info(
        f"批量执行完成: 尝试 {result.total_jobs} 个，执行 {result.run_jobs} 个，"
        f"成功 {result.succeeded_jobs} 个，部分完成 {result.partial_jobs} 个，失败 {result.failed_jobs} 个"
    )
    
    return result

