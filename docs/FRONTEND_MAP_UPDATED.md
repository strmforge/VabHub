# VabHub 前端路由地图

> 本文件是前端页面/路由/导航结构的单一事实来源。  
> 更新于 2025-12-03，任务 UI-GLUE-1 完成。

---

## 1. 导航分组结构

侧边栏导航（`AppDrawer.vue`）按以下分组组织：

```
📺 影视中心
├── 首页总览        /                      HomeDashboard [DONE]
├── 电视墙          /player/wall           PlayerWall [DONE]
├── 媒体库          /library               Library [DONE]
├── 发现            /discover              Discover [DONE]
├── 日历            /calendar              Calendar [DONE]
└── 短剧工作台      /short-drama           ShortDrama [DONE]
📌 电视墙播放策略（LAN/WAN/115）详见 TV_WALL_PLAYBACK_OVERVIEW.md

⬇️ 下载 & 订阅
├── 搜索            /search                Search [DONE]
├── 下载管理        /downloads             Downloads [DONE]
├── 订阅管理（展开）
│   ├── 电影订阅    /subscriptions/movies  MovieSubscriptions [DONE]
│   ├── 电视剧订阅  /subscriptions/tv      TvSubscriptions [DONE]
│   ├── 音乐订阅    /subscriptions/music   MusicSubscriptions [DONE]
│   └── 书籍订阅    /subscriptions/books   BookSubscriptions [DONE]
├── RSS订阅         /rss-subscriptions     RSSSubscriptions [DONE]
├── RSSHub订阅      /rsshub                RSSHub [DONE]
└── 工作流管理      /workflows             Workflows [DONE]
📌 订阅相关模块协作关系详见 SUBS_RULES_OVERVIEW.md
📌 本模块在完整下载流水线中的位置，详见 DOWNLOAD_MEDIA_PIPELINE_OVERVIEW.md

📚 阅读 & 听书
├── 阅读中心        /reading               ReadingHubPage [DONE]
├── 我的书架        /my/shelf              MyShelf [DONE]
├── 我的收藏        /reading/favorites     ReadingFavoriteShelf [TODO]
├── 小说中心        /novels                NovelCenter [WIP]
├── 有声书中心      /audiobooks            AudiobookCenter [DONE]
└── TTS 有声书      /tts/center            TTSCenter [WIP]

📖 漫画中心
├── 本地漫画库      /manga/library         MangaLibraryPage [WIP]
├── 漫画追更中心    /manga/following       MangaFollowCenter [WIP]
├── 远程漫画        /manga/remote          MangaRemoteExplorer [DONE]
├── 第三方漫画源    /manga/source-browser  MangaSourceBrowser [WIP]
└── 阅读历史        /manga/history         MangaHistoryPage [DONE]
📌 阅读/听书/漫画完整链路详见 READING_STACK_OVERVIEW.md

🎵 音乐中心
└── 音乐库          /music                 MusicCenter [WIP]

🤖 AI 中心 [Beta]
├── AI 实验室       /ai-lab                AiLab         [GENERIC]
├── AI 订阅助手     /ai-subs-assistant     AiSubsAssistant [SUBS_ADVISOR]
├── AI 故障医生     /ai-log-doctor         AiLogDoctor   [DIAGNOSE]
├── AI 整理顾问     /ai-cleanup-advisor    AiCleanupAdvisor [CLEANUP_ADVISOR]
├── AI 阅读助手     /ai-reading-assistant  AiReadingAssistant [READING_ASSISTANT]
└── AI 推荐         /recommendations       Recommendations
📌 AI 中心各页面与 Orchestrator 模式映射详见 AI_CENTER_UI_OVERVIEW.md

🌐 站点 & 插件
├── 站点管理        /site-manager          SiteManager [DONE]
├── HNR 风险检测    /hnr                   HNRMonitoring [PRO]
├── 插件市场        /plugins               Plugins [DONE]
├── Local Intel     /local-intel           LocalIntel [Dev, PRO]
└── 外部索引        /external-indexer      ExternalIndexer [Dev]
📌 站点/Local Intel/HR安全策略关系详见 SITE_INTEL_OVERVIEW.md

⚙️ 系统 & 设置
├── 系统设置        /settings              Settings [DONE]
├── 通知中心        /notifications         Notifications [DONE]
├── 任务中心        /tasks                 TaskCenter [DONE]
├── 实时日志        /log-center            LogCenter [DONE]
├── 存储监控        /storage-monitor       StorageMonitor [TODO]
├── 调度器监控      /scheduler-monitor     SchedulerMonitor [TODO]
├── 系统自检        /system-selfcheck      SystemSelfCheck [TODO]
├── 云存储管理      /cloud-storage         CloudStorage [DONE]
├── 媒体服务器      /media-servers         MediaServers [DONE]
└── 系统控制台      /admin                 AdminDashboard [DONE]

🔧 开发工具 [仅 Dev 模式]
├── GraphQL 实验室  /graphql-explorer      GraphQLExplorer [DONE]
├── 小说 Inbox 日志 /dev/novels/inbox      NovelInboxAdmin [DONE]
├── 漫画源配置      /dev/manga/sources     MangaSourceAdmin [DONE]
├── 目录配置        /directory-config      DirectoryConfig [DONE]
├── 媒体文件管理    /media-renamer         MediaRenamer [DONE]
├── 媒体整理        /file-browser          FileBrowser [DONE]
├── 转移历史        /transfer-history      TransferHistory [DONE]
└── 字幕管理        /subtitles             Subtitles [DONE]
```

---

## 2. 状态标记说明

- **[DONE]**: 前端页面已完成API对接，功能正常可用
- **[WIP]**: 前端页面存在但仅显示假数据，需要API对接
- **[TODO]**: 前端页面缺失，需要创建
- **[GENERIC]**: 通用AI页面，支持多种模式
- **[PRO]**: 专业版功能
- **[Dev]**: 开发模式专用

---

## 3. 主要数据来源（API/Service）

| 模块组 | 主要API端点 | 服务层 | 状态 |
|--------|------------|--------|------|
| 下载&订阅 | `/api/media/search`, `/api/downloads`, `/api/subscriptions/*`, `/api/rss`, `/api/rsshub`, `/api/workflows` | searchApi, downloadsApi, subscriptionsApi, rssApi, rsshubApi, workflowsApi | 全部对接完成 |
| 阅读&听书 | `/api/reading/*`, `/api/shelf`, `/api/audiobooks`, `/api/tts` | readingHubApi, myShelfApi, audiobookCenterApi, ttsUserApi | 核心功能对接完成 |
| 漫画中心 | `/api/manga/*` | mangaApi | 部分对接完成 |
| 音乐中心 | `/api/music` | musicApi | 基础对接完成 |
| 站点&插件 | `/api/sites`, `/api/hnr`, `/api/plugins`, `/api/local-intel`, `/api/external-indexer` | siteManagerApi, hnrApi, pluginsApi | 核心功能对接完成 |
| 系统&设置 | `/api/settings`, `/api/notifications`, `/api/tasks`, `/api/logs`, `/api/storage`, `/api/scheduler`, `/api/system/selfcheck` | settingsApi, notificationsApi, taskCenterApi, logsApi | 大部分对接完成 |

---

## 4. AI 页面详情

| 页面 | 路由 | 组件 | 说明 |
|------|------|------|------|
| AI 实验室 | `/ai-lab` | `AiLab.vue` | 调试 AI Orchestrator 的各种模式和工具，面向高级用户和开发者 |
| AI 订阅助手 | `/ai-subs-assistant` | `AiSubsAssistant.vue` | 从自然语言生成订阅工作流草案，需用户确认后才会创建真实订阅 |
| AI 故障医生 | `/ai-log-doctor` | `AiLogDoctor.vue` | 聚合系统健康、Runner 状态、日志快照，生成只读诊断报告 |
| AI 整理顾问 | `/ai-cleanup-advisor` | `AiCleanupAdvisor.vue` | 分析存储和媒体库，生成只读清理/洗版计划，不自动删除或移动 |
| AI 阅读助手 | `/ai-reading-assistant` | `AiReadingAssistant.vue` | 基于阅读/听书/漫画进度规划阅读优先级，不自动修改进度 |
| AI 推荐 | `/recommendations` | `Recommendations.vue` | 基于深度学习的个性化媒体推荐 |

**安全边界**：所有 AI 页面均为**只读顾问模式**，不会自动执行任何破坏性操作。

---

## 5. 其他重要页面

### 独立页面（无导航）

| 页面 | 路由 | 组件 | 说明 |
|------|------|------|------|
| 登录 | `/login` | `Login.vue` | 用户登录页 |
| 引导向导 | `/onboarding` | `OnboardingWizard.vue` | 首次使用引导 |
| 媒体详情 | `/media/:type/:tmdbId` | `MediaDetail.vue` | 影视详情页 |
| 人物详情 | `/person/:personId` | `PersonDetail.vue` | 演员/导演详情 |
| 小说阅读 | `/novels/:ebookId/read` | `NovelReader.vue` | 小说阅读器 |
| 漫画阅读 | `/manga/read/:series_id/:chapter_id?` | `MangaReaderPage.vue` | 漫画阅读器 |
| 作品详情 | `/works/:ebookId` | `WorkDetail.vue` | 电子书作品详情 |
| 115 播放 | `/remote/115/play/:workId` | `Remote115Player.vue` | 115 远程播放 |

### 设置子页面

| 页面 | 路由 | 组件 |
|------|------|------|
| 全局规则 | `/settings/global-rules` | `GlobalRulesSettings.vue` |
| 规则中心 | `/settings/rule-center` | `RuleCenter.vue` |
| 通知渠道 | `/settings/notify-channels` | `UserNotifyChannelsPage.vue` |
| 通知偏好 | `/settings/notify-preferences` | `UserNotifyPreferencesPage.vue` |

### 管理员页面

| 页面 | 路由 | 组件 |
|------|------|------|
| 系统控制台 | `/admin` | `AdminDashboard.vue` |
| 告警渠道 | `/admin/alert-channels` | `AlertChannelAdmin.vue` |
| 通知测试 | `/admin/notify-test` | `NotifyChannelTestPage.vue` |
| 系统自检 | `/admin/self-check` | `SelfCheckPage.vue` |

---

## 6. 路由配置文件

- **主路由**: `frontend/src/router/index.ts`
- **侧边栏**: `frontend/src/layouts/components/AppDrawer.vue`
- **主布局**: `frontend/src/layouts/MainLayout.vue`

---

## 7. UI-GLUE-1 完成情况总结

### 已完成API对接的页面（45个）
- 影视中心（6个）：全部完成
- 下载&订阅（9个）：全部完成，包括搜索、下载、各类订阅、RSS、RSSHub、工作流
- 阅读&听书（6个中的4个）：阅读中心、我的书架、有声书中心已完成
- 漫画中心（5个中的2个）：远程漫画、阅读历史已完成
- 音乐中心（1个）：基础对接完成
- 站点&插件（5个中的4个）：站点管理、插件市场等已完成
- 系统&设置（10个中的7个）：通知中心、任务中心、日志中心等已完成
- 开发工具（9个）：全部完成

### 仍需完成的页面（13个）
- 我的收藏、小说中心、TTS有声书
- 本地漫画库、漫画追更中心、第三方漫画源
- 音乐中心深度功能
- Local Intel、External Indexer专业功能
- 存储监控、调度器监控、系统自检

---

## 8. 维护约定

1. **新增页面时**：
   - 在 `router/index.ts` 添加路由
   - 在 `AppDrawer.vue` 添加导航入口（除非是独立页面）
   - 更新本文件

2. **导航分组调整时**：
   - 修改 `AppDrawer.vue`
   - 同步更新本文件的分组结构

3. **AI 页面变动时**：
   - 同时更新 `docs/FUTURE_AI_OVERVIEW.md` 中的"已落地 AI 场景"

4. **API对接状态更新时**：
   - 完成API对接后，将状态标记从[WIP]改为[DONE]
   - 更新主要数据来源表格

---

*最后更新：2025-12-03 UI-GLUE-1 完成*
