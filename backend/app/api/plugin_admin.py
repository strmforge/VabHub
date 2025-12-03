"""
插件管理 API
DEV-SDK-1 实现

仅管理员可用
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_session
from app.core.auth import require_admin
from app.models.user import User
from app.models.plugin import PluginStatus
from app.schemas.plugin import (
    PluginRead,
    PluginUpdateStatus,
    PluginScanResult,
)
from app.services.plugin_service import (
    scan_plugins_from_filesystem,
    list_plugins,
    get_plugin_by_id,
    set_plugin_status,
)
from app.services.plugin_registry import get_plugin_registry


router = APIRouter(prefix="/dev/plugins", tags=["plugin-admin"])


@router.get("", response_model=list[PluginRead])
async def get_plugins(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """
    列出所有插件
    
    返回已安装的插件列表，包含状态和能力信息
    """
    plugins = await list_plugins(session)
    return plugins


@router.post("/scan", response_model=PluginScanResult)
async def scan_plugins(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """
    扫描插件目录
    
    扫描 PLUGINS_DIR 下的子目录，更新数据库中的插件记录
    """
    logger.info(f"[plugin-api] Scan triggered by user {current_user.id}")
    result = await scan_plugins_from_filesystem(session)
    return result


@router.put("/{plugin_id}/status", response_model=PluginRead)
async def update_plugin_status(
    plugin_id: int,
    body: PluginUpdateStatus,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """
    更新插件状态
    
    启用或禁用插件
    """
    plugin = await get_plugin_by_id(session, plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    
    # 映射状态
    new_status = PluginStatus.ENABLED if body.status == "ENABLED" else PluginStatus.DISABLED
    
    # 更新数据库
    updated = await set_plugin_status(session, plugin_id, new_status)
    if not updated:
        raise HTTPException(status_code=500, detail="状态更新失败")
    
    # 更新运行时注册表
    registry = get_plugin_registry()
    await registry.reload_plugin(session, updated)
    
    logger.info(f"[plugin-api] Plugin {plugin.name} status changed to {body.status}")
    
    return PluginRead.model_validate(updated)


@router.get("/{plugin_id}", response_model=PluginRead)
async def get_plugin(
    plugin_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """
    获取单个插件详情
    """
    plugin = await get_plugin_by_id(session, plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    
    return PluginRead.model_validate(plugin)
