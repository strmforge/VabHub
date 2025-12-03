# 外部索引引擎模块

## 概述

`external_indexer_engine` 是 External Indexer Bridge 的一个 HTTP 引擎实现，通过 HTTP 调用外部 PT 索引服务提供搜索能力。

## 作用

- 作为 External Indexer Bridge 的默认实现之一
- 通过 HTTP 协议与外部 PT 索引服务通信
- 提供统一的搜索、RSS、详情、下载链接接口
- 优雅处理网络错误和配置缺失，不影响主流程

## 环境变量配置

### 必需配置

```bash
# 设置 External Indexer Bridge 使用此模块
EXTERNAL_INDEXER_MODULE=external_indexer_engine.core

# 外部索引服务的基础 URL
EXTERNAL_INDEXER_ENGINE_BASE_URL=http://127.0.0.1:9000
```

### 可选配置

```bash
# HTTP 请求超时时间（秒），默认 15
EXTERNAL_INDEXER_ENGINE_HTTP_TIMEOUT=15

# API 密钥（如果设置，会作为 X-API-Key Header 发送）
EXTERNAL_INDEXER_ENGINE_API_KEY=your_api_key_here
```

## 外部 PT 索引服务 API 规范

外部 PT 索引服务需要暴露以下 HTTP API 端点：

### 1. 搜索种子

**端点**: `GET /api/ext-index/search`

**查询参数**:
- `site_id` (必需): 站点 ID
- `q` (必需): 搜索关键词
- `page` (可选): 页码，默认 1
- `media_type` (可选): 媒体类型（如 "movie" / "tv"）
- `categories` (可选): 分类列表，逗号分隔（如 "movie,tv"）

**响应格式**:
```json
[
  {
    "site_id": "example_site",
    "torrent_id": "12345",
    "title": "Example Torrent",
    "size_bytes": 1073741824,
    "seeders": 10,
    "leechers": 2,
    "published_at": "2024-01-01T00:00:00Z",
    "categories": ["movie"],
    "tags": ["4K", "BluRay"],
    "is_hr": false,
    "free_percent": 100,
    "extra": {}
  }
]
```

或者返回包含 `results` 字段的字典：
```json
{
  "results": [...],
  "total": 100,
  "page": 1
}
```

### 2. 获取 RSS 种子列表

**端点**: `GET /api/ext-index/rss`

**查询参数**:
- `site_id` (必需): 站点 ID
- `limit` (可选): 返回数量限制，默认 100

**响应格式**: 与搜索接口相同

### 3. 获取种子详细信息

**端点**: `GET /api/ext-index/detail`

**查询参数**:
- `site_id` (必需): 站点 ID
- `torrent_id` (必需): 种子 ID

**响应格式**:
```json
{
  "site_id": "example_site",
  "torrent_id": "12345",
  "title": "Example Torrent",
  "description_html": "<p>Description</p>",
  "screenshots": ["https://example.com/screenshot1.jpg"],
  "media_info": "Video: H.264, Audio: AAC",
  "tags": ["4K", "BluRay"],
  "extra": {}
}
```

**状态码**:
- `200`: 成功
- `404`: 种子不存在

### 4. 获取种子下载链接

**端点**: `GET /api/ext-index/download`

**查询参数**:
- `site_id` (必需): 站点 ID
- `torrent_id` (必需): 种子 ID

**响应格式**:
```json
{
  "download_url": "magnet:?xt=urn:btih:..."
}
```

或者直接返回字符串：
```
magnet:?xt=urn:btih:...
```

**状态码**:
- `200`: 成功
- `404`: 种子不存在

## 认证

如果设置了 `EXTERNAL_INDEXER_ENGINE_API_KEY`，所有请求都会在 Header 中携带：

```
X-API-Key: your_api_key_here
```

## 错误处理

- 所有网络错误、HTTP 错误、JSON 解析错误都会被捕获
- 错误会记录到日志（warning 级别）
- 函数返回安全的空值（空列表或 None），不会抛出异常

## 使用示例

### 在 VabHub 中启用

1. 设置环境变量：
   ```bash
   export EXTERNAL_INDEXER_ENABLED=true
   export EXTERNAL_INDEXER_MODULE=external_indexer_engine.core
   export EXTERNAL_INDEXER_ENGINE_BASE_URL=http://127.0.0.1:9000
   ```

2. 启动 VabHub，外部索引引擎会自动加载

3. 搜索功能会自动在结果不足时补充外部索引结果

### 直接调用（测试）

```python
import asyncio
import external_indexer_engine.core as engine

async def test():
    # 搜索
    results = await engine.search_torrents("test-site", "test", None, None, 1)
    print(f"找到 {len(results)} 条结果")
    
    # 获取 RSS
    rss_results = await engine.fetch_rss("test-site", 10)
    print(f"RSS 找到 {len(rss_results)} 条结果")
    
    # 获取详情
    detail = await engine.get_detail("test-site", "12345")
    if detail:
        print(f"详情: {detail['title']}")
    
    # 获取下载链接
    link = await engine.get_download_link("test-site", "12345")
    if link:
        print(f"下载链接: {link}")

asyncio.run(test())
```

## 注意事项

1. **base_url 未配置**: 如果 `EXTERNAL_INDEXER_ENGINE_BASE_URL` 未设置，所有函数会直接返回空值，不会尝试连接
2. **服务不可用**: 如果外部服务不可用，函数会记录警告并返回空值，不会影响 VabHub 主流程
3. **超时控制**: 所有请求都有超时限制，避免长时间阻塞
4. **API 兼容性**: 外部服务需要严格按照 API 规范实现，否则可能无法正常工作

## 故障排查

### 搜索无结果

1. 检查 `EXTERNAL_INDEXER_ENGINE_BASE_URL` 是否正确
2. 检查外部服务是否正常运行
3. 查看日志中的警告信息
4. 使用调试 API 直接测试：`GET /api/debug/ext-indexer/search?site=xxx&q=xxx`

### 连接失败

1. 检查网络连接
2. 检查防火墙设置
3. 检查外部服务的 URL 是否正确
4. 查看日志中的详细错误信息

### API 密钥认证失败

1. 检查 `EXTERNAL_INDEXER_ENGINE_API_KEY` 是否正确
2. 检查外部服务是否支持 `X-API-Key` Header
3. 查看 HTTP 响应状态码和错误信息

