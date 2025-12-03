# 运行监控 & 故障自检

> OPS-1 + OPS-2 实现文档

## 概览

VabHub 的 Ops 能力包括：
- **健康检查**: 核心依赖（数据库/下载器/PT搜索/漫画源/音乐源）状态监控
- **Runner 状态**: 后台任务（同步/下载/TTS）执行状态上报
- **自检 Runner**: 定时运行健康检查并记录结果
- **Web 控制台**: 首页和管理控制台的运维面板
- **通知联动**: 严重故障时发送告警通知
- **告警渠道**: 支持 Telegram/Webhook/Bark 多渠道告警（OPS-2A）
- **体检报告**: 一键生成 JSON/Markdown 格式健康报告（OPS-2B）
- **Runner SLA**: 成功/失败统计、成功率可视化（OPS-2C）
- **多盘监控**: 支持多路径磁盘监控和自定义阈值（OPS-2D）

## 健康检查项列表

| Key | 类型 | 说明 |
|-----|------|------|
| `db.default` | db | 数据库连接检查 |
| `service.redis` | service | Redis 缓存连接检查 |
| `service.download_client` | service | 下载器（qBittorrent/Transmission）检查 |
| `external.indexer` | external | 外部 PT 索引器检查 |
| `manga_source.*` | external | 漫画源检查（按 source_id） |
| `music_chart_source.*` | external | 音乐榜单源检查（按 source_id） |
| `disk.data` | disk | 数据目录磁盘空间检查 |

### 状态说明

| 状态 | 含义 |
|------|------|
| `ok` | 正常 |
| `warning` | 警告（如磁盘空间较低、未配置等） |
| `error` | 错误（连接失败、服务不可用等） |
| `unknown` | 未知（尚未检查） |

## Runner 状态说明

| Runner 名称 | 说明 | 建议间隔 |
|-------------|------|----------|
| `manga_follow_sync` | 漫画追更同步 | 5 分钟 |
| `manga_remote_sync` | 远程漫画章节同步 | 5 分钟 |
| `music_chart_sync` | 音乐榜单同步 | 60 分钟 |
| `music_subscription_sync` | 音乐订阅同步 | 30 分钟 |
| `ops_health_check` | 系统健康检查 | 5 分钟 |
| `demo_seed` | Demo 数据初始化 | 手动 |

### Runner 状态字段

- `last_started_at`: 上次开始时间
- `last_finished_at`: 上次结束时间
- `last_exit_code`: 上次退出码（0=成功）
- `last_duration_ms`: 上次运行时长（毫秒）
- `last_error`: 上次错误信息
- `recommended_interval_min`: 建议运行间隔（分钟）

## 自检 Runner 使用方式

### 单次执行

```bash
python -m app.runners.ops_health_check
```

### 循环模式

```bash
# 每 5 分钟执行一次
python -m app.runners.ops_health_check --loop --interval 300
```

### Docker 部署

在 `docker-compose.yml` 中添加：

```yaml
health-check:
  image: vabhub/backend:latest
  command: python -m app.runners.ops_health_check --loop --interval 300
  depends_on:
    - backend
```

### systemd 定时任务

```ini
# /etc/systemd/system/vabhub-health-check.service
[Unit]
Description=VabHub Health Check
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/opt/vabhub/backend
ExecStart=/opt/vabhub/venv/bin/python -m app.runners.ops_health_check
User=vabhub

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/vabhub-health-check.timer
[Unit]
Description=VabHub Health Check Timer

[Timer]
OnCalendar=*:0/5
Persistent=true

[Install]
WantedBy=timers.target
```

## Web 控制台查看方式

### 首页（HomeDashboard）

首页显示系统健康卡片：
- 整体状态（正常/警告/错误）
- 各状态数量统计
- 最近检查时间
- 点击"查看详情"跳转到管理控制台

### 管理控制台（AdminDashboard）

管理控制台的"系统健康"区域提供：
- 完整的健康检查列表
- 每项检查的详细状态、错误信息、元数据
- Runner 状态表格
- "立刻执行健康检查"按钮

## API 端点

| 端点 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/api/admin/health/summary` | GET | 获取健康汇总 | Admin |
| `/api/admin/health/run_once` | POST | 手动执行健康检查 | Admin |

### 响应示例

```json
{
  "overall_status": "ok",
  "total_checks": 5,
  "ok_count": 4,
  "warning_count": 1,
  "error_count": 0,
  "unknown_count": 0,
  "checks": [
    {
      "key": "db.default",
      "check_type": "db",
      "status": "ok",
      "last_checked_at": "2024-01-01T12:00:00Z",
      "last_duration_ms": 5
    }
  ],
  "runners": [
    {
      "name": "manga_follow_sync",
      "runner_type": "scheduled",
      "last_started_at": "2024-01-01T11:55:00Z",
      "last_finished_at": "2024-01-01T11:55:30Z",
      "last_exit_code": 0,
      "last_duration_ms": 30000,
      "recommended_interval_min": 5
    }
  ],
  "last_check_time": "2024-01-01T12:00:00Z"
}
```

## 通知联动

### 通知类型

- `SYSTEM_HEALTH_ERROR`: 健康检查发现错误
- `SYSTEM_HEALTH_WARNING`: 健康检查发现警告

### 降频机制

- 只在状态**恶化**时发送通知（正常→警告、正常→错误、警告→错误）
- 状态恢复时不发送通知
- 相同状态不重复发送

## 故障定位建议

### db.default 连接失败

1. 检查数据库服务是否运行
2. 检查 `DATABASE_URL` 配置
3. 检查网络连接

### service.download_client 连接失败

1. 检查下载器服务是否运行
2. 检查 `QB_URL` 或 `TR_URL` 配置
3. 检查认证信息

### external.indexer 无可用索引器

1. 在管理控制台添加外部索引器
2. 检查索引器配置是否正确
3. 确保至少有一个索引器处于启用状态

### disk.data 磁盘空间不足

1. 清理不需要的文件
2. 扩展存储空间
3. 调整媒体库路径到更大的磁盘

## OPS-2 新增功能

### 告警渠道（OPS-2A）

支持将告警推送到外部渠道：

- **Telegram**: 通过 Bot 发送到群组或私聊
- **Webhook**: 发送 HTTP 请求到自定义 URL
- **Bark**: 发送 iOS 推送通知

详细配置参见 [告警渠道配置指南](./OPS_ALERT_CHANNELS.md)。

### 体检报告（OPS-2B）

一键生成系统健康报告：

```bash
# JSON 格式
curl -H "Authorization: Bearer $TOKEN" /api/admin/health/report?format=json

# Markdown 格式
curl -H "Authorization: Bearer $TOKEN" /api/admin/health/report?format=markdown
```

### Runner SLA（OPS-2C）

Runner 状态扩展字段：

- `success_count`: 成功次数
- `failure_count`: 失败次数
- `total_runs`: 总运行次数
- `success_rate`: 成功率（%）

API 端点：`GET /api/admin/health/runners`

### 多盘监控（OPS-2D）

支持监控多个磁盘路径，每个路径可配置独立阈值：

```bash
# 获取配置
curl /api/admin/health/disk-config

# 更新配置
curl -X PUT /api/admin/health/disk-config -d '{
  "paths": [
    {"name": "data", "path": "/mnt/data", "warn_percent": 20, "error_percent": 10},
    {"name": "media", "path": "/mnt/media", "warn_percent": 15, "error_percent": 5}
  ]
}'

# 执行检查
curl -X POST /api/admin/health/disk-check
```

## 相关文件

### 后端

- `backend/app/models/system_health.py` - 数据模型
- `backend/app/models/alert_channel.py` - 告警渠道模型（OPS-2A）
- `backend/app/schemas/system_health.py` - Pydantic Schema
- `backend/app/schemas/alert_channel.py` - 告警渠道 Schema（OPS-2A）
- `backend/app/schemas/disk_monitor.py` - 磁盘监控 Schema（OPS-2D）
- `backend/app/services/system_health_service.py` - 健康检查服务
- `backend/app/services/health_checks.py` - 具体检查函数
- `backend/app/services/runner_heartbeat.py` - Runner 心跳
- `backend/app/services/system_health_notify.py` - 通知服务
- `backend/app/services/alert_channel_service.py` - 告警渠道服务（OPS-2A）
- `backend/app/services/system_health_report_service.py` - 体检报告服务（OPS-2B）
- `backend/app/modules/alert_channels/` - 告警渠道适配器（OPS-2A）
- `backend/app/api/system_health.py` - API 端点
- `backend/app/api/alert_channels.py` - 告警渠道 API（OPS-2A）
- `backend/app/runners/ops_health_check.py` - 自检 Runner

### 前端

- `frontend/src/types/systemHealth.ts` - 类型定义
- `frontend/src/types/alertChannel.ts` - 告警渠道类型（OPS-2A）
- `frontend/src/components/admin/SystemHealthCard.vue` - 健康卡片组件
- `frontend/src/pages/admin/AlertChannelAdmin.vue` - 告警渠道管理页（OPS-2A）
