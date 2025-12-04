"""
Plugin Hub Service
PLUGIN-HUB-1 & PLUGIN-HUB-3 & PLUGIN-HUB-4 实现
PLUGIN-SAFETY-1 扩展：轻量级自动更新检测

从远程 Plugin Hub 获取插件索引，与本地插件对比状态
支持多 Hub 源聚合
"""

import json
import re
from datetime import datetime, timedelta
from typing import Optional, Any
from urllib.parse import urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.config import settings, PluginHubSourceConfig
from app.models.plugin import Plugin
from app.models.system_state import SystemState
from app.schemas.plugin_hub import (
    RemotePluginInfo,
    RemotePluginWithLocalStatus,
    PluginSupports,
    PluginHubIndex,
    PluginHubIndexResponse,
    PluginHubSourcePublic,
)


# 缓存 key
CACHE_KEY_INDEX = "plugin_hub_index"
CACHE_KEY_UPDATED_AT = "plugin_hub_updated_at"

# 多 Hub 相关 key（PLUGIN-HUB-4）
CACHE_KEY_HUB_SOURCES = "plugin_hub_sources"           # Hub 源列表
CACHE_KEY_HUB_INDEX_PREFIX = "plugin_hub_index:"       # 单个 Hub 索引前缀
CACHE_KEY_HUB_UPDATED_PREFIX = "plugin_hub_updated:"   # 单个 Hub 更新时间前缀


# ==================== Channel 判定逻辑（PLUGIN-HUB-3） ====================

def extract_org_from_repo_url(repo_url: Optional[str]) -> Optional[str]:
    """
    从 repo_url 中提取组织/用户名
    
    支持格式：
    - https://github.com/strmforge/repo-name
    - git@github.com:strmforge/repo-name.git
    
    Returns:
        组织名（小写）或 None
    """
    if not repo_url:
        return None
    
    try:
        # 处理 git@ 格式
        if repo_url.startswith("git@"):
            # git@github.com:strmforge/repo.git -> strmforge
            match = re.search(r':([^/]+)/', repo_url)
            if match:
                return match.group(1).lower()
            return None
        
        # 处理 https/http 格式
        parsed = urlparse(repo_url)
        path = parsed.path.strip('/')
        parts = path.split('/')
        if len(parts) >= 1:
            return parts[0].lower()
        return None
        
    except Exception:
        return None


def normalize_channel(plugin: RemotePluginInfo) -> str:
    """
    标准化频道字段
    
    逻辑：
    1. 如果 plugin.channel 已指定，直接使用
    2. 否则根据 repo_url 中的组织名判断：
       - 组织在 PLUGIN_OFFICIAL_ORGS 中 → official
       - 否则 → community
    
    Args:
        plugin: 远程插件信息
        
    Returns:
        "official" 或 "community"
    """
    # 已显式指定 channel
    if plugin.channel and plugin.channel in ("official", "community"):
        return plugin.channel
    
    # 根据 repo_url 判断
    org = extract_org_from_repo_url(plugin.repo)
    if org and org in settings.PLUGIN_OFFICIAL_ORGS:
        return "official"
    
    # 默认为 community
    return "community"


def apply_channel_normalization(plugins: list[RemotePluginInfo]) -> list[RemotePluginInfo]:
    """
    对插件列表应用 channel 标准化
    
    Args:
        plugins: 插件列表
        
    Returns:
        更新后的插件列表（原地修改）
    """
    for plugin in plugins:
        plugin.channel = normalize_channel(plugin)
        
        # 如果没有 author_name，尝试从 author 字段获取
        if not plugin.author_name and plugin.author:
            plugin.author_name = plugin.author
    
    return plugins


# ==================== 多 Hub 源管理（PLUGIN-HUB-4） ====================

async def load_runtime_hub_sources(session: AsyncSession) -> list[PluginHubSourceConfig]:
    """
    从 SystemState 加载运行时的 Hub 源列表
    
    逻辑：
    1. 尝试从 DB 读取 plugin_hub_sources
    2. 如果不存在，使用 settings.PLUGIN_HUB_SOURCES 作为初始值并保存
    
    Returns:
        Hub 源配置列表
    """
    try:
        stmt = select(SystemState).where(SystemState.key == CACHE_KEY_HUB_SOURCES)
        result = await session.execute(stmt)
        entry = result.scalar_one_or_none()
        
        if entry and entry.value:
            raw_list = json.loads(entry.value)
            if isinstance(raw_list, list) and raw_list:
                return [PluginHubSourceConfig(**item) for item in raw_list]
        
        # 首次运行，使用配置中的默认值
        default_sources = settings.PLUGIN_HUB_SOURCES
        if default_sources:
            await save_runtime_hub_sources(session, default_sources)
        return default_sources
        
    except Exception as e:
        logger.warning(f"[plugin-hub] Error loading hub sources: {e}")
        return settings.PLUGIN_HUB_SOURCES


async def save_runtime_hub_sources(
    session: AsyncSession,
    sources: list[PluginHubSourceConfig]
) -> None:
    """
    保存 Hub 源列表到 SystemState
    """
    try:
        value = json.dumps([s.model_dump() for s in sources], ensure_ascii=False)
        
        stmt = select(SystemState).where(SystemState.key == CACHE_KEY_HUB_SOURCES)
        result = await session.execute(stmt)
        entry = result.scalar_one_or_none()
        
        if entry:
            entry.value = value
        else:
            entry = SystemState(key=CACHE_KEY_HUB_SOURCES, value=value)
            session.add(entry)
        
        await session.commit()
        logger.info(f"[plugin-hub] Saved {len(sources)} hub sources")
        
    except Exception as e:
        logger.error(f"[plugin-hub] Error saving hub sources: {e}")
        await session.rollback()
        raise


def hub_source_to_public(source: PluginHubSourceConfig) -> PluginHubSourcePublic:
    """将 PluginHubSourceConfig 转换为 PluginHubSourcePublic"""
    return PluginHubSourcePublic(
        id=source.id,
        name=source.name,
        url=source.url,
        channel=source.channel,
        enabled=source.enabled,
        icon_url=source.icon_url,
        description=source.description,
    )


def public_to_hub_source(public: PluginHubSourcePublic) -> PluginHubSourceConfig:
    """将 PluginHubSourcePublic 转换为 PluginHubSourceConfig"""
    return PluginHubSourceConfig(
        id=public.id,
        name=public.name,
        url=public.url,
        channel=public.channel,
        enabled=public.enabled,
        icon_url=public.icon_url,
        description=public.description,
    )


def normalize_hub_url(url: str) -> str:
    """
    标准化 Hub URL
    
    如果是 GitHub 仓库地址，自动转换为 raw plugins.json URL
    """
    url = url.strip()
    
    # 已经是 raw URL 或以 plugins.json 结尾
    if "raw.githubusercontent.com" in url or url.endswith("plugins.json"):
        return url
    
    # GitHub 仓库地址: https://github.com/owner/repo
    if "github.com" in url:
        parts = url.rstrip("/").split("/")
        if len(parts) >= 5:
            owner = parts[-2]
            repo = parts[-1]
            return f"https://raw.githubusercontent.com/{owner}/{repo}/main/plugins.json"
    
    return url


def generate_hub_id_from_url(url: str) -> str:
    """
    从 URL 生成 Hub ID
    """
    try:
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        parts = path.split("/")
        if len(parts) >= 2:
            return f"{parts[0]}-{parts[1]}".lower()
        elif len(parts) >= 1:
            return parts[0].lower()
    except Exception:
        pass
    
    return f"hub-{hash(url) % 10000}"


# ==================== 单 Hub 索引缓存（PLUGIN-HUB-4） ====================

async def load_cached_hub_index(
    session: AsyncSession,
    hub_id: str
) -> Optional[tuple[list[RemotePluginInfo], datetime]]:
    """
    从 SystemState 加载单个 Hub 的缓存索引
    
    Returns:
        (plugins_list, updated_at) 或 None
    """
    try:
        cache_key = f"{CACHE_KEY_HUB_INDEX_PREFIX}{hub_id}"
        time_key = f"{CACHE_KEY_HUB_UPDATED_PREFIX}{hub_id}"
        
        stmt = select(SystemState).where(SystemState.key == cache_key)
        result = await session.execute(stmt)
        cache_entry = result.scalar_one_or_none()
        
        if not cache_entry or not cache_entry.value:
            return None
        
        # 获取更新时间
        stmt_time = select(SystemState).where(SystemState.key == time_key)
        result_time = await session.execute(stmt_time)
        time_entry = result_time.scalar_one_or_none()
        
        updated_at = datetime.min
        if time_entry and time_entry.value:
            try:
                updated_at = datetime.fromisoformat(time_entry.value)
            except ValueError:
                pass
        
        # 解析缓存数据
        raw_plugins = json.loads(cache_entry.value)
        plugins = [RemotePluginInfo(**p) for p in raw_plugins]
        
        return plugins, updated_at
        
    except Exception as e:
        logger.warning(f"[plugin-hub] Error loading cache for hub {hub_id}: {e}")
        return None


async def save_cached_hub_index(
    session: AsyncSession,
    hub_id: str,
    plugins: list[RemotePluginInfo]
) -> None:
    """
    保存单个 Hub 的索引到 SystemState 缓存
    """
    try:
        now = datetime.now()
        cache_key = f"{CACHE_KEY_HUB_INDEX_PREFIX}{hub_id}"
        time_key = f"{CACHE_KEY_HUB_UPDATED_PREFIX}{hub_id}"
        
        cache_value = json.dumps([p.model_dump() for p in plugins], ensure_ascii=False)
        
        # 保存索引数据
        stmt = select(SystemState).where(SystemState.key == cache_key)
        result = await session.execute(stmt)
        cache_entry = result.scalar_one_or_none()
        
        if cache_entry:
            cache_entry.value = cache_value
        else:
            cache_entry = SystemState(key=cache_key, value=cache_value)
            session.add(cache_entry)
        
        # 保存更新时间
        stmt_time = select(SystemState).where(SystemState.key == time_key)
        result_time = await session.execute(stmt_time)
        time_entry = result_time.scalar_one_or_none()
        
        if time_entry:
            time_entry.value = now.isoformat()
        else:
            time_entry = SystemState(key=time_key, value=now.isoformat())
            session.add(time_entry)
        
        await session.commit()
        logger.debug(f"[plugin-hub] Cache saved for hub {hub_id}: {len(plugins)} plugins")
        
    except Exception as e:
        logger.error(f"[plugin-hub] Error saving cache for hub {hub_id}: {e}")
        await session.rollback()


# ==================== 单 Hub 索引拉取（PLUGIN-HUB-4） ====================

async def fetch_hub_index_raw(
    hub: PluginHubSourceConfig
) -> list[dict[str, Any]]:
    """
    从单个 Hub 获取 plugins.json 原始数据
    
    Args:
        hub: Hub 源配置
        
    Returns:
        插件列表（原始 dict）
    """
    hub_url = normalize_hub_url(hub.url)
    logger.info(f"[plugin-hub] Fetching hub '{hub.id}' from: {hub_url}")
    
    try:
        proxy = settings.PROXY_FOR_HTTPX
        async with httpx.AsyncClient(
            timeout=30.0, 
            follow_redirects=True,
            proxy=proxy
        ) as client:
            response = await client.get(hub_url)
            response.raise_for_status()
            
            data = response.json()
            
            # 处理不同格式
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get("plugins", [])
            else:
                logger.error(f"[plugin-hub] Unexpected data format from hub {hub.id}: {type(data)}")
                return []
                
    except httpx.HTTPStatusError as e:
        logger.error(f"[plugin-hub] HTTP error fetching hub {hub.id}: {e.response.status_code}")
        return []
    except httpx.RequestError as e:
        logger.error(f"[plugin-hub] Request error fetching hub {hub.id}: {e}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"[plugin-hub] JSON decode error for hub {hub.id}: {e}")
        return []
    except Exception as e:
        logger.error(f"[plugin-hub] Unexpected error fetching hub {hub.id}: {e}")
        return []


async def get_hub_plugins(
    session: AsyncSession,
    hub: PluginHubSourceConfig,
    *,
    force_refresh: bool = False
) -> list[RemotePluginInfo]:
    """
    获取单个 Hub 的插件列表（带缓存）
    
    Args:
        session: 数据库会话
        hub: Hub 源配置
        force_refresh: 是否强制刷新
        
    Returns:
        插件列表
    """
    # 尝试从缓存加载
    if not force_refresh:
        cache_result = await load_cached_hub_index(session, hub.id)
        if cache_result:
            plugins, updated_at = cache_result
            cache_ttl = settings.PLUGIN_HUB_CACHE_TTL
            if datetime.now() - updated_at < timedelta(seconds=cache_ttl):
                logger.debug(f"[plugin-hub] Using cached index for hub {hub.id} ({len(plugins)} plugins)")
                # 补充 hub 信息
                for p in plugins:
                    p.hub_id = hub.id
                    p.hub_name = hub.name
                    if not p.channel:
                        p.channel = hub.channel
                return plugins
    
    # 从远程获取
    raw_plugins = await fetch_hub_index_raw(hub)
    plugins = parse_remote_index(raw_plugins)
    
    # 补充 hub 信息和 channel
    for p in plugins:
        p.hub_id = hub.id
        p.hub_name = hub.name
        if not p.channel:
            p.channel = hub.channel
    
    # 保存到缓存
    await save_cached_hub_index(session, hub.id, plugins)
    
    logger.info(f"[plugin-hub] Fetched {len(plugins)} plugins from hub {hub.id}")
    return plugins


async def get_all_plugins(
    session: AsyncSession,
    *,
    force_refresh: bool = False,
    hub_ids: Optional[list[str]] = None,
    channel: Optional[str] = None,
    include_community: bool = True,
    installed_only: bool = False,
    not_installed_only: bool = False,
) -> list[RemotePluginWithLocalStatus]:
    """
    获取多 Hub 聚合的插件列表
    
    Args:
        session: 数据库会话
        force_refresh: 是否强制刷新缓存
        hub_ids: 限定的 Hub ID 列表
        channel: 频道过滤（official/community）
        include_community: 是否包含社区插件
        installed_only: 仅返回已安装插件
        not_installed_only: 仅返回未安装插件
        
    Returns:
        带本地状态的插件列表
    """
    # 加载 Hub 源列表
    all_hubs = await load_runtime_hub_sources(session)
    
    # 过滤启用的 Hub
    enabled_hubs = [h for h in all_hubs if h.enabled]
    
    # 过滤指定的 Hub
    if hub_ids:
        enabled_hubs = [h for h in enabled_hubs if h.id in hub_ids]
    
    if not enabled_hubs:
        logger.warning("[plugin-hub] No enabled hub sources")
        return []
    
    # 并发获取所有 Hub 的插件
    all_plugins: list[RemotePluginInfo] = []
    seen_ids: dict[str, RemotePluginInfo] = {}  # 去重用
    
    for hub in enabled_hubs:
        try:
            hub_plugins = await get_hub_plugins(session, hub, force_refresh=force_refresh)
            
            for plugin in hub_plugins:
                # 去重：优先保留官方插件
                if plugin.id in seen_ids:
                    existing = seen_ids[plugin.id]
                    # 如果新插件是官方的，替换已有的社区插件
                    if plugin.channel == "official" and existing.channel != "official":
                        seen_ids[plugin.id] = plugin
                else:
                    seen_ids[plugin.id] = plugin
                    
        except Exception as e:
            logger.error(f"[plugin-hub] Error fetching hub {hub.id}: {e}")
            continue
    
    all_plugins = list(seen_ids.values())
    
    # 应用 channel 标准化
    all_plugins = apply_channel_normalization(all_plugins)
    
    # 社区插件过滤
    if not include_community:
        all_plugins = [p for p in all_plugins if p.channel != "community"]
    
    # 频道过滤
    if channel and channel in ("official", "community"):
        all_plugins = [p for p in all_plugins if p.channel == channel]
    
    # 获取本地插件并合并状态
    local_map = await get_local_plugins_map(session)
    plugins_with_status = merge_with_local_status(all_plugins, local_map)
    
    # 安装状态过滤
    if installed_only and not_installed_only:
        # 冲突：优先 installed_only
        plugins_with_status = [p for p in plugins_with_status if p.installed]
    elif installed_only:
        plugins_with_status = [p for p in plugins_with_status if p.installed]
    elif not_installed_only:
        plugins_with_status = [p for p in plugins_with_status if not p.installed]
    
    return plugins_with_status


async def fetch_remote_index_raw() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    从远程 URL 获取 plugins.json 原始数据
    
    Returns:
        (meta_info, plugins_list): 元信息和插件列表
    """
    hub_url = settings.PLUGIN_HUB_URL
    if not hub_url:
        logger.warning("[plugin-hub] PLUGIN_HUB_URL not configured")
        return {}, []
    
    logger.info(f"[plugin-hub] Fetching remote index from: {hub_url}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # 使用代理（如果配置了）
            proxy = settings.PROXY_FOR_HTTPX
            if proxy:
                client = httpx.AsyncClient(timeout=30.0, follow_redirects=True, proxy=proxy)
            
            response = await client.get(hub_url)
            response.raise_for_status()
            
            data = response.json()
            
            # 处理不同格式
            if isinstance(data, list):
                # 直接是插件列表
                return {}, data
            elif isinstance(data, dict):
                # 带包装的格式
                meta = {
                    "hub_name": data.get("hub_name", "Plugin Hub"),
                    "hub_version": data.get("hub_version", 1),
                }
                plugins = data.get("plugins", [])
                return meta, plugins
            else:
                logger.error(f"[plugin-hub] Unexpected data format: {type(data)}")
                return {}, []
                
    except httpx.HTTPStatusError as e:
        logger.error(f"[plugin-hub] HTTP error fetching index: {e.response.status_code}")
        raise
    except httpx.RequestError as e:
        logger.error(f"[plugin-hub] Request error fetching index: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"[plugin-hub] JSON decode error: {e}")
        raise


def parse_remote_plugin(raw: dict[str, Any]) -> Optional[RemotePluginInfo]:
    """
    解析单个插件数据
    
    Args:
        raw: 原始 JSON 数据
        
    Returns:
        RemotePluginInfo 或 None（如果解析失败）
    """
    try:
        plugin_id = raw.get("id")
        if not plugin_id:
            logger.warning("[plugin-hub] Plugin missing 'id' field, skipping")
            return None
        
        # 解析 supports 字段
        supports_raw = raw.get("supports", {})
        supports = PluginSupports(
            search=supports_raw.get("search", False),
            bot_commands=supports_raw.get("bot_commands", False),
            ui_panels=supports_raw.get("ui_panels", False),
            workflows=supports_raw.get("workflows", False),
        )
        
        return RemotePluginInfo(
            id=plugin_id,
            name=raw.get("name", plugin_id),
            description=raw.get("description"),
            author=raw.get("author"),
            tags=raw.get("tags", []),
            homepage=raw.get("homepage"),
            repo=raw.get("repo"),
            download_url=raw.get("download_url"),
            version=raw.get("version"),
            min_core_version=raw.get("min_core_version"),
            supports=supports,
            panels=raw.get("panels", []),
            enabled_by_default=raw.get("enabled_by_default", False),
            # 作者 & 频道信息（PLUGIN-HUB-3）
            author_name=raw.get("author_name"),
            author_url=raw.get("author_url"),
            channel=raw.get("channel"),
        )
        
    except Exception as e:
        logger.warning(f"[plugin-hub] Error parsing plugin: {e}")
        return None


def parse_remote_index(raw_plugins: list[dict[str, Any]]) -> list[RemotePluginInfo]:
    """
    解析整个插件列表
    
    Args:
        raw_plugins: 原始插件列表
        
    Returns:
        解析后的 RemotePluginInfo 列表
    """
    result = []
    for raw in raw_plugins:
        plugin = parse_remote_plugin(raw)
        if plugin:
            result.append(plugin)
    return result


async def load_cached_index(session: AsyncSession) -> Optional[tuple[PluginHubIndex, datetime]]:
    """
    从 SystemState 加载缓存的索引
    
    Returns:
        (PluginHubIndex, updated_at) 或 None
    """
    try:
        # 获取缓存数据
        stmt = select(SystemState).where(SystemState.key == CACHE_KEY_INDEX)
        result = await session.execute(stmt)
        cache_entry = result.scalar_one_or_none()
        
        if not cache_entry or not cache_entry.value:
            return None
        
        # 获取更新时间
        stmt_time = select(SystemState).where(SystemState.key == CACHE_KEY_UPDATED_AT)
        result_time = await session.execute(stmt_time)
        time_entry = result_time.scalar_one_or_none()
        
        updated_at = None
        if time_entry and time_entry.value:
            try:
                updated_at = datetime.fromisoformat(time_entry.value)
            except ValueError:
                pass
        
        # 解析缓存数据
        data = json.loads(cache_entry.value)
        plugins = [RemotePluginInfo(**p) for p in data.get("plugins", [])]
        
        index = PluginHubIndex(
            hub_name=data.get("hub_name", "Plugin Hub"),
            hub_version=data.get("hub_version", 1),
            plugins=plugins,
            fetched_at=updated_at,
        )
        
        return index, updated_at or datetime.min
        
    except Exception as e:
        logger.warning(f"[plugin-hub] Error loading cache: {e}")
        return None


async def save_cached_index(
    session: AsyncSession,
    meta: dict[str, Any],
    plugins: list[RemotePluginInfo]
) -> None:
    """
    保存索引到 SystemState 缓存
    """
    try:
        now = datetime.now()
        
        # 序列化数据
        cache_data = {
            "hub_name": meta.get("hub_name", "Plugin Hub"),
            "hub_version": meta.get("hub_version", 1),
            "plugins": [p.model_dump() for p in plugins],
        }
        cache_value = json.dumps(cache_data, ensure_ascii=False)
        
        # 保存索引数据
        stmt = select(SystemState).where(SystemState.key == CACHE_KEY_INDEX)
        result = await session.execute(stmt)
        cache_entry = result.scalar_one_or_none()
        
        if cache_entry:
            cache_entry.value = cache_value
        else:
            cache_entry = SystemState(key=CACHE_KEY_INDEX, value=cache_value)
            session.add(cache_entry)
        
        # 保存更新时间
        stmt_time = select(SystemState).where(SystemState.key == CACHE_KEY_UPDATED_AT)
        result_time = await session.execute(stmt_time)
        time_entry = result_time.scalar_one_or_none()
        
        if time_entry:
            time_entry.value = now.isoformat()
        else:
            time_entry = SystemState(key=CACHE_KEY_UPDATED_AT, value=now.isoformat())
            session.add(time_entry)
        
        await session.commit()
        logger.info(f"[plugin-hub] Cache saved with {len(plugins)} plugins")
        
    except Exception as e:
        logger.error(f"[plugin-hub] Error saving cache: {e}")
        await session.rollback()


async def get_local_plugins_map(session: AsyncSession) -> dict[str, Plugin]:
    """
    获取本地已安装插件的映射
    
    Returns:
        {plugin_name: Plugin} 映射
    """
    stmt = select(Plugin)
    result = await session.execute(stmt)
    plugins = result.scalars().all()
    
    # 使用 name 字段作为 key（对应远程的 id）
    return {p.name: p for p in plugins}


def merge_with_local_status(
    remote_plugins: list[RemotePluginInfo],
    local_map: dict[str, Plugin]
) -> list[RemotePluginWithLocalStatus]:
    """
    合并远程插件信息和本地安装状态
    
    Args:
        remote_plugins: 远程插件列表
        local_map: 本地插件映射
        
    Returns:
        带本地状态的插件列表
    """
    result = []
    
    for remote in remote_plugins:
        # 查找本地插件（通过 id 匹配 name）
        local = local_map.get(remote.id)
        
        installed = local is not None
        local_version = local.version if local else None
        local_plugin_id = local.id if local else None
        
        # 判断是否有更新
        has_update = False
        if installed and remote.version and local_version:
            # 简单字符串比较（非语义化版本比较）
            has_update = remote.version != local_version
        
        # 获取本地来源信息（PLUGIN-HUB-2）
        source = getattr(local, 'source', None) if local else None
        installed_ref = getattr(local, 'installed_ref', None) if local else None
        local_repo_url = getattr(local, 'repo_url', None) if local else None
        auto_update_enabled = getattr(local, 'auto_update_enabled', None) if local else None
        
        # 获取本地启用状态（PLUGIN-HUB-4）
        enabled = False
        if local:
            status = getattr(local, 'status', None)
            enabled = status == 'ENABLED' if status else False
        
        result.append(RemotePluginWithLocalStatus(
            **remote.model_dump(),
            installed=installed,
            local_version=local_version,
            has_update=has_update,
            local_plugin_id=local_plugin_id,
            source=source,
            installed_ref=installed_ref,
            local_repo_url=local_repo_url,
            auto_update_enabled=auto_update_enabled,
            enabled=enabled,
        ))
    
    return result


async def get_plugin_hub_index(
    session: AsyncSession,
    *,
    force_refresh: bool = False,
    channel: Optional[str] = None,  # "official" / "community" / None(all)
    include_community: Optional[bool] = None,  # 覆盖 config 中的 PLUGIN_COMMUNITY_VISIBLE
) -> PluginHubIndexResponse:
    """
    获取 Plugin Hub 索引（带本地状态合并）
    
    Args:
        session: 数据库会话
        force_refresh: 是否强制刷新（忽略缓存）
        channel: 频道过滤（official/community/None）
        include_community: 是否包含社区插件（覆盖配置）
        
    Returns:
        PluginHubIndexResponse
    """
    meta = {"hub_name": "Plugin Hub", "hub_version": 1}
    plugins: list[RemotePluginInfo] = []
    fetched_at: Optional[datetime] = None
    cached = False
    
    # 尝试从缓存加载
    if not force_refresh:
        cache_result = await load_cached_index(session)
        if cache_result:
            index, updated_at = cache_result
            
            # 检查缓存是否过期
            cache_ttl = settings.PLUGIN_HUB_CACHE_TTL
            if datetime.now() - updated_at < timedelta(seconds=cache_ttl):
                logger.info(f"[plugin-hub] Using cached index ({len(index.plugins)} plugins)")
                meta = {"hub_name": index.hub_name, "hub_version": index.hub_version}
                plugins = index.plugins
                fetched_at = updated_at
                cached = True
    
    # 需要从远程获取
    if not cached:
        try:
            remote_meta, raw_plugins = await fetch_remote_index_raw()
            plugins = parse_remote_index(raw_plugins)
            meta = remote_meta or meta
            fetched_at = datetime.now()
            
            # 保存到缓存
            await save_cached_index(session, meta, plugins)
            
            logger.info(f"[plugin-hub] Fetched {len(plugins)} plugins from remote")
            
        except Exception as e:
            logger.error(f"[plugin-hub] Failed to fetch remote index: {e}")
            
            # 尝试使用过期缓存
            cache_result = await load_cached_index(session)
            if cache_result:
                index, updated_at = cache_result
                meta = {"hub_name": index.hub_name, "hub_version": index.hub_version}
                plugins = index.plugins
                fetched_at = updated_at
                cached = True
                logger.info("[plugin-hub] Using expired cache as fallback")
            else:
                # 无缓存可用
                raise
    
    # 应用 channel 标准化（PLUGIN-HUB-3）
    plugins = apply_channel_normalization(plugins)
    
    # 根据配置过滤社区插件
    show_community = include_community if include_community is not None else settings.PLUGIN_COMMUNITY_VISIBLE
    if not show_community:
        original_count = len(plugins)
        plugins = [p for p in plugins if p.channel != "community"]
        logger.debug(f"[plugin-hub] Filtered out {original_count - len(plugins)} community plugins")
    
    # 根据 channel 参数过滤
    if channel and channel in ("official", "community"):
        plugins = [p for p in plugins if p.channel == channel]
    
    # 获取本地插件并合并状态
    local_map = await get_local_plugins_map(session)
    plugins_with_status = merge_with_local_status(plugins, local_map)
    
    return PluginHubIndexResponse(
        hub_name=meta.get("hub_name", "Plugin Hub"),
        hub_version=meta.get("hub_version", 1),
        plugins=plugins_with_status,
        fetched_at=fetched_at,
        cached=cached,
    )


async def get_remote_plugin_detail(
    session: AsyncSession,
    plugin_id: str,
    *,
    force_refresh: bool = False
) -> Optional[RemotePluginWithLocalStatus]:
    """
    获取单个远程插件的详细信息（多 Hub 聚合）
    
    Args:
        session: 数据库会话
        plugin_id: 插件 ID
        force_refresh: 是否强制刷新
        
    Returns:
        插件详情或 None
    """
    # 使用多 Hub 聚合获取所有插件
    plugins = await get_multi_hub_index(
        session, 
        force_refresh=force_refresh,
        include_community=True,  # 搜索时包含所有插件
    )
    
    for plugin in plugins:
        if plugin.id == plugin_id:
            return plugin
    
    return None


async def get_plugin_readme(plugin: RemotePluginInfo) -> Optional[str]:
    """
    获取插件的 README 内容
    
    Args:
        plugin: 远程插件信息
        
    Returns:
        README Markdown 内容或 None
    """
    # 尝试从 repo URL 推导 README 地址
    repo_url = plugin.repo
    if not repo_url:
        return None
    
    # 支持 GitHub 仓库
    readme_url = None
    if "github.com" in repo_url:
        # https://github.com/owner/repo -> https://raw.githubusercontent.com/owner/repo/main/README.md
        parts = repo_url.rstrip("/").split("/")
        if len(parts) >= 5:
            owner = parts[-2]
            repo_name = parts[-1]
            readme_url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/main/README.md"
    
    if not readme_url:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(readme_url)
            if response.status_code == 200:
                return response.text
            else:
                # 尝试 master 分支
                readme_url_master = readme_url.replace("/main/", "/master/")
                response = await client.get(readme_url_master)
                if response.status_code == 200:
                    return response.text
                    
    except Exception as e:
        logger.warning(f"[plugin-hub] Failed to fetch README for {plugin.id}: {e}")
    
    return None


# 兼容性别名：get_multi_hub_index -> get_all_plugins
get_multi_hub_index = get_all_plugins


# ============== PLUGIN-SAFETY-1：轻量级自动更新检测 ==============

async def check_plugin_updates_lightweight(
    session: AsyncSession,
    force_refresh: bool = False
) -> dict[str, dict[str, Any]]:
    """
    轻量级插件更新检测
    
    检查本地已安装插件是否有更新可用，但不发送通知。
    仅更新内部状态，供前端查询显示。
    
    Args:
        session: 数据库会话
        force_refresh: 是否强制刷新远程索引
        
    Returns:
        {plugin_name: update_info} 字典，update_info 包含：
        - has_update: bool
        - current_version: str
        - latest_version: str
        - update_url: Optional[str]
    """
    from app.services.plugin_service import get_installed_plugins
    from app.core.cache import cache
    
    # 更新远程索引（如果需要）
    await refresh_plugin_index(session, force_refresh=force_refresh)
    
    # 获取本地插件
    local_plugins = await get_installed_plugins(session)
    update_info = {}
    
    for local_plugin in local_plugins:
        if not local_plugin.hub_id or not local_plugin.auto_update_enabled:
            continue
        
        # 查找远程插件信息
        remote_plugin = await get_plugin_by_id(session, local_plugin.hub_id)
        if not remote_plugin:
            continue
        
        # 版本比较（简单字符串比较，实际应使用语义化版本）
        has_update = remote_plugin.version != local_plugin.version
        
        update_info[local_plugin.name] = {
            "has_update": has_update,
            "current_version": local_plugin.version,
            "latest_version": remote_plugin.version,
            "update_url": remote_plugin.repo,
            "release_notes": remote_plugin.release_notes,
            "updated_at": remote_plugin.updated_at
        }
    
    # 缓存更新信息（24小时）
    await cache.set("plugin_updates_lightweight", update_info, expire=86400)
    
    if update_info:
        available_updates = sum(1 for info in update_info.values() if info["has_update"])
        logger.info(f"[plugin-hub] Lightweight update check completed: {available_updates} updates available")
    
    return update_info


async def get_cached_update_info() -> dict[str, dict[str, Any]]:
    """
    获取缓存的更新信息
    
    Returns:
        缓存的更新信息字典，如果不存在则返回空字典
    """
    from app.core.cache import cache
    
    try:
        cached_info = await cache.get("plugin_updates_lightweight")
        return cached_info or {}
    except Exception as e:
        logger.warning(f"[plugin-hub] Failed to get cached update info: {e}")
        return {}
