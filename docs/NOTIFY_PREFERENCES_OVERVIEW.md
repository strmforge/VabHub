# 通知偏好系统 (NOTIFY-UX-1)

## 概述

VabHub 提供细粒度的用户通知偏好系统，允许用户：
- 按事件类型配置是否接收通知
- 选择通过哪些渠道接收（Web、Telegram、Webhook、Bark）
- 全局静音或临时 Snooze
- 针对特定作品静音

## 功能特性

### 1. 事件类型控制

支持的通知类型：

| 分组 | 类型 | 说明 |
|------|------|------|
| 漫画 | MANGA_NEW_CHAPTER | 漫画新章节 |
| 漫画 | MANGA_UPDATED | 漫画更新通知 |
| 漫画 | MANGA_SYNC_FAILED | 漫画同步失败 |
| 小说 | NOVEL_NEW_CHAPTER | 小说新章节 |
| 小说 | AUDIOBOOK_NEW_TRACK | 有声书新音轨 |
| 小说 | TTS_JOB_COMPLETED | TTS 任务完成 |
| 小说 | TTS_JOB_FAILED | TTS 任务失败 |
| 小说 | AUDIOBOOK_READY | 有声书整体就绪 |
| 音乐 | MUSIC_CHART_UPDATED | 音乐榜单更新 |
| 音乐 | MUSIC_NEW_TRACKS_QUEUED | 新音乐已排队 |
| 音乐 | MUSIC_NEW_TRACKS_DOWNLOADING | 新音乐下载中 |
| 音乐 | MUSIC_NEW_TRACKS_READY | 新音乐已就绪 |
| 系统 | SYSTEM_MESSAGE | 重要系统通知 |

### 2. 渠道控制

每种通知类型可以独立控制：
- **Web 通知**：站内通知铃铛
- **Telegram**：Telegram Bot 推送
- **Webhook**：自定义 Webhook 推送
- **Bark**：iOS Bark 推送

### 3. 静音功能

#### 全局静音
- 暂停所有通知推送
- 可选"允许重要通知"（如系统告警）

#### 临时静音 (Snooze)
- 静音 30 分钟 / 1 小时 / 2 小时 / 4 小时
- 静音到今晚 23:59
- 自定义静音时长

#### 单作品静音
- 针对特定漫画/小说/音乐静音
- 不影响其他作品的通知

## Web 端使用

### 进入设置页面

1. 点击顶部导航栏的通知铃铛
2. 点击"设置"按钮
3. 或直接访问 `/settings/notify-preferences`

### 设置页面功能

#### 通知状态卡片
- 显示当前状态（正常/静音中）
- 快捷静音按钮
- 全局静音开关
- "允许重要通知"开关

#### 通知类型矩阵
- 列出所有通知类型，按分组显示
- 每行显示：类型名称、描述
- 每列显示：Web / Telegram / Webhook / Bark / 静音
- 勾选/取消勾选即时保存

#### 已静音作品列表
- 显示单独静音的作品
- 可取消静音

## Telegram Bot 使用

### /notify 命令

发送 `/notify` 显示通知偏好菜单：

```
🔔 通知偏好设置

当前状态: 正常

点击下方按钮开关各类通知：

[✅ 漫画更新] [✅ 小说/TTS]
[✅ 音乐订阅] [✅ 系统通知]
[⏰ 临时静音]
[🔕 全局静音]
[« 返回主菜单]
```

### 功能按钮

- **分组开关**：点击切换该分组所有通知的开关状态
- **临时静音**：选择静音时长
- **全局静音**：开启/关闭全局静音

### 临时静音菜单

```
⏰ 临时静音

选择静音时长：

[30 分钟] [1 小时]
[2 小时] [4 小时]
[今晚 (23:59)]
[« 返回]
```

## API 说明

### 获取偏好矩阵

```
GET /api/notify/preferences/matrix
```

返回：
```json
{
  "preferences": [...],
  "snooze": {...},
  "available_notification_types": [...]
}
```

### 更新偏好

```
PUT /api/notify/preferences
```

Body:
```json
{
  "notification_type": "MANGA_UPDATED",
  "enable_web": true,
  "enable_telegram": false,
  "muted": false
}
```

### 设置 Snooze

```
PUT /api/notify/preferences/snooze
```

Body:
```json
{
  "muted": false,
  "snooze_until": "2024-01-01T23:59:00Z",
  "allow_critical_only": true
}
```

### 快速 Snooze

```
POST /api/notify/preferences/snooze/quick
```

Body:
```json
{
  "duration_minutes": 120
}
```

### 清除 Snooze

```
DELETE /api/notify/preferences/snooze
```

### 静音某类通知

```
POST /api/notify/preferences/mute-type
```

Body:
```json
{
  "notification_type": "MANGA_UPDATED",
  "media_type": "MANGA",
  "target_id": 123
}
```

## 相关文件

### 后端

**模型：**
- `backend/app/models/user_notify_preference.py` - 用户通知偏好模型
- `backend/app/models/user_notify_snooze.py` - 用户静音状态模型

**Schema：**
- `backend/app/schemas/notify_preferences.py` - Pydantic Schema

**服务：**
- `backend/app/services/notify_preference_service.py` - 偏好服务（核心逻辑）

**API：**
- `backend/app/api/notify_preferences.py` - REST API

**Telegram：**
- `backend/app/modules/bots/commands/notify.py` - /notify 命令

### 前端

**类型：**
- `frontend/src/types/notifyPreferences.ts` - TypeScript 类型定义

**API：**
- `frontend/src/services/api.ts` - `notifyPreferenceApi`

**页面：**
- `frontend/src/pages/settings/UserNotifyPreferencesPage.vue` - 设置页面

**组件：**
- `frontend/src/components/layout/NotificationBell.vue` - 通知铃铛（含设置入口）

## 注意事项

1. **不影响系统告警**：用户级通知偏好不会影响 OPS 系统告警（AlertChannel）
2. **默认行为**：没有任何偏好记录时，保持原有行为（全部照旧发送）
3. **静音仍记录**：静音的通知仍会写入 UserNotification 表，只是不推送
4. **重要通知**：SYSTEM_MESSAGE 等重要通知可以绕过静音
