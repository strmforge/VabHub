# SMART-HEALTH-LIBRARY-1 完成文档

## 概述

在现有的 `/api/smart/health` 返回值中，新增一个 `library` 区块，汇总各类媒体库的核心状态，包括各媒体类型的总数量、配置的库根目录、多形态作品统计和简单的 warning 提示。

## 实现内容

### 一、features.library 完整 JSON 结构

**文件**: `app/api/smart_health.py`

```json
{
  "ok": true,
  "features": {
    "library": {
      "enabled": true,
      "roots": {
        "movie": "./data/library/movie",
        "tv": "./data/library/tv",
        "anime": "./data/library/anime",
        "short_drama": null,
        "ebook": "./data/library/ebook",
        "comic": "./data/library/comic",
        "music": "./data/library/music"
      },
      "counts": {
        "movie": 123,
        "tv": 456,
        "anime": 78,
        "ebook": 89,
        "audiobook": 10,
        "comic": 5,
        "music": 30
      },
      "multi_format_works": {
        "ebook_only": 80,
        "ebook_with_audiobook": 6,
        "ebook_with_comic": 2,
        "ebook_with_both": 1
      },
      "pending_warning": null
    }
  }
}
```

### 二、字段含义说明

#### enabled

- **类型**: `bool`
- **含义**: 媒体库是否启用
- **计算逻辑**: 只要有任意一个 `library_root` 非空` 就视为启用
- **示例**: `true`（如果至少有一个库根目录配置了）

#### roots

- **类型**: `Dict[str, Optional[str]]`
- **含义**: 各媒体类型的库根目录配置
- **字段**:
  - `movie`: `MOVIE_LIBRARY_ROOT`
  - `tv`: `TV_LIBRARY_ROOT`
  - `anime`: `ANIME_LIBRARY_ROOT`
  - `short_drama`: `SHORT_DRAMA_LIBRARY_ROOT`（可选，可能为 `null`）
  - `ebook`: `EBOOK_LIBRARY_ROOT`
  - `comic`: `COMIC_LIBRARY_ROOT`（可选，可能为 `null`）
  - `music`: `MUSIC_LIBRARY_ROOT`（可选，可能为 `null`）
- **说明**: 允许某些为 `null`（例如 comic/music 没配置）

#### counts

- **类型**: `Dict[str, int]`
- **含义**: 各媒体类型的总数量统计
- **字段说明**:
  - `movie`: 统计 `Media` 表中 `media_type == "movie"` 的记录数（作品级）
  - `tv`: 统计 `Media` 表中 `media_type == "tv"` 的记录数（作品级）
  - `anime`: 统计 `Media` 表中 `media_type == "anime"` 的记录数（作品级）
  - `ebook`: 统计 `EBook` 表的记录数（作品级）
  - `audiobook`: 统计 `AudiobookFile` 表中 `is_deleted == False` 的记录数（**文件级**）
  - `comic`: 统计 `Comic` 表的记录数（**作品级**）
  - `music`: 统计 `Music` 表的记录数（**作品级**）

**注意**: 
- `audiobook` 统计的是文件级（`AudiobookFile`），因为一个 EBook 可能有多个 AudiobookFile
- `comic` 和 `music` 统计的是作品级（`Comic` 和 `Music`）

#### multi_format_works

- **类型**: `Dict[str, int]`
- **含义**: 多形态作品统计（以 EBook 为作品中心）
- **字段说明**:
  - `ebook_only`: 只有 EBook，没有对应的 Audiobook / Comic
  - `ebook_with_audiobook`: 有至少一个 `AudiobookFile.ebook_id == ebook.id`
  - `ebook_with_comic`: 通过与 LIBRARY-WORK-BADGE-1 一致的匹配逻辑，存在至少一条相关 Comic
  - `ebook_with_both`: 既有 audiobook 又有 comic 的 ebook 数量

**统计口径**:
- 以 EBook 为作品中心
- 使用与 LIBRARY-WORK-BADGE-1 一致的匹配逻辑：
  - **Audiobook 匹配**: 基于外键 `AudiobookFile.ebook_id == ebook.id`（100% 准确）
  - **Comic 匹配**: 启发式匹配
    - 优先匹配 `series`：如果 `ebook.series` 不为空，使用 `Comic.series ilike "%{ebook.series}%"`
    - 回退到 `title` 匹配：如果没有 `series`，使用 `Comic.title ilike "%{ebook.title}%"`
    - 使用双向包含匹配（更宽松）

**一致性公式**:
```
ebook_only + ebook_with_audiobook + ebook_with_comic + ebook_with_both == 总 ebook 数
```

#### pending_warning

- **类型**: `Optional[str]`
- **含义**: 警告信息
- **可能的值**:
  - `"empty_library"`: 当 `sum(counts.values()) == 0` 时（整个库为空）
  - `null`: 其他情况（当前版本只实现空库警告，后续可扩展）

### 三、实现细节

#### Helper 函数

**`compute_multi_format_work_stats(db: AsyncSession) -> Dict[str, int]`**

- **位置**: `app/api/smart_health.py`
- **功能**: 计算多形态作品统计，复用 LIBRARY-WORK-BADGE-1 中的匹配逻辑
- **性能优化**:
  - 避免 N+1 查询
  - 批量查询所有 EBook（不限制数量，因为统计需要全量数据）
  - 使用 `IN` 查询批量获取 AudiobookFile
  - 使用 `OR` + `ilike` 批量查询 Comic
  - 在 Python 中进行分组聚合

**`get_library_health(settings, db: AsyncSession) -> Dict[str, Any]`**

- **位置**: `app/api/smart_health.py`
- **功能**: 获取媒体库的健康状态信息
- **查询次数**: 最多 7 次（每个媒体类型一次 `COUNT` 查询）+ 多形态统计（3 次查询）= 总计最多 10 次查询
- **性能**: 所有查询都是简单的 `COUNT` 或批量查询，不会出现 N+1 问题

#### 查询优化

- **counts 统计**: 每个媒体类型使用一次 `COUNT` 查询，共 7 次
- **multi_format_works 统计**: 
  - 1 次查询所有 EBook（`id, series, title`）
  - 1 次批量查询 AudiobookFile（`IN` 查询）
  - 1 次批量查询 Comic（`OR` + `ilike`）
  - 在 Python 中分组聚合
- **总计**: 最多 10 次查询，不随数据量线性增长

### 四、测试

#### 测试文件

**`tests/test_smart_health_library.py`**: 5 个测试用例

1. **`test_library_health_basic_structure`**: 测试基本结构
   - 验证 `features.library` 存在
   - 验证字段齐全：`enabled` / `roots` / `counts` / `multi_format_works` / `pending_warning`
   - 验证 `roots` 结构（包含所有预期的键）
   - 验证 `counts` 结构（包含所有预期的键）
   - 验证 `multi_format_works` 结构（包含所有预期的键）

2. **`test_library_health_counts_non_negative`**: 测试 counts 字段都是 >= 0 的整数
   - 验证所有 `counts` 字段都是整数
   - 验证所有 `counts` 字段都 >= 0

3. **`test_library_health_empty_library_warning`**: 测试空库时 `pending_warning == "empty_library"`
   - 验证当 `sum(counts.values()) == 0` 时，`pending_warning == "empty_library"`
   - 验证当库不为空时，`pending_warning` 为 `null` 或不等于 `"empty_library"`

4. **`test_library_health_multi_format_stats_consistent`**: 测试多形态作品统计的一致性
   - 创建测试数据（ebook1 只有电子书，ebook2 有有声书和漫画）
   - 验证 `ebook_only + ebook_with_audiobook + ebook_with_comic + ebook_with_both == 总 ebook 数`
   - 验证至少有一个 `ebook_only`
   - 验证至少有一个 `ebook_with_both`

5. **`test_library_health_counts_accurate`**: 测试 counts 统计的准确性
   - 创建各种类型的测试数据（movie/tv/anime/ebook/audiobook/comic/music）
   - 验证 `counts` 至少包含我们创建的数据

**测试状态**: ✅ 全部通过（5 passed）

### 五、兼容性

#### 向后兼容

- 新增 `features.library` 字段，不影响现有字段结构
- 所有字段都是新增的，不会破坏现有 API 行为
- 如果某些库根目录未配置，返回 `null`，前端可以安全处理

#### 性能影响

- **查询次数**: 最多 10 次查询（7 次 COUNT + 3 次多形态统计）
- **查询类型**: 都是简单的 `COUNT` 或批量查询，数据库可以优化执行计划
- **内存占用**: 多形态统计需要加载所有 EBook 的 `id, series, title`，但只加载必要字段，内存占用可控

### 六、使用示例

#### 调用 API

```bash
GET /api/smart/health
```

#### 响应示例

```json
{
  "ok": true,
  "features": {
    "local_intel": { ... },
    "external_indexer": { ... },
    "ai_site_adapter": { ... },
    "ebook_metadata": { ... },
    "inbox": { ... },
    "library": {
      "enabled": true,
      "roots": {
        "movie": "./data/library/movie",
        "tv": "./data/library/tv",
        "anime": "./data/library/anime",
        "short_drama": null,
        "ebook": "./data/library/ebook",
        "comic": "./data/library/comic",
        "music": "./data/library/music"
      },
      "counts": {
        "movie": 123,
        "tv": 456,
        "anime": 78,
        "ebook": 89,
        "audiobook": 10,
        "comic": 5,
        "music": 30
      },
      "multi_format_works": {
        "ebook_only": 80,
        "ebook_with_audiobook": 6,
        "ebook_with_comic": 2,
        "ebook_with_both": 1
      },
      "pending_warning": null
    }
  }
}
```

## 总结

本次实现完成了在 `/api/smart/health` 中新增 `library` 区块的功能：

1. ✅ **基本结构**: 新增 `features.library` 字段，包含 `enabled` / `roots` / `counts` / `multi_format_works` / `pending_warning`
2. ✅ **库根目录**: 从 settings 中读取各媒体类型的库根目录配置
3. ✅ **数量统计**: 统计各媒体类型的总数量（7 种类型，使用作品级或文件级统计）
4. ✅ **多形态统计**: 以 EBook 为作品中心，统计多形态作品（复用 LIBRARY-WORK-BADGE-1 的匹配逻辑）
5. ✅ **警告提示**: 当整个库为空时，给出 `"empty_library"` 警告
6. ✅ **性能优化**: 避免 N+1 查询，最多 10 次查询完成所有统计
7. ✅ **向后兼容**: 不影响现有 API 行为
8. ✅ **测试覆盖**: 5 个测试用例，全部通过

用户现在可以在 `/api/smart/health` 中查看媒体库的核心状态，包括各媒体类型的总数量、配置的库根目录、多形态作品统计和简单的 warning 提示。

