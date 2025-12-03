# WORK-HUB-PLUS-1 完成文档

## 概述

在现有的 Work Hub 基础上，扩展 `/api/works/{ebook_id}` 和 WorkDetail.vue 页面，让"作品详情"变成一个"作品宇宙面板"，额外展示相关视频改编（电影/剧集/动漫/短剧）和相关音乐（OST/主题曲/概念专辑等）。

## 实现内容

### 一、WorkDetailResponse 扩展后的完整结构

**文件**: `app/schemas/work.py`

```python
class WorkDetailResponse(BaseModel):
    """作品详情响应"""
    ebook: WorkEBook
    ebook_files: List[WorkEBookFile]
    audiobooks: List[WorkAudiobookFile]
    comics: List[WorkComic]
    comic_files: List[WorkComicFile]
    videos: List[WorkVideoItem] = []  # 相关视频改编（新增）
    music: List[WorkMusicItem] = []  # 相关音乐（新增）
```

#### WorkVideoItem Schema

```python
class WorkVideoItem(BaseModel):
    """作品相关视频改编"""
    id: int
    media_type: str  # "movie" | "tv" | "anime" | "short_drama"
    title: str
    original_title: Optional[str] = None
    year: Optional[int] = None
    season_index: Optional[int] = None  # tv/anime 用
    poster_url: Optional[str] = None
    rating: Optional[float] = None
    source_site_id: Optional[int] = None
    created_at: datetime
```

#### WorkMusicItem Schema

```python
class WorkMusicItem(BaseModel):
    """作品相关音乐"""
    id: int
    title: str
    artist: Optional[str] = None
    album: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    cover_url: Optional[str] = None
    created_at: datetime
```

### 二、相关视频/相关音乐的匹配规则

#### 相关视频改编（videos）匹配规则

**文件**: `app/api/work.py` - `get_work_detail()`

**匹配目标**: `Media` 表

**匹配规则（启发式）**:

1. **优先使用 `ebook.series` 作为"作品 IP 名"**:
   - 如果 `ebook.series` 非空：
     - `Media.title ilike "%{ebook.series}%"`
     - `Media.original_title ilike "%{ebook.series}%"`
   
2. **否则使用 `ebook.title`**:
   - `Media.title ilike "%{ebook.title}%"`
   - `Media.original_title ilike "%{ebook.title}%"`

3. **媒体类型过滤**:
   - 只选取 `media_type in ("movie", "tv", "anime", "short_drama")`
   - 限制总数：最多 30 条
   - 排序：`created_at DESC`

4. **字段映射**:
   - `rating`: 从 `Media.extra_metadata["rating"]` 提取（如果存在）
   - `season_index`: 从 `Media.extra_metadata["season_index"]` 提取（如果存在）
   - `poster_url`: 直接使用 `Media.poster_url`

**示例**:
- EBook: `series="三体"` → 匹配 Media: `title="三体"` 或 `original_title="The Three-Body Problem"`
- EBook: `title="流浪地球"`（无 series）→ 匹配 Media: `title="流浪地球"` 或 `original_title="The Wandering Earth"`

#### 相关音乐（music）匹配规则

**文件**: `app/api/work.py` - `get_work_detail()`

**匹配目标**: `Music` 表（作品级）

**匹配规则（启发式）**:

1. **构造候选关键字**:
   - `ebook.title`
   - `ebook.series`（如果存在）
   - `ebook.author`（如果存在）

2. **在 Music 表中做 ilike 匹配**:
   - `Music.title ilike "%{keyword}%"`
   - `Music.album ilike "%{keyword}%"`
   - `Music.tags ilike "%{keyword}%"`
   
   任何一个关键字出现在 `title`/`album`/`tags` 中，就认为"潜在关联"

3. **限制和排序**:
   - 限制总数：最多 50 条
   - 排序：`created_at DESC`

4. **字段映射**:
   - `cover_url`: 从 `Music.extra_metadata["cover_url"]` 提取（如果存在），否则为 `None`

**示例**:
- EBook: `title="测试电子书"`, `series="测试系列"` → 匹配 Music: `title="测试系列 OST"` 或 `album="测试电子书原声带"`

### 三、UI 展示

**文件**: `src/pages/WorkDetail.vue`

#### 相关视频改编区块

- **显示条件**: `workDetail.videos && workDetail.videos.length > 0`
- **标题**: "相关影视改编"
- **提示文案**: "根据作品标题/系列名自动匹配，结果仅供参考，可能包含误匹配。"
- **展示形式**: `v-data-table`
  - **列**:
    - 类型（media_type）：带图标和颜色的 chip（电影/剧集/动漫/短剧）
    - 标题（title + original_title）
    - 年份（year）
    - 评分（rating）：带星星图标
    - 海报（poster_url）：缩略图显示
  - **样式**:
    - 电影：`primary`（蓝色）+ `mdi-movie`
    - 剧集：`info`（青色）+ `mdi-television`
    - 动漫：`purple`（紫色）+ `mdi-animation`
    - 短剧：`indigo`（靛蓝）+ `mdi-television-classic`

#### 相关音乐区块

- **显示条件**: `workDetail.music && workDetail.music.length > 0`
- **标题**: "相关音乐 / OST"
- **提示文案**: "根据作品标题/系列名/作者自动匹配，结果仅供参考。"
- **展示形式**: `v-data-table`
  - **列**:
    - 曲目名（title）
    - 艺术家（artist）：chip 显示
    - 专辑名（album）
    - 年份（year）
    - 风格（genre）：chip 显示（teal 颜色）

### 四、实现细节

#### 性能优化

- **避免 N+1 查询**:
  - 视频匹配：使用 `OR` + `ilike` 批量查询，一次查询完成
  - 音乐匹配：使用 `OR` + `ilike` 批量查询，一次查询完成
  - 总计：最多 2 次额外查询（视频 + 音乐）

- **查询限制**:
  - 视频：最多 30 条
  - 音乐：最多 50 条
  - 避免返回过多数据影响性能

#### 向后兼容

- **新字段默认为空列表**: `videos: List[WorkVideoItem] = []`, `music: List[WorkMusicItem] = []`
- **前端条件渲染**: 只有当 `videos.length > 0` 或 `music.length > 0` 时才显示对应区块
- **旧前端兼容**: 如果旧前端不访问 `videos`/`music` 字段，不会报错

#### 弱关联说明

- **视频和音乐都是"弱关联"**:
  - 基于启发式匹配（series/title/author），允许有误差
  - 前端会显示提示文案，告知用户可能存在误匹配
  - 与"强关联"（ebook/files/audiobook/comic）区分开

### 五、测试

#### 测试文件

**`tests/test_work_detail_plus.py`**: 5 个测试用例

1. **`test_work_detail_videos_by_series_match`**: 通过 series 匹配相关视频
   - 创建 EBook: `series="三体"`
   - 创建 Media: `title="三体"`, `media_type="movie"`
   - 验证 `videos` 列表包含匹配的视频

2. **`test_work_detail_videos_by_title_match`**: 通过 title 匹配相关视频（没有 series）
   - 创建 EBook: `title="流浪地球"`（无 series）
   - 创建 Media: `title="流浪地球"`, `original_title="The Wandering Earth"`
   - 验证 `videos` 列表包含匹配的视频

3. **`test_work_detail_music_by_title_or_series`**: 通过 title/series 匹配相关音乐
   - 创建 EBook: `title="测试电子书"`, `series="测试系列"`
   - 创建 Music: `title="测试系列 OST"` 或 `album="测试电子书原声带"`
   - 验证 `music` 列表包含匹配的音乐

4. **`test_work_detail_videos_and_music_empty_when_no_match`**: 无任何匹配数据时，videos / music 均为空列表
   - 创建 EBook（没有匹配的视频/音乐）
   - 验证 `videos` 和 `music` 都是空列表

5. **`test_work_detail_videos_media_type_filter`**: 只匹配指定类型的视频（movie/tv/anime/short_drama）
   - 创建匹配的 Media（movie 类型）
   - 验证 `videos` 列表中的 `media_type` 都是允许的类型

**测试状态**: ✅ 全部通过（5 passed）

### 六、前端类型定义

**文件**: `src/types/work.ts`

```typescript
export interface WorkVideoItem {
  id: number
  media_type: string // "movie" | "tv" | "anime" | "short_drama"
  title: string
  original_title?: string | null
  year?: number | null
  season_index?: number | null
  poster_url?: string | null
  rating?: number | null
  source_site_id?: number | null
  created_at: string
}

export interface WorkMusicItem {
  id: number
  title: string
  artist?: string | null
  album?: string | null
  year?: number | null
  genre?: string | null
  cover_url?: string | null
  created_at: string
}

export interface WorkDetailResponse {
  ebook: WorkEBook
  ebook_files: WorkEBookFile[]
  audiobooks: WorkAudiobookFile[]
  comics: WorkComic[]
  comic_files: WorkComicFile[]
  videos: WorkVideoItem[]  // 新增
  music: WorkMusicItem[]  // 新增
}
```

### 七、兼容性

#### 向后兼容

- **新字段默认为空列表**: 不影响现有 API 行为
- **前端条件渲染**: 只有当有数据时才显示对应区块
- **旧前端兼容**: 如果旧前端不访问 `videos`/`music` 字段，不会报错

#### 性能影响

- **查询次数**: 最多 2 次额外查询（视频 + 音乐）
- **查询类型**: 使用 `OR` + `ilike` 批量查询，数据库可以优化执行计划
- **结果限制**: 视频最多 30 条，音乐最多 50 条，避免返回过多数据

## 总结

本次实现完成了在 Work Hub 中扩展"作品宇宙面板"的功能：

1. ✅ **Schema 扩展**: 新增 `WorkVideoItem` 和 `WorkMusicItem`，在 `WorkDetailResponse` 中添加 `videos` 和 `music` 字段
2. ✅ **视频匹配**: 基于 `series`/`title` 的启发式匹配，支持 movie/tv/anime/short_drama
3. ✅ **音乐匹配**: 基于 `title`/`series`/`author` 的启发式匹配，在 `title`/`album`/`tags` 中搜索
4. ✅ **前端 UI**: 在 WorkDetail.vue 中添加"相关影视改编"和"相关音乐 / OST"两个区块
5. ✅ **性能优化**: 避免 N+1 查询，使用批量查询
6. ✅ **向后兼容**: 新字段默认为空列表，不影响现有功能
7. ✅ **测试覆盖**: 5 个测试用例，全部通过

用户现在可以在 `/works/{ebook_id}` 页面查看作品的完整"宇宙"，包括电子书、有声书、漫画、相关视频改编和相关音乐，形成一个完整的作品中心视图。

