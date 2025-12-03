# TVDB集成到媒体识别链实现总结

**生成时间**: 2025-01-XX  
**目的**: 总结TVDB集成到媒体识别链的实现

---

## 📋 一、已完成的工作

### 1.1 集成TVDB到媒体识别服务 ✅

**文件**: `VabHub/backend/app/modules/media_identification/service.py`

**实现内容**:
- ✅ 添加 `_get_tvdb_module()` 方法 - 获取TVDB模块实例
- ✅ 添加 `_search_tmdb()` 方法 - 搜索TMDB（异步）
- ✅ 添加 `_search_tvdb()` 方法 - 搜索TVDB（异步，仅用于电视剧）
- ✅ 更新 `identify_media()` 方法 - 实现完整的识别链

**识别链流程**:
1. **文件名解析** - 从文件名提取标题、年份、季、集等信息
2. **TMDB搜索** - 如果文件名解析成功且TMDB API Key已配置，尝试搜索TMDB
3. **TVDB搜索** - 如果是电视剧且TMDB失败或未找到，尝试搜索TVDB（备选数据源）
4. **增强识别服务** - 如果以上都失败，尝试使用增强识别服务

### 1.2 TMDB搜索功能 ✅

**实现内容**:
- ✅ 支持电影和电视剧搜索
- ✅ 年份匹配优化（优先匹配年份）
- ✅ 获取详细信息（标题、年份、概述、图片等）
- ✅ 获取external_ids（对于电视剧，包含TVDB ID）
- ✅ 图片URL生成（海报、背景图）

**特点**:
- ✅ 异步支持
- ✅ 错误处理完善
- ✅ 日志记录

### 1.3 TVDB搜索功能 ✅

**实现内容**:
- ✅ 仅用于电视剧（tv/series类型）
- ✅ 年份匹配优化（优先匹配年份）
- ✅ 获取详细信息（标题、年份、概述、图片等）
- ✅ 获取remoteIds（包含IMDB ID、TMDB ID）
- ✅ 图片URL获取（海报、横幅图）

**特点**:
- ✅ 异步支持
- ✅ 错误处理完善
- ✅ 日志记录
- ✅ 作为TMDB的备选数据源

---

## 📋 二、识别链详细说明

### 2.1 识别流程

```
文件名解析
    ↓ (成功)
TMDB搜索（如果TMDB API Key已配置）
    ↓ (成功)
使用TMDB结果（包含TMDB ID、TVDB ID、IMDB ID等）
    ↓ (失败且是电视剧)
TVDB搜索（备选数据源）
    ↓ (成功)
使用TVDB结果（包含TVDB ID、TMDB ID、IMDB ID等）
    ↓ (失败)
使用文件名解析结果（基础信息）
    ↓ (文件名解析失败)
增强识别服务
```

### 2.2 识别结果字段

**成功识别结果包含**:
- `success`: True
- `title`: 标题
- `year`: 年份
- `season`: 季数（电视剧）
- `episode`: 集数（电视剧）
- `type`: 媒体类型（movie/tv/series）
- `tmdb_id`: TMDB ID（如果找到）
- `tvdb_id`: TVDB ID（如果找到）
- `imdb_id`: IMDB ID（如果找到）
- `poster_url`: 海报图片URL
- `backdrop_url`: 背景图片URL
- `overview`: 概述
- `confidence`: 置信度（0.0-1.0）
- `source`: 识别来源（tmdb/tvdb/filename_parser/enhanced_identification）

**失败识别结果包含**:
- `success`: False
- `error`: 错误信息

---

## 📋 三、识别优先级

### 3.1 数据源优先级

1. **TMDB**（最高优先级）
   - 置信度: 0.9
   - 适用于: 电影和电视剧
   - 条件: TMDB API Key已配置

2. **TVDB**（中等优先级）
   - 置信度: 0.8
   - 适用于: 仅电视剧
   - 条件: TMDB失败或未找到

3. **文件名解析**（较低优先级）
   - 置信度: 0.6
   - 适用于: 所有类型
   - 条件: 文件名解析成功但API搜索失败

4. **增强识别服务**（最低优先级）
   - 置信度: 根据服务返回
   - 适用于: 所有类型
   - 条件: 文件名解析失败

### 3.2 电视剧特殊处理

- ✅ **优先使用TMDB** - 如果TMDB搜索成功，使用TMDB结果（包含TVDB ID）
- ✅ **TVDB作为备选** - 如果TMDB失败，尝试TVDB搜索
- ✅ **自动获取TVDB ID** - 从TMDB的external_ids中获取TVDB ID

---

## 📋 四、使用方式

### 4.1 基本使用

```python
from app.modules.media_identification.service import MediaIdentificationService

# 创建服务实例
service = MediaIdentificationService(db)

# 识别媒体文件
result = await service.identify_media(
    file_path="/path/to/video.mkv",
    file_name="The.Wheel.of.Time.S01E01.1080p.mkv"
)

# 检查识别结果
if result.get("success"):
    print(f"标题: {result.get('title')}")
    print(f"TMDB ID: {result.get('tmdb_id')}")
    print(f"TVDB ID: {result.get('tvdb_id')}")
    print(f"识别来源: {result.get('source')}")
else:
    print(f"识别失败: {result.get('error')}")
```

### 4.2 批量识别

```python
# 批量识别
results = await service.batch_identify([
    "/path/to/video1.mkv",
    "/path/to/video2.mkv",
    "/path/to/video3.mkv"
])

for result in results:
    print(f"文件: {result['file_path']}")
    print(f"识别结果: {result.get('title', '未识别')}")
```

---

## 📋 五、后续工作

### 5.1 待实现功能 ⏳

1. **Fanart集成**（tvdb-3）
   - ⏳ 在识别成功后，使用TVDB ID获取Fanart图片
   - ⏳ 优先使用TVDB ID（电视剧）

2. **NFO文件写入**（tvdb-4）
   - ⏳ 在媒体整理时，写入TVDB ID到NFO文件
   - ⏳ 支持Emby/Jellyfin/Plex格式

---

## 📋 六、总结

### 6.1 实现完成

- ✅ **TVDB集成** - TVDB已成功集成到媒体识别链中
- ✅ **识别链优化** - 实现了完整的识别链（文件名解析 → TMDB → TVDB → 增强识别）
- ✅ **电视剧支持** - 电视剧优先使用TMDB，失败时使用TVDB作为备选
- ✅ **自动获取ID** - 自动获取TMDB ID、TVDB ID、IMDB ID

### 6.2 优势

1. **多数据源支持** - TMDB和TVDB双重保障
2. **智能降级** - 自动在多个数据源间切换
3. **完整信息** - 获取完整的媒体信息（ID、图片、概述等）
4. **高可靠性** - 即使某个数据源失败，也能使用其他数据源

---

**文档生成时间**: 2025-01-XX  
**文档版本**: 1.0

