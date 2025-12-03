# VabHub Plugin SDK 开发指南

> **PLUGIN-SDK-1 / PLUGIN-SDK-2 / PLUGIN-UX-3 实现文档**
> 
> 本文档面向插件开发者，介绍如何使用 VabHub Plugin SDK 和 EventBus 开发插件。

## 目录

- [总体设计](#总体设计)
- [快速开始](#快速开始)
- [SDK 能力一览](#sdk-能力一览)
- [插件权限声明](#插件权限声明sdk_permissions)
- [宿主服务封装](#宿主服务封装)
- [事件系统](#事件系统)
- [插件配置系统](#插件配置系统)
- [Dashboard 系统](#dashboard-系统)
- [插件对外 API](#插件对外-api)
- [最佳实践](#最佳实践)
- [与旧方式的区别](#与旧方式的区别)
- [版本兼容策略](#版本兼容策略)

---

## 总体设计

VabHub 插件运行在主系统的 **同一 Python 进程** 内。插件通过 `setup_plugin(ctx, bus, sdk)` 函数作为入口，获得：

- **PluginContext (ctx)**：插件运行时上下文，包含插件 ID、数据目录等信息
- **EventBus (bus)**：全局事件总线，用于订阅业务事件
- **VabHubSDK (sdk)**：主系统能力封装，提供日志、HTTP、通知等功能

### 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    VabHub 主系统                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │                  EventBus                        │   │
│  │   (漫画更新 / TTS完成 / 下载完成 / 插件生命周期)    │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│         ┌───────────────┼───────────────┐              │
│         ▼               ▼               ▼              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │
│  │  Plugin A   │ │  Plugin B   │ │  Plugin C   │      │
│  │             │ │             │ │             │      │
│  │ setup_plugin│ │ setup_plugin│ │ setup_plugin│      │
│  │   ↓         │ │   ↓         │ │   ↓         │      │
│  │ sdk.log     │ │ sdk.http    │ │ sdk.notify  │      │
│  │ sdk.paths   │ │ sdk.env     │ │ bus.subscribe│     │
│  └─────────────┘ └─────────────┘ └─────────────┘      │
└─────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 最小示例

创建一个插件目录结构：

```
plugins/
  my_plugin/
    plugin.json
    backend/
      my_plugin/
        __init__.py
        main.py
```

**plugin.json**:
```json
{
  "id": "vabhub.my_plugin",
  "display_name": "我的插件",
  "version": "1.0.0",
  "description": "一个简单的示例插件",
  "author": "Your Name",
  "backend": {
    "entry_module": "my_plugin.main"
  },
  "capabilities": {}
}
```

**main.py**:
```python
from typing import Any

from app.plugin_sdk.context import PluginContext
from app.plugin_sdk.api import VabHubSDK
from app.plugin_sdk.events import EventBus, EventType


def setup_plugin(ctx: PluginContext, bus: EventBus, sdk: VabHubSDK) -> None:
    """插件入口函数"""
    sdk.log.info(f"插件 {ctx.plugin_id} 已加载！")
    
    # 订阅漫画更新事件
    async def on_manga_updated(event: EventType, payload: dict[str, Any]) -> None:
        sdk.log.info(f"漫画更新: {payload.get('series_title')}")
    
    bus.subscribe(EventType.MANGA_UPDATED, on_manga_updated, source=ctx.plugin_id)


def register_plugin(registry) -> None:
    """旧版入口（可选，用于注册扩展点）"""
    pass
```

---

## SDK 能力一览

### sdk.log - 日志

插件专用 Logger，自动添加 `[plugin:<plugin_id>]` 前缀。

```python
sdk.log.debug("调试信息")
sdk.log.info("普通日志")
sdk.log.warning("警告信息")
sdk.log.error("错误信息")
sdk.log.exception("异常信息（带堆栈）")
```

### sdk.env - 环境信息

只读访问主系统环境信息。

```python
sdk.env.app_name      # "VabHub"
sdk.env.app_version   # "1.0.0"
sdk.env.base_url      # "http://localhost:8092"
sdk.env.plugin_id     # 当前插件 ID
sdk.env.plugin_name   # 当前插件显示名称
sdk.env.debug         # 是否调试模式
```

### sdk.paths - 路径辅助

获取插件专属目录路径。

```python
sdk.paths.data_dir    # 插件数据目录（持久化存储）
sdk.paths.cache_dir   # 插件缓存目录
sdk.paths.log_dir     # 插件日志目录

# 获取配置文件路径
config_path = sdk.paths.config_path("settings.json")
```

### sdk.http - HTTP 客户端

封装 httpx，提供统一的 UA、超时、代理设置。

```python
# GET 请求
response = await sdk.http.get("https://api.example.com/data")
data = response.json()

# POST 请求
response = await sdk.http.post(
    "https://api.example.com/submit",
    json={"key": "value"}
)

# 自定义超时
response = await sdk.http.get(url, timeout=60.0)
```

### sdk.notify - 通知客户端

向用户发送系统通知。

```python
# 发送通知给单个用户
await sdk.notify.send(
    user_id=1,
    title="任务完成",
    message="您的任务已处理完成",
    payload={"task_id": 123}
)

# 发送通知给多个用户
await sdk.notify.send_to_users(
    user_ids=[1, 2, 3],
    title="系统公告",
    message="新功能已上线！"
)
```

---

## 插件权限声明（sdk_permissions）

> **PLUGIN-SDK-2 新增**

插件需要在 `plugin.json` 中声明所需的 SDK 权限，未声明的能力调用时会被 SDK 拒绝。

### 权限声明示例

```json
{
  "id": "vabhub.my_plugin",
  "display_name": "我的插件",
  "version": "1.0.0",
  "sdk_permissions": [
    "download.write",
    "media.read",
    "cloud115.task"
  ],
  "backend": {
    "entry_module": "my_plugin.main"
  }
}
```

### 可用权限列表

| 权限 ID | 说明 | 安全级别 |
|---------|------|----------|
| `download.read` | 查询下载任务状态 | 安全 |
| `download.write` | 创建下载任务 | ⚠️ 危险 |
| `media.read` | 查询媒体库（电影/电视/有声书等） | 安全 |
| `cloud115.read` | 读取 115 目录信息 | 安全 |
| `cloud115.task` | 创建 115 离线任务 | ⚠️ 危险 |

**注意**：
- 未声明权限时调用会抛出 `PermissionError` 异常
- 危险权限会在插件管理 UI 中以警告色显示
- 基础能力（log/http/notify/事件）无需声明权限

---

## 宿主服务封装

> **PLUGIN-SDK-2 新增**

除了基础能力外，SDK 还提供对主系统核心服务的封装访问。

### sdk.download - 下载服务

需要权限：`download.read` / `download.write`

```python
# 创建下载任务（需要 download.write）
task_id = await sdk.download.add_task(
    url="https://example.com/file.zip",
    title="My Download",
    media_type="other"
)

# 查询任务状态（需要 download.read）
task = await sdk.download.get_task(task_id)
print(f"Status: {task['status']}, Progress: {task['progress']}%")

# 列出下载任务
tasks = await sdk.download.list_tasks(status="downloading", limit=10)
```

### sdk.media - 媒体库查询

需要权限：`media.read`

```python
# 检查电影是否已入库
exists = await sdk.media.has_movie(tmdb_id=550)
exists = await sdk.media.has_movie(title="Fight Club", year=1999)

# 检查电视剧是否已入库
exists = await sdk.media.has_tv(tmdb_id=1399)  # Game of Thrones

# 检查有声书是否已入库
exists = await sdk.media.has_audiobook(title="三体")

# 检查漫画是否已入库
exists = await sdk.media.has_manga(title="海贼王")

# 搜索媒体库
results = await sdk.media.search_media("复仇者", media_type="movie", limit=10)
```

### sdk.cloud115 - 115 云存储

需要权限：`cloud115.task` / `cloud115.read`

```python
# 检查 115 是否可用（无需权限）
if await sdk.cloud115.is_available():
    # 添加离线任务（需要 cloud115.task）
    task_id = await sdk.cloud115.add_offline_task(
        "magnet:?xt=urn:btih:..."
    )
    
    # 列出目录（需要 cloud115.read）
    files = await sdk.cloud115.list_dir("/downloads")
    
    # 获取存储空间信息
    info = await sdk.cloud115.get_storage_info()
```

---

## 综合示例

监听漫画更新事件，检查媒体库，触发下载：

```python
from typing import Any
from app.plugin_sdk.context import PluginContext
from app.plugin_sdk.api import VabHubSDK
from app.plugin_sdk.events import EventBus, EventType


def setup_plugin(ctx: PluginContext, bus: EventBus, sdk: VabHubSDK) -> None:
    sdk.log.info("订阅插件已加载")
    
    async def on_manga_updated(event: EventType, payload: dict[str, Any]) -> None:
        title = payload.get("series_title", "")
        sdk.log.info(f"漫画更新: {title}")
        
        # 检查是否已有对应电影/动画
        if await sdk.media.has_movie(title=title):
            sdk.log.info(f"媒体库已有: {title}")
            return
        
        # 115 可用时添加离线任务（示例）
        if await sdk.cloud115.is_available():
            # 实际使用时需要先获取下载链接
            sdk.log.info(f"可以触发 115 下载: {title}")
    
    bus.subscribe(EventType.MANGA_UPDATED, on_manga_updated, source=ctx.plugin_id)
```

对应的 `plugin.json`：

```json
{
  "id": "vabhub.subscription_helper",
  "display_name": "订阅助手",
  "version": "1.0.0",
  "sdk_permissions": [
    "media.read",
    "cloud115.task"
  ],
  "backend": {
    "entry_module": "subscription_helper.main"
  }
}
```

---

## 事件系统

### EventType 事件类型

v1 支持的事件类型：

| 事件类型 | 说明 | payload 字段 |
|---------|------|-------------|
| `MANGA_UPDATED` | 漫画系列更新 | `series_id`, `series_title`, `new_chapters`, `latest_chapter_id`, `user_id` |
| `MANGA_SYNC_FAILED` | 漫画同步失败 | `series_id`, `series_title`, `error_message` |
| `AUDIOBOOK_TTS_FINISHED` | TTS 任务完成 | `job_id`, `ebook_id`, `ebook_title`, `audiobook_id`, `user_id` |
| `AUDIOBOOK_TTS_FAILED` | TTS 任务失败 | `job_id`, `ebook_id`, `error_message` |
| `AUDIOBOOK_READY` | 有声书就绪 | `audiobook_id`, `audiobook_title`, `source_type`, `user_id` |
| `DOWNLOAD_COMPLETED` | 下载完成 | `task_id`, `filename`, `path` |
| `DOWNLOAD_FAILED` | 下载失败 | `task_id`, `error_message` |
| `MUSIC_CHART_UPDATED` | 音乐榜单更新 | `chart_id`, `new_tracks` |
| `MUSIC_TRACKS_READY` | 音乐就绪 | `track_ids` |
| `PLUGIN_LOADED` | 插件加载完成 | `plugin_id`, `plugin_name`, `version` |
| `PLUGIN_UNLOADING` | 插件即将卸载 | `plugin_id`, `plugin_name` |
| `SYSTEM_STARTUP` | 系统启动 | - |
| `SYSTEM_SHUTDOWN` | 系统关闭 | - |

### 订阅事件

```python
from app.plugin_sdk.events import EventType

async def on_event(event: EventType, payload: dict[str, Any]) -> None:
    # 处理事件
    # payload 中包含事件数据和元数据：
    # - _event_type: 事件类型
    # - _event_time: 事件时间 (ISO 格式)
    # - _event_source: 事件来源
    pass

# 订阅事件（推荐指定 source 以便自动清理）
bus.subscribe(EventType.MANGA_UPDATED, on_event, source=ctx.plugin_id)
```

### 取消订阅

```python
# 取消单个订阅
bus.unsubscribe(EventType.MANGA_UPDATED, on_event)

# 取消插件的所有订阅（插件卸载时自动调用）
bus.unsubscribe_all_from_source(ctx.plugin_id)
```

### 发布事件（高级）

插件也可以发布自定义事件：

```python
from app.plugin_sdk.events import publish_event, EventType

await publish_event(
    EventType.SYSTEM_STARTUP,  # 或自定义事件类型
    {"custom_data": "value"},
    source=ctx.plugin_id
)
```

---

## 最佳实践

### 1. 事件处理器保持快速返回

事件处理器应该快速返回，不要在其中执行长时间阻塞操作。

```python
# ❌ 错误：在 handler 中执行长时间操作
async def on_event(event, payload):
    await long_running_task()  # 会阻塞其他 handler

# ✅ 正确：启动后台任务
import asyncio

async def on_event(event, payload):
    asyncio.create_task(long_running_task())  # 不阻塞
```

### 2. 使用 source 参数便于清理

订阅事件时始终指定 `source` 参数，这样插件卸载时会自动清理订阅。

```python
# ✅ 推荐
bus.subscribe(EventType.MANGA_UPDATED, handler, source=ctx.plugin_id)

# ❌ 不推荐（卸载时无法自动清理）
bus.subscribe(EventType.MANGA_UPDATED, handler)
```

### 3. 异常处理

SDK 会捕获事件处理器中的异常，但建议在关键位置添加异常处理：

```python
async def on_event(event, payload):
    try:
        # 业务逻辑
        pass
    except Exception as e:
        sdk.log.error(f"处理事件失败: {e}")
```

### 4. 数据持久化

使用 `sdk.paths.data_dir` 存储需要持久化的数据：

```python
import json

config_path = sdk.paths.config_path("settings.json")

# 读取配置
if config_path.exists():
    with open(config_path) as f:
        config = json.load(f)

# 保存配置
with open(config_path, "w") as f:
    json.dump(config, f, indent=2)
```

---

## 插件配置系统

> **PLUGIN-UX-3 新增**

插件可以声明配置 Schema，由前端自动渲染配置表单，配置数据统一存储。

### 声明配置 Schema

在 `plugin.json` 中添加 `config_schema` 字段：

```json
{
  "id": "vabhub.my_plugin",
  "display_name": "我的插件",
  "version": "1.0.0",
  "config_schema": {
    "type": "object",
    "properties": {
      "enabled": {
        "type": "boolean",
        "title": "启用",
        "default": true
      },
      "api_key": {
        "type": "string",
        "title": "API Key",
        "description": "第三方服务的 API 密钥"
      },
      "max_items": {
        "type": "integer",
        "title": "最大处理数",
        "minimum": 1,
        "maximum": 100,
        "default": 10
      },
      "mode": {
        "type": "string",
        "title": "运行模式",
        "enum": ["auto", "manual", "scheduled"]
      }
    },
    "required": ["enabled"]
  }
}
```

### 支持的字段类型

| 类型 | 渲染控件 | 支持属性 |
|------|---------|---------|
| `string` | 文本框 | `title`, `description`, `default`, `enum` |
| `boolean` | 开关 | `title`, `description`, `default` |
| `integer` / `number` | 数字输入框 | `title`, `description`, `default`, `minimum`, `maximum` |
| `array` | 多选标签 | `title`, `description` |

### 读取配置

```python
def setup_plugin(ctx, bus, sdk):
    async def init():
        # 获取完整配置
        config = await sdk.config.get()
        api_key = config.get("api_key", "")
        
        # 获取单个配置项
        max_items = await sdk.config.get_value("max_items", default=10)
        
        sdk.log.info(f"已加载配置: max_items={max_items}")
    
    asyncio.create_task(init())
```

---

## Dashboard 系统

> **PLUGIN-UX-3 新增**

插件可以提供 Dashboard，由前端自动渲染展示界面。

### 实现 get_dashboard

```python
from app.plugin_sdk import VabHubSDK
from app.schemas.plugin import PluginDashboardSchema, PluginDashboardWidget, PluginDashboardWidgetType


def get_dashboard(sdk: VabHubSDK) -> PluginDashboardSchema:
    """返回插件 Dashboard"""
    return PluginDashboardSchema(
        widgets=[
            # 统计卡片
            PluginDashboardWidget(
                id="task_count",
                type=PluginDashboardWidgetType.STAT_CARD,
                title="处理任务数",
                value="42",
                unit="个",
                icon="mdi-checkbox-marked-circle",
                color="success",
            ),
            # 文本说明
            PluginDashboardWidget(
                id="readme",
                type=PluginDashboardWidgetType.TEXT,
                title="使用说明",
                markdown="这是一个示例插件。\n\n支持多行文本。",
            ),
            # 操作按钮
            PluginDashboardWidget(
                id="run_task",
                type=PluginDashboardWidgetType.ACTION_BUTTON,
                title="手动执行",
                description="点击立即执行一次任务",
                action_api="/api/plugin/vabhub.my_plugin/run",
                action_method="POST",
                action_label="执行",
                icon="mdi-play",
                color="primary",
            ),
        ]
    )
```

### Widget 类型

| 类型 | 说明 | 必填属性 |
|------|------|---------|
| `stat_card` | 统计卡片 | `value`, `title` |
| `table` | 数据表格 | `columns`, `rows` |
| `text` | 文本/Markdown | `markdown` |
| `action_button` | 操作按钮 | `action_api`, `action_label` |

---

## 插件对外 API

> **PLUGIN-UX-3 新增**

插件可以注册自己的 HTTP API，路径为 `/api/plugin/{plugin_id}/{path}`。

### 实现 get_routes

```python
from app.plugin_sdk import VabHubSDK, PluginRoute


def get_routes(sdk: VabHubSDK) -> list[PluginRoute]:
    """返回插件 API 路由"""
    
    async def hello_handler(ctx, body, sdk):
        """
        处理函数签名：
        - ctx: 包含 request, user_id, username, session
        - body: 请求体（POST/PUT）或查询参数（GET）
        - sdk: VabHubSDK 实例
        """
        return {
            "message": "Hello from plugin!",
            "user": ctx["username"],
        }
    
    async def run_task_handler(ctx, body, sdk):
        # 读取配置
        config = await sdk.config.get()
        max_items = config.get("max_items", 10)
        
        # 执行业务逻辑
        sdk.log.info(f"执行任务: max_items={max_items}")
        
        return {"success": True, "processed": max_items}
    
    return [
        PluginRoute(
            path="hello",
            method="GET",
            summary="Say hello",
            handler=hello_handler,
        ),
        PluginRoute(
            path="run",
            method="POST",
            summary="执行任务",
            handler=run_task_handler,
        ),
    ]
```

### 调用示例

```bash
# GET 请求
curl -H "Authorization: Bearer <token>" \
  http://localhost:8092/api/plugin/vabhub.my_plugin/hello

# POST 请求
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"param": "value"}' \
  http://localhost:8092/api/plugin/vabhub.my_plugin/run
```

### 权限说明

- 默认仅允许 **管理员** 调用插件 API
- 未来版本可能支持细粒度权限控制

---

## 与旧方式的区别

### 旧方式：register_plugin

```python
def register_plugin(registry):
    # 注册搜索提供者、Bot 命令等
    registry.register_search_provider(plugin_id, provider)
```

### 新方式：setup_plugin

```python
def setup_plugin(ctx: PluginContext, bus: EventBus, sdk: VabHubSDK):
    # 获得完整的 SDK 能力
    sdk.log.info("插件已加载")
    bus.subscribe(EventType.MANGA_UPDATED, handler, source=ctx.plugin_id)
```

### 兼容性

- 两种方式可以**同时存在**
- `register_plugin` 先于 `setup_plugin` 调用
- 至少实现其中一个，否则插件会被标记为 BROKEN

---

## 版本兼容策略

- **v1 保证**：`setup_plugin` 签名和 SDK 核心接口不会随意 breaking
- **新能力**：通过版本号和文档发布，旧插件不受影响
- **废弃提示**：如有接口废弃，会提前在文档中标注 `@deprecated`

### SDK 版本检查

```python
from app.plugin_sdk import __version__ as sdk_version

def setup_plugin(ctx, bus, sdk):
    sdk.log.info(f"SDK 版本: {sdk_version}")
```

---

## 安全与监控 (PLUGIN-SAFETY-1)

### 概述

VabHub SDK 提供了完整的安全与监控体系，确保插件系统的稳定性和可观测性：

- **错误隔离**：插件异常不会影响系统稳定性
- **自动隔离**：频繁出错的插件会被自动隔离
- **审计日志**：记录插件的关键操作
- **细粒度权限**：精确控制插件访问权限
- **健康监控**：实时监控插件状态

### 权限系统

#### 细粒度权限 (PLUGIN-SAFETY-1)

SDK 支持细粒度权限控制，替代原有的粗粒度权限：

```json
{
  "sdk_permissions": [
    "download.add",        // 创建下载任务（替代 download.write）
    "download.read",       // 查询下载状态
    "cloud115.add_offline", // 创建115离线任务（替代 cloud115.task）
    "cloud115.read",       // 读取115目录
    "media.read",          // 查询媒体库
    "tts.control"          // 控制TTS队列（预留）
  ]
}
```

#### 权限迁移指南

**旧权限 → 新权限映射：**

```json
// 旧版本（已弃用但仍然支持）
{
  "sdk_permissions": ["download.write", "cloud115.task"]
}

// 新版本推荐
{
  "sdk_permissions": ["download.add", "download.read", "cloud115.add_offline", "cloud115.read"]
}
```

**代码示例：**

```python
def setup_plugin(ctx: PluginContext, bus: EventBus, sdk: VabHubSDK):
    # 检查权限
    if sdk.has_permission(PluginCapability.DOWNLOAD_ADD):
        task_id = await sdk.download.add_task(url, title="My Download")
    
    # 审计日志自动记录，无需手动调用
```

### 错误处理与隔离

#### 自动错误上报

插件运行时异常会自动上报到监控系统：

```python
# 事件处理器中的异常会被自动捕获
async def on_manga_updated(event, payload):
    # 如果这里抛出异常，会自动上报并可能触发隔离
    sdk.log.info("Processing manga update")
    # ... 业务逻辑
```

#### 插件隔离机制

当插件错误次数超过阈值时，会被自动隔离：

- **隔离阈值**：默认 5 次错误/小时
- **隔离效果**：插件的事件处理器被跳过，但插件仍保持加载状态
- **恢复方式**：管理员手动重置或等待自动清理

```python
# 检查插件是否被隔离（调试用）
from app.services.plugin_registry import PluginRegistry

registry = PluginRegistry()
if registry.is_plugin_quarantined("my_plugin"):
    sdk.log.warning("Plugin is quarantined")
```

### 审计日志

#### 自动审计

SDK 会自动记录关键操作的审计日志：

```python
# 以下操作会自动记录审计日志：
await sdk.download.add_task(url, title="Test")     # 记录 "download.add_task"
await sdk.cloud115.add_offline_task(url)           # 记录 "cloud115.add_offline_task"
```

#### 审计日志内容

审计日志包含以下信息：

```json
{
  "plugin_id": "my_plugin",
  "action": "download.add_task",
  "payload": {
    "url": "https://example.com/file.zip",
    "title": "Test Download",
    "media_type": "other"
  },
  "created_at": "2024-11-20T10:30:00Z"
}
```

### 健康监控

#### 插件状态字段

插件模型包含健康状态字段：

```python
# Plugin 模型新增字段
{
  "last_error_at": "2024-11-20T10:30:00Z",  # 最后错误时间
  "error_count": 3,                          # 错误计数
  "is_quarantined": false                    # 是否被隔离
}
```

#### 管理员操作

```python
# 重置插件错误状态
from app.services.plugin_monitor_service import PluginMonitorService

async def reset_plugin_errors(plugin_id: str):
    async for session in get_async_session():
        success = await PluginMonitorService.reset_errors(session, plugin_id)
        if success:
            print(f"Plugin {plugin_id} errors reset")
```

### 最佳实践

#### 1. 权限声明

```json
{
  "sdk_permissions": [
    "download.add",
    "download.read"
  ]
}
```

#### 2. 错误处理

```python
async def safe_operation():
    try:
        # 可能失败的操作
        result = await sdk.download.add_task(url)
        return result
    except Exception as e:
        sdk.log.error(f"Operation failed: {e}")
        # 不要让异常传播到事件系统
        return None
```

#### 3. 资源清理

```python
def setup_plugin(ctx: PluginContext, bus: EventBus, sdk: VabHubSDK):
    # 注册资源
    cleanup_handler = CleanupHandler()
    
    # 插件卸载时清理
    async def cleanup():
        await cleanup_handler.cleanup()
    
    return cleanup
```

### 管理员指南

#### 监控插件健康

```python
# 查看所有插件状态
from app.services.plugin_service import get_enabled_plugins

async def check_plugin_health():
    async for session in get_async_session():
        plugins = await get_enabled_plugins(session)
        for plugin in plugins:
            status = "🟢 正常" if not plugin.is_quarantined else "🔴 隔离"
            print(f"{plugin.name}: {status} (错误: {plugin.error_count})")
```

#### 查询审计日志

```python
# 查询特定插件的审计日志
from app.models.plugin_audit import PluginAuditLog
from sqlalchemy import select

async def get_plugin_audit_logs(plugin_id: str, limit: int = 100):
    async for session in get_async_session():
        stmt = (
            select(PluginAuditLog)
            .where(PluginAuditLog.plugin_id == plugin_id)
            .order_by(PluginAuditLog.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
```

---

## 参考资料

- [DEV_SDK_OVERVIEW.md](./DEV_SDK_OVERVIEW.md) - 插件系统总体架构
- [DEV_SDK_QUICKSTART_HELLO_PLUGIN.md](./DEV_SDK_QUICKSTART_HELLO_PLUGIN.md) - 快速入门教程
- [PLUGIN_HUB_OVERVIEW.md](./PLUGIN_HUB_OVERVIEW.md) - Plugin Hub 使用指南

---

*最后更新：2024-11 (PLUGIN-SAFETY-1)*
