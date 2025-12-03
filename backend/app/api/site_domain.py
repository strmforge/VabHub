"""
站点域名管理API
支持用户自行配置和切换站点域名，无需等待版本更新
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel, HttpUrl
from loguru import logger

from app.core.database import get_db
from app.modules.site_domain.service import SiteDomainService
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter(prefix="/sites/{site_id}/domains", tags=["站点域名管理"])


class DomainConfigUpdate(BaseModel):
    """域名配置更新请求"""
    active_domains: Optional[List[str]] = None
    deprecated_domains: Optional[List[str]] = None
    current_domain: Optional[str] = None
    auto_detect: Optional[bool] = None


class DomainAdd(BaseModel):
    """添加域名请求"""
    domain: str
    is_active: bool = True


@router.get("/", response_model=BaseResponse)
async def get_domain_config(
    site_id: int,
    db = Depends(get_db)
):
    """
    获取站点域名配置
    """
    try:
        service = SiteDomainService(db)
        config_info = await service.get_domain_info(site_id)
        return success_response(data=config_info, message="获取成功")
    except Exception as e:
        logger.error(f"获取站点域名配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取站点域名配置失败: {str(e)}"
            ).model_dump()
        )


@router.put("/", response_model=BaseResponse)
async def update_domain_config(
    site_id: int,
    config: DomainConfigUpdate,
    db = Depends(get_db)
):
    """
    更新站点域名配置
    """
    try:
        service = SiteDomainService(db)
        updated_config = await service.update_domain_config(
            site_id=site_id,
            active_domains=config.active_domains,
            deprecated_domains=config.deprecated_domains,
            current_domain=config.current_domain,
            auto_detect=config.auto_detect
        )
        config_info = await service.get_domain_info(site_id)
        return success_response(data=config_info, message="更新成功")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                error_code="INVALID_INPUT",
                error_message=str(e)
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"更新站点域名配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新站点域名配置失败: {str(e)}"
            ).model_dump()
        )


@router.post("/add", response_model=BaseResponse)
async def add_domain(
    site_id: int,
    request: DomainAdd,
    db = Depends(get_db)
):
    """
    添加域名
    """
    try:
        service = SiteDomainService(db)
        config = await service.add_domain(
            site_id=site_id,
            domain=request.domain,
            is_active=request.is_active
        )
        config_info = await service.get_domain_info(site_id)
        return success_response(data=config_info, message="添加成功")
    except Exception as e:
        logger.error(f"添加域名失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"添加域名失败: {str(e)}"
            ).model_dump()
        )


@router.delete("/remove", response_model=BaseResponse)
async def remove_domain(
    site_id: int,
    domain: str = Query(..., description="要移除的域名"),
    db = Depends(get_db)
):
    """
    移除域名（从活跃移到废弃）
    """
    try:
        service = SiteDomainService(db)
        config = await service.remove_domain(site_id=site_id, domain=domain)
        config_info = await service.get_domain_info(site_id)
        return success_response(data=config_info, message="移除成功")
    except Exception as e:
        logger.error(f"移除域名失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"移除域名失败: {str(e)}"
            ).model_dump()
        )


@router.post("/switch", response_model=BaseResponse)
async def switch_domain(
    site_id: int,
    domain: str = Query(..., description="要切换到的域名"),
    reason: str = Query("手动切换", description="切换原因"),
    db = Depends(get_db)
):
    """
    切换到指定域名
    """
    try:
        service = SiteDomainService(db)
        config = await service.switch_domain(
            site_id=site_id,
            domain=domain,
            reason=reason
        )
        config_info = await service.get_domain_info(site_id)
        return success_response(data=config_info, message="切换成功")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                error_code="INVALID_INPUT",
                error_message=str(e)
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"切换域名失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"切换域名失败: {str(e)}"
            ).model_dump()
        )


@router.post("/detect", response_model=BaseResponse)
async def detect_and_switch_domain(
    site_id: int,
    db = Depends(get_db)
):
    """
    自动检测并切换域名
    尝试访问所有活跃域名，选择第一个可访问的域名
    """
    try:
        service = SiteDomainService(db)
        result = await service.detect_and_switch_domain(site_id)
        return success_response(data=result, message="检测完成")
    except Exception as e:
        logger.error(f"自动检测域名失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"自动检测域名失败: {str(e)}"
            ).model_dump()
        )


@router.post("/check-all", response_model=BaseResponse)
async def check_all_domains(
    site_id: int,
    db = Depends(get_db)
):
    """
    检查所有域名
    
    返回统一响应格式：
    {
        "success": true,
        "message": "检查完成",
        "data": {
            "domains": [
                {"domain": "...", "accessible": true, "response_time": 100},
                ...
            ]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SiteDomainService(db)
        result = await service.check_all_domains(site_id)
        return success_response(data=result, message="检查完成")
    except Exception as e:
        logger.error(f"检查所有域名失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"检查所有域名失败: {str(e)}"
            ).model_dump()
        )


@router.post("/set-active", response_model=BaseResponse)
async def set_active_domain(
    site_id: int,
    domain: str = Query(..., description="要设置为活动状态的域名"),
    db = Depends(get_db)
):
    """
    设置活动域名
    
    返回统一响应格式：
    {
        "success": true,
        "message": "设置成功",
        "data": {...},
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SiteDomainService(db)
        # 使用 switch_domain 方法，它实际上就是设置活动域名
        config = await service.switch_domain(
            site_id=site_id,
            domain=domain,
            reason="手动设置活动域名"
        )
        config_info = await service.get_domain_info(site_id)
        return success_response(data=config_info, message="设置成功")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                error_code="INVALID_INPUT",
                error_message=str(e)
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"设置活动域名失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"设置活动域名失败: {str(e)}"
            ).model_dump()
        )

