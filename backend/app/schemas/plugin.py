"""
插件 Schema
DEV-SDK-1 实现
DEV-SDK-2 扩展：UI Panel 支持
PLUGIN-SDK-2 扩展：SDK 权限声明
PLUGIN-UX-3 扩展：配置 Schema + Dashboard DSL
PLUGIN-SAFETY-1 扩展：健康状态 & 隔离机制
PLUGIN-REMOTE-1 扩展：远程插件支持 & 类型区分
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional, Literal
from pydantic import BaseModel, Field


# ============== UI Panel 类型定义 ==============

class PluginPanelPlacement(str, Enum):
    """面板放置位置"""
    HOME_DASHBOARD = "home_dashboard"
    ADMIN_DASHBOARD = "admin_dashboard"
    TASK_CENTER = "task_center"
    READING_CENTER = "reading_center"
    DEV_PLUGIN = "dev_plugin"
    CUSTOM = "custom"


class PluginPanelType(str, Enum):
    """面板类型"""
    METRIC_GRID = "metric_grid"     # 多个统计卡片
    LIST = "list"                   # 表格/列表
    MARKDOWN = "markdown"           # Markdown 文本
    LOG_STREAM = "log_stream"       # 最近日志
    STATUS_CARD = "status_card"     # 单个状态卡


class PluginPanelDefinition(BaseModel):
    """插件面板定义"""
    id: str
    title: str
    description: Optional[str] = None
    placement: PluginPanelPlacement
    type: PluginPanelType
    endpoint: Optional[str] = None
    order: int = 100
    enabled_by_default: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class PluginPanelWithPlugin(BaseModel):
    """带插件信息的面板"""
    plugin_id: str
    plugin_name: str
    panel: PluginPanelDefinition


class PluginPanelDataResponse(BaseModel):
    """面板数据响应"""
    type: PluginPanelType
    meta: dict[str, Any] = Field(default_factory=dict)
    payload: Any = None


# ============== 插件能力声明 ==============

class PluginCapabilities(BaseModel):
    """插件能力声明"""
    search_providers: list[str] = Field(default_factory=list)
    bot_commands: list[str] = Field(default_factory=list)
    workflows: list[str] = Field(default_factory=list)
    ui_panels: list[str] = Field(default_factory=list)


class PluginRead(BaseModel):
    """插件读取 Schema"""
    id: int
    name: str
    display_name: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    homepage: Optional[str] = None
    entry_module: str
    front_entry: Optional[str] = None
    capabilities: dict[str, Any] = Field(default_factory=dict)
    ui_panels: list[PluginPanelDefinition] = Field(default_factory=list)
    status: str
    plugin_dir: Optional[str] = None
    installed_at: datetime
    updated_at: datetime
    last_error: Optional[str] = None
    
    # PLUGIN-REMOTE-1：插件类型区分
    plugin_type: str = "local"
    remote_config: Optional[dict[str, Any]] = None
    subscribed_events: list[str] = Field(default_factory=list)
    plugin_token: Optional[str] = None
    
    # PLUGIN-SDK-2：SDK 权限声明
    sdk_permissions: list[str] = Field(default_factory=list)
    
    # PLUGIN-UX-3：配置 Schema
    config_schema: Optional[dict[str, Any]] = None
    
    # PLUGIN-SAFETY-1：健康状态 & 隔离机制
    last_error_at: Optional[datetime] = None
    error_count: int = 0
    is_quarantined: bool = False
    
    # 来源信息（PLUGIN-HUB-2）
    source: str = "local"
    hub_id: Optional[str] = None
    repo_url: Optional[str] = None
    installed_ref: Optional[str] = None
    auto_update_enabled: bool = True
    
    # PLUGIN-REMOTE-1：插件行为统计
    call_count: int = 0
    event_handled_count: int = 0
    last_called_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PluginUpdateStatus(BaseModel):
    """插件状态更新 Schema"""
    status: Literal["ENABLED", "DISABLED"]


class PluginScanResult(BaseModel):
    """插件扫描结果"""
    scanned: int = 0
    new_plugins: int = 0
    updated_plugins: int = 0
    broken_plugins: int = 0
    plugins: list[PluginRead] = Field(default_factory=list)


class WorkflowExtensionInfo(BaseModel):
    """Workflow 扩展信息"""
    id: str
    name: str
    description: str
    plugin_id: str
    plugin_name: str


class WorkflowRunRequest(BaseModel):
    """Workflow 执行请求"""
    payload: Optional[dict[str, Any]] = None


class WorkflowRunResult(BaseModel):
    """Workflow 执行结果"""
    workflow_id: str
    success: bool
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: int = 0


# ============== PLUGIN-UX-3：插件配置 ==============

class PluginConfigSchema(BaseModel):
    """插件配置 Schema"""
    plugin_id: str
    config: dict[str, Any] = Field(default_factory=dict)
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PluginConfigUpdate(BaseModel):
    """插件配置更新请求"""
    config: dict[str, Any]


# ============== PLUGIN-UX-3：Dashboard DSL ==============

class PluginDashboardWidgetType(str, Enum):
    """Dashboard Widget 类型"""
    STAT_CARD = "stat_card"         # 统计卡片
    TABLE = "table"                 # 表格
    TEXT = "text"                   # 文本/Markdown
    ACTION_BUTTON = "action_button" # 操作按钮


class PluginDashboardWidget(BaseModel):
    """Dashboard Widget 定义"""
    id: str
    type: PluginDashboardWidgetType
    title: Optional[str] = None
    description: Optional[str] = None
    
    # stat_card 特有
    value: Optional[str] = None
    unit: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    
    # table 特有
    columns: Optional[list[str]] = None
    rows: Optional[list[dict[str, Any]]] = None
    
    # text 特有
    markdown: Optional[str] = None
    
    # action_button 特有
    action_api: Optional[str] = None
    action_method: Optional[str] = "POST"
    action_params_schema: Optional[dict[str, Any]] = None
    action_label: Optional[str] = None


class PluginDashboardSchema(BaseModel):
    """插件 Dashboard Schema"""
    widgets: list[PluginDashboardWidget] = Field(default_factory=list)
