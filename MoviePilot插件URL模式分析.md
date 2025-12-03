# MoviePilot插件URL模式分析

## 📋 URL分析

### 用户提供的URL

```
http://192.168.51.105:3000/api/v1/plugin/P115StrmHelper/redirect_url?apikey=mwKtUfs6MDjnMDt04b8naQ&pickcode=cg16zx93h3xy6ddf1
```

### URL组成部分

| 部分 | 值 | 说明 |
|------|-----|------|
| **协议** | `http://` | HTTP协议（非HTTPS） |
| **主机** | `192.168.51.105` | **内网IP地址**（不是域名） |
| **端口** | `3000` | MoviePilot服务端口 |
| **路径** | `/api/v1/plugin/P115StrmHelper/redirect_url` | 插件重定向端点 |
| **查询参数** | `apikey=mwKtUfs6MDjnMDt04b8naQ&pickcode=cg16zx93h3xy6ddf1` | API密钥和文件pick_code |

## ✅ 结论

### **没有使用域名**

1. ✅ **使用内网IP地址**：`192.168.51.105` 是局域网IP地址，不是域名
2. ✅ **无需DNS解析**：IP地址直接访问，不需要DNS解析
3. ✅ **无需外部服务器**：在本地网络内运行，不需要公网服务器
4. ✅ **无需域名费用**：完全免费，不需要购买域名

### 工作原理

```
媒体服务器播放STRM文件
    ↓
访问: http://192.168.51.105:3000/api/v1/plugin/P115StrmHelper/redirect_url?apikey=xxx&pickcode=xxx
    ↓
MoviePilot插件接收请求
    ↓
使用pickcode获取115网盘下载地址
    ↓
302重定向到115网盘实际下载地址
    ↓
媒体服务器从115网盘下载并播放
```

## 🎯 对VabHub的启示

### 方案1：使用内网IP地址（推荐，与MoviePilot一致）

#### 优势

- ✅ **无需域名**：使用内网IP地址，完全免费
- ✅ **无需DNS解析**：直接使用IP访问
- ✅ **无需外部服务器**：在本地网络运行
- ✅ **与MoviePilot一致**：相同的实现方式

#### STRM文件URL格式

```
http://192.168.51.105:8000/api/strm/stream/115/{pick_code}
```

或使用JWT token：

```
http://192.168.51.105:8000/api/strm/stream/115/{jwt_token}
```

#### 配置

```bash
# .env文件
STRM_URL_MODE=local_redirect
STRM_LOCAL_REDIRECT_HOST=192.168.51.105  # 本地IP地址
STRM_LOCAL_REDIRECT_PORT=8000
```

### 方案2：直接使用115下载地址（最简单）

#### 优势

- ✅ **最简单**：STRM文件直接包含115下载地址
- ✅ **无需任何服务器**：不需要VabHub服务运行
- ✅ **零成本**：完全免费

#### STRM文件内容

```strm
https://xxx.115.com/xxx/xxx.mkv?token=xxx
```

## 📊 三种方案对比

| 特性 | MoviePilot插件 | VabHub本地重定向 | VabHub直接下载地址 |
|------|---------------|-----------------|-------------------|
| **URL格式** | `http://IP:端口/api/...` | `http://IP:端口/api/strm/...` | `https://115.com/...` |
| **域名需求** | ❌ 不需要 | ❌ 不需要 | ❌ 不需要 |
| **服务器需求** | ⚠️ 需要MoviePilot运行 | ⚠️ 需要VabHub运行 | ❌ 不需要 |
| **成本** | ✅ 免费 | ✅ 免费 | ✅ 免费 |
| **链接刷新** | ✅ 自动刷新 | ✅ 自动刷新 | ⚠️ 需要定期刷新 |
| **外网访问** | ❌ 仅限内网 | ❌ 仅限内网 | ✅ 支持外网 |
| **复杂度** | ⚠️ 中等 | ⚠️ 中等 | ✅ 简单 |

## 🎯 推荐方案

### 推荐方案：使用内网IP地址（与MoviePilot一致）

**原因**：
1. ✅ **与MoviePilot一致**：相同的实现方式，用户熟悉
2. ✅ **无需域名**：使用内网IP，完全免费
3. ✅ **自动链接刷新**：每次播放时实时获取最新下载地址
4. ✅ **适合开源项目**：零成本，无需额外资源

**配置**：
```bash
# .env文件
STRM_URL_MODE=local_redirect
STRM_LOCAL_REDIRECT_HOST=192.168.51.105  # 用户的内网IP
STRM_LOCAL_REDIRECT_PORT=8000
```

**STRM文件URL格式**：
```
http://192.168.51.105:8000/api/strm/stream/115/{jwt_token}
```

### 备选方案：直接使用115下载地址

**使用场景**：
- 115下载地址稳定，不经常过期
- 希望最简单的实现
- 不需要链接刷新功能

**配置**：
```bash
# .env文件
STRM_URL_MODE=direct
```

**STRM文件内容**：
```strm
https://xxx.115.com/xxx/xxx.mkv?token=xxx
```

## 🔧 实现建议

### 1. 默认使用本地重定向（内网IP）

```python
# backend/app/modules/strm/config.py

strm_url_mode: str = Field(
    default='local_redirect',  # 默认使用本地重定向
    description="STRM URL生成模式"
)

local_redirect_host: str = Field(
    default='localhost',  # 默认localhost，用户可配置为内网IP
    description="本地重定向服务器主机"
)
```

### 2. 支持自动检测内网IP

```python
import socket

def get_local_ip():
    """获取本机内网IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"
```

### 3. 用户配置

```bash
# .env文件
# 方案1：使用本地重定向（推荐）
STRM_URL_MODE=local_redirect
STRM_LOCAL_REDIRECT_HOST=192.168.51.105  # 用户的内网IP
STRM_LOCAL_REDIRECT_PORT=8000

# 方案2：直接使用115下载地址
STRM_URL_MODE=direct
```

## 📚 相关文档

- [STRM文件直接使用115下载地址方案](./STRM文件直接使用115下载地址方案.md)
- [VabHub STRM文件链接格式设计](./VabHub%20STRM文件链接格式设计.md)
- [115网盘开发者平台域名配置方案](./115网盘开发者平台域名配置方案.md)

## ✅ 总结

**MoviePilot插件URL模式分析**：
- ✅ **没有使用域名**：使用内网IP地址 `192.168.51.105`
- ✅ **无需DNS解析**：直接使用IP访问
- ✅ **无需外部服务器**：在本地网络运行
- ✅ **完全免费**：零成本实现

**对VabHub的建议**：
- ✅ **推荐使用内网IP地址**：与MoviePilot一致，用户熟悉
- ✅ **支持直接下载地址模式**：作为备选方案
- ✅ **无需域名**：完全免费，适合开源项目

