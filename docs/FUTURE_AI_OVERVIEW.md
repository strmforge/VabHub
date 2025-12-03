<!--
FUTURE_AI_OVERVIEW.md v1

用途（单一事实来源 / 给未来 AI & IDE 看的）：
- 描述 VabHub "未来 AI 总控"当前真实实现状态（v1），以及允许的发展方向。
- 让新窗口里的 ChatGPT / Windsurf / SWE-1.5 等，在写 AI 相关任务书之前，先搞清楚：
  - 外部大模型 Endpoint 怎么接入；
  - 本地 AI 器官有哪些（Local Intel / External Indexer / 推荐 / 站点 AI 适配等）；
  - AI Orchestrator 已经支持哪些模式 & 工具；
  - 哪些功能是 [DONE] / [WIP] / [PLANNED] / [LEGACY]。

维护约定：
1. 本文件只描述"AI / 智能相关"的高层结构，不写长代码，也不要展开底层实现细节。
2. 每完成一轮 AI 相关大任务（例如 FUTURE-AI-ORCHESTRATOR-1、FUTURE-AI-SUBS-WORKFLOW-1 等），
   必须更新本文件：
   - 标记对应模块状态（[DONE]/[WIP]/[PLANNED]/[LEGACY]）；
   - 在相关小节补充 1–3 行特点摘要；
   - 如有必要补充新的"模式 / 工具 / 场景"条目。
3. 控制总长度在 ~4000–7000 字符内，历史版本可以移到 `docs/FUTURE_AI_HISTORY.md`。
4. 不要改动本文件的小节编号，方便其他工具（任务书 / 自动分析）跳转引用。
-->

# FUTURE AI 概览 v1.0

> 关键词：**外部大模型 Endpoint + 本地 AI 器官 + Orchestrator 编排层**  
> 目标：在不强制要求本机 GPU 的前提下，让 VabHub 获得"能看懂自己状态、能帮用户配工作流、能给出清理/阅读建议"的智能层。

---

## 0. 使用说明（给 AI / IDE）

1. 在为 VabHub 编写任何 **AI / 智能相关任务书** 之前，请先完整阅读本文件，再结合：
   - `docs/VABHUB_SYSTEM_OVERVIEW.md`（总体系统图）
   - `docs/AI_CENTER_UI_OVERVIEW.md`（AI 中心页面与模式映射，UI 视角说明）
   - 各 AI 子模块的 Notes：
     - `docs/FUTURE_AI_ORCHESTRATOR_NOTES.md` 
     - `docs/FUTURE_AI_SUBS_WORKFLOW_NOTES.md` 
     - `docs/FUTURE_AI_LOG_DOCTOR_NOTES.md` 
     - `docs/FUTURE_AI_CLEANUP_ADVISOR_NOTES.md` 
     - `docs/FUTURE_AI_READING_ASSISTANT_NOTES.md` 

2. 如任务涉及前端新页面或路由，请同时更新或生成：
   - `docs/FRONTEND_MAP.md`（若存在），标明 AI 相关页面和导航入口。

3. 所有"未来 AI"任务书，都必须包含一个 `PZ. 文档更新要求（必须执行）` 小节：
   - 要求执行任务的 IDE / Agent 在任务结束后，同步更新：
     - 本文件 `FUTURE_AI_OVERVIEW.md` 
     - `docs/VABHUB_SYSTEM_OVERVIEW.md` 
     - 对应的 `FUTURE_AI_***_NOTES.md` 
     - 以及 `docs/FRONTEND_MAP.md`（如涉及页面结构）

---

## 1. 总体愿景 & 范围

### 1.1 愿景

- 将 VabHub 打造成"**有自己本地大脑 + 会调用外部大模型的媒体自动化中枢**"，而不是单纯的规则堆叠器。
- 对标（并超出）传统媒体平台接入外部 LLM 之后的能力：
  - 不只是"聊天推荐"，而是能读懂：
    - 站点 / 订阅 / 下载 / HR / 媒体库 / 阅读进度 / 日志健康等 **全局状态**，
  - 然后通过 **AI Orchestrator** 生成：
    - 订阅工作流草案、
    - 故障诊断报告、
    - 清理/洗版建议计划、
    - 阅读/听书/漫画的优先级与计划。

### 1.2 范围（v1 实际落地）

- 不强制要求本机 GPU；大模型推理默认走**外部 Endpoint**。
- 本地已有深度学习推荐模块（NCF / DeepFM / AutoEncoder）视为可选工具，主要用于个性化推荐预览，不做强依赖。
- 站点 AI 适配通道（CF Pages + Qwen2.5-Coder-7B-Instruct）**只用于站点结构解析**，不挪作它用。
- 不实现云端"PT 全站目录聚合大脑"，只保留本地 TorrentIndex / Local Intel。

---

## 2. 架构总览：外部 LLM + 本地 AI 器官

### 2.1 AI Orchestrator（中枢） – [DONE]

- 模块路径：
  - `backend/app/core/ai_orchestrator/llm_client.py` 
  - `backend/app/core/ai_orchestrator/factory.py` 
  - `backend/app/core/ai_orchestrator/service.py` 
  - `backend/app/core/ai_orchestrator/tools/*` 
- 职责：
  - 将外部 LLM 视为"**决策中枢**"，本地模块视为"**工具**"；
  - 提供可配置的多种运行模式（mode），每种模式拥有一组可调用工具；
  - 生成结构化结果（JSON），由后端服务层进一步校验和应用；
  - 遵守严格的安全边界：大部分模式只读；有写操作时必须走专门的 Service（例如订阅草案应用）。

### 2.2 本地 AI 器官 – [DONE / WIP]

这些模块不是"大模型"，而是 Orchestrator 可调用的**本地智能器官**：

- **Local Intel / TorrentIndex**：
  - 模块：`intel_local` / `TorrentIndex` / HR / HNR 分析；
  - 用途：
    - 评估种子 HR/HNR 风险；
    - 支持本地"全站目录索引"和后续"秒搜 / 清理 / 策略"。
- **External Indexer**：
  - 多站点聚合搜索；  
  - 提供搜索预览 / 资源去重 / 来源标记工具。
- **站点 AI 适配（Site AI Adapter）** – [DONE, 专线]
  - 通过 CF Pages + Qwen2.5-Coder-7B-Instruct，仅用于：
    - 解析 PT 站点列表页 / 详情页 / HR 页结构；
    - 生成站点解析规则（供 External Indexer / Local Intel 使用）。
  - **禁止复用该通道做通用聊天或其他任何需求。**
  - 站点侧完整说明详见 `docs/SITE_INTEL_OVERVIEW.md`。
- **深度学习推荐模块** – [DONE, 可选]
  - NCF / DeepFM / AutoEncoder 等推荐器；
  - 提供"推荐预览"工具给 Orchestrator（GetRecommendationPreviewTool）；
  - 是否使用 GPU 由用户配置决定，不影响其它 AI 功能。

### 2.3 云侧"共享大脑" – [LEGACY]

- 早期设想：
  - 在云端聚合用户上传的 PT 站点目录抽象特征，构建"共享识别词 + 行为模式"大脑；
  - 用于加速搜索 / 做种策略 / HR 风险建模。
- 当前状态：
  - 出于成本与合规考虑，**不再实现**任何跨用户目录聚合；
  - 现版只做：
    - 本地 TorrentIndex；
    - 每个用户只分析自己能访问的站点，不上传可还原目录的数据。
- 未来如要做"共享识别词 v2"，只能通过：
  - 公开规则包 / 别名词典 / Git 仓库等形式共享**规则/词典**，而不是聚合原始抓取数据。

> 历史背景与相关构想的演进，可参考 `docs/VABHUB_FEATURE_HISTORY_MAP.md` §2/§3。

---

## 3. LLM 客户端与配置层 – [DONE]

### 3.1 LLM 客户端抽象

- 文件：`backend/app/core/ai_orchestrator/llm_client.py` 
- 实现：
  - `HttpLLMClient`：通用 HTTP API 调用客户端；
  - `DummyLLMClient`：测试 / Demo 模式，返回内置结果，用于无外网或本地开发；
- 工厂：`backend/app/core/ai_orchestrator/factory.py`  
  根据配置返回对应客户端实例。

### 3.2 配置项

在 `backend/app/core/config.py` / `.env.example` 中提供一组 AI Orchestrator 相关配置：

- `AI_ORCH_ENABLED`：是否启用 Orchestrator；
- `AI_ORCH_LLM_ENDPOINT`：外部 LLM HTTP Endpoint；
- `AI_ORCH_LLM_API_KEY`：API Key；
- `AI_ORCH_LLM_MODEL`：默认模型名；
- `AI_ORCH_LLM_TIMEOUT`：请求超时时间；
- `AI_ORCH_LLM_MAX_TOKENS`：最大 token 数；
- `AI_ORCH_DEBUG_LOG`：调试日志开关。

> **详见** `docs/CONFIG_OVERVIEW.md` §3.1（AI Orchestrator 配置）和 `docs/SYSTEM_SELF_CHECK_GUIDE.md` §3（AI 专项检查）。

### 3.3 GPU / 本地模型的定位

- v1 不强制要求本机 GPU；LLM 推理默认走外部 Endpoint。
- 本地 GPU（如有）主要用于：
  - 深度学习推荐模块；
  - 未来可能接入的本地小模型（需单独任务书定义）。
- 任务书中如需使用 GPU，必须明确写出：
  - 该功能在 **无 GPU** 环境下的降级策略（通常为"禁用该子功能，不影响其它 AI 能力"）。

---

## 4. Orchestrator 模式一览（v1 已实现）

所有模式由 `AIOrchestratorService` 管理，通过 `mode` 参数区分行为。

### 4.1 GENERIC – 通用模式 – [DONE]

- 用途：
  - 面向 `/ai-lab` 页面的通用实验模式；
  - 允许用户指定 prompt，由 Orchestrator 调用部分只读工具，从而"问问系统现在是什么状态"。
- 工具集：
  - 典型：站点/订阅概览、搜索预览、推荐预览等；
  - 具体可用工具见 `/api/ai/orchestrator/tools`。

### 4.2 SUBS_ADVISOR – 订阅工作流顾问 – [DONE]

- 相关文件：
  - `backend/app/schemas/ai_subs_workflow.py` 
  - `backend/app/services/ai_subs_workflow.py` 
  - `backend/app/api/ai_subs_workflow.py` 
  - 前端：`frontend/src/pages/AiSubsAssistant.vue` 
- 目标：
  - 将一句自然语言需求（例如"帮我配一套韩剧热门订阅工作流"）转化为一组 **订阅工作流草案**：
    - `SubsWorkflowDraft` 列表；
    - 每个草案包含媒体类型、来源（RSSHub / PT 搜索）、过滤规则、动作配置以及 AI 说明。
- 安全策略：
  - Orchestrator 仅生成草案 JSON；
  - 由 `AISubsWorkflowService.apply()` 在**用户确认后**创建真实订阅：
    - 默认 `status=paused`、`auto_download=false`、`hr_safe=true`；
  - 严禁 Orchestrator 直接对数据库做写操作。
- 与订阅体系的关系：
  - AI 订阅助手生成/应用的订阅，最终在"订阅管理模块"（`/subscriptions/*`）中查看；
  - 整体订阅 / 规则 / RSSHub / 工作流协作关系详见 `docs/SUBS_RULES_OVERVIEW.md`。

### 4.3 DIAGNOSE – 系统故障医生 – [DONE]

- 相关文件：
  - `backend/app/schemas/ai_log_doctor.py` 
  - `backend/app/core/ai_orchestrator/tools/runner_status.py` 
  - `backend/app/services/ai_log_doctor.py` 
  - `backend/app/api/ai_log_doctor.py` 
  - 前端：`frontend/src/pages/AiLogDoctor.vue` 
- 目标：
  - 聚合健康检查、Runner 状态、站点连通性、日志快照等信息；
  - 输出结构化的 `SystemDiagnosisReport`：
    - 总体状态（INFO / WARNING / ERROR / CRITICAL）
    - 诊断项列表（问题描述 + 证据）
    - 建议步骤（安全/手动操作为主）。
- 特点：
  - 只读诊断，不自动修复；
  - 适合用于"最近系统不太对劲"时的一键体检。

### 4.4 CLEANUP_ADVISOR – 整库清理顾问 – [DONE]

- 相关文件：
  - `backend/app/schemas/ai_cleanup_advisor.py` 
  - `backend/app/core/ai_orchestrator/tools/storage_snapshot.py` 
  - `backend/app/core/ai_orchestrator/tools/library_snapshot.py` 
  - `backend/app/services/ai_cleanup_advisor.py` 
  - `backend/app/api/ai_cleanup_advisor.py` 
  - 前端：`frontend/src/pages/AiCleanupAdvisor.vue` 
- 目标：
  - 结合存储快照、媒体库统计、重复媒体检测、做种/HR 状态等；
  - 生成 `CleanupPlanDraft`：
    - 分组列出：删除候选 / STRM 化 / 降级存储 / 洗版 / 保留 & 标注；
    - 对有 HR / 保种风险的条目进行显著提示。
- 特点：
  - v1 **仅输出计划**，不执行任何删除/移动；
  - 计划用于人工审阅，可以跳转到媒体详情进行手动操作；
  - 所有潜在"风险操作"必须在 reason / warnings 中用人话说明。

### 4.5 READING_ASSISTANT – 阅读助手 – [DONE]

- 相关文件：
  - `backend/app/schemas/ai_reading_assistant.py` 
  - `backend/app/core/ai_orchestrator/tools/reading_snapshot.py` 
  - `backend/app/core/ai_orchestrator/tools/library_books.py` 
  - `backend/app/services/ai_reading_assistant.py` 
  - `backend/app/api/ai_reading_assistant.py` 
  - 前端：`frontend/src/pages/AiReadingAssistant.vue` 
- 目标：
  - 基于 Shelf Hub 与阅读/听书/漫画进度：
    - 总结 "正在阅读 / 已完成 / 待读" 状态；
    - 为未来 N 天（或周/月）生成简单阅读计划：
      - continue / start / finish 三类建议；
      - high / medium / low 优先级。
- 特点：
  - 只读，不修改任何阅读进度或收藏状态；
  - 输出 `ReadingInsights` + `ReadingPlan`，用于用户决策与规划；
  - 未来可扩展至 Telegram Bot 端（单独任务书）。
- 与阅读栈的关系：
  - AI 阅读助手只读分析"阅读栈"（小说/有声书/漫画/书架）的数据；
  - 阅读栈整体说明详见 `docs/READING_STACK_OVERVIEW.md`。

---

## 5. 已落地的 AI 场景（v1）

### 5.1 Web 端 AI 中心页面

- `/ai-lab` – AI 实验室：
  - 面向高级用户 & 开发者的通用入口；
  - 可选择不同 Orchestrator mode、查看可用工具、调试 AI 工作流。
- `/ai-subs-assistant` – AI 订阅助手：
  - 从自然语言生成订阅工作流草案；
  - 支持预览、筛选、应用至订阅中心。
- `/ai-log-doctor` – AI 故障医生：
  - 一键系统体检、生成诊断报告与建议步骤。
- `/ai-cleanup-advisor` – AI 整理顾问：
  - 查看各媒体类型的清理/洗版建议计划；
  - 不做自动清理，只作为库管助手。
- `/ai-reading-assistant` – AI 阅读助手：
  - 聚合小说 / 有声书 / 漫画的阅读状态；
  - 提供未来 N 天阅读/听书规划建议。

### 5.2 与其它模块的联动

- 与 **订阅中心 / RSSHub / External Indexer**：
  - 通过 SUBS_ADVISOR + AISubsWorkflowService；
- 与 **Local Intel / TorrentIndex / HR 安全策略**：
  - 通过 TorrentIndexInsight 工具 + CleanupAdvisor；
- 与 **系统健康 / 通知中心 / Runner**：
  - 通过 HealthStatus / RunnerStatus / LogSnapshot 工具 + LogDoctor；
- 与 **Shelf Hub / 阅读 & 追更中心**：
  - 通过 ReadingSnapshot 工具 + ReadingAssistantService。

---

## 6. 安全边界 & 合规约束

> 本节是"AI 任务书必须遵守"的硬约束。

1. **站点 AI 适配通道专用**：
   - CF Pages + Qwen2.5-Coder-7B-Instruct 仅用于站点结构解析；
   - 不得复用为通用聊天/推荐/代码生成等用途；
   - Orchestrator 使用的 LLM Endpoint 必须是独立配置，不可误用站点适配通道。

2. **不做云端 PT 目录聚合**：
   - 不实现"云端全站索引聚合大脑"；
   - 不上传可还原用户 PT 站点目录的数据；
   - 如需共享"识别经验"，必须通过公开规则包 / 别名词典等方式实现。

3. **读写分层**：
   - Orchestrator + 工具层默认只读；
   - 涉及写操作必须：
     - 通过专门的 Service（如 AISubsWorkflowService.apply()）；
     - 在任务书中明确说明写入内容与回滚策略；
     - 在 UI 上提供清晰的用户确认流程。

4. **危险操作须双保险**：
   - 删除 / 移动 / 洗版 等操作在 v1 的 AI 任务中一律视为高危；
   - 当前版本仅允许 AI 提出"计划草案"和"建议"，不允许自动执行；
   - 后续若要开放半自动执行，必须：
     - 单独的 Phase 任务书；
     - 严格的 Dry Run / Preview / Undo 设计。

5. **配置 / 身份 / 凭据保护**：
   - AI 工具在访问 config / secrets / tokens 时，必须：
     - 做脱敏处理（日志 & Orchestrator 输入中）；
     - 不输出完整敏感信息到 LLM 提示文本中。

---

## 7. v2+ 潜在方向（PLANNED / 设想）

> 以下内容为规划或草图，**默认未实现**，写任务书前需再次确认。

- **AI 驱动的半自动修复**：
  - 在 LogDoctor 基础上，增加"生成修复操作草案"；
  - 由用户在 Web/TG 上逐条确认是否执行。
- **AI 驱动的订阅/清理组合策略**：
  - 将 SubsAdvisor + CleanupAdvisor 联动：
    - 例如："边清理旧剧边订阅新剧" 的一键工作流建议。
- **Telegram 端 AI 助手**：
  - 在现有 TG-BOT-BOOK/MUSIC/SHELF 之上：
    - 加 `/ai_diag`、`/ai_cleanup`、`/ai_reading` 等命令；
    - 使用相同服务层，只是换 UI 通道。
- **本地小模型 / On-device LLM（取决于 GPU）**：
  - 如果用户有 GPU 且愿意部署本地模型：
    - 提供可选的本地 LLM Client；
    - 对部分模式（例如 READING_ASSISTANT）进行"离线增强"。

---

## 8. 写未来 AI 任务书的约定（给 AI / IDE）

当你准备编写新的 AI 相关任务书时，请至少包含以下约束与动作：

1. **模式与工具声明**：
   - 明确：
     - 是否新增 Orchestrator mode；
     - 是否只在现有 mode 内增加工具 / 能力；
   - 新工具必须注册到：
     - `backend/app/core/ai_orchestrator/tools/registry.py`。

2. **安全边界说明**：
   - 写清：
     - 本任务是否只读；
     - 如有写操作，具体影响的模型 / 表 / 配置；
     - UI 层的用户确认流程（弹窗/预览/回滚）。

3. **文档更新要求（必须执行）**：
   - 在任务书末尾附上 `PZ. 文档更新要求` 小节，至少要求：
     - 更新本文件 `FUTURE_AI_OVERVIEW.md`；
     - 更新 `docs/VABHUB_SYSTEM_OVERVIEW.md`；
     - 更新对应 Notes（例如 `FUTURE_AI_XYZ_NOTES.md`）；
     - 如有前端路由变动，更新 `docs/FRONTEND_MAP.md`。

4. **无 GPU 环境兼容**：
   - 若本任务使用深度学习推荐或本地小模型：
     - 必须说明在无 GPU 环境下的降级行为（禁用 / 降级 / 切换外部 Endpoint）；
     - 不得因为缺 GPU 影响其它 Orchestrator 模式的正常使用。

> 简单说：**所有新 AI 能力，都要挂在这套"外部 LLM + 本地 AI 器官 + Orchestrator"框架下，  
> 不能绕过它偷偷搞一套"平行宇宙 AI 服务"。**
