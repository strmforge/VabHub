# LIBRARY-CATEGORY-EXTEND-1 实现总结

**任务完成时间**：2025-11-22  
**状态**：✅ 核心功能已完成，测试需要 mock ruamel.yaml

## 任务概述

为 ebook（电子书）、audiobook（有声书）、comic（漫画）补充统一的二级分类规则和目录结构，实现与视频媒体（movie/tv）类似的分类体系。

---

## 一、category.yaml 扩展结构

### 1.1 新增配置段

在 `config/category.yaml` 中新增了三个顶级配置段：

#### **ebook（电子书）**
```yaml
ebook:
  科幻:
    tags: '科幻,硬科幻,软科幻,science-fiction,sci-fi,SF'
  奇幻:
    tags: '奇幻,fantasy,魔幻'
  言情:
    tags: '言情,romance,爱情,恋爱'
  推理:
    tags: '推理,mystery,悬疑,侦探'
  非虚构:
    tags: '非虚构,non-fiction,纪实,传记,历史,哲学'
  轻小说:
    tags: '轻小说,light-novel,ラノベ'
  其他电子书: {}
```

#### **audiobook（有声书）**
```yaml
audiobook:
  科幻有声:
    tags: '科幻,硬科幻,软科幻,science-fiction,sci-fi,SF'
  言情有声:
    tags: '言情,romance,爱情,恋爱'
  推理有声:
    tags: '推理,mystery,悬疑,侦探'
  非虚构有声:
    tags: '非虚构,non-fiction,纪实,传记,历史,哲学'
  其他有声书: {}
```

#### **comic（漫画）**
```yaml
comic:
  日漫:
    region: 'JP'
    language: 'ja'
  国漫:
    region: 'CN'
    language: 'zh,zh-CN'
  美漫:
    region: 'US'
    language: 'en'
  韩漫:
    region: 'KR'
    language: 'ko'
  其他漫画: {}
```

### 1.2 支持的条件字段

#### **ebook / audiobook**
- `tags`: 标签列表（字符串列表或逗号分隔字符串）
  - 匹配逻辑：**至少包含一个**（集合交集）
  - 支持中英文标签混合匹配
  - 可从 `extra_metadata` 中提取
- `language`: 语言代码（如 "zh-CN", "en", "ja" 等）
  - 标准语言代码匹配
  - 可从 `extra_metadata` 中提取

#### **comic**
- `region`: 地区代码（如 "CN", "JP", "US", "KR" 等）
  - 大写匹配
  - 可从 `extra_metadata` 中提取
- `language`: 语言代码
  - 标准语言代码匹配
  - 可从 `extra_metadata` 中提取

### 1.3 配置特点

- **向后兼容**：原有的 `movie`/`tv`/`music` 配置不受影响
- **默认分类**：每个媒体类型都有"其他XXX"作为兜底分类（空规则）
- **顺序匹配**：按 YAML 中的顺序匹配，第一个匹配的分类生效

---

## 二、EBook/Audiobook 目录结构

### 2.1 分类命中时的目录结构

#### **电子书（EBook）**
```
EBOOK_LIBRARY_ROOT/
  Books/
    科幻/                    ← 分类目录（新增）
      刘慈欣/
        地球往事/
          1 - 三体.epub
    言情/
      作者名/
        系列名/
          书名.epub
```

#### **有声书（Audiobook）**
```
EBOOK_LIBRARY_ROOT/          ← 与电子书共享库根
  Audiobooks/
    科幻有声/                ← 分类目录（新增）
      刘慈欣/
        地球往事/
          1 - 三体 - 配音组.mp3
    言情有声/
      作者名/
        系列名/
          卷号 - 书名 - 朗读者.mp3
```

### 2.2 分类未命中时的目录结构

#### **电子书（回退到原有结构）**
```
EBOOK_LIBRARY_ROOT/
  Books/
    其他电子书/              ← 默认分类（如果配置了）
      作者名/
        系列名/
          书名.epub
    或
  Books/                     ← 如果分类返回 None，则不包含分类目录
    作者名/
      系列名/
        书名.epub
```

#### **有声书（回退到原有结构）**
```
EBOOK_LIBRARY_ROOT/
  Audiobooks/
    其他有声书/              ← 默认分类（如果配置了）
      作者名/
        系列名/
          卷号 - 书名 - 朗读者.mp3
    或
  Audiobooks/                ← 如果分类返回 None，则不包含分类目录
    作者名/
      系列名/
        卷号 - 书名 - 朗读者.mp3
```

### 2.3 实现细节

- **EBookImporter.build_target_path()**：
  - 新增 `ebook` 参数（可选）
  - 如果传入 `ebook` 对象，调用 `CategoryHelper.get_ebook_category()` 获取分类
  - 如果返回分类名称，在 `Books/` 下增加分类目录
  - 如果返回 `None`，保持原有结构（不包含分类目录）

- **AudiobookImporter.build_target_path()**：
  - 新增 `ebook` 和 `audiobook_file` 参数（可选）
  - 如果传入 `ebook` 对象，调用 `CategoryHelper.get_audiobook_category()` 获取分类
  - 如果返回分类名称，在 `Audiobooks/` 下增加分类目录
  - 如果返回 `None`，保持原有结构

---

## 三、与 Unified Inbox + Importer 的关系

### 3.1 完整流程

```
1. 文件落入 INBOX_ROOT（统一待整理目录）
   ↓
2. InboxScanner 扫描文件
   ↓
3. attach_pt_hints() 附加 PT 下载任务信息（可选）
   ↓
4. MediaTypeDetectionService 识别媒体类型
   - 使用 PTCategoryDetector（优先）
   - 使用 ExtensionDetector（兜底）
   - 返回 media_type: "ebook" / "audiobook" / "comic"
   ↓
5. InboxRouter 根据 media_type 路由
   - ebook → EBookImporter
   - audiobook → AudiobookImporter
   - comic → ComicImporter（占位）
   ↓
6. Importer 处理
   a) 创建/查找 EBook 作品记录（Work-level）
   b) 调用 build_target_path() 构建目标路径
      - media_type 决定库根路径（EBOOK_LIBRARY_ROOT）
      - CategoryHelper 决定二级分类目录（Books/科幻/）
      - 作品信息决定后续层级（作者/系列/书名）
   c) 移动文件到目标路径
   d) 创建 EBookFile / AudiobookFile 记录
```

### 3.2 两级路径决策

1. **第一级：media_type → 库根路径**
   - `ebook` → `EBOOK_LIBRARY_ROOT`
   - `audiobook` → `EBOOK_LIBRARY_ROOT`（与电子书共享）
   - `comic` → `COMIC_LIBRARY_ROOT`（新增配置）

2. **第二级：分类规则 → 分类目录**
   - 从 `EBook.tags` / `EBook.language` / `EBook.extra_metadata` 提取信息
   - 调用 `CategoryHelper.get_ebook_category()` / `get_audiobook_category()`
   - 如果返回分类名称，在 `Books/` 或 `Audiobooks/` 下增加分类目录
   - 如果返回 `None`，保持原有结构（不包含分类目录）

### 3.3 示例

**场景：从 PT 站点下载的科幻小说**

1. 文件：`三体.epub` 落入 `INBOX_ROOT`
2. PT hint：`source_category="电子书"`, `source_tags=["科幻"]`
3. 识别：`media_type="ebook"`
4. 路由：`EBookImporter.import_ebook_from_file()`
5. 创建 EBook：`title="三体"`, `author="刘慈欣"`, `tags="科幻,硬科幻"`
6. 分类：`CategoryHelper.get_ebook_category()` → `"科幻"`
7. 路径：`EBOOK_LIBRARY_ROOT / Books / 科幻 / 刘慈欣 / 三体.epub`

---

## 四、ComicImporter 占位实现

### 4.1 当前状态

- **位置**：`app/modules/comic/importer.py`
- **状态**：占位实现（`import_comic_from_path()` 返回 `None`，仅记录警告日志）
- **配置**：已添加 `COMIC_LIBRARY_ROOT` 配置项（默认：`./data/library/comics`）

### 4.2 InboxRouter 集成

- `media_type="comic"` 时：
  - 检查 `INBOX_ENABLE_COMIC` 开关
  - 如果启用，返回 `"skipped:comic_not_implemented"`（占位）
  - 如果禁用，返回 `"skipped:comic_disabled"`

### 4.3 未来扩展计划（COMIC-ALPHA-1）

1. **数据模型**：
   - 创建 `Comic` 模型（作品层）
   - 创建 `ComicFile` 模型（文件层）
   - 支持 CBZ/CBR 等格式

2. **导入逻辑**：
   - 解析文件名（系列名/卷号/标题）
   - 识别元数据（地区/语言/标签）
   - 调用 `CategoryHelper.get_comic_category()` 获取分类
   - 构建路径：`COMIC_LIBRARY_ROOT / Comics / 日漫 / 系列名 / 卷号 - 标题.cbz`
   - 移动文件并创建数据库记录

3. **分类支持**：
   - 已实现 `CategoryHelper.get_comic_category()`
   - 支持 `region` 和 `language` 匹配
   - 配置已在 `category.yaml` 中定义

---

## 五、技术实现要点

### 5.1 CategoryHelper 扩展

- **新增方法**：
  - `get_ebook_category(ebook: Dict[str, Any]) -> Optional[str]`
  - `get_audiobook_category(audiobook: Dict[str, Any]) -> Optional[str]`
  - `get_comic_category(comic: Dict[str, Any]) -> Optional[str]`
  - `_get_category_with_tags()`：支持 tags 的"至少包含一个"匹配

- **匹配逻辑**：
  - `tags` 字段：集合交集匹配（至少包含一个）
  - `region` / `language` 字段：标准字符串匹配（支持逗号分隔）

### 5.2 Importer 修改

- **EBookImporter**：
  - `build_target_path()` 新增 `ebook` 参数
  - 在 `import_ebook_from_file()` 中传入 `ebook` 对象

- **AudiobookImporter**：
  - `build_target_path()` 新增 `ebook` 和 `audiobook_file` 参数
  - 在 `import_audiobook_from_file()` 中传入 `ebook` 对象

### 5.3 向后兼容

- **不破坏现有功能**：
  - 如果 `build_target_path()` 不传入 `ebook` 对象，保持原有结构
  - 如果分类返回 `None`，保持原有结构
  - 原有的 `movie`/`tv`/`music` 分类不受影响

---

## 六、测试覆盖

### 6.1 测试文件

- `tests/test_category_helper_ebook.py`：测试 `CategoryHelper` 的电子书分类逻辑
- `tests/test_ebook_importer_category_paths.py`：测试 `EBookImporter` 的路径构建
- `tests/test_audiobook_importer_category_paths.py`：测试 `AudiobookImporter` 的路径构建

### 6.2 测试场景

- ✅ 通过标签匹配分类（科幻/言情/推理等）
- ✅ 从字符串解析标签
- ✅ 从 `extra_metadata` 中提取标签
- ✅ 没有标签时返回默认分类
- ✅ 无匹配标签时返回默认分类
- ✅ 命中分类时路径包含分类目录
- ✅ 未命中分类时保持原有结构
- ✅ 不传入 `ebook` 对象时保持原有结构
- ✅ 带系列和分类的完整路径

---

## 七、配置示例

### 7.1 环境变量

```bash
# 电子书库根目录
EBOOK_LIBRARY_ROOT=/data/ebooks

# 漫画库根目录（新增）
COMIC_LIBRARY_ROOT=/data/comics

# 统一收件箱开关
INBOX_ENABLE_EBOOK=true
INBOX_ENABLE_AUDIOBOOK=true
INBOX_ENABLE_COMIC=false  # 暂未实现，保持 false
```

### 7.2 category.yaml 自定义

用户可以根据需要修改 `config/category.yaml`，添加自定义分类：

```yaml
ebook:
  网络小说:
    tags: '网络小说,网文,起点,晋江'
  经典文学:
    tags: '经典,名著,文学'
  其他电子书: {}
```

---

## 八、总结

本次实现为 ebook/audiobook/comic 补充了统一的二级分类体系，实现了：

1. ✅ **配置驱动**：通过 `category.yaml` 统一管理分类规则
2. ✅ **灵活匹配**：支持 tags 的"至少包含一个"匹配，适应多种标签格式
3. ✅ **向后兼容**：不破坏现有功能，未命中分类时保持原有结构
4. ✅ **扩展性强**：ComicImporter 已预留接口，后续可快速实现

**目录结构示例**：
- 命中分类：`EBOOK_LIBRARY_ROOT / Books / 科幻 / 刘慈欣 / 地球往事 / 1 - 三体.epub`
- 未命中分类：`EBOOK_LIBRARY_ROOT / Books / 刘慈欣 / 地球往事 / 1 - 三体.epub`

**与 unified inbox 的集成**：
- 待整理 → `media_type` 决定库根路径
- 库根下 → 分类规则决定 `Books/科幻/` 这一层级
- 后续层级 → 由作品信息（作者/系列/书名）决定

---

## 九、音乐（Music）支持（MUSIC-ALPHA-1）

### 9.1 概述

在现有"统一 Inbox + 分类 YAML + 媒体库根目录 + Organizer"体系之上，为**音乐（music）**补齐完整流水线。

### 9.2 配置

#### **环境变量**
```bash
# 音乐库根目录（用户可设置为任意路径，如 /115/音乐、/mnt/media/Music 等）
MUSIC_LIBRARY_ROOT=/115/音乐

# 统一收件箱音乐开关
INBOX_ENABLE_MUSIC=true
```

#### **category.yaml 配置**
```yaml
music:
  华语音乐:
    original_language: 'zh,cn'
  欧美音乐:
    original_language: 'en'
  日韩音乐:
    original_language: 'ja,ko'
  其他音乐: {}
```

### 9.3 数据模型

#### **Music（作品/专辑级）**
- `id`: 主键
- `title`: 标题（一般为专辑名或单曲名）
- `artist`: 艺术家/歌手（必填）
- `album`: 专辑名（可选）
- `album_artist`: 专辑艺术家（可选）
- `genre`: 风格（可选）
- `language`: 语言代码（可选）
- `year`: 年份（可选）
- `tags`: 标签（JSON 字符串或逗号分隔）
- `extra_metadata`: 附加元数据（JSON）

#### **MusicFile（文件级）**
- `id`: 主键
- `music_id`: 外键 -> Music.id
- `file_path`: 唯一路径
- `file_size_bytes` / `file_size_mb`: 文件大小（自动计算）
- `format`: mp3/flac/ape/m4a 等
- `duration_seconds`: 时长（秒）
- `bitrate_kbps` / `sample_rate_hz` / `channels`: 音频技术参数
- `track_number`: 轨道号（可选）
- `disc_number`: 碟号（可选）
- `source_site_id` / `source_torrent_id` / `download_task_id`: 来源信息

### 9.4 目录结构

#### **命中分类时**
```
MUSIC_LIBRARY_ROOT/
  华语音乐/                    ← 分类目录（YAML 配置）
    周杰伦/
      七里香/
        01 - 我的地盘.mp3
  欧美音乐/
    Taylor Swift/
      1989/
        03 - Style.flac
  日韩音乐/
    米津玄師/
      单曲/                     ← 无专辑时使用"单曲"目录
        或某张专辑/
          ...
```

#### **未命中分类时**
```
MUSIC_LIBRARY_ROOT/
  未知歌手/                     ← 如果无法分类，仍按 artist/album 组织
    专辑名/
      01 - 歌名.mp3
```

### 9.5 导入流程

1. **文件落入 INBOX_ROOT**
2. **MediaTypeDetectionService 识别**：
   - 优先使用 `PTCategoryDetector`（根据 PT 站点分类/标签）
   - 回退到 `ExtensionDetector`（根据文件扩展名：.mp3, .flac, .m4a 等）
3. **InboxRouter 路由**：
   - `media_type="music"` → `MusicImporter.import_music_from_path()`
4. **MusicImporter 处理**：
   - 使用 `mutagen` 解析音频元数据（artist, album, title, track_number 等）
   - 如果元数据解析失败，从文件名解析（支持 "歌手 - 歌名.mp3" 等格式）
   - 使用 `MusicWorkResolver` 查找或创建 Music 作品记录
   - 调用 `CategoryHelper.get_music_category()` 获取分类（基于 language/genre）
   - 构建目标路径：`MUSIC_LIBRARY_ROOT / 分类 / artist / album / track_number - title.ext`
   - 移动文件并创建 MusicFile 记录

### 9.6 统一库预览支持

- `/api/library/preview` 默认包含 `music` 类型
- 支持 `media_types=music` 过滤
- `extra` 字段包含：`artist`, `album`, `genre`, `album_artist`

### 9.7 最小配置示例

```bash
# .env
INBOX_ROOT=/video/待整理
INBOX_ENABLE_MUSIC=true
MUSIC_LIBRARY_ROOT=/115/音乐
```

---

## 十、后续优化建议

1. **元数据增强**：在导入时自动从 ISBN/文件名/PT 信息中提取更准确的 tags
2. **分类可视化**：在管理界面中展示分类统计和预览
3. **批量重分类**：支持对已导入的电子书/有声书进行批量重新分类
4. **ComicImporter 完整实现**：在 COMIC-ALPHA-1 任务中完成漫画导入功能
5. **音乐封面支持**：从音频文件或外部 API 获取专辑封面
6. **音乐元数据增强**：集成 MusicBrainz 等元数据源，自动补全专辑信息

