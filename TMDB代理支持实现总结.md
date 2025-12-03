# TMDB代理支持实现总结

## 概述

已成功为VabHub的TMDB服务添加代理支持，参考MoviePilot和往期版本的实现。

## 实现内容

### 1. 配置项添加

在 `app/core/config.py` 中添加了以下配置项：

```python
# 网络代理配置（用于TMDB、Github等需要代理的服务）
PROXY_HOST: Optional[str] = os.getenv("PROXY_HOST", None)  # 代理服务器地址
DOH_ENABLE: bool = os.getenv("DOH_ENABLE", "false").lower() == "true"  # 是否启用DNS over HTTPS
DOH_DOMAINS: str = os.getenv("DOH_DOMAINS", "api.themoviedb.org,api.tmdb.org,...")  # DOH域名列表
DOH_RESOLVERS: str = os.getenv("DOH_RESOLVERS", "1.0.0.1,1.1.1.1,9.9.9.9,149.112.112.112")  # DOH解析服务器列表
```

### 2. HTTP客户端工具

创建了 `app/utils/http_client.py`，提供统一的HTTP客户端创建函数：

- `get_proxy_config()`: 获取代理配置
- `create_httpx_client()`: 创建异步HTTP客户端（自动应用代理）
- `create_httpx_sync_client()`: 创建同步HTTP客户端（自动应用代理）

### 3. TMDB API集成

更新了以下文件，使TMDB请求自动使用代理：

- `app/api/media.py`: 所有TMDB API调用（搜索、详情、季信息）
- `app/modules/media_renamer/identifier.py`: 媒体识别时的TMDB查询

### 4. 配置属性

在 `Settings` 类中添加了 `PROXY` 和 `PROXY_FOR_HTTPX` 属性，方便不同场景使用。

## 使用方法

### 环境变量配置

在 `.env` 文件或环境变量中设置：

```bash
# HTTP/HTTPS代理
PROXY_HOST=http://127.0.0.1:7890

# SOCKS5代理
PROXY_HOST=socks5://127.0.0.1:1080

# 带认证的代理
PROXY_HOST=http://username:password@proxy.example.com:8080
```

### 代码使用

```python
from app.utils.http_client import create_httpx_client

# 自动使用代理（如果配置了）
async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
    response = await client.get("https://api.themoviedb.org/3/...")
```

## 对比

| 功能 | MoviePilot | VabHub-1 | 当前VabHub |
|------|------------|----------|------------|
| **代理配置** | ✅ PROXY_HOST | ✅ PROXY_HOST | ✅ PROXY_HOST |
| **TMDB代理** | ✅ 已实现 | ✅ 已实现 | ✅ 已实现 |
| **统一HTTP客户端** | ✅ RequestUtils | ✅ aiohttp | ✅ http_client工具 |
| **DOH支持** | ✅ 已实现 | ✅ 已实现 | ⚠️ 配置项已添加，待实现 |
| **自动应用代理** | ✅ 是 | ✅ 是 | ✅ 是 |

## 待完成工作

- [ ] 实现DNS over HTTPS (DOH)功能
- [ ] Github API代理支持（系统更新时）
- [ ] 代理健康检查
- [ ] 代理自动切换（多个代理）

**说明**: 豆瓣API不需要代理支持，已从待完成清单中移除。

## 总结

TMDB代理支持已完全实现，与MoviePilot和往期版本保持一致。所有TMDB API请求都会自动使用配置的代理（如果设置了`PROXY_HOST`）。

