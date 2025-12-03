# FUTURE-AI-CLEANUP-ADVISOR-1 设计笔记

> AI 整理顾问 v1：库存清理建议助手（只读）

## 1. 目标

提供一个 AI 驱动的只读整理顾问：

- 基于 Local Intel (HR/保种)、媒体库统计、使用历史、质量对比
- 生成 `CleanupPlanDraft`（清理计划草案）
- Web 端专门页面展示建议，用户手动决定是否执行

**硬性边界**：

- ❌ 绝不自动删除或移动
- ❌ 不建议删除仍有 HR/保种价值的内容（至少显著标注风险）
- ✅ 所有输出仅为"建议草案"

---

## 2. 数据维度梳理

### 2.1 存储空间

| 数据源 | 位置 | 关键信息 |
|--------|------|----------|
| StorageMonitor | `modules/storage_monitor/service.py` | 目录使用率、剩余空间、预警状态 |
| 使用趋势 | `StorageMonitorService.get_usage_trends()` | 最近 N 天的空间变化趋势 |
| 目录统计 | `StorageMonitorService.get_statistics()` | 总空间/已用/剩余 |

### 2.2 HR/保种任务

| 数据源 | 位置 | 关键信息 |
|--------|------|----------|
| HNRTask | `models/hnr.py` | 监控中的保种任务、风险评分、做种时间 |
| HNRDetection | `models/hnr.py` | HR 检测记录、判定结果 |
| TorrentIndex | `models/intel_local.py` | 本地种子索引、is_hr 标记 |

关键判断：
- `status="monitoring"` 且 `seed_time_hours < required_seed_time_hours` → 仍需保种
- `risk_score > 0.5` → 高风险，不建议删除

### 2.3 媒体库统计

| 数据源 | 位置 | 关键信息 |
|--------|------|----------|
| Media | `models/media.py` | 媒体标题、类型、年份 |
| MediaFile | `models/media.py` | 文件路径、大小、质量（4K/1080p/720p） |
| DownloadTask | `models/download.py` | 下载任务、状态、大小 |

### 2.4 使用历史（待扩展）

| 场景 | 可用数据 | 备注 |
|------|----------|------|
| 播放记录 | 媒体服务器 API（Emby/Jellyfin/Plex） | 需要集成 |
| 访问时间 | MediaFile.created_at（近似） | 现有 |
| 最后访问 | 文件系统 atime（不可靠） | 可选 |

### 2.5 质量对比

| 场景 | 判断逻辑 |
|------|----------|
| 重复媒体 | 同一 tmdb_id/imdb_id 有多个 MediaFile |
| 质量升级 | 存在 1080p 和 4K 版本，可建议保留高质量 |
| 低质量淘汰 | 同媒体有 720p 和 1080p，建议淘汰 720p |

---

## 3. 现有 AI 工具

| 工具名称 | 文件 | 可用于清理顾问 |
|----------|------|----------------|
| `get_torrent_index_insight` | `tools/torrent_insight.py` | ✅ HR 风险统计 |
| `get_site_and_sub_overview` | `tools/site_overview.py` | ✅ 站点订阅概览 |
| `get_health_status` | `tools/health_status.py` | ✅ 磁盘空间检查 |
| `get_recommendation_preview` | `tools/recommendation_preview.py` | 部分可用 |

---

## 4. 需要新增的工具

### 4.1 存储快照工具（新增）

**文件**：`tools/storage_snapshot.py`

**功能**：
- 获取存储目录使用情况
- 返回各目录的空间占用、预警状态
- 计算可释放空间估算

**数据来源**：
- `modules/storage_monitor/service.py` → `StorageMonitorService`

### 4.2 媒体库快照工具（新增）

**文件**：`tools/library_snapshot.py`

**功能**：
- 获取媒体库统计（按类型、质量分组）
- 识别重复媒体
- 标记可能的低质量淘汰候选

**数据来源**：
- `models/media.py` → `Media`, `MediaFile`
- `models/download.py` → `DownloadTask`

---

## 5. 清理计划数据结构

### 5.1 CleanupAction

```python
class CleanupAction(BaseModel):
    id: str                         # 唯一标识
    action_type: CleanupActionType  # delete / archive / transcode / replace
    target_type: str                # media_file / download_task / torrent
    target_id: str                  # 目标 ID
    target_title: str               # 目标标题（显示用）
    target_path: Optional[str]      # 文件路径
    size_gb: float                  # 可释放空间 (GB)
    reason: str                     # 建议原因
    risk_level: RiskLevel           # safe / caution / risky
    risk_notes: list[str] = []      # 风险提示
    hr_status: Optional[str] = None # 保种状态：active / completed / none
```

### 5.2 CleanupPlanDraft

```python
class CleanupPlanDraft(BaseModel):
    summary: str                       # 总体说明
    total_savable_gb: float           # 预计可释放空间
    actions: list[CleanupAction]      # 建议操作列表
    storage_context: dict             # 存储背景信息
    warnings: list[str] = []          # 全局警告
    generated_at: str                 # 生成时间
```

### 5.3 RiskLevel 枚举

```python
class RiskLevel(str, Enum):
    SAFE = "safe"       # 安全删除（已完成保种、重复低质量版本）
    CAUTION = "caution" # 需谨慎（可能仍有价值）
    RISKY = "risky"     # 高风险（仍在保种中）
```

### 5.4 CleanupActionType 枚举

```python
class CleanupActionType(str, Enum):
    DELETE = "delete"       # 删除
    ARCHIVE = "archive"     # 归档（移动到冷存储）
    TRANSCODE = "transcode" # 转码压缩
    REPLACE = "replace"     # 质量替换（删除低质量保留高质量）
```

---

## 6. Orchestrator CLEANUP_ADVISOR 模式

### 6.1 允许工具集

- `get_torrent_index_insight` – HR 风险统计
- `get_storage_snapshot` – 存储快照（新增）
- `get_library_snapshot` – 媒体库快照（新增）
- `get_site_and_sub_overview` – 站点概览

### 6.2 System Prompt 要点

```
你是 VabHub 的 AI 整理顾问。

你的任务是分析用户的存储使用情况、媒体库内容和保种任务，生成清理计划草案。

你会收到：
1. 存储空间使用情况和趋势
2. 媒体库统计（按类型、质量分组）
3. HR/保种任务状态
4. 重复媒体和低质量候选

你需要生成一个 CleanupPlanDraft JSON：
- summary: 总体说明
- total_savable_gb: 预计可释放空间
- actions: 建议操作列表，每个操作包含：
  - action_type: delete / archive / transcode / replace
  - target_title: 目标标题
  - size_gb: 可释放空间
  - reason: 建议原因
  - risk_level: safe / caution / risky
  - risk_notes: 风险提示（特别是 HR 相关）
  - hr_status: 保种状态（active 表示仍在保种）

重要约束：
- 你只是在生成"草案"，不会自动执行任何删除或移动操作
- 对于仍在保种中的内容（hr_status=active），必须标注 risk_level=risky
- 建议按 risk_level 排序，safe 在前，risky 在后
- 不要建议删除唯一版本的媒体（除非用户明确要求清理）
```

---

## 7. 实现进度

| 阶段 | 内容 | 状态 |
|------|------|------|
| P0 | 现状巡检 & 数据维度梳理 | ✅ 完成 |
| P1 | 工具层增强（存储/媒体库快照） | ✅ 完成 |
| P2 | 清理草案 Schema & Orchestrator 增强 | ✅ 完成 |
| P3 | CleanupAdvisor 服务 & API | ✅ 完成 |
| P4 | 前端 AI 整理顾问页面 | ✅ 完成 |
| P5 | 测试 & UX 打磨 | ✅ 完成 |
| P6 | 文档 & 总结 | ✅ 完成 |

---

## 8. 后续规划

- **v2**: 接入媒体服务器播放记录，基于实际使用频率建议
- **v2**: 支持执行预览（Dry Run 模式）
- **v3**: 智能归档策略（冷热数据分层）
