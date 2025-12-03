# NAV-STRUCTURE-CLEANUP-1 导航审计笔记

> 创建于 2025-12-02  
> 任务：NAV-STRUCTURE-CLEANUP-1 – 前端导航结构 & AI 入口梳理 v1

---

## P2 现状巡检结果

### 当前侧边栏分组（AppDrawer.vue）

```
核心功能
├── 首页总览 (/)
├── 仪表盘 (/dashboard)
├── 搜索 (/search)
├── 订阅管理 (/subscriptions)
├── RSS订阅 (/rss-subscriptions)
├── RSSHub订阅 (/rsshub)
├── 下载管理 (/downloads)
├── 站点管理 (/site-manager) [NEW]
├── 任务中心 (/tasks)
├── 目录配置 (/directory-config)
├── 分类配置 (/category-config)
├── 系统更新 (/system-update)
└── 媒体整理 (/file-browser)

阅读
├── 我的书架 (/my/shelf)
├── 阅读中心 (/reading)
├── 我的收藏 (/reading/favorites)
├── 小说中心 (/novels)
├── 有声书中心 (/audiobooks)
├── 音乐库 (/music) ← 命名冲突：与"音乐管理"重复
├── 远程漫画 (/manga/remote)
├── 第三方漫画源 (/manga/source-browser)
├── 本地漫画库 (/manga/library)
├── 漫画追更中心 (/manga/following)
├── 漫画阅读历史 (/manga/history)
├── 电视墙 (/player/wall) ← 不属于"阅读"
└── 转移历史 (/transfer-history) ← 不属于"阅读"

开发工具 (Dev)
├── 小说 Inbox / 导入日志 (/dev/novels/inbox) [Dev]
└── 漫画源配置 (/dev/manga/sources) [Dev]

VabHub 特色
├── 音乐管理 (/music) [特色] ← 与"音乐库"路由冲突
├── 短剧工作台 (/short-drama) [NEW]
├── GraphQL 实验室 (/graphql-explorer) [调试]
├── AI推荐 (/recommendations) [AI]
├── HNR风险检测 (/hnr) [PRO]
└── 多模态分析监控 (/multimodal-monitoring) [AI]

其他功能
├── 发现 (/discover)
├── 日历 (/calendar)
├── 站点管理 (/sites) ← 与"核心功能"里的站点管理重复
├── 工作流管理 (/workflows)
├── 通知中心 (/notifications)
├── 实时日志中心 (/log-center)
├── 插件市场 (/plugins)
├── 设置 (/settings)
├── 系统控制台 (/admin)
├── 漫画源配置 (/settings/manga-sources) ← 与"开发工具"重复
├── 云存储管理 (/cloud-storage)
├── 存储监控 (/storage-monitor)
├── 调度器监控 (/scheduler-monitor)
├── [Dev] Local Intel (/local-intel) [PRO]
├── [Dev] 外部索引 (/external-indexer) [实验]
├── 系统自检 (/system-selfcheck) [Beta]
├── 媒体服务器 (/media-servers)
├── 媒体文件管理 (/media-renamer)
└── 字幕管理 (/subtitles)
```

### 🚨 关键问题：5 个 AI 页面无入口

以下 5 个 AI 页面在路由中存在，但**侧边栏完全没有入口**：

| 页面 | 路由 | 组件 | 状态 |
|------|------|------|------|
| AI 实验室 | `/ai-lab` | AiLab.vue | Beta, 无入口 |
| AI 订阅助手 | `/ai-subs-assistant` | AiSubsAssistant.vue | Beta, 无入口 |
| AI 故障医生 | `/ai-log-doctor` | AiLogDoctor.vue | Beta, 无入口 |
| AI 整理顾问 | `/ai-cleanup-advisor` | AiCleanupAdvisor.vue | Beta, 无入口 |
| AI 阅读助手 | `/ai-reading-assistant` | AiReadingAssistant.vue | Beta, 无入口 |

用户只能通过手动输入 URL 访问这些页面。

### 其他发现的问题

1. **重复入口**：
   - 站点管理：`/site-manager`（核心功能）和 `/sites`（其他功能）
   - 漫画源配置：`/dev/manga/sources`（开发工具）和 `/settings/manga-sources`（其他功能）
   - 音乐：`/music` 被"阅读-音乐库"和"VabHub特色-音乐管理"同时使用

2. **分组不合理**：
   - "电视墙"和"转移历史"放在"阅读"分组下，但与阅读无关
   - "其他功能"分组过于庞大，混杂了运维、设置、开发等多种类型

3. **命名不一致**：
   - "音乐库" vs "音乐管理"
   - 两个"站点管理"

---

## P3 目标导航蓝图

### 目标分组结构

```
📺 影视中心
├── 首页总览 (/)
├── 电视墙 (/player/wall)
├── 媒体库 (/library)
├── 发现 (/discover)
└── 日历 (/calendar)

⬇️ 下载 & 订阅
├── 搜索 (/search)
├── 下载管理 (/downloads)
├── 订阅管理 (/subscriptions)
├── RSS订阅 (/rss-subscriptions)
├── RSSHub订阅 (/rsshub)
└── 工作流管理 (/workflows)

📚 阅读 & 听书
├── 阅读中心 (/reading)
├── 我的书架 (/my/shelf)
├── 我的收藏 (/reading/favorites)
├── 小说中心 (/novels)
├── 有声书中心 (/audiobooks)
└── TTS 有声书中心 (/tts/center)

📖 漫画中心
├── 本地漫画库 (/manga/library)
├── 漫画追更中心 (/manga/following)
├── 远程漫画 (/manga/remote)
├── 第三方漫画源 (/manga/source-browser)
└── 漫画阅读历史 (/manga/history)

🎵 音乐中心
├── 音乐库 (/music)
└── 短剧工作台 (/short-drama)

🤖 AI 中心 (NEW)
├── AI 实验室 (/ai-lab) [Beta]
├── AI 订阅助手 (/ai-subs-assistant) [Beta]
├── AI 故障医生 (/ai-log-doctor) [Beta]
├── AI 整理顾问 (/ai-cleanup-advisor) [Beta]
└── AI 阅读助手 (/ai-reading-assistant) [Beta]

🌐 站点 & 插件
├── 站点管理 (/site-manager)
├── HNR风险检测 (/hnr) [PRO]
├── 插件市场 (/plugins)
└── Local Intel (/local-intel) [PRO, Dev]

⚙️ 系统 & 设置
├── 系统设置 (/settings)
├── 通知中心 (/notifications)
├── 任务中心 (/tasks)
├── 实时日志中心 (/log-center)
├── 存储监控 (/storage-monitor)
├── 调度器监控 (/scheduler-monitor)
├── 系统自检 (/system-selfcheck) [Beta]
├── 云存储管理 (/cloud-storage)
├── 媒体服务器 (/media-servers)
└── 系统控制台 (/admin)

🔧 开发工具 (仅 Dev 模式显示)
├── GraphQL 实验室 (/graphql-explorer)
├── 漫画源配置 (/dev/manga/sources)
├── 小说 Inbox 日志 (/dev/novels/inbox)
└── ...其他 /dev/* 页面
```

### AI 页面角色说明（文案蓝本）

| 页面 | 角色说明 |
|------|----------|
| AI 实验室 | 调试 AI Orchestrator 的各种模式和工具，面向高级用户和开发者。 |
| AI 订阅助手 | 从自然语言生成订阅工作流草案，需用户确认后才会创建真实订阅。 |
| AI 故障医生 | 聚合系统健康、Runner 状态、日志快照，生成只读诊断报告帮助排查问题。 |
| AI 整理顾问 | 分析存储和媒体库，生成只读清理/洗版计划，不会自动删除或移动任何文件。 |
| AI 阅读助手 | 基于阅读/听书/漫画进度，规划阅读优先级和计划，不自动修改任何进度。 |

---

## 实现清单（已完成）

### P4 侧边栏菜单重构 ✅
- [x] 按目标分组重构 AppDrawer.vue
- [x] 新增"AI 中心"分组，包含 5 个 AI 页面入口
- [x] 移除重复入口（站点管理、漫画源配置）
- [x] 调整"电视墙"、"转移历史"到合理分组

### P5 AI 页面文案补充 ✅
- [x] 5 个 AI 页面已有完善的顶部说明文案
- [x] 均强调"只读"和"需用户确认"

### P6 文档更新 ✅
- [x] 创建 docs/FRONTEND_MAP.md
- [x] 更新 VABHUB_SYSTEM_OVERVIEW.md 里程碑和前端引用
- [x] FUTURE_AI_OVERVIEW.md 已是最新（v1.0）

---

*NAV-STRUCTURE-CLEANUP-1 任务完成于 2025-12-02*
