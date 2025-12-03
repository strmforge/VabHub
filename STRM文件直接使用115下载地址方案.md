# STRM文件直接使用115下载地址方案

## 📋 概述

由于是开源免费项目，没有独立服务器，为了节省开支，STRM文件**直接使用115网盘下载地址**，无需域名和重定向服务器。

## 🎯 设计原则

1. ✅ **直接使用115下载地址**：STRM文件直接写入115网盘下载地址
2. ✅ **无需域名**：不使用外部域名，节省开支
3. ✅ **无需服务器**：不需要独立的重定向服务器
4. ✅ **可选本地重定向**：如果需要链接刷新，可以使用本地服务（localhost）

## 🔧 实现方案

### 方案1：直接使用115下载地址（推荐，默认）

#### 工作流程

```
1. 上传文件到115网盘
   ↓
2. 获取文件pick_code
   ↓
3. 调用115 API获取下载地址
   ↓
4. 直接写入STRM文件
   ↓
5. 媒体服务器播放时直接访问115下载地址
```

#### STRM文件内容

```strm
# VabHub STRM Metadata
# {
#   "file_id": "cg16zx93h3xy6ddf1",
#   "provider": "115",
#   "media_type": "movie",
#   "title": "示例电影",
#   "year": 2023
# }
https://xxx.115.com/xxx/xxx.mkv?token=xxx
```

#### 优势

- ✅ **无需服务器**：不需要独立服务器
- ✅ **无需域名**：不需要外部域名
- ✅ **零成本**：完全免费
- ✅ **简单直接**：媒体服务器直接访问115下载地址

#### 劣势

- ⚠️ **下载地址可能过期**：115下载地址可能有有效期
- ⚠️ **需要定期刷新**：如果地址过期，需要重新获取并更新STRM文件

### 方案2：本地服务重定向（可选）

#### 使用场景

- 下载地址会过期，需要定期刷新
- 希望统一管理链接刷新

#### 工作流程

```
1. 上传文件到115网盘
   ↓
2. 获取文件pick_code
   ↓
3. 生成JWT token（包含pick_code）
   ↓
4. 写入STRM文件（使用localhost重定向URL）
   ↓
5. 媒体服务器播放时访问localhost重定向服务
   ↓
6. 本地服务实时获取115下载地址并302跳转
```

#### STRM文件内容

```strm
# VabHub STRM Metadata
# {
#   "file_id": "cg16zx93h3xy6ddf1",
#   "provider": "115",
#   "media_type": "movie",
#   "title": "示例电影",
#   "year": 2023
# }
http://localhost:8000/api/strm/stream/115/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 优势

- ✅ **链接自动刷新**：每次播放时实时获取最新下载地址
- ✅ **无需外部服务器**：使用localhost，无需域名
- ✅ **零成本**：完全免费

#### 劣势

- ⚠️ **需要本地服务运行**：VabHub服务必须运行
- ⚠️ **仅限本地访问**：媒体服务器必须能访问localhost

## 🔧 代码实现

### 1. 配置更新

```python
# backend/app/modules/strm/config.py

class STRMConfig(BaseModel):
    """STRM系统配置"""
    # STRM URL生成模式
    # direct: 直接使用115网盘下载地址（推荐，无需服务器）
    # local_redirect: 使用本地服务重定向（用于链接刷新）
    strm_url_mode: str = Field(
        default='direct',
        description="STRM URL生成模式: direct 或 local_redirect"
    )
    
    # 115下载地址刷新配置（仅当strm_url_mode为direct时使用）
    refresh_download_url: bool = Field(
        default=False,
        description="是否定期刷新115下载地址"
    )
    download_url_refresh_interval_hours: int = Field(
        default=24 * 7,  # 7天
        description="115下载地址刷新间隔（小时）"
    )
```

### 2. STRM生成器更新

```python
# backend/app/modules/strm/generator.py

async def _generate_strm_url(
    self,
    cloud_file_id: str,  # pick_code
    cloud_storage: str,
    cloud_115_api: Optional[Cloud115API] = None
) -> str:
    """生成STRM文件URL"""
    if self.config.strm_url_mode == 'direct':
        # 直接使用115网盘下载地址
        if cloud_115_api:
            result = await cloud_115_api.get_download_url(pick_code=cloud_file_id)
            if result.get("success"):
                return result.get("download_url")
        # 如果获取失败，回退到本地重定向
        return self._get_local_redirect_url(cloud_file_id, cloud_storage)
    else:
        # 使用本地服务重定向
        return self._get_local_redirect_url(cloud_file_id, cloud_storage)
```

### 3. 本地重定向API（可选）

```python
# backend/app/api/strm.py

@router.get("/stream/{storage_type}/{token}")
async def stream_file(
    storage_type: str,
    token: str,
    request: Request
):
    """STRM文件流媒体重定向端点（localhost）"""
    # 1. 验证JWT token
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    pick_code = payload.get("pick_code")
    
    # 2. 获取115网盘下载地址
    api = Cloud115API(access_token=settings.cloud_115_access_token)
    result = await api.get_download_url(pick_code=pick_code)
    
    if result.get("success"):
        download_url = result.get("download_url")
        # 3. 302跳转到115下载地址
        return RedirectResponse(url=download_url, status_code=302)
    else:
        raise HTTPException(status_code=404, detail="文件不存在")
```

## 📊 对比分析

| 特性 | 直接下载地址（direct） | 本地重定向（local_redirect） |
|------|----------------------|---------------------------|
| **服务器需求** | ❌ 不需要 | ⚠️ 需要本地VabHub服务运行 |
| **域名需求** | ❌ 不需要 | ❌ 不需要（使用localhost） |
| **成本** | ✅ 零成本 | ✅ 零成本 |
| **链接刷新** | ⚠️ 需要定期刷新STRM文件 | ✅ 自动刷新（实时获取） |
| **外网访问** | ✅ 支持（直接访问115） | ❌ 仅限本地（localhost） |
| **复杂度** | ✅ 简单 | ⚠️ 中等 |
| **推荐场景** | 下载地址稳定，不经常过期 | 下载地址会过期，需要自动刷新 |

## 🎯 推荐方案

### 默认方案：直接使用115下载地址

**原因**：
1. ✅ **零成本**：无需服务器和域名
2. ✅ **简单直接**：STRM文件直接包含下载地址
3. ✅ **外网支持**：媒体服务器可以直接访问115下载地址
4. ✅ **适合开源项目**：完全免费，无需额外资源

**配置**：
```bash
# .env文件
STRM_URL_MODE=direct
```

### 可选方案：本地重定向（如果需要链接刷新）

**使用场景**：
- 115下载地址会过期
- 希望自动刷新链接
- 媒体服务器和VabHub在同一台机器上

**配置**：
```bash
# .env文件
STRM_URL_MODE=local_redirect
STRM_LOCAL_REDIRECT_HOST=localhost
STRM_LOCAL_REDIRECT_PORT=8000
```

## 📝 STRM文件示例

### 直接下载地址模式

```strm
# VabHub STRM Metadata
# {
#   "file_id": "cg16zx93h3xy6ddf1",
#   "provider": "115",
#   "media_type": "movie",
#   "title": "示例电影",
#   "year": 2023
# }
https://proq straight.115.com/down_anqitui/cg16zx93h3xy6ddf1/xxx.mkv?token=xxx&expires=xxx
```

### 本地重定向模式

```strm
# VabHub STRM Metadata
# {
#   "file_id": "cg16zx93h3xy6ddf1",
#   "provider": "115",
#   "media_type": "movie",
#   "title": "示例电影",
#   "year": 2023
# }
http://localhost:8000/api/strm/stream/115/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwaWNrX2NvZGUiOiJjZzE2eng5M2gzeHk2ZGRmMSIsInN0b3JhZ2VfdHlwZSI6IjExNSIsImZpbGVfdHlwZSI6InZpZGVvIiwiZXhwIjoxNzM1NjgwMDAwfQ.signature
```

## 🔄 链接刷新机制（可选）

如果115下载地址会过期，可以实现定期刷新机制：

```python
# 定期刷新STRM文件中的下载地址
async def refresh_strm_download_urls():
    """定期刷新STRM文件中的115下载地址"""
    # 1. 扫描所有STRM文件
    # 2. 提取pick_code
    # 3. 重新获取下载地址
    # 4. 更新STRM文件
    pass
```

## 🚀 实施步骤

1. ✅ **更新配置**：添加 `strm_url_mode` 配置选项
2. ✅ **更新生成器**：实现直接获取115下载地址
3. ✅ **可选实现本地重定向API**：如果需要链接刷新
4. ✅ **测试验证**：测试两种模式
5. ✅ **文档更新**：更新用户文档

## 📚 相关文档

- [VabHub STRM文件链接格式设计](./VabHub%20STRM文件链接格式设计.md)
- [115网盘官方API文档集成完成总结](./115网盘官方API文档集成完成总结.md)
- [视频字幕列表API在302跳转STRM中的应用分析](./视频字幕列表API在302跳转STRM中的应用分析.md)

## ✅ 总结

**推荐使用直接下载地址模式**：
- ✅ 零成本，无需服务器和域名
- ✅ 简单直接，适合开源免费项目
- ✅ 外网支持，媒体服务器可以直接访问115下载地址
- ✅ 完全免费，节省开支

如果115下载地址会过期，可以考虑：
- 实现定期刷新机制
- 或使用本地重定向模式（localhost）

