# 统一收件箱健康检查文档

## 概述

本文档说明统一收件箱（INBOX）在智能健康检查系统（`/api/smart/health`）中的集成情况。

## 健康检查字段

在 `/api/smart/health` 的返回体中，`features.inbox` 字段包含以下信息：

```json
{
  "ok": true,
  "features": {
    "inbox": {
      "enabled": true,
      "inbox_root": "/path/to/INBOX_ROOT",
      "enabled_media_types": ["video", "ebook", "audiobook", "novel_txt", "comic", "music"],
      "last_run_at": "2025-11-22T10:30:00",
      "last_run_status": "success",
      "last_run_summary": "处理完成：成功 10，跳过 2，失败 0",
      "pending_warning": null
    }
  }
}
```

### 字段说明

#### `enabled` (boolean)
- **含义**：是否至少有一个媒体类型启用了 INBOX
- **计算逻辑**：当任何一个 `INBOX_ENABLE_*` 为 `True` 时，`enabled = True`；全为 `False` 时，`enabled = False`

#### `inbox_root` (string)
- **含义**：当前 INBOX 根目录路径
- **来源**：直接来自 `settings.INBOX_ROOT`

#### `enabled_media_types` (array)
- **含义**：已启用的媒体类型列表
- **可能的值**：`["video", "ebook", "audiobook", "novel_txt", "comic", "music"]`
- **计算逻辑**：遍历所有相关的 `INBOX_ENABLE_*` 配置，如果为 `True` 则加入列表

#### `last_run_at` (string | null)
- **含义**：最近一次 `run-once` 的结束时间（ISO 格式）
- **来源**：从 `InboxRunLog` 表中查询最近一条记录的 `finished_at` 字段
- **如果不存在记录**：返回 `null`

#### `last_run_status` (string)
- **含义**：最近一次运行的状态
- **可能的值**：
  - `"never"`：从未运行过
  - `"success"`：全部成功
  - `"partial"`：部分成功（有成功也有失败）
  - `"failed"`：全部失败
  - `"empty"`：扫描结果为空
- **来源**：从 `InboxRunLog` 表中查询最近一条记录的 `status` 字段

#### `last_run_summary` (string | null)
- **含义**：最近一次运行的总结信息
- **示例**：`"处理完成：成功 10，跳过 2，失败 0"`
- **来源**：从 `InboxRunLog` 表中查询最近一条记录的 `message` 字段
- **如果不存在记录**：返回 `null`

#### `pending_warning` (string | null)
- **含义**：待处理的警告信息
- **可能的值**：
  - `null`：无警告
  - `"never_run"`：启用但从未运行过
  - `"too_long_without_run"`：超过 24 小时未运行
  - `"last_run_failed"`：最近一次运行失败
- **计算逻辑**：
  1. 如果 `enabled = False`，返回 `null`
  2. 如果不存在运行记录，返回 `"never_run"`
  3. 如果最近一次状态是 `"failed"`，返回 `"last_run_failed"`
  4. 如果距离最近一次运行超过 24 小时，返回 `"too_long_without_run"`
  5. 否则返回 `null`

## 运行日志模型（InboxRunLog）

每次执行 `/api/dev/inbox/run-once` 时，系统会自动记录一条运行日志。

### 模型字段

- `id`：主键
- `started_at`：开始时间
- `finished_at`：结束时间
- `status`：状态（`success` / `partial` / `failed` / `empty`）
- `total_items`：本次扫描到的文件数
- `handled_items`：成功处理/导入的数
- `skipped_items`：跳过的数（如某 media_type disabled）
- `failed_items`：失败的数
- `message`：总结性信息
- `details`：结构化信息（JSON，包含按 media_type 的统计）
- `created_at`：记录创建时间

### Status 计算逻辑

1. `total_items == 0` → `status = "empty"`
2. `failed_items == 0` → `status = "success"`
3. `failed_items > 0` 且 `handled_items > 0` → `status = "partial"`
4. `failed_items > 0` 且 `handled_items == 0` → `status = "failed"`

## 如何判断统一收件箱是否正常工作

### 正常状态

1. **`enabled = true`**：至少有一个媒体类型启用
2. **`last_run_status = "success"` 或 `"partial"`**：最近一次运行成功或部分成功
3. **`pending_warning = null`**：无警告
4. **`last_run_at` 在最近 24 小时内**：定期运行

### 示例（正常）

```json
{
  "enabled": true,
  "inbox_root": "/data/inbox",
  "enabled_media_types": ["video", "ebook"],
  "last_run_at": "2025-11-22T10:30:00",
  "last_run_status": "success",
  "last_run_summary": "处理完成：成功 10，跳过 2，失败 0",
  "pending_warning": null
}
```

### 异常状态

1. **`pending_warning = "never_run"`**：启用但从未运行过
   - **建议**：执行一次 `/api/dev/inbox/run-once`

2. **`pending_warning = "too_long_without_run"`**：超过 24 小时未运行
   - **建议**：检查定时任务是否正常，或手动执行一次 `run-once`

3. **`pending_warning = "last_run_failed"`**：最近一次运行失败
   - **建议**：查看日志文件，检查失败原因，修复后重新运行

4. **`last_run_status = "failed"`**：最近一次运行全部失败
   - **建议**：检查 INBOX_ROOT 目录权限、Importer 配置、数据库连接等

### 示例（异常）

```json
{
  "enabled": true,
  "inbox_root": "/data/inbox",
  "enabled_media_types": ["video"],
  "last_run_at": "2025-11-21T10:30:00",
  "last_run_status": "failed",
  "last_run_summary": "处理完成：成功 0，跳过 0，失败 5",
  "pending_warning": "last_run_failed"
}
```

## 运维策略建议

### 1. 定时任务

建议通过定时任务（如 cron）定期执行 `run-once`：

```bash
# 每天凌晨 2 点执行一次
0 2 * * * curl -X POST http://localhost:8000/api/dev/inbox/run-once
```

或者使用系统调度器（如 APScheduler）在应用内定时执行。

### 2. 监控告警

建议监控以下指标：

- **`pending_warning`**：如果存在警告，发送告警通知
- **`last_run_status`**：如果为 `"failed"`，发送告警通知
- **`last_run_at`**：如果超过 24 小时未更新，发送告警通知

### 3. 日志查看

运行日志存储在 `inbox_run_logs` 表中，可以通过以下方式查看：

```sql
-- 查看最近 10 条运行记录
SELECT * FROM inbox_run_logs ORDER BY created_at DESC LIMIT 10;

-- 查看失败记录
SELECT * FROM inbox_run_logs WHERE status = 'failed' ORDER BY created_at DESC;
```

### 4. 健康检查集成

可以将 `/api/smart/health` 集成到监控系统（如 Prometheus、Grafana）中：

```bash
# 示例：使用 curl 检查健康状态
curl http://localhost:8000/api/smart/health | jq '.features.inbox'
```

## 测试覆盖

### 测试文件

1. **`tests/test_inbox_run_log_model.py`**：测试 InboxRunLog 模型
   - 基本创建
   - 默认值
   - status 字段
   - 计数字段
   - details 字段

2. **`tests/test_inbox_run_once_logging.py`**：测试 run-once 日志记录
   - 成功时记录日志
   - 部分成功时记录日志
   - 全部失败时记录日志
   - 空结果时记录日志
   - 按 media_type 统计
   - 异常时记录日志

3. **`tests/test_smart_health_inbox.py`**：测试健康检查 inbox 区块
   - 所有类型禁用
   - 启用但从未运行
   - 最近成功运行
   - 最近失败运行
   - 超过 24 小时未运行
   - 所有媒体类型启用
   - inbox_root 路径

### 运行测试

```bash
cd VabHub/backend
pytest tests/test_inbox_run_log_model.py -v
pytest tests/test_inbox_run_once_logging.py -v
pytest tests/test_smart_health_inbox.py -v
```

## 总结

统一收件箱健康检查功能提供了：

1. ✅ **运行状态可见性**：通过 `/api/smart/health` 一目了然地查看 INBOX 状态
2. ✅ **自动日志记录**：每次 `run-once` 自动记录执行结果
3. ✅ **智能警告**：自动检测异常情况（未运行、失败、长期未运行）
4. ✅ **运维友好**：提供清晰的字段和状态，便于监控和告警

通过集成到智能健康检查系统，运维人员可以在一个接口中快速了解统一收件箱的运行状态，及时发现和解决问题。

