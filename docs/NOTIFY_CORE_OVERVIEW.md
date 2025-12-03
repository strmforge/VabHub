# NOTIFY-CORE 统一用户通知核心

## 概述

NOTIFY-CORE 是 VabHub 的统一用户通知系统，用于管理用户级别的通知渠道配置，并将各类事件通知推送到用户配置的外部设备。

## 与 OPS AlertChannel 的区别

| 特性 | UserNotifyChannel | AlertChannel |
|------|-------------------|--------------|
| 用途 | 用户级通知 | 系统级告警 |
| 配置者 | 每个用户自己 | 管理员 |
| 典型场景 | 漫画更新、下载完成、TTS 就绪 | 系统健康异常、磁盘空间不足 |
| 前端入口 | /settings/notify-channels | /admin/alert-channels |

## 支持的渠道类型

### 1. Telegram Bot

通过 Telegram Bot 接收通知。

**配置方式**: 通过绑定流程自动配置，无需手动输入。

**绑定流程**:
1. 在 Web 界面点击"获取绑定码"
2. 在 Telegram 中向 VabHub Bot 发送 `/start <绑定码>`
3. 绑定成功后自动创建渠道

### 2. Webhook

发送 HTTP 请求到自定义 URL。

**配置字段**:

| 字段 | 说明 | 必填 |
|------|------|------|
| `url` | Webhook URL | 是 |
| `secret` | 请求签名密钥 | 否 |

**请求格式**:
```json
{
  "title": "漫画更新",
  "message": "《XXX》更新了 3 话",
  "url": "https://vabhub.example.com/manga/123",
  "extra": {}
}
```

### 3. Bark

通过 Bark App 发送 iOS 推送通知。

**配置字段**:

| 字段 | 说明 | 必填 |
|------|------|------|
| `server` | Bark 服务器地址 | 是 |
| `sound` | 提示音 | 否 |
| `group` | 分组名称 | 否 |

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/notify/channels` | GET | 获取当前用户的渠道列表 |
| `/api/notify/channels` | POST | 创建渠道 |
| `/api/notify/channels/{id}` | PUT | 更新渠道 |
| `/api/notify/channels/{id}` | DELETE | 删除渠道 |
| `/api/notify/channels/{id}/test` | POST | 发送测试消息 |

## 通知总线

### notify_user 函数

所有用户通知都通过 `notify_user` 函数发送：

```python
from app.services.notify_user_service import notify_user

await notify_user(
    session,
    user,
    title="漫画更新",
    message="《XXX》更新了 3 话",
    event_type=NotificationType.MANGA_UPDATED,
    media_type="manga",
    target_id=series_id,
    url="https://vabhub.example.com/manga/123",
)
```

### 行为

1. 写入 `UserNotification` 表（Web 通知列表）
2. 获取用户所有启用的 `UserNotifyChannel`
3. 并行调用各渠道适配器发送消息
4. 失败时记录日志但不抛异常

## 已接入的事件

| 事件类型 | 说明 | 函数 |
|----------|------|------|
| MANGA_UPDATED | 漫画更新 | `notify_manga_updated` |
| TTS_JOB_COMPLETED | TTS 任务完成 | `notify_tts_job_completed` |
| MUSIC_NEW_TRACKS_READY | 音乐新曲目就绪 | `notify_music_new_tracks_ready` |

## 前端页面

访问 `/settings/notify-channels` 进入通知渠道管理页面：

1. **渠道列表**: 显示所有已配置的渠道
2. **添加渠道**: 点击"添加渠道"按钮
3. **Telegram 绑定**: 通过绑定码关联 Telegram 账号
4. **测试**: 发送测试消息验证配置

## 未来扩展

以下渠道类型预留但暂未实现：

- **WeCom（企业微信）**
- **飞书**
- **Discord**
- **Slack**

**明确不支持**:
- SMTP 邮件
- Prometheus / Grafana 集成

## 相关文件

### 后端

- `backend/app/models/enums/user_notify_channel_type.py` - 渠道类型枚举
- `backend/app/models/user_notify_channel.py` - 渠道模型
- `backend/app/schemas/user_notify_channel.py` - Pydantic Schema
- `backend/app/services/user_notify_channel_service.py` - 渠道服务
- `backend/app/services/notify_user_service.py` - 通知总线
- `backend/app/modules/user_notify_channels/` - 渠道适配器
- `backend/app/api/user_notify_channels.py` - API 端点

### 前端

- `frontend/src/types/userNotifyChannel.ts` - 类型定义
- `frontend/src/pages/settings/UserNotifyChannelsPage.vue` - 管理页面
