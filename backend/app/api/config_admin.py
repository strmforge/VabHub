"""
配置管理 API
LAUNCH-1 L1-1 实现

提供配置 Schema 查询、校验和当前配置查看
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.response import BaseResponse, success_response
from app.core.config_schema import (
    get_config_schema,
    validate_config,
    get_effective_config,
    ConfigValidationResult
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/config", tags=["配置管理"])


def require_admin(user: User) -> User:
    """要求管理员权限"""
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return user


@router.get("/schema", response_model=BaseResponse, summary="获取配置 Schema")
async def get_schema(
    current_user: User = Depends(get_current_user),
):
    """
    获取配置 Schema
    
    返回支持的配置键、类型、默认值说明，用于前端渲染表单
    """
    require_admin(current_user)
    
    try:
        schema = get_config_schema()
        return success_response(
            data=schema.model_dump(),
            message="获取配置 Schema 成功"
        )
    except Exception as e:
        logger.error(f"获取配置 Schema 失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置 Schema 失败: {str(e)}"
        )


@router.post("/validate", response_model=BaseResponse, summary="校验配置")
async def validate_config_api(
    config: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    """
    校验配置
    
    接受 JSON 配置，返回是否通过校验及错误列表
    """
    require_admin(current_user)
    
    try:
        result = validate_config(config)
        return success_response(
            data=result.model_dump(),
            message="校验完成" if result.valid else "配置存在错误"
        )
    except Exception as e:
        logger.error(f"校验配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"校验配置失败: {str(e)}"
        )


@router.get("/effective", response_model=BaseResponse, summary="获取当前生效配置")
async def get_effective(
    current_user: User = Depends(get_current_user),
):
    """
    获取当前生效配置
    
    敏感字段值用 *** 替代
    """
    require_admin(current_user)
    
    try:
        config = get_effective_config(mask_sensitive=True)
        return success_response(
            data=config,
            message="获取当前配置成功"
        )
    except Exception as e:
        logger.error(f"获取当前配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取当前配置失败: {str(e)}"
        )
