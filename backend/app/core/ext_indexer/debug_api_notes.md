# 外部索引桥接调试 API 说明

## 设计目标

外部索引桥接（External Indexer Bridge）是 VabHub 用于集成外部 PT 索引引擎的统一接口层。

### 核心特性

1. **动态模块加载**：通过模块路径动态加载外部索引引擎，不绑定任何特定项目
2. **优雅降级**：外部索引失败不影响主流程，只记录日志
3. **统一接口**：提供标准化的搜索、RSS、详情、下载链接接口
4. **授权桥接**：支持检查站点登录状态和风控状态

### 架构设计

```
VabHub 搜索服务
    ↓
IndexedSearchService（本地索引优先）
    ↓（结果不足时）
ExternalIndexerSearchProvider（外部索引补充）
    ↓
ExternalIndexerRuntime（动态模块运行时）
    ↓
外部索引引擎模块（用户自定义）
```

## 环境变量配置

### 启用外部索引桥接

```bash
# 启用外部索引桥接
EXTERNAL_INDEXER_ENABLED=true

# 指定外部索引模块路径（Python 模块路径，如 "external_indexer_engine.core"）
EXTERNAL_INDEXER_MODULE=external_indexer_engine.core

# 最小结果阈值（如果本地索引结果 >= 此值，不补充外部索引）
EXTERNAL_INDEXER_MIN_RESULTS=20

# 外部索引请求超时时间（秒）
EXTERNAL_INDEXER_TIMEOUT_SECONDS=15
```

## 外部模块接口约定

外部索引引擎模块需要实现以下异步函数：

### 1. search_torrents

```python
async def search_torrents(
    site_id: str,
    keyword: str,
    *,
    media_type: Optional[str] = None,
    categories: Optional[List[str]] = None,
    page: int = 1,
) -> List[Dict[str, Any]]:
    """
    搜索种子
    
    Args:
        site_id: 站点 ID
        keyword: 搜索关键词
        media_type: 媒体类型（如 "movie" / "tv"）
        categories: 分类列表
        page: 页码（从 1 开始）
        
    Returns:
        搜索结果字典列表，每个字典应包含：
        - torrent_id: 种子 ID
        - title: 种子标题
        - size_bytes: 文件大小（字节）
        - seeders: 做种数
        - leechers: 下载数
        - published_at: 发布时间（datetime 或 ISO 格式字符串）
        - is_hr: 是否 HR（Hit & Run）
        - free_percent: 免费百分比（0/30/50/100 等）
        - categories: 分类列表
        - tags: 标签列表
        - 其他自定义字段（会保存在 raw 字段中）
    """
    pass
```

### 2. fetch_rss

```python
async def fetch_rss(
    site_id: str,
    *,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    获取 RSS 种子列表
    
    Args:
        site_id: 站点 ID
        limit: 返回数量限制
        
    Returns:
        RSS 种子字典列表（格式同 search_torrents）
    """
    pass
```

### 3. get_detail

```python
async def get_detail(
    site_id: str,
    torrent_id: str,
) -> Optional[Dict[str, Any]]:
    """
    获取种子详细信息
    
    Args:
        site_id: 站点 ID
        torrent_id: 种子 ID
        
    Returns:
        种子详细信息字典，包含：
        - title: 种子标题
        - description_html: 描述（HTML）
        - screenshots: 截图 URL 列表
        - media_info: 媒体信息
        - tags: 标签列表
        - 其他自定义字段
        如果不存在则返回 None
    """
    pass
```

### 4. get_download_link

```python
async def get_download_link(
    site_id: str,
    torrent_id: str,
) -> Optional[str]:
    """
    获取种子下载链接
    
    Args:
        site_id: 站点 ID
        torrent_id: 种子 ID
        
    Returns:
        下载链接（磁力链接或种子 URL），如果获取失败则返回 None
    """
    pass
```

## 调试 API 接口

### 1. GET /api/debug/ext-indexer/sites

列出所有外部站点配置和已注册的适配器。

**响应示例**：

```json
{
  "sites": [
    {
      "site_id": "example_site",
      "name": "Example Site",
      "base_url": "https://example.com",
      "framework": "nexusphp",
      "enabled": true,
      "capabilities": ["search", "rss", "detail"]
    }
  ],
  "registered": ["example_site"]
}
```

### 2. GET /api/debug/ext-indexer/search

调试搜索接口，直接调用外部索引运行时进行搜索。

**查询参数**：

- `site` (必需): 站点 ID
- `q` (必需): 搜索关键词
- `page` (可选): 页码，默认 1

**响应示例**：

```json
{
  "site": "example_site",
  "query": "test",
  "page": 1,
  "results": [
    {
      "site_id": "example_site",
      "torrent_id": "12345",
      "title": "Test Torrent",
      "size_bytes": 1073741824,
      "seeders": 10,
      "leechers": 2,
      "published_at": "2024-01-01T00:00:00",
      "is_hr": false,
      "free_percent": 100,
      "categories": ["movie"],
      "tags": ["4K"],
      "raw": {}
    }
  ],
  "count": 1
}
```

### 3. GET /api/debug/ext-indexer/status

获取外部索引桥接状态。

**响应示例**：

```json
{
  "external_indexer_enabled": true,
  "external_indexer_module": "external_indexer_engine.core",
  "runtime_loaded": true
}
```

## 使用流程

1. **配置环境变量**：设置 `EXTERNAL_INDEXER_ENABLED=true` 和 `EXTERNAL_INDEXER_MODULE`
2. **实现外部模块**：按照接口约定实现外部索引引擎模块
3. **启动 VabHub**：外部索引桥接会在启动时自动初始化
4. **测试调试 API**：使用调试 API 验证外部索引功能
5. **正常使用**：搜索服务会自动在结果不足时补充外部索引结果

## 注意事项

1. **降级策略**：外部索引失败不会影响主流程，只记录警告日志
2. **性能考虑**：外部索引只在本地索引结果不足时才会调用
3. **去重机制**：外部索引结果会自动与本地索引结果去重
4. **超时控制**：外部索引请求有超时限制，避免阻塞主流程
5. **授权检查**：外部索引会检查站点授权状态，有挑战的站点会被跳过

## 故障排查

### 外部索引未初始化

- 检查 `EXTERNAL_INDEXER_ENABLED` 是否为 `true`
- 检查 `EXTERNAL_INDEXER_MODULE` 是否正确
- 检查外部模块是否在 Python 路径中
- 查看启动日志中的错误信息

### 搜索无结果

- 使用 `/api/debug/ext-indexer/status` 检查运行时状态
- 使用 `/api/debug/ext-indexer/search` 直接测试搜索
- 检查外部模块的函数签名是否正确
- 查看日志中的警告信息

### 模块加载失败

- 确认模块路径正确
- 确认模块在 Python 路径中
- 检查模块是否有语法错误
- 查看启动日志中的详细错误信息

