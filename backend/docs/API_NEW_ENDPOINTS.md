# 新实现的API端点文档

本文档描述了最新实现的API端点，包括下载器管理、网关签名、插件管理、规则集管理、刮削器管理和密钥管理等功能。

## 目录

- [下载器管理](#下载器管理)
- [网关签名](#网关签名)
- [插件管理](#插件管理)
- [规则集管理](#规则集管理)
- [刮削器管理](#刮削器管理)
- [密钥管理](#密钥管理)
- [参数名兼容性](#参数名兼容性)

## 下载器管理

### 获取下载器实例列表

**端点**: `GET /api/dl/instances`

**描述**: 获取所有已配置的下载器实例列表

**响应示例**:
```json
{
  "success": true,
  "message": "获取成功",
  "data": [
    {
      "id": "qbittorrent-1",
      "name": "qBittorrent主实例",
      "type": "qBittorrent",
      "host": "localhost",
      "port": 8080,
      "enabled": true
    }
  ],
  "timestamp": "2025-01-XX..."
}
```

### 获取下载器统计信息

**端点**: `GET /api/dl/{did}/stats`

**参数**:
- `did` (路径参数): 下载器实例ID

**描述**: 获取指定下载器实例的统计信息（下载速度、上传速度、活动任务数等）

**响应示例**:
```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "download_speed": 10.5,
    "upload_speed": 2.3,
    "active_tasks": 5,
    "total_tasks": 20
  },
  "timestamp": "2025-01-XX..."
}
```

### 测试下载器连接

**端点**: `POST /api/dl/{did}/test`

**参数**:
- `did` (路径参数): 下载器实例ID

**描述**: 测试指定下载器实例的连接状态

**响应示例**:
```json
{
  "success": true,
  "message": "连接成功",
  "data": {
    "connected": true,
    "response_time_ms": 50
  },
  "timestamp": "2025-01-XX..."
}
```

## 网关签名

### HMAC签名

**端点**: `POST /api/gateway/sign`

**描述**: 对URL路径进行HMAC签名，用于STRM文件重定向等场景

**请求体**:
```json
{
  "path": "/strm/stream/115/test-token",
  "method": "GET"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "签名成功",
  "data": {
    "signature": "abc123...",
    "expires_at": "2025-01-XX..."
  },
  "timestamp": "2025-01-XX..."
}
```

## 插件管理

### 获取插件注册表

**端点**: `GET /api/plugins/registry`

**描述**: 获取可用的插件注册表

**响应示例**:
```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "plugins": [
      {
        "id": "example-plugin",
        "name": "示例插件",
        "version": "1.0.0",
        "description": "这是一个示例插件"
      }
    ]
  },
  "timestamp": "2025-01-XX..."
}
```

### 安装插件

**端点**: `POST /api/plugins/{pid}/install`

**参数**:
- `pid` (路径参数): 插件ID

**描述**: 安装指定的插件

**响应示例**:
```json
{
  "success": true,
  "message": "安装成功",
  "data": null,
  "timestamp": "2025-01-XX..."
}
```

## 规则集管理

### 获取规则集配置

**端点**: `GET /api/ruleset`

**描述**: 获取订阅规则集配置

**响应示例**:
```json
{
  "success": true,
  "message": "获取规则集配置成功",
  "data": {
    "rules": {
      "default": {
        "quality": "1080p",
        "resolution": "1920x1080",
        "min_seeders": 5,
        "sites": [],
        "include": [],
        "exclude": []
      }
    }
  },
  "timestamp": "2025-01-XX..."
}
```

### 更新规则集配置

**端点**: `PUT /api/ruleset`

**请求体**:
```json
{
  "rules": {
    "default": {
      "quality": "4K",
      "min_seeders": 10
    }
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "更新规则集配置成功",
  "data": null,
  "timestamp": "2025-01-XX..."
}
```

## 刮削器管理

### 获取刮削器配置

**端点**: `GET /api/scraper/config`

**描述**: 获取所有刮削器的配置信息

**响应示例**:
```json
{
  "success": true,
  "message": "获取刮削器配置成功",
  "data": {
    "tmdb_enabled": true,
    "douban_enabled": true,
    "tvdb_enabled": true,
    "fanart_enabled": true,
    "musicbrainz_enabled": true,
    "acoustid_enabled": true,
    "cache_enabled": true,
    "cache_ttl": 3600
  },
  "timestamp": "2025-01-XX..."
}
```

### 更新刮削器配置

**端点**: `PUT /api/scraper/config`

**请求体**:
```json
{
  "tmdb_enabled": true,
  "cache_enabled": true,
  "cache_ttl": 7200
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "更新刮削器配置成功",
  "data": null,
  "timestamp": "2025-01-XX..."
}
```

### 测试刮削器连接

**端点**: `POST /api/scraper/test`

**查询参数**:
- `scraper_type` (必需): 刮削器类型 (`tmdb`, `douban`, `tvdb`, `fanart`, `musicbrainz`, `acoustid`)
- `test_query` (可选): 测试查询字符串

**描述**: 测试指定刮削器的连接状态

**响应示例**:
```json
{
  "success": true,
  "message": "刮削器测试成功",
  "data": {
    "scraper_type": "tmdb",
    "connected": true,
    "response_time_ms": 150
  },
  "timestamp": "2025-01-XX..."
}
```

## 密钥管理

### 获取密钥状态

**端点**: `GET /api/secrets/status`

**描述**: 获取系统密钥的配置状态

**响应示例**:
```json
{
  "success": true,
  "message": "获取密钥状态成功",
  "data": {
    "secret_manager_enabled": true,
    "api_key_manager_enabled": true,
    "secrets_file_exists": true,
    "api_keys_encrypted": true,
    "tmdb_api_key_configured": true,
    "tvdb_api_key_configured": true,
    "fanart_api_key_configured": true,
    "douban_api_key_configured": false,
    "api_token_configured": true
  },
  "timestamp": "2025-01-XX..."
}
```

## 参数名兼容性

FastAPI的路由参数名不影响URL匹配，因此以下端点可以互相兼容：

### 下载管理端点

- `/api/downloads/{task_id}` 和 `/api/downloads/{download_id}` 都能正常工作
- `/api/downloads/{task_id}/pause` 和 `/api/downloads/{download_id}/pause` 都能正常工作
- `/api/downloads/{task_id}/resume` 和 `/api/downloads/{download_id}/resume` 都能正常工作

### 订阅管理端点

- `/api/subscriptions/{subscription_id}` 和 `/api/subscriptions/{sid}` 都能正常工作

### 任务管理端点

- `/api/tasks/{task_id}` 和 `/api/tasks/{tid}` 都能正常工作
- `/api/tasks/{task_id}/retry` 和 `/api/tasks/{tid}/retry` 都能正常工作

**注意**: 虽然URL参数名可以不同，但建议使用后端实际定义的参数名（如 `task_id`、`subscription_id`）以确保代码一致性。

## 统一响应格式

所有端点都遵循统一的响应格式：

**成功响应**:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {...},
  "timestamp": "2025-01-XX..."
}
```

**错误响应**:
```json
{
  "success": false,
  "error_code": "ERROR_CODE",
  "error_message": "错误描述",
  "details": {...},
  "timestamp": "2025-01-XX..."
}
```

## WebSocket端点

### WebSocket连接

**端点**: `WS /api/ws/ws`

**描述**: WebSocket实时更新端点，支持订阅多个主题

**支持的主题**:
- `dashboard`: 仪表盘数据更新
- `downloads`: 下载任务更新
- `system`: 系统资源更新

**消息格式**:
```json
{
  "type": "subscribe",
  "topics": ["dashboard", "downloads"]
}
```

**响应格式**:
```json
{
  "type": "subscribed",
  "topics": ["dashboard", "downloads"],
  "timestamp": "2025-01-XX..."
}
```

## 前端使用示例

### TypeScript/Vue示例

```typescript
import { downloaderApi, gatewayApi, pluginsApi, rulesetApi, scraperApi, secretsApi } from '@/services/api'

// 获取下载器实例列表
const instances = await downloaderApi.getInstances()

// 获取下载器统计信息
const stats = await downloaderApi.getStats('qbittorrent-1')

// 测试下载器连接
const testResult = await downloaderApi.testConnection('qbittorrent-1')

// 网关签名
const signature = await gatewayApi.sign({
  path: '/strm/stream/115/test-token',
  method: 'GET'
})

// 获取插件注册表
const registry = await pluginsApi.getRegistry()

// 安装插件
await pluginsApi.installPlugin('example-plugin')

// 获取规则集配置
const ruleset = await rulesetApi.getRuleset()

// 更新规则集配置
await rulesetApi.updateRuleset({
  rules: {
    default: {
      quality: '4K',
      min_seeders: 10
    }
  }
})

// 获取刮削器配置
const scraperConfig = await scraperApi.getConfig()

// 更新刮削器配置
await scraperApi.updateConfig({
  tmdb_enabled: true,
  cache_enabled: true
})

// 测试刮削器
const testResult = await scraperApi.testScraper('tmdb', 'The Matrix')

// 获取密钥状态
const secretsStatus = await secretsApi.getStatus()
```

## 错误处理

所有端点都使用统一的错误响应格式。前端应该检查 `success` 字段来判断请求是否成功：

```typescript
try {
  const response = await downloaderApi.getInstances()
  // response.data 包含实际数据
} catch (error: any) {
  if (error.errorCode) {
    console.error(`错误代码: ${error.errorCode}`)
    console.error(`错误消息: ${error.message}`)
  }
}
```

## 认证

所有端点都需要认证（除了健康检查等公开端点）。请求头中需要包含：

```
Authorization: Bearer <token>
```

如果认证失败（401），前端应该自动跳转到登录页面。

