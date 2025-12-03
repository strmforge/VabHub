"""
字幕设置API
管理字幕下载的全局设置
"""

from fastapi import APIRouter, Depends, HTTPException, status as http_status
from pydantic import BaseModel
from loguru import logger

from app.core.database import get_db
from app.modules.settings.service import SettingsService
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter()


class SubtitleSettingsResponse(BaseModel):
    """字幕设置响应"""
    auto_download: bool  # 是否自动下载字幕
    default_language: str  # 默认字幕语言
    enabled_sources: list[str]  # 启用的字幕源列表


class SubtitleSettingsUpdate(BaseModel):
    """字幕设置更新"""
    auto_download: bool = None  # 是否自动下载字幕
    default_language: str = None  # 默认字幕语言
    enabled_sources: list[str] = None  # 启用的字幕源列表


@router.get("/", response_model=BaseResponse)
async def get_subtitle_settings(db = Depends(get_db)):
    """
    获取字幕设置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": SubtitleSettingsResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        settings_service = SettingsService(db)
        
        # 从系统设置读取
        auto_download = await settings_service.get_setting("subtitle_auto_download", "false")
        default_language = await settings_service.get_setting("subtitle_default_language", "zh")
        enabled_sources_str = await settings_service.get_setting("subtitle_enabled_sources", "opensubtitles")
        
        # 解析启用的字幕源
        enabled_sources = enabled_sources_str.split(",") if enabled_sources_str else ["opensubtitles"]
        
        settings_response = SubtitleSettingsResponse(
            auto_download=auto_download.lower() == "true" if isinstance(auto_download, str) else bool(auto_download),
            default_language=default_language if isinstance(default_language, str) else "zh",
            enabled_sources=[s.strip() for s in enabled_sources]
        )
        
        return success_response(
            data=settings_response.model_dump(),
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取字幕设置失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取字幕设置时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.put("/", response_model=BaseResponse)
async def update_subtitle_settings(
    settings: SubtitleSettingsUpdate,
    db = Depends(get_db)
):
    """
    更新字幕设置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": SubtitleSettingsResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        settings_service = SettingsService(db)
        
        # 更新设置
        if settings.auto_download is not None:
            await settings_service.set_setting("subtitle_auto_download", str(settings.auto_download).lower())
        
        if settings.default_language is not None:
            await settings_service.set_setting("subtitle_default_language", settings.default_language)
        
        if settings.enabled_sources is not None:
            await settings_service.set_setting("subtitle_enabled_sources", ",".join(settings.enabled_sources))
        
        # 返回更新后的设置
        return await get_subtitle_settings(db)
        
    except Exception as e:
        logger.error(f"更新字幕设置失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新字幕设置时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )

