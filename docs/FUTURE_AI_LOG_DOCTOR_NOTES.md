# FUTURE-AI-LOG-DOCTOR-1 设计笔记

> AI 故障医生 v1：系统健康 & 日志诊断助手（只读）

## 1. 目标

提供一个 AI 驱动的只读诊断助手：

- 用户自然语言描述问题（或点击"最近 24h 系统体检"）
- Orchestrator 调用健康检查、日志快照、站点概览、Runner 状态等工具
- LLM 生成结构化「诊断报告」（SystemDiagnosisReport）
- Web 端专门页面展示诊断结果

**硬性边界**：

- ❌ 不改配置、不执行任何自动修复
- ❌ 不访问敏感字段（密码、Token、Cookie）
- ✅ 所有输出仅为"建议"

---

## 2. 诊断维度梳理

### 2.1 系统组件健康

| 组件 | 数据来源 | 关键字段 |
|------|----------|----------|
| Database | `services/health_checks.check_database()` | status, duration_ms, error |
| Redis | `services/health_checks.check_redis()` | status, duration_ms, error |
| Downloader | `services/health_checks.check_download_client()` | status, qbittorrent/transmission 配置状态 |
| External Indexer | `services/health_checks.check_external_indexer()` | enabled_count |
| Disk Space | `services/health_checks.check_disk_space()` | free_gb, used_percent, status |
| Manga Sources | `services/health_checks.check_manga_sources()` | 各源启用状态 |
| Music Chart | `services/health_checks.check_music_chart_sources()` | 各源启用状态 |

现有工具：`GetHealthStatusTool`（health_status.py）已封装 DB/Redis/Downloader/Disk 检查。

### 2.2 Runner / 定时任务状态

| 数据源 | 位置 | 关键信息 |
|--------|------|----------|
| APScheduler Jobs | `core/scheduler.py` → `get_jobs()` | job_id, name, next_run_time, trigger |
| Task Executions | `modules/scheduler/monitor.py` → `SchedulerMonitor` | status, last_run_time, run_count, success_count, fail_count, error_message |
| Task Statistics | `SchedulerMonitor.get_task_statistics()` | avg_duration, success_rate, recent_executions |

关键 Runners（需要监控）：

- `auto_search_subscriptions` – 订阅搜索（每小时）
- `update_download_status` – 下载状态更新（每30秒）
- `check_rss_subscriptions` – RSS 检查（每30分钟）
- `process_rsshub_subscriptions` – RSSHub 处理（每30分钟）
- `sync_favorite_manga` – 漫画追更（每2小时）
- `auto_checkin_sites` – 站点签到（每天3点）
- `update_hnr_tasks` – HNR 监控（每5分钟）
- `watch_hr_pages` – HR 页面监控（每6小时）
- `watch_inbox_messages` – 站内信监控（每30分钟）

### 2.3 错误日志

| 数据源 | 位置 | 关键信息 |
|--------|------|----------|
| LogCenter | `modules/log_center/service.py` | 内存缓存，支持级别/来源/组件过滤 |
| 统计 | `LogCenter.get_statistics()` | total, by_level, by_source, error_count, warning_count |
| 日志条目 | `LogCenter.get_logs()` | timestamp, level, source, component, message |

现有工具：`GetLogSnapshotTool`（log_snapshot.py）已封装日志快照获取。

日志来源分类（LogSource 枚举）：

- `core` – 核心系统
- `plugin` – 插件
- `downloader` – 下载器
- `media_server` – 媒体服务器
- `scheduler` – 调度器
- `api` – API 层
- `search` – 搜索
- `subscription` – 订阅
- `multimodal` – 多模态

### 2.4 用户感知问题映射

| 用户描述 | 可能原因 | 检查维度 |
|----------|----------|----------|
| "下载失败多" | 下载器连接失败 / 站点访问失败 | Downloader 健康 + 站点状态 + download 相关日志 |
| "站点超时" | 网络问题 / Cookie 过期 / 站点维护 | 站点概览 + site_guard 日志 |
| "TTS 不出声" | TTS Runner 失败 / 外部服务不可用 | scheduler 日志 + TTS 相关任务 |
| "订阅不动" | 订阅任务失败 / 无匹配结果 | subscription Runner 状态 + 订阅日志 |
| "RSSHub 不更新" | RSSHub 服务不可用 / 订阅配置问题 | RSSHub Runner 状态 + rsshub 日志 |

---

## 3. 现有 AI 工具

| 工具名称 | 文件 | 功能 |
|----------|------|------|
| `get_health_status` | `tools/health_status.py` | 健康检查（DB/Redis/Downloader/Disk） |
| `get_log_snapshot` | `tools/log_snapshot.py` | 日志快照（最近24h，支持过滤） |
| `get_site_and_sub_overview` | `tools/site_overview.py` | 站点和订阅概览 |
| `get_search_preview` | `tools/search_preview.py` | 搜索预览 |
| `get_torrent_index_insight` | `tools/torrent_insight.py` | 种子索引洞察 |
| `get_recommendation_preview` | `tools/recommendation_preview.py` | 推荐预览 |

---

## 4. 需要新增/增强的工具

### 4.1 Runner 状态工具（新增）

**文件**：`tools/runner_status.py`

**功能**：

- 获取所有/指定 Runner 的状态
- 返回：名称、上次运行时间、最近执行结果、计划频率

**数据来源**：

- `core/scheduler.py` → `get_scheduler().get_jobs()`
- `modules/scheduler/monitor.py` → `SchedulerMonitor`

### 4.2 日志工具增强（可选）

**现有**：`GetLogSnapshotTool` 已支持 level/source/component 过滤

**增强点**：

- 支持时间窗口参数（1h / 24h / 7d）
- 增加 Top N 错误消息模式（去重）
- 按组件聚合错误计数

---

## 5. 诊断报告数据结构

### 5.1 DiagnosisItem

```python
class DiagnosisItem(BaseModel):
    id: str                           # 唯一标识
    severity: DiagnosisSeverity       # info/warning/error/critical
    title: str                        # 问题标题
    description: str                  # 问题描述
    evidence: list[str] = []          # 证据（日志片段/检查项）
    related_components: list[str] = [] # 相关组件
```

### 5.2 DiagnosisPlanStep

```python
class DiagnosisPlanStep(BaseModel):
    step: int              # 步骤编号
    title: str             # 步骤标题
    detail: str            # 详细说明
    is_safe: bool = True   # 是否为安全操作（只读检查）
```

### 5.3 SystemDiagnosisReport

```python
class SystemDiagnosisReport(BaseModel):
    overall_status: DiagnosisSeverity  # 总体状态
    summary: str                        # 一句话总结
    items: list[DiagnosisItem]         # 诊断项列表
    suggested_steps: list[DiagnosisPlanStep]  # 建议步骤
    raw_refs: dict[str, Any] = {}      # 原始数据引用（调试用）
```

---

## 6. Orchestrator DIAGNOSE 模式

### 6.1 允许工具集

- `get_health_status` – 系统健康
- `get_log_snapshot` – 日志快照
- `get_site_and_sub_overview` – 站点状态
- `get_runner_status` – Runner 状态（新增）

### 6.2 System Prompt 要点

```
你是 VabHub 系统的 AI 故障医生。你的任务是分析系统健康状况并生成诊断报告。

你会收到：
1. 系统组件健康检查结果
2. Runner/定时任务执行状态
3. 最近的错误和警告日志
4. 站点连通性状态

你需要生成一个 SystemDiagnosisReport JSON：
- overall_status: 总体健康评分（info/warning/error/critical）
- summary: 一句话总结当前状态
- items: 诊断项列表，每项包含：
  - severity: 严重程度
  - title: 问题标题
  - description: 问题描述
  - evidence: 支持该诊断的证据（日志片段/检查项摘要）
  - related_components: 相关组件标识
- suggested_steps: 建议的操作步骤，每步包含：
  - step: 编号
  - title: 步骤标题
  - detail: 详细操作说明
  - is_safe: 是否为只读/安全操作

重要约束：
- 你只是在提供建议，不会自动执行任何修复操作
- 建议步骤应该是人类可以执行的具体操作
- 对于需要修改配置或重启服务的步骤，明确标注 is_safe=false
```

---

## 7. 实现进度

| 阶段 | 内容 | 状态 |
|------|------|------|
| P0 | 现状巡检 & 诊断维度梳理 | ✅ 完成 |
| P1 | Doctor 专用工具（Runner 状态等） | ✅ 完成 |
| P2 | 诊断报告 Schema & Orchestrator 增强 | ✅ 完成 |
| P3 | LogDoctor 服务 & API | ✅ 完成 |
| P4 | 前端 AI 故障医生页面 | ✅ 完成 |
| P5 | 测试 & UX 打磨 | ✅ 完成 |
| P6 | 文档 & 总结 | ✅ 完成 |

---

## 8. 示例诊断报告

### 8.1 正常系统示例

```json
{
  "overall_status": "info",
  "summary": "系统运行正常，所有组件健康，定时任务执行稳定。",
  "items": [
    {
      "id": "health_ok",
      "severity": "info",
      "title": "系统健康检查通过",
      "description": "数据库、Redis、下载器、磁盘空间均正常。",
      "evidence": ["database: ok (5ms)", "redis: ok (2ms)", "disk: 68% free"],
      "related_components": ["database", "redis", "disk"]
    }
  ],
  "suggested_steps": [
    {
      "step": 1,
      "title": "保持当前配置",
      "detail": "系统运行良好，建议定期检查确保持续稳定。",
      "is_safe": true
    }
  ],
  "generated_at": "2025-12-02T03:00:00"
}
```

### 8.2 有问题的系统示例

```json
{
  "overall_status": "error",
  "summary": "发现 2 个问题需要关注：下载器连接失败、RSSHub 任务执行异常。",
  "items": [
    {
      "id": "downloader_error",
      "severity": "error",
      "title": "下载器连接失败",
      "description": "无法连接到 qBittorrent，可能是服务未启动或网络问题。",
      "evidence": ["error: Connection refused", "last success: 2h ago"],
      "related_components": ["downloader", "qbittorrent"]
    },
    {
      "id": "rsshub_runner_fail",
      "severity": "warning",
      "title": "RSSHub 处理任务连续失败",
      "description": "最近 3 次执行均失败，可能是 RSSHub 服务不可用。",
      "evidence": ["process_rsshub_subscriptions: 3 failures", "error: timeout"],
      "related_components": ["runner", "rsshub"]
    }
  ],
  "suggested_steps": [
    {
      "step": 1,
      "title": "检查下载器服务",
      "detail": "确认 qBittorrent 是否正在运行，检查端口 8080 是否可访问。",
      "is_safe": true
    },
    {
      "step": 2,
      "title": "检查 RSSHub 服务",
      "detail": "确认 RSSHub 服务端是否正常响应，尝试直接访问 RSSHub 地址。",
      "is_safe": true
    },
    {
      "step": 3,
      "title": "重启相关服务",
      "detail": "如果上述检查正常，尝试重启 VabHub 后端服务。",
      "is_safe": false
    }
  ],
  "generated_at": "2025-12-02T03:00:00"
}
```

---

## 9. 后续规划

- **v2**: 支持更多组件健康检查（Telegram Bot、RSSHub 服务端、媒体服务器）
- **v2**: 历史诊断报告存档与对比
- **v3**: 基于历史数据的趋势分析
