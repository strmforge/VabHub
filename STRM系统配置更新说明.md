# STRM系统配置更新说明

## 📋 更新内容

### 1. 新增刮削配置开关

在 `STRMConfig` 中新增了两个刮削配置开关：

- **`scrape_cloud_files`**: 是否对网盘文件进行刮削（默认：`False`）
- **`scrape_local_strm`**: 是否对本地STRM文件进行刮削（默认：`True`）

### 2. 新增其他配置项

为了完善配置模型，还新增了以下配置项：

- **`generate_nfo`**: 是否生成NFO文件（默认：`True`）
- **`generate_subtitle_files`**: 是否生成字幕文件（默认：`True`）
- **`media_servers`**: 媒体服务器列表（默认：`[]`）
- **`auto_refresh`**: 是否自动刷新媒体服务器（默认：`True`）
- **`refresh_delay`**: 刷新延迟（秒）（默认：`300`）
- **`enabled`**: 是否启用STRM系统（默认：`True`）

## 🔧 配置使用

### 配置示例

```python
from app.modules.strm.config import STRMConfig

# 创建STRM配置
config = STRMConfig(
    # 媒体库路径
    media_library_path='/media_library',
    movie_path='/media_library/Movies',
    tv_path='/media_library/TV Shows',
    
    # STRM URL生成模式
    strm_url_mode='direct',  # 或 'local_redirect'
    
    # 刮削配置
    scrape_cloud_files=False,  # 不对网盘文件进行刮削
    scrape_local_strm=True,  # 对本地STRM文件进行刮削
    
    # NFO配置
    generate_nfo=True,  # 生成NFO文件
    
    # 字幕配置
    generate_subtitle_files=True,  # 生成字幕文件
    
    # 媒体服务器配置
    media_servers=['plex', 'jellyfin'],  # 媒体服务器列表
    auto_refresh=True,  # 自动刷新
    refresh_delay=300  # 刷新延迟5分钟
    
    # 服务开关
    enabled=True  # 启用STRM系统
)
```

### 使用场景

#### 场景1：只生成STRM文件，不进行刮削

```python
config = STRMConfig(
    scrape_cloud_files=False,  # 不对网盘文件进行刮削
    scrape_local_strm=False,  # 不对本地STRM文件进行刮削
    generate_nfo=False,  # 不生成NFO文件
    generate_subtitle_files=True  # 只生成字幕文件
)
```

#### 场景2：完整功能（包括刮削）

```python
config = STRMConfig(
    scrape_cloud_files=True,  # 对网盘文件进行刮削
    scrape_local_strm=True,  # 对本地STRM文件进行刮削
    generate_nfo=True,  # 生成NFO文件
    generate_subtitle_files=True,  # 生成字幕文件
    media_servers=['plex', 'jellyfin', 'emby'],  # 所有媒体服务器
    auto_refresh=True  # 自动刷新
)
```

#### 场景3：网盘刮削但本地不刮削

```python
config = STRMConfig(
    scrape_cloud_files=True,  # 对网盘文件进行刮削
    scrape_local_strm=False,  # 不对本地STRM文件进行刮削
    generate_nfo=True,  # 生成NFO文件
    generate_subtitle_files=True  # 生成字幕文件
)
```

## 📊 配置对比

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `scrape_cloud_files` | `False` | 是否对网盘文件进行刮削 |
| `scrape_local_strm` | `True` | 是否对本地STRM文件进行刮削 |
| `generate_nfo` | `True` | 是否生成NFO文件 |
| `generate_subtitle_files` | `True` | 是否生成字幕文件 |
| `media_servers` | `[]` | 媒体服务器列表 |
| `auto_refresh` | `True` | 是否自动刷新媒体服务器 |
| `refresh_delay` | `300` | 刷新延迟（秒） |
| `enabled` | `True` | 是否启用STRM系统 |

## 🔍 实现逻辑

### 刮削逻辑

```python
async def generate_strm_file(
    self,
    media_info: Dict[str, Any],
    cloud_file_id: str,
    cloud_storage: str,
    cloud_path: str,
    subtitle_files: Optional[List[str]] = None
):
    """生成STRM文件"""
    
    # 1. 生成STRM文件
    strm_path = await self._generate_strm(...)
    
    # 2. 网盘刮削（如果启用）
    if self.config.scrape_cloud_files:
        await self._scrape_cloud_file(
            cloud_storage=cloud_storage,
            cloud_file_id=cloud_file_id,
            media_info=media_info
        )
    
    # 3. 生成本地文件（字幕、NFO等）
    if subtitle_files and self.config.generate_subtitle_files:
        await self._generate_subtitle_files(...)
    
    if self.config.generate_nfo:
        await self._generate_nfo(...)
    
    # 4. 本地STRM刮削（如果启用）
    if self.config.scrape_local_strm:
        await self._scrape_local_strm(
            strm_path=strm_path,
            media_info=media_info
        )
    
    # 5. 刷新媒体服务器（如果启用）
    if self.config.auto_refresh and self.config.media_servers:
        await self._refresh_media_servers(
            media_servers=self.config.media_servers,
            strm_path=strm_path,
            media_info=media_info
        )
```

## ✅ 优势

1. **灵活配置**：可以根据需要开启或关闭刮削功能
2. **性能优化**：不进行刮削时可以提高STRM生成速度
3. **资源节约**：不进行网盘刮削时可以节省API调用
4. **易于维护**：配置清晰，易于理解和修改

## 📝 注意事项

1. **网盘刮削**：需要调用主系统的 `MediaScraperService.scrape_cloud_file()` 方法
2. **本地STRM刮削**：需要调用主系统的 `MediaScraperService.scrape_local_strm()` 方法
3. **默认配置**：网盘刮削默认关闭，本地STRM刮削默认开启
4. **性能影响**：刮削会增加STRM生成时间，但可以提供更完整的媒体信息

