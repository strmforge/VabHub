# SUBS-MODULE-UI-1 工作笔记

> 内部开发笔记，任务完成后可删除或归档

---

## P1. 现状巡检总结

### 订阅模型速查表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | 主键 |
| `user_id` | Integer | 用户 ID |
| `title` | String | 标题 |
| `original_title` | String | 原标题 |
| `year` | Integer | 年份 |
| `media_type` | String | 类型：movie/tv/short_drama/anime/music |
| `tmdb_id` | Integer | TMDB ID |
| `poster` | String | 海报 URL |
| `backdrop` | String | 背景图 URL |
| `status` | String | 状态：active/paused/completed |
| `season` | Integer | 季数（电视剧） |
| `total_episode` | Integer | 总集数（电视剧） |
| `start_episode` | Integer | 起始集数（电视剧） |
| `quality` | String | 目标质量 |
| `resolution` | String | 分辨率 |
| `sites` | JSON | 订阅站点列表 |
| `last_check_at` | DateTime | 最后检查时间 |
| `last_success_at` | DateTime | 最后成功时间 |

### 前端现状

- **Subscriptions.vue**：已有卡片布局，使用 SubscriptionCard 组件
- **SubscriptionCard.vue**：已有海报、标题、状态、类型标签等
- **类型过滤**：已支持 movie/tv/short_drama/anime/music
- **API**：`GET /api/subscriptions` 支持 `media_type` 参数过滤

### 需要改造的点

1. ✅ 路由：添加 `/subscriptions/movies` 等子路由
2. ✅ 导航：订阅管理改为可展开的父项
3. ✅ Subscriptions.vue：读取 route.meta.mediaType
4. ⚠️ 电视剧集数：模型有 `total_episode` 字段，但需要补充"已下载集数"
5. ✅ 移除"创建订阅"按钮，添加快捷入口

### v1 限制说明

- **电视剧集数**：模型有 `total_episode` 字段，v1 使用 `start_episode` 作为"已下载集数"的近似值
- 更精确的"已下载集数"需要从媒体库统计，留待后续版本接入
- 卡片显示格式：`已下载 X / Y 集`（Y 为总集数，X 为起始集数或 0）

---

## 已完成内容

### 路由变更
- `/subscriptions` → 重定向到 `/subscriptions/movies`
- `/subscriptions/movies` → 电影订阅（MovieSubscriptions）
- `/subscriptions/tv` → 电视剧订阅（TvSubscriptions）
- `/subscriptions/music` → 音乐订阅（MusicSubscriptions）
- `/subscriptions/books` → 书籍订阅（BookSubscriptions）

### 导航变更
- "订阅管理" 改为可展开的 `v-list-group`
- 子项：电影订阅 / 电视剧订阅 / 音乐订阅 / 书籍订阅

### UI 变更
- 移除"创建订阅"按钮
- 添加"规则中心"和"AI 订阅助手"快捷入口
- 根据路由 meta 中的 mediaType 自动过滤
- 隐藏类型过滤器（已按路由分类）
- SubscriptionCard 增加集数进度条（电视剧类型）
- SubscriptionCard 增加质量信息显示

---

*最后更新：2025-12-02 SUBS-MODULE-UI-1*
