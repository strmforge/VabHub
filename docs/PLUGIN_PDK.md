# VabHub 插件开发指南（Plugin PDK）

> 适用于希望通过 `plugins/` 目录扩展 VabHub 功能的开发者。本文介绍插件文件结构、生命周期钩子、配置读写与调试流程。

---

## 1. 目录结构

```text
VabHub/
├─ backend/
│  └─ app/core/plugins/          # 热更新与配置管理
├─ plugins/
│  ├─ __init__.py
│  ├─ example_pt_site.py         # 官方 PT 示例插件
│  └─ example_short_drama_site.py# 官方短剧样板插件
└─ docs/PLUGIN_PDK.md            # 本文档
```

- **插件文件**：放置在仓库根目录的 `plugins/`，每个插件一个 `.py` 文件。
- **命名规则**：建议使用英文小写+下划线，例如 `my_cool_plugin.py`。文件名即插件 ID。

---

## 2. 必需导出内容

每个插件都需要导出以下对象：

```python
from app.core.plugins.spec import PluginMetadata, PluginContext, PluginHooks

PLUGIN_METADATA = PluginMetadata(
    id="example_pt_site",
    name="示例 PT 站点",
    version="0.1.0",
    description="演示插件开发流程",
    author="VabHub",
    tags=["demo", "pt"],
)

def register(context: PluginContext) -> PluginHooks:
    # 初始化配置
    context.config.ensure_defaults({"enabled": True})

    def on_startup(ctx: PluginContext):
        ctx.logger.info("插件启动，当前配置：%s", ctx.config.all())

    def on_shutdown(ctx: PluginContext):
        ctx.logger.info("插件关闭")

    return PluginHooks(on_startup=on_startup, on_shutdown=on_shutdown)
```

### 2.1 `PluginMetadata`

| 字段        | 必填 | 说明                                   |
| ----------- | ---- | -------------------------------------- |
| `id`        | 是   | 插件唯一标识（建议与文件名一致）       |
| `name`      | 是   | 展示名称                               |
| `version`   | 是   | 语义化版本                              |
| `description` | 是 | 简洁描述                               |
| `author`    | 否   | 作者                                   |
| `homepage`  | 否   | 项目主页 / 仓库地址                    |
| `tags`      | 否   | 标签列表                               |

### 2.2 `register(context)`

- 在插件加载时由 VabHub 调用。
- 可进行初始化（如写入默认配置、注册事件）。
- 返回 `PluginHooks`，支持 `on_startup` / `on_shutdown` 两个可选回调。

---

## 3. PluginContext 能力

`PluginContext` 提供：

| 属性/方法          | 说明                                                                 |
| ------------------ | -------------------------------------------------------------------- |
| `logger`           | 基于 Loguru 的带有 `plugin=` 绑定的 logger。                         |
| `settings`         | 直接访问 `app.core.config.settings`，可读取全局配置。               |
| `config`           | `PluginConfigStore` 实例，提供 `all()/set()/ensure_defaults()` 等方法。 |
| `emit_event(event, payload)` | 简单事件记录辅助。                                           |

`PluginConfigStore` 默认将配置写入 `data/plugin_configs/<plugin>.json`，支持：

- `all()`：读取完整配置。
- `set(key, value)`、`set_all(dict)`：写入配置。
- `ensure_defaults(defaults)`：只在缺失时填充默认值。

---

## 4. 本地调试与热更新

1. 在根目录创建或修改 `plugins/*.py`。
2. 启动后端（`uvicorn main:app --reload` 或脚本）。
3. 访问前端「系统 > 插件管理」页面即可：
   - 查看插件状态 / 元数据；
   - 手动“重载 / 卸载”；
   - 修改 Key-Value 配置（写入 `PluginConfigStore`）。
4. 若开启「热更新」，保存文件后 Watchdog 会自动重载插件。
5. 插件日志可在后端控制台或 LogCenter 查看，日志前缀会带 `plugin=<name>`。

---

## 5. 示例插件说明

### 5.1 `example_pt_site.py`

最简示例，演示：

- 如何填写 `PLUGIN_METADATA`；
- 如何在 `register()` 中写默认配置；
- 如何在 `on_startup` / `on_shutdown` 中读取配置并输出日志。

### 5.2 `example_short_drama_site.py`

短剧垂类样板，覆盖：

- **配置结构**：`site_url / site_name / auth / category_mapping / subscription_defaults / download_defaults`，加载时会深度写入 `data/plugin_configs/example_short_drama_site.json`，方便在插件管理页面按需调整。
- **订阅辅助函数**：`create_subscription_payload()` 返回 `SubscriptionService.create_subscription()` 可直接食用的字典（自动带上 `media_type="short_drama"` 与 `short_drama_metadata`）。
- **下载辅助函数**：`create_download_payload()` 返回 `DownloadService.create_download()` 所需字段，并在 `extra_metadata.short_drama` 标记剧集跨度。
- **自测脚本联动**：`backend/scripts/test_short_drama_minimal.py` 默认会检查并重载该插件，随后自动创建订阅 / 下载 / 媒体条目，便于在 CI 或本地环境快速验证短剧闭环。

开发者可以直接复制该文件，自定义站点分类映射 / 认证字段，再结合自身 PT 站点的数据源去创建短剧订阅或触发下载。

---

## 6. 快速上手：脚手架创建插件

- 运行脚本：

  ```bash
  python backend/scripts/create_plugin.py my_pt_plugin --name "My PT Plugin"
  ```

- 根据提示修改生成的 `plugins/my_pt_plugin.py`，补充站点配置 / 订阅逻辑。
- 在 Web UI → 插件管理 中点击“重载”即可热加载新插件；若需要批量生成，可使用不同的 `--from-template`（目前支持 `plugin_pt_site`）。

脚手架会把模板 `templates/plugin_pt_site/` 渲染为可运行的骨架，自动填充 `PluginMetadata`、默认配置与基本日志，避免重复搬运示例代码。

---

## 7. REST / GraphQL 扩展（进阶）

### 7.1 register_rest

在 `PluginHooks` 中返回 `register_rest(router: APIRouter)`，即可直接向 router 上添加 FastAPI 路由。所有路由会自动挂载到 `/api/plugins/{plugin_id}/...` 命名空间下：

```python
from fastapi import APIRouter

def register(context: PluginContext) -> PluginHooks:
    def register_rest(router: APIRouter):
        @router.get("/status")
        async def status():
            return {"plugin": context.name, "enabled": context.config.get("enabled")}

    return PluginHooks(register_rest=register_rest)
```

### 7.2 register_graphql

通过 `register_graphql(builder: GraphQLSchemaBuilder)` 可以向 GraphQL Query / Mutation 注入 mixin：

```python
import strawberry
from app.core.plugins.graphql_builder import GraphQLSchemaBuilder
from app.graphql.schema import _session  # 复用已有的 session helper

class ExampleQuery:
    @strawberry.field(description="插件示例字段")
    async def plugin_echo(self, info, text: str = "hi") -> str:
        return f"[{info.context.get('request_id')}] {text}"

def register(context: PluginContext) -> PluginHooks:
    def register_graphql(builder: GraphQLSchemaBuilder):
        builder.add_query(ExampleQuery)

    return PluginHooks(register_graphql=register_graphql)
```

框架会在构建 GraphQL Schema 时自动混入这些 mixin；无需重复创建 `strawberry.Schema`。

---

## 8. 注意事项

1. **插件运行环境**与主应用共享，请避免长时间阻塞操作，必要时使用异步任务或后台线程。
2. **异常处理**：若 `register/on_startup` 抛出异常，插件会被标记为 `error`，可在 UI 中查看 `last_error`。
3. **配置格式**：当前版本为通用 JSON，前端只提供简单的键值编辑，通过 String 保存；如需结构化配置，可存储 JSON 字符串并在插件内部解析。
4. **API 扩展**：插件可在 `register` 中导入自定义模块，与现有 Service 交互（如访问 `SubscriptionService`），但请谨慎修改核心表结构。

---

## 9. 后续规划

- 提供插件模板仓库与脚手架命令；
- 支持插件注册 REST/GraphQL 扩展点；
- 维护官方插件索引，方便在 UI 中一键安装。

## 10. 插件安装与安全

1. **默认无远程安装**  
   - `PLUGIN_REMOTE_INSTALL_ENABLED=false`（默认）时，`POST /api/plugins/{id}/install` 会直接拒绝请求。  
   - 如需启用远程安装，请在部署环境中显式设置：  
     ```env
     PLUGIN_REMOTE_INSTALL_ENABLED=true
     PLUGIN_REMOTE_ALLOWED_HOSTS=["raw.githubusercontent.com","plugins.example.com"]
     ```  
     只有名单内的域名会被允许下载。

2. **注册表与下载地址**  
   - 官方插件列表位于 `templates/plugin_registry.json`，可以为每个条目提供 `download_url`。  
   - 安装接口会优先读取该地址，也可以在请求体中自定义：  
     ```json
     { "download_url": "https://example.com/my_plugin.py" }
     ```

3. **文件大小限制**  
   - `PLUGIN_INSTALL_MAX_BYTES`（默认 256 KB）用于限制单个插件文件大小，超过阈值会被拒绝。

4. **安全建议**  
   - 推荐在生产环境中先审阅插件源码，再将 `.py` 文件手动放置到 `plugins/` 目录，或者自建内部仓库存放受信任插件。  
   - 如果必须开启远程安装，请使用只读账号或代理仓库，避免直接暴露生产环境的写权限。

欢迎根据上述规范提交自定义插件或完善现有生态！如有问题，可在 Issues 中附带插件文件与日志。祝开发愉快 🎉
