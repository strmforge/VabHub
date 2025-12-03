# VabHub 插件开发套件（PDK）概述

## 简介

VabHub 插件开发套件（Plugin Development Kit, PDK）允许第三方开发者扩展 VabHub 的功能，包括：

- **全局搜索扩展**：添加自定义搜索源
- **Bot 命令扩展**：添加 Telegram Bot 命令
- **Workflow 扩展**：添加自动化任务

## 插件目录结构

```
plugins/
└── my-plugin/
    ├── plugin.json              # 插件清单（必需）
    ├── README.md                # 说明文档（推荐）
    └── backend/
        └── my_plugin/           # Python 包
            ├── __init__.py
            └── main.py          # 入口模块（必需）
```

## plugin.json 格式

```json
{
  "id": "vendor.plugin_name",         // 唯一标识，推荐格式：vendor.plugin_name
  "display_name": "插件显示名称",       // 在 UI 中显示的名称
  "version": "1.0.0",                  // 语义化版本号
  "description": "插件描述",            // 可选
  "author": "作者名",                   // 可选
  "homepage": "https://...",           // 可选，项目主页
  "backend": {
    "entry_module": "my_plugin.main"   // Python 入口模块路径
  },
  "frontend": {
    "entry_point": "dev:my_plugin"     // 预留，前端扩展入口
  },
  "capabilities": {
    "search_providers": ["..."],       // 声明的搜索提供者 ID
    "bot_commands": ["..."],           // 声明的 Bot 命令
    "workflows": ["..."]               // 声明的 Workflow ID
  }
}
```

## 入口函数

每个插件必须在入口模块中定义 `register_plugin` 函数：

```python
# my_plugin/main.py

def register_plugin(registry):
    """
    插件注册函数
    
    Args:
        registry: PluginRegistry 实例
    """
    plugin_id = "vendor.my_plugin"
    
    # 注册各类扩展
    registry.register_search_provider(plugin_id, MySearchProvider())
    registry.register_bot_command(plugin_id, MyBotCommand())
    registry.register_workflow(plugin_id, MyWorkflow())
```

## 扩展点接口

### SearchProvider

```python
class SearchProvider(Protocol):
    id: str  # 唯一 ID
    
    async def search(
        self,
        session: AsyncSession,
        query: str,
        scope: Optional[str] = None,
        limit: int = 10,
    ) -> Iterable[GlobalSearchItem]:
        ...
```

**示例实现：**

```python
from app.schemas.global_search import GlobalSearchItem

class MySearchProvider:
    id = "my_plugin.search"
    
    async def search(self, session, query, scope=None, limit=10):
        if "keyword" not in query.lower():
            return []
        
        return [
            GlobalSearchItem(
                media_type="plugin",
                id="result_1",
                title="搜索结果标题",
                sub_title="副标题",
                cover_url=None,
                route_name="SomeRoute",
                route_params={},
            )
        ]
```

### BotCommandExtension

```python
class BotCommandExtension(Protocol):
    command: str  # 命令名，不含斜杠
    
    async def handle(self, ctx: TelegramUpdateContext) -> None:
        ...
```

**示例实现：**

```python
class MyBotCommand:
    command = "mycommand"
    
    async def handle(self, ctx):
        await ctx.reply_text("Hello from plugin!")
```

**ctx 常用方法：**

- `ctx.reply_text(text, reply_markup=None)` - 回复文本
- `ctx.user` - 当前用户对象
- `ctx.args` - 命令参数列表
- `ctx.session` - 数据库会话

### WorkflowExtension

```python
class WorkflowExtension(Protocol):
    id: str           # 唯一 ID
    name: str         # 显示名称
    description: str  # 描述
    
    async def run(
        self,
        session: AsyncSession,
        payload: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        ...
```

**示例实现：**

```python
class MyWorkflow:
    id = "my_plugin.my_job"
    name = "我的任务"
    description = "任务描述"
    
    async def run(self, session, payload=None):
        # 执行任务逻辑
        return {"status": "completed", "data": payload}
```

## 配置

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `APP_PLUGINS_DIR` | 插件目录路径 | `plugins` |
| `APP_PLUGINS_AUTO_SCAN` | 启动时自动扫描 | `true` |
| `APP_PLUGINS_AUTO_LOAD` | 启动时自动加载 | `true` |

### Docker 挂载

```yaml
services:
  vabhub:
    volumes:
      - ./my-plugins:/app/plugins
```

## API 端点

### 插件管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/dev/plugins` | 列出所有插件 |
| POST | `/api/dev/plugins/scan` | 扫描插件目录 |
| PUT | `/api/dev/plugins/{id}/status` | 启用/禁用插件 |
| GET | `/api/dev/plugins/{id}` | 获取插件详情 |

### Workflow

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/dev/workflows` | 列出所有 Workflow |
| POST | `/api/dev/workflows/{id}/run` | 执行 Workflow |

## 调试

### 查看日志

插件加载和执行日志会输出到 VabHub 主日志，标签为 `[plugin]` 或 `[plugin-registry]`。

### 常见错误

1. **Missing register_plugin function**
   - 入口模块缺少 `register_plugin` 函数

2. **ModuleNotFoundError**
   - 入口模块路径配置错误
   - 插件的 backend 目录未正确添加到 sys.path

3. **BROKEN 状态**
   - 检查 `last_error` 字段查看具体错误
   - 修复后重新扫描

## 安全注意事项

⚠️ **重要提示**

1. 插件运行在 VabHub 同一 Python 进程中，**没有沙箱隔离**
2. 插件可以通过 `AsyncSession` 直接操作数据库
3. 只安装来自可信来源的插件
4. 建议在测试环境中先验证插件

## 相关文档

- [快速开始：HelloWorld 插件](./DEV_SDK_QUICKSTART_HELLO_PLUGIN.md)
- [示例插件源码](../plugins-example/hello-world/)
