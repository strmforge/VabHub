# 开发者通知系统文档

## 概述

VabHub 通知系统支持多种类型的通知，包括阅读、下载、系统等。本文档主要介绍下载相关通知的实现和使用。

## 下载通知类型

### 1. DOWNLOAD_SUBSCRIPTION_MATCHED - 订阅命中通知

**触发时机**：当用户订阅规则匹配到新内容并创建下载任务时

**Payload 结构**：
```json
{
  "notification_type": "DOWNLOAD_SUBSCRIPTION_MATCHED",
  "subscription_name": "订阅规则名称",
  "title": "下载内容标题",
  "route_name": "download-tasks",
  "route_params": {"task_id": 123},
  "task_id": 123,
  "subscription_id": 456,
  "torrent_id": 789,
  "category_label": "anime",
  "rule_labels": ["1080p", "中字"]
}
```

**前端组件**：`DownloadNotificationCard.vue` (蓝色主题)

### 2. DOWNLOAD_TASK_COMPLETED - 下载完成通知

**触发时机**：当下载任务完成并尝试入库时

**Payload 结构**：
```json
{
  "notification_type": "DOWNLOAD_TASK_COMPLETED",
  "title": "下载内容标题",
  "route_name": "download-tasks", 
  "route_params": {"task_id": 123},
  "task_id": 123,
  "success": true,
  "media_type": "anime",
  "file_size_gb": 2.5,
  "download_duration_minutes": 45,
  "library_path": "/media/anime/title",
  "season_number": 1,
  "episode_number": 12,
  "category_label": "anime"
}
```

**前端组件**：`DownloadNotificationCard.vue` (绿色主题，成功时)

### 3. DOWNLOAD_HR_RISK - HR 风险通知

**触发时机**：当下载任务存在保种要求或风险时

**Payload 结构**：
```json
{
  "notification_type": "DOWNLOAD_HR_RISK",
  "title": "下载内容标题",
  "route_name": "download-tasks",
  "route_params": {"task_id": 123},
  "task_id": 123,
  "risk_level": "H&R",
  "reason": "站点要求永久保种",
  "min_seed_time_hours": 72,
  "category_label": "anime"
}
```

**前端组件**：`DownloadNotificationCard.vue` (橙色主题)

## 后端实现

### 触发点位置

1. **订阅命中**：`app/modules/subscription/service.py:607`
   ```python
   await notify_download_subscription_matched_for_user(
       session=session,
       user_id=user_id,
       payload=notification_payload
   )
   ```

2. **下载完成**：`app/modules/download/status_updater.py:301`
   ```python
   await notify_download_task_completed_for_user(
       session=self.db,
       user_id=user_id,
       payload=notification_payload
   )
   ```

### Helper 函数

所有下载通知都通过 `app/services/notification_service.py` 中的统一函数处理：

- `notify_download_subscription_matched_for_user()`
- `notify_download_task_completed_for_user()`
- `notify_download_hr_risk_for_user()`

## 前端实现

### 组件集成

下载通知使用专用的 `DownloadNotificationCard` 组件，在以下位置集成：

1. **通知列表页面**：`frontend/src/pages/UserNotifications.vue`
   - 通过 `isDownloadNotification()` 函数识别下载通知
   - 动态渲染不同类型的下载通知卡片

2. **通知抽屉**：`frontend/src/components/common/NotificationDrawer.vue`
   - 支持下载通知的路由跳转

### 类型定义

前端类型定义位于 `frontend/src/types/notify.ts`：

```typescript
export type NotificationType = 
  | 'DOWNLOAD_SUBSCRIPTION_MATCHED' 
  | 'DOWNLOAD_TASK_COMPLETED' 
  | 'DOWNLOAD_HR_RISK'
  | // ... 其他类型

export interface NotificationPayload {
  // 下载通知相关字段
  notification_type?: string
  subscription_name?: string
  file_size_gb?: number
  download_duration_minutes?: number
  category_label?: string
  risk_level?: string
  reason?: string
  min_seed_time_hours?: number
  // ... 其他字段
}
```

## Telegram 推送配置

### 当前策略

- **HR 风险通知**：默认启用 Telegram 推送（关键提醒）
- **订阅命中/下载完成**：默认禁用 Telegram 推送（避免噪音）

### 启用所有下载通知推送

如需启用订阅命中和下载完成的 Telegram 推送，取消注释以下代码：

1. **订阅命中推送**：`app/services/notification_service.py:782-797`
2. **下载完成推送**：`app/services/notification_service.py:841-856`

### 消息格式化

Telegram 消息通过 `TelegramChannel._format_message()` 格式化：

- 支持 Markdown/HTML 格式
- 自动添加 emoji 图标
- 根据通知类型设置不同颜色

## 用户偏好设置

通知系统支持用户级别的偏好设置：

- 通过 `notify_preference_service.py` 评估通知投递决策
- 支持按通知类型、媒体类型过滤
- 支持渠道级别开关（Telegram/Webhook/Bark）

## 开发指南

### 添加新的下载通知类型

1. **后端**：
   - 在 `app/schemas/notification_download.py` 中定义新的 Payload schema
   - 在 `app/services/notification_service.py` 中添加 helper 函数
   - 在 `app/models/enums/notification_type.py` 中添加新类型

2. **前端**：
   - 在 `frontend/src/types/notify.ts` 中更新 `NotificationType`
   - 在 `DownloadNotificationCard.vue` 中添加新的渲染逻辑
   - 在 `UserNotifications.vue` 中更新类型识别函数

### 测试通知

使用测试脚本验证通知功能：

```python
# test_notifications.py
python test_notifications.py
```

## 故障排除

### 常见问题

1. **通知未显示**：检查 `UserNotification` 表中的记录
2. **Telegram 未推送**：确认用户已配置 Telegram 渠道且偏好允许
3. **前端渲染错误**：检查 payload 字段是否与类型定义匹配

### 日志调试

相关日志关键词：
- `[notify]` - 通知系统日志
- `[notify-user]` - 用户通知日志
- `DownloadNotificationCard` - 前端组件日志

## 版本历史

- **v1.0** - 初始下载通知支持（订阅命中、下载完成、HR 风险）
- **v1.1** - 前端专用组件集成
- **v1.2** - Telegram 推送优化
