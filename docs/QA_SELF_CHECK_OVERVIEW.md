# VabHub 自检系统

## 概述

VabHub 自检系统是一个功能级检查工具，用于验证各核心功能链路是否正常工作。

### OPS 健康检查 vs QA 自检

| 维度 | OPS 健康检查 (OPS-1/2) | QA 自检 (QA-1) |
|------|------------------------|----------------|
| **关注点** | 基础设施层 | 业务功能层 |
| **检查内容** | 数据库连接、磁盘空间、外部服务 | API 可用性、Runner 心跳、功能链路 |
| **运行方式** | 定时自动运行，结果入库 | 按需手动触发 |
| **告警** | 触发 OPS 告警渠道 | 仅报告，不发通知 |
| **用途** | 持续监控 | 升级验收、问题诊断 |

## 自检覆盖范围

### 1. 核心检查 (core)

| 检查项 | 说明 |
|--------|------|
| `db.migrations` | Alembic 迁移版本表是否存在 |
| `db.simple_query` | 数据库查询是否正常 |
| `redis.ping` | Redis 连接（如已启用） |
| `download_client.config` | 下载器配置 |
| `disk.data_writable` | 数据盘可写性 |

### 2. 小说 / TTS / 有声书 (novel_tts)

| 检查项 | 说明 |
|--------|------|
| `api.novel_center.stats` | 小说中心统计查询 |
| `api.tts.storage_overview` | TTS 存储概览 |
| `runner.tts_config` | TTS Provider 配置 |
| `reading_hub.aggregation` | 阅读中心聚合 |

### 3. 漫画 (manga)

| 检查项 | 说明 |
|--------|------|
| `api.manga.local_series` | 本地漫画系列 |
| `api.manga.following` | 追更列表 |
| `runner.manga_follow_heartbeat` | 漫画追更 Runner 心跳 |

### 4. 音乐 (music)

| 检查项 | 说明 |
|--------|------|
| `api.music.library` | 音乐库 |
| `api.music.charts` | 音乐榜单源 |
| `runner.music_subscription_heartbeat` | 音乐订阅 Runner 心跳 |

### 5. 通知 (notify)

| 检查项 | 说明 |
|--------|------|
| `notify.write_user_notification` | 用户通知写入能力 |
| `notify.user_channel_exists` | 用户通知渠道配置 |
| `notify.ops_alert_channels` | OPS 告警渠道配置 |

### 6. Bot / Telegram (bot)

| 检查项 | 说明 |
|--------|------|
| `bot.telegram.config` | Telegram Bot 配置 |
| `bot.telegram.whoami` | Telegram API 连通性（可选） |

### 7. Runner 状态 (runners)

| 检查项 | 说明 |
|--------|------|
| `runner.manga_follow_sync` | 漫画追更同步 Runner |
| `runner.manga_remote_sync` | 漫画远程同步 Runner |
| `runner.music_subscription_sync` | 音乐订阅同步 Runner |
| `runner.ops_health_check` | OPS 健康检查 Runner |

## 使用方法

### CLI 方式

```bash
cd backend

# 运行自检（表格输出）
python -m app.runners.qa_self_check

# JSON 格式输出
python -m app.runners.qa_self_check --json

# WARN 时也返回非零退出码
python -m app.runners.qa_self_check --fail-on-warn

# 安静模式（仅输出结果）
python -m app.runners.qa_self_check --quiet
```

**退出码：**
- `0`：所有检查通过或仅有 WARN
- `1`：存在 FAIL
- `2`：存在 WARN（仅在 `--fail-on-warn` 时）

### Web 方式

1. 登录管理员账号
2. 访问 `/admin/self-check`
3. 点击「立即自检」按钮
4. 查看各组检查结果

### API 方式

```bash
# 触发自检
curl -X POST http://localhost:8000/api/admin/self_check/run \
  -H "Authorization: Bearer <TOKEN>"
```

## 结果解读

| 状态 | 含义 | 建议 |
|------|------|------|
| **PASS** | 检查通过 | 无需操作 |
| **WARN** | 需要关注 | 建议检查配置或部署 Runner |
| **FAIL** | 关键异常 | 应立即修复 |
| **SKIPPED** | 已跳过 | 功能未启用或未配置 |

### 常见 WARN 场景

- **Runner 未运行过**：Runner 尚未部署或从未执行
- **无启用的渠道**：用户/告警通知渠道未配置
- **TTS Provider 未配置**：TTS 功能未启用

### 常见 FAIL 场景

- **数据库查询失败**：数据库连接问题
- **磁盘不可写**：权限或空间问题
- **API 查询异常**：表结构或数据问题

## 配置选项

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `QA_SKIP_TELEGRAM_CHECKS` | 跳过 Telegram API 调用检查 | `false` |

## 推荐使用场景

1. **升级前后**：升级 VabHub 版本后，运行自检确认功能正常
2. **问题诊断**：用户报告功能异常时，快速定位问题范围
3. **部署验证**：新环境部署后，验证配置正确性
4. **定期巡检**：定期（如每周）运行自检，提前发现潜在问题

## 注意事项

- 自检**只读不写**：不会创建真实数据、不会发送真实通知
- 自检**不发通知**：避免骚扰用户，只在触发时运行
- 自检**不阻塞**：即使存在 FAIL，也不会阻止系统运行

## 相关文档

- [OPS 监控概述](./OPS_MONITORING_OVERVIEW.md)
- [告警渠道配置](./OPS_ALERT_CHANNELS.md)
- [系统健康检查](./OPS_HEALTH_CHECKS.md)
