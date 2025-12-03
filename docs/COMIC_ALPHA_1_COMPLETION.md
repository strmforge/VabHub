# COMIC-ALPHA-1 完成文档

## 概述

将漫画从"占位状态"升级为可用功能，完整接入统一收件箱、媒体库根目录、统一预览和前端展示。

## 实现内容

### 一、Comic / ComicFile 模型

**文件**: `app/models/comic.py`

#### Comic（作品级：系列/卷）

**字段设计**:
- `id`: 主键
- `title`: 卷标题或单卷名称（必填）
- `original_title`: 原始标题（可选）
- `author`: 作者/原作（可选）
- `illustrator`: 漫画家/作画（可选）
- `series`: 系列名（可选，索引）
- `volume_index`: 卷号/话数（可选，整数）
- `language`: 语言代码（默认 "zh-CN"）
- `region`: 地区（如 "CN" / "JP" / "US" / "KR"），用于分类
- `publish_year`: 出版年份（可选）
- `tags`: 标签（JSON 字符串或逗号分隔）
- `description`: 简介（可选）
- `cover_url`: 封面图片 URL（可选）
- `extra_metadata`: JSON，用于记录原始文件/站点元数据
- `created_at` / `updated_at`: 时间戳

**索引**:
- `ix_comics_author_title`: (author, title)
- `ix_comics_series_volume`: (series, volume_index)

#### ComicFile（文件级：具体压缩包文件）

**字段设计**:
- `id`: 主键
- `comic_id`: 外键 -> Comic.id（CASCADE 删除）
- `file_path`: 文件绝对路径或相对路径（唯一 + 索引）
- `file_size_bytes` / `file_size_mb`: 文件大小（自动计算）
- `format`: 文件格式（"cbz" / "cbr" / "zip" / "rar" 等）
- `page_count`: 页数（可选，预留字段）
- `source_site_id` / `source_torrent_id` / `download_task_id`: 来源 PT 信息
- `is_deleted`: 软删除标记
- `created_at` / `updated_at`: 时间戳

**自动计算**: `file_size_mb` 在 `__init__` 中自动从 `file_size_bytes` 计算。

### 二、ComicImporter 实现

**文件**: `app/modules/comic/importer.py`

#### 主要行为

1. **文件格式判断** (`is_comic_file`):
   - 支持后缀：`.cbz`, `.cbr`, `.zip`, `.rar`
   - 未来可扩展更多格式

2. **文件名解析** (`parse_filename`):
   - 支持的格式：
     - `系列名_v01.cbz` / `系列名_01.cbz`
     - `系列名 - 第01卷 - 标题.cbz`
     - `系列名 - 01 - 标题.cbz`
     - `系列名 第01卷.cbz`
   - 使用正则匹配卷号：`v?(\d+)`、`第(\d+)卷` 等
   - 解析失败时回退：
     - `series` = 去掉扩展名的文件名
     - `volume_index` = None
     - `title` = None

3. **目标路径构建** (`build_target_path`):
   - 使用 `COMIC_LIBRARY_ROOT` 作为库根
   - 目录结构：
     - **命中分类时**:
       ```
       COMIC_LIBRARY_ROOT / Comics / {分类名} / {系列名} / {卷号:02d} - {标题}.ext
       ```
     - **未命中分类时**:
       ```
       COMIC_LIBRARY_ROOT / Comics / {系列名} / {卷号:02d} - {标题}.ext
       ```
   - 分类通过 `CategoryHelper.get_comic_category()` 获取
   - 文件名清理：去除非法字符 `[<>:"/\\|?*]`
   - 卷号格式化：两位补零（`v01`, `v02`）

4. **导入流程** (`import_comic_from_path`):
   - 验证文件存在且是支持的漫画格式
   - 调用 `parse_filename()` 得到基础元信息
   - 从 `hints` (InboxItem) 中提取额外信息（region, language, tags 等）
   - 使用 `ComicWorkResolver.find_existing_work()` 判断是否复用 Comic
   - 构造 `comic_info` 字典，调用 `CategoryHelper.get_comic_category()` 获取分类
   - 构造目标路径并移动文件
   - 创建 `ComicFile` 记录
   - 返回新路径或 None（错误时）

#### 错误处理

- 文件不存在：记录 warning，返回 None
- 解析失败：回退到"单卷未知信息"模式，不抛异常
- 所有异常被捕获、记录日志，不影响其他文件处理

### 三、InboxRouter 对 comic 的正式接入

**文件**: `app/modules/inbox/router.py`

#### 路由逻辑

对于 `media_type == "comic"`:

1. **禁用检查**:
   - 若 `settings.INBOX_ENABLE_COMIC` 为 False：
     - 返回 `"skipped:comic_disabled"`

2. **启用处理**:
   - 调用 `comic_importer.import_comic_from_path(file_path=item.path, hints=item)`
   - 根据返回值：
     - 返回 `"handled:comic"`（成功）
     - 返回 `"failed:comic_import_error"`（导入失败或异常）

3. **异常处理**:
   - 捕获异常，记录日志，返回 `"failed:comic_import_error"`

#### 完整流程

```
INBOX_ROOT (待整理目录)
  ↓
InboxScanner 扫描文件
  ↓
MediaTypeDetectionService 检测 media_type="comic"
  ↓
InboxRouter.route() 路由到 ComicImporter
  ↓
ComicImporter.import_comic_from_path()
  ↓
解析文件名 → 查找/创建 Comic → 获取分类 → 构建路径
  ↓
移动文件到 COMIC_LIBRARY_ROOT / Comics / [分类] / [系列] / [卷号 - 标题].ext
  ↓
创建 ComicFile 记录
  ↓
返回 "handled:comic"
```

### 四、统一预览 `/api/library/preview` 对 comic 的支持

**文件**: `app/api/library.py`

#### 查询逻辑

- 当 `media_types` 包含 `"comic"` 或默认类型包含 `"comic"` 时：
  - 从 `Comic` 表中按 `created_at` 降序查询前 `fetch_limit` 条
  - 映射为 `LibraryPreviewItem`:
    - `id`: `comic.id`
    - `media_type`: `"comic"`
    - `title`: `comic.title` 或 `comic.series` 或 `"未知标题"`
    - `year`: `comic.publish_year`
    - `cover_url`: `comic.cover_url`
    - `created_at`: `comic.created_at`
    - `extra`: 包含：
      - `series`: `comic.series`
      - `volume_index`: `comic.volume_index`
      - `author`: `comic.author`
      - `illustrator`: `comic.illustrator`
      - `region`: `comic.region`

- 总数统计时，把 `comics` 数量也加进去

### 五、前端 LibraryPreview 中漫画卡片展示

**文件**: 
- `src/pages/LibraryPreview.vue`
- `src/components/library/LibraryPreviewCard.vue`
- `src/types/library.ts`

#### 类型定义更新

- `MediaType`: 添加 `'comic'` 和 `'music'`
- `LibraryPreviewItem.extra`: 添加 comic 相关字段：
  - `volume_index?: number | string`
  - `illustrator?: string`
  - `region?: string`

#### LibraryPreview.vue

- 媒体类型过滤器中，加入 "漫画" 选项：
  - `value: "comic"`
  - `label: "漫画"`
  - `icon: "mdi-book-open-page-variant"`

#### LibraryPreviewCard.vue

- 媒体类型图标和颜色：
  - `icon: "mdi-book-open-page-variant"`
  - `color: "pink"`

- 显示信息：
  - **标题**: `item.title`
  - **系列 + 卷号**: `"{series} · 第 {volume_index} 卷"`（如果有系列）
  - **卷号**: `"第 {volume_index} 卷"`（如果没有系列但有卷号）
  - **作画**: `item.extra.illustrator`（如果有）
  - **地区**: `item.extra.region`（如果有，小字显示）

## 测试

### 测试文件

1. **`tests/test_comic_models.py`**:
   - `test_comic_model_creation`: Comic 模型基本创建
   - `test_comic_file_model_creation`: ComicFile 模型基本创建
   - `test_comic_file_auto_calculate_size`: 自动计算 file_size_mb
   - `test_comic_file_without_size`: 没有文件大小的情况

2. **`tests/test_comic_importer.py`**:
   - `test_is_comic_file`: 文件格式判断
   - `test_parse_filename_simple`: 解析简单文件名
   - `test_parse_filename_with_title`: 解析包含标题的文件名
   - `test_parse_filename_default`: 解析默认文件名
   - `test_import_comic_file_not_exists`: 导入不存在的文件
   - `test_import_comic_invalid_format`: 导入不支持的文件格式

3. **`tests/test_inbox_comic_integration.py`**:
   - `test_comic_routing_disabled`: 漫画处理禁用时的路由
   - `test_comic_routing_enabled`: 漫画处理启用时的路由
   - `test_comic_import_failure`: ComicImporter 返回 None 时的处理
   - `test_comic_import_exception`: ComicImporter 抛出异常时的处理

4. **`tests/test_library_preview_comic.py`**:
   - `test_library_preview_includes_comic`: 统一库预览默认包含漫画
   - `test_library_preview_comic_only`: 只查询漫画类型
   - `test_library_preview_comic_extra_fields`: 漫画项的 extra 字段

**测试用例总数**: 15 个

## 配置要求

### 环境变量

```env
# 漫画库根目录
COMIC_LIBRARY_ROOT=/115/漫画

# 启用漫画处理
INBOX_ENABLE_COMIC=true
```

### category.yaml 配置

确保 `config/category.yaml` 中有 `comic` 段，例如：

```yaml
comic:
  国漫:
    region: 'CN'
  日漫:
    region: 'JP'
  美漫:
    region: 'US'
  韩漫:
    region: 'KR'
```

## 目录结构示例

### 命中分类时

```
/115/漫画/Comics/日漫/进击的巨人/v01 - 第1话.cbz
/115/漫画/Comics/日漫/进击的巨人/v02 - 第2话.cbz
/115/漫画/Comics/国漫/一人之下/v01 - 第1话.cbz
```

### 未命中分类时

```
/115/漫画/Comics/未知系列/v01 - 标题.cbz
/115/漫画/Comics/单卷漫画/标题.cbz
```

## 总结

本次实现完成了漫画从占位状态到完整功能的升级，包括：

1. ✅ **模型定义**: Comic / ComicFile 模型，支持作品级和文件级分离
2. ✅ **导入器实现**: ComicImporter 完整实现，支持文件名解析、分类、路径构建
3. ✅ **InboxRouter 集成**: 正式接入统一收件箱，支持自动识别和导入
4. ✅ **统一预览支持**: `/api/library/preview` 支持查询和展示漫画
5. ✅ **前端展示**: LibraryPreview 页面和卡片组件支持漫画展示
6. ✅ **测试覆盖**: 15 个测试用例，覆盖模型、导入器、路由和预览

漫画功能现已完全可用，可以像其他媒体类型一样通过统一收件箱自动整理和展示。

