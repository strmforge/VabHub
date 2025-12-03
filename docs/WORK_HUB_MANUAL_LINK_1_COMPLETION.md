# WORK-HUB-MANUAL-LINK-1 完成文档

## 概述

在现有 Work Hub（`/api/works/{ebook_id}` + WorkDetail.vue）的基础上，增加了手动纠偏/手动绑定能力，允许用户明确标记某个视频/漫画/音乐与 ebook 的关联关系，或标记误匹配的候选项为"忽略"。

## 实现内容

### 一、WorkLink 模型结构说明

**文件**: `app/models/work_link.py`

```python
class WorkLink(Base):
    """作品关联模型"""
    __tablename__ = "work_links"
    
    id: int  # 主键
    ebook_id: int  # 外键 -> ebooks.id (CASCADE DELETE)
    target_type: str  # "video" | "comic" | "music"
    target_id: int  # 对应 Media/Comic/Music 的 id
    relation: str  # "include" | "exclude"
    created_at: datetime
    updated_at: datetime
```

**唯一约束**: `(ebook_id, target_type, target_id)` - 同一个 ebook/target_type/target_id 只应有一条记录。

**字段含义**:
- `ebook_id`: 电子书作品 ID（作为 Work 的锚点）
- `target_type`: 目标类型，支持 `"video"`、`"comic"`、`"music"`
- `target_id`: 目标实体的 ID（对应 Media/Comic/Music 表的 id）
- `relation`: 关联关系
  - `"include"`: 强制认为这个目标是该 ebook 的关联作品，即使启发式匹配不到也要展示
  - `"exclude"`: 明确告诉系统"这个候选是误匹配"，以后启发式匹配到了也不要展示

### 二、管理 API 说明

**文件**: `app/api/work_links.py`

#### 1. GET `/api/admin/work-links/by-ebook/{ebook_id}`

获取指定 ebook 的所有 WorkLink 记录（包含 include 和 exclude）。

**响应格式**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "ebook_id": 123,
      "target_type": "video",
      "target_id": 456,
      "relation": "include",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "message": "获取作品关联成功"
}
```

#### 2. POST `/api/admin/work-links`

创建或更新作品关联。

**请求体**:
```json
{
  "ebook_id": 123,
  "target_type": "video",
  "target_id": 456,
  "relation": "include"
}
```

**逻辑**:
- 如果已有同 `ebook_id/target_type/target_id` 记录 → 更新 `relation`
- 否则创建新记录

**响应格式**: 同 GET 接口的单个 WorkLink 对象。

#### 3. DELETE `/api/admin/work-links/{link_id}`

删除指定的 WorkLink 记录。

#### 4. DELETE `/api/admin/work-links/by-target?ebook_id=..&target_type=..&target_id=..`

通过组合键删除 WorkLink 记录（可选功能）。

### 三、/api/works/{ebook_id} 聚合逻辑调整

**文件**: `app/api/work.py`

#### 优先级规则

1. **手动 include 的记录永远优先**:
   - 直接查询 `includes_*_ids` 对应的实体（Media/Comic/Music）
   - 映射为对应的 WorkItem（WorkVideoItem/WorkComic/WorkMusicItem）
   - 这些记录会出现在最终结果中，即使启发式匹配不到

2. **启发式匹配的结果**:
   - 保持原有的 series/title/author 匹配逻辑
   - 在构造列表前做过滤：
     - 排除所有 `target_id` 在 `excludes_*_ids` 中的
     - 排除所有 `target_id` 在 `includes_*_ids` 中的（避免重复）

3. **合并顺序**:
   - `final_items = manual_includes + heuristic_candidates_filtered`
   - 手动 include 的记录在前，启发式候选在后

#### 具体实现

**Videos 聚合**:
1. 手动 include: 用 `includes_video_ids` 查询 Media 表，构造 WorkVideoItem
2. 启发式匹配: 保持原有的 series/title 匹配逻辑
3. 过滤: 排除 `excludes_video_ids` 和 `includes_video_ids` 中的
4. 合并: `videos = manual_includes + filtered_heuristic`

**Comics 聚合**:
1. 手动 include: 用 `includes_comic_ids` 查询 Comic 表，同时查询 ComicFile
2. 启发式匹配: 保持原有的 series/title 匹配逻辑
3. 过滤: 排除 `excludes_comic_ids` 和 `includes_comic_ids` 中的
4. 合并: `comics = manual_includes + filtered_heuristic`

**Music 聚合**:
1. 手动 include: 用 `includes_music_ids` 查询 Music 表，构造 WorkMusicItem
2. 启发式匹配: 保持原有的 title/series/author 匹配逻辑
3. 过滤: 排除 `excludes_music_ids` 和 `includes_music_ids` 中的
4. 合并: `music = manual_includes + filtered_heuristic`

#### WorkDetailResponse 扩展

**文件**: `app/schemas/work.py`

```python
class WorkDetailResponse(BaseModel):
    """作品详情响应"""
    ebook: WorkEBook
    ebook_files: List[WorkEBookFile]
    audiobooks: List[WorkAudiobookFile]
    comics: List[WorkComic]
    comic_files: List[WorkComicFile]
    videos: List[WorkVideoItem] = []
    music: List[WorkMusicItem] = []
    links: List[Any] = []  # 手动关联列表（WorkLinkResponse），可选字段，向后兼容
```

**向后兼容**: `links` 字段为可选，旧前端不访问也不会报错。

### 四、前端 WorkDetail 页面手动绑定 UI

**文件**: `src/pages/WorkDetail.vue`

#### Dev 模式控制

```typescript
const isDevMode = import.meta.env.DEV || import.meta.env.VITE_DEV_MODE === 'true'
```

只有在 dev 模式下才显示手动绑定按钮，普通用户只看到"最终结果"。

#### 辅助函数

```typescript
// 获取指定 target 的 WorkLink
const getLinkFor = (targetType: WorkTargetType, targetId: number): WorkLink | undefined

// 判断是否已 include
const isIncluded = (targetType: WorkTargetType, targetId: number): boolean

// 判断是否已 exclude
const isExcluded = (targetType: WorkTargetType, targetId: number): boolean

// 处理手动绑定操作
const handleLinkAction = async (
  action: "include" | "exclude" | "delete",
  targetType: WorkTargetType,
  targetId: number
)
```

#### UI 交互规则

**对于每个 item（video/comic/music）**:

1. **如果还没有任何记录**:
   - 显示两个按钮：
     - "标记关联" → 调用 `createOrUpdate(relation="include")`
     - "忽略这条" → 调用 `createOrUpdate(relation="exclude")`

2. **如果已有 include**:
   - 显示"已关联"状态（绿色 chip）
   - 附带一个"取消"按钮（调用 `delete`）

3. **如果已有 exclude**:
   - 显示"已忽略"状态（灰色 chip）
   - 附带一个"取消"按钮（调用 `delete`）

**操作成功后**:
- 更新本地 `links` 列表
- 重新加载 `/api/works/{ebook_id}` 以更新显示

#### UI 位置

- **漫画**: 在 `v-expansion-panel-title` 中，每个漫画卷的标题旁边
- **视频**: 在 `v-data-table` 中，新增 `actions` 列
- **音乐**: 在 `v-data-table` 中，新增 `actions` 列

### 五、API 封装

**文件**: `src/services/api.ts`

```typescript
export const workLinksApi = {
  // 获取指定 ebook 的所有关联
  listByEbook: (ebookId: number) => api.get<WorkLink[]>(`/admin/work-links/by-ebook/${ebookId}`),
  
  // 创建或更新作品关联
  createOrUpdate: (payload: {
    ebook_id: number
    target_type: "video" | "comic" | "music"
    target_id: number
    relation: "include" | "exclude"
  }) => api.post<WorkLink>("/admin/work-links", payload),
  
  // 删除作品关联
  delete: (linkId: number) => api.delete(`/admin/work-links/${linkId}`),
  
  // 通过组合键删除作品关联
  deleteByTarget: (params: {
    ebook_id: number
    target_type: "video" | "comic" | "music"
    target_id: number
  }) => api.delete("/admin/work-links/by-target", { params })
}
```

### 六、类型定义

**文件**: `src/types/work.ts`

```typescript
export type WorkTargetType = "video" | "comic" | "music"
export type WorkLinkRelation = "include" | "exclude"

export interface WorkLink {
  id: number
  ebook_id: number
  target_type: WorkTargetType
  target_id: number
  relation: WorkLinkRelation
  created_at: string
  updated_at: string
}

export interface WorkDetailResponse {
  // ... 其他字段
  links?: WorkLink[]  // 手动关联列表（可选，向后兼容）
}
```

### 七、测试

#### 测试文件

**`tests/test_work_links_model_and_api.py`**: 3 个测试用例

1. **`test_create_include_link_and_update_relation`**: 创建 include 链接，然后用相同组合键更新 relation
2. **`test_delete_link`**: 删除 WorkLink 后，对应记录不存在
3. **`test_get_links_by_ebook`**: 返回正确 ebook_id 下的所有 WorkLink

**`tests/test_work_detail_with_manual_links.py`**: 5 个测试用例

1. **`test_manual_include_video_overrides_heuristic`**: 即使启发式匹配不到该 Media，手动 include 后，videos 中应包含
2. **`test_manual_exclude_video_filters_out_heuristic_match`**: 手动 exclude 之后，即使启发式匹配到了，该 Media 不应出现在 videos 中
3. **`test_manual_include_comic_overrides_heuristic`**: 手动 include 的漫画即使启发式匹配不到也会显示
4. **`test_manual_exclude_music_filters_out_heuristic_match`**: 手动 exclude 的音乐即使启发式匹配到了也不会显示
5. **`test_manual_include_priority_over_heuristic`**: 手动 include 的记录优先显示，且不会重复

**测试状态**: ✅ 全部通过（8 passed）

### 八、性能优化

- **避免 N+1 查询**:
  - WorkLink 查询: 一次查询获取所有链接，在 Python 中分组
  - 手动 include 查询: 使用 `IN` 批量查询
  - 启发式匹配: 保持原有的批量查询逻辑
  - 总计: 最多 3-4 次额外查询（WorkLink + include 查询）

- **去重逻辑**:
  - 手动 include 的记录如果与启发式结果重合，最终只出现一条（通过 `includes_*_ids` 过滤启发式结果）

### 九、兼容性

#### 向后兼容

- **新字段可选**: `links` 字段为可选，旧前端不访问也不会报错
- **原有逻辑不变**: 启发式匹配逻辑完全保留，只是在其之上增加"人工覆盖层"
- **API 行为**: 原有 API 调用不应崩，只是增加了新的功能

#### Dev 模式控制

- **前端 UI**: 只有在 dev 模式下才显示手动绑定按钮
- **普通用户**: 只看到"最终结果"，看不到"手动纠偏开关"

## 总结

本次实现完成了在 Work Hub 中增加手动关联/绑定功能：

1. ✅ **WorkLink 模型**: 创建了统一的"作品关联表"，支持 include/exclude 两种关系
2. ✅ **管理 API**: 提供了完整的 CRUD 接口（创建/更新/删除/查询）
3. ✅ **聚合逻辑调整**: `/api/works/{ebook_id}` 优先使用手动绑定，启发式匹配只作为"候选补充"
4. ✅ **前端 UI**: 在 WorkDetail.vue 中添加了手动绑定按钮（dev 模式）
5. ✅ **性能优化**: 避免 N+1 查询，使用批量查询
6. ✅ **向后兼容**: 新字段可选，不影响现有功能
7. ✅ **测试覆盖**: 8 个测试用例，全部通过

用户现在可以在 `/works/{ebook_id}` 页面手动标记某个视频/漫画/音乐与 ebook 的关联关系，或标记误匹配的候选项为"忽略"，系统会优先使用手动绑定，启发式匹配只作为"候选补充"。

