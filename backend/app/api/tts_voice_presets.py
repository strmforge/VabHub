"""
TTS 声线预设 Dev API

提供 TTS 声线预设的管理接口（仅在 Dev 模式下可用）
"""

from fastapi import APIRouter, Depends, HTTPException, Path as PathParam
from typing import List, Optional
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.config import settings
from app.core.database import get_db
from app.models.tts_voice_preset import TTSVoicePreset
from app.schemas.tts import (
    TTSVoicePresetResponse,
    UpsertTTSVoicePresetRequest
)

router = APIRouter()


@router.get("/voice-presets", response_model=List[TTSVoicePresetResponse], summary="获取所有 TTS 声线预设")
async def list_voice_presets(
    db: AsyncSession = Depends(get_db)
) -> List[TTSVoicePresetResponse]:
    """
    获取所有 TTS 声线预设列表
    
    此接口仅在 Dev 模式下可用。
    
    Args:
        db: 数据库会话
    
    Returns:
        List[TTSVoicePresetResponse]: 预设列表，按创建时间排序
    """
    # Dev guard
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="此接口仅在 DEBUG 模式下可用"
        )
    
    result = await db.execute(
        select(TTSVoicePreset)
        .order_by(desc(TTSVoicePreset.created_at))
    )
    presets = result.scalars().all()
    
    return [TTSVoicePresetResponse.model_validate(preset) for preset in presets]


@router.post("/voice-presets", response_model=TTSVoicePresetResponse, summary="创建/更新 TTS 声线预设")
async def upsert_voice_preset(
    payload: UpsertTTSVoicePresetRequest,
    db: AsyncSession = Depends(get_db)
) -> TTSVoicePresetResponse:
    """
    创建或更新 TTS 声线预设
    
    此接口仅在 Dev 模式下可用。
    
    如果 is_default=True，会将其他预设的 is_default 设为 False。
    
    Args:
        payload: 预设数据（id 为 None 则创建，否则更新）
        db: 数据库会话
    
    Returns:
        TTSVoicePresetResponse: 创建/更新后的预设
    """
    # Dev guard
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="此接口仅在 DEBUG 模式下可用"
        )
    
    if payload.id:
        # 更新现有预设
        result = await db.execute(
            select(TTSVoicePreset)
            .where(TTSVoicePreset.id == payload.id)
        )
        preset = result.scalar_one_or_none()
        
        if not preset:
            raise HTTPException(status_code=404, detail=f"TTSVoicePreset {payload.id} not found")
        
        # 检查 name 唯一性（如果 name 被修改）
        if preset.name != payload.name:
            name_check = await db.execute(
                select(TTSVoicePreset)
                .where(TTSVoicePreset.name == payload.name)
            )
            if name_check.scalar_one_or_none():
                raise HTTPException(status_code=400, detail=f"预设名称 '{payload.name}' 已存在")
        
        # 更新字段
        preset.name = payload.name
        preset.provider = payload.provider
        preset.language = payload.language
        preset.voice = payload.voice
        preset.speed = payload.speed
        preset.pitch = payload.pitch
        preset.notes = payload.notes
        
        # 处理 is_default 标志
        if payload.is_default:
            # 将其他预设的 is_default 设为 False
            other_defaults_result = await db.execute(
                select(TTSVoicePreset)
                .where(TTSVoicePreset.id != preset.id)
                .where(TTSVoicePreset.is_default == True)
            )
            for other in other_defaults_result.scalars().all():
                other.is_default = False
        
        preset.is_default = payload.is_default
        logger.info(f"更新 TTS 声线预设: {preset.name}")
    else:
        # 创建新预设
        # 检查 name 唯一性
        name_check = await db.execute(
            select(TTSVoicePreset)
            .where(TTSVoicePreset.name == payload.name)
        )
        if name_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"预设名称 '{payload.name}' 已存在")
        
        # 如果设置为默认，先将其他预设的 is_default 设为 False
        if payload.is_default:
            other_defaults_result = await db.execute(
                select(TTSVoicePreset)
                .where(TTSVoicePreset.is_default == True)
            )
            for other in other_defaults_result.scalars().all():
                other.is_default = False
        
        preset = TTSVoicePreset(
            name=payload.name,
            provider=payload.provider,
            language=payload.language,
            voice=payload.voice,
            speed=payload.speed,
            pitch=payload.pitch,
            is_default=payload.is_default,
            notes=payload.notes
        )
        db.add(preset)
        logger.info(f"创建 TTS 声线预设: {preset.name}")
    
    await db.commit()
    await db.refresh(preset)
    
    return TTSVoicePresetResponse.model_validate(preset)


@router.delete("/voice-presets/{preset_id}", summary="删除 TTS 声线预设")
async def delete_voice_preset(
    preset_id: int = PathParam(..., description="预设 ID"),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    删除指定 TTS 声线预设
    
    此接口仅在 Dev 模式下可用。
    
    如果有 TTSWorkProfile 引用了该预设，会自动将它们的 preset_id 置为 None。
    
    Args:
        preset_id: 预设 ID
        db: 数据库会话
    
    Returns:
        dict: 删除结果
    """
    # Dev guard
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="此接口仅在 DEBUG 模式下可用"
        )
    
    # 查找预设
    result = await db.execute(
        select(TTSVoicePreset)
        .where(TTSVoicePreset.id == preset_id)
    )
    preset = result.scalar_one_or_none()
    
    if not preset:
        raise HTTPException(status_code=404, detail=f"TTSVoicePreset {preset_id} not found")
    
    # 查找引用该预设的 Profile，将它们的 preset_id 置为 None
    from app.models.tts_work_profile import TTSWorkProfile
    profiles_result = await db.execute(
        select(TTSWorkProfile)
        .where(TTSWorkProfile.preset_id == preset_id)
    )
    affected_profiles = profiles_result.scalars().all()
    for profile in affected_profiles:
        profile.preset_id = None
        logger.debug(f"将 Profile {profile.id} 的 preset_id 置为 None（预设 {preset_id} 被删除）")
    
    # 删除预设
    await db.delete(preset)
    await db.commit()
    
    logger.info(f"删除 TTS 声线预设: {preset.name}，影响了 {len(affected_profiles)} 个 Profile")
    
    return {
        "success": True,
        "message": f"TTSVoicePreset {preset_id} deleted",
        "affected_profiles": len(affected_profiles)
    }

