"""
版本信息 API
RELEASE-1 R0-1 实现
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.core.version import get_version_info, APP_NAME, APP_VERSION
from app.core.config import settings

router = APIRouter(prefix="/version", tags=["版本"])


class VersionResponse(BaseModel):
    """版本信息响应"""
    name: str
    version: str
    build_commit: Optional[str] = None
    build_date: Optional[str] = None
    demo_mode: bool = False


@router.get("", response_model=VersionResponse)
async def get_version():
    """
    获取应用版本信息
    
    返回应用名称、版本号、构建信息等
    """
    info = get_version_info()
    
    # 添加 demo_mode 状态
    demo_mode = getattr(settings, 'APP_DEMO_MODE', False)
    
    return VersionResponse(
        name=info["name"],
        version=info["version"],
        build_commit=info.get("build_commit"),
        build_date=info.get("build_date"),
        demo_mode=demo_mode,
    )


@router.get("/info", response_model=VersionResponse)
async def get_app_info():
    """
    获取应用信息（别名）
    
    与 /version 相同，提供更直观的路径
    """
    return await get_version()
