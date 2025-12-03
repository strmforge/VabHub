"""
刮削开关设置API
管理媒体文件刮削时的各种元数据文件生成开关
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Optional, Any
from pydantic import BaseModel
from loguru import logger

from app.core.database import get_db
from app.modules.settings.service import SettingsService
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter(prefix="/system/setting", tags=["系统设置"])


class ScrapingSwitches(BaseModel):
    """刮削开关设置"""
    # 电影
    movie_nfo: bool = True
    movie_poster: bool = True
    movie_backdrop: bool = True
    movie_logo: bool = True
    movie_disc: bool = True
    movie_banner: bool = True
    movie_thumb: bool = True
    
    # 电视剧
    tv_nfo: bool = True
    tv_poster: bool = True
    tv_backdrop: bool = True
    tv_banner: bool = True
    tv_logo: bool = True
    tv_thumb: bool = True
    
    # 季
    season_nfo: bool = True
    season_poster: bool = True
    season_banner: bool = True
    season_thumb: bool = True
    
    # 集
    episode_nfo: bool = True
    episode_thumb: bool = True


@router.get("/ScrapingSwitchs", response_model=BaseResponse)
async def get_scraping_switches(db = Depends(get_db)):
    """
    获取刮削开关设置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "value": {
                "movie_nfo": true,
                "movie_poster": true,
                ...
            }
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        settings_service = SettingsService(db)
        
        # 从数据库获取刮削开关设置
        switches = await settings_service.get_setting("scraping_switches", {})
        
        # 如果不存在，返回默认值
        if not switches:
            default_switches = ScrapingSwitches()
            switches = default_switches.model_dump()
        
        return success_response(
            data={"value": switches},
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取刮削开关设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取刮削开关设置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/ScrapingSwitchs", response_model=BaseResponse)
async def update_scraping_switches(
    switches: Dict[str, Any],
    db = Depends(get_db)
):
    """
    更新刮削开关设置
    
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
        
        # 验证数据格式
        try:
            validated_switches = ScrapingSwitches(**switches)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="VALIDATION_ERROR",
                    error_message=f"刮削开关设置格式错误: {str(e)}"
                ).model_dump()
            )
        
        # 保存到数据库
        await settings_service.set_setting(
            key="scraping_switches",
            value=validated_switches.model_dump(),
            category="scraping",
            description="刮削开关设置"
        )
        
        return success_response(message="更新成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新刮削开关设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新刮削开关设置时发生错误: {str(e)}"
            ).model_dump()
        )

