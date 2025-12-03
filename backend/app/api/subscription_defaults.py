"""
默认订阅配置API
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.schemas import BaseResponse
from app.core.security import get_current_user
from app.models.user import User
from app.modules.subscription.defaults import (
    DefaultSubscriptionConfig,
    DefaultSubscriptionConfigService
)
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/subscriptions/default-config", tags=["subscription-defaults"])


# 请求/响应模型
class DefaultSubscriptionConfigRequest(BaseModel):
    """默认订阅配置请求模型"""
    quality: Optional[str] = None
    resolution: Optional[str] = None
    effect: Optional[str] = None
    min_seeders: Optional[int] = None
    auto_download: Optional[bool] = None
    best_version: Optional[bool] = None
    include: Optional[str] = None
    exclude: Optional[str] = None
    filter_group_ids: Optional[List[int]] = None
    allow_hr: Optional[bool] = None
    allow_h3h5: Optional[bool] = None
    strict_free_only: Optional[bool] = None
    sites: Optional[List[int]] = None
    downloader: Optional[str] = None
    save_path: Optional[str] = None


class DefaultSubscriptionConfigResponse(BaseModel):
    """默认订阅配置响应模型"""
    quality: str
    resolution: str
    effect: str
    min_seeders: int
    auto_download: bool
    best_version: bool
    include: str
    exclude: str
    filter_group_ids: List[int]
    allow_hr: bool
    allow_h3h5: bool
    strict_free_only: bool
    sites: List[int]
    downloader: str
    save_path: str


class AllConfigsResponse(BaseModel):
    """所有配置响应模型"""
    configs: Dict[str, DefaultSubscriptionConfigResponse]
    supported_media_types: List[str]


@router.get("/{media_type}", response_model=BaseResponse[DefaultSubscriptionConfigResponse])
async def get_default_subscription_config(
    media_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定媒体类型的默认订阅配置
    
    Args:
        media_type: 媒体类型 (movie, tv, short_drama, anime, music)
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        默认订阅配置
    """
    try:
        service = DefaultSubscriptionConfigService(db)
        
        # 验证媒体类型
        if not service.validate_media_type(media_type):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的媒体类型: {media_type}"
            )
        
        # 获取配置
        config = await service.get_default_config(media_type)
        
        return BaseResponse(
            success=True,
            message="获取默认配置成功",
            data=DefaultSubscriptionConfigResponse(**config.model_dump())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取默认配置失败: {str(e)}"
        )


@router.post("/{media_type}", response_model=BaseResponse[DefaultSubscriptionConfigResponse])
async def save_default_subscription_config(
    media_type: str,
    data: DefaultSubscriptionConfigRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    保存指定媒体类型的默认订阅配置
    
    Args:
        media_type: 媒体类型 (movie, tv, short_drama, anime, music)
        data: 配置数据
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        保存后的配置
    """
    try:
        service = DefaultSubscriptionConfigService(db)
        
        # 验证媒体类型
        if not service.validate_media_type(media_type):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的媒体类型: {media_type}"
            )
        
        # 过滤None值
        config_data = {k: v for k, v in data.model_dump().items() if v is not None}
        
        # 保存配置
        config = await service.save_default_config(media_type, config_data)
        
        return BaseResponse(
            success=True,
            message="保存默认配置成功",
            data=DefaultSubscriptionConfigResponse(**config.model_dump())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"保存默认配置失败: {str(e)}"
        )


@router.delete("/{media_type}", response_model=BaseResponse[DefaultSubscriptionConfigResponse])
async def reset_default_subscription_config(
    media_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    重置指定媒体类型的默认订阅配置为内置值
    
    Args:
        media_type: 媒体类型 (movie, tv, short_drama, anime, music)
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        重置后的配置
    """
    try:
        service = DefaultSubscriptionConfigService(db)
        
        # 验证媒体类型
        if not service.validate_media_type(media_type):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的媒体类型: {media_type}"
            )
        
        # 重置配置
        config = await service.reset_default_config(media_type)
        
        return BaseResponse(
            success=True,
            message="重置默认配置成功",
            data=DefaultSubscriptionConfigResponse(**config.model_dump())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"重置默认配置失败: {str(e)}"
        )


@router.get("", response_model=BaseResponse[AllConfigsResponse])
async def get_all_default_subscription_configs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有媒体类型的默认订阅配置
    
    Args:
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        所有配置
    """
    try:
        service = DefaultSubscriptionConfigService(db)
        
        # 获取所有配置
        configs = await service.get_all_configs()
        
        # 转换为响应格式
        config_responses = {
            media_type: DefaultSubscriptionConfigResponse(**config.model_dump())
            for media_type, config in configs.items()
        }
        
        return BaseResponse(
            success=True,
            message="获取所有默认配置成功",
            data=AllConfigsResponse(
                configs=config_responses,
                supported_media_types=service.get_supported_media_types()
            )
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取所有默认配置失败: {str(e)}"
        )


@router.get("/media-types", response_model=BaseResponse[List[str]])
async def get_supported_media_types(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取支持的媒体类型列表
    
    Args:
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        支持的媒体类型列表
    """
    try:
        service = DefaultSubscriptionConfigService(db)
        
        return BaseResponse(
            success=True,
            message="获取支持的媒体类型成功",
            data=service.get_supported_media_types()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取支持的媒体类型失败: {str(e)}"
        )


@router.post("/apply/{media_type}", response_model=BaseResponse[dict])
async def apply_default_config_to_subscription(
    media_type: str,
    subscription_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    将默认配置应用到订阅数据（供创建订阅时使用）
    
    Args:
        media_type: 媒体类型
        subscription_data: 订阅数据
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        应用默认配置后的订阅数据
    """
    try:
        service = DefaultSubscriptionConfigService(db)
        
        # 验证媒体类型
        if not service.validate_media_type(media_type):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的媒体类型: {media_type}"
            )
        
        # 应用默认配置
        updated_data = await service.apply_default_to_subscription_data(
            media_type, subscription_data
        )
        
        return BaseResponse(
            success=True,
            message="应用默认配置成功",
            data=updated_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"应用默认配置失败: {str(e)}"
        )
