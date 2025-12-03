"""
规则集管理API
用于管理订阅规则集
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from pydantic import BaseModel
from loguru import logger

from app.core.database import get_db
from app.modules.settings.service import SettingsService
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter(prefix="/ruleset", tags=["规则集"])


class RulesetConfig(BaseModel):
    """规则集配置"""
    rules: Dict[str, Any]  # 规则配置（JSON格式）


@router.get("/", response_model=BaseResponse)
async def get_ruleset(
    db: AsyncSession = Depends(get_db)
):
    """
    获取规则集配置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "rules": {...}
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        settings_service = SettingsService(db)
        
        # 从设置中获取规则集配置
        ruleset_json = await settings_service.get_setting("ruleset_config", category="subscription")
        
        if ruleset_json:
            import json
            try:
                rules = json.loads(ruleset_json) if isinstance(ruleset_json, str) else ruleset_json
            except:
                rules = {}
        else:
            # 默认规则集配置
            rules = {
                "default": {
                    "quality": "1080p",
                    "resolution": "1920x1080",
                    "min_seeders": 5,
                    "sites": [],
                    "include": [],
                    "exclude": []
                }
            }
        
        return success_response(
            data={"rules": rules},
            message="获取规则集配置成功"
        )
    except Exception as e:
        logger.error(f"获取规则集配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取规则集配置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.put("/", response_model=BaseResponse)
async def update_ruleset(
    config: RulesetConfig,
    db: AsyncSession = Depends(get_db)
):
    """
    更新规则集配置
    
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
        
        # 将规则集配置保存到设置中
        import json
        ruleset_json = json.dumps(config.rules, ensure_ascii=False)
        await settings_service.set_setting("ruleset_config", ruleset_json, category="subscription")
        
        return success_response(message="更新规则集配置成功")
    except Exception as e:
        logger.error(f"更新规则集配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新规则集配置时发生错误: {str(e)}"
            ).model_dump()
        )

