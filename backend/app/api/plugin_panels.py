"""
插件面板 API
DEV-SDK-2 实现
PLUGIN-UX-3 扩展：Dashboard DSL

提供插件 UI 面板列表和数据获取接口
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from loguru import logger

from app.core.deps import DbSessionDep, CurrentUserDep, CurrentAdminUserDep
from app.schemas.response import BaseResponse
from app.models.plugin import Plugin, PluginStatus
from app.schemas.plugin import (
    PluginPanelPlacement,
    PluginPanelType,
    PluginPanelDefinition,
    PluginPanelWithPlugin,
    PluginPanelDataResponse,
    PluginDashboardSchema,
)
from app.services.plugin_registry import get_plugin_registry


router = APIRouter(prefix="/plugin_panels", tags=["plugin-panels"])


@router.get("", response_model=list[PluginPanelWithPlugin])
async def list_panels_by_placement(
    db: DbSessionDep,
    current_user: CurrentUserDep,
    placement: PluginPanelPlacement = Query(..., description="面板位置"),
):
    """
    按位置列出插件面板
    
    返回指定位置的所有已启用插件的面板定义
    """
    # 获取所有已启用的插件
    stmt = select(Plugin).where(Plugin.status == PluginStatus.ENABLED)
    result = await db.execute(stmt)
    plugins = result.scalars().all()
    
    panels: list[PluginPanelWithPlugin] = []
    
    for plugin in plugins:
        ui_panels = plugin.ui_panels or []
        
        for panel_data in ui_panels:
            if not isinstance(panel_data, dict):
                continue
            
            panel_placement = panel_data.get("placement")
            if panel_placement != placement.value:
                continue
            
            try:
                panel = PluginPanelDefinition(**panel_data)
                panels.append(PluginPanelWithPlugin(
                    plugin_id=plugin.name,
                    plugin_name=plugin.display_name,
                    panel=panel,
                ))
            except Exception as e:
                logger.warning(f"[plugin-panels] Invalid panel in {plugin.name}: {e}")
    
    # 按 order 排序
    panels.sort(key=lambda x: x.panel.order)
    
    return panels


@router.get("/{plugin_id}/{panel_id}/data", response_model=PluginPanelDataResponse)
async def get_panel_data(
    plugin_id: str,
    panel_id: str,
    db: DbSessionDep,
    current_user: CurrentUserDep,
):
    """
    获取面板数据
    
    调用插件注册的 PanelProvider 获取面板数据
    """
    # 验证插件存在且已启用
    stmt = select(Plugin).where(
        Plugin.name == plugin_id,
        Plugin.status == PluginStatus.ENABLED
    )
    result = await db.execute(stmt)
    plugin = result.scalar_one_or_none()
    
    if not plugin:
        raise HTTPException(status_code=404, detail=f"插件不存在或未启用: {plugin_id}")
    
    # 验证面板存在
    ui_panels = plugin.ui_panels or []
    panel_def = None
    for p in ui_panels:
        if isinstance(p, dict) and p.get("id") == panel_id:
            panel_def = p
            break
    
    if not panel_def:
        raise HTTPException(status_code=404, detail=f"面板不存在: {panel_id}")
    
    # 获取数据
    registry = get_plugin_registry()
    context = {
        "user_id": current_user.id,
        "username": current_user.username,
    }
    
    data = registry.get_panel_data(plugin_id, panel_id, context)
    
    if data is None:
        # 提供默认空数据
        logger.info(f"[plugin-panels] No data provider for {plugin_id}/{panel_id}, returning empty")
        data = {}
    
    panel_type = PluginPanelType(panel_def.get("type", "status_card"))
    
    return PluginPanelDataResponse(
        type=panel_type,
        meta=panel_def.get("config", {}),
        payload=data,
    )


# ============== PLUGIN-UX-3：Dashboard API ==============

@router.get(
    "/dashboard/{plugin_id}",
    response_model=BaseResponse[Optional[PluginDashboardSchema]],
    summary="获取插件 Dashboard",
)
async def get_plugin_dashboard(
    plugin_id: str,
    db: DbSessionDep,
    current_admin: CurrentAdminUserDep,
):
    """
    获取插件 Dashboard
    
    调用插件的 get_dashboard(sdk) 函数获取 Dashboard schema。
    如果插件未实现 get_dashboard，返回 None。
    """
    # 验证插件存在且已启用
    stmt = select(Plugin).where(
        Plugin.name == plugin_id,
        Plugin.status == PluginStatus.ENABLED
    )
    result = await db.execute(stmt)
    plugin = result.scalar_one_or_none()
    
    if not plugin:
        raise HTTPException(status_code=404, detail=f"插件不存在或未启用: {plugin_id}")
    
    # 获取 Dashboard
    registry = get_plugin_registry()
    dashboard = registry.get_dashboard(plugin_id)
    
    return BaseResponse(
        success=True,
        data=dashboard
    )
