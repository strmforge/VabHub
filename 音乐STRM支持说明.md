# 音乐STRM支持说明

## 概述

是的，**Emby、Jellyfin、Plex等媒体库软件支持音乐媒体库，同时也支持STRM文件用于音乐**。

## 技术原理

### STRM文件的工作原理

STRM（Stream）文件是一个文本文件，包含指向实际媒体文件的URL或本地文件路径。媒体服务器读取STRM文件，获取URL，然后通过302重定向或代理来播放实际的媒体文件。

### 音乐STRM的可行性

1. **技术层面**：
   - Emby/Jellyfin/Plex都原生支持STRM文件
   - STRM文件格式是通用的，不区分媒体类型
   - 音乐文件也可以通过STRM文件指向云存储中的音频文件

2. **应用场景**：
   - 音乐文件存储在115网盘等云存储
   - 通过STRM文件让媒体服务器直接播放云盘中的音乐
   - 节省本地存储空间（特别是FLAC等无损格式）

3. **优势**：
   - 无需下载到本地即可播放
   - 节省本地存储空间
   - 统一管理云盘和本地音乐

## VabHub的音乐STRM支持

### 已实现的功能

1. **STRM文件名生成**：
   - 支持音乐类型：`music` 或 `audio`
   - 文件名格式：
     - 有专辑：`Artist - Album - TrackNumber - Title.strm`
     - 无专辑：`Artist - Title.strm`

2. **路径组织**：
   - 基础路径：`/media_library/Music`
   - 目录结构：`Artist/Album/` 或 `Artist/`
   - 自动识别云存储路径中的"音乐/"或"Music/"前缀

3. **媒体信息支持**：
   - 艺术家（artist）
   - 标题（title）
   - 专辑（album）
   - 曲目编号（track_number）

### 使用示例

#### 生成音乐STRM文件

```python
from app.modules.strm.generator import STRMGenerator
from app.modules.strm.config import STRMConfig

# 配置
config = STRMConfig(
    media_library_path="/media_library",
    music_path="/media_library/Music"
)

# 创建生成器
generator = STRMGenerator(config)

# 音乐媒体信息
media_info = {
    "type": "music",  # 或 "audio"
    "title": "夜曲",
    "artist": "周杰伦",
    "album": "十一月的萧邦",
    "track_number": 1,
    "year": 2005
}

# 生成STRM文件
result = await generator.generate_strm_file(
    media_info=media_info,
    cloud_file_id="pick_code_123456",
    cloud_storage="115",
    cloud_path="/115/音乐/周杰伦/十一月的萧邦/夜曲.flac"
)

# 结果：
# {
#     'strm_path': '/media_library/Music/周杰伦/十一月的萧邦/周杰伦 - 十一月的萧邦 - 01 - 夜曲.strm',
#     'subtitle_paths': [],
#     'nfo_path': '/media_library/Music/周杰伦/十一月的萧邦/周杰伦 - 十一月的萧邦 - 01 - 夜曲.nfo'
# }
```

#### STRM文件内容示例

```
#STRM Local Redirect
http://192.168.1.100:8000/api/strm/stream/115/eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
#METADATA
{
  "storage_type": "115",
  "file_id": "pick_code_123456",
  "file_name": "夜曲.flac",
  "media_type": "music",
  "artist": "周杰伦",
  "title": "夜曲",
  "album": "十一月的萧邦"
}
```

## 媒体服务器配置

### Emby配置

1. 添加音乐库：
   - 类型选择：**音乐**
   - 路径：`/media_library/Music`
   - 元数据提供者：MusicBrainz、Last.fm等

2. 扫描STRM文件：
   - Emby会自动识别`.strm`文件
   - 读取STRM文件中的URL
   - 通过302重定向播放云盘中的音乐

### Jellyfin配置

1. 添加音乐库：
   - 内容类型：**音乐**
   - 路径：`/media_library/Music`
   - 元数据提供者：MusicBrainz、Last.fm等

2. STRM支持：
   - Jellyfin原生支持STRM文件
   - 自动处理URL重定向

### Plex配置

1. 添加音乐库：
   - 类型：**音乐**
   - 路径：`/media_library/Music`
   - 代理：MusicBrainz、Last.fm等

2. STRM支持：
   - Plex原生支持STRM文件
   - 通过代理服务器处理URL

## 注意事项

1. **URL有效期**：
   - 115网盘的下载地址可能会过期
   - 建议使用`local_redirect`模式，自动刷新链接

2. **网络要求**：
   - 媒体服务器需要能够访问STRM文件中的URL
   - 如果使用本地重定向，需要确保网络连通性

3. **文件格式**：
   - 支持所有音频格式：MP3、FLAC、WAV、M4A、AAC等
   - 媒体服务器需要支持相应的音频编解码器

4. **元数据**：
   - STRM文件本身不包含音频元数据
   - 需要配合NFO文件或媒体服务器的元数据提供者
   - 建议启用`generate_nfo`选项

## 与视频STRM的区别

| 特性 | 视频STRM | 音乐STRM |
|------|---------|---------|
| 文件大小 | 通常较大（GB级别） | 通常较小（MB级别） |
| 存储优势 | 显著节省空间 | 中等节省空间 |
| 播放方式 | 流式播放 | 流式播放或完整下载 |
| 元数据 | 电影/电视剧信息 | 艺术家/专辑信息 |
| 目录结构 | Title (Year)/ | Artist/Album/ |

## 总结

**是的，Emby等媒体库软件的音乐媒体库支持也意味着对STRM文件的支持**。VabHub已经扩展了STRM系统以支持音乐文件，可以：

1. ✅ 为云盘中的音乐文件生成STRM文件
2. ✅ 自动组织目录结构（Artist/Album/）
3. ✅ 生成符合音乐命名规范的STRM文件名
4. ✅ 支持所有主流音频格式
5. ✅ 与Emby/Jellyfin/Plex无缝集成

这使得用户可以将大量音乐文件存储在云盘中，通过STRM文件在媒体服务器中播放，既节省了本地存储空间，又保持了统一的媒体管理体验。

