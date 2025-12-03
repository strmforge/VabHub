"""
Plugin Hub Schema
PLUGIN-HUB-1 & PLUGIN-HUB-3 & PLUGIN-HUB-4 实现

远程插件索引相关数据类型
"""

from datetime import datetime
from typing import Any, Optional, Literal
from pydantic import BaseModel, Field


# 频道类型
PluginChannel = Literal["official", "community"]


class PluginSupports(BaseModel):
    """插件支持的功能"""
    search: bool = False
    bot_commands: bool = False
    ui_panels: bool = False
    workflows: bool = False


class RemotePluginInfo(BaseModel):
    """
    远程插件信息
    
    字段映射自 vabhub-plugins 仓库的 plugins.json
    """
    id: str
    name: str
    description: Optional[str] = None
    author: Optional[str] = None  # 兼容旧字段
    tags: list[str] = Field(default_factory=list)
    
    # 仓库信息
    homepage: Optional[str] = None
    repo: Optional[str] = None  # Git 仓库地址
    download_url: Optional[str] = None  # 下载链接（ZIP）
    
    # 版本信息
    version: Optional[str] = None
    min_core_version: Optional[str] = None
    
    # 功能支持
    supports: PluginSupports = Field(default_factory=PluginSupports)
    panels: list[str] = Field(default_factory=list)  # 支持的面板位置
    
    # 其他
    enabled_by_default: bool = False
    extra: dict[str, Any] = Field(default_factory=dict)
    
    # 作者 & 频道信息（PLUGIN-HUB-3）
    author_name: Optional[str] = None  # 作者名称
    author_url: Optional[str] = None   # 作者主页（GitHub 等）
    channel: Optional[str] = None      # 频道：official / community
    
    # Hub 来源信息（PLUGIN-HUB-4）
    hub_id: Optional[str] = None       # 来源 Hub ID
    hub_name: Optional[str] = None     # 来源 Hub 名称


class RemotePluginWithLocalStatus(RemotePluginInfo):
    """
    带本地安装状态的远程插件信息
    """
    installed: bool = False
    local_version: Optional[str] = None
    has_update: bool = False
    local_plugin_id: Optional[int] = None  # 本地 Plugin 表的 ID
    
    # 本地来源信息（PLUGIN-HUB-2）
    source: Optional[str] = None
    installed_ref: Optional[str] = None
    local_repo_url: Optional[str] = None  # 本地记录的 repo_url
    auto_update_enabled: Optional[bool] = None
    
    # 本地状态（PLUGIN-HUB-4）
    enabled: bool = False  # 本地插件是否启用


class PluginHubIndex(BaseModel):
    """Plugin Hub 索引"""
    hub_name: str = "VabHub Plugin Hub"
    hub_version: int = 1
    plugins: list[RemotePluginInfo] = Field(default_factory=list)
    fetched_at: Optional[datetime] = None


class PluginHubIndexResponse(BaseModel):
    """Plugin Hub 索引响应"""
    hub_name: str
    hub_version: int
    plugins: list[RemotePluginWithLocalStatus]
    fetched_at: Optional[datetime] = None
    cached: bool = False


# ==================== Hub 源管理 DTO（PLUGIN-HUB-4） ====================

class PluginHubSourcePublic(BaseModel):
    """
    插件 Hub 源公开信息（用于 API 响应）
    """
    id: str
    name: str
    url: str
    channel: Literal["official", "community"] = "community"
    enabled: bool = True
    icon_url: Optional[str] = None
    description: Optional[str] = None


class PluginHubSourceUpdateRequest(BaseModel):
    """
    更新插件 Hub 源列表请求
    """
    sources: list[PluginHubSourcePublic]


class PluginHubConfigResponse(BaseModel):
    """
    Plugin Hub 配置响应（PLUGIN-HUB-3 & 4）
    """
    community_visible: bool
    community_install_enabled: bool
    official_orgs: list[str]
