"""
系统设置API
提供基础设置和高级设置的统一管理接口
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field, RootModel
from loguru import logger
import secrets
import string

from app.core.database import get_db
from app.core.config import settings as app_settings
from app.modules.settings.service import SettingsService
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter(prefix="/system", tags=["系统设置"])


class SystemEnvResponse(BaseModel):
    """系统环境变量响应"""
    # 基础设置
    APP_DOMAIN: Optional[str] = None
    RECOGNIZE_SOURCE: str = "themoviedb"
    API_TOKEN: Optional[str] = None
    WALLPAPER: str = "tmdb"
    CUSTOMIZE_WALLPAPER_API_URL: Optional[str] = None
    MEDIASERVER_SYNC_INTERVAL: Optional[int] = 6
    GITHUB_TOKEN: Optional[str] = None
    OCR_HOST: Optional[str] = None
    
    # 高级设置 - 系统
    AUXILIARY_AUTH_ENABLE: bool = False
    GLOBAL_IMAGE_CACHE: bool = False
    SUBSCRIBE_STATISTIC_SHARE: bool = True
    PLUGIN_STATISTIC_SHARE: bool = True
    WORKFLOW_STATISTIC_SHARE: bool = True
    BIG_MEMORY_MODE: bool = False
    DB_WAL_ENABLE: bool = True
    VABHUB_AUTO_UPDATE: str = "false"
    AUTO_UPDATE_RESOURCE: bool = True
    
    # 高级设置 - 媒体
    TMDB_API_KEY: Optional[str] = None  # TMDB API Key（用户需要自己申请）
    TMDB_API_DOMAIN: str = "api.themoviedb.org"
    TMDB_IMAGE_DOMAIN: str = "image.tmdb.org"
    TMDB_LOCALE: str = "zh"
    META_CACHE_EXPIRE: int = 0
    SCRAP_FOLLOW_TMDB: bool = True
    FANART_ENABLE: bool = False
    FANART_LANG: str = "zh,en"
    TMDB_SCRAP_ORIGINAL_IMAGE: Optional[bool] = None
    # TVDB和Fanart API Key使用内置默认值，不在UI中显示
    
    # 高级设置 - 网络
    PROXY_HOST: Optional[str] = None
    GITHUB_PROXY: Optional[str] = None
    PIP_PROXY: Optional[str] = None
    DOH_ENABLE: bool = False
    DOH_RESOLVERS: str = "1.0.0.1,1.1.1.1,9.9.9.9,149.112.112.112"
    DOH_DOMAINS: str = "api.themoviedb.org,api.tmdb.org,webservice.fanart.tv,api.github.com,github.com"
    SECURITY_IMAGE_DOMAINS: list = Field(default_factory=list)
    
    # 高级设置 - 日志
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_MAX_FILE_SIZE: str = "5"
    LOG_BACKUP_COUNT: str = "3"
    LOG_FILE_FORMAT: str = "【%(levelname)s】%(asctime)s - %(message)s"
    
    # 高级设置 - 实验室
    PLUGIN_AUTO_RELOAD: bool = False
    ENCODING_DETECTION_PERFORMANCE_MODE: bool = True


class SystemEnvUpdate(RootModel[Dict[str, Any]]):
    """系统环境变量更新请求"""
    # 允许更新所有字段（Pydantic v2 使用 RootModel）
    root: Dict[str, Any]


def generate_api_token(length: int = 32) -> str:
    """生成随机API令牌"""
    charset = string.ascii_letters + string.digits + '-_'
    return ''.join(secrets.choice(charset) for _ in range(length))


def validate_api_token(token: Optional[str]) -> tuple[bool, Optional[str]]:
    """
    验证API令牌
    
    Returns:
        (是否有效, 错误信息或新生成的令牌)
    """
    if not token:
        # 自动生成新令牌
        new_token = generate_api_token()
        logger.info(f"API_TOKEN未设置，已自动生成: {new_token[:8]}...")
        return False, new_token
    
    if len(token) < 16:
        # 令牌长度不足，自动生成新令牌
        new_token = generate_api_token()
        logger.warning(f"API_TOKEN长度不足16个字符，已自动生成新令牌: {new_token[:8]}...")
        return False, new_token
    
    return True, None


@router.get("/api-token", response_model=BaseResponse)
async def get_api_token():
    """
    获取API Token（只读，用于显示）
    
    Returns:
        API Token值
    """
    try:
        from app.core.config import settings
        api_token = settings.API_TOKEN_DYNAMIC
        return success_response(
            data={"api_token": api_token},
            message="API Token获取成功"
        )
    except Exception as e:
        logger.error(f"获取API Token失败: {e}")
        return error_response(
            error_code="INTERNAL_SERVER_ERROR",
            error_message=f"获取API Token失败: {str(e)}"
        )


@router.get("/env", response_model=BaseResponse)
async def get_system_env(db = Depends(get_db)):
    """
    获取系统环境变量（配置）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "APP_DOMAIN": "...",
            "RECOGNIZE_SOURCE": "themoviedb",
            ...
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        # 从数据库设置服务获取配置
        settings_service = SettingsService(db)
        db_settings = await settings_service.get_all_settings()
        
        # 构建响应数据（优先使用数据库设置，否则使用环境变量/默认值）
        env_data = SystemEnvResponse()
        
        # 基础设置
        env_data.APP_DOMAIN = db_settings.get("APP_DOMAIN") or app_settings.APP_DOMAIN or None
        env_data.RECOGNIZE_SOURCE = db_settings.get("RECOGNIZE_SOURCE") or app_settings.RECOGNIZE_SOURCE
        env_data.API_TOKEN = db_settings.get("API_TOKEN") or app_settings.API_TOKEN
        env_data.WALLPAPER = db_settings.get("WALLPAPER") or app_settings.WALLPAPER
        env_data.CUSTOMIZE_WALLPAPER_API_URL = db_settings.get("CUSTOMIZE_WALLPAPER_API_URL") or app_settings.CUSTOMIZE_WALLPAPER_API_URL
        env_data.MEDIASERVER_SYNC_INTERVAL = db_settings.get("MEDIASERVER_SYNC_INTERVAL") or app_settings.MEDIASERVER_SYNC_INTERVAL
        env_data.GITHUB_TOKEN = db_settings.get("GITHUB_TOKEN") or app_settings.GITHUB_TOKEN
        env_data.OCR_HOST = db_settings.get("OCR_HOST") or app_settings.OCR_HOST
        
        # 高级设置 - 系统
        env_data.AUXILIARY_AUTH_ENABLE = db_settings.get("AUXILIARY_AUTH_ENABLE", app_settings.AUXILIARY_AUTH_ENABLE)
        env_data.GLOBAL_IMAGE_CACHE = db_settings.get("GLOBAL_IMAGE_CACHE", app_settings.GLOBAL_IMAGE_CACHE)
        env_data.SUBSCRIBE_STATISTIC_SHARE = db_settings.get("SUBSCRIBE_STATISTIC_SHARE", app_settings.SUBSCRIBE_STATISTIC_SHARE)
        env_data.PLUGIN_STATISTIC_SHARE = db_settings.get("PLUGIN_STATISTIC_SHARE", app_settings.PLUGIN_STATISTIC_SHARE)
        env_data.WORKFLOW_STATISTIC_SHARE = db_settings.get("WORKFLOW_STATISTIC_SHARE", app_settings.WORKFLOW_STATISTIC_SHARE)
        env_data.BIG_MEMORY_MODE = db_settings.get("BIG_MEMORY_MODE", app_settings.BIG_MEMORY_MODE)
        env_data.DB_WAL_ENABLE = db_settings.get("DB_WAL_ENABLE", app_settings.DB_WAL_ENABLE)
        env_data.VABHUB_AUTO_UPDATE = db_settings.get("VABHUB_AUTO_UPDATE", app_settings.VABHUB_AUTO_UPDATE)
        env_data.AUTO_UPDATE_RESOURCE = db_settings.get("AUTO_UPDATE_RESOURCE", app_settings.AUTO_UPDATE_RESOURCE)
        
        # 高级设置 - 媒体
        env_data.TMDB_API_KEY = db_settings.get("TMDB_API_KEY") or app_settings.TMDB_API_KEY or ""
        env_data.TMDB_API_DOMAIN = db_settings.get("TMDB_API_DOMAIN") or app_settings.TMDB_API_DOMAIN
        env_data.TMDB_IMAGE_DOMAIN = db_settings.get("TMDB_IMAGE_DOMAIN") or app_settings.TMDB_IMAGE_DOMAIN
        env_data.TMDB_LOCALE = db_settings.get("TMDB_LOCALE") or app_settings.TMDB_LOCALE
        env_data.META_CACHE_EXPIRE = db_settings.get("META_CACHE_EXPIRE", app_settings.META_CACHE_EXPIRE)
        env_data.SCRAP_FOLLOW_TMDB = db_settings.get("SCRAP_FOLLOW_TMDB", app_settings.SCRAP_FOLLOW_TMDB)
        env_data.FANART_ENABLE = db_settings.get("FANART_ENABLE", app_settings.FANART_ENABLE)
        env_data.FANART_LANG = db_settings.get("FANART_LANG") or app_settings.FANART_LANG
        env_data.TMDB_SCRAP_ORIGINAL_IMAGE = db_settings.get("TMDB_SCRAP_ORIGINAL_IMAGE", app_settings.TMDB_SCRAP_ORIGINAL_IMAGE)
        
        # 高级设置 - 网络
        env_data.PROXY_HOST = db_settings.get("PROXY_HOST") or app_settings.PROXY_HOST
        env_data.GITHUB_PROXY = db_settings.get("GITHUB_PROXY") or app_settings.GITHUB_PROXY
        env_data.PIP_PROXY = db_settings.get("PIP_PROXY") or app_settings.PIP_PROXY
        env_data.DOH_ENABLE = db_settings.get("DOH_ENABLE", app_settings.DOH_ENABLE)
        env_data.DOH_RESOLVERS = db_settings.get("DOH_RESOLVERS") or app_settings.DOH_RESOLVERS
        env_data.DOH_DOMAINS = db_settings.get("DOH_DOMAINS") or app_settings.DOH_DOMAINS
        security_domains = db_settings.get("SECURITY_IMAGE_DOMAINS")
        if security_domains:
            if isinstance(security_domains, str):
                import json
                try:
                    env_data.SECURITY_IMAGE_DOMAINS = json.loads(security_domains)
                except:
                    env_data.SECURITY_IMAGE_DOMAINS = [security_domains]
            else:
                env_data.SECURITY_IMAGE_DOMAINS = security_domains
        else:
            env_data.SECURITY_IMAGE_DOMAINS = app_settings.SECURITY_IMAGE_DOMAINS
        
        # 高级设置 - 日志
        env_data.DEBUG = db_settings.get("DEBUG", app_settings.DEBUG)
        env_data.LOG_LEVEL = db_settings.get("LOG_LEVEL") or app_settings.LOG_LEVEL
        env_data.LOG_MAX_FILE_SIZE = db_settings.get("LOG_MAX_FILE_SIZE") or app_settings.LOG_MAX_FILE_SIZE
        env_data.LOG_BACKUP_COUNT = db_settings.get("LOG_BACKUP_COUNT") or app_settings.LOG_BACKUP_COUNT
        env_data.LOG_FILE_FORMAT = db_settings.get("LOG_FILE_FORMAT") or app_settings.LOG_FILE_FORMAT
        
        # 高级设置 - 实验室
        env_data.PLUGIN_AUTO_RELOAD = db_settings.get("PLUGIN_AUTO_RELOAD", app_settings.PLUGIN_AUTO_RELOAD)
        env_data.ENCODING_DETECTION_PERFORMANCE_MODE = db_settings.get("ENCODING_DETECTION_PERFORMANCE_MODE", app_settings.ENCODING_DETECTION_PERFORMANCE_MODE)
        
        return success_response(data=env_data.model_dump(), message="获取成功")
    except Exception as e:
        logger.error(f"获取系统环境变量失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取系统环境变量时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/env", response_model=BaseResponse)
async def update_system_env(
    update: Dict[str, Any],
    db = Depends(get_db)
):
    """
    更新系统环境变量（配置）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        settings_service = SettingsService(db)
        
        # 验证API_TOKEN
        if "API_TOKEN" in update:
            is_valid, new_token = validate_api_token(update["API_TOKEN"])
            if not is_valid and new_token:
                # 自动更新为新生成的令牌
                update["API_TOKEN"] = new_token
                logger.info("API_TOKEN已自动更新")
        
        # 处理空字符串（设置为None以恢复默认值）
        cleaned_update = {}
        for key, value in update.items():
            if value == "" or value is None:
                # 某些字段允许为空，某些需要设置为None
                if key in ["APP_DOMAIN", "CUSTOMIZE_WALLPAPER_API_URL", "GITHUB_TOKEN", 
                          "PROXY_HOST", "GITHUB_PROXY", "PIP_PROXY", "TMDB_SCRAP_ORIGINAL_IMAGE"]:
                    cleaned_update[key] = None
                else:
                    # 其他字段保持原值或使用默认值
                    continue
            else:
                cleaned_update[key] = value
        
        # 保存到数据库
        # 导入API密钥管理器
        from app.core.api_key_manager import get_api_key_manager
        api_key_manager = get_api_key_manager()
        
        for key, value in cleaned_update.items():
            # 特殊处理：API密钥使用加密存储
            if key == "TMDB_API_KEY":
                # TMDB API Key保存到加密存储
                if value:
                    api_key_manager.set_tmdb_api_key(value)
                    logger.info("TMDB API Key已保存到加密存储")
                # 同时保存到数据库（标记为加密，但实际值已加密存储）
                await settings_service.set_setting(key, "", category="advanced_media", is_encrypted=True)
                continue
            elif key == "TVDB_V4_API_KEY":
                # TVDB API Key保存到加密存储
                if value:
                    # 获取PIN（如果有）
                    tvdb_pin = cleaned_update.get("TVDB_V4_API_PIN", "")
                    api_key_manager.set_tvdb_api_key(value, tvdb_pin)
                    logger.info("TVDB API Key已保存到加密存储")
                # 同时保存到数据库（标记为加密）
                await settings_service.set_setting(key, "", category="advanced_media", is_encrypted=True)
                continue
            elif key == "TVDB_V4_API_PIN":
                # TVDB API PIN保存到加密存储（与API Key一起）
                # 已经在TVDB_V4_API_KEY处理中处理，这里跳过
                continue
            elif key == "FANART_API_KEY":
                # Fanart API Key保存到加密存储
                if value:
                    api_key_manager.set_fanart_api_key(value)
                    logger.info("Fanart API Key已保存到加密存储")
                # 同时保存到数据库（标记为加密）
                await settings_service.set_setting(key, "", category="advanced_media", is_encrypted=True)
                continue
            
            # 确定分类
            if key in ["APP_DOMAIN", "RECOGNIZE_SOURCE", "API_TOKEN", "WALLPAPER", 
                      "CUSTOMIZE_WALLPAPER_API_URL", "MEDIASERVER_SYNC_INTERVAL", 
                      "GITHUB_TOKEN", "OCR_HOST"]:
                category = "basic"
            elif key in ["AUXILIARY_AUTH_ENABLE", "GLOBAL_IMAGE_CACHE", "SUBSCRIBE_STATISTIC_SHARE",
                        "PLUGIN_STATISTIC_SHARE", "WORKFLOW_STATISTIC_SHARE", "BIG_MEMORY_MODE",
                        "DB_WAL_ENABLE", "VABHUB_AUTO_UPDATE", "AUTO_UPDATE_RESOURCE"]:
                category = "advanced_system"
            elif key in ["TMDB_API_DOMAIN", "TMDB_IMAGE_DOMAIN", "TMDB_LOCALE", "META_CACHE_EXPIRE",
                        "SCRAP_FOLLOW_TMDB", "FANART_ENABLE", "FANART_LANG", "TMDB_SCRAP_ORIGINAL_IMAGE"]:
                category = "advanced_media"
            elif key in ["PROXY_HOST", "GITHUB_PROXY", "PIP_PROXY", "DOH_ENABLE", "DOH_RESOLVERS",
                        "DOH_DOMAINS", "SECURITY_IMAGE_DOMAINS"]:
                category = "advanced_network"
            elif key in ["DEBUG", "LOG_LEVEL", "LOG_MAX_FILE_SIZE", "LOG_BACKUP_COUNT", "LOG_FILE_FORMAT"]:
                category = "advanced_log"
            elif key in ["PLUGIN_AUTO_RELOAD", "ENCODING_DETECTION_PERFORMANCE_MODE"]:
                category = "advanced_lab"
            else:
                category = "basic"
            
            # 确定是否为加密字段
            is_encrypted = key.endswith("_TOKEN") or key.endswith("_KEY") or key.endswith("_PASSWORD")
            
            await settings_service.set_setting(key, value, category, is_encrypted=is_encrypted)
        
        return success_response(message="更新成功")
    except Exception as e:
        logger.error(f"更新系统环境变量失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新系统环境变量时发生错误: {str(e)}"
            ).model_dump()
        )


# 兼容性端点（映射到 /env）
@router.get("/settings", response_model=BaseResponse)
async def get_system_settings(db = Depends(get_db)):
    """
    获取系统设置（兼容性端点）
    
    映射到 /env
    """
    return await get_system_env(db)


@router.put("/settings", response_model=BaseResponse)
async def update_system_settings(
    update: Dict[str, Any],
    db = Depends(get_db)
):
    """
    更新系统设置（兼容性端点）
    
    映射到 /env
    """
    return await update_system_env(update, db)


@router.get("/settings/{key}", response_model=BaseResponse)
async def get_system_setting(
    key: str,
    db = Depends(get_db)
):
    """
    获取单个系统设置项
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "key": "TMDB_API_KEY",
            "value": "...",
            "category": "advanced_media"
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        settings_service = SettingsService(db)
        
        # 尝试从数据库获取
        value = await settings_service.get_setting(key)
        
        # 如果是API密钥，从加密存储获取
        if key in ["TMDB_API_KEY", "TVDB_V4_API_KEY", "FANART_API_KEY"]:
            from app.core.api_key_manager import get_api_key_manager
            api_key_manager = get_api_key_manager()
            
            if key == "TMDB_API_KEY":
                value = api_key_manager.get_tmdb_api_key()
            elif key == "TVDB_V4_API_KEY":
                value = api_key_manager.get_tvdb_api_key()
            elif key == "FANART_API_KEY":
                value = api_key_manager.get_fanart_api_key()
        
        # 确定分类
        if key in ["APP_DOMAIN", "RECOGNIZE_SOURCE", "API_TOKEN", "WALLPAPER", 
                  "CUSTOMIZE_WALLPAPER_API_URL", "MEDIASERVER_SYNC_INTERVAL", 
                  "GITHUB_TOKEN", "OCR_HOST"]:
            category = "basic"
        elif key in ["AUXILIARY_AUTH_ENABLE", "GLOBAL_IMAGE_CACHE", "SUBSCRIBE_STATISTIC_SHARE",
                    "PLUGIN_STATISTIC_SHARE", "WORKFLOW_STATISTIC_SHARE", "BIG_MEMORY_MODE",
                    "DB_WAL_ENABLE", "VABHUB_AUTO_UPDATE", "AUTO_UPDATE_RESOURCE"]:
            category = "advanced_system"
        elif key in ["TMDB_API_DOMAIN", "TMDB_IMAGE_DOMAIN", "TMDB_LOCALE", "META_CACHE_EXPIRE",
                    "SCRAP_FOLLOW_TMDB", "FANART_ENABLE", "FANART_LANG", "TMDB_SCRAP_ORIGINAL_IMAGE"]:
            category = "advanced_media"
        elif key in ["PROXY_HOST", "GITHUB_PROXY", "PIP_PROXY", "DOH_ENABLE", "DOH_RESOLVERS",
                    "DOH_DOMAINS", "SECURITY_IMAGE_DOMAINS"]:
            category = "advanced_network"
        elif key in ["DEBUG", "LOG_LEVEL", "LOG_MAX_FILE_SIZE", "LOG_BACKUP_COUNT", "LOG_FILE_FORMAT"]:
            category = "advanced_log"
        elif key in ["PLUGIN_AUTO_RELOAD", "ENCODING_DETECTION_PERFORMANCE_MODE"]:
            category = "advanced_lab"
        else:
            category = "basic"
        
        return success_response(
            data={
                "key": key,
                "value": value,
                "category": category
            },
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取系统设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取系统设置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.put("/settings/{key}", response_model=BaseResponse)
async def update_system_setting(
    key: str,
    value: Any,
    db = Depends(get_db)
):
    """
    更新单个系统设置项
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        # 使用批量更新方法
        update_dict = {key: value}
        return await update_system_env(update_dict, db)
    except Exception as e:
        logger.error(f"更新系统设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新系统设置时发生错误: {str(e)}"
            ).model_dump()
        )

