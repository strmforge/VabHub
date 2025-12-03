"""
插件模型
DEV-SDK-1 实现
PLUGIN-SDK-2 扩展：SDK 权限声明
PLUGIN-UX-3 扩展：配置 schema
PLUGIN-SAFETY-1 扩展：健康状态 & 隔离机制
PLUGIN-REMOTE-1 扩展：远程插件支持 & 类型区分

描述已安装的插件及其状态
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, JSON, Boolean
from sqlalchemy.sql import func

from app.core.database import Base


class PluginStatus(str, Enum):
    """插件状态"""
    INSTALLED = "INSTALLED"     # 已安装但未启用
    ENABLED = "ENABLED"         # 已启用
    DISABLED = "DISABLED"       # 已禁用
    BROKEN = "BROKEN"           # 加载失败/损坏


class PluginType(str, Enum):
    """插件类型（PLUGIN-REMOTE-1）"""
    LOCAL = "local"      # 本地插件：克隆到本地，作为 Python 包运行
    REMOTE = "remote"    # 远程插件：通过 HTTP 调用远程服务


class Plugin(Base):
    """
    插件记录模型
    
    记录已安装的插件信息及其运行状态
    """
    __tablename__ = "plugin"
    
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    
    # 插件唯一标识（如 vabhub.example.hello_world）
    name: str = Column(String(255), unique=True, nullable=False, index=True)
    
    # 显示名称
    display_name: str = Column(String(255), nullable=False)
    
    # ==================== PLUGIN-REMOTE-1：插件类型区分 ====================
    # 插件类型：本地插件 vs 远程插件
    plugin_type: PluginType = Column(
        SQLEnum(PluginType),
        nullable=False,
        default=PluginType.LOCAL,
        index=True
    )
    
    # 版本号
    version: str = Column(String(50), nullable=False, default="0.0.1")
    
    # 描述
    description: Optional[str] = Column(Text, nullable=True)
    
    # 作者
    author: Optional[str] = Column(String(255), nullable=True)
    
    # 主页 URL
    homepage: Optional[str] = Column(String(512), nullable=True)
    
    # 后端入口模块（如 hello_plugin.main）
    entry_module: str = Column(String(255), nullable=False)
    
    # 前端入口标记（如 dev:hello_plugin）
    front_entry: Optional[str] = Column(String(255), nullable=True)
    
    # 声明支持的扩展点（JSON）
    # 格式：{"search_providers": ["global"], "bot_commands": ["hello"], "workflows": ["demo"]}
    capabilities: dict = Column(JSON, nullable=False, default=dict)
    
    # PLUGIN-SDK-2：SDK 权限声明（JSON 数组）
    # 格式：["download.read", "download.write", "media.read", "cloud115.task"]
    # 未声明的能力调用时会被 SDK 拒绝
    sdk_permissions: list = Column(JSON, nullable=False, default=list)
    
    # UI 面板声明（JSON）
    # 格式：[{id, title, placement, type, ...}]
    ui_panels: list = Column(JSON, nullable=False, default=list)
    
    # PLUGIN-UX-3：配置 Schema（JSON）
    # 格式：{"type": "object", "properties": {...}, "required": [...]}
    # 用于前端自动渲染配置表单
    config_schema: Optional[dict] = Column(JSON, nullable=True)
    
    # ==================== PLUGIN-REMOTE-1：远程插件配置 ====================
    # 远程插件配置（JSON，仅当 plugin_type=REMOTE 时使用）
    # 格式：{"base_url": "https://example.com", "token": "xxx", "timeout": 5}
    remote_config: Optional[dict] = Column(JSON, nullable=True)
    
    # 订阅的事件列表（JSON，用于远程插件事件分发）
    # 格式：["manga.updated", "audiobook.tts_finished"]
    subscribed_events: list = Column(JSON, nullable=False, default=list)
    
    # 插件状态
    status: PluginStatus = Column(
        SQLEnum(PluginStatus),
        nullable=False,
        default=PluginStatus.INSTALLED
    )
    
    # 插件目录路径（相对于 PLUGINS_DIR）
    plugin_dir: Optional[str] = Column(String(512), nullable=True)
    
    # 时间戳
    installed_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at: datetime = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # 最后错误信息
    last_error: Optional[str] = Column(Text, nullable=True)
    
    # ==================== PLUGIN-SAFETY-1：健康状态 & 隔离机制 ====================
    # 最后错误时间
    last_error_at: Optional[datetime] = Column(DateTime, nullable=True, index=True)
    
    # 错误计数
    error_count: int = Column(Integer, nullable=False, default=0, index=True)
    
    # 是否被隔离（标记为有问题的插件，不再调用其 handler）
    # 不等同于卸载，只是"不再调用它"
    is_quarantined: bool = Column(Boolean, nullable=False, default=False, index=True)
    
    # ==================== 插件来源信息（PLUGIN-HUB-2） ====================
    # 来源类型：local（手工放入）/ plugin_hub（一键安装）/ manual_hub（手动安装但有 hub 关联）
    source: str = Column(String(32), nullable=False, default="local", index=True)
    
    # 关联的 Plugin Hub 条目 ID（对应 RemotePluginInfo.id）
    hub_id: Optional[str] = Column(String(128), nullable=True, index=True)
    
    # Git 仓库地址
    repo_url: Optional[str] = Column(String(512), nullable=True)
    
    # 当前安装的 commit/ref 信息
    installed_ref: Optional[str] = Column(String(128), nullable=True)
    
    # 是否启用自动更新
    auto_update_enabled: bool = Column(Boolean, nullable=False, default=True)
    
    # ==================== PLUGIN-REMOTE-1：远程插件令牌（预留） ====================
    # 远程插件访问令牌（用于远程插件调用宿主 API，v1 预留）
    plugin_token: Optional[str] = Column(String(255), nullable=True, index=True)
    
    # ==================== PLUGIN-REMOTE-1：插件行为统计（轻量） ====================
    # SDK 级调用次数（宿主服务调用插件的次数）
    call_count: int = Column(Integer, nullable=False, default=0, index=True)
    
    # 事件处理次数（远程插件处理事件的次数）
    event_handled_count: int = Column(Integer, nullable=False, default=0, index=True)
    
    # 最后调用时间
    last_called_at: Optional[datetime] = Column(DateTime, nullable=True, index=True)
    
    def __repr__(self) -> str:
        return f"<Plugin {self.name} ({self.status.value})>"
