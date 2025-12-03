# 统一阅读中心概述

> Phase READ-1 + READ-2 实现文档

## 概念

统一阅读中心将 **小说**、**漫画**、**有声书** 三种媒体类型的阅读/收听进度聚合到一个统一视图，让用户有一个「我在读什么」的总入口。

### 与现有中心的关系

```
┌─────────────────────────────────────────────────────────────┐
│                     统一阅读中心                              │
│  (ReadingHubPage + ReadingFavoriteShelf)                    │
│                                                             │
│  聚合展示：正在进行 / 历史记录 / 统一收藏                      │
└─────────────────────────────────────────────────────────────┘
        ↑               ↑               ↑
        │               │               │
┌───────┴───────┐ ┌─────┴─────┐ ┌───────┴───────┐
│   小说中心     │ │ 有声书中心 │ │   漫画库      │
│ (NovelCenter) │ │(Audiobook │ │(MangaLibrary) │
│               │ │  Center)  │ │               │
└───────────────┘ └───────────┘ └───────────────┘
```

- **不替代**：原有的 NovelCenter / AudiobookCenter / MangaLibraryPage 保持独立运行
- **聚合展示**：阅读中心从各子系统的进度表中读取数据，统一展示
- **双向入口**：各中心页面可跳转到阅读中心，阅读中心也可跳转到具体内容

## 后端结构

### 核心服务

| 文件 | 说明 |
|------|------|
| `backend/app/services/reading_hub_service.py` | 聚合服务，从各进度表读取数据 |
| `backend/app/schemas/reading_hub.py` | 统一 DTO 定义 |
| `backend/app/api/reading_hub.py` | API 路由 |

### 数据来源

| 媒体类型 | 进度模型 | 内容模型 |
|----------|----------|----------|
| 小说 | `UserNovelReadingProgress` | `EBook` |
| 有声书 | `UserAudiobookProgress` | `EBook` + `AudiobookFile` |
| 漫画 | `MangaReadingProgress` | `MangaSeriesLocal` + `MangaChapterLocal` |

### 通知系统集成 (READING-NOTIFY-1)

统一阅读中心与通知中心深度集成，为用户提供阅读相关的实时通知：

#### 通知类型
- **MANGA_UPDATED** - 漫画追更通知（新增章节）
- **READING_EBOOK_IMPORTED** - 电子书导入完成通知
- **AUDIOBOOK_READY** - 有声书生成完成通知
- **TTS_JOB_COMPLETED** - TTS 任务完成通知

#### 统一 Payload 结构
所有阅读通知使用标准化的 payload 格式：
```typescript
{
  media_type: "manga" | "novel" | "audiobook",
  title: string,
  cover_url?: string,
  route_name: string,
  route_params: object,
  source_label: string,
  // 类型特有字段...
}
```

#### Web UI 增强
- **ReadingNotificationCard** - 专门的阅读通知卡片组件
- 支持封面图片展示、媒体类型图标、来源标签
- 一键跳转到对应阅读页面
- 自动标记已读功能

#### 触发点集成
- **Manga 追更** - `manga_follow_sync.py` 检测新章节时触发
- **EBook 导入** - `novel_demo.py` 导入完成后触发
- **TTS 完成** - `tts/notification_service.py` 任务完成时触发

### 统一 DTO（READ-2 增强版）

```python
# 阅读状态枚举
ReadingStatus = Literal['not_started', 'in_progress', 'finished']

# 活动类型枚举
ActivityType = Literal['read', 'listen', 'update']

class ReadingOngoingItem(BaseModel):
    media_type: ReadingMediaType  # NOVEL / AUDIOBOOK / MANGA
    item_id: int                  # 对应实体的主键
    title: str
    sub_title: Optional[str]      # 作者/系列等（READ-2 新增）
    cover_url: Optional[str]
    source_label: Optional[str]   # 如 "小说中心" / "有声书" / "漫画"
    progress_label: str           # 如 "第 12 章" / "12:34 / 30:00" / "第 5 话 · 第 8 页"
    progress_percent: Optional[float]  # 0-100 进度百分比（READ-2 新增）
    status: ReadingStatus         # 阅读状态（READ-2 新增）
    is_finished: bool
    last_read_at: datetime
    last_activity_at: Optional[datetime]  # 最近活动时间（READ-2 新增）
    update_reason: Optional[str]  # 更新原因（READ-2 新增）
    route_name: str               # 前端路由名
    route_params: Dict[str, Any]  # 前端路由参数

class ReadingActivityItem(BaseModel):
    """阅读活动项（时间线用，READ-2 新增）"""
    media_type: ReadingMediaType
    item_id: int
    title: str
    sub_title: Optional[str]
    cover_url: Optional[str]
    status: ReadingStatus
    activity_type: ActivityType   # read / listen / update
    activity_label: str           # 活动描述
    occurred_at: datetime
    route_name: str
    route_params: Dict[str, Any]
```

### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/reading/ongoing` | 获取正在进行的阅读列表 |
| GET | `/api/reading/history` | 获取阅读历史（支持类型过滤） |
| GET | `/api/reading/stats` | 获取阅读统计（增强版） |
| GET | `/api/reading/recent_activity` | 获取最近活动时间线（READ-2 新增） |

## 前端结构

### 页面

| 路由 | 组件 | 说明 |
|------|------|------|
| `/reading` | `ReadingHubPage.vue` | 阅读中心主页 |
| `/reading/favorites` | `ReadingFavoriteShelf.vue` | 统一收藏书架 |

### 入口

1. **侧边栏**：
   - 「阅读中心」→ ReadingHubPage
   - 「我的收藏」→ ReadingFavoriteShelf

2. **各中心页面 PageHeader**：
   - NovelCenter → 阅读中心按钮
   - AudiobookCenter → 阅读中心按钮
   - MangaLibraryPage → 阅读中心按钮

### 类型定义（READ-2 增强版）

```typescript
// frontend/src/types/readingHub.ts
export type ReadingMediaType = 'NOVEL' | 'AUDIOBOOK' | 'MANGA'
export type ReadingStatus = 'not_started' | 'in_progress' | 'finished'
export type ActivityType = 'read' | 'listen' | 'update'

export interface ReadingOngoingItem {
  media_type: ReadingMediaType
  item_id: number
  title: string
  sub_title?: string | null        // READ-2 新增
  cover_url?: string | null
  source_label?: string | null
  progress_label: string
  progress_percent?: number | null // READ-2 新增
  status: ReadingStatus            // READ-2 新增
  is_finished: boolean
  last_read_at: string
  last_activity_at?: string | null // READ-2 新增
  update_reason?: string | null    // READ-2 新增
  route_name: string
  route_params: Record<string, any>
}

export interface ReadingActivityItem {
  // READ-2 新增：时间线用
  media_type: ReadingMediaType
  item_id: number
  title: string
  sub_title?: string | null
  cover_url?: string | null
  status: ReadingStatus
  activity_type: ActivityType
  activity_label: string
  occurred_at: string
  route_name: string
  route_params: Record<string, any>
}
```

### API 客户端

```typescript
// frontend/src/services/api.ts
export const readingHubApi = {
  listOngoing: async (params?) => { ... },
  listHistory: async (params?) => { ... },
  getStats: async () => { ... },
  getRecentActivity: async (params?) => { ... }  // READ-2 新增
}
```

## 功能特性

### 阅读中心 (ReadingHubPage) - READ-2 增强版

**顶部 Summary 卡片**：
- 正在阅读数量
- 已完成数量
- 收藏数量
- 最近7天活动数量

**Tab 结构**：
- **概览 Tab**：展示正在进行的阅读/收听项目，支持过滤和排序
- **时间线 Tab**：按时间倒序展示最近活动（READ-2 新增）
- **收藏 Tab**：快捷入口跳转到统一收藏书架

**过滤控件**：
- 媒体类型：全部 / 小说 / 有声书 / 漫画
- 阅读状态：全部 / 未开始 / 进行中 / 已完成
- 排序：最近活动 / 标题 (A→Z)

**卡片功能**：
- 显示封面、标题、子标题、进度条
- 媒体类型标签（颜色区分）
- 状态标签（未开始/进行中/已完成）
- 操作按钮：继续阅读/收听、查看详情

**URL Query 参数支持**：
- `focus_media_type`：自动过滤到指定媒体类型（用于从通知跳转）

### 统一收藏 (ReadingFavoriteShelf)

- **跨类型收藏**：小说、漫画、有声书收藏统一展示
- **类型筛选**：Tab 切换查看不同类型
- **关键字搜索**：搜索收藏标题
- **漫画更新提示**：显示追更漫画的新章节数
- **快速操作**：阅读/收听、取消收藏

## 运维说明

### 纯读取聚合

阅读中心是**纯读取**的聚合层：
- 不写入任何数据
- 不涉及后台任务或 Runner
- 数据由各子系统的阅读器/播放器写入

### 与 Runner 的关系

| Runner | 作用 | 与阅读中心关系 |
|--------|------|----------------|
| TTS Runner | 生成有声书音频 | 生成后，用户播放时写入 `UserAudiobookProgress` |
| 漫画追更 Runner | 同步远程漫画更新 | 同步后，用户阅读时写入 `MangaReadingProgress` |

阅读中心只负责**展示**这些进度数据。

### Telegram 阅读控制台视图矩阵

阅读中心在 Telegram Bot 中提供三个只读视角：

| 视角 | 命令前缀 | 数据来源 | 用途 |
|------|----------|----------|------|
| 进行中视角 | `/reading*` | ReadingOngoingItem | 查看当前在读/在听/在看的项目 |
| 时间线视角 | `/reading_recent*` | ReadingActivityItem | 查看最近的阅读活动记录 |
| 书架视角 | `/shelf*` | ReadingShelfItem | 查看收藏的小说/有声书/漫画 |

**Telegram 命令示例：**
- `/reading` - 进行中阅读列表
- `/reading_recent` - 最近活动时间线  
- `/shelf` - 我的书架（混合）
- `/shelf_books` - 收藏的小说
- `/shelf_detail 1` - 查看书架条目详情

**缓存机制：**
- 所有视角均采用 10 分钟 TTL 缓存
- 支持按索引快速访问单条记录
- 书架视角按类型分别缓存（mixed/novel/audiobook/manga）

### Telegram 阅读控制台 – 交互视角

TG-BOT-BOOK-3 引入了交互操作，让 Telegram 真正成为"阅读遥控器"。

**核心设计原则：**
- **幂等性**：重复执行不会产生脏数据
- **用户隔离**：严格限制在 user_id 范围内的操作
- **数据一致性**：与 Web 前端共享同一套数据模型
- **缓存失效**：操作后正确失效相关缓存

**交互命令：**
- `/reading_done <index>` - 标记进行中列表中的某条为已完成
- `/reading_fav <index>` - 从进行中列表中将某条加入书架收藏
- `/shelf_unfav <index>` - 从书架视角中取消某条收藏

**技术架构：**
- **Service 层**：`ReadingControlService` 统一写操作入口
  - `mark_reading_finished()` - 标记完成
  - `add_favorite_from_reading()` - 添加收藏
  - `remove_favorite_by_internal_id()` - 取消收藏
- **缓存失效策略**：
  - 标记完成：ReadingListCache + ReadingActivityCache
  - 收藏操作：ReadingShelfCache（主要）
- **错误处理**：`ReadingControlError` 统一异常处理

**安全特性：**
- 所有写操作明确标注"⚠️ 会修改状态"
- 支持用户绑定检查，未绑定用户无法执行
- 操作可在 Web 端逆向修复
- 完整的操作日志记录

### 性能考虑

- 聚合查询使用 `LIMIT` 限制每种类型的返回数量
- 历史记录支持分页
- 前端使用懒加载（Tab 切换时才加载对应数据）

## 文件清单

### 后端

```
backend/app/
├── api/
│   └── reading_hub.py              # API 路由
├── schemas/
│   └── reading_hub.py              # DTO 定义
├── services/
│   └── reading_hub_service.py      # 聚合服务
└── models/
    └── enums/
        └── reading_media_type.py   # 媒体类型枚举
```

### 前端

```
frontend/src/
├── pages/
│   └── reading/
│       ├── ReadingHubPage.vue      # 阅读中心页面
│       └── ReadingFavoriteShelf.vue # 统一收藏页面
├── components/
│   └── reading/
│       └── ReadingItemCard.vue     # 阅读项卡片组件
├── types/
│   ├── readingHub.ts               # 阅读中心类型
│   └── readingFavorite.ts          # 收藏类型
└── services/
    └── api.ts                      # readingHubApi
```

## 扩展点

1. **更多媒体类型**：如需支持新类型（如播客），只需：
   - 后端：在 `reading_hub_service.py` 添加对应的 `_load_xxx_reading_items` 函数
   - 前端：在 `ReadingMediaType` 添加新类型

2. **阅读统计增强**：可扩展 `/api/reading/stats` 返回更详细的统计数据

3. **推荐系统**：基于阅读历史，可在阅读中心添加「猜你喜欢」模块
