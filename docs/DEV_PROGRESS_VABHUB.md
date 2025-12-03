# VabHub 开发进度与结构说明（给 AI / IDE 看）

> 本文档描述当前 VabHub 项目真实代码结构和阶段进度，  
> 方便 AI / IDE 在不了解历史聊天记录的情况下继续开发。

---

## 最近进度快照（按时间）

- 2025-11-15：在本地以 `API_BASE_URL=http://127.0.0.1:8100` 启动后端，
  `backend/scripts/quick_test.py` 与 `backend/scripts/test_functional.py` 测试通过：
  - 登录 / 创建订阅 / 订阅列表 / 仪表盘 / 基础设置等核心 API 均返回 2xx，
  - `SubscriptionService` 缺失 `_record_history` 导致的 500 错误已修复，
  - 当前可视为「核心后端 API 可用，可以在此基础上继续开发新功能」。
- 2025-11-15（追加-1）：在同样以 `API_BASE_URL=http://127.0.0.1:8100` 启动后端的前提下，依次运行：
  - `VabHub/backend/scripts/quick_test.py`
  - `VabHub/backend/scripts/test_functional.py`
  - `VabHub/backend/scripts/test_music_minimal.py`
  - `VabHub/backend/scripts/test_graphql_minimal.py`  
  结果与备注：
  - 音乐最小闭环脚本 `test_music_minimal.py` 可以正常创建音乐订阅并触发一次预览流程；
  - GraphQL 最小脚本 `test_graphql_minimal.py` 可以通过 `/graphql` 查询基础数据（最小只读 Schema 正常工作）；
  - `quick_test.py` 第一步仍打印“创建订阅异常”，通常与重复数据或账号状态相关，目前不影响其余断言；
  - 若旧数据库中 `music_subscriptions` 表缺少 `subscription_id` 列，首次创建音乐订阅时会尝试自动 `ALTER TABLE`，失败时需手工执行 `ALTER TABLE music_subscriptions ADD COLUMN subscription_id INTEGER;` 再重试；
  - 日志中仍可见 `app.api.websocket.broadcast_dashboard_update` 中 `logger` 未定义的噪声，本轮未处理，留待后续专门修复。
- 2025-11-15（追加-2）：在上述基础上进一步完善音乐与 GraphQL：
  - GraphQL Schema 中新增 `musicSubscriptions` 查询（`MusicSubscriptionType`），支持按平台筛选最近的音乐订阅；同时新增 `/music/charts/history` REST 接口与 `musicCharts` GraphQL 查询，为音乐榜单历史与更细粒度过滤提供统一数据源；
  - `backend/scripts/test_music_minimal.py` 增强，新增 `--execute` 开关：
    - 默认：走“预览”链路，仅验证音乐订阅创建与预览逻辑；
    - 加 `--execute`：触发真实自动下载，并调用 `/api/downloads/` 回查任务是否生成；
  - `DEV_PROGRESS_VABHUB.md` 已同步记录 `musicSubscriptions` 查询、`test_music_minimal.py --execute` 能力以及旧数据库缺列时的处理方式；
  - 一组完整回归测试命令为：  
    - `API_BASE_URL=http://127.0.0.1:8100 python VabHub/backend/scripts/quick_test.py`（首个“创建订阅”步骤仍提示异常，其余断言通过）  
    - `API_BASE_URL=http://127.0.0.1:8100 python VabHub/backend/scripts/test_functional.py`  
    - `API_BASE_URL=http://127.0.0.1:8100 python VabHub/backend/scripts/test_music_minimal.py`  
    - `API_BASE_URL=http://127.0.0.1:8100 python VabHub/backend/scripts/test_music_minimal.py --execute`  
    - `API_BASE_URL=http://127.0.0.1:8100 python VabHub/backend/scripts/test_graphql_minimal.py`  
  - `quick_test.py` 第一阶段仍会报告“创建订阅异常”（与既有重复数据相关），其余断言通过；  
    `app.api.websocket.broadcast_dashboard_update` 的 `logger` 未定义警告依旧存在，计划在后续单独修复。
- 2025-11-15（追加-3）：日志降噪与 HNR 兼容性收尾：
  - 新增 `settings.REDIS_ENABLED` 开关，并在 `app.core.cache` 中仅在首次连接失败时输出 WARNING，后续转为 DEBUG，默认自动退回内存/L3 缓存；
  - `app.api.websocket.broadcast_dashboard_update` 统一使用 Loguru logger，已验证不会再因 logger 未定义污染日志；
  - `app.modules.scheduler.monitor.record_execution` 若发现 `SchedulerTask` 缺失会自动补建，`update_download_status` / `update_hnr_tasks` 不再刷屏 “任务不存在”；
  - `SignaturePack` 允许 `site_overrides` 为 `null`/缺失，兼容 HNR 签名包的空字段；
  - 上述调整后以 `API_BASE_URL=http://127.0.0.1:8100` 重新跑完 `quick_test.py`、`test_functional.py`、`test_music_minimal.py`（含 `--execute`）以及 `test_graphql_minimal.py` 均通过，仅保留既有的“创建订阅异常”提示（重复数据）作为已知信息。
- 2025-11-15（追加-4）：启动 P6 的 RSSHub 外键修复工作：
  - `app/models/rsshub.py` 的 `relationship` 改为使用 `and_ + foreign()` 显式注解，避免 APScheduler 初始化时出现“无法定位外键”异常；
  - 新增脚本 `backend/scripts/fix_rsshub_fk.py`，可一键扫描并回退缺失目标的订阅（默认指向 `legacy` 占位源/组合，同时禁用）；
  - `RSSHubScheduler` 在运行时检测到缺失的源/组合会自动禁用对应订阅并记录结构化 WARNING，防止错误无限重试；
  - `RSSHubService.toggle_subscription` 现在会检查目标是否存在，不允许订阅不存在的源/组合；
  - 下一步按照 P6 规划继续补充自测脚本 / 运行文档，并陆续清理遗留的 RSSHub 日志告警。
- 2025-11-15（追加-5）：RSSHub 自测闭环与脚本增强：
  - 新增 `backend/scripts/test_rsshub_minimal.py`，在无 RSSHub 服务的情况下仍可验证“正常订阅 + 孤儿订阅”两种路径，自动触发 `RSSHubScheduler` 并确认异常订阅被禁用；
  - 新增 `backend/scripts/test_all.py`，串联 `quick_test` / `test_functional` / `test_music_minimal`（含 `--execute` 可选）/ `test_graphql_minimal` / `test_rsshub_minimal`，支持 `--skip-music-execute` 快速模式；
  - `backend/scripts/fix_rsshub_fk.py` 增强 `--dry-run` / `--limit` / `--verbose`，并输出结构化 JSON 总结，便于在生产环境演练或审核修复结果。
- 2025-11-16（追加-7）：音乐 & GraphQL 前端闭环 + 一键回归固化：
  - `frontend/src/services/graphqlClient.ts` + `music.ts` 封装了 GraphQL 请求与音乐相关查询，`MusicCharts.vue` 改为调用 GraphQL `musicCharts` 数据，并新增历史批次视图；`Music.vue` 的订阅标签页可在榜单创建订阅后自动刷新；
  - 新增 `GraphQLExplorer.vue` 页面与 `/graphql-explorer` 路由，侧边栏提供「GraphQL 实验室」入口，可一键执行 `musicSubscriptions` / `musicCharts` / 综合仪表盘查询；
  - `MusicSubscriptions.vue` 以及 `pages/MusicSubscriptions.vue` 统一复用了 GraphQL 数据源，`Subscriptions.vue` 额外提供 `media_type="music"` 过滤选项，完成「榜单 → 订阅 → 下载」前端闭环；
  - 文档 / README 均明确推荐 `API_BASE_URL=http://127.0.0.1:8100 python backend/scripts/test_all.py --skip-music-execute` 作为快速回归命令，`backend/scripts/test_all.py` 补充成功/失败提示；
  - 新增 GitHub Actions 工作流 `.github/workflows/test-all.yml`：自动启动 uvicorn、执行 `test_all.py --skip-music-execute`，确保合并前至少跑一次核心后端回归。

---

## 0. 项目定位 & 目标

- **名称**：VabHub
- **类型**：面向 PT 站用户的多媒体自动化管理平台
- **当前阶段主要支持对象**：
  - 电影 / 电视剧
  - 音乐（功能在逐步扩展中）
- **尚未实现但规划中的类型（未来扩展方向）**：
  - 有声书
  - 漫画
  - 电子书
- **长期目标能力**：
  - 聚合多家 PT 站的多种媒体资源（电影 / 剧集 / 音乐，后续扩展到有声书/漫画/电子书）
  - 支持：订阅下载、自动“洗版”、重命名、分类、刮削、质量对比、H&R 规避
  - 暴露统一 API（REST + GraphQL），支持前端、插件、第三方集成
  - 提供实时日志中心、可视化配置界面、插件体系

> ⚠️ 对 AI / IDE 的提醒：  
> 目前仓库代码中 **没有** 专门针对「有声书 / 漫画 / 电子书」的完整实现，  
> 若要扩展这些类型，请基于现有电影/剧集/音乐的架构做设计，而不是直接假设已经存在相关模块。

---

## 1. 仓库整体结构（当前真实情况）

> 根目录：`VabHub/`

### 1.1 后端：`VabHub/backend`

- 技术栈：Python 3 + FastAPI + SQLAlchemy + AsyncPG + Redis + Loguru 等  
- 主要文件：
  - `main.py`：FastAPI 主入口（挂载路由、中间件、静态资源等）
  - `manage.py`：初始化数据库脚本（调用 `app.core.database.init_db`）
  - `requirements.txt`：完整依赖列表（包含 `fastapi`, `sqlalchemy`, `strawberry-graphql`, `apscheduler`, `redis` 等）

- 数据库设计（非常重要）：

  - 通过 `app.core.config.Settings.DATABASE_URL` 统一配置数据库连接：
    - **推荐/默认目标（生产环境）**：PostgreSQL  
      示例连接串：
      `postgresql://vabhub:vabhub@localhost:5432/vabhub`
    - **开发环境默认**：若未显式设置 `DATABASE_URL`，则**自动退回**本地 SQLite 文件：
      `sqlite:///./vabhub.db`
  - `app.core.database` 中逻辑：
    - 若 `DATABASE_URL` 以 `sqlite` 开头，则使用 `sqlite+aiosqlite://` 异步驱动（用于开发/测试）
    - 其它情况按 PostgreSQL 等标准异步驱动处理

  > 换句话说：  
  > - 从设计与部署角度，**PostgreSQL 是推荐“默认数据库”**（请在生产环境务必配置为 PostgreSQL）  
  > - 为了让开发环境简单一点，如果你什么都不配，代码会自动用 SQLite 本地文件启动。
  > - 若你使用的是**旧版本数据库**（已经存在 `music_subscriptions` 表但缺少 `subscription_id` 列），
  >   首次创建音乐订阅时，代码会尝试自动 `ALTER TABLE`，如失败请手工执行：  
  >   `ALTER TABLE music_subscriptions ADD COLUMN subscription_id INTEGER;`，然后重新运行音乐相关脚本。

- 核心包结构：`backend/app/`  
  - `app/core/`：底层基础设施
    - `config.py`：配置管理（pydantic-settings），支持 `DATABASE_URL` 等环境变量
    - `database.py`：SQLAlchemy 异步引擎与 Session 管理（PostgreSQL 优先，SQLite 用于开发）
    - `cache.py` / `cache_decorator.py` / `cache_optimizer.py`：缓存与性能优化
    - `logging.py` / `log_handler.py`：统一日志配置（Loguru）
    - `scheduler.py`：定时任务调度（APScheduler）
    - `security.py` / `api_key_manager.py` / `secret_manager.py`：鉴权、API Key、密钥管理
    - `downloaders/`：下载器适配层（qBittorrent 等）
    - `music_clients/`：音乐相关外部接口客户端（为未来音乐扩展准备）
    - `rsshub/`（API 层有对应路由）：与 RSSHub / RSS 源集成的基础设施
    - `plugins/`：插件系统与热重载支持（见后文）
    - `websocket.py`：WebSocket 相关基础封装
  - `app/api/`：HTTP API 路由
    - 常用模块示例：
      - `auth.py`：登录 / 鉴权
      - `dashboard.py`：仪表盘数据
      - `download.py` / `downloader.py`：下载任务管理、下载器对接
      - `search.py` / `search_chain.py`：站内/跨站搜索
      - `rss.py` / `rsshub.py` / `rss_chain.py`：RSS / RSSHub 集成
      - `subscription.py`：订阅管理 API
      - `hnr.py`：H&R 风险检测相关 API
      - `quality_comparison.py`：版本质量对比相关 API
      - `log_center.py`：实时日志中心 API（WebSocket 使用此接口）
      - `cloud_storage.py` / `cloud_storage_chain.py`：云盘 / 对象存储相关（例如 115、OSS 等）
      - `file_browser.py` / `file_operation.py`：文件浏览 / 文件操作
      - `media_library.py` / `media_server.py`：本地媒体库 & 媒体服务器集成
      - `settings.py` / `system.py`：系统设置相关 API
      - `plugins.py`：插件管理 API（与热更新系统关联）
      - （如已落地）`music.py`：音乐相关 API（榜单 / 订阅 / 自动下载）
      - （如已落地）`graphql.py` / 或在 `main.py` 中直接挂载 GraphQL Router
  - `app/modules/`：业务模块实现（服务层）
    - **订阅 & 洗版逻辑**
      - `subscription/rule_engine.py`：订阅规则引擎（按标题/正则/关键字等匹配）
      - `subscription/refresh_engine.py`：订阅刷新逻辑
      - `subscription/service.py`：面向 API 的订阅服务封装（含 `_record_history` 调用）
    - **H&R 规则与检测**
      - `hnr/detector.py`：HNR 检测器，支持 YAML 签名包、关键字匹配、误报规避等
      - 其他工具模块：文本标准化、规则加载等
    - **实时日志中心**
      - `log_center/service.py`：核心 WebSocket 日志服务
        - 管理 WebSocket 客户端连接
        - 支持多源日志聚合（核心 / 插件 / 下载器等）
        - 内存环形缓冲区 + 简单筛选
    - **下载 / 文件 / 媒体**
      - `download/*`：下载任务、限速、重试等逻辑
      - `file_browser/*` / `file_cleaner/*` / `file_operation/*`：文件浏览、清理、移动、重命名等
      - `media_identification/*`：媒体识别（剧集/电影/季/集等）
      - `subtitle/*`：字幕下载/匹配（预留/初版）
    - **站点 / 元数据 / RSS 等**
      - `site/*` / `site_profile/*` / `site_icon/*` / `site_domain/*`：PT 站点管理与配置
      - `douban/*`：豆瓣相关接口封装
      - `charts/*`：排行榜 / 统计类功能（电影/剧集/音乐榜单）
    - **音乐 / 多媒体扩展（当前以音乐为主）**
      - `music/*`：音乐元数据/榜单/订阅相关模块（正在扩展中，已支持最小闭环测试）
      - **⚠️ 这里目前没有有声书 / 漫画 / 电子书专用模块，未来如需支持，将在此目录或相邻目录新增子模块。**
    - **推荐系统（实验性）**
      - `recommendation/`：
        - `algorithms.py`：基础推荐算法
        - `deep_learning/`：深度学习推荐（AutoEncoder、NCF、DeepFM 等）
        - `realtime/`：实时推荐（流式特征更新、A/B 测试）
        - 这些模块依赖 torch 等，可选启用（requirements 中已注释）
  - `app/models/` / `app/schemas/`：
    - 数据库 ORM 模型和 Pydantic 模型（用户、站点、订阅、任务、日志、文件记录、音乐订阅等）
  - 其他：
    - `logs/`：后端运行日志
    - `data/` / `tmp/`：临时文件/上传缓存等

- **注意：`backend/VabHub/backend/...`**
  - 这是一个嵌套的旧目录/实验目录，只包含部分推荐系统与临时 DB。
  - **AI / IDE 开发时请忽略这块目录**，以 `backend/app/...` 为主工程。

---

### 1.2 前端：`VabHub/frontend`

- 技术栈：
  - Vue 3 + Vite + TypeScript
  - Pinia（状态管理）
  - Vue Router
  - Vuetify（UI 组件库）
  - vue-i18n（国际化，当前只简单配置）
  - axios（调用后端 API）

- 核心文件：
  - `package.json`：前端依赖与脚本
    - `npm run dev`：开发模式
    - `npm run build`：构建
    - `npm run lint`：ESLint 修复
  - `vite.config.ts`：Vite 配置
  - `src/main.ts`：
    - 创建 Vue 应用，挂载 Pinia、Router、Vuetify、i18n、Toast 等
  - `src/router/`：
    - 定义路由（Dashboard / Sites / Subscriptions / LogCenter 等）
  - `src/pages/`（关键页面示例）：
    - `Dashboard.vue`：总览仪表盘
    - `Login.vue`：登录页面
    - `Sites.vue`：站点管理
    - `Subscriptions.vue`：订阅管理
    - `RSSHub.vue` / `RSSSubscriptions.vue`：RSS / RSSHub 集成
    - `Downloads.vue`：下载任务列表
    - `FileBrowser.vue`：文件浏览器
    - `MediaIdentification.vue`：媒体识别
    - `MediaRenamer.vue`：重命名相关页面
    - `MediaServers.vue`：媒体服务器（如 Emby/Jellyfin）管理
    - `LogCenter.vue`：实时日志中心前端页面（对接后端 WebSocket）
    - `HNRMonitoring.vue`：H&R 监控
    - `StorageMonitor.vue`：存储监控
    - `SchedulerMonitor.vue`：任务调度监控
    - `Plugins.vue`：插件管理
    - `Settings.vue` / `SystemSettings.vue`：全局设置
    - `Workflows.vue` / `TransferHistory.vue` 等：工作流和迁移历史

> 总体来说：前端页面基本骨架已经齐全，大部分模块都有对应页面和路由，  
> 但交互细节、表单校验、国际化文案、样式优化仍然有较多可完善空间。

---

## 2. 当前功能完成度（简要评估）

> 这里只是粗粒度评估，主要是给 AI / IDE 一个路标。

### 2.1 基础设施

- ✅ FastAPI 应用结构与启动入口已存在（`backend/main.py`）
- ✅ 配置管理 / 数据库 / 日志 / 缓存 / 调度 / 安全 等核心基础设施已实现
- ✅ 大量 API 路由已接入（auth / download / search / rss / subscription / hnr / log_center 等）
- ✅ 前端 Vue 3 + Vite + Pinia + Vuetify 已搭好基础骨架
- ✅ 前端各个页面文件已就位并与路由集成

### 2.2 PT / 下载 / 文件管理（电影 / 剧集 / 音乐）

- ✅ 下载器适配层（后端）存在，支持基础任务操作（添加/查询/删除）
- ✅ 站点管理 / 订阅 / 搜索 / RSS 相关 API 和页面基本齐全
- ✅ 文件浏览器 / 文件操作 / 简单清理逻辑已存在
- ⚠️ 仍需通盘联调与完善（特别是多站点、多下载器、多目录组合的复杂情况）
- ⚠️ 音乐相关功能处于**进行中**状态，有部分模块和页面，但尚未形成完整闭环（最小后端链路已通过 `test_music_minimal.py` / `--execute` 做了验证）。

### 2.3 订阅规则 & 洗版 & H&R

- ✅ `subscription.rule_engine`：订阅规则引擎已实现（按标题/关键字/正则等）
- ✅ `hnr.detector`：HNR 检测器已实现，支持 YAML 签名包、关键字匹配、误报规避
- ✅ `quality_comparison` API：提供版本质量对比相关接口
- ✅ 前端有 `Subscriptions.vue` / `HNRMonitoring.vue` / `Downloads.vue` 等配套页面
- ⚠️ 需要一个统一的“洗版策略层”把：
  - 订阅匹配结果
  - 质量对比结果
  - H&R 风险
  综合起来做**最终决策**（当前是多个模块分散，可用但不够一体化）

### 2.4 实时日志中心

- ✅ `log_center.service`：后端 WebSocket 日志中心逻辑完整
- ✅ `log_center.py`：API 层已存在
- ✅ `LogCenter.vue`：前端页面已存在
- ⚠️ 需要：
  - 确认前端与 WebSocket 连接协议一致（路径、消息格式等）
  - 优化过滤 / 分级 / 搜索等交互细节
  - 修复 `app.api.websocket.broadcast_dashboard_update` 中 `logger` 未定义的问题（当前仅为日志噪声，不影响核心功能）。

### 2.5 插件系统

- ✅ `app/core/plugins` + `app/api/plugins.py`：已经有插件热重载框架（`HotReloadManager` 等）
- ✅ 前端 `Plugins.vue`：有基础页面
- ⚠️ 尚缺：
  - 一个“官方插件目录结构规范”（PDK 文档）
  - 示例插件（例如一个简单的“虚拟 PT 站点”或“假数据下载器”）
  - 前端插件安装/启停/配置的完整流程

### 2.6 GraphQL

- ✅ 依赖中已经加入 `strawberry-graphql`
- ✅ 已实现最小只读 Schema，并通过 `backend/scripts/test_graphql_minimal.py` 进行了基本验证：
  - 可以从 `/graphql` 查询站点 / 订阅 / 下载任务 / 仪表盘统计等基础信息；
  - 已新增 `musicSubscriptions` 查询，使用 `MusicSubscriptionType` 映射，可按平台等条件筛选最近音乐订阅。
- ⏳ 后续仍可扩展更多字段、过滤条件和 Mutation 能力。

### 2.7 高级功能（推荐系统 / 音乐 / 多模态等）

- ✅ `modules/recommendation`：已经有算法/深度学习/实时推荐等模块
- ✅ `modules/music`：音乐相关模块已经有基本结构
- ✅ 前端有 `Recommendations.vue` / `MultimodalMonitoring.vue` 等页面
- 🧪 定位为**实验性增强功能**：
  - 需 GPU / torch 环境支持
  - 若当前部署环境不适合，可以暂时视为“保留项”，优先保证基础媒体管理链路稳定
- ❌ **当前没有有声书 / 漫画 / 电子书的专用模块和前端页面**  
  - 如要实现这些类型，请视为**新增需求**，不要假定已存在。

---

## 3. 环境配置与启动方式（给 AI / IDE 的硬性要求）

### 3.1 后端开发 & 部署环境

1. **推荐数据库策略：**

   - **生产环境（默认目标）**：  
     - 请务必设置 `DATABASE_URL` 为 PostgreSQL 连接串，例如：
       - `postgresql://vabhub:vabhub@localhost:5432/vabhub`
     - 这一模式视为 VabHub 的“默认数据库方案”。

   - **开发 / 本地环境**：  
     - 若不设置 `DATABASE_URL`，则自动使用 SQLite 本地文件：
       - `sqlite:///./vabhub.db`
     - 适合快速启动/调试，不建议长期在生产使用。

2. **后端启动步骤（Windows / Linux 通用）：**

   ```bash
   cd VabHub/backend

   # 创建虚拟环境（视平台调整命令）
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate

   pip install -U pip
   pip install -r requirements.txt

   # （可选）设置数据库为 PostgreSQL（推荐用于生产/模拟生产）
   # set DATABASE_URL=postgresql://vabhub:vabhub@localhost:5432/vabhub   # Windows
   # export DATABASE_URL=postgresql://vabhub:vabhub@localhost:5432/vabhub # Linux/macOS

   # 初始化数据库（使用当前 DATABASE_URL）
   python manage.py

   # 启动开发服务
   uvicorn main:app --reload --host 0.0.0.0 --port 8092
   ```

3. **配置说明：**

   - 若 `DATABASE_URL` 未设置，则后端会使用默认 SQLite DB：`sqlite:///./vabhub.db`
   - 建议：
     - 本地开发：使用 SQLite 或本地 PostgreSQL，视资源情况而定
     - 正式部署：**必须**使用 PostgreSQL，并正确配置 `DATABASE_URL`
   - 其他关键环境变量见：`app/core/config.py`
   - 若出现音乐订阅相关的 SQL 错误，并提示 `music_subscriptions.subscription_id` 字段不存在，
     请参考本文件开头的“最近进度快照”中的说明，执行一次手工 `ALTER TABLE` 迁移。

### 3.2 前端开发环境

1. **建议步骤：**

   ```bash
   cd VabHub/frontend
   npm install
   npm run dev
   ```

2. **前后端联调：**

   - 默认后端监听 `http://localhost:8092`
   - 前端 axios 基础 URL 请保持与后端一致（若未配置，需 IDE 协助补充统一配置）

---

## 4. 后续开发优先级（给 AI / IDE 的 TODO 列表）

> ⚠️ 请 AI / IDE 在动手前**务必先通读本节**。

### P1：保证最小闭环可用（登录 → 配置站点 → 订阅 → 下载 → 查看日志）

（本阶段核心 API 已通过 quick_test/test_functional 验证，仍可做细节完善）

1. **后端基础联调**

   - [ ] 确认 `main.py` 中：
     - 挂载了所有 API 路由（尤其是 auth / sites / subscription / download / log_center 等）
     - CORS 配置允许前端域名访问
   - [ ] 检查数据库初始化是否完整（用户表、站点表、订阅表、任务表等）
   - [ ] 提供一个创建初始管理员账号的脚本或 API（如果已有脚本，则在文档中说明用法）

2. **前端基础联调**

   - [ ] 确保前端登录页 `Login.vue` 可正常调用 `auth` API 完成登录
   - [ ] 确认登录后能访问仪表盘 `Dashboard.vue`
   - [ ] 为常用页面配置路由守卫（未登录跳转登录页）

3. **日志中心闭环**

   - [ ] 确认 `LogCenter.vue` 能通过 WebSocket 连接后端 `log_center` 服务
   - [ ] 后端 log_center 把重要事件（任务创建、订阅运行、HNR 检测等）推送到日志流
   - [ ] 前端支持按模块/级别过滤
   - [ ] 修复 `app.api.websocket.broadcast_dashboard_update` 中 `logger` 未定义问题，避免无意义报错干扰日志观察。

### P2：订阅 / 洗版 / H&R 体验打磨

1. **统一“下载决策”逻辑**

   - [ ] 在后端新增一个统一的“决策服务”（可以放在 `modules/subscription` 或新建 `modules/decision`）：
     - 输入：候选种子信息、本地已有版本、HNR 风险、质量对比结果
     - 输出：**下载 / 不下 / 替换已有种子** 等决策
   - [ ] 将 `subscription.rule_engine` + `hnr.detector` + `quality_comparison` 的结果整合到该服务中

2. **前端体验优化**

   - [ ] 在 `Subscriptions.vue` 中展示：
     - 每个订阅的规则摘要
     - 最近触发记录、下载历史
   - [ ] 在 `HNRMonitoring.vue` 中展示：
     - 被识别为 HNR 风险的种子、站点、原因
   - [ ] 在 `Downloads.vue` 中标注：
     - 哪些下载是“订阅触发”
     - 哪些是“洗版升级”

### P3：插件系统 & GraphQL 相关准备

1. **插件开发套件（PDK）雏形**

   - [ ] 在 `app/core/plugins` 内整理一份“插件接口约定”：
     - 插件目录结构（例如 `plugins/<name>/plugin.py`）
     - 插件入口函数签名（init / register / on_event 等）
     - 可用的 context（日志、数据库访问、配置、下载器接口等）
   - [ ] 在后端新增一个示例插件（例如：虚拟站点 or 假数据下载器）
   - [ ] 在前端 `Plugins.vue` 中：
     - 列出已安装插件
     - 提供启用/禁用/重载操作入口

> GraphQL 的具体实现放在 P5 展开。

---

### P4：音乐功能最小闭环（给 IDE 的具体任务）

> 目标：先做一个“**可以从一个音乐榜单订阅 → 通过 PT 搜索 → 创建下载任务 → 进文件夹**”的最小 MVP，  
> 不追求 UI 完美，先把链路打通。  
> 当前版本中，最小后端链路已通过 `backend/scripts/test_music_minimal.py` / `--execute` 做了验证，  
> 后续可以在此基础上逐步增强。

#### P4-1. 后端音乐领域模型与服务梳理

- [ ] 在 `app/modules/music`（若不存在则创建目录）中整理/新增以下内容：
  - `services.py`：对外服务层，负责：
    - 从外部音乐榜单源拉取榜单（可以复用已有 `charts` / `music_clients` 逻辑）
    - 提供“根据榜单条目生成 PT 搜索关键字”的方法
  - `schemas.py`：音乐相关 Pydantic 模型：
    - `MusicTrack`, `MusicAlbum`, `MusicChartEntry`（至少包含 title/artist/rank/link 等）
- [ ] 在 `app/models` 中确认或新增音乐相关表（如没有则可以从简单表开始）：
  - `music_tracks` / `music_albums` / `music_charts`（先尽量简单，后续再扩展）

#### P4-2. 音乐榜单 → PT 搜索 → 下载的后端 API

- [ ] 在 `app/api/music.py`（新建）中提供以下基础 API：
  - `GET /music/charts`：返回当前可用榜单源与部分排名数据（从 `music.services` 读取）
  - `POST /music/subscriptions`：
    - 请求体：选中的榜单条目 ID / 名称 / 简单规则（如“只要前 20 名”）
    - 行为：为音乐创建一个“订阅配置”，并触发一次 PT 搜索预览
  - `POST /music/autodownload`：
    - 根据订阅配置，为匹配到的种子创建下载任务（调用现有的下载器接口）

> 暂时不必做复杂规则系统，只要有“根据榜单拉一波种子”即可。

#### P4-3. 与现有订阅系统的简单打通

- [ ] 在 `subscription` 模块中增加对 `media_type="music"` 的支持：
  - `Subscription` 模型中如果已有 `media_type` 字段，确保包含 `"music"`；
  - 当 `media_type="music"` 时，调用 `music.services` 中的逻辑，而不是影视专用解析；
- [ ] 确保创建音乐订阅时，`_record_history` 能正常记录（action 可以为 `create_music_subscription` 等）。

#### P4-4. 前端音乐入口（粗糙版即可）

- [ ] 在前端新增 `Music.vue` 页面（若已存在则扩展），放在 `src/pages/`：
  - 左侧展示可选榜单（例如“Apple Music / Spotify / 其他”）；
  - 中间展示榜单条目列表（标题、歌手、排名）；
  - 每条记录提供“创建订阅”按钮（调用 `POST /music/subscriptions`）。
- [ ] 在 `router` 中新增 `/music` 路由并挂到主菜单里。

#### P4-5. 最小自测脚本

- [ ] 在 `backend/scripts/test_music_minimal.py` 新增或扩展脚本，流程为：
  1. 调用 `/api/music/charts` 取一份榜单；
  2. 对第一条或前 N 条创建音乐订阅；
  3. 调用 `/api/subscriptions` 检查是否出现 `media_type=music` 的订阅；
  4. 可选：调用 `/api/music/autodownload` + `/api/downloads`，确认出现相应下载任务。
- [ ] 若已存在该脚本，请在本文件中更新其覆盖范围与已验证的行为（当前已用于验证“音乐订阅 + 预览 + 自动下载”最小闭环）。

---

### P5：GraphQL `/graphql` 最小 Schema（给 IDE 的具体任务）

> 目标：先搭起一个**只读的最小 GraphQL API**，  
> 能通过 `/graphql` 查询基本信息（站点、订阅、任务、仪表盘统计、音乐订阅），  
> 不做复杂 Mutation，先让前端/插件有一个可用的 GraphQL 入口。  
> 当前版本中，最小 Schema 已存在，并通过 `backend/scripts/test_graphql_minimal.py` 做了基础验证。

#### P5-1. 基础集成

- [ ] 在 `backend/app/graphql` 目录下创建或完善：
  - `schema.py`：定义 GraphQL Schema
  - `types.py`：定义 GraphQL 类型（与 Pydantic/ORM 分离）
- [ ] 在 `schema.py` 中使用 `strawberry-graphql` 定义最小 Query：
  - `sites`: 列出已配置站点（id, name, url, enabled）
  - `subscriptions`: 支持分页的订阅列表（id, title, media_type, status, created_at）
  - `downloadTasks`: 当前下载任务（id, title, status, progress, size_gb）
  - `dashboardStats`: 仪表盘统计（简单几个字段即可：总订阅数、总下载任务数、HNR 风险数量等）
  - `musicSubscriptions`: 最近的音乐订阅列表（可按平台等条件筛选，字段映射到 `MusicSubscriptionType`）

#### P5-2. 数据源与类型映射

- [ ] 在 `types.py` 中定义对应的 GraphQL 类型，例如：

  - `@strawberry.type class SiteType: ...`
  - `@strawberry.type class SubscriptionType: ...`
  - `@strawberry.type class DownloadTaskType: ...`
  - `@strawberry.type class DashboardStatsType: ...`
  - `@strawberry.type class MusicSubscriptionType: ...`

- [ ] 在 `schema.py` 中的 resolver 里：
  - 通过 SQLAlchemy 异步 Session 查询对应 ORM 模型；
  - 做简单映射，不要在 resolver 内写复杂业务逻辑。

#### P5-3. 路由挂载

- [ ] 在 `backend/main.py` 中：
  - 引入 `strawberry.fastapi.GraphQLRouter`；
  - 创建 `graphql_app = GraphQLRouter(schema)`；
  - 通过 `app.include_router(graphql_app, prefix="/graphql")` 挂载；
- [ ] 确保 Swagger 仍正常，GraphQL 独立使用。

#### P5-4. 简单测试与文档

- [ ] 新建或扩展 `backend/scripts/test_graphql_minimal.py`，使用 `httpx` 或 `requests`：
  - 发起一个 `POST /graphql` 请求，查询：  
    `subscriptions { id title media_type }`、`musicSubscriptions { id platform title }` 等；
  - 校验返回结构中包含对应字段且为列表。
- [ ] 在 `README` 或 `docs/DEV_PROGRESS_VABHUB.md`（本文件）中新增一小节说明：
  - `/graphql` 的基础用法；
  - 提示插件/前端可从这里读取数据。
- [ ] 若该脚本已存在且通过，请在“最近进度快照”中记录（本文件已记录 2025-11-15 的一次通过）。

---

## 5. 给 AI / IDE 的特别说明

1. **请优先遵循本文件的结构和优先级，而不是随意翻代码“乱改”。**  
2. **不要把 `backend/VabHub/backend/...` 当成主工程**，那里是旧的实验目录，仅供参考。  
3. 所有面向用户的功能（订阅、下载、H&R、日志中心、插件、音乐等），请优先查阅：
   - 后端：`backend/app/api/` + `backend/app/modules/`
   - 前端：`frontend/src/pages/` + `frontend/src/services/`（若有）  
4. 任何新的设计决策或较大的重构，请同步更新本文件，保持“项目记忆”在仓库中，而不是只存在聊天记录里。

---

> 当前文档版本：`v0.8（新增日志降噪 / Redis 开关 / Scheduler 自动建档 / HNR site_overrides 兼容性说明）`  
> 如果你（未来的 AI / IDE）发现本文件与实际代码不符，请先更新这里，再继续改代码。  
---

## 6. 下一阶段任务草案（基于 v0.8 状态）

> 说明：本节是在 `v0.8`（日志降噪 / Redis 开关 / Scheduler 自动建档 / HNR site_overrides 兼容）基础上的“下一阶段”任务规划，  
> 主要围绕：RSSHub 外键报错收尾、音乐 & GraphQL 前端接入、测试脚本与部署运维补完。

### P6：RSSHub / 订阅外键修复与数据自愈

> 目标：彻底解决 `rsshub_source ↔ user_rsshub_subscription` 外键缺失导致的 ORM 报错，  
> 确保即使存在历史脏数据，系统也能自愈或优雅降级，不再在日志里刷异常。

1. **模型与外键关系梳理**

   - [ ] 在 `backend/app/models/` 中查找与 `rsshub_source` 和 `user_rsshub_subscription` 相关的 ORM 模型：
     - 确认两者之间的外键字段命名（例如 `rsshub_source_id`）与 `ForeignKey` 声明是否一致。
     - 若存在“可为空但实际逻辑假定必须有值”的字段，补充 `nullable=False` + 合理默认值策略。
   - [ ] 在模型上补充/统一 `relationship` 定义：
     - 例如：在订阅模型中增加 `rsshub_source = relationship("RSSHubSource", back_populates="subscriptions")` 之类声明（具体类名以实际代码为准）。
     - 避免因为 `lazy` / `cascade` 配置不当导致删除源时遗留孤儿订阅。

2. **历史数据修复脚本**

   - [ ] 在 `backend/scripts/` 新增 `fix_rsshub_fk.py`（名称可调整，但要求语义清晰），职责：
     - 扫描 `user_rsshub_subscription` 表，找出 `rsshub_source_id` 为空或指向不存在 `rsshub_source` 记录的订阅。
     - 为这些“孤儿订阅”采取统一策略（至少选择其一）：
       - 策略 A：为它们创建一个通用的“默认 RSSHub 源”（如 `name="legacy-default"`），并把外键指向该源；
       - 策略 B：将其标记为停用状态并记录日志，提示管理员人工处理。
     - 执行时打印修复统计信息（修复了多少条、剩余多少需要人工处理）。
   - [ ] 在本文件“最近进度快照”中预留一行，用于未来记录该脚本第一次成功执行的时间和效果。

3. **运行时的防御性逻辑**

   - [ ] 在所有依赖 `rsshub_source` 的核心路径中增加防御性处理（主要集中在 `app/modules/rsshub/*` 与相关 Scheduler 任务）：
     - 当通过 ORM 访问订阅的 `rsshub_source` 时，如果为 `None` 或查询不到：
       - 记录一条结构化 WARNING 日志（包含订阅 ID / 用户 ID），避免直接抛出异常。
       - 选择以下行为之一：
         - 跳过当前订阅（不终止整个批次任务）；
         - 或尝试调用上面的“默认源”策略自动补建。
   - [ ] 确保上述处理不会影响已经健康的订阅链路（即正常订阅不引入额外性能负担）。

4. **自测与回归**

   - [ ] 新建一个针对 RSSHub 的最小自测脚本，例如 `backend/scripts/test_rsshub_minimal.py`：
     - 构造一个正常的 RSSHub 订阅并触发一次刷新/拉取；
     - 构造一个“孤儿订阅”（可以通过直接插入 DB 或在脚本中手工删除其 source），验证：
       - 不会出现 ORM 报错；
       - 自愈策略或跳过策略生效；
       - 日志中有明确的 WARNING，而不是 traceback 刷屏。
   - [ ] 将该脚本纳入统一回归命令组，并在本文件中记录其用法（参照 `quick_test.py` 等脚本的说明风格）。

---

### P7：音乐 & GraphQL 前端接入（基于现有后端能力）

> 目标：在后端已经具备 `musicSubscriptions` / `musicCharts` / `/music/charts/history` 等能力的前提下，  
> 做一版可用但不花哨的前端页面，让“音乐榜单 → 订阅 → 下载”流程在 UI 上可视化。

1. **GraphQL 客户端与封装**

   - [ ] 在 `frontend/src/` 下新增（或完善）一个 GraphQL 客户端封装，例如：
     - `src/services/graphqlClient.ts`：
       - 导出 `query<T>(query: string, variables?: Record<string, any>): Promise<T>`；
       - 底层使用 axios 对 `/graphql` 发起 POST 请求。
   - [ ] 约定所有前端 GraphQL 调用都通过此封装，不在页面里直接写 `axios.post('/graphql', ...)`。

2. **音乐相关 GraphQL 查询封装**

   - [ ] 在 `frontend/src/services/music.ts`（如不存在则新建）中整理音乐相关 API：
     - `fetchMusicSubscriptions(...)`：调用 `musicSubscriptions` 查询最近音乐订阅列表；
     - `fetchMusicChartsHistory(...)`：调用 `musicCharts` 查询历史榜单数据（支持平台/时间过滤）。
   - [ ] 若已有 REST 版 `/music/charts` / `/music/charts/history`，则统一命名 & 封装：
     - 保持 REST 与 GraphQL 的字段命名尽量一致，避免前端做大量转换。

3. **Music 页面 UI（最小可用版）**

   - [ ] 在 `frontend/src/pages/` 中创建或扩展 `Music.vue`：
     - 顶部：选择平台 + 时间范围的过滤控件（下拉框 + 日期范围选择）。
     - 左侧/上方：当前榜单列表（曲目名称 / 歌手 / 排名字段）。
     - 每一行提供：
       - “创建订阅”按钮（调用后端 `/music/subscriptions` 或 GraphQL Mutation，如暂未实现 Mutation 则继续走 REST）。
       - “预览 PT 搜索结果”入口，可简单跳转到现有搜索页面并带上关键字。
   - [ ] 在 `router` 中挂载 `/music` 路由到侧边栏菜单（若尚未挂载），图标和名称保持与现有页面风格一致。

4. **音乐订阅列表与状态可视化**

   - [ ] 在前端新增一个简单的“音乐订阅列表”视图，可以是：
     - 独立页面 `MusicSubscriptions.vue`，或
     - 在 `Subscriptions.vue` 中增加 `media_type="music"` 的筛选 Tab。
   - [ ] 展示字段：
     - 订阅名称 / 平台 / 创建时间 / 最近执行时间；
     - 最近一次执行结果（例如：找到多少条候选 / 创建了多少下载任务）。
   - [ ] 若后端已有 `test_music_minimal.py --execute` 所依赖的字段，则优先复用这些字段。

5. **最小前后端联调自测**

   - [ ] 启动后端（确保之前的 quick_test / test_functional / test_music_minimal / test_graphql_minimal 全部通过）。
   - [ ] 启动前端，手工完成以下操作：
     - 在 `/music` 页面选择某个平台（如 Apple Music），加载榜单；
     - 为前 N 条创建音乐订阅；
     - 在音乐订阅页面/Tab 中确认订阅出现；
     - 触发一次自动下载（通过前端或后端脚本），在下载列表中看到对应任务。
   - [ ] 把这套“人肉回归流程”简要记录在本文件或单独的 `docs/MUSIC_FLOW.md` 中，便于未来复查。

---

### P8：测试脚本整合与部署运维注意事项

> 目标：把现有零散的测试脚本打包成一个“统一入口”，  
> 同时在文档层面明确“如何避免旧版 uvicorn 实例继续写入过期日志”。

1. **统一测试入口脚本**

   - [ ] 在 `backend/scripts/` 新增 `test_all.py`：
     - 依次调用：
       - `quick_test.py`
       - `test_functional.py`
       - `test_music_minimal.py`
       - `test_music_minimal.py --execute`
       - `test_graphql_minimal.py`
       - （后续可以接入 `test_rsshub_minimal.py` 等）
     - 要求：任一子脚本返回非零状态时立即退出并打印清晰错误提示。
   - [ ] 在本文件“最近进度快照”中预留一行用于记录 `test_all.py` 首次完整通过的日期。

2. **CI / 自动化测试（可选但推荐）**

   - [ ] 在仓库根目录下新增简单的 GitHub Actions 工作流（若项目已关联 GitHub）：
     - `.github/workflows/backend-tests.yml`
     - 内容：使用 Python 3.11，安装 `backend/requirements.txt`，运行 `python backend/scripts/test_all.py`。
   - [ ] 在 `README.md` 或 `docs/` 下补充一句说明：  
     - “建议每次合并前跑一遍 `test_all.py` 或查看 CI 状态，确保核心链路未被破坏。”

3. **避免旧版 uvicorn 实例污染日志**

   - [ ] 在 `docs/CLOUD_DEPLOYMENT.md` 或本文件新增一小节“部署时的进程管理注意事项”：
     - 提醒：使用 systemd / supervisor / pm2 等进程管理工具，确保只存在一个当前版本的 uvicorn 实例；
     - 给出示例：
       - Linux 上可以通过 `ps aux | grep uvicorn` 检查；
       - 使用 `systemctl restart vabhub-backend.service` 之类命令重启，而不是在后台手动起多个 uvicorn。
   - [ ] 在 `backend/app/core/logging.py` 或相邻位置增加一条简短的启动日志：
     - 内容包括：版本号 / 启动时间 / 当前 `settings.REDIS_ENABLED` 等关键配置；
     - 方便通过日志首行判断当前运行的是哪一个版本（有助于区分旧实例写入的日志）。

---

> 以上 P6 / P7 / P8 为基于 `v0.8` 状态的“下一阶段建议任务”。  
> 建议未来的 AI / IDE 在开始实现新功能前，优先完成 P6（数据一致性）与 P7 的基础部分，  
> 再视资源情况推进 P8（测试与运维自动化）。

### 最近进度快照补充

2025-11-15（追加-5）：RSSHub 外键语义修复与数据自愈落地：

app/models/rsshub.py 中与 user_rsshub_subscription 相关的关系统一改为 and_ + foreign() 的可执行表达式，SQLAlchemy 不再因缺少外键注解报错，订阅关系映射恢复稳定；

新增 backend/scripts/fix_rsshub_fk.py，会在需要时创建 legacy 默认源/组合，并把指向不存在目标的订阅统一回退到该占位记录（同时标记为禁用），执行过程会输出修复统计，便于后续审计；

RSSHubScheduler 在运行时遇到缺失的源/组合会自动禁用订阅并输出结构化 WARNING，避免无限重试；RSSHubService.toggle_subscription 在切换订阅状态前会检查目标是否存在，阻止新建指向无效 ID 的订阅；

文档层面已经记录 P6 启动情况与修复脚本存在，推荐在实际环境中先跑一遍 `python backend/scripts/fix_rsshub_fk.py --dry-run`，再依次执行：

- `API_BASE_URL=http://127.0.0.1:8100 python backend/scripts/quick_test.py`
- `API_BASE_URL=http://127.0.0.1:8100 python backend/scripts/test_functional.py`
- `API_BASE_URL=http://127.0.0.1:8100 python backend/scripts/test_music_minimal.py`
- `API_BASE_URL=http://127.0.0.1:8100 python backend/scripts/test_graphql_minimal.py`

2025-11-15（追加-6）：RSSHub 订阅健康检查闭环：

- 新增 `GET /api/rsshub/subscriptions/health` 接口（返回 legacy 占位 / 最近错误 / 更新时间等字段），并在 Scheduler 中记录 `last_error_code/last_error_message/last_error_at`；
- `frontend/src/pages/RSSHub.vue` 加入“订阅健康检查”卡片，可快速筛选 legacy/异常记录、查看详情并一键触发重新启用或跳转到订阅管理；
- `user_rsshub_subscription` 表新增健康字段，运行期自动 `ALTER TABLE`，无需额外迁移脚本。

P6：RSSHub / 订阅外键修复与数据自愈（后续补完 TODO）

当前状态：

✅ ORM 外键关系已通过 and_ + foreign() 明确语义并稳定工作；

✅ backend/scripts/fix_rsshub_fk.py 已能创建 legacy 默认源/组合并回退脏数据；

✅ Scheduler 与 Service 层具备“自动禁用异常订阅 + 结构化 WARNING” 的运行期防御能力；
本节只列出尚未完成但推荐继续推进的任务，交给 IDE 实施。

#### P6-1. 自测脚本与回归整合

- [x] 新增 `backend/scripts/test_rsshub_minimal.py`，涵盖“正常订阅 + 孤儿订阅”两条链路，并在缺少 RSSHub 服务时优雅降级（只记录 WARNING，不抛异常）。
- [x] 新增 `backend/scripts/test_all.py`，串联 `quick_test.py` → `test_functional.py` → `test_music_minimal.py` → `test_music_minimal.py --execute` → `test_graphql_minimal.py` → `test_rsshub_minimal.py`，支持 `--skip-music-execute` 加速选项。
- [ ] 在 GitHub Actions / 文档中固定 `test_all.py` 作为“一键回归”入口（待 P8 落地）。

#### P6-2. `fix_rsshub_fk.py` 安全性与可观察性

- [x] 增加 `--dry-run` / `--limit` / `--verbose` 参数，便于预览、限流与排查。
- [x] 修复完成后输出结构化 JSON 摘要（包含扫描/修复/禁用统计及运行模式），方便在生产日志中检索。
- [ ] 在运维文档中补充“如何基于新参数执行修复”的演练步骤。

#### P6-3. 管理端可视化 & 手工干预入口

 在前端 RSSHub 相关页面增加“订阅健康检查”区域

建议由 IDE 在现有 RSSHub 页面或新建 Tab 中实现：

列出所有被自动禁用、且外键曾经有问题的订阅（可通过数据库字段或日志标记识别）；

支持按用户 / 站点 / 创建时间筛选；

显示当前绑定的源/组合是否为 legacy 占位记录。

 提供简单的“手工修正”入口

在这一列表中，为每条订阅提供：

“跳转到该订阅编辑页”的按钮（复用现有订阅编辑组件）；

或至少提供订阅 ID / 用户 ID / 原始外键字段，方便管理员在 DB 或 API 层手动修正；

确保手工修改后，订阅状态可以从“禁用 + legacy 回退”恢复到正常工作状态。

#### P6-4. 文档与运维指引补完

 在 docs/DEV_PROGRESS_VABHUB.md 的 P6 部分追加“生产环境操作指引”

建议明确写出以下内容，供未来自己和 IDE 参考：

在生产环境上线包含 P6 修复的版本后，推荐流程：

确认新代码版本的后端已经完全替换旧版 uvicorn 实例；

对数据库做一次快照/备份；

运行 python backend/scripts/fix_rsshub_fk.py --dry-run，观察输出；

若结果合理，再运行不带 --dry-run 的正式修复；

之后按顺序执行主要回归脚本（test_all.py 或对应子脚本）。

说明 legacy 默认源/组合的语义（仅作为占位与诊断用途，不参与实际 RSS 抓取）。

 如已有 docs/CLOUD_DEPLOYMENT.md，在部署章节增加“RSSHub 数据修复与定期巡检”小节

简要说明：

新环境首次上线时如何跑 fix_rsshub_fk.py；

日志中如何快速确认是否仍存在新的“孤儿订阅”；

建议多久进行一次巡检（例如每次大版本升级后或定期任务）。

### P6 附录：RSSHub / 订阅外键修复与数据自愈（后续 TODO）

> 前提：本轮已完成：
>
> - `backend/scripts/test_rsshub_minimal.py` 最小自测脚本；
> - `backend/scripts/test_all.py` 一键回归脚本（含 `--skip-music-execute`）；
> - `backend/scripts/fix_rsshub_fk.py` 的 `--dry-run` / `--limit` / `--verbose` 与 JSON 摘要输出；
> - `docs/DEV_PROGRESS_VABHUB.md` 已补充对应说明。:contentReference[oaicite:1]{index=1}

#### P6-3（附录）：管理端可视化 & 手工干预入口

- [x] **后端：RSSHub 订阅健康检查 API**
  - `GET /api/rsshub/subscriptions/health` 已上线，默认提取禁用订阅 + legacy 占位 + 最近错误信息，可按用户 / 类型 / legacy-only 筛选、限制返回数量；
  - Scheduler 在抓取成功时会清理 `last_error_*` 字段，缺失目标或抓取失败会自动写入错误并（必要时）禁用订阅。

- [x] **前端：RSSHub 页面增加“订阅健康检查”区域**
  - `RSSHub.vue` 新增健康检查卡片：支持按用户ID、目标类型、仅 legacy、返回数量过滤，表格展示目标名称 / 最后错误 / 更新时间；
  - 提供“刷新”“重新启用”以及“订阅详情”跳转按钮（可直接进入 `/subscriptions` 页面进一步手工修正）。

- [x] **手工修正流程打通**
  - 通过健康列表的“重新启用”按钮即可直接调用后端 toggle API，修复成功后 `last_error_*` 字段随 Scheduler/手工操作被清除；
  - “订阅详情”操作将跳转到订阅管理页（`/subscriptions`），便于管理员手动重新赋值源并恢复正常状态。

#### P6-4（附录）：文档与运维指引补完

- [x] **生产环境操作指引（本文件）**
  - 升级到包含 P6 修复的版本后建议遵循：
    1. **停止旧实例**：确认所有旧版本 uvicorn 进程均已退出，避免旧代码继续写入日志/数据库。
    2. **备份数据库**：对生产库执行一次快照或冷备份。
    3. **预览修复**：运行 `python backend/scripts/fix_rsshub_fk.py --dry-run`，核对 JSON 摘要（扫描条数 / 修复条数 / legacy 回退等）。
    4. **正式修复**：确认无误后去掉 `--dry-run` 再执行一次脚本。
    5. **快速回归**：运行 `API_BASE_URL=<生产地址> python backend/scripts/test_all.py --skip-music-execute`；若需要验证真实音乐下载，再补跑一次不带 `--skip-music-execute` 的完整回归。
  - `legacy` 占位源/组合仅作为历史脏数据容器与诊断线索：不会参与实际订阅抓取，也不会被 Scheduler 拉取。

- [x] **云端部署补充说明**
  - 在 `docs/CLOUD_DEPLOYMENT.md`（“阶段二部署指南”）追加“小节：RSSHub 数据修复与巡检”，内容包括：
    - 新环境首次上线时依旧先执行 `fix_rsshub_fk.py --dry-run` → 正式修复；
    - 通过 `/api/rsshub/subscriptions/health` 与日志关键字（`[RSSHub-FIX]`、`FETCH_FAILED`、`MISSING_TARGET` 等）快速定位新的“孤儿订阅”；
    - 建议巡检频率：每次大版本升级后 + 至少每月一次运行 `--dry-run` 进行检查。

---

### P7：音乐 & GraphQL 前端接入（本轮之后可启动）

> 目标：在后端已有 `musicSubscriptions` / `musicCharts` / `/music/charts/history` 能力的基础上，  
>
> 做一版可用的 UI，让「音乐榜单 → 订阅 → 下载」在前端看得见、点得动。:contentReference[oaicite:2]{index=2}  

#### P7-1. GraphQL 客户端封装

- [x] 在 `frontend/src/services/` 新增 `graphqlClient.ts`：
  - 暴露 `graphqlRequest` 通用方法，统一处理 `/graphql` 请求与错误；
  - 与 `music.ts` 等服务共享 axios 实例与鉴权头。

#### P7-2. 音乐相关 Service 封装

- [x] 在 `frontend/src/services/music.ts` 中接入 GraphQL：
  - `fetchMusicChartBatches`、`fetchMusicSubscriptions` 均直接调用 GraphQL；
  - 返回结果在前端做轻量映射（例如补充 `target_name`）以兼容既有 UI。

#### P7-3. Music 页面 & 订阅列表 UI

- [x] `Music.vue` / `MusicCharts.vue` / `MusicSubscriptions.vue`：
  - 榜单过滤项新增地区 + 历史批次，UI 直接消费 GraphQL 数据；
  - 从榜单创建订阅后会触发订阅列表刷新，形成“榜单 → 订阅 → 下载”闭环。

- [x] 音乐订阅视图：
  - `MusicSubscriptions.vue` + `pages/MusicSubscriptions.vue` 统一复用 GraphQL 数据源，并暴露 `reload` / `openCreateDialog`；
  - `Subscriptions.vue` 增加 `media_type="music"` 过滤选项，便于在通用订阅页观察音乐订阅。

---

### P8：测试脚本整合 & CI / 运维（围绕 test_all.py 收尾）

> 目标：让 `test_all.py` 真正成为“一键回归”的固定入口，并配合 CI 与部署文档。:contentReference[oaicite:3]{index=3}  

#### P8-1. 一键回归入口与文档固化

- [x] 在 `docs/DEV_PROGRESS_VABHUB.md` 与主 `README.md` 中：
  - 明确标注：推荐使用  
    `API_BASE_URL=http://127.0.0.1:8100 python backend/scripts/test_all.py --skip-music-execute`  
    作为日常快速回归入口；
  - 同时给出“不带 `--skip-music-execute`”的完整回归命令，并注明需要真实的音乐下载环境。

- [x] 在 `backend/scripts/test_all.py` 内部：
  - 运行前打印每个脚本的执行命令；
  以及成功/失败 ✅ / ❌ 提示；
  - 任意子脚本失败会立即中止并抛出非 0 返回码。

#### P8-2. CI 集成（可选但推荐）

- [x] 在仓库根目录新增 GitHub Actions 工作流 `.github/workflows/test-all.yml`：
  - 使用 Python 3.11 + SQLite；
  - 启动 uvicorn 后执行 `python backend/scripts/test_all.py --skip-music-execute` 作为回归基线。
- [x] 在 `README` 中增加一句说明：
  - “合并前建议本地跑一遍 `test_all.py` 或确认 CI 通过，避免破坏核心链路。”

---

> 你可以直接把上面的 Markdown 片段追加进 `DEV_PROGRESS_VABHUB.md`：  
>
> - P6 部分补上 P6-3 / P6-4；  
> - P7 / P8 保持为「下一阶段开发路线」，给 IDE 当待办清单。

::contentReference[oaicite:4]{index=4}

### 最近进度快照补充（2025-11-15，追加-6 补充）

- 2025-11-15（追加-6）：RSSHub 订阅健康检查闭环 + 运行期 schema ensure：
  - 新增 `app/modules/rsshub/constants.py`，集中维护 legacy 占位 ID 与错误码；`schema_utils.ensure_subscription_health_columns()` 在首次访问 `user_rsshub_subscription` 时自动 `ALTER TABLE` 添加 `last_error_code` / `last_error_message` / `last_error_at`，避免手工迁移。
  - `UserRSSHubSubscription` 模型扩展上述字段，`backend/scripts/fix_rsshub_fk.py` 统一引用这些常量，确保脚本与运行时使用同一语义。
  - `RSSHubScheduler` 在成功处理订阅后会清理 `last_error_*`，在抓取失败 / 缺少目标等异常场景下记录错误并（必要时）禁用订阅，健康字段写入 legacy / 缺源原因，避免无限重试刷日志。
  - `RSSHubService` 在所有涉及 `user_rsshub_subscription` 的接口前自动调用 schema ensure，并通过 `list_subscription_health()` 暴露 `/api/rsshub/subscriptions/health` 查询接口，支持 `userId` / `targetType` / `onlyLegacy` / `limit` 筛选，方便运维侧按需巡检。
  - 前端 `src/pages/RSSHub.vue` 新增“订阅健康检查”卡片：支持按用户 ID、目标类型、仅 legacy、数量上限过滤；表格展示目标名称、最近错误、更新时间，并提供“一键重新启用”和“跳转到订阅管理”操作，方便人工修复。
  - 文档 `docs/DEV_PROGRESS_VABHUB.md` 已标记为 `v0.8 → 追加-6`，在 P6-3 勾选已完成事项，并保留 P6-4 / P7 / P8 作为下一阶段 TODO；同时修复部分 Markdown lint（标题与列表之间补空行等）。:contentReference[oaicite:0]{index=0}
  - 由于 `DATABASE_URL=sqlite:///./vabhub.db` 使用相对路径，已对仓库根目录的 `vabhub.db` 执行一次 `ALTER TABLE`，确保在仓库根目录运行脚本时不会缺少新列；后续新环境可以直接依赖 schema ensure 自动补列。

### 最近进度快照补充（2025-11-16，追加-7 补充）

- `frontend/src/services/graphqlClient.ts`、`music.ts` 与 `MusicCharts.vue` / `MusicSubscriptions.vue` 已全部用 GraphQL 数据通路改写，榜单视图支持历史批次、地区筛选，并在创建订阅后自动刷新订阅卡片；
- `Music.vue` / `MusicSubscriptions.vue` / `pages/MusicSubscriptions.vue` 组成的前端链路形成“榜单 → 订阅 → 自动下载”的最小闭环；`Subscriptions.vue` 补充 `media_type="music"` 过滤器；
- 新增 `GraphQLExplorer.vue` 页面（路由 `/graphql-explorer`，侧边栏入口“GraphQL 实验室”），内置多组预设查询，可直接调试 `musicSubscriptions` / `musicCharts` / `dashboardStats`；
- `backend/scripts/test_all.py` 输出更加明确的 ✅ / ❌ 提示，README 与文档同步推荐 `test_all.py --skip-music-execute` 为官方一键回归；
- `.github/workflows/test-all.yml` 上线，GitHub Actions 自动启动 uvicorn 并串跑 `test_all.py --skip-music-execute`，保证 PR 最低限度的后端回归。

---

### 与追加-6 对应的测试说明

- 在本地后端已运行且 `API_BASE_URL=http://127.0.0.1:8100` 时推荐执行：

  - `python backend/scripts/test_rsshub_minimal.py`
    - 当前没有真实 RSSHub 服务时会出现 `getaddrinfo failed`，脚本将其视为 WARNING，整体流程应成功结束，同时验证正常订阅 + 孤儿订阅两条链路的禁用逻辑。

  - `python backend/scripts/test_all.py --skip-music-execute`
    - 仍会看到既有的“创建订阅异常”打印以及 RSSHub 抓取相关 WARNING，属于历史重复数据问题；其余断言全部通过，可视为当前一键回归在无真实音乐下载环境下的“绿灯”状态。

- 运维提示：

  - 如需在真实环境验证 RSSHub 健康字段与订阅禁用逻辑，请确保后端完成一次重启，让新的 schema ensure 在目标数据库上执行；
  - 若在仓库根目录运行 CLI，请继续沿用根目录下的 `vabhub.db`，避免多份 SQLite 文件导致列缺失或数据不一致。

---

### 接下来交给 IDE 的重点 TODO（基于当前状态）

> 说明：P6-1 / P6-2 / P6-3 已基本落地，本节只强调后续需要继续推进的部分。:contentReference[oaicite:1]{index=1}

#### P7 / P8：保持原有规划不变，等待后续迭代

- P7：音乐 & GraphQL 前端接入
  - 目标：基于已有的 `musicSubscriptions` / `musicCharts` / `/music/charts/history` 能力，补完前端 GraphQL 封装与 `Music.vue` / 音乐订阅列表页面，让“音乐榜单 → 订阅 → 下载”在 UI 层闭环。（详细子任务已在 P7 小节列出，此处不重复展开）

- P8：测试脚本整合 & CI / 运维
  - 目标：把 `test_all.py` 固化为“一键回归”入口，并在 GitHub Actions / 文档中明确推荐用法，逐步引入简单 CI 流水线，保障核心链路稳定。（详细子任务已在 P8 小节列出，此处不重复展开）
说明：

P6（RSSHub 外键 + 健康检查）、P7（音乐 & GraphQL 前端接入）、P8（一键回归 + CI）已经有一轮落地；

下面的任务默认以当前 GraphQL 音乐链路 + test_all.py + CI 已可用为基线，继续做“加深”和“扩展”。

P9：音乐 & GraphQL 深度打磨（在现有闭环上加体验和能力）

P9-1. GraphQL 能力扩展（从只读到「轻写」）

- [x] **后端 Mutation**：`toggleSubscription` / `createMusicSubscriptionFromChart` / `triggerMusicSubscriptionRun` 已上线，并复用现有 Service。
- [x] **音乐链路**：`MusicCharts.vue` 通过 GraphQL Mutation 基于榜单条目建订阅，`MusicSubscriptionCard.vue` 支持 GraphQL 启用/禁用与手动执行。
- [x] **类型补完**：`MusicSubscriptionMutationPayload` / `MusicAutoDownloadPayload` 等返回结构可直接在 GraphQL Explorer 中查看。

P9-2. GraphQL Explorer 作为「调试 / 教学」工具强化

- [x] 预设查询覆盖订阅 / 音乐 / Dashboard / Scheduler / RSSHub Health；
- [x] Query、Variables、Result 支持一键复制，执行状态 + 错误明细集中展示；
- [x] Explorer 直接显示 GraphQL `errors`，便于排查。

P9-3. GraphQL 覆盖更多基础数据（为未来插件 / 可视化做铺垫）

- [x] 新增只读 Query：`schedulerTasks`、`rsshubSubscriptionHealth`、`logStreams`；
- [ ] 前端页面的 GraphQL/REST 开关仍保留 TODO（后续在 RSSHub / Scheduler 页面增加切换入口）。

P10：插件 PDK & 开发者体验（把「插件」真正做成可以用的产品能力）

目标：在已具备基础插件框架的前提下，补齐「规范 + 示例 + UI 管理」三件套，让第三方/未来的自己能愉快写插件。

P10-1. 插件接口与生命周期规范化

- [x] `app/core/plugins/spec.py` 提供统一的 `PluginMetadata` / `PluginContext` / `PluginHooks`，`hot_reload.py` 在加载时校验 metadata、注入上下文、调用 `register()`、`on_startup()/on_shutdown()`；
- [x] `plugins/example_pt_site.py` 作为官方示例，演示默认配置 + 日志输出。

P10-2. 插件管理前端 UI 完整一轮

- [x] Backend 新增 `/api/plugins/{name}/config`、列表返回 metadata & 状态，并允许启用/禁用热更新；
- [x] Frontend `Plugins.vue` 完成插件卡片、状态展示、热更新开关、重载/卸载操作以及简单 Key-Value 配置弹窗（写入 `PluginConfigStore`）。

P10-3. 文档与开发者指引

- [x] `docs/PLUGIN_PDK.md` 覆盖目录结构、Context 能力、调试流程，README 链接该文档；
- [x] `services/阶段2部署指南.md` 新增“插件部署与热更新”小节，提醒挂载 `plugins/` 目录、使用 UI 管理插件。

P11：统一「下载决策层」的中期目标（可以排在 P9/P10 之后）

这块是之前 P2 中提到但尚未完全收敛的部分，先简单挂个 TODO，等 P9/P10 稳定后再推进。

 在 app/modules/ 下新增 decision/ 模块，负责把：

订阅匹配结果（subscription.rule_engine）

质量对比（quality_comparison）

H&R 检测（hnr.detector）
三者统一封装成一个「下载决策」接口，例如 decide_download(candidate, context) -> DecisionResult。

 将订阅刷新 / 自动洗版 / HNR 相关 Scheduler 的核心判断逻辑，逐步迁移到 decision 模块，减少各处复制粘贴和分叉逻辑。

 在 DEV_PROGRESS_VABHUB.md 中新增一个专门小节描述“下载决策层”的设计目标和当前落地情况，方便后续迭代。

- 2025-11-16（追加-8）：插件 PDK & 插件管理 UI 初版完成
  - 插件框架规范化
    - 新增 `app/core/plugins/spec.py` 与 `config_store.py`，统一定义 `PluginMetadata / PluginContext / PluginHooks`。
    - `HotReloadManager` 在加载插件时会校验 `PLUGIN_METADATA`，并向插件注入 `PluginContext`，依次调用 `register() / on_startup() / on_shutdown()`。
    - 仓库内置官方示例 `plugins/example_pt_site.py`，演示元数据、配置初始化与生命周期钩子。
  - 插件管理 API / UI
    - 新增 `/api/plugins/list | /status | /{name}/config` 等接口，返回插件 `metadata`、当前配置与热更新状态。
    - 前端 `Plugins.vue` 改造为实用管理页：支持查看状态、启停热更新、重载 / 卸载插件，以及通过 JSON 方式编辑配置（写入 `PluginConfigStore`）。
    - 新增 `src/services/plugins.ts` 封装上述 API 调用。
  - 文档与指南
    - 编写 `docs/PLUGIN_PDK.md`，系统化说明插件目录布局、必需导出对象、`PluginContext` 能力与本地调试流程。
    - 在 `README`、`services/阶段2部署指南.md` 与 `docs/DEV_PROGRESS_VABHUB.md` 中补充插件规范引用，并将相关任务归为 P10，标记为已完成。
  - 测试现状与注意事项
    - 本轮未执行自动化测试；推荐在后端服务启动后运行：
      - `API_BASE_URL=http://127.0.0.1:8100 python backend/scripts/test_all.py --skip-music-execute`
    - 仓库中 `README`、阶段 2 部署指南等仍存在较多 Markdown lint 警告，本轮未统一清理，后续可集中在文档规范化阶段处理。

P11：短剧专用管线 & PT 插件实战（进行中）

目标：基于现有插件 PDK 和下载/重命名能力，打通一个「短剧」垂类的最小闭环：从 PT 订阅 → 下载器 → 重命名入库 → 前端展示。
产出一个可运行的“短剧样板插件”，给后续更多 PT 插件提供模板。

- 2025-11-17（追加-9）：短剧媒体类型打底  
  - 引入 `short_drama` 媒体类型、表结构自动迁移与统一的 `is_tv_like()` 判断。  
  - 订阅 / 下载 / RSS / Category / 日历 / 重命名 / Douban / 搜索链路均识别短剧，并延用电视剧策略。  
  - DownloadTask、GraphQL、REST 响应输出短剧元数据，Dashboard 新增 `total_short_drama` 统计。

P11-1：后端领域建模 & 类型打通

- [x] **P11-1-1：新增短剧媒体类型枚举**  
  - `app/constants/media_types.py` 统一收口媒体类型，新增 `short_drama`、`is_tv_like()` 等辅助方法。  
  - `subscriptions` / `download_tasks` / `media` 引入 `extra_metadata` / `media_type` 新列，并在启动时通过 `ensure_short_drama_columns()` 自动 `ALTER TABLE` 与回填。  
  - REST/GraphQL 的下载任务响应携带 `media_type` 与 `extra_metadata`，缓存、脚本、同步工具均写入 `short_drama`。
- [x] **P11-1-2：短剧元数据扩展（轻量版）**  
  - 订阅创建/更新支持 `short_drama_metadata`，统一落入 `extra_metadata.short_drama`，可记录单集时长、总集数、垂类标签。  
  - DownloadService/链路会把短剧元数据透传到下载记录与 WebSocket 推送，为后续重命名/前端展示留钩子。
- [x] **P11-1-3：下载 & HNR 规则兼容**  
  - Subscription、RSS、Category、日历、重命名、覆盖策略、搜索、公共索引器等所有 “电视剧” 分支改用 `is_tv_like()`，短剧共享刷新频率、过滤和评分逻辑。  
  - Douban/Search API 能以电视剧模式请求短剧内容；Dashboard 单独暴露 `total_short_drama`，以便监控短剧入库规模。  
  - 下载模块存储 `short_drama` media_type，GraphQL/REST 前端即可按需过滤短剧任务，为后续插件/前端闭环奠定数据面。

P11-2：短剧 PT 插件样板（基于现有 PDK）

- [x] **P11-2-1：短剧站插件骨架**  
  - 新增 `plugins/example_short_drama_site.py`，`PLUGIN_METADATA.tags` 指定 `short_drama`，`register()` 会深度填充默认配置并在启动/卸载阶段输出站点状态。  
- [x] **P11-2-2：插件配置结构**  
  - 默认配置覆盖 `site_url/site_name/auth/category_mapping/subscription_defaults/download_defaults`，并写入 `data/plugin_configs/example_short_drama_site.json`，便于在插件管理页直接调整。  
- [x] **P11-2-3：下载任务生成与 media_type 绑定**  
  - 插件导出 `create_subscription_payload()` 与 `create_download_payload()`，用于生成 `SubscriptionService` / `DownloadService` 的请求体，自动附带 `media_type="short_drama"` 与 `short_drama_metadata` / `extra_metadata.short_drama`。  
  - 下载偏好与 Episode span 会记录到 `extra_metadata`，方便后续重命名/可视化。

P11-3：重命名规则 & 媒体库入库策略

- [x] **P11-3-1：短剧专用命名模板**  
  - `MediaRenamer` 内置 `short_drama`/`shortdrama_default` 模板，格式：`短剧/{title}/S{season}/{title}.S{season}E{episode} {source} {quality}`，并自动推断 `episode_span`、S/E 默认值。  
  - 前端媒体整理页增加模板快捷选择，点击即可填入 `shortdrama_default` 或其它预设，方便在 API 调用中直接引用模板名称。
- [x] **P11-3-2：媒体库入库策略调整**  
  - `MediaOrganizer` 在未启用分类器时，会把 `media_type="short_drama"` 的文件放入 `目标目录/短剧`，与 `电影/电视剧/音乐` 并列。  
  - Dashboard 与 Media 模块保持 `short_drama` 统计，为后续媒体库展示单独挂载入口奠定基础。

P11-2：短剧 PT 插件样板（基于现有 PDK）

 P11-2-1：短剧站插件骨架

在 plugins/ 目录下新增一个官方示例插件（命名示例）：

plugins/example_short_drama_site.py

要求：

使用 PLUGIN_METADATA 正确声明自身为 "short_drama" 垂类（例如在 categories、tags 或自定义字段中体现）。

实现 register() 里基本的资源声明（搜索 / 订阅 / 解析 若暂时实现不了，可先只实现订阅解析链路）。

 P11-2-2：插件配置结构

在 PluginConfigStore 中为短剧插件预留一份默认配置结构，例如：

站点 URL / 站点名

所需的 auth cookie / token 占位字段

分类映射（短剧专区所用分类 ID）

在前端的插件管理页面中，能对这份 JSON 做基本编辑 & 保存。

 P11-2-3：下载任务生成与 media_type 绑定

让短剧插件在生成订阅 / 下载任务时：

明确写入 media_type="short_drama"。

如有需要，在任务 metadata 中标记“短剧系列名称 / 集数范围”。

P11-3：重命名规则 & 媒体库入库策略

 P11-3-1：短剧专用命名模板

在现有重命名系统中新增一个短剧模板（示例名称）：

shortdrama_default

规则示例：

目录：短剧/{series_title}/{series_title}.S01E01-E20.{source}.WEB-DL

单集文件：{series_title}.S01E{episode:02d}.{quality}.{group}.mkv

要求：

模板中如果 episode 范围不好准确获取，可以先用单集命名，后续再优化合并策略。

 P11-3-2：媒体库入库策略调整

入库时：

将 media_type="short_drama" 的条目归类到一个单独节点（如 “短剧” tab / section），避免混入长剧。

如已有 Library Type / Collection Type 枚举，同步扩展。

P11-4：前端短剧页面 & 过滤入口

- [x] **P11-4-1：短剧列表页 / Tab**  
  - 新增 `src/pages/ShortDrama.vue`，展示短剧订阅/下载总览、均值时长等指标，并支持状态/关键词筛选与一键跳转到订阅、下载、插件页面。  
  - 复用 `SubscriptionCard` + `v-data-table`，直接读取 `media_type="short_drama"` 的数据，形成闭环看板。
- [x] **P11-4-2：订阅 & 下载中心短剧过滤**  
  - `Subscriptions.vue` / `Downloads.vue` 增加短剧类型选项和路由 `?media_type=short_drama`，并在卡片/列表中以紫色徽章标识短剧。  
  - `DownloadList` 追加短剧标签，下载页支持“短剧”专用过滤芯片，便于快速聚焦。
- [x] **P11-4-3：插件入口联动**  
  - `Plugins.vue` 在带 `short_drama` 标签的插件卡片上新增“短剧工作台”直达按钮。  
  - App Drawer 中加入「短剧工作台」导航，并在插件卡片/侧边菜单标记 `NEW` 状态，便于测试与演示。

- [x] **P11-5：测试脚本 & 文档补充**
  - **P11-5-1：最小化短剧回归脚本**  
    - 新增 `backend/scripts/test_short_drama_minimal.py`，串联插件校验 → 创建短剧订阅 → 搜索/下载 → 媒体库补齐，自动确保 `subscriptions / downloads / media` 都至少存在一条 `media_type="short_drama"` 记录。  
    - 若搜索阶段尚未产生日志，脚本会自动补打一条短剧下载及媒体库记录，保证闭环验证可在纯本地 mock 数据下完成。
  - **P11-5-2：集成到 test_all.py**  
    - `test_all.py` 通过 `ENABLE_SHORT_DRAMA_TEST=1`（或命令行 `--with-short-drama`）即可追加运行短剧脚本，默认关闭避免 CI 被真实下载阻塞。  
    - 运行顺序追加在 RSSHub 自测之后，保持插件/GraphQL 回归 → 短剧闭环的节奏。
  - **P11-5-3：文档与操作指南**  
    - 本文档加入 P11-5 完成记录，并在 “快速回归” 章节提示新的环境变量。  
    - `docs/PLUGIN_PDK.md` 的短剧插件章节补充了脚本依赖 `example_short_drama_site` 的说明，便于外部开发者对齐示例。

### P12：插件生态扩展 & 文档规范化（基于 P10 已完成）

> 前提：
>
> - P10 已完成基础插件 PDK（`app/core/plugins/spec.py` / `config_store.py`）、热更新机制与 `Plugins.vue` 管理页。
> - 开发者指南已在 `docs/PLUGIN_PDK.md` 落地，可指导外部插件开发者接入。
> - 参考《VabHub 插件开发指南（Plugin PDK）》第 9 节“后续规划”。

- 2025-11-18（追加-10）：P12-1 插件模板与脚手架初版  
  - 仓库新增 `templates/plugin_pt_site/`，抽象 `PluginMetadata`、默认配置与日志输出，作为脚手架模板。  
  - `backend/scripts/create_plugin.py` 支持 `python backend/scripts/create_plugin.py my_pt_plugin --name "My PT Plugin"` 创建骨架并提示后续步骤。  
  - `docs/PLUGIN_PDK.md` 增加「快速上手：脚手架创建插件」章节，同时调整「注意事项 / 后续规划」编号以匹配最新结构。

#### P12-1：插件模板仓库与脚手架命令

- [x] 在当前仓库旁新建官方插件模板仓库（或子目录），例如：  
  - 仓库：`vabhub-plugin-template-pt-site`（独立 Git 仓库，便于 fork）  
  - 或目录：`templates/plugin_pt_site/`（包含最小可运行插件骨架）  
- [x] 模板内容基于现有 `plugins/example_pt_site.py` 抽象：  
  - 使用占位符保留 `id/name/version/description/author/tags` 等字段；  
  - 提供一个最小化的 `register(context: PluginContext)` 实现，仅演示配置读写与日志输出。  
- [x] 新增脚本 `backend/scripts/create_plugin.py`：  
  - 用法：`python backend/scripts/create_plugin.py my_cool_plugin --from-template pt_site`  
  - 功能：复制模板文件到 `plugins/my_cool_plugin.py` 并替换元数据占位符。  
  - 输出：在控制台打印新插件路径与下一步操作提示（例如“请在 Plugins 管理页启用该插件”）。  
- [x] 在 `docs/PLUGIN_PDK.md` 中追加「快速上手：脚手架创建插件」小节，示例完整命令与预期界面效果。  

#### P12-2：插件 REST / GraphQL 扩展点

- [x] 扩展 `PluginHooks` 以支持 API 注册钩子（示例）：  
  - 在 `app/core/plugins/spec.py` 中为 `PluginHooks` 增加可选字段：  
    - `register_rest(router: APIRouter) | None`  
    - `register_graphql(schema_builder: GraphQLSchemaBuilder) | None`（具体类型按现有 GraphQL 实现适配）  
- [x] 在插件加载流程中（HotReloadManager）：  
  - 若插件返回 `register_rest`，在主应用启动时把该函数挂载到统一的 `/api/plugins/{plugin_id}/...` 命名空间下；  
  - 若返回 `register_graphql`，在构建 GraphQL Schema 时注入插件扩展。  
- [x] 在 `docs/PLUGIN_PDK.md` 中新增「高级用法：扩展 REST / GraphQL API」章节：  
  - 提供一个示例插件，演示如何暴露查询/Mutation；  
  - 说明命名规范与权限边界（例如不得直接修改核心业务表结构）。  
- [x] 为插件扩展点补充最小化自动化测试：  
  - 在 `backend/tests/test_plugins_api.py` 中添加：  
    - 加载 `example_extension_plugin` 并断言 `/api/plugins/example_extension_plugin/ping` 可用；  
    - 对 GraphQL 扩展点发送 `pluginEcho` 查询，验证返回值。  
  - `backend/scripts/test_all.py` 已串联该脚本，确保回归时覆盖插件扩展面。  

#### P12-3：官方插件索引与一键安装（中期）

- [x] 设计插件索引数据结构，例如：  
  - `templates/plugin_registry.json`：  
    - `id` / `name` / `description` / `version` / `homepage` / `tags` / `download_url` 等字段。  
- [x] 后端：新增插件索引相关 API：  
  - `GET /api/plugins/registry`：返回可用插件列表；  
  - `POST /api/plugins/registry/install`：根据 `id` 或 `download_url` 下载插件 `.py` 到 `plugins/` 目录（本地环境可简单走 HTTP 下载 + 校验）。  
- [x] 前端 `Plugins.vue` 扩展「插件市场」视图：  
  - 新增“官方插件/本地(社区)插件”面板，消费注册表接口并提供安装按钮；  
  - 安装操作当前以占位流程触发后端 `POST /api/plugins/{id}/install`，安装后自动刷新本地插件列表。  
- [x] 安全 & 运维注意：  
  - `PLUGIN_REMOTE_INSTALL_ENABLED` 默认关闭，文档加入白名单示例与文件大小限制（`PLUGIN_INSTALL_MAX_BYTES`）；  
  - 部署指南与 PDK 均要求审阅源码/指定允许域名后再启用远程安装。

#### P12-4：文档 Markdown lint & 规范化（低优先级但建议完成）

- [x] 在仓库根目录新增 `package.json` + `.markdownlint.json`，集成 `markdownlint-cli` 并提供统一命令：  
  - `npm install && npm run md:lint` 会对 `README*.md`、`docs/**/*.md`、`services/**/*.md` 执行校验。  
- [x] 针对核心文档调整规则并确保可通过检查：  
  - `README.md`、`docs/DEV_PROGRESS_VABHUB.md`、`docs/PLUGIN_PDK.md`、`services/阶段2部署指南.md` 在新规则下无阻塞错误。  
- [x] 新增 `docs/CONTRIBUTING.md`，要求贡献前执行 `npm run md:lint`，并列出常见 Markdown 风格注意事项。  
---

## 追加-13：下一阶段任务草案（基于 2025-11-16 版本）

> 前置基线：  
> - P6：RSSHub 外键修复 + 健康检查闭环已落地，`test_rsshub_minimal.py` + `fix_rsshub_fk.py` 可用于自愈与巡检。  
> - P7：音乐 GraphQL + 前端接入已完成，`Music.vue` / `MusicCharts.vue` / `MusicSubscriptions.vue` 走 GraphQL 数据源。  
> - P8：`test_all.py` + GitHub Actions CI 已可用，`--skip-music-execute` 下核心链路绿灯。  
> - P9 / P11（短剧）：`short_drama` 媒体类型 + 短剧 PT 样板插件 + 重命名 / 入库策略已打通一条最小闭环。  
> - P10 / P12：插件 PDK + 插件管理 UI + 官方插件索引 & 一键安装已上线。

接下来优先解决两件事：

1. 把早期挂在 P11 的「下载决策层」真正做成独立模块，而不是散落在各个 Scheduler 里。
2. 把生产环境的“安装 / 迁移 / 可选依赖 / 测试噪声”收一收，降低新环境踩坑成本。

### P13：统一「下载决策层」与洗版 / H&R 规则（承接早期 P11 草案）

> 目标：  
> - 把订阅规则匹配、质量比较、H&R / 洗版决策统一收敛到一个 `decision` 模块。  
> - 外部（Scheduler / 插件 / 前端触发的“立即洗版”）只需要调用一个 `decide_download(candidate, context)`，拿到清晰的决策结果，而不是在各处重复判断逻辑。

#### P13-1. decision 模块骨架与领域建模

- [x] 在 `backend/app/modules/decision/` 新增模块（示例结构）：  
  - `backend/app/modules/decision/__init__.py`  
  - `backend/app/modules/decision/models.py` （定义 `DecisionInput` / `DecisionContext` / `DecisionResult` 等 Pydantic/Dataclass）  
  - `backend/app/modules/decision/service.py` （核心决策函数）

- [x] 在 `service.py` 中抽象统一入口：  

  - `async def decide_download(candidate: DecisionInput, context: DecisionContext) -> DecisionResult:`  
    - 内部串联三块现有能力：  
      - 订阅规则匹配（原 `subscription.rule_engine`）  
      - 质量对比 / 洗版优先级（原“洗版优先级规则组”等逻辑）  
      - H&R 风险检测（原 `hnr.detector` 或相关策略）  
    - `DecisionResult` 至少包含：  
      - `should_download: bool`  
      - `reason_code: str`（如 `ok_new`, `ok_upgrade`, `reject_inferior`, `reject_hnr_risk` 等）  
      - `selected_quality` / `current_quality` 等方便日志展示的字段。

- [x] 在 `docs/DEV_PROGRESS_VABHUB.md` 单独新增一小节「下载决策层设计说明」，画清楚：  
  - 决策输入是什么（候选种子 / 当前已有任务 / 用户偏好）  
  - 决策输出是什么（下载 / 跳过 / 替换 / 停用订阅 等）  
  - 与 Scheduler / 插件的调用关系。

> 进展说明：`DecisionService` 已经初步集成订阅规则引擎、质量比较与 HNR 检测，暴露 `decide_download()` 供调度器与插件调用。下一步将补充设计说明、REST/GraphQL 调试入口与测试脚本，随后推动 Scheduler 渐进迁移。

##### 下载决策层设计说明

- **输入结构**：  
  - `DecisionCandidate`：由搜索结果/索引器或插件提供的候选条目，包含 `title/quality/resolution/seeders/site` 等基础属性以及原始 `raw` 字段。  
  - `DecisionContext`：由订阅/调度器构造，带入订阅偏好（质量/分辨率/规则组）、当前活跃任务 & 媒体库条目列表 (`existing_items`)、以及 H&R 检测所需的 `site/badges/html` 等信息。  
  - 可选的 `user_preferences` 用于后续扩展，例如不同用户对可疑 HNR 的容忍度。

- **决策流程**：  
  1. 调用 `RuleEngine.match_result()` 依据订阅规则做初筛；  
  2. 检查 `existing_items` 判断是否重复下载，随后比较质量并打分（`score` / `reason`）；  
  3. 使用 `HNRDetector.detect()` 评估风险，必要时直接阻断；  
  4. 生成 `DecisionResult`，包含 `should_download`、`reason`、`message`、标准化质量与调试上下文。

- **输出使用方式**：  
  - `should_download=True`：Scheduler 继续下发下载任务，同时记录 `reason` 与 `score`；  
  - `should_download=False`：Scheduler 直接跳过候选，对 `reason` 做分级日志上报，例如 `RULE_MISMATCH / QUALITY_INFERIOR / HNR_BLOCKED`；  
  - `debug_context` 仅在 DEBUG 模式下输出，便于排查。

- **与 Scheduler / 插件的关系**：  
  - Scheduler（订阅刷新、洗版、HNR 补种）在筛选候选资源时统一通过 `DecisionService` 做判定；  
  - 插件可直接调用 `decide_download()` 做“Dry-run”以便在 UI 中展示是否值得下载；  
  - 后续 REST/GraphQL 调试接口也会复用相同入口，确保决策逻辑唯一。

#### P13-2. Scheduler 调用路径渐进迁移

- [x] 在以下模块中，增加一层“调用 decision 模块”的适配层（避免一次性大改）：  
  - `app/modules/scheduler/subscription_refresh.py`  
  - `app/modules/scheduler/wash_tasks.py`（若存在类似“洗版调度器”）  
  - `app/modules/scheduler/hnr_tasks.py` / `update_hnr_tasks` 等。

- [x] 第一阶段策略：  
  - 保留旧逻辑，但在关键分支处**优先调用 `decide_download()`**，并在日志中打印 `DecisionResult.reason_code`。  
  - 若决策层返回 `None` / 异常，再回退旧逻辑（避免一次性引入新 bug）。

- [ ] 第二阶段（可在后续追加条目中执行）：  
  - 清理 Scheduler 中与“质量比较 / H&R 判断”重复的代码，逐步以 decision 模块为准。  
  - 将“洗版规则组 / H&R 策略”等配置项搬到一个统一配置结构中（可挂在 `DecisionContext` 或独立 `decision_settings.py`）。

> 进展说明：当前已在 `SubscriptionService.execute_search()` 的自动下载流程中接入 `DecisionService`，Scheduler 触发搜索时会先执行决策层并记录 `reason`，若判定为 `RULE_MISMATCH / QUALITY_INFERIOR / HNR_*` 将直接跳过下载。其他调度入口会在下一阶段持续迁移。

- 2025-11-22：RSS 自动下载流程也完成决策接入  
  - `RSSSubscriptionService._process_rss_item()` 在匹配订阅后会构建候选信息并调用 `DecisionService`。  
  - 若决策返回 `should_download=False`，RSS 项会记录原因并跳过下载；若允许，将 `decision` 元数据写入下载任务。  
  - 该逻辑由 Scheduler 的 `check_rss_subscriptions` 定时任务触发，确保 RSS → 下载路径沿用统一的下载决策层。

#### P13-3. 日志与调试能力

- [x] 在 `DecisionResult` 中增加 `debug_context: dict | None` 字段（仅在 DEBUG 级别输出），记录：  
  - 各候选质量评分 / 评分来源  
  - 命中的订阅规则 ID / 规则组名称  
  - H&R 检测的关键指标（做过适当脱敏）

- [x] 为下载决策新增一个简单的 GraphQL/REST 调试接口（只读）：  
  - 例如：`POST /api/decision/dry-run`  
  - 请求体输入一个候选种子（站点/标题/质量/做种数等），响应为 `DecisionResult`，方便本地 / Web UI 做“Dry-run 决策测试”。

- [x] 新增脚本 `backend/scripts/test_decision_minimal.py`：  
  - 构造几组典型场景：  
    - 质量升级 vs 降级  
    - H&R 风险 vs 安全  
    - 规则命中 vs 未命中  
  - 打印决策结果并校验 `should_download` 与 `reason_code` 是否符合预期。

> 进展说明：`POST /api/decision/dry-run` 已可复用订阅上下文执行决策并返回可选的 `debug_context`，`test_decision_minimal.py` 覆盖规则命中/降级/HNR 等场景并已串入 `test_all.py`。GraphQL 调试入口可作为后续增强。

- 2025-11-22：GraphQL 新增 `decisionDryRun` Mutation，沿用 REST 入口能力，可在 `GraphQLExplorer.vue` 直接提交候选参数并查看 `DecisionResult`。

---

### P14：安装 / 迁移 / 可选依赖的生产化收尾（承接 TEST_FIX_REPORT 建议）

> 目标：  
> - 把目前分散在多个 `schema_utils.ensure_*` / 服务内部的自动迁移逻辑，统一到一个可重复执行的“迁移入口”。  
> - 明确 Redis / RSSHub / 下载器等外部服务的「可选性」，防止在未部署时影响主链路。  
> - 让 `test_all.py` 在各种“半配置”环境下都尽量是“可跑可读”的状态。

#### P14-1. 统一迁移入口（Migration Manager）

- [x] 在 `backend/app/core/` 下新增 `migrations/` 模块（或 `schema_migrator.py`），集中封装：  
  - 短剧字段补齐（现有 `short_drama/schema_utils.ensure_*`）  
  - 音乐相关列补齐（现有 `music/service.py` 内部自动 `ALTER TABLE`）  
  - RSSHub 健康字段 / legacy 源占位等结构性变更。

- [x] 新增 CLI 脚本 `backend/scripts/migrate.py`：  
  - 接受 `--dry-run` / `--verbose` 等参数；  
  - 默认按顺序执行所有迁移步骤（幂等设计，重复执行不出错）；  
  - 最终输出 JSON 摘要（与 `fix_rsshub_fk.py` 风格一致），方便日志检索。

- [x] 在 `services/阶段2部署指南.md` + README 中补充：  
  - 建议在部署 / 升级后，执行：  
    - `python backend/scripts/migrate.py --dry-run`  
    - 如无异常再执行 `python backend/scripts/migrate.py`  
  - 并说明该脚本与 `fix_rsshub_fk.py` 的关系（一个偏结构迁移，一个偏数据修复）。

> 进展说明：`app/core/migrations/steps.py` 汇集短剧、音乐、RSSHub 三类结构步骤，`run_migrations()` 统一调度，`backend/scripts/migrate.py` 可输出 JSON 报告并支持 dry-run。README 与阶段2部署指南均已加入执行示例与动作顺序（迁移 → fix_rsshub_fk）。

#### P14-2. 可选依赖（Redis / RSSHub / Downloader）的配置开关梳理

- [x] 把现在分散的配置开关梳理为统一文档 + 代码：  
  - Redis：`REDIS_ENABLED`（已有），默认开启，缺服务时自动降级 + 一次性 WARNING。  
  - RSSHub：增加 `RSSHUB_ENABLED` / `RSSHUB_BASE_URL` 等显式开关；禁用时相关 Scheduler 不再报错，只输出 INFO。  
  - 下载器：若没有绑定实际下载后台（qbittorrent/transmission 等），在 UI / API 中清晰提示当前为“模拟模式”。

- [x] 在 `backend/scripts/test_all.py` 中：  
  - 根据环境变量自动跳过需要真实外部服务的测试用例（给出 SKIP 说明，而不是裸 500）。  
  - 在报告尾部打印“当前环境缺少：Redis / RSSHub / Downloader”等摘要，方便判断是环境问题还是代码问题。

- [ ] 在 `TEST_FIX_REPORT_*.md` 的下一版里，补充“如何在生产环境下按开关排查问题”的建议，作为长期运维文档的一部分。

> 进展说明：  
> - 配置层新增 `RSSHUB_ENABLED` / `RSSHUB_BASE_URL`，`RSSHubService`、GraphQL、REST API 及 Scheduler 均在禁用时返回一致的“RSSHub 已禁用”提示，并跳过后台任务。  
> - `RSSHubClient` 默认读取 `settings.RSSHUB_BASE_URL`，避免散落的环境变量。  
> - `DownloadService` 自动检测 qBittorrent/Transmission 配置是否仍为默认值，未绑定实际下载器时以“模拟模式”入库并在 `/api/downloads` 的 `meta.simulation_mode` + 创建任务响应中显式提示，前端可据此渲染警告。  
> - README 补充了 Redis/RSSHub/下载器的可选开关介绍，阶段2部署指南延续了 migrate → fix_rsshub_fk 的步骤。

#### P14-3. 测试降噪与可视化汇总

- [x] 进一步清理 `test_all.py` 中的历史噪声输出：  
  - 对已知的“创建订阅异常”（历史脏数据）升级为结构化 WARNING，并在报告栏目中归一统计。  
  - 避免在正常通过时刷大量栈追踪。

- [x] `test_all.py` 生成可消费的结构化报告：  
  - 追加 `--report-path` 将执行摘要（环境缺失、各脚本耗时、警告列表）写为 JSON，供后续前端 / CI 读取。  
  - 为“系统自检”页面预留后端接口（REST/GraphQL）并串联 `test_all` 最新结果。

- [x] 在 `frontend` 中考虑新增一个只读“系统自检”页（可选）：  
  - 通过 GraphQL / REST 调用 `test_all` / 健康接口的轻量版，展示：  
    - 数据库迁移状态 / 缺失列检查  
    - Redis / RSSHub / Downloader 检查结果  
    - 最近一次 `test_all` 的执行时间与结果概要。

> 进展说明：  
> - `test_all.py` 现已自动聚合“创建订阅异常 / Redis 连接失败 / Scheduler task does not exist”等常见噪声，并在脚本尾部打印摘要。  
> - 新增 `--report-path` 参数，可输出结构化 JSON 报告（含环境依赖、跳过项、各子脚本耗时与告警），为后续系统自检/CI 可视化准备数据源。  
> - 后端提供 `GET /api/system/selfcheck` + GraphQL `systemSelfCheck` 两种入口，聚合可选依赖、Schema 自检与最新 `test_all` 报告；前端加入 `SystemSelfCheck.vue` 页面（侧边栏“系统自检”），可视化展示结果。
> 这部分暂时不要求 IDE 立刻动手，只作为「阶段 3」的方向占位，等 P13 / P14 稳定后再展开。

---

### P15：中期规划预留（多媒体扩展 & 插件生态深度化）

- [ ] P15-1：电子书 / 有声书最小闭环  
  - 规划新的 `media_type="book"/"audiobook"`，以及最小字段（作者 / 出版社 / ISBN / 语言）。  
  - 先不做复杂刮削，只打通“订阅 → 下载 → 重命名 → 入库 → 前端列表”。

- [ ] P15-2：漫画集成与 Suwayomi 互通（可选）  
  - 调研是否通过插件方式对接现有漫画后台（如 Suwayomi），由插件负责抓取 / 转封装为 VabHub 的 DownloadTask。  
  - 前端媒体库增加基础的漫画展示入口。

- [ ] P15-3：插件商店与版本管理增强  
  - 在现有官方插件索引基础上，引入版本约束 / 兼容性标记（要求最低 VabHub 版本、依赖库等）。  
  - 在 Plugins.vue 中增加“可升级插件”视图与更新提示。

---

### 与追加-13 对应的测试建议

在后端已启动且完成一次迁移（`migrate.py`）后，推荐执行：

- `API_BASE_URL=http://127.0.0.1:8100 python backend/scripts/test_decision_minimal.py`  
  - 验证下载决策层的基础场景是否符合预期。

- `API_BASE_URL=http://127.0.0.1:8100 python backend/scripts/test_all.py --skip-music-execute`  
  - 观察报告中是否新增了决策层相关的统计项；  
  - 确认在未配置 Redis / RSSHub / Downloader 的环境下，测试以 WARNING / SKIP 形式优雅收尾。

> 说明：如果 IDE 发现本段任务与实际代码结构有偏差（例如某些模块尚不存在），请优先对齐本文件与目录结构，再开始编码；任何重构请同步更新本段，保持项目“记忆”一致。
