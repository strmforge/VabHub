# LIBRARY-WORK-BADGE-1 完成文档

## 概述

在统一媒体库预览接口 `/api/library/preview` 返回的每个 item 上，补充「作品形态概览」字段，让前端可以在 `/library` 页面一眼看出这个作品有哪些形态（电子书、有声书、漫画、音乐）。

## 实现内容

### 一、work_formats 字段结构

**文件**: `app/schemas/library.py`

#### WorkFormats Schema

```python
class WorkFormats(BaseModel):
    """作品形态概览"""
    has_ebook: bool = False
    has_audiobook: bool = False
    has_comic: bool = False
    has_music: bool = False  # 预留，当前暂不实现
```

#### LibraryPreviewItem 扩展

```python
class LibraryPreviewItem(BaseModel):
    ...
    work_formats: Optional[WorkFormats] = None  # 作品形态概览（仅对 ebook 类型有意义）
```

**注意**: 
- 此字段仅对 `media_type == "ebook"` 的 item 填充
- 对其他类型（movie/tv/anime/music/comic）返回 `None` 或不返回

### 二、后端计算逻辑

**文件**: `app/api/library.py` - `get_library_preview()`

#### 计算流程

1. **收集本页所有 ebook_ids**:
   ```python
   ebook_ids = [ebook.id for ebook in ebook_list]
   ```

2. **批量查询 AudiobookFile**（避免 N+1）:
   ```python
   # 使用 IN 查询，一次性获取所有关联的 ebook_id
   audiobook_stmt = (
       select(AudiobookFile.ebook_id)
       .where(
           AudiobookFile.ebook_id.in_(ebook_ids),
           AudiobookFile.is_deleted == False
       )
       .distinct()
   )
   audiobook_ebook_ids = set(audiobook_result.scalars().all())
   ```

3. **批量查询 Comic**（启发式匹配）:
   - **收集所有 ebook 的 series 和 title**:
     - 优先使用 `series` 匹配（如果存在）
     - 如果没有 `series`，使用 `title` 匹配
   - **构建 SQL 查询**:
     ```python
     # 使用 ilike 进行模糊匹配
     comic_conditions = []
     if ebook_series_map:
         for series in ebook_series_map.keys():
             comic_conditions.append(Comic.series.ilike(f"%{series}%"))
     if ebook_title_map:
         for title in ebook_title_map.keys():
             comic_conditions.append(Comic.title.ilike(f"%{title}%"))
     ```
   - **在 Python 中匹配**:
     - 对每个匹配到的 comic，反向查找对应的 ebook
     - 使用双向包含匹配（更宽松）：`series in comic_series or comic_series in series`
     - 使用 `lower()` 进行不区分大小写的匹配

4. **构造 WorkFormats**:
   ```python
   work_formats = WorkFormats(
       has_ebook=True,  # ebook 项当然有电子书
       has_audiobook=ebook.id in audiobook_ebook_ids,
       has_comic=ebook.id in comic_ebook_ids,
       has_music=False  # 预留，当前暂不实现
   )
   ```

#### 性能优化

- **避免 N+1 查询**:
  - 使用 `IN` 查询批量获取 AudiobookFile
  - 使用 `OR` + `ilike` 批量查询 Comic
  - 在 Python 中进行分组聚合

- **查询次数**:
  - 1 次查询 EBook 列表
  - 1 次批量查询 AudiobookFile（如果本页有 ebook）
  - 1 次批量查询 Comic（如果本页有 ebook 且有 series/title）
  - 总计：最多 3 次查询，不随 ebook 数量线性增长

### 三、前端显示

**文件**: `src/components/library/LibraryPreviewCard.vue`

#### 徽章显示逻辑

- **显示条件**: 
  - 仅对 `media_type === "ebook"` 的卡片显示
  - 如果 `work_formats` 不存在或全为 `false`，不显示徽章行

- **徽章顺序**:
  1. 📖 **书** (`has_ebook == true`)
     - 颜色：`success`（绿色）
     - 图标：`mdi-book-open-variant`
  2. 🎧 **有声** (`has_audiobook == true`)
     - 颜色：`orange`（橙色）
     - 图标：`mdi-headphones`
  3. 📚 **漫画** (`has_comic == true`)
     - 颜色：`pink`（粉色）
     - 图标：`mdi-book-open-page-variant`
  4. 🎵 **音乐** (`has_music == true`)
     - 颜色：`teal`（青色）
     - 图标：`mdi-music`

- **UI 实现**:
  ```vue
  <v-card-actions v-if="item.media_type === 'ebook' && hasWorkFormats">
    <div class="d-flex align-center gap-1 flex-wrap">
      <v-chip v-if="item.work_formats?.has_ebook" size="x-small" color="success">
        <v-icon start size="x-small">mdi-book-open-variant</v-icon>
        书
      </v-chip>
      <!-- 其他徽章... -->
    </div>
  </v-card-actions>
  ```

#### 类型定义

**文件**: `src/types/library.ts`

```typescript
export interface WorkFormats {
  has_ebook: boolean
  has_audiobook: boolean
  has_comic: boolean
  has_music: boolean
}

export interface LibraryPreviewItem {
  ...
  work_formats?: WorkFormats | null
}
```

### 四、匹配规则说明

#### has_audiobook 计算

- **规则**: 查询是否存在 `AudiobookFile.ebook_id == ebook.id` 的记录
- **查询方式**: 批量 `IN` 查询，一次性获取所有关联的 ebook_id
- **准确性**: 100%（基于外键关联）

#### has_comic 计算

- **规则**: 启发式匹配（与 Work Hub 保持一致）
  - **优先匹配 series**:
    - 如果 `ebook.series` 不为空：使用 `Comic.series ilike "%{ebook.series}%"` 匹配
  - **回退到 title 匹配**:
    - 如果没有 `series`：使用 `Comic.title ilike "%{ebook.title}%"` 匹配
- **查询方式**: 批量 `OR` + `ilike` 查询，在 Python 中反向匹配
- **准确性**: 启发式匹配，可能有误差（例如同名不同作品）

### 五、测试

#### 测试文件

**`tests/test_library_preview_work_formats.py`**: 5 个测试用例

1. `test_work_formats_for_ebook_only`: 只有 EBook，无 Audiobook/Comic
   - 验证：`has_ebook=True`，其他为 `False`

2. `test_work_formats_with_audiobook`: 为某个 ebook 插入对应的 AudiobookFile
   - 验证：`has_audiobook=True`

3. `test_work_formats_with_comic_by_series`: ebook.series = "xxx"，有 Comic.series = "xxx"
   - 验证：`has_comic=True`

4. `test_work_formats_with_comic_by_title`: 通过 title 匹配漫画
   - 验证：`has_comic=True`

5. `test_library_preview_non_ebook_has_no_work_formats`: movie/tv/music 类型 item 的 work_formats 为 None
   - 验证：非 ebook 类型的 `work_formats` 为 `None`

**测试状态**: ✅ 全部通过（5 passed）

### 六、兼容性

#### 向后兼容

- `work_formats` 字段为可选（`Optional[WorkFormats] = None`）
- 对于没有此字段的旧响应，前端不会报错
- 对于非 ebook 类型，字段为 `None`，前端不显示徽章

#### 前端兼容

- TypeScript 类型定义中 `work_formats` 为可选字段
- 使用 `hasWorkFormats` computed 属性检查是否需要显示徽章
- 如果没有 `work_formats` 或全为 `false`，不显示徽章行

### 七、性能影响

#### 查询优化

- **优化前**（如果使用 N+1）:
  - 对每个 ebook：1 次查询 AudiobookFile + 1 次查询 Comic
  - 20 个 ebook = 40 次查询

- **优化后**（批量查询）:
  - 1 次查询 EBook 列表
  - 1 次批量查询 AudiobookFile（`IN` 查询）
  - 1 次批量查询 Comic（`OR` + `ilike`）
  - 总计：最多 3 次查询

#### 数据库压力

- 使用 `IN` 查询和 `OR` 条件，数据库可以优化执行计划
- 查询字段最小化（只查询必要的 `ebook_id`、`series`、`title`）
- 对数据库压力可控，不会出现明显的性能问题

## 总结

本次实现完成了在统一媒体库预览中增加「作品形态概览」功能：

1. ✅ **Schema 扩展**: 新增 `WorkFormats` 和 `work_formats` 字段
2. ✅ **后端计算**: 批量查询 AudiobookFile 和 Comic，避免 N+1
3. ✅ **启发式匹配**: Comic 匹配规则与 Work Hub 保持一致
4. ✅ **前端显示**: 在 LibraryPreviewCard 上显示小徽章
5. ✅ **性能优化**: 最多 3 次查询，不随 ebook 数量线性增长
6. ✅ **向后兼容**: 字段可选，不影响现有功能
7. ✅ **测试覆盖**: 5 个测试用例，全部通过

用户现在可以在 `/library` 页面一眼看出每个电子书作品是否有其他形态（有声书、漫画），无需额外请求即可获得作品形态概览。

