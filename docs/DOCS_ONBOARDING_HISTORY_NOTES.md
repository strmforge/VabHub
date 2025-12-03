# DOCS-ONBOARDING-HISTORY-1 巡检笔记

> 临时工作笔记，任务完成后可删除

---

## P2.1 README 与 SYSTEM_OVERVIEW 差异

### README 缺失的关键模块

1. **AI Orchestrator & AI 中心**
   - 5 个 AI 助手完全未提及
   - 外部 LLM + 本地 AI 器官架构未说明

2. **阅读 & 听书体系**
   - NovelToEbook / TTS / 有声书中心
   - Telegram 阅读控制台
   - 阅读进度统一

3. **漫画中心**
   - 第三方源适配（Komga/Kavita/OPDS/Suwayomi）
   - 追更 / 通知

4. **Local Intel 本地大脑**
   - HR/HNR 安全决策
   - TorrentIndex 本地索引
   - SiteGuard 站点保护

5. **站点 AI 适配**
   - CF Pages + Qwen 通道（专用于站点解析）

6. **Plugin Hub**
   - 插件生态简要提及但无链接

### README 过时/不准确的信息

- 后端端口：README 写 8000，实际是 8092
- 部分路径结构与实际不符
- 未提及 CONFIG_OVERVIEW.md / SYSTEM_SELF_CHECK_GUIDE.md

---

## P2.2 需要在 GETTING_STARTED 中体现的模块

按 NAV-STRUCTURE-CLEANUP-1 的导航分组：

1. 📺 **影视中心** – 电视墙、媒体库、115 播放
2. ⬇️ **下载 & 订阅** – 搜索、订阅、RSSHub
3. 📚 **阅读 & 听书** – TXT → EBook → TTS → 有声书
4. 📖 **漫画中心** – 第三方源、追更、阅读器
5. 🎵 **音乐 & 短剧** – 音乐订阅、榜单
6. 🤖 **AI 中心** – 5 个 AI 助手
7. 🌐 **站点 & 插件** – 站点墙、Local Intel、插件中心
8. ⚙️ **系统 & 设置** – 设置、通知中心、日志中心

---

## P5 历史称呼映射清单（草稿）

| 历史称呼 | 现版模块 | 状态 |
|----------|----------|------|
| 重命名/自动整理服务 | 媒体整理流程 | [NOW] |
| 云大脑 v1（分布式抓站） | N/A | [LEGACY] |
| Site Guard 全站行为监控 | Local Intel + SiteStats | [NOW] |
| 高阶 HR 策略中心 | Settings HR + Local Intel | [MERGED] |
| 小说管道 TXT→EBook→TTS | Novel/EBook/TTS 模块 | [NOW] |
| 漫画第三方源聚合 | MangaSource 框架 | [NOW]/[WIP] |
| 音乐榜单一条龙 | MUSIC-AUTOLOOP | [NOW] |
| 未来 AI 总控 | AI Orchestrator | [NOW] |
| GPU 大模型本地推理 | 深度学习推荐 | [OPTIONAL] |

---

*最后更新：2025-12-02*
