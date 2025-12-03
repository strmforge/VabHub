# VabHub API端点清单

## 📊 API模块总览

**总模块数**: 20个  
**总路由数**: 130个  
**API前缀**: `/api/v1`

---

## 🔐 1. 认证模块 (auth)

**前缀**: `/api/v1/auth`  
**标签**: `认证`

### 端点
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户信息
- `POST /api/v1/auth/refresh` - 刷新Token
- `POST /api/v1/auth/logout` - 用户登出

---

## 🔍 2. 搜索模块 (search)

**前缀**: `/api/v1/search`  
**标签**: `搜索`

### 端点
- `GET /api/v1/search` - 搜索资源
- `POST /api/v1/search/multi` - 多源搜索
- `GET /api/v1/search/history` - 获取搜索历史
- `DELETE /api/v1/search/history/{history_id}` - 删除搜索历史

---

## 📋 3. 订阅管理模块 (subscription)

**前缀**: `/api/v1/subscriptions`  
**标签**: `订阅`

### 端点
- `GET /api/v1/subscriptions` - 获取订阅列表
- `POST /api/v1/subscriptions` - 创建订阅
- `GET /api/v1/subscriptions/{subscription_id}` - 获取订阅详情
- `PUT /api/v1/subscriptions/{subscription_id}` - 更新订阅
- `DELETE /api/v1/subscriptions/{subscription_id}` - 删除订阅
- `POST /api/v1/subscriptions/{subscription_id}/search` - 执行订阅搜索
- `POST /api/v1/subscriptions/{subscription_id}/enable` - 启用订阅
- `POST /api/v1/subscriptions/{subscription_id}/disable` - 禁用订阅

---

## ⬇️ 4. 下载管理模块 (download)

**前缀**: `/api/v1/downloads`  
**标签**: `下载`

### 端点
- `GET /api/v1/downloads` - 获取下载列表
- `POST /api/v1/downloads` - 创建下载任务
- `GET /api/v1/downloads/{download_id}` - 获取下载详情
- `PUT /api/v1/downloads/{download_id}` - 更新下载任务
- `DELETE /api/v1/downloads/{download_id}` - 删除下载任务
- `POST /api/v1/downloads/{download_id}/pause` - 暂停下载
- `POST /api/v1/downloads/{download_id}/resume` - 恢复下载
- `POST /api/v1/downloads/{download_id}/stop` - 停止下载

---

## 📊 5. 仪表盘模块 (dashboard)

**前缀**: `/api/v1/dashboard`  
**标签**: `仪表盘`

### 端点
- `GET /api/v1/dashboard` - 获取仪表盘数据
- `GET /api/v1/dashboard/stats` - 获取统计数据
- `GET /api/v1/dashboard/recent` - 获取最近活动

---

## 🔄 6. 工作流模块 (workflow)

**前缀**: `/api/v1/workflows`  
**标签**: `工作流`

### 端点
- `GET /api/v1/workflows` - 获取工作流列表
- `POST /api/v1/workflows` - 创建工作流
- `GET /api/v1/workflows/{workflow_id}` - 获取工作流详情
- `PUT /api/v1/workflows/{workflow_id}` - 更新工作流
- `DELETE /api/v1/workflows/{workflow_id}` - 删除工作流
- `POST /api/v1/workflows/{workflow_id}/execute` - 执行工作流
- `GET /api/v1/workflows/{workflow_id}/executions` - 获取工作流执行历史

---

## 🌐 7. 站点管理模块 (site)

**前缀**: `/api/v1/sites`  
**标签**: `站点管理`

### 端点
- `GET /api/v1/sites` - 获取站点列表
- `POST /api/v1/sites` - 创建站点
- `GET /api/v1/sites/{site_id}` - 获取站点详情
- `PUT /api/v1/sites/{site_id}` - 更新站点
- `DELETE /api/v1/sites/{site_id}` - 删除站点
- `POST /api/v1/sites/{site_id}/checkin` - 站点签到
- `POST /api/v1/sites/{site_id}/test` - 测试站点连接
- `POST /api/v1/sites/sync-cookiecloud` - 同步CookieCloud

---

## 🔔 8. 通知模块 (notification)

**前缀**: `/api/v1/notifications`  
**标签**: `通知`

### 端点
- `GET /api/v1/notifications` - 获取通知列表
- `POST /api/v1/notifications` - 创建通知
- `GET /api/v1/notifications/{notification_id}` - 获取通知详情
- `PUT /api/v1/notifications/{notification_id}/read` - 标记通知为已读
- `DELETE /api/v1/notifications/{notification_id}` - 删除通知
- `POST /api/v1/notifications/read-all` - 标记所有通知为已读
- `GET /api/v1/notifications/unread-count` - 获取未读通知数量

---

## 📅 9. 日历模块 (calendar)

**前缀**: `/api/v1/calendar`  
**标签**: `日历`

### 端点
- `GET /api/v1/calendar` - 获取日历事件
- `GET /api/v1/calendar/ical` - 导出iCalendar文件

---

## 🎵 10. 音乐模块 (music)

**前缀**: `/api/v1/music`  
**标签**: `音乐`

### 端点
- `GET /api/v1/music/subscriptions` - 获取音乐订阅列表
- `POST /api/v1/music/subscriptions` - 创建音乐订阅
- `GET /api/v1/music/subscriptions/{subscription_id}` - 获取音乐订阅详情
- `PUT /api/v1/music/subscriptions/{subscription_id}` - 更新音乐订阅
- `DELETE /api/v1/music/subscriptions/{subscription_id}` - 删除音乐订阅
- `GET /api/v1/music/search` - 搜索音乐
- `GET /api/v1/music/charts` - 获取音乐榜单
- `GET /api/v1/music/recommendations` - 获取音乐推荐

---

## 🎬 11. 媒体模块 (media)

**前缀**: `/api/v1/media`  
**标签**: `媒体`

### 端点
- `GET /api/v1/media/search` - 搜索媒体
- `GET /api/v1/media/{media_id}` - 获取媒体详情
- `GET /api/v1/media/{media_id}/seasons` - 获取电视剧季数
- `GET /api/v1/media/{media_id}/episodes` - 获取剧集列表

---

## 🔌 12. WebSocket模块 (websocket)

**前缀**: 无  
**标签**: `WebSocket`

### 端点
- `WS /ws` - WebSocket连接
- `WS /ws/{channel}` - 指定频道的WebSocket连接

---

## ⚙️ 13. 设置模块 (settings)

**前缀**: `/api/v1/settings`  
**标签**: `系统设置`

### 端点
- `GET /api/v1/settings` - 获取设置列表
- `GET /api/v1/settings/{key}` - 获取设置项
- `PUT /api/v1/settings/{key}` - 更新设置项
- `POST /api/v1/settings` - 创建设置项
- `DELETE /api/v1/settings/{key}` - 删除设置项

---

## 🛡️ 14. HNR检测模块 (hnr)

**前缀**: `/api/v1/hnr`  
**标签**: `HNR检测`

### 端点
- `GET /api/v1/hnr/detections` - 获取HNR检测列表
- `GET /api/v1/hnr/detections/{detection_id}` - 获取HNR检测详情
- `POST /api/v1/hnr/detections` - 创建HNR检测
- `GET /api/v1/hnr/tasks` - 获取HNR任务列表
- `POST /api/v1/hnr/tasks` - 创建HNR任务
- `GET /api/v1/hnr/tasks/{task_id}` - 获取HNR任务详情
- `PUT /api/v1/hnr/tasks/{task_id}` - 更新HNR任务
- `DELETE /api/v1/hnr/tasks/{task_id}` - 删除HNR任务
- `POST /api/v1/hnr/signatures/reload` - 重新加载签名包

---

## 📊 15. 榜单模块 (charts)

**前缀**: `/api/v1/charts`  
**标签**: `榜单`

### 端点
- `GET /api/v1/charts/music` - 获取音乐榜单
- `GET /api/v1/charts/video` - 获取视频榜单
- `GET /api/v1/charts/compare` - 对比榜单

---

## 🎯 16. 推荐模块 (recommendation)

**前缀**: `/api/v1/recommendations`  
**标签**: `推荐`

### 端点
- `GET /api/v1/recommendations/settings` - 获取推荐设置
- `PUT /api/v1/recommendations/settings` - 更新推荐设置
- `GET /api/v1/recommendations/user` - 获取用户推荐
- `GET /api/v1/recommendations/popular` - 获取热门推荐
- `GET /api/v1/recommendations/similar/{media_id}` - 获取相似内容

---

## 🔍 17. 媒体识别模块 (media_identification)

**前缀**: `/api/v1/media-identification`  
**标签**: `媒体识别`

### 端点
- `POST /api/v1/media-identification/identify` - 识别媒体
- `POST /api/v1/media-identification/batch` - 批量识别媒体
- `POST /api/v1/media-identification/upload` - 上传文件识别
- `GET /api/v1/media-identification/history` - 获取识别历史
- `DELETE /api/v1/media-identification/history/{history_id}` - 删除识别历史

---

## 💚 18. 健康检查模块 (health)

**前缀**: `/api/v1/health`  
**标签**: `健康检查`

### 端点
- `GET /api/v1/health` - 整体健康检查
- `GET /api/v1/health/database` - 数据库健康检查
- `GET /api/v1/health/cache` - 缓存健康检查
- `GET /api/v1/health/redis` - Redis健康检查

---

## ⏰ 19. 定时任务模块 (scheduler)

**前缀**: `/api/v1/scheduler`  
**标签**: `定时任务`

### 端点
- `GET /api/v1/scheduler/tasks` - 获取定时任务列表
- `GET /api/v1/scheduler/tasks/{task_id}` - 获取定时任务详情
- `POST /api/v1/scheduler/tasks/{task_id}/run` - 手动执行任务
- `POST /api/v1/scheduler/tasks/{task_id}/pause` - 暂停任务
- `POST /api/v1/scheduler/tasks/{task_id}/resume` - 恢复任务

---

## ☁️ 20. 云存储模块 (cloud_storage)

**前缀**: `/api/v1/cloud-storage`  
**标签**: `云存储`

### 端点
- `GET /api/v1/cloud-storage` - 获取云存储列表
- `POST /api/v1/cloud-storage` - 创建云存储配置
- `GET /api/v1/cloud-storage/{storage_id}` - 获取云存储详情
- `PUT /api/v1/cloud-storage/{storage_id}` - 更新云存储配置
- `DELETE /api/v1/cloud-storage/{storage_id}` - 删除云存储配置
- `POST /api/v1/cloud-storage/{storage_id}/qrcode` - 生成二维码
- `GET /api/v1/cloud-storage/{storage_id}/status` - 检查登录状态
- `GET /api/v1/cloud-storage/{storage_id}/files` - 获取文件列表
- `POST /api/v1/cloud-storage/{storage_id}/upload` - 上传文件
- `GET /api/v1/cloud-storage/{storage_id}/download/{file_id}` - 下载文件
- `POST /api/v1/cloud-storage/{storage_id}/move` - 移动文件
- `POST /api/v1/cloud-storage/{storage_id}/copy` - 复制文件
- `POST /api/v1/cloud-storage/{storage_id}/rename` - 重命名文件
- `DELETE /api/v1/cloud-storage/{storage_id}/files/{file_id}` - 删除文件
- `POST /api/v1/cloud-storage/{storage_id}/mkdir` - 创建文件夹
- `GET /api/v1/cloud-storage/{storage_id}/usage` - 获取存储使用情况

---

## 📊 统计信息

### 按模块统计
- **认证模块**: 5个端点
- **搜索模块**: 4个端点
- **订阅管理**: 8个端点
- **下载管理**: 8个端点
- **仪表盘**: 3个端点
- **工作流**: 7个端点
- **站点管理**: 8个端点
- **通知**: 7个端点
- **日历**: 2个端点
- **音乐**: 8个端点
- **媒体**: 4个端点
- **WebSocket**: 2个端点
- **设置**: 5个端点
- **HNR检测**: 9个端点
- **榜单**: 3个端点
- **推荐**: 5个端点
- **媒体识别**: 5个端点
- **健康检查**: 4个端点
- **定时任务**: 5个端点
- **云存储**: 14个端点

### 总计
- **总模块数**: 20个
- **总端点数**: 约130个
- **API前缀**: `/api/v1`

---

## 🔒 认证要求

### 需要认证的端点
- 大部分API端点需要认证
- 使用JWT Token进行认证
- Token通过 `Authorization: Bearer <token>` 头部传递

### 不需要认证的端点
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/health` - 健康检查（部分）
- `GET /` - 根端点
- `GET /docs` - API文档

---

## 📝 响应格式

### 统一响应格式
所有API端点使用统一的响应格式：

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "error_code": null,
  "timestamp": "2025-11-09T00:00:00"
}
```

### 错误响应格式
```json
{
  "success": false,
  "data": null,
  "message": "错误信息",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-11-09T00:00:00"
}
```

---

## 🎯 下一步

### 测试计划
1. **基础测试**
   - 测试各个模块的端点
   - 验证响应格式
   - 检查错误处理

2. **功能测试**
   - 测试订阅管理功能
   - 测试下载管理功能
   - 测试搜索系统功能

3. **集成测试**
   - 测试前后端集成
   - 测试API响应格式
   - 测试错误处理

---

**创建时间**: 2025-11-09  
**最后更新**: 2025-11-09  
**状态**: 完整清单

