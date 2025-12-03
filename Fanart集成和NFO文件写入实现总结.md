# Fanart集成和NFO文件写入实现总结

**生成时间**: 2025-01-XX  
**目的**: 总结Fanart集成和NFO文件写入的实现

---

## 📋 一、已完成的工作

### 1.1 Fanart集成到媒体识别服务 ✅

**文件**: `VabHub/backend/app/modules/media_identification/service.py`

**实现内容**:
- ✅ 添加 `_get_fanart_module()` 方法 - 获取Fanart模块实例
- ✅ 添加 `_get_fanart_images()` 方法 - 获取Fanart图片（异步）
- ✅ 在识别成功后自动获取Fanart图片
  - TMDB识别成功：如果是电视剧，自动获取Fanart图片
  - TVDB识别成功：自动获取Fanart图片（优先使用TVDB ID）

**特点**:
- ✅ **自动集成** - 识别成功后自动获取Fanart图片
- ✅ **智能选择** - 电视剧优先使用TVDB ID获取Fanart图片
- ✅ **图片处理** - 自动选择最佳图片（优先中文/英文，按likes排序）
- ✅ **图片类型** - 支持海报、背景图、Logo等

### 1.2 NFO文件写入模块 ✅

**文件**: `VabHub/backend/app/modules/media_renamer/nfo_writer.py`

**实现内容**:
- ✅ `NFOWriter` 类 - NFO文件写入器
- ✅ `write_nfo()` - 写入NFO文件
- ✅ `_generate_emby_nfo()` - 生成Emby/Jellyfin格式NFO
- ✅ `_generate_movie_nfo()` - 生成电影NFO
- ✅ `_generate_tv_nfo()` - 生成电视剧NFO（支持单集和整剧）
- ✅ `_format_xml()` - 格式化XML输出

**支持的NFO格式**:
- ✅ **Emby格式** - 标准Emby NFO格式
- ✅ **Jellyfin格式** - 与Emby兼容
- ✅ **Plex格式** - 与Emby兼容（Plex也支持Emby格式）

**NFO文件包含的信息**:
- ✅ 基本信息：标题、年份
- ✅ ID信息：TMDB ID、TVDB ID、IMDB ID
- ✅ 元数据：概述、海报URL、背景图URL
- ✅ 电视剧信息：季数、集数（单集NFO）

### 1.3 NFO写入集成到媒体整理器 ✅

**文件**: `VabHub/backend/app/modules/media_renamer/organizer.py`

**实现内容**:
- ✅ 在 `MediaOrganizer` 中添加 `NFOWriter` 实例
- ✅ 在 `organize_file()` 中添加 `write_nfo` 参数
- ✅ 文件整理完成后自动写入NFO文件
- ✅ NFO文件包含完整的媒体信息（TMDB ID、TVDB ID、IMDB ID等）

### 1.4 MediaInfo扩展 ✅

**文件**: `VabHub/backend/app/modules/media_renamer/parser.py`

**扩展内容**:
- ✅ 添加 `tmdb_id` 字段 - TMDB ID
- ✅ 添加 `tvdb_id` 字段 - TVDB ID
- ✅ 添加 `imdb_id` 字段 - IMDB ID
- ✅ 添加 `overview` 字段 - 概述
- ✅ 添加 `poster_url` 字段 - 海报URL
- ✅ 添加 `backdrop_url` 字段 - 背景图URL

### 1.5 MediaIdentifier增强 ✅

**文件**: `VabHub/backend/app/modules/media_renamer/identifier.py`

**增强内容**:
- ✅ 优先使用 `MediaIdentificationService` 进行完整识别
- ✅ 自动获取TMDB ID、TVDB ID、IMDB ID
- ✅ 自动获取Fanart图片（如果可用）
- ✅ 回退机制：如果MediaIdentificationService失败，回退到TMDB查询
- ✅ 更新 `_merge_tmdb_info()` 方法，填充所有ID字段

---

## 📋 二、Fanart集成详细说明

### 2.1 集成流程

```
媒体识别成功
    ↓
检查是否为电视剧
    ↓ (是)
检查Fanart是否启用
    ↓ (是)
获取Fanart图片
    ↓
处理图片数据（选择最佳图片）
    ↓
添加到识别结果
```

### 2.2 图片选择策略

**电视剧**:
- **海报** - 优先选择中文/英文，按likes排序
- **背景图** - 按likes排序，选择最高
- **Logo** - 按likes排序，选择最高

**电影**:
- **海报** - 按likes排序，选择最高
- **背景图** - 按likes排序，选择最高

### 2.3 识别结果增强

识别结果现在包含 `fanart_images` 字段：
```python
{
    "success": True,
    "title": "The Wheel of Time",
    "tvdb_id": 355730,
    "fanart_images": {
        "poster": "http://assets.fanart.tv/fanart/tv/355730/tvposter/...",
        "backdrop": "http://assets.fanart.tv/fanart/tv/355730/showbackground/...",
        "logo": "http://assets.fanart.tv/fanart/tv/355730/hdtvlogo/..."
    }
}
```

---

## 📋 三、NFO文件写入详细说明

### 3.1 NFO文件格式

**电影NFO** (`movie.nfo`):
```xml
<?xml version="1.0" encoding="utf-8"?>
<movie>
  <title>Fight Club</title>
  <year>1999</year>
  <tmdbid>550</tmdbid>
  <imdbid>tt0137523</imdbid>
  <plot>概述内容...</plot>
  <poster>海报URL</poster>
  <fanart>背景图URL</fanart>
</movie>
```

**电视剧单集NFO** (`episode.nfo`):
```xml
<?xml version="1.0" encoding="utf-8"?>
<episodedetails>
  <title>Episode Title</title>
  <season>1</season>
  <episode>1</episode>
  <plot>概述内容...</plot>
  <tmdbid>12345</tmdbid>
  <tvdbid>355730</tvdbid>
  <imdbid>tt1234567</imdbid>
  <thumb>海报URL</thumb>
  <fanart>背景图URL</fanart>
</episodedetails>
```

**电视剧整剧NFO** (`tvshow.nfo`):
```xml
<?xml version="1.0" encoding="utf-8"?>
<tvshow>
  <title>The Wheel of Time</title>
  <year>2021</year>
  <tmdbid>12345</tmdbid>
  <tvdbid>355730</tvdbid>
  <imdbid>tt1234567</imdbid>
  <plot>概述内容...</plot>
  <poster>海报URL</poster>
  <fanart>背景图URL</fanart>
</tvshow>
```

### 3.2 NFO文件位置

NFO文件与媒体文件在同一目录，文件名相同，扩展名为 `.nfo`：
```
/media/movies/Fight Club (1999)/Fight Club (1999) [1080p].mkv
/media/movies/Fight Club (1999)/Fight Club (1999) [1080p].nfo
```

### 3.3 使用方式

```python
from app.modules.media_renamer.organizer import MediaOrganizer

# 创建整理器（指定NFO格式）
organizer = MediaOrganizer(
    tmdb_api_key="your-key",
    nfo_format="emby"  # 或 "jellyfin" 或 "plex"
)

# 整理文件（自动写入NFO）
result = await organizer.organize_file(
    file_path="/path/to/video.mkv",
    target_base_dir="/media/movies",
    write_nfo=True  # 启用NFO写入
)
```

---

## 📋 四、完整工作流

### 4.1 媒体识别和整理流程

```
1. 文件名解析
    ↓
2. MediaIdentificationService识别
    ├─ TMDB搜索
    ├─ TVDB搜索（电视剧备选）
    └─ Fanart图片获取（电视剧）
    ↓
3. 文件重命名
    ↓
4. 文件分类
    ↓
5. 文件移动/复制
    ↓
6. 字幕下载（可选）
    ↓
7. NFO文件写入（包含TVDB ID）
```

### 4.2 数据流

```
MediaIdentificationService
    ↓ (识别结果)
MediaIdentifier
    ↓ (MediaInfo对象)
MediaOrganizer
    ↓ (整理结果)
NFOWriter
    ↓ (NFO文件)
```

---

## 📋 五、总结

### 5.1 实现完成

- ✅ **Fanart集成** - 自动获取Fanart图片，优先使用TVDB ID
- ✅ **NFO文件写入** - 支持Emby/Jellyfin/Plex格式
- ✅ **TVDB ID支持** - NFO文件包含TVDB ID
- ✅ **完整信息** - NFO文件包含TMDB ID、TVDB ID、IMDB ID等

### 5.2 优势

1. **自动化** - 识别和整理过程中自动获取Fanart图片和写入NFO
2. **多格式支持** - 支持Emby、Jellyfin、Plex格式
3. **完整信息** - 包含所有媒体ID和元数据
4. **智能选择** - 自动选择最佳图片和匹配结果

---

**文档生成时间**: 2025-01-XX  
**文档版本**: 1.0

