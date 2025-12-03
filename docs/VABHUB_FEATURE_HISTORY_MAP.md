# VabHub 功能历史对照表

> 把历史聊天中的概念/老名字映射到当前模块，让新窗口 AI / IDE 能快速理解"你在说的是哪块"。

---

## 0. 使用说明（给 AI / IDE / 人类）

### 0.1 本文用途

- 将历史讨论中的概念、老名字映射到当前模块
- 标记状态：`[NOW]`（已融入现版）、`[RENAMED]`、`[MERGED]`、`[LEGACY]`、`[PLANNED]`
- 帮助新窗口 AI 理解历史背景，避免重复沟通

### 0.2 状态标记说明

| 标记 | 含义 |
|------|------|
| `[NOW]` | 已落地，当前版本可用 |
| `[RENAMED]` | 已改名，功能保留 |
| `[MERGED]` | 已合并到其他模块 |
| `[LEGACY]` | 已废弃或明确放弃 |
| `[PLANNED]` | 计划中，尚未实现 |
| `[OPTIONAL]` | 可选功能，非必需 |

### 0.3 给新窗口 AI 的提醒

> 当用户提到某个你不认识的模块名称时，请先在本文件中搜索，看它是不是一个历史称呼或已合并模块。  
> 若本文件与 `VABHUB_SYSTEM_OVERVIEW.md` / `FUTURE_AI_OVERVIEW.md` 有冲突，以后两者为准，但请在任务书中安排更新本文件。

---

## 1. 核心演进主线（简版时间轴）

```
2024-Q1  本地重命名/整理服务 → VabHub 媒体自动化平台雏形
2024-Q2  引入 Local Intel / External Indexer / 站点 AI 适配通道
2024-Q3  引入小说→TTS→有声书链路、漫画中心、音乐订阅
2024-Q4  引入 Plugin Hub / 插件中心
2025-Q1  引入 AI Orchestrator & 5 个 AI 助手（订阅/故障/整理/阅读/实验室）
2025-Q1  放弃云大脑 v1（跨用户目录聚合），改为"本地大脑 + 规则包共享设想"
2025-12  NAV-STRUCTURE-CLEANUP-1：前端导航分组统一，AI 中心入口落地
2025-12  CONFIG-SELF-CHECK-1：配置总览与自检指南统一
2025-12  RELEASE-NOTES-RC1-1：VabHub 0.1.0-rc1 内部 RC 版本发布，统一版本号与元数据
2025-12  REPO-DOCS-PUBLIC-1：完成文档精简 + 公共部署说明强化
2025-12  REPO-DOCS-ROOT-MD-TRIM-1：根目录 Markdown 文档清理
2025-12  REPO-SCRIPTS-ORGANIZE-1：根目录脚本归档与规范化
2025-12  CI-FRONTEND-PNPM-1：前端 CI 工具链调整，统一使用 Node 20 + pnpm/action-setup 安装 pnpm
2025-12  CI-BACKEND-AIOSQLITE-1：修复后端 CI 中缺失 aiosqlite 导致 API 启动失败的问题
2025-12  CI-BACKEND-PYTEST-2：后端自检脚本与 CI 测试依赖收敛，确保 CI 环境下必跑 pytest
```

---

## 2. 旧称 → 现版模块 对照表

| 历史称呼 / 早期设想 | 当前模块 / 名称 | 状态 | 说明 |
|---------------------|-----------------|------|------|
| 重命名/自动整理服务 | 媒体整理流程（下载后处理） | `[NOW]` | 整合到下载完成后的媒体整理 pipeline |
| 云大脑 v1（分布式抓站 + 共享识别词） | N/A | `[LEGACY]` | 出于成本与合规考虑已停用，只保留本地大脑 |
| Site Guard 全站行为监控 | Local Intel + SiteStats + SiteAccessConfig | `[NOW]` | 分解为本地智能大脑的多个组件 |
| 高阶 HR 策略中心 | Settings HR 区域 + Local Intel HR 决策 | `[MERGED]` | 不再是独立模块，融入设置与 Local Intel |
| HR/HNR 风险检测中心 | Local Intel HNR 模块 + 站点保护策略 | `[NOW]` | 内置于 Local Intel，提供风险评分和策略 |
| 小说自动管道：TXT → EBook → TTS → 有声书 | NovelToEbookPipeline + TTS Runner + 有声书中心 | `[NOW]` | 已在阅读 & 听书中心落地 |
| Telegram 阅读控制台 | Telegram Bot 阅读模块 | `[NOW]` | 配合 Telegram Bot 控制阅读/TTS |
| 漫画第三方源聚合 | MangaSource 适配框架 + 漫画中心 | `[NOW]/[WIP]` | 支持 Komga/Kavita/OPDS/Suwayomi，自建源按 Phase 扩展 |
| 音乐榜单订阅一条龙 | MUSIC-AUTOLOOP + TG-BOT-MUSIC-1 | `[NOW]` | 整合 RSSHub/订阅/自动循环/Telegram 控制台 |
| 未来 AI 总控 | AI Orchestrator + AI 中心 5 页面 | `[NOW]` | 已实现多模式只读 AI 助手 |
| AI 订阅助手 | SUBS_ADVISOR 模式 + /ai-subs-assistant | `[NOW]` | 自然语言 → 订阅工作流草案 |
| AI 故障医生 | DIAGNOSE 模式 + /ai-log-doctor | `[NOW]` | 系统健康诊断 + 建议步骤 |
| AI 整理顾问 | CLEANUP_ADVISOR 模式 + /ai-cleanup-advisor | `[NOW]` | 存储分析 + 清理计划草案 |
| AI 阅读助手 | READING_ASSISTANT 模式 + /ai-reading-assistant | `[NOW]` | 阅读计划 + 优先级建议 |
| GPU 大模型本地一键推理 | 深度学习推荐系统 (NCF/DeepFM/AE) | `[RENAMED]/[OPTIONAL]` | 仅作为推荐模块加速选项，不是 AI 总控硬前提 |
| External Indexer | External Indexer 模块 | `[NOW]` | 外部索引器接入（如 Prowlarr） |
| 站点 AI 适配通道 | CF Pages + Qwen2.5-Coder-7B-Instruct | `[NOW]` | 专用于站点结构解析，不做通用 LLM |
| Plugin Hub | 插件中心 + strmforge/vabhub-plugins | `[NOW]` | 官方插件索引 + 本地插件管理 |
| 工作流系统 | Workflow 模块 + 工作流设计器 | `[NOW]` | 可视化工作流，事件驱动自动化 |
| 通知中心 | Notification 模块 | `[NOW]` | 多渠道通知（微信/邮件/Telegram/Webhook） |

---

## 3. 已明确放弃或改道的构想

### 3.1 云大脑 v1 – `[LEGACY]`

- **原始设想**：跨用户 PT 站点目录聚合，实现"共享识别词/共享种子元数据"
- **放弃原因**：成本高、合规风险、维护复杂
- **替代方案**：Local Intel 本地大脑 + 未来可能的"规则包/词典共享"（离线分发）

### 3.2 CF + Qwen 通道当通用 LLM – `[LEGACY]`

- **原始设想**：复用站点 AI 适配通道做通用聊天/推荐
- **放弃原因**：安全边界不清、滥用风险
- **当前状态**：CF + Qwen 只做站点结构解析，Orchestrator 走独立 LLM Endpoint

### 3.3 激进的一键清理/自动修复 – `[LEGACY]`

- **原始设想**：AI 直接执行删除、移动、修改配置
- **放弃原因**：风险过高，用户可能误操作
- **当前状态**：统一收敛到"AI 只读建议 + 手动执行"模式

---

## 4. 仍然可能在未来实现的方向

| 方向 | 状态 | 说明 |
|------|------|------|
| 订阅/搜索规则中心 v2 | `[PLANNED]` | 更强大的规则编辑器 + 规则包导入导出 |
| 站点诊断中心 / 日志可视化 | `[PLANNED]` | 站点访问日志可视化分析 |
| 更细粒度的 HR 安全策略 UI | `[PLANNED]` | 可视化 HR 策略配置 |
| 规则包 / 别名词典共享 v2 | `[PLANNED]` | 离线分发识别词和规则包 |
| 漫画自建源扩展 | `[WIP]` | 更多第三方源适配 |
| 短剧中心完善 | `[PLANNED]` | 类似漫画中心的短剧管理 |

> 详见 `FUTURE_AI_OVERVIEW.md` §7 和 `VABHUB_SYSTEM_OVERVIEW.md` 中的 `[PLANNED]` 项。

---

## 5. 写给未来 AI / IDE 的提醒

1. **当用户提起某个你不认识的模块名称时**，请先在本文件 §2 表格中搜索，看它是不是一个历史称呼或已合并模块。

2. **若本文件与 `VABHUB_SYSTEM_OVERVIEW.md` / `FUTURE_AI_OVERVIEW.md` 有冲突**，以后两者为准，但请在任务书中安排更新本文件，保持同步。

3. **新增模块或重命名时**，请同步更新本文件：
   - 在 §2 表格中添加新条目
   - 如有废弃，在 §3 中说明原因和替代方案

---

*最后更新：2025-12-04 CI-BACKEND-PYTEST-2*
