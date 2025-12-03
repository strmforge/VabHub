<!--
VabHub 系统总览（单一事实来源）

用途：
- 给人类 + 各种 AI/IDE（ChatGPT、Windsurf、SWE-1.5 等）快速理解当前版本 VabHub 的整体结构和完成度。
- 新聊天窗口 / 新任务书，应优先阅读本文件，而不是重新猜项目是干什么的。

【重要约定：面向"写任务书的 AI / IDE"】
1. 任何为 VabHub 编写「任务书 / Phase 任务 / 大任务说明」的 AI / IDE，
   都必须在任务书中加入一个专门的小节：
   标题固定为：`PZ. 文档更新要求（必须执行)`。
2. 该小节的内容至少要包含：
   - 要求执行任务的 IDE / Agent 在任务完成后：
     - 更新本文件 `docs/VABHUB_SYSTEM_OVERVIEW.md` 中相关模块的状态与要点；
     - 在「7. 最近里程碑」中追加一条简短记录；
     - 如涉及前端路由 / 页面结构，还需更新 `docs/FRONTEND_MAP.md`（如存在）。
3. 若你是一个"新窗口"中的 AI / IDE：
   - 请先完整阅读本文件；
   - 在编写任何 VabHub 相关任务书时，务必遵守上面的规则，并把 `PZ. 文档更新要求` 小节写入任务书中。

维护约定（执行任务的 IDE / Agent 请遵守）：
1. 本文件只做「高层总览」，不要塞长代码或大段实现细节。
2. 每完成一轮明显的功能任务（例如某个 P0–Px 阶段、某个 *-1 大任务书），
   - 必须至少更新：
     - 3. 核心模块地图：相应模块的状态标记（[DONE]/[WIP]/[PLANNED]/[LEGACY]）。
     - 7. 最近里程碑：追加 1 条不超过 2 行的简短描述。
3. 控制本文件总长度在 ~4000–6000 字符以内，必要时把旧的里程碑移动到 `docs/VABHUB_HISTORY.md`。
4. 不要改动各小节标题编号，便于其他工具定位（例如 "见 5. 工作流 & RSSHub"）。
-->

# VabHub 系统总览 v1.2.1

> 面向 NAS/PT 玩家的本地优先「搜索 · 下载 · 媒体库」自动化中枢。  
> 以影视 / 音乐 / 小说 / 漫画 / 有声书为核心媒体库，同时支持 PT 站上的其它资源（游戏 / 工具软件等）的统一搜索与下载（非媒体资源只做下载与任务管理，不做细致库管理）。

---

## 0. 使用说明（给 AI / IDE）

> 如果你是一个新窗口中的 ChatGPT / AI Agent / IDE 助手，请先阅读本节，再执行任何 VabHub 相关任务。

1. 本文件是 VabHub 的「单一事实来源」高层总览。  
   在编写任务书、规划 Phase、分析模块之前，请先通读本文件。
2. 当你要为 VabHub 编写任何「任务书 / 大任务说明」时，必须在任务书末尾添加一个固定小节：
   - 标题：`PZ. 文档更新要求（必须执行）` 
   - 内容：要求执行任务的 IDE / Agent 在任务完成后：
     - 更新本文件 `docs/VABHUB_SYSTEM_OVERVIEW.md` 的相关模块状态与要点；
     - 在 **7. 最近里程碑** 中追加一条记录；
     - 如涉及前端路由 / 页面结构，更新 `docs/FRONTEND_MAP.md`（如存在）。
3. 若你是执行任务的 IDE / Agent：
   - 完成开发后，务必按照任务书中的 `PZ. 文档更新要求` 小节修改本文件；
   - 确保文档描述与实际代码状态一致，避免出现"功能已删除但文档仍在宣传"的情况。

---

## 1. 项目定位 & 目标用户

- **目标用户**：有一定折腾能力的 NAS / PT 玩家（群晖 / 绿联 / 自组机 / 软路由人群），不是零基础小白。
- **核心定位**：
  - 统一管理：影视、剧集、音乐、小说、漫画、有声书、下载任务、通知、第三方源。
  - 打通：PT 站点、RSSHub、下载器、云盘（115 等）、本地媒体库、Telegram Bot。
  - 提供闭环自动化：  
    搜索 → 订阅 → 下载 → 整理入库 → 媒体浏览 / 阅读 / 听书 / 追更 → 通知与远程控制。
- **愿景**：
  - 对标并超越 MoviePilot：  
    更强调 **Local-first、自托管、不依赖单一外部服务**，  
    提供站点 AI 适配、本地智能大脑、插件生态等扩展能力。

---

## 2. 技术栈速览

- **后端**：Python 3.11+ / FastAPI / SQLAlchemy 2 / Alembic / APScheduler
- **前端**：Vue 3 / TypeScript / Vite / Vuetify 3 / Pinia
- **数据层**：PostgreSQL / SQLite（开发） / Redis（可选缓存）
- **任务 / 消息**：Celery（部分异步任务）、APScheduler（定时任务）
- **外部集成**：
  - 下载器：qBittorrent / Transmission 等
  - 云盘：115 等（通过远程播放 / 挂载）
  - Telegram Bot：音乐/阅读控制台、通知入口
  - CF adapter + 硅基流动：站点 AI 适配专用

---

## 3. 核心模块地图（状态总览）

> 状态标记：  
> **[DONE]** 已有完整后端 + 前端入口，日常可用  
> **[WIP]** 已有后端能力，前端/体验未完全  
> **[PLANNED]** 有设计意图 / 文档，但未实装  
> **[LEGACY]** 老版本能力，部分通过适配保留

### 3.1 设置 / 安全策略 / 本地策略

- **设定模块（Settings）** – [DONE]  
  - 全局下载规则（路径、命名、整理行为、STRM 策略）。  
  - HR 安全配置（是否保留源文件、何时强制 COPY 等）。  
  - 分辨率 & 质量偏好、字幕/音轨语言偏好。  
  - 云盘 / 下载器 / 外部服务（TMDB 等）的连接配置。
- **HR / HNR 安全系统** – [DONE]  
  - HNR 规则检测、做种统计与风险标记。  
  - 根据 HR / H&R 状态调整整理策略（MOVE → COPY 等）。  
  - 与 Local Intel、TorrentIndex、下载管理深度联动。

### 3.2 站点管理 & 站点 AI 适配

- **站点管理 v1（Site Manager）** – [DONE]  
  - 站点墙 UI：展示所有已配置 PT 站点的状态、类型、图标等。  
  - 站点访问配置：Cookie / UA / Host / Proxy / CookieCloud 联动。  
  - SiteStats / SiteAccessConfig 等统计与访问参数。  
  - 基础健康检查：连通性、错误统计。
- **站点 AI 适配（Site AI Adapter + CF adapter）** – [DONE / WIP]  
  - 远端 CF Pages + 硅基流动 Qwen2.5-Coder-7B-Instruct，仅用于**站点页面结构解析**（列表/详情/HR 页）。  
  - 本地缓存 + 频率控制：同一站点不会频繁重算，仅在必要时刷新。  
  - 暂不对其他功能开放，是面向所有 VabHub 用户的"站点适配福利专线"。

> 📌 **站点管理 / Local Intel / External Indexer / HR 安全策略** 的完整关系说明详见 `docs/SITE_INTEL_OVERVIEW.md`。

- **站点诊断 / 云大脑 v1（共享识别词 + 分布式抓取设想）** – [LEGACY]  
  - 初始整体构想：
    - 每个用户在本地只抓取 **自己有账号的 PT 站** 的目录信息；  
    - 云端根据"用户拥有哪些站点"来做 **任务分配**：  
      - 比如 A、B、C 三个用户都上了同一个站，云端就把这个站的不同页 / 不同时间片拆分给这几个人抓；  
      - 目的是"大家一起帮忙扫完各自能访问的站点"，尽快完成全站覆盖。  
    - 所有用户的抓取结果汇总到云端，由云端统一整理成"站点资源视图 + 识别词大脑"。  
  - 数据形态演进设想：
    - 早期 PoC 可能会在云端短暂保留更多原始字段（标题、分类、大小等）用于建模；  
    - 后续设计趋向收紧：只上传**抽象特征**（标题别名、命名习惯、识别词、HR/HNR 行为模式等），  
      避免构造出可直接还原"某用户完整站点目录"的数据。  
  - 搜索链路的理想形态：
    - 用户在 VabHub 里发起搜索时：  
      1. 客户端先请求云端大脑；  
      2. 云端根据"该用户配置了哪些 PT 站点"过滤可用数据，只在**用户自己拥有的站点集合**内给出结果；  
      3. 若云端已有索引 → 直接秒回结果；  
      4. 若云端数据缺失 / 过旧 → 由本地或在线站点搜索兜底（触发增量抓取或临时实时搜索）。  
    - 目标体验：用户搜索时"优先命中云端汇总的识别经验"，仅在必要时再访问真实站点。  
  - 权限边界的原则：
    - 即使云端维护了"全局视图"，**每个用户仍然只能看到自己能登录的那些站点的结果**；  
    - 云端不会变成"帮你搜所有站"的超级 PT 聚合搜索，而是共享"识别经验"和"谁大概有货"的统计。  
  - 现状：
    - 出于成本与合规考虑，当前版本**完全停用了云端聚合与上传部分**；  
    - 不再做任何跨用户的抓取任务分配与目录汇总；  
    - 仅保留本地全站抓取（TorrentIndex）作为个人智能索引与安全决策基础（见 4. 本地智能大脑）。  
    - 仓库中仍保留 `services/intel_center` / `services/mesh_scheduler` 等目录，仅作为历史 PoC 与未来设计参考，不应在现版直接启用。  
  - 未来可能的方向（仅作为设想，不承诺实现）：
    - 通过**公开规则包 / 别名词典 / Git 仓库**等形式，构建「共享识别词大脑 v2」，  
      以规则和词典的方式共享"识别经验"，而不是共享任意用户的站点目录数据或抓取任务。

### 3.3 下载管理 & 媒体管理

- **下载管理中心** – [DONE]  
  - 多下载器任务列表（进度、速率、错误等）。  
  - 任务状态：下载中 / 完成 / 失败 / 种子被删 / HNR 风险。  
  - 与 HR/HNR、STRM 策略联动，阻止危险操作（误删源、影响保种等）。  
  - 前端页面已全面对接真实API，支持搜索、过滤、批量操作。
- **订阅中心（电影 / 电视剧 / 音乐 / 书籍等）** – [DONE]  
  - "订阅管理"模块按媒体类型拆分为"电影订阅 / 电视剧订阅 / 音乐订阅 / 书籍订阅"四个子页面。  
  - 使用卡片视图展示订阅进度（电视剧显示总集数/已下载集数，电影显示入库状态）。  
  - 新订阅通过搜索结果、规则中心、AI 订阅助手创建，订阅管理模块主要用于查看与管理。  
  - 与搜索、下载、整理、通知联动，形成自动下载闭环。  
  - 前端所有订阅子页面已完成API对接，支持实时状态展示和操作。
- **RSS 订阅** – [DONE]  
  - RSS源管理、订阅创建、状态监控。  
  - 前端RSSSubscriptions.vue已对接真实API，支持增删改查和健康检查。
- **RSSHub 子系统** – [DONE]  
  - RSSHub源管理、组合订阅、健康监控。  
  - 前端RSSHub.vue已完整对接API，支持源启用/禁用和预览功能。
- **工作流系统** – [DONE]  
  - 下载/整理流程的事件驱动工作流。  
  - 前端Workflows.vue已对接API，支持工作流创建、编辑、执行和状态管理。
- **媒体整理 / 媒体管理模块** – [DONE]  
  - 下载完成 → 自动或手动触发"整理入库"（重命名、刮削、移动/复制）。  
  - 显示整理完成 / 失败状态，支持失败后重试/人工干预。  
  - 仅对"媒体类资源"（影视/动漫/音乐/书籍/有声书/漫画等）做深度入库。
- **媒体质量比较 / 洗版辅助** – [DONE / WIP]

> 📌 **完整的下载→整理→入库→播放流水线说明**，详见 `docs/DOWNLOAD_MEDIA_PIPELINE_OVERVIEW.md`。
- **媒体质量比较 / 洗版辅助** – [DONE / WIP]  
  - 后端提供质量比较模块和 API，可对候选文件进行解析打分，选出"质量最优"版本，用于后续洗版和版本替换策略。  
  - 目前主要被下载/整理/订阅逻辑与调试工具使用，尚无专门的前端可视化页面。
- **非媒体资源支持（游戏 / 软件等）** – [WIP/设计中]  
  - 目标：在全局搜索 + 下载管理中支持查看与下载非媒体类资源，以通用列表形式展示。  
  - 不进入媒体库，仅由下载管理负责任务状态和文件路径。  
  - 现状：后端索引与分类已能区分非媒体资源，UI 侧尚无独立"其他资源"视图，主要通过通用下载任务/搜索结果呈现。

### 3.4 媒体库 & 阅读 / 收听中心

- **影视 / 电视墙 + 播放器** – [DONE]  
  - 电视墙：聚合电影/剧集/短剧海报墙、多维筛选。  
  - 短剧工作台：归属影视中心，用于短剧内容管理。
  - 播放器：本地媒体播放 + 115 远程播放（HLS + hls.js），可从详情页直接进入。
  - 电视墙播放策略（局域网媒体库优先 / 外网 115 播放）详见 `docs/TV_WALL_PLAYBACK_OVERVIEW.md`。
- **音乐中心 + 自动循环订阅** – [DONE]  
  - 音乐订阅规则（按榜单/RSS/PT 源）。  
  - MUSIC-AUTOLOOP：自动循环下载、清理与规则执行。  
  - Telegram 音乐控制台（TG-BOT-MUSIC-1）已完成。
- **小说 / 电子书 / 有声书中心** – [DONE]  
  - TXT/EPUB → EBook → TTS → 有声书整链路（NovelToEbookPipeline + TTS Runner）。  
  - 小说中心 v2：统一展示电子书列表、TTS 状态、听书进度。  
  - 有声书播放器 + `UserAudiobookProgress`：精确进度管理。
- **漫画中心 + 第三方源接入** – [DONE]  
  - MangaSource 适配框架：支持接入 Komga / Kavita / OPDS / Suwayomi 等自建服务。  
  - `UserMangaFollow` + 追更 Runner + `MANGA_UPDATED` 通知已打通。  
  - 漫画阅读进度追踪；漫画中心 UI v1 可用，第三方源配置的高级功能按 Phase 迭代。
- **Shelf Hub & 统一阅读控制** – [DONE]  
  - 统一管理小说 / 漫画 / 有声书的"在读 / 收藏 / 最近活动"。  
  - Telegram 阅读控制台（TG-BOT-BOOK-1/2/3）：支持进度查看、跳转、收藏、最近活动时间线等操作。

> 📌 **阅读 / 听书 / 漫画 / 书架 / 通知 / Telegram / AI 阅读助手** 的完整链路说明详见 `docs/READING_STACK_OVERVIEW.md`。

### 3.5 搜索 / 订阅 / 工作流 / RSSHub

- **全局搜索** – [DONE]  
  - 多站点聚合搜索（PT + 外部索引 + 本地媒体库）。  
  - External Indexer + 站点适配：合并、去重、排序、标记资源来源。  
  - 后续方向：使用本地 TorrentIndex 提升"秒搜"与站点选择智能度（LOCAL-BRAIN-SEARCH 相关）。  
  - 对于**单个用户**而言，只要本机长期开机、让本地 TorrentIndex 逐步完成自己所有 PT 站的全站索引，就可以在"当前用户已登录的站点范围内"实现本机级的**全局秒搜**（无需逐站在线翻页查询）。
- **订阅中心（电影 / 电视剧 / 音乐 / 书籍等）** – [DONE]  
  - "订阅管理"模块按媒体类型拆分为"电影订阅 / 电视剧订阅 / 音乐订阅 / 书籍订阅"四个子页面。  
  - 使用卡片视图展示订阅进度（电视剧显示总集数/已下载集数，电影显示入库状态）。  
  - 新订阅通过搜索结果、规则中心、AI 订阅助手创建，订阅管理模块主要用于查看与管理。  
  - 与搜索、下载、整理、通知联动，形成自动下载闭环。  
  - 后端能力较完整，前端订阅规则中心 / 可视化配置仍有改进空间。
- **工作流系统（下载/整理流程 + 计划中的可视化规则）** – [DONE]  
  - 现状：针对 PT 下载 → 整理 → 入库 → 通知的事件驱动流程已经存在。  
  - 规划：建立统一"订阅/搜索规则中心 + 工作流配置"页面，将 RSSHub 源、搜索规则、过滤器、动作组装成可复用模板。
- **RSSHub 子系统（简化模型）** – [DONE]  
  - 模型：
    - `RSSHubSource`：单源（`url_path`、`type=video/tv/variety/anime/music/mixed`、`group=rank/update` 等）。  
    - `RSSHubComposite`：组合源（多源打包订阅）。  
    - `UserRSSHubSubscription`：用户对源/组合的订阅状态（`target_type`、`enabled`、`last_item_hash`、错误记录等）。  
  - 调度：
    - APScheduler 中预留"RSSHub 订阅处理"定时任务，用 `last_item_hash` 做增量更新。  
  - API：
    - `/api/rsshub/...` 路由已挂载，用于管理源/组合/用户订阅。  
  - 前端 UI / 与工作流中心联动：已完成，支持源管理和状态监控。

### 3.6 插件系统 & Plugin Hub

- **插件系统（后端 + SDK）** – [DONE / WIP]  
  - 提供插件注册、配置、启用/禁用能力。  
  - 插件通过统一 SDK 与核心服务交互，受到安全控制。  
- **Plugin Hub（`strmforge/vabhub-plugins` 仓库）** – [DONE]  
  - 作为官方插件索引仓库，存放插件清单（如 `plugins.json`）。  
  - 主项目中预留远程拉取插件列表、展示/跳转文档的能力。  
  - 前端"插件中心"面板仍有扩展空间（安装指引、状态展示等）。

### 3.7 通知中心 & Telegram Bot

- **通知中心（NOTIFY-CENTER-1）** – [DONE]  
  - 统一的 `notificationApi` + Pinia Store 轮询未读数。  
  - `NotificationDrawer` / `NotificationBell` 重构为使用全局 Store。  
  - 阅读相关事件（漫画更新、有声书 TTS 完成、电子书导入等）有专门卡片组件，可一键跳转。
- **Telegram Bot 控制台** – [DONE / 持续扩展]  
  - 音乐订阅控制台：TG-BOT-MUSIC-1。  
  - 阅读控制台：TG-BOT-BOOK-1/2/3（小说/有声书/漫画）只读 + 写操作。  
  - 阅读时间线（`/reading_recent` 系列命令）统一展示最近活动。  
  - 后续可扩展：站点状态、下载控制、简单搜索等命令。

### 3.8 日志中心（Log Center）

- **日志中心（Log Center）** – [DONE]  
  - 后端 `modules/log_center` + `api/log_center` 提供多源聚合与 WebSocket 实时日志流，支持按 level/source/component 等过滤。  
  - 前端 `LogCenter.vue` 页面可查看实时日志、历史查询与统计，是排障与观察订阅/下载行为的重要工具。  
  - 未来可与订阅 / 下载决策、质量比较等模块更深度联动（例如在异常时自动弹出关联日志）。

### 3.9 系统健康检查 / 外部依赖监控

- **健康检查服务** – [DONE]  
  - 后端 `services/health_checks.py` 提供数据库、Redis、下载器、索引器、磁盘空间等组件的标准健康检查接口。  
  - 与 P0–P6 自检脚本配合，可在 5–15 分钟内完成一轮从"服务可用性 → 外部依赖 → 核心链路"的系统健康体检。  
  - 后续可考虑在 Web UI 中增加"系统健康状态"小组件，对接该服务结果。

### 3.10 未来 AI 总控 / AI Orchestrator

- **AI Orchestrator（只读版 v1）** – [DONE]  
  - 外部 LLM + 本地 AI 器官的只读编排层（FUTURE-AI-ORCHESTRATOR-1）。
  - 后端 `core/ai_orchestrator` 提供 LLM 客户端抽象、工具注册表、Orchestrator 服务。
  - 已封装 6 个只读工具：站点概览、搜索预览、HR 风险洞察、健康检查、日志快照、推荐预览。
  - API：`/api/ai/orchestrator/*` 提供 plan/execute/status 端点。
  - 前端：`AiLab.vue` 提供实验性 AI 助手界面（Beta）。
  - **所有输出仅为建议，不执行任何写操作**。
- **AI 订阅助手 v1** – [DONE]  
  - 自然语言 → 订阅工作流草案 → 预览 & 手动应用（FUTURE-AI-SUBS-WORKFLOW-1）。
  - 后端：`services/ai_subs_workflow.py` + `api/ai_subs_workflow.py`。
  - 前端：`AiSubsAssistant.vue` 提供 AI 订阅向导页面（`/ai-subs-assistant`）。
  - 支持电影/电视剧/动漫订阅草案生成，草案需用户确认后才创建实际订阅。
  - 创建的订阅默认暂停状态，自动下载默认关闭。
- **AI 故障医生 v1** – [DONE]  
  - 基于健康检查和日志的只读诊断助手（FUTURE-AI-LOG-DOCTOR-1）。
  - 后端：`services/ai_log_doctor.py` + `api/ai_log_doctor.py`。
  - 前端：`AiLogDoctor.vue` 提供 AI 诊断页面（`/ai-log-doctor`）。
  - 新增 `GetRunnerStatusTool` 监控定时任务状态。
  - 生成结构化 `SystemDiagnosisReport`，包含诊断项和建议步骤。
- **AI 整理顾问 v1** – [DONE]  
  - 媒体库清理建议助手（FUTURE-AI-CLEANUP-ADVISOR-1）。
  - 后端：`services/ai_cleanup_advisor.py` + `api/ai_cleanup_advisor.py`。
  - 前端：`AiCleanupAdvisor.vue` 提供 AI 清理页面（`/ai-cleanup-advisor`）。
  - 新增 `GetStorageSnapshotTool` 和 `GetLibrarySnapshotTool` 工具。
  - 生成 `CleanupPlanDraft`，含风险级别和保种状态标注，纯只读不执行删除。
- **AI 阅读助手 v1** – [DONE]  
  - 阅读规划建议助手（FUTURE-AI-READING-ASSISTANT-1）。
  - 后端：`services/ai_reading_assistant.py` + `api/ai_reading_assistant.py`。
  - 前端：`AiReadingAssistant.vue` 提供 AI 阅读页面（`/ai-reading-assistant`）。
  - 新增 `GetReadingSnapshotTool` 和 `GetLibraryBooksTool` 工具。
  - 生成 `ReadingPlanDraft`，含阅读目标、建议和洞察，纯只读不修改进度。

> 📌 **AI 中心各页面与 Orchestrator 模式映射、UI 交互规范** 详见 `docs/AI_CENTER_UI_OVERVIEW.md`。

---

## 4. 本地智能大脑（Local Intel / Torrent Index / 安全器官）

> 这一节描述已经落地的本地智能能力，不包含未来可能的自然语言助手。

- **Local Intel 总体**  
  - 模块：`intel_local`，负责本地 PT 行为分析、Torrent 索引、HR/HNR 相关决策。  
  - 与下载器、站点管理、HR/HNR 检测、整理/STRM 流程深度集成。  
  - 已接入统一的 SQLAlchemy 仓储实现，并被搜索服务、下载决策等模块实际使用，后续仍预留优化空间（更智能的站点选择 / 风险评估）。
- **Torrent Indexer（本地全站 / 增量索引引擎）**  
  - `sync_site_full(site_id)`：按页抓取指定 PT 站的种子列表，构建"本地站点目录"（受 SiteGuard 限流保护）。  
  - `sync_site_incremental(site_id, max_pages=N)`：增量扫描最近 N 页，保持索引更新。  
  - 索引字段包括：站点 ID、种子 ID、原始标题、分类、HR/免费标记、大小、种子/下载人数、发布时间、最后出现时间、是否删除等。  
  - 当前用途：
    - 为 HR/HNR / Local Intel 高级判断提供数据。  
    - 为"本地秒搜 / 站点选择智能化"提供基础（IndexedSearchService 已能优先命中本地索引）。
- **SiteGuard / 扫描节流**  
  - `before_pt_scan(site_id)`：在执行全站/增量扫描前检查站点健康、节流计数与封禁风险。  
  - 避免短时间内对某站发起过多请求，降低封号和被视为攻击的风险。
- **HNR / HR 决策引擎**  
  - 结合下载器实际做种统计与站点规则，识别 HNR 风险种子。  
  - 与设定模块中"保留源文件 / 是否允许移动或删种"等关键动作挂钩。  

对于单个用户来说，只要本机保持足够的开机时间，让 TorrentIndex 逐步完成"自己所有 PT 站"的全站索引和增量维护，本地智能大脑就能够在**用户自己可访问的站点范围内**提供接近"全局秒搜"的体验——差别只在于这些索引和识别经验只服务于本机，而不会像云端那样"前人栽树后人乘凉"。

> 云端聚合的"云大脑 v1（共享识别词 + 分布式抓取 + 站点行为模式的跨用户聚合）"当前视为 [LEGACY] 设计，未在现版实现。  
> 现版仅保留 **"本机范围内的全站索引 + 安全决策"**：每个用户只分析和搜索自己可访问的 PT 站，不做任何跨用户目录合并或任务分配。  
> 仓库中保留的 `intel_center` / `mesh_scheduler` 相关代码仅作为历史 PoC 与未来设计素材，当前版本不应直接启用。

---

## 5. 前端结构（简略）

> 此处只给模块级页面，不展开具体组件。  
> 更细粒度的页面/路由清单建议由 `FRONTEND-MAP-1` 任务生成 `docs/FRONTEND_MAP.md`。

- 左侧导航主模块（大致结构）：
  - 电视墙 / 媒体库
  - 下载中心
  - 小说中心 / 有声书中心
  - 漫画中心
  - 音乐中心
  - 站点管理（站点墙）
  - 订阅 / 规则 / 工作流中心（部分已存在，部分待完善）
    - AI 订阅助手（`/ai-subs-assistant`，Beta，自然语言生成订阅草案）
  - 插件中心
  - 日志中心（Log Center）
  - 通知中心
  - AI 实验室（`/ai-lab`，Beta，实验性 AI 助手界面）
  - 设置（下载规则 / HR 策略 / 外部服务配置等）

---

## 6. 已完成的系统健康检查（P0–P6 概要）

> 详细过程与技术细节见：  
> `SYSTEM_HEALTH_P0_OVERVIEW.md` ～ `SYSTEM_HEALTH_P6_FINAL_SUMMARY.md`、`SITE_MANAGER_P0_OVERVIEW.md`。  
> 此处只保留结论级摘要。

- **P0 – 现状巡检与方案设计**  
  - 检查现有站点管理 / Local Intel / 配置系统。  
  - 设计 Site 模型扩展（key/domain/category 等）、SiteStats/SiteAccessConfig 新表结构。  
  - 明确与 SETTINGS-RULES-1、Local Intel、CookieCloud 之间的边界。
- **P1 – 后端代码质量修复**  
  - 修复 15+ mypy 类型错误，解决 async_session_factory 导入问题。  
  - 统一类型注解与 None 校验，`app.chain.init` 导入策略优化。
- **P2 – 前端构建修复**  
  - 修复 10+ Vue 组件与 TS 错误，从构建失败恢复到构建成功。  
  - 重构损坏组件（如 `UserNotifications.vue`），解决所有 TS lint 错误。
- **P3 – Telegram Bot / 通知链路检查**  
  - 确认 11 个命令模块全部可用。  
  - 验证"事件 → 推送"的完整链路，Runner 心跳机制正常。  
  - 确认仅需配置 Token 即可启用。
- **P4 – 配置管理对齐**  
  - `config.py` 和 `.env.example` 从 ~156 行扩展至 ~269 行，填补 100+ 缺失配置项。  
  - 按功能模块整理配置结构，完善说明与示例。
- **P5 – 自检命令清单**  
  - 提供"5 分钟基础健康检查"和"15 分钟深度检查"命令集。  
  - 整理常见问题排查工具、应急恢复与故障处理流程。  
  - 对接 `services/health_checks.py`，统一外部依赖检查入口。
- **P6 – 最终总结**  
  - 系统整体状态：🟢 健康。  
  - 修复问题总数：30+。  
  - 新增多篇技术文档，为后续开发与生产部署提供可靠基础。

---

## 7. 最近里程碑（示例，需持续维护）

> IDE / Agent 每完成一轮大任务后，在此追加 1–2 行。旧记录可移动至 `docs/VABHUB_HISTORY.md`。

- **2025-11-27 – NOTIFY-CENTER-1 完成**：  
  通知中心前端重构，统一 notificationApi + Pinia Store 轮询，通知抽屉和铃铛组件联动，阅读相关通知卡片与跳转完善。
- **2025-11-27 – TG-BOT-BOOK-3 完成**：  
  Telegram 端实现小说/有声书/漫画的交互式控制，通过 ReadingControlService 提供幂等、安全的阅读状态写操作，阅读时间线命令完整。
- **2025-11-28 – Plugin Hub v1 完成**：  
  创建 `strmforge/vabhub-plugins` 仓库作为官方插件索引，主项目初步接入远程插件列表能力。
- **2025-11-29 – SITE-MANAGER-P0 完成**：  
  站点模型扩展设计与 SiteStats/SiteAccessConfig 模型方案完成，为站点管理 v2 打基础。
- **2025-12-02 – MODULES_DEEP_ANALYSIS 完成**：  
  完成 39 个 service.py 文件的 10 阶段深度分析，生成 TRUE_FILE_BY_FILE_DEEP_ANALYSIS.md，为模块理解提供完整技术洞察。
- **2025-12-02 – FUTURE-AI-ORCHESTRATOR-1 完成**：  
  实现只读版 AI 总控层 v1，支持外部 LLM + 本地 AI 器官的安全编排，封装 6 个只读工具，提供 AI 实验室（Beta）页面。
- **2025-12-02 – FUTURE-AI-SUBS-WORKFLOW-1 完成**：  
  实现 AI 订阅助手 v1，支持自然语言生成订阅工作流草案，提供预览与一键应用到订阅中心，草案需用户确认，创建的订阅默认暂停。
- **2025-12-02 – FUTURE-AI-LOG-DOCTOR-1 完成**：  
  实现 AI 故障医生 v1，支持自然语言诊断系统健康、日志分析、Runner 状态监控，生成结构化诊断报告和建议步骤，纯只读不执行任何修复。
- **2025-12-02 – FUTURE-AI-CLEANUP-ADVISOR-1 完成**：  
  实现 AI 整理顾问 v1，支持存储分析、重复媒体识别、保种状态检查，生成清理计划草案含风险级别标注，纯只读不执行任何删除.
- **2025-12-02 – FUTURE-AI-READING-ASSISTANT-1 完成**：  
  实现 AI 阅读助手 v1，支持阅读进度分析、书库统计、阅读目标规划，生成阅读计划草案含优先级建议，纯只读不修改阅读进度.
- **2025-12-02 – NAV-STRUCTURE-CLEANUP-1 完成**：  
  重构前端导航结构，新增“AI 中心”分组统一 5 个 AI 页面入口，优化 8 个导航分组，创建 FRONTEND_MAP.md 路由文档.
- **2025-12-02 – CONFIG-SELF-CHECK-1 完成**：  
  整理配置总览与自检指南，统一 config.py / .env.example 分组与注释，创建 CONFIG_OVERVIEW.md 和 SYSTEM_SELF_CHECK_GUIDE.md。
- **2025-12-02 – DOCS-ONBOARDING-HISTORY-1 完成**：  
  新增 GETTING_STARTED 上手指南和 VABHUB_FEATURE_HISTORY_MAP 历史对照表，对外 README 文案与文档入口统一。
- **2025-12-02 – SUBS-MODULE-UI-1 完成**：  
  重构订阅管理模块为按媒体类型展开的卡片视图（电影/电视剧/音乐/书籍），显示集数进度，并与规则中心和 AI 订阅助手建立轻量联动。
- **2025-12-02 – SUBS-RULES-OVERVIEW-1 完成**：  
  补充 SUBS_RULES_OVERVIEW 文档，梳理订阅管理、规则中心、RSS/RSSHub 与工作流、AI 订阅助手之间的职责与典型使用路径。
- **2025-12-02 – READING-STACK-OVERVIEW-1 完成**：  
  补充 READING_STACK_OVERVIEW 文档，梳理 TXT→EBook→TTS→有声书、漫画追更、书架、通知中心、TG-BOT-BOOK 和 AI 阅读助手之间的完整阅读链路。
- **2025-12-03 – SITE-INTEL-OVERVIEW-1 完成**：  
  补充 SITE_INTEL_OVERVIEW 文档，系统梳理站点管理、Local Intel/TorrentIndex、External Indexer、站点 AI 适配与 HR/HNR 安全策略之间的关系，并明确云大脑 v1 的 LEGACY 边界。
- **2025-12-03 – TVWALL-MUSIC-SPLIT-1 完成**：  
  新增 TV_WALL_PLAYBACK_OVERVIEW 文档，描述电视墙播放策略（LAN/WAN/115）；将短剧工作台从"音乐 & 短剧"拆分至影视中心，音乐独立为"音乐中心"模块组。
- **2025-12-03 – AI-CENTER-OVERVIEW-1 完成**：  
  新增 AI_CENTER_UI_OVERVIEW 文档，描述 AI 中心各页面与 Orchestrator 模式映射；统一 5 个 AI 页面的头部布局、模式标签、只读提示和 LLM 未配置警告。
- **2025-12-03 – DOWNLOAD-MEDIA-PIPELINE-OVERVIEW-1 完成**：  
  新增下载→整理→媒体库全链路概览文档，收拢搜索/订阅/RSSHub/下载/整理/媒体库/AI 整理顾问之间的关系，提供完整流水线视图。
- **2025-12-03 – UI-GLUE-1 完成**：  
  前端导航下各模块与既有后端能力完成首次全面拼接，主要工作包括下载&订阅、阅读栈、站点&插件、系统运维页面的列表和状态展示。
- **2025-12-03 – UI-GLUE-FILL-GAPS-1 完成**：  
  按 UI_GAPS_OVERVIEW.md 标记，完成所有 [WIP]/[TODO] 页面的真实 API 对接，包括发现、日历、RSS/RSSHub、工作流、阅读中心、漫画追更等模块，实现"能点到的页面都有真实数据"。
- **2025-12-03 – UI-LAYOUT-TUNING-1 完成**：  
  对首页、电视墙、下载&订阅、阅读&听书、漫画、音乐、站点&插件、系统设置等关键页面的布局和信息层级进行统一调整，提升可读性和状态可视化。
- **2025-12-03 – UI-FEEDBACK-FIX-1 完成**：  
  基于真实使用反馈对关键页面进行点状 UI 修复，包括海报墙布局、媒体详情页按钮排列、系统健康卡片样式统一、任务汇总信息突出显示、后台服务表格行高优化、最近活动时间线文字显示优化等，提升整体使用顺手度。
- **2025-12-03 – PRE-RELEASE-CHECK-1 完成**：  
  建立统一的预发布自检流程与文档（PRE_RELEASE_CHECK_NOTES / UI_CHECKLIST / SMOKE_SCENARIOS / KNOWN_LIMITATIONS），对后端/前端健康、配置入口、UI 与关键业务链路进行了系统性巡检，为后续 RC 与公开发布打下基础。
- **2025-12-03 – RELEASE-NOTES-RC1-1 完成**：  
  编写 VabHub 0.1.0-rc1 内部 RC 版本说明，统一后端/前端版本号元数据，整理预发布自检文档与已知限制，为后续对外发布与版本演进提供统一的叙事基线。
- **2025-12-03 – DOCKER-INSTALL-GUIDE-1 完成**：  
  新增 Docker 部署指南与示例 docker-compose 配置，统一 README/GETTING_STARTED 的安装路径，明确 Docker/docker-compose 为唯一官方支持的部署方式。
- **2025-12-03 – DOCKER-SMOKE-RUN-1 完成**：  
  在真实 Docker 环境中完成 0.1.0-rc1 的 docker-compose 首跑与核心功能冒烟检查，确认 Docker 部署路径可用，并将经验回写到部署与预发布文档。
- **2025-12-03 – REPO-HYGIENE-1 完成**：  
  完成仓库文档瘦身与 LICENSE 补齐，建立文档分层结构（user/admin/dev/internal），优化 GitHub 访客体验，添加 MIT License。
- **2025-12-03 – REPO-DOCS-PUBLIC-1 完成**：  
  公开仓库文档精简 & Docker Compose 可视化部署说明强化，精简公共仓库文档，仅保留系统总览/AI 总览/前端地图/部署与上手指南/版本历史等核心文档；大量阶段总结/测试报告从仓库移除或转为本地笔记；补充 README / GETTING_STARTED / DEPLOY_WITH_DOCKER 中的 Docker Compose 示例，使 Docker-only 部署路径对新用户更直观。
- **2025-12-03 – REPO-DOCS-ROOT-MD-TRIM-1 完成**：  
  仓库根目录 Markdown 文档彻底清理，将根目录大量历史实施总结/测试报告类 Markdown 文档从公共仓库移除，仅保留 README/CHANGELOG；对保留内容进行汇总沉淀到 LEGACY 实施笔记与 VABHUB_FEATURE_HISTORY_MAP 中，额外文本只保存在本地 local-notes/，显著提升 GitHub 仓库首页可读性。
- **2025-12-04 – REPO-SCRIPTS-ORGANIZE-1 完成**：
  根目录脚本归档 & scripts 目录规范化，将根目录大量 .bat/.ps1/.py 脚本迁移到 scripts/windows、scripts/python、scripts/tools 目录集中管理，根目录不再直接暴露开发/调试脚本；脚本使用被明确标记为“开发者/维护者工具”，普通用户按 Docker-only 路径即可完成部署。
- **2025-12-04 – CI-FRONTEND-PNPM-1 完成**：
  修复 GitHub Actions 前端 pnpm 工具链问题，统一使用 pnpm/action-setup@v4 安装 pnpm，消除 "Unable to locate executable file: pnpm" 报错，优化 CI 缓存策略。
- **2025-12-04 – CI-BACKEND-AIOSQLITE-1 完成**：
  修复后端 CI 中缺失 aiosqlite 导致 API 启动失败的问题，补齐 SQLite AsyncEngine 所需的 aiosqlite 运行依赖，并在 CI requirements 中显式声明。
- **2025-12-04 – CI-BACKEND-PYTEST-2 完成**：
  后端自检脚本与 GitHub CI 测试依赖收敛，确保 CI 环境下必跑 pytest，避免"测试未运行但流水线显示通过"的情况。
  新建 requirements-dev.txt 统一管理测试依赖，修改脚本在 CI 环境下严格检查 pytest 安装。
- **2025-12-04 – CI-BACKEND-PYTEST-3 完成**：
  修复 email-validator 依赖 & app.main 兼容模块 & 测试语法错误，保证后端 pytest 能在 CI 中完整启动。
  解决了 email-validator 缺失、app.main 导入错误、测试文件语法错误等问题。
- **2025-12-04 – CI-BACKEND-UVICORN-PSUTIL-1 完成**：
  补齐 psutil + 搜索扩展依赖，修复后端健康检查启动失败问题。
  解决了 CI 中 uvicorn 启动失败、健康检查无法通过的问题，确保后端服务能正常运行。
- **2025-12-04 – CI-BACKEND-NOTIFY-GET-SESSION-1 完成**：
  为通知相关测试补齐 get_session 历史兼容别名，消除 ImportError，保证 pytest 可以完成收集。
- **2025-12-04 – CI-BACKEND-ASYNCSESSION-FIX-1 完成**：
  修复 app.main 兼容模块导入错误 & FastAPI 中 AsyncSession 依赖声明错误，保证后端 pytest 能顺利完成收集。
- （此处由后续任务持续追加）

---

## 8. 提示给未来的 AI / IDE

> 如果你是新加入的 AI / IDE，请按以下顺序理解并操作本项目：

1. **先完整阅读本文件**，形成对 VabHub 模块和完成度的整体认知。
2. **快速上手**：
   - 上手指南：`docs/GETTING_STARTED.md`（新用户从零到跑通核心流程）
   - 历史对照：`docs/VABHUB_FEATURE_HISTORY_MAP.md`（历史称呼 → 现版模块映射）
3. **配置与自检**：
   - 配置总览：`docs/CONFIG_OVERVIEW.md`（快速了解配置分组和必填项）
   - 自检指南：`docs/SYSTEM_SELF_CHECK_GUIDE.md`（5/15 分钟健康检查命令）
4. 若要动后端：
   - 先看：  
     - `SYSTEM_HEALTH_P0_OVERVIEW.md` ～ `SYSTEM_HEALTH_P6_FINAL_SUMMARY.md`  
     - `SITE_MANAGER_P0_OVERVIEW.md`  
     - 如需模块细节，可按需查 `TRUE_FILE_BY_FILE_DEEP_ANALYSIS.md` 中对应章节（避免整篇通读）。
5. 若要动前端：
   - 查看 `docs/FRONTEND_MAP.md`（已由 NAV-STRUCTURE-CLEANUP-1 创建），  
     理解当前路由 / 页面结构 / 导航分组，再决定改动点。
6. 若要扩展智能功能（Local Intel / RSSHub / 工作流 / 站点 AI 适配）：
   - 必须遵守以下边界：
     - 硅基流动 Qwen 7B 通道仅用于"站点适配"，不可挪作通用聊天或其他功能。  
     - 全站目录抓取（TorrentIndex）只在本机使用：  
       · 仅用于本机智能索引与 HR/HNR / 安全决策；  
       · 不应实现"跨用户合并目录"的云端聚合功能。  
     - 早期云大脑 v1 方案（基于分布式抓取、上传抽象统计信息、构建共享识别词和行为模式）当前处于 [LEGACY] 状态：  
       · 如需探索"共享识别词大脑 v2"，应采用**公开规则包 / 别名词典**等方式，
         避免上传任何可还原具体站点目录或用户抓取行为的敏感数据。

7. 新 AI 在大改前建议先阅读 PRE_RELEASE_CHECK_NOTES 与 KNOWN_LIMITATIONS，了解当前版本的状态和限制。

---

## （模板）PZ. 文档更新要求（必须执行）

> 本节为所有 VabHub 任务书的固定尾部小节模板，请 AI / IDE 在撰写任务书时直接拷贝并按需微调。

1. 更新 `docs/VABHUB_SYSTEM_OVERVIEW.md`：
   - 在 **3. 核心模块地图** 中，调整本次涉及模块的状态标记，并简要补充新能力要点（简短 bullet 即可）。  
   - 在 **7. 最近里程碑** 段落末尾，追加 1 条本次任务的简短描述（不超过 2 行），格式示例：  
     - `- 2025-12-01 – SUBS-RULES-1 完成：实现订阅规则中心 v1，支持 4 类媒体订阅的可视化配置与校验。`  
   - 如最近里程碑超过 ~10 条，请将最早的记录移动到 `docs/VABHUB_HISTORY.md`（如存在）。

2. 如本任务对前端路由 / 页面结构有改动：
   - 请同时更新或生成 `docs/FRONTEND_MAP.md`：  
     - 补充本次新增/修改的页面路径、组件名、所属模块，简要状态说明（已完成/半成品）。

3. 提交前请自查：
   - `VABHUB_SYSTEM_OVERVIEW.md` 中的描述与本次改动保持一致；  
   - 不要保留已废弃功能的宣传描述。
