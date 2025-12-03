"""
Plugin Install Service
PLUGIN-HUB-2 实现
PLUGIN-REMOTE-1 扩展：远程插件支持

插件安装、更新、卸载业务逻辑
"""

from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.plugin import Plugin, PluginStatus
from app.schemas.plugin_hub import RemotePluginWithLocalStatus
from app.services.plugin_git_service import (
    PluginInstallError,
    PluginUpdateError,
    PluginUninstallError,
    get_plugin_dir,
    git_clone,
    git_pull,
    git_current_rev,
    git_remote_url,
    remove_plugin_dir,
)
from app.services.plugin_hub_service import (
    get_plugin_hub_index,
    get_remote_plugin_detail,
)


async def find_remote_plugin_by_id(
    session: AsyncSession,
    plugin_id: str,
) -> Optional[RemotePluginWithLocalStatus]:
    """
    从 Plugin Hub 索引中查找插件
    
    Args:
        session: 数据库会话
        plugin_id: 插件 ID
        
    Returns:
        RemotePluginWithLocalStatus 或 None
    """
    return await get_remote_plugin_detail(session, plugin_id)


async def find_local_plugin_by_name(
    session: AsyncSession,
    name: str,
) -> Optional[Plugin]:
    """
    查找本地插件
    
    Args:
        session: 数据库会话
        name: 插件名称（对应 plugin_id）
        
    Returns:
        Plugin 或 None
    """
    stmt = select(Plugin).where(Plugin.name == name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def rescan_single_plugin(
    session: AsyncSession,
    plugin_id: str,
) -> Optional[Plugin]:
    """
    重新扫描单个插件目录
    
    这个函数会读取 plugin.json 并更新数据库记录
    
    Args:
        session: 数据库会话
        plugin_id: 插件 ID
        
    Returns:
        更新后的 Plugin 或 None
    """
    import json
    from pathlib import Path
    from app.services.plugin_service import _parse_ui_panels
    
    plugin_dir = get_plugin_dir(plugin_id)
    
    if not plugin_dir.exists():
        return None
    
    # 查找 plugin.json
    plugin_json_path = plugin_dir / "plugin.json"
    if not plugin_json_path.exists():
        logger.warning(f"[plugin-install] No plugin.json found in {plugin_dir}")
        return None
    
    try:
        with open(plugin_json_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"[plugin-install] Failed to read plugin.json: {e}")
        return None
    
    # 解析配置
    name = config.get("id") or config.get("name")
    if not name:
        logger.error(f"[plugin-install] Plugin config missing 'id' or 'name'")
        return None
    
    display_name = config.get("display_name") or config.get("name") or name
    version = config.get("version", "0.0.1")
    description = config.get("description")
    author = config.get("author")
    homepage = config.get("homepage")
    entry_module = config.get("entry_module", f"{name.replace('-', '_')}.main")
    front_entry = config.get("front_entry")
    capabilities = config.get("capabilities", {})
    
    # PLUGIN-REMOTE-1：解析插件类型和远程配置
    plugin_type_raw = config.get("plugin_type", "local")
    from app.models.plugin import PluginType
    plugin_type = PluginType.LOCAL if plugin_type_raw.lower() != "remote" else PluginType.REMOTE
    
    remote_config = config.get("remote") if plugin_type == PluginType.REMOTE else None
    subscribed_events = config.get("events", []) if plugin_type == PluginType.REMOTE else []
    
    # 解析 UI Panels
    ui_panels_raw = config.get("ui_panels", [])
    ui_panels = _parse_ui_panels(ui_panels_raw, name)
    
    # 查找或创建 Plugin 记录
    existing = await find_local_plugin_by_name(session, name)
    
    if existing:
        # 更新现有记录
        existing.display_name = display_name
        existing.version = version
        existing.description = description
        existing.author = author
        existing.homepage = homepage
        existing.entry_module = entry_module
        existing.front_entry = front_entry
        existing.capabilities = capabilities
        existing.ui_panels = ui_panels
        
        # PLUGIN-REMOTE-1：更新远程插件配置
        existing.plugin_type = plugin_type
        existing.remote_config = remote_config
        existing.subscribed_events = subscribed_events
        
        existing.plugin_dir = str(plugin_dir.relative_to(plugin_dir.parent.parent))
        existing.status = PluginStatus.INSTALLED
        existing.last_error = None
        
        await session.commit()
        await session.refresh(existing)
        return existing
    else:
        # 创建新记录
        plugin = Plugin(
            name=name,
            display_name=display_name,
            version=version,
            description=description,
            author=author,
            homepage=homepage,
            entry_module=entry_module,
            front_entry=front_entry,
            capabilities=capabilities,
            ui_panels=ui_panels,
            
            # PLUGIN-REMOTE-1：保存远程插件配置
            plugin_type=plugin_type,
            remote_config=remote_config,
            subscribed_events=subscribed_events,
            
            plugin_dir=str(plugin_dir.relative_to(plugin_dir.parent.parent)),
            status=PluginStatus.INSTALLED,
        )
        session.add(plugin)
        await session.commit()
        await session.refresh(plugin)
        return plugin


async def install_plugin_from_hub(
    session: AsyncSession,
    plugin_id: str,
) -> RemotePluginWithLocalStatus:
    """
    从 Plugin Hub 一键安装插件
    
    Args:
        session: 数据库会话
        plugin_id: 插件 ID
        
    Returns:
        更新后的 RemotePluginWithLocalStatus
        
    Raises:
        PluginInstallError: 安装失败
    """
    logger.info(f"[plugin-install] Installing plugin from hub: {plugin_id}")
    
    # 1. 从 Hub 索引中找到插件
    remote_plugin = await find_remote_plugin_by_id(session, plugin_id)
    if not remote_plugin:
        raise PluginInstallError(f"Plugin not found in Plugin Hub: {plugin_id}")
    
    # 2. 检查是否已安装
    if remote_plugin.installed:
        raise PluginInstallError(f"Plugin is already installed: {plugin_id}")
    
    # 3. 检查 repo_url
    repo_url = remote_plugin.repo
    if not repo_url:
        raise PluginInstallError(f"Plugin has no repository URL: {plugin_id}")
    
    # 4. 计算插件目录
    plugin_dir = get_plugin_dir(plugin_id)
    
    # 5. 克隆仓库
    await git_clone(repo_url, plugin_dir)
    
    # 6. 获取 installed_ref
    installed_ref = await git_current_rev(plugin_dir)
    
    # 7. 扫描并注册插件
    local_plugin = await rescan_single_plugin(session, plugin_id)
    if not local_plugin:
        # 清理失败的安装
        remove_plugin_dir(plugin_dir)
        raise PluginInstallError(f"Failed to scan installed plugin: {plugin_id}")
    
    # 8. 更新来源信息
    local_plugin.source = "plugin_hub"
    local_plugin.hub_id = plugin_id
    local_plugin.repo_url = repo_url
    local_plugin.installed_ref = installed_ref
    local_plugin.auto_update_enabled = True
    
    await session.commit()
    
    logger.info(f"[plugin-install] Successfully installed {plugin_id} (ref: {installed_ref})")
    
    # 9. 返回更新后的状态
    return await find_remote_plugin_by_id(session, plugin_id)


async def update_plugin_from_hub(
    session: AsyncSession,
    plugin_id: str,
) -> RemotePluginWithLocalStatus:
    """
    从 Plugin Hub 更新已安装的插件
    
    Args:
        session: 数据库会话
        plugin_id: 插件 ID
        
    Returns:
        更新后的 RemotePluginWithLocalStatus
        
    Raises:
        PluginUpdateError: 更新失败
    """
    logger.info(f"[plugin-install] Updating plugin from hub: {plugin_id}")
    
    # 1. 从 Hub 索引中找到插件
    remote_plugin = await find_remote_plugin_by_id(session, plugin_id)
    if not remote_plugin:
        raise PluginUpdateError(f"Plugin not found in Plugin Hub: {plugin_id}")
    
    # 2. 检查是否已安装
    if not remote_plugin.installed:
        raise PluginUpdateError(f"Plugin is not installed: {plugin_id}")
    
    # 3. 查找本地插件
    local_plugin = await find_local_plugin_by_name(session, plugin_id)
    if not local_plugin:
        raise PluginUpdateError(f"Local plugin record not found: {plugin_id}")
    
    # 4. 检查来源
    source = getattr(local_plugin, 'source', 'local')
    if source not in ("plugin_hub", "manual_hub"):
        raise PluginUpdateError(
            f"Cannot update plugin with source '{source}'. "
            "Only plugins installed from Plugin Hub can be updated."
        )
    
    # 5. 检查自动更新是否启用
    auto_update = getattr(local_plugin, 'auto_update_enabled', True)
    if not auto_update:
        raise PluginUpdateError(f"Auto-update is disabled for plugin: {plugin_id}")
    
    # 6. 计算插件目录
    plugin_dir = get_plugin_dir(plugin_id)
    
    if not plugin_dir.exists():
        raise PluginUpdateError(f"Plugin directory not found: {plugin_dir}")
    
    # 7. 拉取更新
    await git_pull(plugin_dir)
    
    # 8. 获取新的 installed_ref
    installed_ref = await git_current_rev(plugin_dir)
    
    # 9. 重新扫描插件
    updated_plugin = await rescan_single_plugin(session, plugin_id)
    if not updated_plugin:
        raise PluginUpdateError(f"Failed to rescan plugin after update: {plugin_id}")
    
    # 10. 更新 installed_ref
    updated_plugin.installed_ref = installed_ref
    await session.commit()
    
    logger.info(f"[plugin-install] Successfully updated {plugin_id} (ref: {installed_ref})")
    
    # 11. 返回更新后的状态
    return await find_remote_plugin_by_id(session, plugin_id)


async def uninstall_plugin(
    session: AsyncSession,
    plugin_id: str,
) -> bool:
    """
    卸载插件
    
    Args:
        session: 数据库会话
        plugin_id: 插件 ID
        
    Returns:
        是否成功卸载
        
    Raises:
        PluginUninstallError: 卸载失败
    """
    logger.info(f"[plugin-install] Uninstalling plugin: {plugin_id}")
    
    # 1. 查找本地插件
    local_plugin = await find_local_plugin_by_name(session, plugin_id)
    
    # 2. 计算插件目录
    plugin_dir = get_plugin_dir(plugin_id)
    
    # 3. 删除目录
    if plugin_dir.exists():
        remove_plugin_dir(plugin_dir)
    else:
        logger.warning(f"[plugin-install] Plugin directory not found: {plugin_dir}")
    
    # 4. 删除数据库记录
    if local_plugin:
        await session.delete(local_plugin)
        await session.commit()
        logger.info(f"[plugin-install] Deleted plugin record: {plugin_id}")
    else:
        logger.warning(f"[plugin-install] Plugin record not found in database: {plugin_id}")
    
    logger.info(f"[plugin-install] Successfully uninstalled {plugin_id}")
    
    return True
