"""
TTS 作品级配置 Dev API

提供作品级 TTS Profile 的管理接口（仅在 Dev 模式下可用）
"""

from fastapi import APIRouter, Depends, HTTPException, Path as PathParam
from typing import Optional
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.models.ebook import EBook
from app.models.tts_work_profile import TTSWorkProfile
from app.schemas.tts import (
    TTSWorkProfileResponse,
    UpsertTTSWorkProfileRequest
)

router = APIRouter()


@router.get("/work-profile/{ebook_id}", response_model=Optional[TTSWorkProfileResponse], summary="获取作品 TTS Profile")
async def get_work_profile(
    ebook_id: int = PathParam(..., description="电子书 ID"),
    db: AsyncSession = Depends(get_db)
) -> Optional[TTSWorkProfileResponse]:
    """
    获取指定作品的 TTS Profile
    
    此接口仅在 Dev 模式下可用。
    
    Args:
        ebook_id: 电子书 ID
        db: 数据库会话
    
    Returns:
        Optional[TTSWorkProfileResponse]: Profile 信息，不存在则返回 null
    """
    # Dev guard
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="此接口仅在 DEBUG 模式下可用"
        )
    
    # 验证 EBook 存在
    ebook_result = await db.execute(select(EBook).where(EBook.id == ebook_id))
    ebook = ebook_result.scalar_one_or_none()
    if not ebook:
        raise HTTPException(status_code=404, detail=f"EBook {ebook_id} not found")
    
    # 查找 Profile
    result = await db.execute(
        select(TTSWorkProfile)
        .where(TTSWorkProfile.ebook_id == ebook_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        return None
    
    return TTSWorkProfileResponse.model_validate(profile)


@router.post("/work-profile", response_model=TTSWorkProfileResponse, summary="创建/更新作品 TTS Profile")
async def upsert_work_profile(
    payload: UpsertTTSWorkProfileRequest,
    db: AsyncSession = Depends(get_db)
) -> TTSWorkProfileResponse:
    """
    创建或更新指定作品的 TTS Profile
    
    此接口仅在 Dev 模式下可用。
    
    Args:
        payload: Profile 数据
        db: 数据库会话
    
    Returns:
        TTSWorkProfileResponse: 创建/更新后的 Profile
    """
    # Dev guard
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="此接口仅在 DEBUG 模式下可用"
        )
    
    # 验证 EBook 存在
    ebook_result = await db.execute(select(EBook).where(EBook.id == payload.ebook_id))
    ebook = ebook_result.scalar_one_or_none()
    if not ebook:
        raise HTTPException(status_code=404, detail=f"EBook {payload.ebook_id} not found")
    
    # 验证 preset_id（如果提供）
    if payload.preset_id:
        from app.models.tts_voice_preset import TTSVoicePreset
        preset_result = await db.execute(
            select(TTSVoicePreset)
            .where(TTSVoicePreset.id == payload.preset_id)
        )
        preset = preset_result.scalar_one_or_none()
        if not preset:
            raise HTTPException(status_code=404, detail=f"TTSVoicePreset {payload.preset_id} not found")
    
    # 查找现有 Profile
    result = await db.execute(
        select(TTSWorkProfile)
        .where(TTSWorkProfile.ebook_id == payload.ebook_id)
    )
    profile = result.scalar_one_or_none()
    
    if profile:
        # 更新现有 Profile
        profile.preset_id = payload.preset_id
        profile.provider = payload.provider
        profile.language = payload.language
        profile.voice = payload.voice
        profile.speed = payload.speed
        profile.pitch = payload.pitch
        profile.enabled = payload.enabled
        profile.notes = payload.notes
        logger.info(f"更新 EBook {payload.ebook_id} 的 TTS Profile (preset_id={payload.preset_id})")
    else:
        # 创建新 Profile
        profile = TTSWorkProfile(
            ebook_id=payload.ebook_id,
            preset_id=payload.preset_id,
            provider=payload.provider,
            language=payload.language,
            voice=payload.voice,
            speed=payload.speed,
            pitch=payload.pitch,
            enabled=payload.enabled,
            notes=payload.notes
        )
        db.add(profile)
        logger.info(f"为 EBook {payload.ebook_id} 创建新的 TTS Profile (preset_id={payload.preset_id})")
    
    await db.commit()
    await db.refresh(profile)
    
    return TTSWorkProfileResponse.model_validate(profile)


@router.delete("/work-profile/{ebook_id}", summary="删除作品 TTS Profile")
async def delete_work_profile(
    ebook_id: int = PathParam(..., description="电子书 ID"),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    删除指定作品的 TTS Profile
    
    此接口仅在 Dev 模式下可用。
    
    Args:
        ebook_id: 电子书 ID
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
    
    # 查找 Profile
    result = await db.execute(
        select(TTSWorkProfile)
        .where(TTSWorkProfile.ebook_id == ebook_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail=f"TTS Profile for EBook {ebook_id} not found")
    
    await db.delete(profile)
    await db.commit()
    
    logger.info(f"删除 EBook {ebook_id} 的 TTS Profile")
    
    return {"success": True, "message": f"TTS Profile for EBook {ebook_id} deleted"}

