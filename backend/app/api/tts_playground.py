"""
TTS Playground API

提供开发调试用的 TTS 单次合成接口
"""

import os
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.core.config import settings
from app.core.database import get_db
from app.schemas.tts import TTSPlaygroundRequest, TTSPlaygroundResponse
from app.modules.tts.factory import get_tts_engine
from app.modules.tts.base import TTSRequest
from app.modules.tts.rate_limiter import should_allow, record_request, get_state as get_rate_limit_state
from app.modules.tts.profile_service import resolve_tts_profile_for_ebook
from app.models.ebook import EBook

router = APIRouter()


def _check_debug_mode():
    """检查是否在 DEBUG 模式下"""
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="TTS Playground API 仅在 DEBUG 模式下可用"
        )


@router.post("/playground/synthesize", response_model=TTSPlaygroundResponse)
async def synthesize_playground(
    request: TTSPlaygroundRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    TTS Playground 单次合成接口
    
    输入文本，调用当前 TTS 引擎生成音频，返回可播放的 URL
    """
    _check_debug_mode()
    
    # 校验文本
    if not request.text or len(request.text.strip()) == 0:
        return TTSPlaygroundResponse(
            success=False,
            message="文本不能为空",
            char_count=0
        )
    
    if len(request.text) > 5000:
        return TTSPlaygroundResponse(
            success=False,
            message="文本长度不能超过 5000 字符",
            char_count=len(request.text)
        )
    
    char_count = len(request.text)
    
    try:
        # 解析 TTS Profile
        resolved_provider = settings.SMART_TTS_PROVIDER or "dummy"
        resolved_language = None
        resolved_voice = None
        resolved_speed = None
        resolved_pitch = None
        
        if request.ebook_id:
            # 从作品 Profile 解析
            ebook_result = await db.execute(
                select(EBook).where(EBook.id == request.ebook_id)
            )
            ebook = ebook_result.scalar_one_or_none()
            
            if not ebook:
                return TTSPlaygroundResponse(
                    success=False,
                    message=f"EBook {request.ebook_id} 不存在",
                    char_count=char_count
                )
            
            try:
                resolved_profile = await resolve_tts_profile_for_ebook(
                    db,
                    ebook,
                    settings
                )
                resolved_provider = resolved_profile.provider
                resolved_language = resolved_profile.language
                resolved_voice = resolved_profile.voice
                resolved_speed = resolved_profile.speed
                resolved_pitch = resolved_profile.pitch
            except Exception as e:
                logger.warning(f"解析 EBook {request.ebook_id} 的 TTS Profile 失败: {e}")
                # 继续使用全局默认值
        
        # 使用全局默认值（如果未从 Profile 解析到）
        if resolved_language is None:
            resolved_language = "zh-CN"
        
        # Request 中的参数优先级最高，覆盖解析结果
        if request.provider is not None:
            resolved_provider = request.provider
        if request.language is not None:
            resolved_language = request.language
        if request.voice is not None:
            resolved_voice = request.voice
        if request.speed is not None:
            resolved_speed = request.speed
        if request.pitch is not None:
            resolved_pitch = request.pitch
        
        # RateLimiter 检查
        rate_limited = False
        rate_limit_reason = None
        
        if not request.skip_rate_limit:
            if not should_allow(char_count, settings=settings, run_context=None):
                rate_limit_state = get_rate_limit_state()
                rate_limit_reason = rate_limit_state.last_limited_reason or "rate_limited"
                
                return TTSPlaygroundResponse(
                    success=False,
                    message=f"请求被限流: {rate_limit_reason}",
                    provider=resolved_provider,
                    language=resolved_language,
                    voice=resolved_voice,
                    speed=resolved_speed,
                    pitch=resolved_pitch,
                    char_count=char_count,
                    rate_limited=True,
                    rate_limit_reason=rate_limit_reason
                )
        
        # 获取 TTS 引擎
        if not settings.SMART_TTS_ENABLED:
            return TTSPlaygroundResponse(
                success=False,
                message="TTS 当前未启用",
                provider=resolved_provider,
                language=resolved_language,
                voice=resolved_voice,
                speed=resolved_speed,
                pitch=resolved_pitch,
                char_count=char_count
            )
        
        tts_engine = get_tts_engine(settings=settings)
        if not tts_engine:
            return TTSPlaygroundResponse(
                success=False,
                message="TTS 引擎不可用",
                provider=resolved_provider,
                language=resolved_language,
                voice=resolved_voice,
                speed=resolved_speed,
                pitch=resolved_pitch,
                char_count=char_count
            )
        
        # 构造目标文件路径
        output_root = Path(settings.SMART_TTS_OUTPUT_ROOT or "./data/tts_output")
        playground_dir = output_root / "playground"
        playground_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        random_id = str(uuid.uuid4())[:8]
        file_name = f"{timestamp}_{random_id}.wav"
        target_path = playground_dir / file_name
        
        # 构造 TTSRequest
        tts_request = TTSRequest(
            text=request.text,
            language=resolved_language,
            voice=resolved_voice,
            speed=resolved_speed,
            pitch=resolved_pitch,
            ebook_id=request.ebook_id
        )
        
        # 调用 TTS 引擎合成
        try:
            tts_result = await tts_engine.synthesize(tts_request, target_path)
            
            # 记录 RateLimiter（如果未被限流且未跳过）
            if not rate_limited and not request.skip_rate_limit:
                record_request(char_count, settings=settings, run_context=None)
            
            # 构造 audio_url
            audio_url = f"/api/dev/tts/playground/audio/{file_name}"
            
            return TTSPlaygroundResponse(
                success=True,
                message="合成成功",
                provider=resolved_provider,
                language=resolved_language,
                voice=resolved_voice,
                speed=resolved_speed,
                pitch=resolved_pitch,
                char_count=char_count,
                duration_seconds=tts_result.duration_seconds,
                audio_url=audio_url,
                rate_limited=False
            )
            
        except Exception as e:
            logger.error(f"TTS 合成失败: {e}", exc_info=True)
            return TTSPlaygroundResponse(
                success=False,
                message=f"TTS 合成失败: {str(e)}",
                provider=resolved_provider,
                language=resolved_language,
                voice=resolved_voice,
                speed=resolved_speed,
                pitch=resolved_pitch,
                char_count=char_count
            )
    
    except Exception as e:
        logger.error(f"TTS Playground 处理失败: {e}", exc_info=True)
        return TTSPlaygroundResponse(
            success=False,
            message=f"处理失败: {str(e)}",
            char_count=char_count
        )


@router.get("/playground/audio/{file_name}")
async def get_playground_audio(
    file_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取 Playground 生成的音频文件
    
    用于前端 <audio> 标签播放
    """
    _check_debug_mode()
    
    # 安全检查：只允许安全字符，避免路径穿越
    if not file_name or not all(c.isalnum() or c in "._-" for c in file_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的文件名"
        )
    
    # 构造文件路径
    output_root = Path(settings.SMART_TTS_OUTPUT_ROOT or "./data/tts_output")
    playground_dir = output_root / "playground"
    file_path = playground_dir / file_name
    
    # 检查文件是否存在
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="音频文件不存在"
        )
    
    # 确定 MIME 类型
    mime_type = "audio/wav"
    if file_name.endswith(".mp3"):
        mime_type = "audio/mpeg"
    elif file_name.endswith(".ogg"):
        mime_type = "audio/ogg"
    
    # 返回文件
    return FileResponse(
        path=str(file_path),
        media_type=mime_type,
        filename=file_name
    )

