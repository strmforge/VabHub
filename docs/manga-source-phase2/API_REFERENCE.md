# API 参考文档

## 概述

本文档列出 Manga Source Phase 2 新增的 API 端点。所有 API 都遵循 RESTful 设计，使用 JSON 格式进行数据交换。

## 基础信息

- **Base URL**: `http://localhost:8000/api/manga`
- **认证**: Bearer Token（如果启用）
- **Content-Type**: `application/json`

## 新增端点

### 1. 聚合搜索

**端点**: `GET /remote/aggregated-search`

**描述**: 并发搜索所有启用的漫画源，返回合并结果

**参数**:
- `q` (string, required): 搜索关键词
- `sources` (array, optional): 源ID列表，不传则搜索所有源
- `limit` (int, optional): 每个源返回的结果数量限制，默认20

**示例**:
```bash
# 基础搜索
curl "http://localhost:8000/api/manga/remote/aggregated-search?q=海贼王"

# 指定源搜索
curl "http://localhost:8000/api/manga/remote/aggregated-search?q=进击的巨人&sources=1,2"

# 限制结果数量
curl "http://localhost:8000/api/manga/remote/aggregated-search?q=火影忍者&limit=10"
```

**响应**:
```json
{
  "query": "海贼王",
  "results": {
    "1": [
      {
        "remote_id": "123",
        "title": "海贼王",
        "description": "冒险漫画",
        "cover_url": "http://example.com/cover.jpg",
        "source_id": 1,
        "source_name": "Komga"
      }
    ],
    "2": [
      {
        "remote_id": "456",
        "title": "海贼王",
        "description": "经典冒险",
        "cover_url": "http://example.com/cover2.jpg",
        "source_id": 2,
        "source_name": "OPDS"
      }
    ]
  },
  "total_results": 2
}
```

### 2. 外部URL构建

**端点**: `GET /remote/series/{source_id}/{remote_series_id}/external-url`

**描述**: 构建漫画在原站的访问URL

**参数**:
- `source_id` (int, required): 漫画源ID
- `remote_series_id` (string, required): 远程漫画ID

**示例**:
```bash
# 获取外部URL
curl "http://localhost:8000/api/manga/remote/series/1/123/external-url"
```

**响应**:
```json
{
  "external_url": "http://komga:8080/series/123",
  "source_name": "Komga"
}
```

### 3. 远程追更

**端点**: `POST /remote/follow`

**描述**: 追更远程漫画（不下载章节）

**请求体**:
```json
{
  "source_id": 1,
  "remote_series_id": "123"
}
```

**示例**:
```bash
curl -X POST "http://localhost:8000/api/manga/remote/follow" \
  -H "Content-Type: application/json" \
  -d '{"source_id": 1, "remote_series_id": "123"}'
```

**响应**:
```json
{
  "success": true,
  "message": "追更成功",
  "follow_id": 456
}
```

## 现有端点增强

### 1. 源列表

**端点**: `GET /remote/sources`

**新增字段**: 响应中包含源类型和状态信息

**响应示例**:
```json
[
  {
    "id": 1,
    "name": "我的 Komga",
    "type": "KOMGA",
    "base_url": "http://komga:8080",
    "is_enabled": true,
    "status": "connected"
  }
]
```

### 2. 漫画详情

**端点**: `GET /remote/series/{source_id}/{remote_series_id}`

**新增字段**: 响应中包含外部URL信息

**响应示例**:
```json
{
  "remote_id": "123",
  "title": "海贼王",
  "description": "冒险漫画",
  "cover_url": "http://example.com/cover.jpg",
  "chapters_count": 100,
  "last_updated": "2024-01-01T00:00:00Z",
  "external_url_available": true
}
```

## 错误处理

### 标准错误响应

```json
{
  "error": {
    "code": "SOURCE_NOT_FOUND",
    "message": "指定的漫画源不存在",
    "details": {
      "source_id": 999
    }
  }
}
```

### 常见错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|------------|------|
| `SOURCE_NOT_FOUND` | 404 | 漫画源不存在 |
| `SERIES_NOT_FOUND` | 404 | 漫画不存在 |
| `ALREADY_FOLLOWING` | 409 | 已经在追更此漫画 |
| `INVALID_SOURCE_TYPE` | 400 | 不支持的源类型 |
| `NETWORK_ERROR` | 503 | 网络连接错误 |

## 速率限制

- 搜索API: 每分钟最多60次请求
- 追更API: 每分钟最多30次请求
- 其他API: 每分钟最多100次请求

## 认证

如果启用了认证，需要在请求头中包含：

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" "http://localhost:8000/api/manga/remote/sources"
```

## 数据模型

### AggregatedSearchResult

```typescript
interface AggregatedSearchResult {
  query: string;
  results: Record<string, RemoteMangaSeries[]>;
  total_results: number;
}
```

### ExternalUrlResponse

```typescript
interface ExternalUrlResponse {
  external_url: string;
  source_name: string;
}
```

### FollowResponse

```typescript
interface FollowResponse {
  success: boolean;
  message: string;
  follow_id?: number;
}
```

## 使用示例

### 完整的搜索和追更流程

```bash
# 1. 搜索漫画
SEARCH_RESULT=$(curl -s "http://localhost:8000/api/manga/remote/aggregated-search?q=海贼王")

# 2. 解析结果获取第一个漫画的ID
SOURCE_ID=$(echo $SEARCH_RESULT | jq -r '.results."1"[0].source_id')
REMOTE_ID=$(echo $SEARCH_RESULT | jq -r '.results."1"[0].remote_id')

# 3. 追更漫画
curl -X POST "http://localhost:8000/api/manga/remote/follow" \
  -H "Content-Type: application/json" \
  -d "{\"source_id\": $SOURCE_ID, \"remote_series_id\": \"$REMOTE_ID\"}"

# 4. 获取原站链接
curl "http://localhost:8000/api/manga/remote/series/$SOURCE_ID/$REMOTE_ID/external-url"
```

更多技术细节请参考源代码中的 API 定义。
