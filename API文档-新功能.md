# VabHub API 文档 - 新功能

## 📋 目录

1. [豆瓣API](#豆瓣api)
2. [媒体文件管理API](#媒体文件管理api)
3. [字幕管理API](#字幕管理api)
4. [重复文件检测API](#重复文件检测api)
5. [文件质量比较API](#文件质量比较api)

---

## 豆瓣API

### 1. 搜索豆瓣媒体

**端点**: `GET /api/v1/douban/search`

**描述**: 搜索豆瓣电影或电视剧

**参数**:
- `query` (string, 必需): 搜索关键词
- `media_type` (string, 可选): 媒体类型，`movie` 或 `tv`，默认 `movie`
- `start` (integer, 可选): 起始位置，默认 `0`
- `count` (integer, 可选): 返回数量，默认 `20`，最大 `100`

**示例请求**:
```bash
curl -X GET "http://localhost:8000/api/v1/douban/search?query=肖申克的救赎&media_type=movie&count=10"
```

**响应示例**:
```json
{
  "success": true,
  "message": "搜索成功",
  "data": {
    "total": 10,
    "items": [
      {
        "id": "1292052",
        "title": "肖申克的救赎",
        "original_title": "The Shawshank Redemption",
        "year": 1994,
        "rating": 9.7,
        "rating_count": 2000000,
        "poster": "https://img1.doubanio.com/view/photo/s_ratio_poster/public/p480747492.jpg",
        "type": "movie",
        "genres": ["剧情", "犯罪"],
        "directors": ["弗兰克·德拉邦特"],
        "actors": ["蒂姆·罗宾斯", "摩根·弗里曼"]
      }
    ]
  },
  "timestamp": "2025-01-XX..."
}
```

### 2. 获取豆瓣媒体详情

**端点**: `GET /api/v1/douban/detail/{subject_id}`

**描述**: 获取豆瓣媒体详细信息

**路径参数**:
- `subject_id` (string, 必需): 豆瓣主题ID

**查询参数**:
- `media_type` (string, 可选): 媒体类型，`movie` 或 `tv`，默认 `movie`

**示例请求**:
```bash
curl -X GET "http://localhost:8000/api/v1/douban/detail/1292052?media_type=movie"
```

**响应示例**:
```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "id": "1292052",
    "title": "肖申克的救赎",
    "original_title": "The Shawshank Redemption",
    "year": 1994,
    "rating": 9.7,
    "rating_count": 2000000,
    "poster": "https://img1.doubanio.com/view/photo/s_ratio_poster/public/p480747492.jpg",
    "backdrop": "https://img1.doubanio.com/view/photo/s_ratio_poster/public/p480747492.jpg",
    "type": "movie",
    "genres": ["剧情", "犯罪"],
    "countries": ["美国"],
    "directors": ["弗兰克·德拉邦特"],
    "actors": ["蒂姆·罗宾斯", "摩根·弗里曼"],
    "summary": "影片讲述了银行家安迪被冤枉杀了他的妻子和其情人..."
  },
  "timestamp": "2025-01-XX..."
}
```

### 3. 获取豆瓣评分

**端点**: `GET /api/v1/douban/rating/{subject_id}`

**描述**: 获取豆瓣评分和评分分布

**路径参数**:
- `subject_id` (string, 必需): 豆瓣主题ID

**查询参数**:
- `media_type` (string, 可选): 媒体类型，`movie` 或 `tv`，默认 `movie`

**示例请求**:
```bash
curl -X GET "http://localhost:8000/api/v1/douban/rating/1292052?media_type=movie"
```

**响应示例**:
```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "rating": 9.7,
    "rating_count": 2000000,
    "stars": {
      "5": 0.8,
      "4": 0.15,
      "3": 0.04,
      "2": 0.008,
      "1": 0.002
    }
  },
  "timestamp": "2025-01-XX..."
}
```

### 4. 获取豆瓣电影TOP250

**端点**: `GET /api/v1/douban/top250`

**描述**: 获取豆瓣电影TOP250榜单

**参数**:
- `start` (integer, 可选): 起始位置，默认 `0`
- `count` (integer, 可选): 返回数量，默认 `20`，最大 `100`

**示例请求**:
```bash
curl -X GET "http://localhost:8000/api/v1/douban/top250?start=0&count=20"
```

### 5. 获取热门电影

**端点**: `GET /api/v1/douban/hot/movie`

**描述**: 获取豆瓣热门电影

**参数**:
- `start` (integer, 可选): 起始位置，默认 `0`
- `count` (integer, 可选): 返回数量，默认 `20`，最大 `100`

### 6. 获取热门电视剧

**端点**: `GET /api/v1/douban/hot/tv`

**描述**: 获取豆瓣热门电视剧

**参数**:
- `start` (integer, 可选): 起始位置，默认 `0`
- `count` (integer, 可选): 返回数量，默认 `20`，最大 `100`

---

## 媒体文件管理API

### 1. 识别媒体文件

**端点**: `POST /api/v1/media-renamer/identify`

**描述**: 识别媒体文件信息

**参数**:
- `file_path` (string, 必需): 文件路径

**示例请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/media-renamer/identify?file_path=/path/to/movie.mkv"
```

**响应示例**:
```json
{
  "success": true,
  "message": "识别成功",
  "data": {
    "title": "肖申克的救赎",
    "year": 1994,
    "media_type": "movie",
    "quality": "1080p",
    "resolution": "1920x1080",
    "codec": "H.264",
    "raw_title": "The.Shawshank.Redemption.1994.1080p.BluRay.x264"
  },
  "timestamp": "2025-01-XX..."
}
```

### 2. 整理媒体文件

**端点**: `POST /api/v1/media-renamer/organize`

**描述**: 整理单个媒体文件（识别、重命名、移动）

**请求体**:
```json
{
  "source_path": "/path/to/source.mkv",
  "target_base_dir": "/path/to/target",
  "rename_template": "{title} ({year})",
  "move_file": true,
  "download_subtitle": false,
  "subtitle_language": "zh",
  "use_classification": true
}
```

### 3. 批量整理目录

**端点**: `POST /api/v1/media-renamer/organize/directory`

**描述**: 整理目录中的所有媒体文件

**请求体**:
```json
{
  "source_path": "/path/to/source",
  "target_base_dir": "/path/to/target",
  "rename_template": "{title} ({year})",
  "move_file": true,
  "media_extensions": [".mp4", ".mkv"],
  "download_subtitle": false,
  "subtitle_language": "zh",
  "use_classification": true
}
```

---

## 字幕管理API

### 1. 下载字幕

**端点**: `POST /api/v1/subtitle/download`

**描述**: 为媒体文件下载字幕

**参数**:
- `media_file_path` (string, 必需): 媒体文件路径
- `language` (string, 可选): 语言，默认 `zh`
- `save_path` (string, 可选): 保存路径
- `force_download` (boolean, 可选): 是否强制下载，默认 `true`

**示例请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/subtitle/download?media_file_path=/path/to/movie.mkv&language=zh&force_download=true"
```

### 2. 搜索字幕

**端点**: `GET /api/v1/subtitle/search`

**描述**: 搜索字幕（不下载）

**参数**:
- `media_file_path` (string, 必需): 媒体文件路径
- `language` (string, 可选): 语言，默认 `zh`

### 3. 获取字幕列表

**端点**: `GET /api/v1/subtitle`

**描述**: 获取字幕列表（支持分页）

**参数**:
- `media_file_path` (string, 可选): 媒体文件路径过滤
- `language` (string, 可选): 语言过滤
- `page` (integer, 可选): 页码，默认 `1`
- `page_size` (integer, 可选): 每页数量，默认 `20`，最大 `100`

### 4. 获取字幕详情

**端点**: `GET /api/v1/subtitle/{subtitle_id}`

**描述**: 获取字幕详细信息

**路径参数**:
- `subtitle_id` (integer, 必需): 字幕ID

### 5. 删除字幕

**端点**: `DELETE /api/v1/subtitle/{subtitle_id}`

**描述**: 删除字幕

**路径参数**:
- `subtitle_id` (integer, 必需): 字幕ID

---

## 重复文件检测API

### 1. 检测重复文件

**端点**: `POST /api/v1/duplicate-detection/detect`

**描述**: 检测目录中的重复文件

**参数**:
- `directory` (string, 必需): 要检测的目录路径
- `extensions` (array, 可选): 文件扩展名列表，如 `[".mp4", ".mkv"]`
- `use_hash` (boolean, 可选): 是否使用哈希值检测，默认 `true`

**示例请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/duplicate-detection/detect?directory=/path/to/media&use_hash=false" \
  -H "Content-Type: application/json" \
  -d '{"extensions": [".mp4", ".mkv"]}'
```

**响应示例**:
```json
{
  "success": true,
  "message": "检测完成：找到 5 组重复文件，共 12 个文件",
  "data": {
    "total_groups": 5,
    "total_files": 12,
    "groups": [
      {
        "group_id": 1,
        "files": [
          {
            "file_path": "/path/to/file1.mkv",
            "file_size": 2147483648,
            "file_hash": "abc123...",
            "group_id": 1
          },
          {
            "file_path": "/path/to/file2.mkv",
            "file_size": 2147483648,
            "file_hash": "abc123...",
            "group_id": 1
          }
        ],
        "total_size": 4294967296,
        "recommended_keep": "/path/to/file1.mkv"
      }
    ]
  },
  "timestamp": "2025-01-XX..."
}
```

### 2. 比较重复文件质量

**端点**: `POST /api/v1/duplicate-detection/compare`

**描述**: 比较重复文件的质量，推荐保留的文件

**请求体**:
```json
[
  "/path/to/file1.mkv",
  "/path/to/file2.mkv",
  "/path/to/file3.mkv"
]
```

**响应示例**:
```json
{
  "success": true,
  "message": "比较完成",
  "data": {
    "files": [
      {
        "file_path": "/path/to/file1.mkv",
        "file_size": 2147483648,
        "resolution": "1080p",
        "codec": "H.264",
        "quality_score": 85.5
      },
      {
        "file_path": "/path/to/file2.mkv",
        "file_size": 3221225472,
        "resolution": "4K",
        "codec": "H.265",
        "quality_score": 95.0
      }
    ],
    "recommended_keep": {
      "file_path": "/path/to/file2.mkv",
      "file_size": 3221225472,
      "resolution": "4K",
      "codec": "H.265",
      "quality_score": 95.0
    }
  },
  "timestamp": "2025-01-XX..."
}
```

---

## 文件质量比较API

### 1. 比较文件质量

**端点**: `POST /api/v1/quality-comparison/compare`

**描述**: 比较多个文件的质量

**请求体**:
```json
[
  "/path/to/file1.mkv",
  "/path/to/file2.mkv",
  "/path/to/file3.mkv"
]
```

**响应示例**:
```json
{
  "success": true,
  "message": "比较完成",
  "data": {
    "files": [
      {
        "file_path": "/path/to/file1.mkv",
        "file_size": 2147483648,
        "resolution": "1080p",
        "resolution_width": 1920,
        "resolution_height": 1080,
        "codec": "H.264",
        "bitrate": 8000000,
        "quality_score": 85.5
      },
      {
        "file_path": "/path/to/file2.mkv",
        "file_size": 3221225472,
        "resolution": "4K",
        "resolution_width": 3840,
        "resolution_height": 2160,
        "codec": "H.265",
        "bitrate": 25000000,
        "quality_score": 95.0
      }
    ],
    "best_quality": {
      "file_path": "/path/to/file2.mkv",
      "file_size": 3221225472,
      "resolution": "4K",
      "resolution_width": 3840,
      "resolution_height": 2160,
      "codec": "H.265",
      "bitrate": 25000000,
      "quality_score": 95.0
    }
  },
  "timestamp": "2025-01-XX..."
}
```

### 2. 分析文件质量

**端点**: `POST /api/v1/quality-comparison/analyze`

**描述**: 分析单个文件的质量

**参数**:
- `file_path` (string, 必需): 文件路径

**示例请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/quality-comparison/analyze?file_path=/path/to/movie.mkv"
```

**响应示例**:
```json
{
  "success": true,
  "message": "分析完成",
  "data": {
    "file_path": "/path/to/movie.mkv",
    "file_size": 3221225472,
    "resolution": "4K",
    "resolution_width": 3840,
    "resolution_height": 2160,
    "codec": "H.265",
    "bitrate": 25000000,
    "quality_score": 95.0
  },
  "timestamp": "2025-01-XX..."
}
```

---

## 统一响应格式

所有API端点都使用统一的响应格式：

```json
{
  "success": true,
  "message": "操作成功",
  "data": {},
  "timestamp": "2025-01-XX..."
}
```

**错误响应**:
```json
{
  "success": false,
  "error_code": "ERROR_CODE",
  "error_message": "错误信息",
  "timestamp": "2025-01-XX..."
}
```

---

## 认证

大部分API端点需要认证。请在使用API时提供有效的认证令牌。

**Header**:
```
Authorization: Bearer <token>
```

---

## 错误码

- `200`: 成功
- `400`: 请求错误
- `401`: 未认证
- `403`: 无权限
- `404`: 未找到
- `422`: 参数验证错误
- `500`: 服务器错误

---

## 注意事项

1. **文件路径**: 所有文件路径都应该是服务器上的绝对路径
2. **权限**: 确保服务器有读取/写入文件的权限
3. **性能**: 大文件操作可能需要较长时间，请适当设置超时时间
4. **缓存**: 豆瓣API响应会被缓存1小时，以提高性能
5. **限制**: 某些API可能有请求频率限制

---

**最后更新**: 2025-01-XX

