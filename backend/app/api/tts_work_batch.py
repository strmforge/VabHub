"""
TTS Work Batch API

提供批量应用 TTS 声线预设到作品的 Dev API
"""

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.tts_voice_preset import TTSVoicePreset
from app.schemas.tts import (
    TTSWorkBatchFilter,
    TTSWorkBatchPreviewResponse,
    TTSWorkBatchPreviewItem,
    ApplyTTSWorkPresetRequest,
    ApplyTTSWorkPresetResult
)
from app.modules.tts.work_batch_service import (
    preview_ebooks_for_preset_batch,
    apply_preset_to_ebooks
)

router = APIRouter()


@router.post("/work-batch/preview", response_model=TTSWorkBatchPreviewResponse, summary="预览批量应用预设")
async def preview_work_batch(
    filter: TTSWorkBatchFilter,
    db: AsyncSession = Depends(get_db),
    limit: int = 500
) -> TTSWorkBatchPreviewResponse:
    """
    预览符合条件的 EBook 列表及其 TTS Profile 状态
    
    此接口仅在 Dev 模式下可用。
    
    Args:
        filter: 筛选条件
        db: 数据库会话
        limit: 最大返回数量（默认 500）
    
    Returns:
        TTSWorkBatchPreviewResponse: 预览结果
    """
    # Dev guard
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="此接口仅在 DEBUG 模式下可用"
        )
    
    try:
        items = await preview_ebooks_for_preset_batch(
            db=db,
            filter=filter,
            limit=limit
        )
        
        return TTSWorkBatchPreviewResponse(
            total=len(items),
            limit=limit,
            items=items
        )
    except Exception as e:
        logger.exception(f"预览批量应用预设失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"预览失败: {str(e)}"
        )


@router.post("/work-batch/apply", response_model=ApplyTTSWorkPresetResult, summary="批量应用预设")
async def apply_work_batch(
    request: ApplyTTSWorkPresetRequest,
    db: AsyncSession = Depends(get_db)
) -> ApplyTTSWorkPresetResult:
    """
    批量应用 TTS 声线预设到符合条件的作品
    
    此接口仅在 Dev 模式下可用。
    
    Args:
        request: 批量应用请求
        db: 数据库会话
    
    Returns:
        ApplyTTSWorkPresetResult: 处理结果统计
    """
    # Dev guard
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="此接口仅在 DEBUG 模式下可用"
        )
    
    # 验证预设存在
    from sqlalchemy import select
    preset_result = await db.execute(
        select(TTSVoicePreset)
        .where(TTSVoicePreset.id == request.preset_id)
    )
    preset = preset_result.scalar_one_or_none()
    if not preset:
        raise HTTPException(
            status_code=400,
            detail=f"TTSVoicePreset {request.preset_id} not found"
        )
    
    try:
        result = await apply_preset_to_ebooks(
            db=db,
            preset_id=request.preset_id,
            filter=request.filter,
            override_existing=request.override_existing,
            enable_profile=request.enable_profile,
            dry_run=request.dry_run,
            max_items=500
        )
        
        return result
    except ValueError as e:
        # 预设不存在等业务错误
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"批量应用预设失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"批量应用失败: {str(e)}"
        )

