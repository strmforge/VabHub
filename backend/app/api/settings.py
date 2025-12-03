"""
系统设置相关API
使用统一响应模型
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Optional, Any
from pydantic import BaseModel
from loguru import logger

from app.core.database import get_db
from app.modules.settings.service import SettingsService
from app.core.schemas import (
    BaseResponse,
    NotFoundResponse,
    success_response,
    error_response
)

router = APIRouter()


class SettingUpdate(BaseModel):
    """更新设置请求"""
    value: Any
    category: Optional[str] = None
    description: Optional[str] = None


class SettingsUpdate(BaseModel):
    """批量更新设置请求"""
    settings: Dict[str, Any]
    category: Optional[str] = None


@router.get("/", response_model=BaseResponse)
async def get_all_settings(db = Depends(get_db)):
    """
    获取所有系统设置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {settings_dict},
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SettingsService(db)
        settings = await service.get_all_settings()
        return success_response(data=settings, message="获取成功")
    except Exception as e:
        logger.error(f"获取所有系统设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取所有系统设置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/category/{category}", response_model=BaseResponse)
async def get_settings_by_category(category: str, db = Depends(get_db)):
    """
    获取指定分类的设置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {settings_dict},
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SettingsService(db)
        settings = await service.get_settings_by_category(category)
        return success_response(data=settings, message="获取成功")
    except Exception as e:
        logger.error(f"获取分类设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取分类设置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{key}", response_model=BaseResponse)
async def get_setting(key: str, db = Depends(get_db)):
    """
    获取单个设置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {"key": "key", "value": "value"},
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SettingsService(db)
        value = await service.get_setting(key)
        if value is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"设置 '{key}' 不存在"
                ).model_dump()
            )
        return success_response(data={"key": key, "value": value}, message="获取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取设置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.put("/{key}", response_model=BaseResponse)
async def update_setting(
    key: str,
    update: SettingUpdate,
    db = Depends(get_db)
):
    """
    更新单个设置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": {"key": "key", "value": "value"},
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SettingsService(db)
        category = update.category or "basic"
        setting = await service.set_setting(
            key=key,
            value=update.value,
            category=category,
            description=update.description
        )
        return success_response(
            data={"key": setting.key, "value": update.value},
            message="更新成功"
        )
    except Exception as e:
        logger.error(f"更新设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新设置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/batch", response_model=BaseResponse)
async def update_settings_batch(
    update: SettingsUpdate,
    db = Depends(get_db)
):
    """
    批量更新设置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "批量更新成功",
        "data": {"updated_count": 10},
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SettingsService(db)
        category = update.category or "basic"
        count = await service.set_settings(update.settings, category)
        return success_response(
            data={"updated_count": count},
            message=f"批量更新成功，已更新 {count} 个设置"
        )
    except Exception as e:
        logger.error(f"批量更新设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"批量更新设置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/{key}", response_model=BaseResponse)
async def delete_setting(key: str, db = Depends(get_db)):
    """
    删除设置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "删除成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SettingsService(db)
        success = await service.delete_setting(key)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"设置 '{key}' 不存在"
                ).model_dump()
            )
        return success_response(message="删除成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除设置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/initialize", response_model=BaseResponse)
async def initialize_settings(db = Depends(get_db)):
    """
    初始化默认设置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "初始化成功，已初始化 X 个设置",
        "data": {"initialized_count": 10},
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SettingsService(db)
        count = await service.initialize_default_settings()
        return success_response(
            data={"initialized_count": count},
            message=f"初始化成功，已初始化 {count} 个设置"
        )
    except Exception as e:
        logger.error(f"初始化默认设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"初始化默认设置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/defaults/all", response_model=BaseResponse)
async def get_default_settings(db = Depends(get_db)):
    """
    获取默认设置（不包含已设置的值）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {defaults_dict},
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SettingsService(db)
        defaults = await service.get_default_settings()
        return success_response(data=defaults, message="获取成功")
    except Exception as e:
        logger.error(f"获取默认设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取默认设置时发生错误: {str(e)}"
            ).model_dump()
        )


# P4-1: 安全设置相关API端点
@router.get("/safety/global", response_model=BaseResponse)
async def get_safety_global_settings(db = Depends(get_db)):
    """
    获取全局安全策略设置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": GlobalSafetySettings,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.safety.settings import SafetySettingsService
        
        safety_service = SafetySettingsService(db)
        settings = await safety_service.get_global()
        return success_response(data=settings, message="获取成功")
    except Exception as e:
        logger.error(f"获取全局安全设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取全局安全设置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/safety/global", response_model=BaseResponse)
async def update_safety_global_settings(
    settings_data: dict,
    db = Depends(get_db)
):
    """
    更新全局安全策略设置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": GlobalSafetySettings,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.safety.settings import SafetySettingsService
        from app.modules.safety.models import GlobalSafetySettings
        
        safety_service = SafetySettingsService(db)
        
        # 验证并更新设置
        updated_settings = await safety_service.update_global(settings_data)
        return success_response(data=updated_settings, message="更新成功")
    except Exception as e:
        logger.error(f"更新全局安全设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                error_code="UPDATE_FAILED",
                error_message=f"更新全局安全设置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/safety/site/{site_key}", response_model=BaseResponse)
async def get_safety_site_settings(
    site_key: str,
    db = Depends(get_db)
):
    """
    获取站点安全策略设置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": SiteSafetySettings,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.safety.settings import SafetySettingsService
        
        safety_service = SafetySettingsService(db)
        settings = await safety_service.get_site(site_key)
        return success_response(data=settings, message="获取成功")
    except Exception as e:
        logger.error(f"获取站点安全设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取站点安全设置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/safety/site/{site_key}", response_model=BaseResponse)
async def update_safety_site_settings(
    site_key: str,
    settings_data: dict,
    db = Depends(get_db)
):
    """
    更新站点安全策略设置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": SiteSafetySettings,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.safety.settings import SafetySettingsService
        
        safety_service = SafetySettingsService(db)
        updated_settings = await safety_service.update_site(site_key, settings_data)
        return success_response(data=updated_settings, message="更新成功")
    except Exception as e:
        logger.error(f"更新站点安全设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                error_code="UPDATE_FAILED",
                error_message=f"更新站点安全设置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/safety/subscription/{subscription_id}", response_model=BaseResponse)
async def get_safety_subscription_settings(
    subscription_id: int,
    db = Depends(get_db)
):
    """
    获取订阅安全策略设置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": SubscriptionSafetySettings,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.safety.settings import SafetySettingsService
        
        safety_service = SafetySettingsService(db)
        settings = await safety_service.get_subscription(subscription_id)
        return success_response(data=settings, message="获取成功")
    except Exception as e:
        logger.error(f"获取订阅安全设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取订阅安全设置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/safety/subscription/{subscription_id}", response_model=BaseResponse)
async def update_safety_subscription_settings(
    subscription_id: int,
    settings_data: dict,
    db = Depends(get_db)
):
    """
    更新订阅安全策略设置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": SubscriptionSafetySettings,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.safety.settings import SafetySettingsService
        
        safety_service = SafetySettingsService(db)
        updated_settings = await safety_service.update_subscription(subscription_id, settings_data)
        return success_response(data=updated_settings, message="更新成功")
    except Exception as e:
        logger.error(f"更新订阅安全设置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                error_code="UPDATE_FAILED",
                error_message=f"更新订阅安全设置时发生错误: {str(e)}"
            ).model_dump()
        )

