# FUTURE-AI-READING-ASSISTANT-1 设计笔记

> AI 阅读助手 v1：阅读规划与推荐助手（只读）

## 1. 目标

提供一个 AI 驱动的阅读规划助手：

- 基于阅读进度、阅读历史、收藏夹、库存分析
- 生成 `ReadingPlanDraft`（阅读计划草案）
- 提供个性化阅读推荐和目标规划

**硬性边界**：

- ✅ 只读分析，不修改阅读进度
- ✅ 输出仅为"规划建议"，用户决定是否采纳

---

## 2. 数据维度梳理

### 2.1 阅读进度（核心）

| 数据源 | 位置 | 关键信息 |
|--------|------|----------|
| UserNovelReadingProgress | `models/user_novel_reading_progress.py` | 小说进度、章节、是否完成 |
| UserAudiobookProgress | `models/user_audiobook_progress.py` | 有声书进度、播放位置 |
| MangaReadingProgress | `models/manga_reading_progress.py` | 漫画进度、页码、章节 |

### 2.2 阅读中心服务

| 服务 | 位置 | 功能 |
|------|------|------|
| ReadingHubService | `services/reading_hub_service.py` | 聚合进度、历史、统计 |
| list_ongoing_reading() | - | 获取进行中的阅读 |
| list_reading_history() | - | 获取阅读历史 |
| get_reading_stats() | - | 获取阅读统计 |
| get_recent_activity() | - | 获取最近活动 |

### 2.3 书库统计

| 数据源 | 位置 | 关键信息 |
|--------|------|----------|
| EBook | `models/ebook.py` | 电子书作品、标题、作者、系列 |
| EBookFile | `models/ebook.py` | 电子书文件、格式、大小 |
| MangaSeriesLocal | `models/manga_series_local.py` | 漫画系列 |

### 2.4 收藏与偏好

| 数据源 | 位置 | 关键信息 |
|--------|------|----------|
| ReadingFavorite | `services/reading_favorite_service.py` | 阅读收藏夹 |
| UserMediaFavorite | `models/user_favorite_media.py` | 用户收藏 |

---

## 3. 现有 AI 工具

| 工具名称 | 可用于阅读助手 |
|----------|----------------|
| `get_recommendation_preview` | ✅ 推荐系统预览 |
| `get_site_and_sub_overview` | 部分可用 |

---

## 4. 需要新增的工具

### 4.1 阅读进度快照工具（新增）

**文件**：`tools/reading_snapshot.py`

**功能**：
- 获取用户阅读进度摘要（小说/有声书/漫画）
- 统计正在阅读、已完成、待读数量
- 返回最近活动和进度百分比

### 4.2 书库统计工具（新增）

**文件**：`tools/library_books.py`

**功能**：
- 获取书库统计（按类型、按作者、按系列）
- 识别未开始阅读的书籍
- 返回待读列表和推荐优先级

---

## 5. 阅读计划数据结构

### 5.1 ReadingGoal

```python
class ReadingGoal(BaseModel):
    goal_type: ReadingGoalType  # daily / weekly / monthly / yearly
    target_count: int           # 目标数量
    current_count: int          # 当前进度
    media_types: list[str]      # 适用媒体类型
    deadline: Optional[str]     # 截止日期
```

### 5.2 ReadingSuggestion

```python
class ReadingSuggestion(BaseModel):
    suggestion_type: SuggestionType  # continue / start / finish / pause
    media_type: str                  # novel / manga / audiobook
    item_id: int                     # 书籍/漫画 ID
    title: str                       # 标题
    reason: str                      # 推荐理由
    priority: str                    # high / medium / low
    estimated_time: Optional[str]    # 预估阅读时间
```

### 5.3 ReadingPlanDraft

```python
class ReadingPlanDraft(BaseModel):
    summary: str                              # 总体说明
    goals: list[ReadingGoal]                 # 阅读目标
    suggestions: list[ReadingSuggestion]     # 阅读建议
    stats_context: dict                      # 统计背景
    insights: list[str]                      # 阅读洞察
    generated_at: str                        # 生成时间
```

### 5.4 枚举定义

```python
class ReadingGoalType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class SuggestionType(str, Enum):
    CONTINUE = "continue"   # 继续阅读
    START = "start"         # 开始新书
    FINISH = "finish"       # 完成当前
    PAUSE = "pause"         # 暂停建议
```

---

## 6. Orchestrator READING_ASSISTANT 模式

### 6.1 允许工具集

- `get_reading_snapshot` – 阅读进度快照（新增）
- `get_library_books` – 书库统计（新增）
- `get_recommendation_preview` – 推荐预览

### 6.2 System Prompt 要点

```
你是 VabHub 的 AI 阅读助手。

你的任务是分析用户的阅读进度、书库存量和阅读习惯，生成个性化的阅读计划建议。

你会收到：
1. 用户阅读进度（正在阅读、已完成、待读）
2. 书库统计（按类型、系列分组）
3. 最近阅读活动

你需要生成一个 ReadingPlanDraft JSON：
- summary: 总体说明
- goals: 阅读目标列表
- suggestions: 阅读建议列表，按优先级排序
- insights: 阅读洞察（如阅读速度、偏好分析）

重要约束：
- 你只是在生成"规划建议"，不会修改任何阅读进度
- 建议应该具体且可执行
- 考虑用户的阅读节奏，不要给出过于激进的目标
- 优先建议完成进行中的阅读，再开始新书
```

---

## 7. 实现进度

| 阶段 | 内容 | 状态 |
|------|------|------|
| P0 | 现状巡检 & 功能设计 | ✅ 完成 |
| P1 | 工具层增强（阅读快照/书库统计） | ✅ 完成 |
| P2 | 阅读计划 Schema & Orchestrator 增强 | ✅ 完成 |
| P3 | ReadingAssistant 服务 & API | ✅ 完成 |
| P4 | 前端 AI 阅读助手页面 | ✅ 完成 |
| P5 | 测试 & UX 打磨 | ✅ 完成 |
| P6 | 文档 & 总结 | ✅ 完成 |

---

## 8. 后续规划

- **v2**: 智能阅读提醒（结合通知系统）
- **v2**: 阅读成就与徽章系统
- **v3**: 社交阅读（书友推荐）
