"""
插件服务
DEV-SDK-1 实现
DEV-SDK-2 扩展：UI Panel 支持
PLUGIN-SDK-1 扩展：SDK + EventBus 集成

插件扫描、注册、状态管理
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.config import settings
from app.models.plugin import Plugin, PluginStatus
from app.schemas.plugin import (
    PluginScanResult,
    PluginPanelDefinition,
    PluginPanelPlacement,
    PluginPanelType,
)


# ============== PLUGIN-SDK-1：插件上下文构建 ==============

def build_plugin_context(plugin: Plugin) -> "PluginContext":
    """
    为插件构建运行时上下文
    
    Args:
        plugin: 插件数据库记录
        
    Returns:
        PluginContext 实例
    """
    from app.plugin_sdk.context import PluginContext
    
    # 计算插件数据目录
    data_root = Path(settings.STORAGE_PATH) / "plugin_data"
    plugin_data_dir = data_root / plugin.name.replace(".", "_")
    plugin_data_dir.mkdir(parents=True, exist_ok=True)
    
    return PluginContext(
        plugin_id=plugin.name,
        plugin_name=plugin.display_name,
        data_dir=plugin_data_dir,
        logger_name=f"vabhub.plugin.{plugin.name.split('.')[-1]}",
        app_version=settings.APP_VERSION,
        base_url=settings.APP_BASE_URL,
    )


def _get_plugins_dir() -> Path:
    """获取插件根目录的绝对路径"""
    plugins_dir = settings.PLUGINS_DIR
    
    if os.path.isabs(plugins_dir):
        return Path(plugins_dir)
    
    # 相对于项目根目录
    # backend/app/services/plugin_service.py -> backend/
    base_dir = Path(__file__).parent.parent.parent
    return base_dir / plugins_dir


def _parse_ui_panels(panels_raw: list, plugin_id: str) -> list[dict[str, Any]]:
    """
    解析 UI 面板声明
    
    Args:
        panels_raw: 原始面板配置列表
        plugin_id: 插件 ID
        
    Returns:
        验证后的面板配置列表（字典形式，用于 JSON 存储）
    """
    result = []
    
    for panel in panels_raw:
        if not isinstance(panel, dict):
            logger.warning(f"[plugin] {plugin_id}: invalid panel definition (not a dict)")
            continue
        
        panel_id = panel.get("id")
        if not panel_id:
            logger.warning(f"[plugin] {plugin_id}: panel missing 'id' field")
            continue
        
        title = panel.get("title", panel_id)
        
        # 验证 placement
        placement = panel.get("placement", "custom")
        try:
            PluginPanelPlacement(placement)
        except ValueError:
            logger.warning(f"[plugin] {plugin_id}/{panel_id}: invalid placement '{placement}'")
            placement = "custom"
        
        # 验证 type
        panel_type = panel.get("type", "status_card")
        try:
            PluginPanelType(panel_type)
        except ValueError:
            logger.warning(f"[plugin] {plugin_id}/{panel_id}: invalid type '{panel_type}'")
            panel_type = "status_card"
        
        result.append({
            "id": panel_id,
            "title": title,
            "description": panel.get("description"),
            "placement": placement,
            "type": panel_type,
            "endpoint": panel.get("endpoint"),
            "order": panel.get("order", 100),
            "enabled_by_default": panel.get("enabled_by_default", True),
            "config": panel.get("config", {}),
        })
    
    return result


async def scan_plugins_from_filesystem(session: AsyncSession) -> PluginScanResult:
    """
    扫描插件目录并同步到数据库
    
    遍历 PLUGINS_DIR 下的子目录，查找 plugin.json
    
    Returns:
        PluginScanResult: 扫描结果
    """
    plugins_dir = _get_plugins_dir()
    result = PluginScanResult()
    
    logger.info(f"[plugin] Scanning plugins from: {plugins_dir}")
    
    if not plugins_dir.exists():
        logger.warning(f"[plugin] Plugins directory does not exist: {plugins_dir}")
        # 创建目录
        try:
            plugins_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"[plugin] Created plugins directory: {plugins_dir}")
        except Exception as e:
            logger.error(f"[plugin] Failed to create plugins directory: {e}")
        return result
    
    # 遍历子目录
    for item in plugins_dir.iterdir():
        if not item.is_dir():
            continue
        
        manifest_path = item / "plugin.json"
        if not manifest_path.exists():
            logger.debug(f"[plugin] Skipping {item.name}: no plugin.json")
            continue
        
        result.scanned += 1
        
        try:
            # 解析 manifest
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            
            plugin_id = manifest.get("id")
            if not plugin_id:
                logger.warning(f"[plugin] {item.name}/plugin.json missing 'id' field")
                result.broken_plugins += 1
                continue
            
            display_name = manifest.get("display_name", plugin_id)
            version = manifest.get("version", "0.0.1")
            description = manifest.get("description")
            author = manifest.get("author")
            homepage = manifest.get("homepage")
            
            # 后端配置
            backend_config = manifest.get("backend", {})
            entry_module = backend_config.get("entry_module")
            if not entry_module:
                logger.warning(f"[plugin] {plugin_id}: missing backend.entry_module")
                result.broken_plugins += 1
                continue
            
            # 前端配置
            frontend_config = manifest.get("frontend", {})
            front_entry = frontend_config.get("entry_point")
            
            # 能力声明（扩展点）
            capabilities = manifest.get("capabilities", {})
            
            # PLUGIN-SDK-2：SDK 权限声明
            # 格式：["download.read", "download.write", "media.read", "cloud115.task"]
            sdk_permissions = manifest.get("sdk_permissions", [])
            if not isinstance(sdk_permissions, list):
                sdk_permissions = []
            
            # UI 面板声明
            ui_panels_raw = manifest.get("ui_panels", [])
            ui_panels = _parse_ui_panels(ui_panels_raw, plugin_id)
            
            # PLUGIN-UX-3：配置 Schema
            config_schema = manifest.get("config_schema")
            if config_schema is not None and not isinstance(config_schema, dict):
                logger.warning(f"[plugin] {plugin_id}: config_schema must be an object")
                config_schema = None
            
            # 查找或创建记录
            stmt = select(Plugin).where(Plugin.name == plugin_id)
            db_result = await session.execute(stmt)
            existing = db_result.scalar_one_or_none()
            
            if existing:
                # 更新
                existing.display_name = display_name
                existing.version = version
                existing.description = description
                existing.author = author
                existing.homepage = homepage
                existing.entry_module = entry_module
                existing.front_entry = front_entry
                existing.capabilities = capabilities
                existing.sdk_permissions = sdk_permissions  # PLUGIN-SDK-2
                existing.ui_panels = ui_panels
                existing.config_schema = config_schema  # PLUGIN-UX-3
                existing.plugin_dir = item.name
                
                # 如果之前是 BROKEN，且现在解析成功，改回 DISABLED
                if existing.status == PluginStatus.BROKEN:
                    existing.status = PluginStatus.DISABLED
                    existing.last_error = None
                
                result.updated_plugins += 1
                logger.info(f"[plugin] Updated: {plugin_id} v{version}")
            else:
                # 创建新记录
                new_plugin = Plugin(
                    name=plugin_id,
                    display_name=display_name,
                    version=version,
                    description=description,
                    author=author,
                    homepage=homepage,
                    entry_module=entry_module,
                    front_entry=front_entry,
                    capabilities=capabilities,
                    sdk_permissions=sdk_permissions,  # PLUGIN-SDK-2
                    ui_panels=ui_panels,
                    config_schema=config_schema,  # PLUGIN-UX-3
                    plugin_dir=item.name,
                    status=PluginStatus.DISABLED,  # 新插件默认禁用
                )
                session.add(new_plugin)
                result.new_plugins += 1
                logger.info(f"[plugin] New plugin: {plugin_id} v{version}")
            
        except json.JSONDecodeError as e:
            logger.error(f"[plugin] {item.name}/plugin.json parse error: {e}")
            result.broken_plugins += 1
        except Exception as e:
            logger.error(f"[plugin] Error processing {item.name}: {e}")
            result.broken_plugins += 1
    
    await session.commit()
    
    # 获取所有插件
    all_plugins = await list_plugins(session)
    result.plugins = all_plugins
    
    logger.info(
        f"[plugin] Scan complete: scanned={result.scanned}, "
        f"new={result.new_plugins}, updated={result.updated_plugins}, "
        f"broken={result.broken_plugins}"
    )
    
    return result


async def list_plugins(session: AsyncSession) -> list:
    """
    列出所有插件
    
    Returns:
        List[PluginRead]: 插件列表
    """
    from app.schemas.plugin import PluginRead
    
    stmt = select(Plugin).order_by(Plugin.name)
    result = await session.execute(stmt)
    plugins = result.scalars().all()
    
    # 转换为 PluginRead，处理 ui_panels
    plugin_reads = []
    for p in plugins:
        data = {
            "id": p.id,
            "name": p.name,
            "display_name": p.display_name,
            "version": p.version,
            "description": p.description,
            "author": p.author,
            "homepage": p.homepage,
            "entry_module": p.entry_module,
            "front_entry": p.front_entry,
            "capabilities": p.capabilities or {},
            "ui_panels": _convert_ui_panels(p.ui_panels or []),
            "status": p.status.value if p.status else "DISABLED",
            "plugin_dir": p.plugin_dir,
            "installed_at": p.installed_at,
            "updated_at": p.updated_at,
            "last_error": p.last_error,
        }
        plugin_reads.append(PluginRead(**data))
    
    return plugin_reads


def _convert_ui_panels(panels_data: list) -> list[PluginPanelDefinition]:
    """将 JSON 格式的面板数据转换为 PluginPanelDefinition 列表"""
    result = []
    for panel in panels_data:
        if not isinstance(panel, dict):
            continue
        try:
            result.append(PluginPanelDefinition(**panel))
        except Exception:
            # 跳过无效的面板定义
            continue
    return result


async def get_plugin_by_id(session: AsyncSession, plugin_id: int) -> Optional[Plugin]:
    """根据 ID 获取插件"""
    stmt = select(Plugin).where(Plugin.id == plugin_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_plugin_by_name(session: AsyncSession, name: str) -> Optional[Plugin]:
    """根据名称获取插件"""
    stmt = select(Plugin).where(Plugin.name == name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def set_plugin_status(
    session: AsyncSession,
    plugin_id: int,
    status: PluginStatus,
    error: Optional[str] = None
) -> Optional[Plugin]:
    """
    设置插件状态
    
    Args:
        session: 数据库会话
        plugin_id: 插件 ID
        status: 新状态
        error: 错误信息（如果是 BROKEN）
        
    Returns:
        更新后的插件对象，如果不存在则返回 None
    """
    plugin = await get_plugin_by_id(session, plugin_id)
    if not plugin:
        return None
    
    plugin.status = status
    if error:
        plugin.last_error = error
    elif status != PluginStatus.BROKEN:
        plugin.last_error = None
    
    await session.commit()
    await session.refresh(plugin)
    
    logger.info(f"[plugin] {plugin.name} status changed to {status.value}")
    return plugin


async def get_enabled_plugins(session: AsyncSession) -> list[Plugin]:
    """获取所有已启用的插件"""
    stmt = select(Plugin).where(Plugin.status == PluginStatus.ENABLED)
    result = await session.execute(stmt)
    return list(result.scalars().all())


def add_plugin_to_path(plugin: Plugin) -> Optional[str]:
    """
    将插件的 backend 目录添加到 sys.path
    
    Returns:
        添加的路径，如果失败则返回 None
    """
    if not plugin.plugin_dir:
        return None
    
    plugins_dir = _get_plugins_dir()
    backend_path = plugins_dir / plugin.plugin_dir / "backend"
    
    if backend_path.exists() and str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
        logger.debug(f"[plugin] Added to sys.path: {backend_path}")
        return str(backend_path)
    
    return None
