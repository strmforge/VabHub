"""
VabHub 系统管理 API
DEPLOY-UPGRADE-1 实现

提供版本查询和升级功能的管理员 API。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.core.deps import CurrentAdminUserDep
from app.services.upgrade_service import (
    get_upgrade_service,
    VersionInfo,
    UpgradeResult
)
from loguru import logger


router = APIRouter(prefix="/admin/system", tags=["admin-system"])


# ============== 响应模型 ==============

class VersionResponse(BaseModel):
    """版本信息响应"""
    success: bool
    data: VersionInfo


class UpgradeRequest(BaseModel):
    """升级请求"""
    mode: str = "check_only"  # "check_only" | "apply"


class UpgradeResponse(BaseModel):
    """升级响应"""
    success: bool
    data: UpgradeResult


class DockerStatusResponse(BaseModel):
    """Docker 状态响应"""
    success: bool
    docker_available: bool
    message: str


# ============== API 端点 ==============

@router.get("/version", response_model=VersionResponse)
async def get_version(
    admin_user: CurrentAdminUserDep
):
    """
    获取系统版本信息
    
    返回当前运行版本、构建信息和更新状态。
    """
    service = get_upgrade_service()
    try:
        info = await service.get_version_info()
        return VersionResponse(success=True, data=info)
    except Exception as e:
        logger.error(f"获取版本信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取版本信息失败: {str(e)}"
        )


@router.post("/upgrade", response_model=UpgradeResponse)
async def upgrade_system(
    request: UpgradeRequest,
    admin_user: CurrentAdminUserDep
):
    """
    系统升级
    
    - mode="check_only": 仅检查是否有新版本
    - mode="apply": 执行升级（拉取新镜像并重启容器）
    """
    service = get_upgrade_service()
    
    try:
        if request.mode == "check_only":
            result = await service.check_update()
        elif request.mode == "apply":
            result = await service.apply_upgrade()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的升级模式: {request.mode}"
            )
        
        return UpgradeResponse(success=result.success, data=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"升级操作失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"升级操作失败: {str(e)}"
        )


@router.get("/docker-status", response_model=DockerStatusResponse)
async def get_docker_status(
    admin_user: CurrentAdminUserDep
):
    """
    获取 Docker 状态
    
    检查 docker.sock 是否可用，用于判断是否支持 UI 升级功能。
    """
    service = get_upgrade_service()
    available = service.is_docker_available()
    
    if available:
        message = "Docker Socket 可用，支持 UI 升级功能"
    else:
        message = "Docker Socket 不可用，请使用 docker compose pull 手动升级"
    
    return DockerStatusResponse(
        success=True,
        docker_available=available,
        message=message
    )
