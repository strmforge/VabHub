# Phase EXT-2 完成报告：外部索引引擎模块实现

## 概述

Phase EXT-2 完成了外部索引引擎模块 `external_indexer_engine` 的实现，作为 External Indexer Bridge 的默认 HTTP 实现之一。该模块通过 HTTP 调用外部 PT 索引服务，提供统一的搜索、RSS、详情、下载链接接口。

## 新增文件

### 核心模块（`external_indexer_engine/`）

1. **`__init__.py`**
   - 包初始化文件，定义版本号

2. **`config.py`**
   - `EngineSettings`：Pydantic 配置类
   - `get_engine_settings()`：带缓存的配置获取函数
   - 从环境变量读取：`EXTERNAL_INDEXER_ENGINE_BASE_URL`、`EXTERNAL_INDEXER_ENGINE_HTTP_TIMEOUT`、`EXTERNAL_INDEXER_ENGINE_API_KEY`

3. **`models.py`**
   - `RemoteTorrentItem`：远程服务返回的种子项模型
   - `RemoteTorrentDetail`：远程服务返回的种子详情模型
   - 用于解析和验证远程服务返回的 JSON 数据

4. **`client.py`**
   - `ExternalIndexerHttpClient`：HTTP 客户端封装类
   - `get_http_client()`：HTTP 客户端单例工厂
   - 实现 4 个 HTTP 请求方法：`search_torrents`、`fetch_rss`、`get_detail`、`get_download_link`
   - 使用 `httpx.AsyncClient` 进行异步 HTTP 请求
   - 支持 API 密钥认证（通过 `X-API-Key` Header）

5. **`core.py`**
   - 导出 4 个异步函数，符合 External Indexer Bridge 的接口约定：
     - `search_torrents(site_id, keyword, media_type, categories, page) -> list[dict]`
     - `fetch_rss(site_id, limit) -> list[dict]`
     - `get_detail(site_id, torrent_id) -> dict | None`
     - `get_download_link(site_id, torrent_id) -> str | None`
   - 所有函数都捕获异常，返回安全值，不会抛出异常

6. **`README_EXT_ENGINE.md`**
   - 完整的使用文档
   - 环境变量配置说明
   - 外部 PT 索引服务 API 规范
   - 使用示例和故障排查

## 核心功能

### 1. 配置管理

- 从环境变量读取配置
- 使用 `@lru_cache` 缓存配置，避免重复读取
- 支持配置热重载（通过 `clear_settings_cache()`）

### 2. HTTP 客户端

- 使用 `httpx.AsyncClient` 进行异步 HTTP 请求
- 支持超时控制
- 支持 API 密钥认证
- 懒加载单例模式，避免重复创建客户端

### 3. 数据模型

- 使用 Pydantic 模型验证远程服务返回的数据
- 自动处理类型转换和验证
- 支持额外字段（通过 `extra` 字段）

### 4. 核心函数

#### `search_torrents`

- 调用远程服务的 `/api/ext-index/search` 端点
- 将 `RemoteTorrentItem` 转换为字典，字段对齐 `ExternalTorrentResult`
- 如果 `base_url` 未配置，直接返回空列表
- 捕获所有异常，返回空列表

#### `fetch_rss`

- 调用远程服务的 `/api/ext-index/rss` 端点
- 与 `search_torrents` 相同的转换逻辑
- 如果 `base_url` 未配置，直接返回空列表
- 捕获所有异常，返回空列表

#### `get_detail`

- 调用远程服务的 `/api/ext-index/detail` 端点
- 将 `RemoteTorrentDetail` 转换为字典，字段对齐 `ExternalTorrentDetail`
- 如果 `base_url` 未配置或种子不存在，返回 `None`
- 捕获所有异常，返回 `None`

#### `get_download_link`

- 调用远程服务的 `/api/ext-index/download` 端点
- 提取下载链接字符串（支持字典和字符串格式）
- 如果 `base_url` 未配置或链接不存在，返回 `None`
- 捕获所有异常，返回 `None`

## 与 External Indexer Bridge 的集成

### 配置方式

在环境变量中设置：

```bash
EXTERNAL_INDEXER_ENABLED=true
EXTERNAL_INDEXER_MODULE=external_indexer_engine.core
EXTERNAL_INDEXER_ENGINE_BASE_URL=http://127.0.0.1:9000
```

### 加载流程

1. VabHub 启动时，`DynamicModuleRuntime` 会尝试加载 `external_indexer_engine.core` 模块
2. 如果加载成功，`core.py` 中的 4 个函数会被注册到运行时
3. 当 `IndexedSearchService` 需要补充外部索引结果时，会调用这些函数
4. 函数内部通过 HTTP 客户端访问远程服务，获取结果并返回

### 降级策略

- **base_url 未配置**：所有函数直接返回空值，不尝试连接
- **网络错误**：记录警告日志，返回空值
- **HTTP 错误**：记录警告日志，返回空值
- **JSON 解析错误**：记录警告日志，返回空值
- **服务不可用**：不影响 VabHub 主流程，搜索功能继续使用本地索引

## 外部 PT 索引服务 API 规范

### 端点列表

1. **搜索种子**: `GET /api/ext-index/search`
   - 查询参数：`site_id`, `q`, `page`, `media_type`, `categories`
   - 返回：种子项列表或包含 `results` 字段的字典

2. **获取 RSS**: `GET /api/ext-index/rss`
   - 查询参数：`site_id`, `limit`
   - 返回：种子项列表或包含 `results` 字段的字典

3. **获取详情**: `GET /api/ext-index/detail`
   - 查询参数：`site_id`, `torrent_id`
   - 返回：种子详情字典
   - 状态码：200（成功）、404（不存在）

4. **获取下载链接**: `GET /api/ext-index/download`
   - 查询参数：`site_id`, `torrent_id`
   - 返回：下载链接字典或字符串
   - 状态码：200（成功）、404（不存在）

### 认证

如果设置了 `EXTERNAL_INDEXER_ENGINE_API_KEY`，所有请求会在 Header 中携带：

```
X-API-Key: your_api_key_here
```

## 自检结果

### 导入测试

```bash
cd VabHub
python -c "import external_indexer_engine.core; print('Import successful')"
```

**结果**: ✅ 导入成功

### 函数调用测试

```bash
cd VabHub
python -c "import asyncio; import external_indexer_engine.core as engine; result = asyncio.run(engine.search_torrents('test-site', 'test', None, None, 1)); print(f'Result: {result} (type: {type(result)})')"
```

**结果**: ✅ 函数正常执行，返回空列表（因为 base_url 未配置）

### 系统启动测试

在 `EXTERNAL_INDEXER_ENABLED=true` 且 `EXTERNAL_INDEXER_MODULE=external_indexer_engine.core`、但 `EXTERNAL_INDEXER_ENGINE_BASE_URL` 未设置时：

**结果**: ✅ 系统正常启动，外部索引部分返回空值，不影响主流程

## 字段映射

### RemoteTorrentItem → ExternalTorrentResult

| RemoteTorrentItem | ExternalTorrentResult | 说明 |
|------------------|----------------------|------|
| site_id | site_id | 站点 ID |
| torrent_id | torrent_id | 种子 ID |
| title | title | 标题 |
| size_bytes | size_bytes | 大小（字节） |
| seeders | seeders | 做种数 |
| leechers | leechers | 下载数 |
| published_at | published_at | 发布时间 |
| categories | categories | 分类列表 |
| tags | tags | 标签列表 |
| is_hr | is_hr | HR 标记 |
| free_percent | free_percent | 免费百分比 |
| extra + 其他字段 | raw | 原始数据 |

### RemoteTorrentDetail → ExternalTorrentDetail

| RemoteTorrentDetail | ExternalTorrentDetail | 说明 |
|---------------------|----------------------|------|
| site_id | site_id | 站点 ID |
| torrent_id | torrent_id | 种子 ID |
| title | title | 标题 |
| description_html | description_html | 描述（HTML） |
| screenshots | screenshots | 截图列表 |
| media_info | media_info | 媒体信息 |
| tags | tags | 标签列表 |
| extra + 其他字段 | raw | 原始数据 |

## 使用示例

### 1. 环境变量配置

```bash
export EXTERNAL_INDEXER_ENABLED=true
export EXTERNAL_INDEXER_MODULE=external_indexer_engine.core
export EXTERNAL_INDEXER_ENGINE_BASE_URL=http://127.0.0.1:9000
export EXTERNAL_INDEXER_ENGINE_HTTP_TIMEOUT=15
export EXTERNAL_INDEXER_ENGINE_API_KEY=your_api_key_here
```

### 2. 启动 VabHub

外部索引引擎会在启动时自动加载，如果配置正确，会在日志中看到：

```
外部索引桥接已初始化: external_indexer_engine.core
```

### 3. 搜索功能

当执行搜索时，如果本地索引结果不足，会自动调用外部索引引擎补充结果。

### 4. 调试 API

可以使用调试 API 测试外部索引功能：

```bash
# 检查状态
curl http://localhost:8092/api/debug/ext-indexer/status

# 测试搜索
curl "http://localhost:8092/api/debug/ext-indexer/search?site=test-site&q=test&page=1"
```

## 注意事项

1. **base_url 未配置**：如果 `EXTERNAL_INDEXER_ENGINE_BASE_URL` 未设置，所有函数会直接返回空值，不会尝试连接，这是预期的降级行为

2. **服务不可用**：如果外部服务不可用，函数会记录警告并返回空值，不会影响 VabHub 主流程

3. **超时控制**：所有请求都有超时限制（默认 15 秒），避免长时间阻塞

4. **API 兼容性**：外部服务需要严格按照 API 规范实现，否则可能无法正常工作

5. **异常处理**：所有函数都捕获异常并返回安全值，确保不会抛出异常给上层

## 后续工作

1. **实现外部 PT 索引服务**：按照 API 规范实现实际的外部索引服务
2. **性能优化**：添加结果缓存、连接池优化等
3. **监控和日志**：添加更详细的监控指标和日志记录
4. **错误重试**：添加自动重试机制，提高可靠性
5. **批量请求**：支持批量查询，提高效率

## 总结

Phase EXT-2 成功实现了外部索引引擎模块 `external_indexer_engine`，为 VabHub 提供了通过 HTTP 调用外部 PT 索引服务的能力。所有功能都经过精心设计，确保优雅降级、配置驱动、接口清晰，为后续的实际服务集成工作奠定了坚实基础。

