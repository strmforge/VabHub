# 告警渠道配置指南

> OPS-2A 实现文档

## 概述

VabHub 支持多种告警渠道，当系统健康检查发现问题时，可以将告警推送到配置的渠道。

## 支持的渠道类型

### 1. Telegram

通过 Telegram Bot 发送告警消息。

**所需配置：**
| 字段 | 说明 | 示例 |
|------|------|------|
| `bot_token` | Telegram Bot Token | `1234567890:ABCdef...` |
| `chat_id` | 目标 Chat ID | `-1001234567890` 或 `123456789` |

**如何获取：**
1. 通过 [@BotFather](https://t.me/BotFather) 创建 Bot，获取 Token
2. 将 Bot 添加到群组或与 Bot 私聊
3. 通过 `https://api.telegram.org/bot<TOKEN>/getUpdates` 获取 Chat ID

### 2. Webhook

发送 HTTP 请求到自定义 Webhook URL。

**所需配置：**
| 字段 | 说明 | 示例 |
|------|------|------|
| `url` | Webhook URL | `https://example.com/alert` |
| `method` | HTTP 方法 | `POST`（默认）或 `GET` |
| `headers` | 额外 Headers（可选） | `{"Authorization": "Bearer xxx"}` |

**Webhook 请求格式（POST JSON）：**
```json
{
  "title": "系统健康告警：disk.data",
  "body": "检查项：disk.data\n严重级别：ERROR\n错误信息：可用空间不足\n时间：2025-01-01 12:00:00 UTC",
  "channel_name": "My Webhook",
  "severity": "error"
}
```

### 3. Bark

通过 Bark App 发送 iOS 推送通知。

**所需配置：**
| 字段 | 说明 | 示例 |
|------|------|------|
| `server` | Bark 服务器地址 | `https://api.day.app/your-key` |
| `sound` | 提示音（可选） | `alarm`、`bell` 等 |
| `group` | 分组名称（可选） | `VabHub` |

**如何获取：**
1. 在 App Store 下载 Bark App
2. 打开 App，复制推送 URL（类似 `https://api.day.app/xxxxx`）

## 通知策略

### 最小告警级别

每个渠道可以设置最小告警级别：
- **INFO**：接收所有通知（含信息级别）
- **WARNING**：只接收警告和错误
- **ERROR**：只接收错误

### 过滤规则

**白名单（include_checks）：**
- 只接收匹配的检查项告警
- 留空表示接收所有
- 支持通配符：`disk.*` 匹配所有磁盘检查

**黑名单（exclude_checks）：**
- 排除匹配的检查项告警
- 支持通配符：`manga_source.*` 排除所有漫画源检查

### 降频机制

系统内置降频逻辑，只在状态**恶化**时发送通知：
- OK → WARNING：发送警告
- OK → ERROR：发送错误
- WARNING → ERROR：发送错误
- ERROR → OK：不发送（恢复时不通知）
- ERROR → ERROR：不发送（相同状态不重复）

## 配置示例

### Telegram 渠道 - 只接收错误

```json
{
  "name": "运维群告警",
  "channel_type": "telegram",
  "is_enabled": true,
  "min_severity": "error",
  "config": {
    "bot_token": "1234567890:ABCdef...",
    "chat_id": "-1001234567890"
  },
  "include_checks": null,
  "exclude_checks": null
}
```

### Bark 渠道 - 只关心磁盘和下载器

```json
{
  "name": "个人手机推送",
  "channel_type": "bark",
  "is_enabled": true,
  "min_severity": "warning",
  "config": {
    "server": "https://api.day.app/your-key",
    "sound": "alarm",
    "group": "VabHub"
  },
  "include_checks": ["disk.*", "service.download_client"],
  "exclude_checks": null
}
```

### Webhook 渠道 - 排除漫画源

```json
{
  "name": "自定义 Webhook",
  "channel_type": "webhook",
  "is_enabled": true,
  "min_severity": "warning",
  "config": {
    "url": "https://your-server.com/vabhub-alert",
    "method": "POST"
  },
  "include_checks": null,
  "exclude_checks": ["manga_source.*", "music_chart_source.*"]
}
```

## API 端点

| 端点 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/api/admin/alert_channels` | GET | 获取所有渠道 | Admin |
| `/api/admin/alert_channels` | POST | 创建渠道 | Admin |
| `/api/admin/alert_channels/{id}` | GET | 获取单个渠道 | Admin |
| `/api/admin/alert_channels/{id}` | PUT | 更新渠道 | Admin |
| `/api/admin/alert_channels/{id}` | DELETE | 删除渠道 | Admin |
| `/api/admin/alert_channels/{id}/test` | POST | 发送测试消息 | Admin |

## 前端管理

访问 `/admin/alert-channels` 进入告警渠道管理页面：

1. **查看列表**：显示所有配置的告警渠道
2. **添加渠道**：点击"添加渠道"按钮
3. **编辑渠道**：点击编辑图标
4. **测试渠道**：点击发送图标，发送测试消息
5. **启用/禁用**：通过开关快速切换

## 故障排查

### Telegram 发送失败
1. 检查 Bot Token 是否正确
2. 确认 Bot 已添加到目标群组或与用户有对话
3. 检查 Chat ID 是否正确（群组 ID 通常是负数）

### Webhook 发送失败
1. 检查 URL 是否可访问
2. 确认目标服务器正常运行
3. 检查是否有防火墙阻止

### Bark 发送失败
1. 检查服务器地址格式是否正确
2. 确认 Bark App 已安装并有网络连接
3. 检查推送权限是否开启

## 相关文件

### 后端
- `backend/app/models/alert_channel.py` - 数据模型
- `backend/app/models/enums/alert_channel_type.py` - 渠道类型枚举
- `backend/app/models/enums/alert_severity.py` - 严重级别枚举
- `backend/app/schemas/alert_channel.py` - Pydantic Schema
- `backend/app/services/alert_channel_service.py` - 渠道服务
- `backend/app/modules/alert_channels/` - 适配器模块
- `backend/app/api/alert_channels.py` - API 端点

### 前端
- `frontend/src/types/alertChannel.ts` - 类型定义
- `frontend/src/pages/admin/AlertChannelAdmin.vue` - 管理页面
