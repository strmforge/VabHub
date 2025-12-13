# VabHub 前端路由地图

> 本文件是前端页面/路由/导航结构的单一事实来源。  
> 更新于 2025-12-13，任务 VABHUB-0.0.2-UI-BASELINE。

---

## 1. 导航分组结构

侧边栏导航（`AppDrawer.vue`）按以下分组组织：

```
📺 影视中心
├── 首页总览        /                      HomeDashboard
├── 电视墙          /player/wall           PlayerWall
├── 媒体库          /library               Library
├── 发现            /discover              Discover
├── 日历            /calendar              Calendar
└── 短剧工作台      /short-drama           ShortDrama
📌 电视墙播放策略（LAN/WAN/115）详见 TV_WALL_PLAYBACK_OVERVIEW.md

⬇️ 下载 & 订阅
├── 搜索            /search                Search [NOW]
├── 下载管理        /downloads             Downloads [NOW]
│   └── 支持下载限速弹窗（SpeedLimitDialog），可设置单任务/批量/全局限速
├── 订阅管理（展开）
│   ├── 电影订阅    /subscriptions/movies  MovieSubscriptions [NOW]
│   ├── 电视剧订阅  /subscriptions/tv      TvSubscriptions [NOW]
│   ├── 音乐订阅    /subscriptions/music   MusicSubscriptions [NOW]
│   └── 书籍订阅    /subscriptions/books   BookSubscriptions [NOW]
├── RSS订阅         /rss-subscriptions     RSSSubscriptions [NOW]
├── RSSHub订阅      /rsshub                RSSHub [NOW]
└── 工作流管理      /workflows             Workflows [NOW]
📌 订阅相关模块协作关系详见 SUBS_RULES_OVERVIEW.md
📌 本模块在完整下载流水线中的位置，详见 DOWNLOAD_MEDIA_PIPELINE_OVERVIEW.md

📚 阅读 & 听书 & 漫画
├── 阅读中心        /reading               ReadingHubPage [NOW]
├── 我的书架        /my/shelf              MyShelf [NOW]
├── 我的收藏        /reading/favorites     ReadingFavoriteShelf [NOW]
├── 小说中心        /novels                NovelCenter [NOW]
├── 有声书中心      /audiobooks            AudiobookCenter [NOW]
├── TTS 有声书      /tts/center            TTSCenter [NOW]
├── 本地漫画库      /manga/library         MangaLibraryPage [NOW]
├── 漫画追更中心    /manga/following       MangaFollowCenter [NOW]
├── 远程漫画        /manga/remote          MangaRemoteExplorer [NOW]
├── 第三方漫画源    /manga/source-browser  MangaSourceBrowser [NOW]
└── 阅读历史        /manga/history         MangaHistoryPage [NOW]
📌 阅读/听书/漫画完整链路详见 READING_STACK_OVERVIEW.md

🎵 音乐中心
├── 音乐库          /music                 MusicCenter [NOW]
└── 榜单 & 订阅    /subscriptions/music   MusicSubscriptions [NOW]

🤖 AI 中心 [Beta]
├── AI 实验室       /ai-lab                AiLab         [GENERIC]
├── AI 订阅助手     /ai-subs-assistant     AiSubsAssistant [SUBS_ADVISOR]
├── AI 故障医生     /ai-log-doctor         AiLogDoctor   [DIAGNOSE]
├── AI 整理顾问     /ai-cleanup-advisor    AiCleanupAdvisor [CLEANUP_ADVISOR]
├── AI 阅读助手     /ai-reading-assistant  AiReadingAssistant [READING_ASSISTANT]
└── AI 推荐         /recommendations       Recommendations [NOW]
📌 AI 中心各页面与 Orchestrator 模式映射详见 AI_CENTER_UI_OVERVIEW.md

🛡️ 站点 & 安全
├── 站点管理        /site-manager          SiteManager [NOW]
├── HNR 风险检测    /hnr                   HNRMonitoring [PRO] [NOW]
├── 插件市场        /plugins               Plugins [NOW]
├── Local Intel     /local-intel           LocalIntel [Dev, PRO] [NOW]
└── 外部索引        /external-indexer      ExternalIndexer [Dev] [NOW]
📌 站点/Local Intel/HR安全策略关系详见 SITE_INTEL_OVERVIEW.md

⚙️ 系统 & 设置
├── 系统设置        /settings              Settings [NOW]
├── 通知中心        /notifications         Notifications [NOW]
├── 任务中心        /tasks                 TaskCenter [NOW]
├── 实时日志        /log-center            LogCenter [NOW]
├── 存储监控        /storage-monitor       StorageMonitor [NOW]
├── 调度器监控      /scheduler-monitor     SchedulerMonitor [NOW]
├── 系统自检        /system-selfcheck      SystemSelfCheck [NOW]
├── 云存储管理      /cloud-storage         CloudStorage [NOW]
├── 媒体服务器      /media-servers         MediaServers [NOW]
└── 系统控制台      /admin                 AdminDashboard [NOW]

🔧 开发工具 [仅 Dev 模式]
├── GraphQL 实验室  /graphql-explorer      GraphQLExplorer
├── 小说 Inbox 日志 /dev/novels/inbox      NovelInboxAdmin
├── 漫画源配置      /dev/manga/sources     MangaSourceAdmin
├── 目录配置        /directory-config      DirectoryConfig
├── 媒体文件管理    /media-renamer         MediaRenamer
├── 媒体整理        /file-browser          FileBrowser
├── 转移历史        /transfer-history      TransferHistory
└── 字幕管理        /subtitles             Subtitles
```

---

## 2. AI 页面详情

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

## 3. 其他重要页面

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

## 4. 路由配置文件

- **主路由**: `frontend/src/router/index.ts`
- **侧边栏**: `frontend/src/layouts/components/AppDrawer.vue`
- **主布局**: `frontend/src/layouts/MainLayout.vue`

---

## 5. 维护约定

1. **新增页面时**：
   - 在 `router/index.ts` 添加路由
   - 在 `AppDrawer.vue` 添加导航入口（除非是独立页面）
   - 更新本文件

2. **导航分组调整时**：
   - 修改 `AppDrawer.vue`
   - 同步更新本文件的分组结构

3. **AI 页面变动时**：
   - 同时更新 `docs/FUTURE_AI_OVERVIEW.md` 中的"已落地 AI 场景"

---

*最后更新：2025-12-13 VABHUB-0.0.2-UI-BASELINE（导航重组、版本 0.0.2、发现页增强）*
