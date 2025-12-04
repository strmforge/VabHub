"""
Plugin Hub API
PLUGIN-HUB-1 & PLUGIN-HUB-2 & PLUGIN-HUB-4 实现

远程插件索引查询 & 一键安装/更新/卸载接口 & Hub 源管理（仅管理员可用）
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.core.config import settings, PluginHubSourceConfig
from app.core.deps import DbSessionDep, CurrentAdminUserDep
from app.schemas.plugin_hub import (
    RemotePluginWithLocalStatus,
    PluginHubIndexResponse,
    PluginHubSourcePublic,
    PluginHubSourceUpdateRequest,
)
from app.services.plugin_hub_service import (
    get_plugin_hub_index,
    get_remote_plugin_detail,
    get_plugin_readme,
    get_multi_hub_index,
    load_runtime_hub_sources,
    save_runtime_hub_sources,
    hub_source_to_public,
    public_to_hub_source,
    normalize_hub_url,
    generate_hub_id_from_url,
)
from app.services.plugin_install_service import (
    install_plugin_from_hub,
    update_plugin_from_hub,
    uninstall_plugin,
)
from app.services.plugin_git_service import (
    PluginInstallError,
    PluginUpdateError,
    PluginUninstallError,
    RepoNotAllowedError,
)


router = APIRouter(prefix="/dev/plugin_hub", tags=["plugin-hub"])


@router.get("/config")
async def get_plugin_hub_config_api(
    current_admin: CurrentAdminUserDep,
):
    """
    获取 Plugin Hub 配置信息
    
    返回社区插件相关配置，供前端使用
    """
    from app.core.config import settings
    
    return {
        "community_visible": settings.PLUGIN_COMMUNITY_VISIBLE,
        "community_install_enabled": settings.PLUGIN_COMMUNITY_INSTALL_ENABLED,
        "official_orgs": settings.PLUGIN_OFFICIAL_ORGS,
    }


# ==================== Hub 源管理（PLUGIN-HUB-4） ====================

@router.get("/hubs", response_model=List[PluginHubSourcePublic])
async def get_plugin_hub_sources_api(
    db: DbSessionDep,
    current_admin: CurrentAdminUserDep,
):
    """
    获取插件 Hub 源列表
    
    返回当前配置的所有插件市场源
    """
    logger.info(f"[plugin-hub-api] Hub sources requested by user {current_admin.id}")
    
    try:
        sources = await load_runtime_hub_sources(db)
        return [hub_source_to_public(s) for s in sources]
    except Exception as e:
        logger.error(f"[plugin-hub-api] Failed to get hub sources: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取 Hub 源列表失败：{str(e)}"
        )


@router.put("/hubs", response_model=List[PluginHubSourcePublic])
async def update_plugin_hub_sources_api(
    payload: PluginHubSourceUpdateRequest,
    db: DbSessionDep,
    current_admin: CurrentAdminUserDep,
):
    """
    更新插件 Hub 源列表
    
    注意：更新后会清除所有缓存，需要重新获取索引
    """
    logger.info(f"[plugin-hub-api] Hub sources update by user {current_admin.id}, count={len(payload.sources)}")
    
    try:
        # 校验和标准化 URL
        sources: list[PluginHubSourceConfig] = []
        for src in payload.sources:
            # 校验 URL
            url = src.url.strip()
            if not url.startswith(("http://", "https://")):
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的 URL 格式：{url}"
                )
            
            # 转换为内部配置格式
            source = public_to_hub_source(src)
            sources.append(source)
        
        # 保存到 DB
        await save_runtime_hub_sources(db, sources)
        
        # 返回更新后的列表
        return [hub_source_to_public(s) for s in sources]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[plugin-hub-api] Failed to update hub sources: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"更新 Hub 源列表失败：{str(e)}"
        )


# ==================== 插件列表（PLUGIN-HUB-1 & 4） ====================

@router.get("", response_model=List[RemotePluginWithLocalStatus])
async def get_plugin_hub_index_api(
    db: DbSessionDep,
    current_admin: CurrentAdminUserDep,
    force_refresh: bool = Query(False, description="强制刷新（忽略缓存）"),
    channel: Optional[str] = Query(None, description="频道过滤：official / community"),
    include_community: bool = Query(True, description="是否包含社区插件"),
    hub_id: Optional[str] = Query(None, description="限定某个 Hub"),
    installed_only: bool = Query(False, description="仅返回已安装插件"),
    not_installed_only: bool = Query(False, description="仅返回未安装插件"),
):
    """
    获取 Plugin Hub 插件列表（多 Hub 聚合）
    
    返回远程插件索引，包含本地安装状态和更新标记
    
    - **force_refresh**: 是否强制刷新（忽略缓存）
    - **channel**: 频道过滤（official / community）
    - **include_community**: 是否包含社区插件
    - **hub_id**: 限定某个 Hub
    - **installed_only**: 仅返回已安装插件（用于"我的插件"视图）
    - **not_installed_only**: 仅返回未安装插件（用于"插件市场"视图）
    
    注意：installed_only 和 not_installed_only 不能同时为 True
    """
    logger.info(
        f"[plugin-hub-api] Index requested by user {current_admin.id}, "
        f"force_refresh={force_refresh}, channel={channel}, hub_id={hub_id}, "
        f"installed_only={installed_only}, not_installed_only={not_installed_only}"
    )
    
    # 参数冲突检查
    if installed_only and not_installed_only:
        raise HTTPException(
            status_code=400,
            detail="installed_only 和 not_installed_only 不能同时为 True"
        )
    
    try:
        # 使用多 Hub 聚合函数
        plugins = await get_multi_hub_index(
            db,
            force_refresh=force_refresh,
            hub_ids=[hub_id] if hub_id else None,
            channel=channel,
            include_community=include_community,
            installed_only=installed_only,
            not_installed_only=not_installed_only,
        )
        return plugins
    except Exception as e:
        logger.error(f"[plugin-hub-api] Failed to get index: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"无法获取 Plugin Hub 索引：{str(e)}"
        )


@router.get("/{plugin_id}", response_model=RemotePluginWithLocalStatus)
async def get_plugin_detail_api(
    plugin_id: str,
    db: DbSessionDep,
    current_admin: CurrentAdminUserDep,
):
    """
    获取单个远程插件详情
    
    - **plugin_id**: 插件 ID
    """
    plugin = await get_remote_plugin_detail(db, plugin_id)
    
    if not plugin:
        raise HTTPException(
            status_code=404,
            detail=f"Plugin Hub 中未找到插件：{plugin_id}"
        )
    
    return plugin


@router.get("/{plugin_id}/readme")
async def get_plugin_readme_api(
    plugin_id: str,
    db: DbSessionDep,
    current_admin: CurrentAdminUserDep,
):
    """
    获取远程插件的 README 内容
    
    - **plugin_id**: 插件 ID
    
    返回 Markdown 格式的 README 文本
    """
    plugin = await get_remote_plugin_detail(db, plugin_id)
    
    if not plugin:
        raise HTTPException(
            status_code=404,
            detail=f"Plugin Hub 中未找到插件：{plugin_id}"
        )
    
    readme = await get_plugin_readme(plugin)
    
    if not readme:
        return {"content": None, "message": "README 不可用"}
    
    return {"content": readme}


@router.get("/{plugin_id}/install_guide")
async def get_plugin_install_guide_api(
    plugin_id: str,
    db: DbSessionDep,
    current_admin: CurrentAdminUserDep,
):
    """
    获取插件安装指南
    
    返回手动安装的命令行指令
    """
    plugin = await get_remote_plugin_detail(db, plugin_id)
    
    if not plugin:
        raise HTTPException(
            status_code=404,
            detail=f"Plugin Hub 中未找到插件：{plugin_id}"
        )
    
    # 生成安装指南
    guide_lines = [
        f"# 插件安装指南：{plugin.name}",
        "",
        f"**插件 ID**: `{plugin.id}`",
        f"**版本**: `{plugin.version or '未知'}`",
    ]
    
    if plugin.repo:
        guide_lines.extend([
            f"**仓库地址**: {plugin.repo}",
            "",
            "## 手动安装步骤",
            "",
            "```bash",
            "# 1. 进入 VabHub 根目录",
            "cd /path/to/vabhub",
            "",
            "# 2. 确保 plugins 目录存在",
            "mkdir -p plugins",
            "",
            f"# 3. 克隆插件仓库",
            f"git clone {plugin.repo} plugins/{plugin.id}",
            "",
            "# 4. 重启 VabHub 或在 Web UI 执行「重新扫描插件」",
            "```",
        ])
    elif plugin.download_url:
        guide_lines.extend([
            f"**下载地址**: {plugin.download_url}",
            "",
            "## 手动安装步骤",
            "",
            "1. 下载插件 ZIP 包",
            "2. 解压到 `plugins/` 目录",
            "3. 重启 VabHub 或在 Web UI 执行「重新扫描插件」",
        ])
    else:
        guide_lines.extend([
            "",
            "**注意**: 该插件未提供仓库地址或下载链接，请联系插件作者获取安装方式。",
        ])
    
    # 如果已安装且有更新
    if plugin.installed and plugin.has_update:
        guide_lines.extend([
            "",
            "## 更新说明",
            "",
            f"- 当前本地版本: `{plugin.local_version}`",
            f"- 远程最新版本: `{plugin.version}`",
            "",
            "更新步骤:",
            "```bash",
            f"cd plugins/{plugin.id}",
            "git pull origin main",
            "```",
        ])
    
    return {
        "plugin_id": plugin.id,
        "plugin_name": plugin.name,
        "installed": plugin.installed,
        "has_update": plugin.has_update,
        "guide": "\n".join(guide_lines),
    }


# ==================== PLUGIN-HUB-2 & 3：一键操作 ====================

async def check_community_install_allowed(
    db: DbSessionDep,
    plugin_id: str,
) -> None:
    """
    检查社区插件是否允许一键安装
    
    Raises:
        HTTPException: 如果社区插件被禁止一键安装
    """
    from app.core.config import settings
    
    # 如果允许社区插件安装，直接返回
    if settings.PLUGIN_COMMUNITY_INSTALL_ENABLED:
        return
    
    # 获取插件详情检查 channel
    plugin = await get_remote_plugin_detail(db, plugin_id)
    if not plugin:
        return  # 插件不存在，让后续逻辑处理
    
    # 应用 channel 标准化
    from app.services.plugin_hub_service import normalize_channel
    channel = normalize_channel(plugin)
    
    if channel == "community":
        raise HTTPException(
            status_code=403,
            detail="社区插件已被禁用一键安装，请使用安装指南手动部署"
        )


@router.post("/{plugin_id}/install", response_model=RemotePluginWithLocalStatus)
async def install_plugin_api(
    plugin_id: str,
    db: DbSessionDep,
    current_admin: CurrentAdminUserDep,
):
    """
    从 Plugin Hub 一键安装插件
    
    - **plugin_id**: 插件 ID
    
    需要管理员权限。插件会被克隆到 plugins 目录。
    
    注意：如果服务器配置禁用了社区插件一键安装，社区插件将返回 403。
    """
    logger.info(f"[plugin-hub-api] Install requested for {plugin_id} by user {current_admin.id}")
    
    # 检查社区插件安装权限（PLUGIN-HUB-3）
    await check_community_install_allowed(db, plugin_id)
    
    try:
        result = await install_plugin_from_hub(db, plugin_id)
        return result
    except RepoNotAllowedError as e:
        logger.warning(f"[plugin-hub-api] Repo not allowed: {e}")
        raise HTTPException(
            status_code=403,
            detail=f"仓库地址不在白名单中：{str(e)}"
        )
    except PluginInstallError as e:
        logger.error(f"[plugin-hub-api] Install failed: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"安装失败：{str(e)}"
        )
    except Exception as e:
        logger.error(f"[plugin-hub-api] Unexpected error during install: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"安装过程中发生错误：{str(e)}"
        )


@router.post("/{plugin_id}/update", response_model=RemotePluginWithLocalStatus)
async def update_plugin_api(
    plugin_id: str,
    db: DbSessionDep,
    current_admin: CurrentAdminUserDep,
):
    """
    从 Plugin Hub 更新已安装的插件
    
    - **plugin_id**: 插件 ID
    
    需要管理员权限。会执行 git pull 拉取最新代码。
    
    注意：如果服务器配置禁用了社区插件一键更新，社区插件将返回 403。
    """
    logger.info(f"[plugin-hub-api] Update requested for {plugin_id} by user {current_admin.id}")
    
    # 检查社区插件更新权限（PLUGIN-HUB-3）
    await check_community_install_allowed(db, plugin_id)
    
    try:
        result = await update_plugin_from_hub(db, plugin_id)
        return result
    except PluginUpdateError as e:
        logger.error(f"[plugin-hub-api] Update failed: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"更新失败：{str(e)}"
        )
    except Exception as e:
        logger.error(f"[plugin-hub-api] Unexpected error during update: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"更新过程中发生错误：{str(e)}"
        )


@router.post("/{plugin_id}/uninstall")
async def uninstall_plugin_api(
    plugin_id: str,
    db: DbSessionDep,
    current_admin: CurrentAdminUserDep,
):
    """
    卸载插件
    
    - **plugin_id**: 插件 ID
    
    需要管理员权限。会删除插件目录和数据库记录。
    
    ⚠️ 警告：此操作不可逆，插件目录将被完全删除。
    """
    logger.info(f"[plugin-hub-api] Uninstall requested for {plugin_id} by user {current_admin.id}")
    
    try:
        success = await uninstall_plugin(db, plugin_id)
        return {
            "success": success,
            "plugin_id": plugin_id,
            "message": "插件已卸载" if success else "卸载失败"
        }
    except PluginUninstallError as e:
        logger.error(f"[plugin-hub-api] Uninstall failed: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"卸载失败：{str(e)}"
        )
    except Exception as e:
        logger.error(f"[plugin-hub-api] Unexpected error during uninstall: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"卸载过程中发生错误：{str(e)}"
        )
