# VabHub UI 缺口总览

> 本文件是 UI-GLUE-1 任务的 P0 阶段产物，用于记录当前系统中后端已有能力但前端缺页面/入口，或页面只有假数据的情况。
> 更新于 2025-12-03，任务 UI-GLUE-1。
> 
> **状态说明**：UI 缺口已在 UI-GLUE-FILL-GAPS-1 + UI-LAYOUT-TUNING-1 中完成 v1 收尾，目前为历史记录 / 未来检查参考。

---

## 1. 影视中心

| 页面 | 路由 | 状态 | 说明 |
|------|------|------|------|
| 首页总览 | `/` | [OK] | 已对接真实数据，展示仪表盘信息 |
| 电视墙 | `/player/wall` | [OK] | 已对接真实数据，支持多源播放 |
| 媒体库 | `/library` | [OK] | 已对接真实数据，展示媒体库内容 |
| 发现 | `/discover` | [OK] | 已对接真实数据，支持多源内容发现 |
| 日历 | `/calendar` | [OK] | 已对接真实数据，支持日历事件管理 |
| 短剧工作台 | `/short-drama` | [OK] | 已从音乐中心拆分至影视中心，功能正常 |

---

## 2. 下载 & 订阅

| 页面 | 路由 | 状态 | 说明 |
|------|------|------|------|
| 搜索 | `/search` | [OK] | 已对接真实搜索 API，支持多站点搜索 |
| 下载管理 | `/downloads` | [OK] | 已对接真实下载任务 API，支持任务管理 |
| 电影订阅 | `/subscriptions/movies` | [OK] | 已对接真实 API，展示电影订阅列表 |
| 电视剧订阅 | `/subscriptions/tv` | [OK] | 已对接真实 API，展示电视剧订阅列表 |
| 音乐订阅 | `/subscriptions/music` | [OK] | 已对接真实 API，展示音乐订阅列表 |
| 书籍订阅 | `/subscriptions/books` | [OK] | 已对接真实 API，展示书籍订阅列表 |
| RSS 订阅 | `/rss-subscriptions` | [OK] | 已对接真实 API，支持 RSS 源管理和状态监控 |
| RSSHub 订阅 | `/rsshub` | [OK] | 已对接真实 API，支持 RSSHub 源管理和状态监控 |
| 工作流管理 | `/workflows` | [OK] | 已对接真实 API，支持工作流管理和执行 |

---

## 3. 阅读 & 听书

| 页面 | 路由 | 状态 | 说明 |
|------|------|------|------|
| 阅读中心 | `/reading` | [OK] | 已对接真实 API，展示阅读进度和活动时间线 |
| 我的书架 | `/my/shelf` | [OK] | 已对接真实 API，展示书架上的书籍和阅读进度 |
| 我的收藏 | `/reading/favorites` | [OK] | 已对接收藏 API，展示收藏的书籍 |
| 小说中心 | `/novels` | [OK] | 已对接真实 API，展示电子书列表和 TTS 状态 |
| 有声书中心 | `/audiobooks` | [OK] | 已对接真实 API，展示有声书列表和播放状态 |
| TTS 有声书 | `/tts/center` | [OK] | 已对接真实 API，展示 TTS 任务列表和状态 |

---

## 4. 漫画中心

| 页面 | 路由 | 状态 | 说明 |
|------|------|------|------|
| 本地漫画库 | `/manga/library` | [OK] | 已对接真实 API，展示本地漫画 |
| 漫画追更中心 | `/manga/following` | [OK] | 已对接 UserMangaFollow API，展示漫画追更状态 |
| 远程漫画 | `/manga/remote` | [OK] | 已对接远程漫画源 API，支持远程漫画浏览 |
| 第三方漫画源 | `/manga/source-browser` | [OK] | 已对接 MangaSource API，支持漫画源配置 |
| 阅读历史 | `/manga/history` | [OK] | 已对接阅读历史 API，展示漫画阅读历史 |

---

## 5. 音乐中心

| 页面 | 路由 | 状态 | 说明 |
|------|------|------|------|
| 音乐库 | `/music` | [OK] | 已对接真实 API，展示音乐库内容和播放控制 |

---

## 6. AI 中心

| 页面 | 路由 | 状态 | 说明 |
|------|------|------|------|
| AI 实验室 | `/ai-lab` | [OK] | 已对接真实 API，支持 AI 工具调用 |
| AI 订阅助手 | `/ai-subs-assistant` | [OK] | 已对接真实 API，支持自然语言生成订阅 |
| AI 故障医生 | `/ai-log-doctor` | [OK] | 已对接真实 API，支持系统诊断 |
| AI 整理顾问 | `/ai-cleanup-advisor` | [OK] | 已对接真实 API，支持媒体清理建议 |
| AI 阅读助手 | `/ai-reading-assistant` | [OK] | 已对接真实 API，支持阅读计划建议 |
| AI 推荐 | `/recommendations` | [OK] | 已对接推荐 API，展示个性化媒体推荐 |

---

## 7. 站点 & 插件

| 页面 | 路由 | 状态 | 说明 |
|------|------|------|------|
| 站点管理 | `/site-manager` | [OK] | 已对接真实 API，支持站点管理和健康检查 |
| HNR 风险检测 | `/hnr` | [OK] | 已对接真实 HNR 检测 API，展示 HNR 风险任务 |
| 插件市场 | `/plugins` | [OK] | 已对接远程插件列表 API，展示可用插件 |
| Local Intel | `/local-intel` | [OK] | 已对接 Local Intel API，展示本地智能索引状态 |
| 外部索引 | `/external-indexer` | [OK] | 已对接 External Indexer API，展示外部索引状态 |

---

## 8. 系统 & 设置

| 页面 | 路由 | 状态 | 说明 |
|------|------|------|------|
| 系统设置 | `/settings` | [OK] | 已对接真实 API，支持系统配置 |
| 通知中心 | `/notifications` | [OK] | 已对接真实 API，支持通知管理 |
| 任务中心 | `/tasks` | [OK] | 已对接 Runner 状态和历史 API，展示任务执行情况 |
| 实时日志 | `/log-center` | [OK] | 已对接真实 API，支持实时日志查看 |
| 存储监控 | `/storage-monitor` | [OK] | 已对接存储快照 API，展示存储使用情况 |
| 调度器监控 | `/scheduler-monitor` | [OK] | 已对接调度器 API，展示调度器状态 |
| 系统自检 | `/system-selfcheck` | [OK] | 已对接系统自检 API，展示系统健康状态 |
| 云存储管理 | `/cloud-storage` | [OK] | 已对接云存储 API，支持云存储配置 |
| 媒体服务器 | `/media-servers` | [OK] | 已对接媒体服务器 API，支持媒体服务器管理 |
| 系统控制台 | `/admin` | [OK] | 已对接管理员 API，提供系统管理功能 |

---

## 9. 开发工具

| 页面 | 路由 | 状态 | 说明 |
|------|------|------|------|
| GraphQL 实验室 | `/graphql-explorer` | [OK] | 已对接真实 GraphQL API |
| 小说 Inbox 日志 | `/dev/novels/inbox` | [OK] | 已对接真实 API，用于开发调试 |
| 漫画源配置 | `/dev/manga/sources` | [OK] | 已对接真实 API，用于开发调试 |
| 目录配置 | `/directory-config` | [OK] | 已对接真实 API，用于目录配置 |
| 媒体文件管理 | `/media-renamer` | [OK] | 已对接真实 API，用于媒体重命名 |
| 媒体整理 | `/file-browser` | [OK] | 已对接真实 API，用于文件浏览 |
| 转移历史 | `/transfer-history` | [OK] | 已对接真实 API，用于转移历史查看 |
| 字幕管理 | `/subtitles` | [OK] | 已对接真实 API，用于字幕管理 |

---

## 2. 缺口分析与优先级

### 2.1 高优先级缺口

| 模块 | 缺口 | 影响 | 建议 |
|------|------|------|------|
| 下载 & 订阅 | RSS/RSSHub/工作流页面 | 影响自动下载闭环 | 优先对接真实 API，实现基本列表和状态展示 |
| 阅读 & 听书 | 阅读中心/书架/有声书中心 | 影响阅读体验 | 优先对接 Shelf API，实现阅读进度同步 |
| 漫画中心 | 追更中心/远程漫画 | 影响漫画追更体验 | 优先对接追更 API，实现漫画更新通知 |
| 系统 & 设置 | 任务中心/存储监控 | 影响系统监控 | 优先对接 Runner 状态和存储快照 API |

### 2.2 中优先级缺口

| 模块 | 缺口 | 影响 | 建议 |
|------|------|------|------|
| 影视中心 | 发现/日历 | 影响内容发现体验 | 对接真实发现和日历功能 |
| 音乐中心 | 音乐库 | 影响音乐播放体验 | 对接真实音乐库 API |
| 站点 & 插件 | HNR 检测/插件市场 | 影响站点管理体验 | 对接真实 HNR 检测和插件列表 API |

### 2.3 低优先级缺口

| 模块 | 缺口 | 影响 | 建议 |
|------|------|------|------|
| AI 中心 | AI 推荐 | 影响推荐体验 | 对接真实推荐 API |
| 系统 & 设置 | 调度器监控/云存储管理 | 影响系统管理体验 | 对接相关 API |

---

## 3. 完整闭环模块

以下模块已实现完整闭环，后续无需修改：

- 首页总览
- 电视墙
- 媒体库
- 短剧工作台
- 搜索
- 下载管理
- 订阅管理（电影/电视剧/音乐/书籍）
- 小说中心
- 本地漫画库
- AI 实验室
- AI 订阅助手
- AI 故障医生
- AI 整理顾问
- AI 阅读助手
- 系统设置
- 通知中心
- 实时日志
- 所有开发工具页面

---

## 4. 后续工作建议

1. **P1 阶段**：优先处理下载 & 订阅组的缺口，确保自动下载闭环
2. **P2 阶段**：处理阅读 & 听书、漫画中心的缺口，提升阅读体验
3. **P3 阶段**：处理站点 & 插件组的缺口，完善站点管理功能
4. **P4 阶段**：处理系统 & 设置组的缺口，完善系统监控功能
5. **P5 阶段**：处理首页 Dashboard 小补丁，确保数据展示一致
6. **P6 阶段**：更新文档，确保文档与实际代码一致
7. **P7 阶段**：验收测试，确保所有页面都有真实数据或友好空状态

---

## 5. 术语说明

- **[OK]**：完整闭环，后端已有能力，前端已对接真实数据，功能正常
- **[WIP]**：页面存在，但需对接真实 API 或完善功能
- **[TODO]**：页面存在，但内容是假数据，需完全对接真实 API
- **[MISSING]**：后端已有能力，但前端缺页面或入口

---

## 6. 临时 TODO Notes（UI-GLUE-FILL-GAPS-1）

### 本次任务改动清单

#### 影视中心
- [OK] 发现 `/discover` (by UI-GLUE-FILL-GAPS-1：已对接 mediaApi/doubanApi/bangumiApi)
- [OK] 日历 `/calendar` (by UI-GLUE-FILL-GAPS-1：已对接 calendar API)

#### 下载 & 订阅
- [OK] RSS 订阅 `/rss-subscriptions` (by UI-GLUE-FILL-GAPS-1：已对接 rssApi)
- [OK] RSSHub 订阅 `/rsshub` (by UI-GLUE-FILL-GAPS-1：已对接 api.get('/rsshub/sources'))
- [OK] 工作流管理 `/workflows` (by UI-GLUE-FILL-GAPS-1：已对接 api.get('/workflows'))

#### 阅读 & 听书
- [OK] 阅读中心 `/reading` (by UI-GLUE-FILL-GAPS-1：已对接 readingHubApi)
- [OK] 我的书架 `/my/shelf` (by UI-GLUE-FILL-GAPS-1：已对接 myShelfApi)
- [OK] 我的收藏 `/reading/favorites` (by UI-GLUE-FILL-GAPS-1：已对接收藏 API)
- [OK] 有声书中心 `/audiobooks` (by UI-GLUE-FILL-GAPS-1：已对接 audiobookApi)
- [OK] TTS 有声书 `/tts/center` (by UI-GLUE-FILL-GAPS-1：已对接 TTS 任务 API)

#### 漫画中心
- [OK] 漫画追更中心 `/manga/following` (by UI-GLUE-FILL-GAPS-1：已对接 UserMangaFollow API)
- [OK] 远程漫画 `/manga/remote` (by UI-GLUE-FILL-GAPS-1：已对接远程漫画源 API)
- [OK] 第三方漫画源 `/manga/source-browser` (by UI-GLUE-FILL-GAPS-1：已对接 MangaSource API)
- [OK] 阅读历史 `/manga/history` (by UI-GLUE-FILL-GAPS-1：已对接阅读历史 API)

#### 音乐中心
- [OK] 音乐库 `/music` (by UI-GLUE-FILL-GAPS-1：已对接音乐库 API)

#### AI 中心
- [OK] AI 推荐 `/recommendations` (by UI-GLUE-FILL-GAPS-1：已对接推荐 API)

#### 站点 & 插件
- [OK] 站点管理 `/site-manager` (by UI-GLUE-FILL-GAPS-1：已对接站点 API)
- [OK] HNR 风险检测 `/hnr` (by UI-GLUE-FILL-GAPS-1：已对接 HNR 检测 API)
- [OK] 插件市场 `/plugins` (by UI-GLUE-FILL-GAPS-1：已对接远程插件列表 API)
- [OK] Local Intel `/local-intel` (by UI-GLUE-FILL-GAPS-1：已对接 Local Intel API)
- [OK] 外部索引 `/external-indexer` (by UI-GLUE-FILL-GAPS-1：已对接 External Indexer API)

#### 系统 & 设置
- [OK] 任务中心 `/tasks` (by UI-GLUE-FILL-GAPS-1：已对接 Runner 状态和历史 API)
- [OK] 存储监控 `/storage-monitor` (by UI-GLUE-FILL-GAPS-1：已对接存储快照 API)
- [OK] 调度器监控 `/scheduler-monitor` (by UI-GLUE-FILL-GAPS-1：已对接调度器 API)
- [OK] 系统自检 `/system-selfcheck` (by UI-GLUE-FILL-GAPS-1：已对接系统自检 API)
- [OK] 云存储管理 `/cloud-storage` (by UI-GLUE-FILL-GAPS-1：已对接云存储 API)
- [OK] 媒体服务器 `/media-servers` (by UI-GLUE-FILL-GAPS-1：已对接媒体服务器 API)
- [OK] 系统控制台 `/admin` (by UI-GLUE-FILL-GAPS-1：已对接管理员 API)
