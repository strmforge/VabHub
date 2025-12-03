"""
有声书文件播放 API

提供有声书文件的流式播放功能
"""
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.core.database import get_db
from app.core.config import settings
from app.models.audiobook import AudiobookFile
from app.api.auth import oauth2_scheme
from app.core.security import decode_access_token
from app.models.user import User

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


@router.get("/files/{file_id}/stream", summary="流式播放有声书文件")
async def stream_audiobook_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    流式播放有声书文件
    
    根据 file_id 查询 AudiobookFile，返回音频文件流。
    需要登录用户，但不做复杂权限校验（Alpha 阶段）。
    """
    try:
        # 查询文件记录
        stmt = select(AudiobookFile).where(
            AudiobookFile.id == file_id,
            AudiobookFile.is_deleted == False
        )
        result = await db.execute(stmt)
        audiobook_file = result.scalar_one_or_none()
        
        if not audiobook_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audiobook file not found"
            )
        
        # 构建文件路径
        file_path = Path(audiobook_file.file_path)
        
        # 如果是相对路径，尝试从配置的根目录解析
        if not file_path.is_absolute():
            # 尝试从多个可能的根目录查找
            possible_roots = [
                Path(settings.EBOOK_LIBRARY_ROOT) / "Audiobooks",
                Path(settings.SMART_TTS_OUTPUT_ROOT),
                Path("."),
            ]
            
            for root in possible_roots:
                full_path = root / file_path
                if full_path.exists():
                    file_path = full_path
                    break
            else:
                # 如果都找不到，尝试直接使用相对路径
                if not file_path.exists():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Audio file not found: {audiobook_file.file_path}"
                    )
        else:
            if not file_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Audio file not found: {audiobook_file.file_path}"
                )
        
        # 确定 Content-Type
        content_type_map = {
            "mp3": "audio/mpeg",
            "m4a": "audio/mp4",
            "m4b": "audio/mp4",
            "flac": "audio/flac",
            "ogg": "audio/ogg",
            "opus": "audio/opus",
            "aac": "audio/aac",
            "wav": "audio/wav",
        }
        content_type = content_type_map.get(audiobook_file.format.lower(), "audio/mpeg")
        
        return FileResponse(
            path=str(file_path),
            media_type=content_type,
            filename=file_path.name,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stream audiobook file {file_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stream audio file: {str(e)}"
        )

