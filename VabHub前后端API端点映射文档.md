# VabHub 前后端API端点映射文档

## 📋 概述

本文档提供了VabHub所有API端点的完整映射，包括前端页面使用情况和后端实现位置。

## 🔗 API端点结构

### 基础路径
- **API前缀**: `/api/v1`
- **文档**: `/docs` (Swagger UI)
- **ReDoc**: `/redoc`

## 📊 API端点列表

### 1. 认证模块 (`/api/v1/auth`)

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/api/v1/auth/register` | POST | 用户注册 | `pages/login.vue` | `Token` |
| `/api/v1/auth/login` | POST | 用户登录 | `pages/login.vue` | `Token` |
| `/api/v1/auth/me` | GET | 获取当前用户信息 | `pages/profile.vue` | `UserResponse` |
| `/api/v1/auth/logout` | POST | 用户登出 | 所有页面 | `SuccessResponse` |

**后端实现**:
- API层: `backend/app/api/auth.py`
- 模型: `backend/app/models/user.py`
- 服务: `backend/app/core/security.py`

---

### 2. 搜索模块 (`/api/v1/search`)

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/api/v1/search` | POST | 搜索资源 | `pages/resource.vue`, `pages/discover.vue` | `SearchResponse` |
| `/api/v1/search/history` | GET | 获取搜索历史 | `pages/resource.vue` | `List[SearchHistory]` |
| `/api/v1/search/suggestions` | GET | 获取搜索建议 | `pages/resource.vue` | `List[str]` |

**后端实现**:
- API层: `backend/app/api/search.py`
- Chain层: `backend/app/chain/search.py` (SearchChain)
- 服务: `backend/app/modules/search/service.py`

---

### 3. 订阅模块 (`/api/v1/subscriptions`)

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/api/v1/subscriptions` | GET | 获取订阅列表 | `pages/subscribe.vue` | `List[SubscriptionResponse]` |
| `/api/v1/subscriptions` | POST | 创建订阅 | `pages/subscribe.vue` | `SubscriptionResponse` |
| `/api/v1/subscriptions/{id}` | GET | 获取订阅详情 | `pages/subscribe.vue` | `SubscriptionResponse` |
| `/api/v1/subscriptions/{id}` | PUT | 更新订阅 | `pages/subscribe.vue` | `SubscriptionResponse` |
| `/api/v1/subscriptions/{id}` | DELETE | 删除订阅 | `pages/subscribe.vue` | `SuccessResponse` |
| `/api/v1/subscriptions/{id}/enable` | POST | 启用订阅 | `pages/subscribe.vue` | `SubscriptionResponse` |
| `/api/v1/subscriptions/{id}/disable` | POST | 禁用订阅 | `pages/subscribe.vue` | `SubscriptionResponse` |
| `/api/v1/subscriptions/{id}/search` | POST | 执行订阅搜索 | `pages/subscribe.vue` | `SearchResponse` |

**后端实现**:
- API层: `backend/app/api/subscription.py`
- Chain层: `backend/app/chain/subscribe.py` (SubscribeChain)
- 服务: `backend/app/modules/subscription/service.py`
- 模型: `backend/app/models/subscription.py`

---

### 4. 下载模块 (`/api/v1/downloads`)

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/api/v1/downloads` | GET | 获取下载列表 | `pages/downloading.vue`, `pages/history.vue` | `List[DownloadResponse]` |
| `/api/v1/downloads` | POST | 创建下载任务 | `pages/resource.vue` | `DownloadResponse` |
| `/api/v1/downloads/{id}` | GET | 获取下载详情 | `pages/downloading.vue` | `DownloadResponse` |
| `/api/v1/downloads/{id}/pause` | POST | 暂停下载 | `pages/downloading.vue` | `SuccessResponse` |
| `/api/v1/downloads/{id}/resume` | POST | 恢复下载 | `pages/downloading.vue` | `SuccessResponse` |
| `/api/v1/downloads/{id}` | DELETE | 删除下载 | `pages/downloading.vue` | `SuccessResponse` |

**后端实现**:
- API层: `backend/app/api/download.py`
- Chain层: `backend/app/chain/download.py` (DownloadChain)
- 服务: `backend/app/modules/download/service.py`

---

### 5. 仪表盘模块 (`/api/v1/dashboard`)

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/api/v1/dashboard` | GET | 获取仪表盘数据 | `pages/dashboard.vue` | `DashboardResponse` |
| `/api/v1/dashboard/system` | GET | 获取系统统计 | `pages/dashboard.vue` | `SystemStats` |
| `/api/v1/dashboard/media` | GET | 获取媒体统计 | `pages/dashboard.vue` | `MediaStats` |
| `/api/v1/dashboard/download` | GET | 获取下载统计 | `pages/dashboard.vue` | `DownloadStats` |

**后端实现**:
- API层: `backend/app/api/dashboard.py`
- Chain层: `backend/app/chain/dashboard.py` (DashboardChain)
- 服务: `backend/app/modules/dashboard/service.py`

---

### 6. 工作流模块 (`/api/v1/workflows`)

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/api/v1/workflows` | GET | 获取工作流列表 | `pages/workflow.vue` | `List[WorkflowResponse]` |
| `/api/v1/workflows` | POST | 创建工作流 | `pages/workflow.vue` | `WorkflowResponse` |
| `/api/v1/workflows/{id}` | GET | 获取工作流详情 | `pages/workflow.vue` | `WorkflowResponse` |
| `/api/v1/workflows/{id}` | PUT | 更新工作流 | `pages/workflow.vue` | `WorkflowResponse` |
| `/api/v1/workflows/{id}` | DELETE | 删除工作流 | `pages/workflow.vue` | `SuccessResponse` |
| `/api/v1/workflows/{id}/execute` | POST | 执行工作流 | `pages/workflow.vue` | `WorkflowExecutionResponse` |
| `/api/v1/workflows/{id}/history` | GET | 获取执行历史 | `pages/workflow.vue` | `List[WorkflowExecution]` |

**后端实现**:
- API层: `backend/app/api/workflow.py`
- Chain层: `backend/app/chain/workflow.py` (WorkflowChain)
- 服务: `backend/app/modules/workflow/service.py`

---

### 7. 站点管理模块 (`/api/v1/sites`)

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/api/v1/sites` | GET | 获取站点列表 | `pages/site.vue` | `List[SiteResponse]` |
| `/api/v1/sites` | POST | 创建站点 | `pages/site.vue` | `SiteResponse` |
| `/api/v1/sites/{id}` | GET | 获取站点详情 | `pages/site.vue` | `SiteResponse` |
| `/api/v1/sites/{id}` | PUT | 更新站点 | `pages/site.vue` | `SiteResponse` |
| `/api/v1/sites/{id}` | DELETE | 删除站点 | `pages/site.vue` | `SuccessResponse` |
| `/api/v1/sites/{id}/checkin` | POST | 站点签到 | `pages/site.vue` | `CheckInResponse` |
| `/api/v1/sites/{id}/test` | POST | 测试站点连接 | `pages/site.vue` | `TestResponse` |
| `/api/v1/sites/cookiecloud/sync` | POST | CookieCloud同步 | `pages/site.vue` | `SyncResponse` |

**后端实现**:
- API层: `backend/app/api/site.py`
- Chain层: `backend/app/chain/site.py` (SiteChain)
- 服务: `backend/app/modules/site/service.py`

---

### 8. 通知模块 (`/api/v1/notifications`)

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/api/v1/notifications` | GET | 获取通知列表 | 所有页面（通知栏） | `List[NotificationResponse]` |
| `/api/v1/notifications/{id}/read` | POST | 标记为已读 | 所有页面 | `SuccessResponse` |
| `/api/v1/notifications/read-all` | POST | 标记全部为已读 | 所有页面 | `SuccessResponse` |
| `/api/v1/notifications/unread-count` | GET | 获取未读数量 | 所有页面 | `UnreadCountResponse` |

**后端实现**:
- API层: `backend/app/api/notification.py`
- 服务: `backend/app/modules/notification/service.py`
- 模型: `backend/app/models/notification.py`

---

### 9. 日历模块 (`/api/v1/calendar`)

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/api/v1/calendar` | GET | 获取日历数据 | `pages/calendar.vue` | `CalendarResponse` |
| `/api/v1/calendar/events` | GET | 获取事件列表 | `pages/calendar.vue` | `List[CalendarEvent]` |
| `/api/v1/calendar/ical` | GET | 导出iCalendar | `pages/calendar.vue` | `text/calendar` |

**后端实现**:
- API层: `backend/app/api/calendar.py`
- 服务: `backend/app/modules/calendar/service.py`

---

### 10. 音乐模块 (`/api/v1/music`) - VabHub特色功能

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/api/v1/music/search` | POST | 搜索音乐 | `pages/music.vue` | `MusicSearchResponse` |
| `/api/v1/music/charts` | GET | 获取榜单 | `pages/music.vue` | `List[ChartResponse]` |
| `/api/v1/music/subscriptions` | GET | 获取音乐订阅 | `pages/music.vue` | `List[MusicSubscriptionResponse]` |
| `/api/v1/music/subscriptions` | POST | 创建音乐订阅 | `pages/music.vue` | `MusicSubscriptionResponse` |
| `/api/v1/music/library/stats` | GET | 获取音乐库统计 | `pages/music.vue` | `MusicLibraryStats` |

**后端实现**:
- API层: `backend/app/api/music.py`
- Chain层: `backend/app/chain/music.py` (MusicChain)
- 服务: `backend/app/modules/music/service.py`

---

### 11. 媒体模块 (`/api/v1/media`)

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/api/v1/media/search` | POST | 搜索媒体 | `pages/discover.vue` | `MediaSearchResponse` |
| `/api/v1/media/{id}` | GET | 获取媒体详情 | `pages/media.vue` | `MediaDetailResponse` |
| `/api/v1/media/{id}/recommendations` | GET | 获取推荐 | `pages/media.vue` | `List[MediaResponse]` |

**后端实现**:
- API层: `backend/app/api/media.py`
- 服务: `backend/app/modules/media/service.py`

---

### 12. 系统设置模块 (`/api/v1/settings`)

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/api/v1/settings` | GET | 获取系统设置 | `pages/setting.vue` | `SettingsResponse` |
| `/api/v1/settings` | PUT | 更新系统设置 | `pages/setting.vue` | `SettingsResponse` |
| `/api/v1/settings/{key}` | GET | 获取单个设置 | `pages/setting.vue` | `SettingResponse` |
| `/api/v1/settings/{key}` | PUT | 更新单个设置 | `pages/setting.vue` | `SettingResponse` |

**后端实现**:
- API层: `backend/app/api/settings.py`
- 服务: `backend/app/modules/settings/service.py`

---

### 13. HNR检测模块 (`/api/v1/hnr`)

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/api/v1/hnr/detect` | POST | 检测HNR | `pages/hnr.vue` | `HNRDetectionResponse` |
| `/api/v1/hnr/signatures` | GET | 获取签名列表 | `pages/hnr.vue` | `List[HNRSignature]` |
| `/api/v1/hnr/signatures` | POST | 上传签名 | `pages/hnr.vue` | `HNRSignatureResponse` |

**后端实现**:
- API层: `backend/app/api/hnr.py`
- 服务: `backend/app/modules/hnr/service.py`

---

### 14. 榜单模块 (`/api/v1/charts`)

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/api/v1/charts/music` | GET | 获取音乐榜单 | `pages/charts.vue` | `List[MusicChartResponse]` |
| `/api/v1/charts/movie` | GET | 获取电影榜单 | `pages/charts.vue` | `List[MovieChartResponse]` |
| `/api/v1/charts/tv` | GET | 获取电视剧榜单 | `pages/charts.vue` | `List[TVChartResponse]` |

**后端实现**:
- API层: `backend/app/api/charts.py`
- 服务: `backend/app/modules/charts/service.py`

---

### 15. 推荐模块 (`/api/v1/recommendations`)

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/api/v1/recommendations` | GET | 获取推荐 | `pages/recommend.vue` | `List[RecommendationResponse]` |
| `/api/v1/recommendations/popular` | GET | 获取热门推荐 | `pages/recommend.vue` | `List[RecommendationResponse]` |
| `/api/v1/recommendations/personalized` | GET | 获取个性化推荐 | `pages/recommend.vue` | `List[RecommendationResponse]` |
| `/api/v1/recommendations/settings` | GET | 获取推荐设置 | `pages/recommend.vue` | `RecommendationSettingsResponse` |
| `/api/v1/recommendations/settings` | PUT | 更新推荐设置 | `pages/recommend.vue` | `RecommendationSettingsResponse` |

**后端实现**:
- API层: `backend/app/api/recommendation.py`
- 服务: `backend/app/modules/recommendation/service.py`

---

### 16. 媒体识别模块 (`/api/v1/media-identification`)

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/api/v1/media-identification/identify` | POST | 识别媒体 | `pages/media-identification.vue` | `IdentificationResponse` |
| `/api/v1/media-identification/history` | GET | 获取识别历史 | `pages/media-identification.vue` | `List[IdentificationHistory]` |

**后端实现**:
- API层: `backend/app/api/media_identification.py`
- 服务: `backend/app/modules/media_identification/service.py`

---

### 17. 健康检查模块 (`/api/v1/health`)

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/api/v1/health` | GET | 获取健康状态 | 系统监控 | `HealthResponse` |
| `/api/v1/health/{check_name}` | GET | 获取单项健康检查 | 系统监控 | `HealthCheckResponse` |

**后端实现**:
- API层: `backend/app/api/health.py`
- 服务: `backend/app/core/health.py`

---

### 18. 定时任务模块 (`/api/v1/scheduler`)

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/api/v1/scheduler/jobs` | GET | 获取任务列表 | `pages/scheduler.vue` | `List[JobResponse]` |
| `/api/v1/scheduler/jobs/{id}` | GET | 获取任务详情 | `pages/scheduler.vue` | `JobResponse` |
| `/api/v1/scheduler/jobs/{id}/run` | POST | 手动执行任务 | `pages/scheduler.vue` | `JobExecutionResponse` |

**后端实现**:
- API层: `backend/app/api/scheduler.py`
- 服务: `backend/app/core/scheduler.py`

---

### 19. 云存储模块 (`/api/v1/cloud-storage`)

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/api/v1/cloud-storage` | GET | 获取云存储列表 | `pages/cloud-storage.vue` | `List[CloudStorageResponse]` |
| `/api/v1/cloud-storage` | POST | 创建云存储配置 | `pages/cloud-storage.vue` | `CloudStorageResponse` |
| `/api/v1/cloud-storage/{id}` | GET | 获取云存储详情 | `pages/cloud-storage.vue` | `CloudStorageResponse` |
| `/api/v1/cloud-storage/{id}` | PUT | 更新云存储配置 | `pages/cloud-storage.vue` | `CloudStorageResponse` |
| `/api/v1/cloud-storage/{id}` | DELETE | 删除云存储配置 | `pages/cloud-storage.vue` | `SuccessResponse` |
| `/api/v1/cloud-storage/{id}/qr-code` | GET | 生成二维码 | `pages/cloud-storage.vue` | `QRCodeResponse` |
| `/api/v1/cloud-storage/{id}/qr-status` | GET | 检查二维码状态 | `pages/cloud-storage.vue` | `QRStatusResponse` |
| `/api/v1/cloud-storage/{id}/files` | GET | 获取文件列表 | `pages/cloud-storage.vue` | `List[CloudFileInfo]` |
| `/api/v1/cloud-storage/{id}/usage` | GET | 获取存储使用情况 | `pages/cloud-storage.vue` | `CloudStorageUsage` |

**后端实现**:
- API层: `backend/app/api/cloud_storage.py`
- Chain层: `backend/app/chain/storage.py` (StorageChain)
- 服务: `backend/app/modules/cloud_storage/service.py`
- Provider: `backend/app/core/cloud_storage/providers/`

---

### 20. Chain模式API (`/api/v1/chain`)

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/api/v1/chain/storage/*` | * | 存储Chain操作 | 各种页面 | 根据操作类型 |
| `/api/v1/chain/search/*` | * | 搜索Chain操作 | 各种页面 | 根据操作类型 |
| `/api/v1/chain/site/*` | * | 站点Chain操作 | 各种页面 | 根据操作类型 |

**后端实现**:
- API层: `backend/app/api/cloud_storage_chain.py`, `backend/app/api/search_chain.py`, `backend/app/api/site_chain.py`
- Chain层: `backend/app/chain/`

---

### 21. WebSocket (`/ws`)

| 端点 | 方法 | 功能 | 前端页面 | 响应模型 |
|------|------|------|----------|---------|
| `/ws` | WebSocket | WebSocket连接 | 所有页面 | 实时消息 |

**后端实现**:
- API层: `backend/app/api/websocket.py`
- 服务: `backend/app/modules/websocket/service.py`

---

## 📝 统一响应格式

### 成功响应
```json
{
  "success": true,
  "message": "success",
  "data": {...},
  "timestamp": "2025-01-XXTXX:XX:XX"
}
```

### 错误响应
```json
{
  "success": false,
  "error_code": "ERROR_CODE",
  "error_message": "Error message",
  "details": {...},
  "timestamp": "2025-01-XXTXX:XX:XX"
}
```

### 分页响应
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

## 🔒 认证

### 认证方式
- **JWT Token**: Bearer Token认证
- **Token获取**: `/api/v1/auth/login`
- **Token刷新**: 自动刷新（如果实现）

### 使用方式
```http
Authorization: Bearer <token>
```

## 📊 数据模型

### 统一数据模型
- **BaseResponse**: 基础响应模型
- **ErrorResponse**: 错误响应模型
- **PaginatedResponse**: 分页响应模型
- **SuccessResponse**: 成功响应模型

### 异常处理
- **VabHubException**: 基础异常类
- **NotFoundError**: 资源未找到
- **ValidationError**: 验证错误
- **UnauthorizedError**: 未授权
- **ForbiddenError**: 禁止访问
- **ConflictError**: 资源冲突
- **InternalServerError**: 内部服务器错误

## 🚀 使用示例

### 前端调用示例
```javascript
// 使用axios
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Authorization': `Bearer ${token}`
  }
})

// 获取订阅列表
const subscriptions = await api.get('/subscriptions')

// 创建订阅
const newSubscription = await api.post('/subscriptions', {
  title: 'Test',
  media_type: 'movie'
})
```

### 后端使用示例
```python
from app.core.exceptions import NotFoundError
from app.core.schemas import BaseResponse, SuccessResponse

@router.get("/{id}")
async def get_subscription(id: int):
    subscription = await service.get_subscription(id)
    if not subscription:
        raise NotFoundError("Subscription", str(id))
    return BaseResponse(data=subscription)
```

## 📚 相关文档

- **API文档**: `/docs` (Swagger UI)
- **ReDoc**: `/redoc`
- **实施计划**: `阶段4-前后端关联优化实施计划.md`

---

**最后更新**: 2025-01-XX  
**版本**: 1.0.0

