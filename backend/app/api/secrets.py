"""
密钥管理API
用于查看密钥状态
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from loguru import logger

from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter(prefix="/secrets", tags=["密钥管理"])


class SecretStatus(BaseModel):
    """密钥状态"""
    secret_manager_enabled: bool = True
    api_key_manager_enabled: bool = True
    secrets_file_exists: bool = False
    api_keys_encrypted: bool = True
    tmdb_api_key_configured: bool = False
    tvdb_api_key_configured: bool = False
    fanart_api_key_configured: bool = False
    douban_api_key_configured: bool = False
    api_token_configured: bool = False


@router.get("/status", response_model=BaseResponse)
async def get_secrets_status():
    """
    获取密钥状态
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": SecretStatus,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from pathlib import Path
        from app.core.secret_manager import get_secret_manager
        from app.core.api_key_manager import get_api_key_manager
        
        secret_manager = get_secret_manager()
        api_key_manager = get_api_key_manager()
        
        # 检查密钥文件是否存在
        secrets_file = Path("./data/.vabhub_secrets.json")
        secrets_file_exists = secrets_file.exists()
        
        # 检查API密钥是否已配置
        tmdb_api_key_configured = bool(api_key_manager.get_tmdb_api_key())
        tvdb_api_key_configured = bool(api_key_manager.get_tvdb_api_key())
        fanart_api_key_configured = bool(api_key_manager.get_fanart_api_key())
        
        # 检查其他密钥
        api_token_configured = bool(secret_manager.get_api_token())
        
        # 检查Douban API Key（从设置中获取）
        try:
            from app.modules.settings.service import SettingsService
            from app.core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                settings_service = SettingsService(db)
                douban_api_key = await settings_service.get_setting("DOUBAN_API_KEY", category="advanced_media")
                douban_api_key_configured = bool(douban_api_key)
        except:
            douban_api_key_configured = False
        
        status_data = SecretStatus(
            secret_manager_enabled=True,
            api_key_manager_enabled=True,
            secrets_file_exists=secrets_file_exists,
            api_keys_encrypted=True,  # APIKeyManager使用Fernet加密
            tmdb_api_key_configured=tmdb_api_key_configured,
            tvdb_api_key_configured=tvdb_api_key_configured,
            fanart_api_key_configured=fanart_api_key_configured,
            douban_api_key_configured=douban_api_key_configured,
            api_token_configured=api_token_configured
        )
        
        return success_response(
            data=status_data.model_dump(),
            message="获取密钥状态成功"
        )
    except Exception as e:
        logger.error(f"获取密钥状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取密钥状态时发生错误: {str(e)}"
            ).model_dump()
        )

