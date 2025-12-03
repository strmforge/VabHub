# FUTURE-AI-ORCHESTRATOR-1 设计笔记

> 本文件记录 AI 总控层 v1 的设计决策、边界约束和实现笔记。

---

## 1. 现有模块能力概览

### 1.1 Local Intel / TorrentIndex
- **位置**: `backend/app/core/intel_local/`
- **核心文件**:
  - `indexer.py` (12KB) - 本地全站/增量索引引擎
  - `hr_policy.py` / `hr_state.py` / `hr_watcher.py` - HR/HNR 风险检测
  - `site_guard.py` - 扫描节流与封禁风险控制
  - `engine.py` - 本地智能引擎
- **能力**:
  - 本地 PT 站点种子索引（全站/增量）
  - HR/HNR 风险评估与状态追踪
  - 站点健康检查与节流控制
- **状态**: [DONE]

### 1.2 External Indexer / AI 站点适配
- **位置**: `backend/app/core/ext_indexer/`
- **核心文件**:
  - `ai_bridge.py` - AI 适配桥接
  - `search_provider.py` (8.6KB) - 搜索提供者
  - `registry.py` - 索引器注册表
  - `runtime.py` - 运行时
- **能力**:
  - 站点页面结构解析（通过 CF Pages + Qwen）
  - 多站点聚合搜索
  - 索引器管理
- **状态**: [DONE/WIP]

### 1.3 推荐系统
- **位置**: `backend/app/modules/recommendation/`
- **核心文件**:
  - `service.py` (17KB) - 推荐服务
  - `algorithms.py` (26KB) - 推荐算法
  - `deep_learning_recommender.py` (10KB) - 深度学习推荐
  - `realtime_service.py` (14KB) - 实时推荐
- **能力**:
  - 协同过滤推荐
  - 内容相似度推荐
  - 深度学习推荐（可选）
  - 实时推荐更新
- **状态**: [WIP]

### 1.4 LogCenter 日志中心
- **位置**: `backend/app/modules/log_center/`
- **核心文件**:
  - `service.py` (12KB) - 日志服务
- **能力**:
  - 多源日志聚合
  - 按 level/source/component 过滤
  - WebSocket 实时日志流
  - 历史查询与统计
- **状态**: [DONE]

### 1.5 健康检查服务
- **位置**: `backend/app/services/health_checks.py`
- **能力**:
  - 数据库连接检查
  - Redis 连接检查
  - 下载器连接检查
  - 索引器状态检查
  - 磁盘空间检查
- **状态**: [DONE]

### 1.6 RSSHub 子系统
- **位置**: `backend/app/modules/rsshub/`
- **核心文件**:
  - `service.py` (12KB) - RSSHub 服务
  - `scheduler.py` (17KB) - 调度器
  - `workflow_templates.py` (9KB) - 工作流模板
- **能力**:
  - RSS 源管理（单源/组合源）
  - 用户订阅管理
  - 增量更新调度
  - 工作流模板
- **状态**: [DONE/WIP]

### 1.7 订阅中心
- **位置**: `backend/app/modules/subscription/`
- **能力**:
  - 媒体订阅规则管理
  - 质量偏好配置
  - 与搜索/下载联动
- **状态**: [DONE/WIP]

### 1.8 站点管理
- **位置**: `backend/app/modules/site_manager/` + `backend/app/modules/site/`
- **能力**:
  - 站点配置管理
  - 站点状态统计
  - Cookie/UA/Proxy 配置
- **状态**: [DONE]

---

## 2. 硬性边界 & 非目标

### 2.1 硬性限制

#### ❌ 不得复用站点 AI 适配通道
- 现有 CF Pages + 硅基流动 Qwen2.5-Coder-7B 通道**仅用于站点结构解析**
- AI Orchestrator 必须使用独立的 LLM Endpoint 配置
- 两个通道完全隔离，不共享 API Key 或配额

#### ❌ 不直接访问敏感数据
- 不访问 PT 页面原始 HTML
- 不访问用户文件系统路径（仅抽象后的媒体库信息）
- 不访问下载器认证信息（Cookie/Token/密码）
- Orchestrator 只能通过已有服务层获取**抽象过的数据**

#### ❌ P0–P6 期间不实现写操作
- 不创建/修改订阅规则
- 不触发下载任务
- 不删除文件或种子
- 不修改系统配置
- 所有建议以「草稿 JSON + 文本说明」形式返回，由用户手动确认执行

### 2.2 非目标

#### 不做本地大模型部署
- 不集成 Ollama / vLLM / llama.cpp 等本地推理框架
- v1 仅支持外部 HTTP LLM Endpoint
- 本地 LLM 留待未来插件任务

#### 不做云大脑 v1 式跨用户聚合
- 不实现分布式抓取任务分配
- 不上传用户站点目录到云端
- 不构建跨用户的识别词/行为模式聚合
- Local Intel 数据仅服务于本机

#### 不做重生成任务
- 不做「1688 商品 AI 视频」
- 不做「小说转动画」
- 不做「AI 配音」等内容生成
- 这些留给未来插件系统

---

## 3. 初步架构设计

### 3.1 架构图（文字版）

```text
┌─────────────────────────────────────────────────────────────────┐
│                        用户 / 前端 AI Lab                        │
└─────────────────────────────────▲───────────────────────────────┘
                                  │
                    POST /api/ai/orchestrator/execute
                                  │
┌─────────────────────────────────▼───────────────────────────────┐
│                     FastAPI Router Layer                         │
│                  (backend/app/api/ai_orchestrator.py)            │
└─────────────────────────────────▲───────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────┐
│                   AIOrchestratorService                          │
│              (backend/app/core/ai_orchestrator/service.py)       │
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │ Mode Router │───▶│ Tool Filter │───▶│ Execution Engine    │  │
│  │ (4 modes)   │    │ (allowlist) │    │ (max 3 tool calls)  │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  LLMClient    │  │ ToolRegistry  │  │ Orchestrator  │
│  (Abstract)   │  │ (Read-only    │  │ Context       │
│               │  │  Tools)       │  │ (DI inject)   │
│ ┌───────────┐ │  │               │  │               │
│ │HttpLLM    │ │  │ - SiteOverview│  │ - DB Session  │
│ │Client     │ │  │ - SearchPreview│ │ - User Info   │
│ └───────────┘ │  │ - TorrentInsight│ │ - Config     │
│ ┌───────────┐ │  │ - HealthStatus │  │ - Services   │
│ │DummyLLM   │ │  │ - LogSnapshot │  │               │
│ │Client     │ │  │ - RecommendPreview│              │
│ └───────────┘ │  │               │  │               │
└───────────────┘  └───────┬───────┘  └───────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
│ Local Intel     │ │ LogCenter   │ │ Recommendation  │
│ TorrentIndex    │ │ Service     │ │ Service         │
│ HR Policy       │ │             │ │                 │
└─────────────────┘ └─────────────┘ └─────────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
│ External Indexer│ │ Health      │ │ RSSHub          │
│ Search Provider │ │ Checks      │ │ Service         │
└─────────────────┘ └─────────────┘ └─────────────────┘
```

### 3.2 组件说明

#### LLMClient 抽象
- **职责**: 封装与外部 LLM 的通信
- **实现**:
  - `HttpLLMClient`: 通过 HTTP 调用配置的 LLM Endpoint
  - `DummyLLMClient`: 测试/演示用，返回预定义的 tool_calls
- **接口**:
  ```python
  class LLMClient(Protocol):
      async def chat(
          self,
          messages: list[ChatMessage],
          tools: list[LLMToolSpec] | None = None,
      ) -> LLMResponse: ...
  ```

#### AIOrchestratorService
- **职责**: 编排 LLM 与本地工具的交互
- **模式**: 4 种预定义模式，决定可用工具集
  - `SUBS_ADVISOR`: 订阅工作流顾问
  - `DIAGNOSE`: 系统故障诊断
  - `CLEANUP_ADVISOR`: 整理/清理建议
  - `GENERIC`: 通用安全模式
- **流程**:
  1. 根据 mode 筛选允许的工具
  2. 构造 system prompt
  3. 调用 LLM 获取 tool_calls
  4. 执行工具（最多 3 次）
  5. 再次调用 LLM 生成总结

#### ToolRegistry
- **职责**: 管理所有可用的 AI 工具
- **v1 工具集** (全部只读):
  - `GetSiteAndSubOverviewTool`: 站点 + 订阅速览
  - `GetSearchPreviewTool`: 搜索预览（不触发下载）
  - `GetTorrentIndexInsightTool`: HR 风险洞察
  - `GetHealthStatusTool`: 健康检查状态
  - `GetLogSnapshotTool`: 日志快照
  - `GetRecommendationPreviewTool`: 推荐预览

#### OrchestratorContext
- **职责**: 通过 FastAPI DI 注入依赖
- **内容**:
  - 数据库会话
  - 当前用户信息
  - 配置对象
  - 各服务入口

### 3.3 数据流

```text
用户 Prompt
    │
    ▼
[Mode Selection] ─────▶ 确定可用工具集
    │
    ▼
[LLM Call #1] ─────────▶ 返回 tool_calls
    │
    ▼
[Tool Execution] ──────▶ 执行工具，收集结果
    │                   （最多 3 个工具）
    ▼
[LLM Call #2] ─────────▶ 生成总结 + 建议配置
    │
    ▼
OrchestratorResult
  - plan: 执行计划
  - tool_results: 工具输出
  - llm_summary: 文本总结
  - llm_suggested_changes: 建议配置（草案）
```

---

## 4. 安全设计

### 4.1 工具层安全
- 所有工具仅实现只读操作
- 工具输出自动脱敏：
  - 移除文件系统路径
  - 移除 Cookie/Token
  - 掩码 PT 站点 URL

### 4.2 执行层安全
- 单次会话最多 3 次工具调用
- 非法工具调用自动丢弃
- 工具执行错误不抛异常，记录到结果中

### 4.3 输出层安全
- `llm_suggested_changes` 仅为草案
- 后端不执行任何写操作
- 前端明确标注「仅为建议，未实际应用」

---

## 5. 配置项设计

```python
# AI Orchestrator 配置
AI_ORCH_ENABLED: bool = False              # 总控开关
AI_ORCH_LLM_PROVIDER: str = "http"         # LLM 提供者类型
AI_ORCH_LLM_ENDPOINT: str | None = None    # LLM API 端点
AI_ORCH_LLM_API_KEY: str | None = None     # LLM API Key
AI_ORCH_LLM_MODEL: str | None = None       # 模型名称
AI_ORCH_LLM_TIMEOUT: int = 30              # 请求超时（秒）
AI_ORCH_LLM_MAX_TOKENS: int = 2048         # 最大 token 数
AI_ORCH_DEBUG_LOG: bool = False            # 调试日志开关
```

---

## 6. 实现进度

| 阶段 | 内容 | 状态 |
|------|------|------|
| P0 | 现状巡检 & 设计对齐 | ✅ 完成 |
| P1 | 配置 & LLM 客户端抽象 | ✅ 完成 |
| P2 | 工具抽象 & 封装 | ✅ 完成 |
| P3 | Orchestrator 内核 | ✅ 完成 |
| P4 | HTTP API & 后端集成 | ✅ 完成 |
| P5 | 前端 AI Lab 页面 | ✅ 完成 |
| P6 | 测试、文档 & 安全复盘 | ✅ 完成 |

---

## 7. 安全复盘（P6-2）

### 7.1 现状确认
- v1 仅实现只读工具和只读建议
- 未调用站点 AI 适配的 Qwen 通道（硅基流动通道完全隔离）
- 使用独立的 LLM Endpoint 配置

### 7.2 安全确认
- ✅ 写操作路径全部未接入 Orchestrator
- ✅ 工具集未包含任何"写配置/写数据库/操作下载"的接口
- ✅ 日志中不会泄露敏感信息（路径 / Cookie / Token 已脱敏）
- ✅ 所有输出明确标注为"建议"，前端有明显提示

### 7.3 已实现的安全措施
- 单次会话最多 3 次工具调用
- 非法工具调用自动丢弃
- 工具输出自动脱敏（移除路径、Cookie、Token）
- `llm_suggested_changes` 仅为草案，后端不执行

---

## 8. 后续规划（非本任务范围）

- **写操作闭环**: 由后续任务实现「确认执行」能力
- **本地 LLM**: 通过插件支持 Ollama 等本地推理
- **更多工具**: 根据需求扩展工具集
- **多轮对话**: 支持上下文连续对话
