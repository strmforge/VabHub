"""
用户批量 TTS API

提供用户批量预览和批量创建 TTS Job 的接口
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.config import settings
from app.core.database import get_db
from app.schemas.tts import (
    UserTTSBatchFilter,
    UserTTSBatchPreviewResponse,
    UserTTSBatchEnqueueRequest,
    UserTTSBatchEnqueueResult
)
from app.modules.tts.user_batch_service import (
    preview_ebooks_for_user_batch,
    enqueue_tts_jobs_for_user_batch
)

router = APIRouter()


def _check_tts_enabled():
    """检查 TTS 是否启用"""
    if not settings.SMART_TTS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TTS is disabled"
        )


@router.post("/preview", response_model=UserTTSBatchPreviewResponse, summary="预览批量 TTS 候选作品")
async def preview_tts_batch(
    filter: UserTTSBatchFilter,
    db: AsyncSession = Depends(get_db),
):
    """
    根据筛选条件预览候选作品列表
    
    用于批量生成 TTS 任务前的预览
    """
    _check_tts_enabled()
    
    try:
        result = await preview_ebooks_for_user_batch(db, filter)
        return result
    except Exception as e:
        logger.error(f"Failed to preview TTS batch: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to preview TTS batch"
        )


@router.post("/enqueue", response_model=UserTTSBatchEnqueueResult, summary="批量创建 TTS 任务")
async def enqueue_tts_batch(
    req: UserTTSBatchEnqueueRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    批量创建 TTS Job
    
    根据筛选条件和跳过规则，为符合条件的作品创建 TTS 任务
    """
    _check_tts_enabled()
    
    try:
        result = await enqueue_tts_jobs_for_user_batch(
            db=db,
            filter=req.filter,
            max_new_jobs=req.max_new_jobs,
            skip_if_has_tts=req.skip_if_has_tts,
            settings=None
        )
        await db.commit()
        
        logger.info(
            f"User batch TTS enqueue completed: "
            f"total={result.total_candidates}, "
            f"enqueued={result.enqueued_new_jobs}, "
            f"skipped_audiobook={result.skipped_has_audiobook}, "
            f"skipped_tts={result.skipped_has_tts}, "
            f"skipped_active_job={result.skipped_has_active_job}, "
            f"already_had={result.already_had_jobs}"
        )
        
        return result
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to enqueue TTS batch: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enqueue TTS batch"
        )

