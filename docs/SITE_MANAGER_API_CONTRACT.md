# SITE-MANAGER-1 API 契约文档

## 概述

SITE-MANAGER-1 模块提供完整的站点管理REST API，包括站点CRUD操作、健康检查、访问配置管理、导入导出等功能。

**基础路径**: `/api/sites`  
**认证**: Bearer Token  
**内容类型**: `application/json`

---

## 核心数据模型

### SiteBrief (站点简要信息)
```json
{
  "id": 1,
  "key": "hdhome",
  "domain": "hdhome.org", 
  "category": "PT",
  "icon_url": "https://example.com/icon.png",
  "priority": 1,
  "tags": "高清,PT",
  "name": "高清家园",
  "url": "https://hdhome.org",
  "enabled": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "stats": {
    "health_status": "OK",
    "last_seen_at": "2024-01-01T00:00:00Z",
    "error_count": 0
  }
}
```

### SiteDetail (站点详细信息)
```json
{
  "id": 1,
  "key": "hdhome",
  "domain": "hdhome.org",
  "category": "PT", 
  "icon_url": "https://example.com/icon.png",
  "priority": 1,
  "tags": "高清,PT",
  "name": "高清家园",
  "url": "https://hdhome.org",
  "cookie": "encrypted_cookie_string",
  "cookiecloud_uuid": "uuid-string",
  "cookiecloud_password": "password",
  "cookiecloud_server": "https://cookiecloud.example.com",
  "enabled": true,
  "user_data": {},
  "last_checkin": "2024-01-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "stats": {
    "upload_bytes": 1073741824,
    "download_bytes": 536870912,
    "ratio": 2.0,
    "health_status": "OK",
    "last_seen_at": "2024-01-01T00:00:00Z",
    "last_error_at": null,
    "error_count": 0,
    "total_requests": 100,
    "successful_requests": 95,
    "avg_response_time": 250.5
  },
  "access_config": {
    "rss_url": "https://hdhome.org/rss",
    "api_key": "api-key-string",
    "auth_header": "Authorization: Bearer token",
    "cookie": "encrypted_cookie_string",
    "user_agent": "Mozilla/5.0...",
    "use_api_mode": false,
    "use_proxy": false,
    "use_browser_emulation": false,
    "min_interval_seconds": 10,
    "max_concurrent_requests": 1,
    "timeout_seconds": 30,
    "retry_count": 3
  },
  "recent_health_checks": [
    {
      "site_id": 1,
      "status": "OK",
      "response_time_ms": 250,
      "error_message": null,
      "http_status_code": 200,
      "check_type": "basic",
      "checked_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

## API 端点

### 1. 站点管理

#### 1.1 获取站点列表
```http
GET /api/sites
```

**查询参数**:

| 参数 | 类型 | 必填 | 描述 | 示例 |
|------|------|------|------|------|
| enabled | boolean | 否 | 启用状态过滤 | true |
| category | string | 否 | 分类过滤 | PT |
| health_status | string | 否 | 健康状态过滤 | OK |
| keyword | string | 否 | 关键词搜索 | 高清 |
| tags | string[] | 否 | 标签过滤 | ["高清","PT"] |
| priority_min | integer | 否 | 最小优先级 | 1 |
| priority_max | integer | 否 | 最大优先级 | 5 |
| page | integer | 否 | 页码 | 1 |
| size | integer | 否 | 每页数量 | 20 |

**响应**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "key": "hdhome",
      "name": "高清家园",
      "enabled": true,
      "stats": {
        "health_status": "OK"
      }
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
```

#### 1.2 获取站点详情
```http
GET /api/sites/{site_id}
```

**路径参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| site_id | integer | 站点ID |

**响应**: SiteDetail 对象

#### 1.3 创建站点
```http
POST /api/sites
```

**请求体**:
```json
{
  "name": "新站点",
  "url": "https://example.com",
  "key": "new_site",
  "domain": "example.com",
  "category": "PT",
  "icon_url": "https://example.com/icon.png",
  "priority": 1,
  "tags": "新站点,测试",
  "enabled": true,
  "cookie": "cookie_string",
  "cookiecloud_uuid": "uuid",
  "cookiecloud_password": "password",
  "cookiecloud_server": "https://cookiecloud.example.com"
}
```

**响应**: 创建的 SiteDetail 对象

#### 1.4 更新站点
```http
PUT /api/sites/{site_id}
```

**路径参数**: site_id (integer)

**请求体**: SiteUpdatePayload 对象
```json
{
  "name": "更新的站点名",
  "priority": 2,
  "enabled": false
}
```

**响应**: 更新的 SiteDetail 对象

#### 1.5 删除站点
```http
DELETE /api/sites/{site_id}
```

**路径参数**: site_id (integer)

**响应**:
```json
{
  "success": true,
  "data": true
}
```

### 2. 访问配置管理

#### 2.1 更新站点访问配置
```http
PUT /api/sites/{site_id}/access-config
```

**请求体**:
```json
{
  "rss_url": "https://example.com/rss",
  "api_key": "new-api-key",
  "auth_header": "Authorization: Bearer new-token",
  "cookie": "new-encrypted-cookie",
  "user_agent": "Custom User Agent",
  "use_api_mode": true,
  "use_proxy": false,
  "use_browser_emulation": false,
  "min_interval_seconds": 15,
  "max_concurrent_requests": 2,
  "timeout_seconds": 45,
  "retry_count": 5,
  "custom_headers": "X-Custom: value"
}
```

**响应**: 更新的 SiteDetail 对象

### 3. 健康检查

#### 3.1 单站点健康检查
```http
POST /api/sites/{site_id}/health-check
```

**查询参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| check_type | string | 否 | 检查类型: basic/rss/api |

**响应**:
```json
{
  "success": true,
  "data": {
    "site_id": 1,
    "status": "OK",
    "response_time_ms": 250,
    "error_message": null,
    "http_status_code": 200,
    "check_type": "basic",
    "checked_at": "2024-01-01T00:00:00Z"
  }
}
```

#### 3.2 批量健康检查
```http
POST /api/sites/batch-health-check
```

**请求体**:
```json
{
  "site_ids": [1, 2, 3],
  "check_type": "basic"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total": 3,
    "success_count": 2,
    "failed_count": 1,
    "results": [
      {
        "site_id": 1,
        "status": "OK",
        "response_time_ms": 250
      }
    ],
    "message": "批量检查完成: 成功 2, 失败 1"
  }
}
```

### 4. 导入导出

#### 4.1 导出站点
```http
POST /api/sites/export
```

**请求体**:
```json
{
  "site_ids": [1, 2, 3]
}
```

**响应**:
```json
{
  "success": true,
  "data": [
    {
      "name": "站点1",
      "url": "https://site1.com",
      "key": "site1",
      "domain": "site1.com",
      "category": "PT",
      "enabled": true,
      "rss_url": "https://site1.com/rss",
      "use_proxy": false,
      "use_browser_emulation": false,
      "min_interval_seconds": 10,
      "max_concurrent_requests": 1
    }
  ]
}
```

#### 4.2 导入站点
```http
POST /api/sites/import
```

**请求体**:
```json
{
  "sites": [
    {
      "name": "新站点",
      "url": "https://newsite.com",
      "key": "newsite",
      "domain": "newsite.com",
      "category": "PT",
      "enabled": true,
      "rss_url": "https://newsite.com/rss"
    }
  ]
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total": 1,
    "success_count": 1,
    "failed_count": 0,
    "failed_items": [],
    "message": "导入完成: 成功 1, 失败 0"
  }
}
```

### 5. 分类和统计

#### 5.1 获取站点分类
```http
GET /api/sites/categories
```

**响应**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "key": "pt",
      "name": "PT站点",
      "description": "Private Tracker站点",
      "icon": "mdi-server",
      "sort_order": 1,
      "enabled": true
    }
  ]
}
```

#### 5.2 获取统计摘要
```http
GET /api/sites/stats
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total_sites": 10,
    "enabled_sites": 8,
    "disabled_sites": 2,
    "healthy_sites": 7,
    "warning_sites": 1,
    "error_sites": 0,
    "categories": {
      "PT": 5,
      "BT": 3,
      "小说": 2
    }
  }
}
```

---

## 错误响应格式

所有API错误都遵循统一格式：

```json
{
  "success": false,
  "error": {
    "code": "SITE_NOT_FOUND",
    "message": "站点不存在",
    "details": {
      "site_id": 999
    }
  }
}
```

### 常见错误码

| 错误码 | HTTP状态码 | 描述 |
|--------|------------|------|
| SITE_NOT_FOUND | 404 | 站点不存在 |
| VALIDATION_ERROR | 400 | 请求参数验证失败 |
| DUPLICATE_KEY | 409 | 站点key或domain重复 |
| UNAUTHORIZED | 401 | 未授权访问 |
| FORBIDDEN | 403 | 权限不足 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |

---

## 集成点说明

### CookieCloud 集成
- **触发事件**: `SITE_UPDATED`
- **集成方式**: 钩子系统自动触发CookieCloud同步
- **状态更新**: 同步结果自动更新 `SiteStats.health_status`

### External Indexer 集成
- **调用方法**: `SiteManagerService.get_active_healthy_sites()`
- **过滤条件**: `enabled=True` 且 `health_status != 'ERROR'`
- **返回数据**: 包含访问配置的站点列表

### Local Intel 集成
- **触发事件**: `SITE_HEALTH_CHANGED`
- **数据格式**: 使用 `Site.id` 替代字符串站点名称
- **同步内容**: 健康状态变化实时同步

---

## 使用示例

### JavaScript/TypeScript
```typescript
// 获取站点列表
const response = await fetch('/api/sites?enabled=true&category=PT', {
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  }
});

const result = await response.json();
const sites = result.data;
```

### Python
```python
import requests

# 创建站点
response = requests.post('/api/sites', json={
    'name': '新站点',
    'url': 'https://example.com',
    'category': 'PT'
}, headers={
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
})

site = response.json()['data']
```

---

## 版本信息

- **当前版本**: v1.0.0
- **API版本**: v1
- **最后更新**: 2024-01-01
- **兼容性**: 向后兼容，新增字段不影响现有客户端
