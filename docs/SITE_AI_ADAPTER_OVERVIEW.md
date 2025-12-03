# 站点 AI 适配模块概览

## 1. 模块简介

站点 AI 适配模块是 VabHub 的一个辅助功能模块，负责**自动分析 PT 站点结构并生成适配配置**。

### 核心功能

1. **自动抓取站点 HTML**
   - 登录页 HTML
   - 种子列表页 HTML
   - 种子详情页 HTML

2. **调用外部 LLM 服务**
   - 将 HTML 样本发送到部署在 Cloudflare Pages 上的 LLM 适配服务
   - 获取结构化的站点适配配置

3. **生成适配配置**
   - 搜索接口配置（URL、方法、参数等）
   - 详情页选择器（标题、大小、做种数等）
   - HR 规则（触发条件、严重性等）
   - 登录表单配置（选择器、字段映射等）
   - 分类映射等

4. **缓存配置到数据库**
   - 将生成的配置保存到 `ai_site_adapters` 表
   - 以 `site_id` 为主键，支持后续查询和使用

### 设计特点

- **后台自动分析**：站点创建/更新后自动触发，不阻塞主流程
- **可手动刷新**：提供管理 API 支持手动重新分析
- **只负责生成配置**：当前版本仅生成配置，不直接控制下载、删源等操作
- **无 API Key 泄露风险**：所有 LLM 调用逻辑在独立的 Cloudflare Pages Function 中完成，VabHub 代码中不包含任何明文 API Key

## 2. 整体架构

### 调用链路

```
用户在 WebUI 创建/更新站点
    ↓
FastAPI POST /api/sites/ 或 PUT /api/sites/{site_id}
    ↓
SiteService.create_site() 或 SiteService.update_site()
    ↓
事务提交成功，站点对象已刷新
    ↓
BackgroundTasks.add_task(analyze_in_background, site_id)
    ↓
[后台任务] analyze_in_background(site_id)
    ↓
创建新的数据库会话
    ↓
maybe_auto_analyze_site(site_id, new_db)
    ↓
检查 AI_ADAPTER_ENABLED 开关
    ↓
analyze_and_save_for_site(site_id, db)
    ↓
┌─────────────────────────────────────┐
│ 1. 从数据库加载站点信息              │
│    - site_id, name, url, cookie      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. 使用 HTTP 客户端抓取 HTML         │
│    - 登录页（尝试多个常见路径）      │
│    - 列表页（torrents.php 等）      │
│    - 详情页（details.php?id=1 等）  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. 调用 Cloudflare Pages API         │
│    POST AI_ADAPTER_ENDPOINT          │
│    - 发送 site_id, engine, HTML 样本 │
│    - 接收 JSON 格式的适配配置        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 4. 解析并验证配置                    │
│    - 使用 AISiteAdapterConfig 验证   │
│    - 转换为 SiteAIAdapterResult     │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 5. 保存到数据库                      │
│    - 检查 ai_site_adapters 表        │
│    - 存在则更新，不存在则插入        │
│    - 记录 config_json, raw_output    │
└─────────────────────────────────────┘
    ↓
返回结果（或 None，失败时只记录日志）
```

### 后续使用场景

其他模块（如 Local Intel、External Indexer）可以在后续版本中：

- 读取 `ai_site_adapters` 表中的配置
- 根据配置中的 `search` 部分构建搜索请求
- 使用 `detail.selectors` 解析种子详情页
- 应用 `hr.rules` 进行 HR 检测
- 使用 `auth` 配置处理登录流程

## 3. 相关代码位置说明

### 核心模块

**路径：** `backend/app/core/site_ai_adapter/`

#### `models.py`

定义数据模型：

- **`AISearchConfig`**：搜索接口配置
  - `url`：搜索接口 URL
  - `method`：HTTP 方法（GET/POST）
  - `query_params`：查询参数映射
  - `form_data`：表单数据（POST 时使用）
  - `encoding`：字符编码

- **`AIDetailSelectors`**：详情页 CSS 选择器
  - `title`、`size`、`seeds`、`peers`、`download_link` 等

- **`AIDetailConfig`**：详情页配置
  - `url`：详情页 URL 模板
  - `selectors`：AIDetailSelectors 实例

- **`AIHRRule`**：HR 规则定义
  - `pattern`：匹配模式（正则或关键词）
  - `location`：规则位置
  - `severity`：严重性（low/medium/high）

- **`AIHRConfig`**：HR 配置集合
  - `enabled`：是否启用 HR 检测
  - `rules`：规则列表

- **`AIAuthConfig`**：认证配置
  - `login_url`：登录页 URL
  - `selectors`：表单选择器
  - `cookie_names`：Cookie 名称列表

- **`AISiteAdapterConfig`**：完整的站点适配配置
  - `search`：AISearchConfig
  - `detail`：AIDetailConfig
  - `hr`：AIHRConfig
  - `auth`：AIAuthConfig
  - `categories`：分类映射字典

- **`SiteAIAdapterResult`**：一次分析的结果封装
  - `site_id`：站点 ID
  - `engine`：站点框架类型（如 "nexusphp"）
  - `config`：AISiteAdapterConfig 实例
  - `raw_model_output`：LLM 原始输出（用于调试）
  - `created_at`：创建时间

#### `client.py`

Cloudflare Pages API 客户端封装：

- **`call_cf_adapter()`**：调用外部 LLM 适配服务
  - 读取 `AI_ADAPTER_ENDPOINT`、`AI_ADAPTER_TIMEOUT_SECONDS` 等配置
  - 截断过长的 HTML（根据 `AI_ADAPTER_MAX_HTML_BYTES`）
  - 发送 HTTP POST 请求
  - 解析响应并验证为 `AISiteAdapterConfig`
  - 处理超时、HTTP 错误等异常

- **`AIAdapterClientError`**：自定义异常类

#### `service.py`

业务逻辑层：

- **`analyze_and_save_for_site(site_id, db)`**：主流程函数
  - 从数据库加载站点信息
  - 使用 `httpx.AsyncClient` 抓取 HTML
  - 调用 `call_cf_adapter()` 获取配置
  - 保存到 `ai_site_adapters` 表（插入或更新）

- **`get_site_adapter_config(site_id, db)`**：读取已缓存的配置
  - 从 `ai_site_adapters` 表查询
  - 返回配置字典或 None

- **`maybe_auto_analyze_site(site_id, db)`**：安全入口函数
  - 检查 `AI_ADAPTER_ENABLED` 开关
  - 调用 `analyze_and_save_for_site()`
  - 捕获所有异常，只记录日志，不抛出

#### `__init__.py`

模块导出：

- `analyze_and_save_for_site`
- `get_site_adapter_config`
- `maybe_auto_analyze_site`
- `AISiteAdapterConfig`
- `SiteAIAdapterResult`

### 数据库模型

**路径：** `backend/app/models/ai_site_adapter.py`

- **`AISiteAdapter`**：SQLAlchemy 模型
  - `id`：主键（自增）
  - `site_id`：站点 ID（字符串，唯一索引）
  - `engine`：站点框架类型
  - `config_json`：配置 JSON（TEXT/JSONB）
  - `raw_model_output`：原始 LLM 输出（TEXT，可选）
  - `version`：配置版本号（默认 1）
  - `created_at`：创建时间
  - `updated_at`：更新时间

**表名：** `ai_site_adapters`

### 迁移脚本

**路径：** `backend/scripts/migrate_ai_site_adapter_schema.py`

- 创建 `ai_site_adapters` 表
- 创建 `site_id` 索引
- 支持 SQLite 和 PostgreSQL

**执行方式：**
```bash
cd backend
python scripts/migrate_ai_site_adapter_schema.py
```

### 站点创建/更新入口

**路径：** `backend/app/api/site.py`

- **`create_site(background_tasks, ...)`**
  - 在站点创建成功后，通过 `BackgroundTasks` 异步调用 `analyze_in_background(site_id)`
  - 后台任务中创建新的数据库会话，调用 `maybe_auto_analyze_site()`

- **`update_site(background_tasks, ...)`**
  - 在站点更新成功后，同样触发后台分析任务

### 管理 API

**路径：** `backend/app/api/site_ai_adapter.py`

- **`POST /api/admin/site-ai-adapter/refresh/{site_id}`**
  - 手动触发站点适配配置刷新
  - 返回分析结果（成功/失败）

- **`GET /api/admin/site-ai-adapter/config/{site_id}`**
  - 查询已缓存的适配配置
  - 返回配置 JSON

### 配置项

**路径：** `backend/app/core/config.py`

所有配置项均通过环境变量读取，支持 `.env` 文件：

- **`AI_ADAPTER_ENABLED`**（第 328 行）
- **`AI_ADAPTER_ENDPOINT`**（第 330-333 行）
- **`AI_ADAPTER_TIMEOUT_SECONDS`**（第 335 行）
- **`AI_ADAPTER_MAX_HTML_BYTES`**（第 337 行）

## 4. 配置与环境变量说明

### AI_ADAPTER_ENABLED

- **类型：** 布尔值
- **默认值：** `true`
- **作用：** 总开关，控制是否启用站点 AI 适配功能
- **行为：**
  - `true`：站点创建/更新后自动触发分析
  - `false`：所有自动分析逻辑短路，`maybe_auto_analyze_site()` 直接返回，只记录 DEBUG 日志

### AI_ADAPTER_ENDPOINT

- **类型：** 字符串（URL）
- **默认值：** `https://vabhub-cf-adapter.pages.dev/api/site-adapter`
- **作用：** 指定外部 LLM 适配服务的 HTTP 端点
- **说明：**
  - 该端点应部署在 Cloudflare Pages Functions 上
  - 接收 POST 请求，请求体包含 `site_id`、`engine`、`samples`（HTML 样本）等
  - 返回 JSON 格式的站点适配配置

### AI_ADAPTER_TIMEOUT_SECONDS

- **类型：** 整数（秒）
- **默认值：** `30`
- **作用：** 设置调用 LLM 服务的 HTTP 请求超时时间
- **建议：**
  - LLM 响应较慢时，可适当增加（如 60 秒）
  - 网络不稳定时，可适当减少（如 15 秒）

### AI_ADAPTER_MAX_HTML_BYTES

- **类型：** 整数（字节数）
- **默认值：** `100000`（约 100 KB）
- **作用：** 限制单次发送给 LLM 的 HTML 总大小
- **说明：**
  - 避免 HTML 过长导致 LLM token 消耗过大
  - 超过限制的 HTML 会被截断，并记录 WARNING 日志
  - 如果站点页面较大，可适当增加（如 200000），但需注意 LLM 服务的 token 限制

### 配置示例

在 `.env` 文件中：

```bash
# 启用 AI 适配
AI_ADAPTER_ENABLED=true

# 自定义端点（如果部署在其他位置）
AI_ADAPTER_ENDPOINT=https://your-custom-endpoint.com/api/site-adapter

# 超时时间（秒）
AI_ADAPTER_TIMEOUT_SECONDS=30

# HTML 最大字节数
AI_ADAPTER_MAX_HTML_BYTES=100000
```

## 5. 触发时机 & 使用方式

### 自动触发

当用户通过 API 或 WebUI 执行以下操作时，会自动触发 AI 适配分析：

1. **创建新站点**
   - API：`POST /api/sites/`
   - 流程：站点创建成功 → 后台任务启动 → 异步分析

2. **更新站点**
   - API：`PUT /api/sites/{site_id}`
   - 流程：站点更新成功 → 后台任务启动 → 异步分析（覆盖旧配置）

**特点：**
- 分析过程与用户请求解耦，不会拖慢接口响应
- 即使分析失败，也不影响站点创建/更新的成功返回
- 所有错误只记录在日志中

### 手动触发

#### 刷新站点适配配置

**API：** `POST /api/admin/site-ai-adapter/refresh/{site_id}`

**用途：**
- 调试适配配置
- 站点改版后重新适配
- 修复之前分析失败的站点

**示例：**
```bash
curl -X POST http://localhost:8092/api/admin/site-ai-adapter/refresh/1
```

**响应：**
```json
{
  "success": true,
  "message": "站点适配配置分析成功",
  "data": {
    "ok": true,
    "site_id": "1",
    "engine": "nexusphp",
    "created_at": "2025-11-21T03:00:00",
    "config": {
      "search": { ... },
      "detail": { ... },
      "hr": { ... },
      "auth": { ... }
    }
  }
}
```

#### 查看已缓存的配置

**API：** `GET /api/admin/site-ai-adapter/config/{site_id}`

**用途：**
- 查看当前数据库中缓存的适配配置
- 验证配置是否正确生成

**示例：**
```bash
curl http://localhost:8092/api/admin/site-ai-adapter/config/1
```

**响应：**
```json
{
  "success": true,
  "message": "获取站点适配配置成功",
  "data": {
    "site_id": "1",
    "config": {
      "search": { ... },
      "detail": { ... },
      ...
    }
  }
}
```

## 6. 错误处理与降级策略

### 设计原则

所有错误处理都遵循**优雅降级**原则，确保 AI 适配失败不会影响主业务流程。

### 具体场景

#### 场景 1：AI 适配功能未启用

- **条件：** `AI_ADAPTER_ENABLED = false`
- **行为：**
  - `maybe_auto_analyze_site()` 直接返回 `None`
  - 只记录一条 DEBUG 日志：`"AI 适配功能已禁用，跳过自动分析"`
  - 站点创建/更新流程正常完成

#### 场景 2：HTML 抓取失败

- **条件：** 无法访问站点页面（网络错误、站点不可达等）
- **行为：**
  - `analyze_and_save_for_site()` 捕获异常
  - 记录 ERROR 日志，包含 `site_id` 和错误详情
  - 返回 `None`，不抛出异常
  - 站点创建/更新流程正常完成

#### 场景 3：Cloudflare Pages / LLM 服务不可用

- **条件：** 外部服务挂掉、超时、返回错误等
- **行为：**
  - `call_cf_adapter()` 捕获 `httpx.TimeoutException`、`httpx.HTTPStatusError` 等
  - 记录 WARNING 或 ERROR 日志
  - 抛出 `AIAdapterClientError`，被 `maybe_auto_analyze_site()` 捕获
  - 返回 `None`，不向上传播异常
  - 站点创建/更新流程正常完成

#### 场景 4：配置解析失败

- **条件：** LLM 返回的 JSON 格式错误、缺少必需字段等
- **行为：**
  - `call_cf_adapter()` 在验证 `AISiteAdapterConfig` 时捕获异常
  - 记录 ERROR 日志，包含原始响应内容（用于调试）
  - 抛出 `AIAdapterClientError`
  - 被上层捕获，返回 `None`

#### 场景 5：数据库保存失败

- **条件：** 数据库连接错误、约束冲突等
- **行为：**
  - `analyze_and_save_for_site()` 捕获异常
  - 执行 `db.rollback()`
  - 记录 ERROR 日志
  - 返回 `None`

### 日志级别

- **DEBUG：** 功能未启用、正常流程信息
- **INFO：** 开始分析、分析成功
- **WARNING：** HTML 截断、非关键错误
- **ERROR：** 严重错误（网络失败、解析失败等），包含异常堆栈

### 排查建议

当 AI 适配失败时，可通过以下方式排查：

1. **检查日志**
   ```bash
   # 查看最近的错误日志
   grep "AI 适配" logs/app.log | tail -20
   ```

2. **检查配置**
   - 确认 `AI_ADAPTER_ENABLED=true`
   - 确认 `AI_ADAPTER_ENDPOINT` 正确
   - 确认站点 URL 和 Cookie 有效

3. **手动触发测试**
   ```bash
   curl -X POST http://localhost:8092/api/admin/site-ai-adapter/refresh/{site_id}
   ```

4. **查看数据库**
   ```sql
   SELECT * FROM ai_site_adapters WHERE site_id = '1';
   ```

## 7. 与其他子系统的关系

### 当前版本

站点 AI 适配模块**只负责生成并缓存配置**，不直接参与其他业务流程：

- ✅ 生成站点适配配置
- ✅ 保存到数据库
- ✅ 提供查询 API
- ❌ 不直接控制下载
- ❌ 不直接控制搜索
- ❌ 不直接控制 HR 检测

### 未来扩展方向

#### 下载/搜索模块

**潜在集成点：**
- 根据 `AISiteAdapterConfig.search` 配置自动构建搜索请求
- 使用 `detail.selectors` 解析种子详情页，提取下载链接
- 根据 `categories` 映射进行分类筛选

**示例代码（伪代码）：**
```python
# 未来可能的实现
from app.core.site_ai_adapter import get_site_adapter_config

config = await get_site_adapter_config(site_id, db)
if config:
    # 使用 AI 生成的搜索配置
    search_url = config["search"]["url"]
    params = {k: v.format(keyword=keyword) for k, v in config["search"]["query_params"].items()}
    # 发送搜索请求...
```

#### Local Intel

**潜在集成点：**
- 使用 `hr.rules` 增强 HR 检测规则
- 根据 `hr.enabled` 和 `hr.rules` 自动识别站点特定的 HR 触发条件
- 结合 Local Intel 的现有规则，形成更完善的 HR 策略

#### External Indexer

**潜在集成点：**
- 将 AI 生成的适配配置转换为 External Indexer 的站点配置格式
- 自动注册到 External Indexer 的站点注册表
- 实现"一键适配新站点"的功能

#### 站点管理页面（前端）

**潜在功能：**
- 在站点列表中显示"AI 适配状态"（已适配/未适配/适配失败）
- 展示适配配置的摘要（搜索接口、HR 规则数量等）
- 提供"重新适配"按钮，调用 `POST /api/admin/site-ai-adapter/refresh/{site_id}`
- 展示适配配置的原始 JSON（用于调试）

## 8. 注意事项

### 给未来维护者的提示

#### 1. 不要在请求主流程中直接调用 LLM

**错误示例：**
```python
# ❌ 错误：会阻塞请求
async def create_site(...):
    site = await service.create_site(...)
    result = await analyze_and_save_for_site(site.id, db)  # 阻塞！
    return site
```

**正确做法：**
```python
# ✅ 正确：使用后台任务
async def create_site(background_tasks: BackgroundTasks, ...):
    site = await service.create_site(...)
    background_tasks.add_task(analyze_in_background, site.id)
    return site
```

#### 2. 不要在代码中硬编码 API Key

**原则：**
- 所有 LLM 相关的 API Key 应配置在 Cloudflare Pages 的环境变量中
- VabHub 代码中只包含 Cloudflare Pages 的端点 URL，不包含 LLM 提供商的密钥
- 如果未来需要更换 LLM 服务（如从硅基流动换到其他提供商），只需修改 Cloudflare Pages Function 的代码和配置，VabHub 端无需改动

#### 3. 数据库会话管理

**重要：**
- 后台任务中必须创建新的数据库会话（使用 `AsyncSessionLocal()`）
- 不能使用请求中的 `db` 会话，因为请求结束后会话会被关闭
- 后台任务中的异常不应影响主请求的事务

**正确示例：**
```python
async def analyze_in_background(site_id: int):
    async with AsyncSessionLocal() as new_db:
        try:
            await maybe_auto_analyze_site(str(site_id), new_db)
        except Exception as e:
            logger.error(f"后台任务异常: {e}", exc_info=True)
```

#### 4. 站点结构大改时的处理

**场景：** 当 PT 站点进行重大改版（HTML 结构变化很大）时

**建议：**
1. 手动触发重新适配：`POST /api/admin/site-ai-adapter/refresh/{site_id}`
2. 检查生成的配置是否正确
3. 如果 LLM 生成的配置不准确，可能需要：
   - 调整发送给 LLM 的 HTML 样本（在 `service.py` 中修改抓取逻辑）
   - 或手动在数据库中修正配置 JSON

#### 5. 性能考虑

**当前实现：**
- HTML 抓取是串行的（登录页 → 列表页 → 详情页）
- 如果未来需要优化，可以考虑并发抓取

**LLM 调用：**
- 每次分析都会调用一次外部 LLM 服务
- 如果站点数量很大，建议：
  - 批量分析时添加限流（如每秒最多 1 个请求）
  - 或使用队列系统（如 Celery）进行异步处理

#### 6. 配置版本管理

**当前实现：**
- `ai_site_adapters` 表有 `version` 字段（默认 1）
- 未来如果需要支持配置升级，可以：
  - 检测配置版本
  - 如果版本过低，自动触发重新分析
  - 或在配置变更时递增版本号

#### 7. 测试建议

**单元测试：**
- 测试 `call_cf_adapter()` 的各种异常场景（超时、HTTP 错误等）
- 测试 `analyze_and_save_for_site()` 的 HTML 抓取逻辑
- Mock 外部 LLM 服务，避免真实调用

**集成测试：**
- 测试站点创建后是否正确触发后台任务
- 测试配置是否正确保存到数据库
- 测试手动刷新 API 的功能

---

**文档版本：** 1.0  
**最后更新：** 2025-11-21  
**维护者：** VabHub 开发团队

