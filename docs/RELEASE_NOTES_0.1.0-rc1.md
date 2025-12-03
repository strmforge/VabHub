<!--
VabHub 0.1.0-rc1 Release Notes（内部预发布版）

用途：
- 给人类和 AI / IDE 快速理解"这一版 RC 到底包含了什么能力"
- 对齐系统总览 / AI 总览 / 各专题文档的视角
-->

# VabHub 0.1.0-rc1 Release Notes（内部 RC）

## 1. 版本概览
- 版本名：VabHub 0.1.0-rc1（内部预发布）
- 日期：2025-12-03
- 适用人群：项目作者 & 内部测试 & 高阶 NAS/PT 玩家
- 状态：仅供 RC 试用，不推荐大规模生产部署

## 2. 核心变化摘要（一屏读懂）
- 导航 & UI：完成导航重构 & UI glue & 布局调优，形成统一的导航结构和视觉风格
- 下载 & 媒体管线：实现从搜索/订阅到下载/整理/入库/播放的完整流水线
- 阅读 / 听书 / 漫画：完成小说→EBook→TTS→有声书链路，漫画追更→通知闭环
- 站点 & Local Intel & External Indexer：实现 Local Intel / TorrentIndex / External Indexer / HR 策略联动
- AI 中心 & Orchestrator：AI Orchestrator + 5 个 AI 页面（实验室/订阅助手/故障医生/整理顾问/阅读助手）
- 配置体系 & 自检工具：建立配置自检和系统预发布检查机制
- 文档矩阵 & 历史对照：形成完整的文档体系，包括系统总览、AI 总览、各专题文档等

## 3. 模块级亮点（按 SYSTEM_OVERVIEW 模块划分）
### 3.1 影视 / 电视墙 & 播放
- 完成 TVWALL-LOCAL-LIB-PLAY-1，实现电视墙本地媒体库播放
- 支持局域网/外网/115 播放策略，详见 TV_WALL_PLAYBACK_OVERVIEW.md
- 实现电视墙作为选片中枢，支持多种播放场景

### 3.2 下载 & 订阅 & 流水线
- 完成 SUBS-MODULE-UI-1 / SUBS-RULES-OVERVIEW-1 / DOWNLOAD-MEDIA-PIPELINE-OVERVIEW-1
- 实现从搜索/订阅→下载→整理→入库→播放的完整流水线
- 支持多种下载器集成，提供统一的下载管理界面

### 3.3 阅读 & 听书 & 漫画 & Shelf
- 完成小说→EBook→TTS→有声书链路，支持从小说文件到有声书中心播放
- 实现漫画追更→Runner 拉新章节→通知中心/TG 反馈闭环
- 支持音乐订阅自动循环，从订阅配置→AutoLoop 执行→下载完成→媒体库可见

### 3.4 站点 & Local Intel & External Indexer
- 完成 SITE-INTEL-OVERVIEW-1，实现 Local Intel / TorrentIndex / External Indexer / HR 策略联动
- 支持站点管理、本地智能索引、外部索引器接入
- 实现 HR 风险检测和安全策略

### 3.5 AI 中心 & Orchestrator
- 完成 FUTURE-AI-ORCHESTRATOR-1，实现 AI Orchestrator 框架
- 支持 5 种 AI 模式：GENERIC / SUBS_ADVISOR / DIAGNOSE / CLEANUP_ADVISOR / READING_ASSISTANT
- 提供 5 个 AI 页面：AI 实验室/订阅助手/故障医生/整理顾问/阅读助手

### 3.6 配置体系 & 自检工具
- 完成 CONFIG-SELF-CHECK-1，建立配置自检和系统预发布检查机制
- 整理配置总览与自检指南，统一 config.py / .env.example 分组与注释
- 创建 CONFIG_OVERVIEW.md 和 SYSTEM_SELF_CHECK_GUIDE.md
- 提供"5 分钟基础健康检查"和"15 分钟深度检查"命令集
- 整理常见问题排查工具、应急恢复与故障处理流程
- 对接 services/health_checks.py，统一外部依赖检查入口

### 3.7 UI 导航 & 布局优化
- 完成 NAV-STRUCTURE-CLEANUP-1，重构前端导航结构，新增"AI 中心"分组统一 5 个 AI 页面入口
- 优化 8 个导航分组，创建 FRONTEND_MAP.md 路由文档
- 完成 UI-GLUE-1，前端导航下各模块与既有后端能力完成首次全面拼接
- 完成 UI-GLUE-FILL-GAPS-1，按 UI_GAPS_OVERVIEW.md 标记，完成所有 [WIP]/[TODO] 页面的真实 API 对接
- 完成 UI-LAYOUT-TUNING-1，对关键页面的布局和信息层级进行统一调整
- 完成 UI-FEEDBACK-FIX-1，基于真实使用反馈对关键页面进行点状 UI 修复

## 4. 已知限制 & 暂不处理事项（概览）
- **功能层面限制**：部分高级功能（如 HR 风险检测）需要额外配置才能使用；非媒体资源只在下载管理中可见
- **性能与规模**：本版本未针对 10w+ 种子/媒体库进行压测，大规模媒体库下部分操作可能耗时较长
- **部署与环境**：当前仅提供单机 docker-compose 模式，未提供 k8s Helm Chart；日志/监控/备份工具集成需要用户自行安排
- **AI & 外部服务**：AI Orchestrator 默认为 Dummy LLM，未配置真实 LLM 时所有 AI 页面仅作演示
- **测试与质量**：部分功能缺乏完整的测试覆盖，部分 UI 组件可能存在无障碍访问问题
- **文档与配置**：部分文档可能与代码存在不一致，部分配置项的说明不够详细

## 5. 升级 & 使用建议
- **推荐用法**：将 0.1.0-rc1 当作"新起点"，后续版本以此为基准
- **部署建议**：RC1 阶段在文档层面已经确立"Docker-only 官方部署线路"，推荐使用 Docker/docker-compose 部署
- **验证建议**：先按 DEPLOY_WITH_DOCKER.md 快速启动，再用 PRE_RELEASE_SMOKE_SCENARIOS.md 验证基本链路
- **环境建议**：不建议直接拿 RC 投产在"业务必须 7x24 稳定"的环境中
- **升级提示**：如从老版本升级，建议先备份数据，再按最新文档重新配置

## 6. 关联文档索引
- [VABHUB_SYSTEM_OVERVIEW.md](VABHUB_SYSTEM_OVERVIEW.md) - 系统总览（模块地图）
- [FUTURE_AI_OVERVIEW.md](FUTURE_AI_OVERVIEW.md) - AI 架构与模式
- [SUBS_RULES_OVERVIEW.md](SUBS_RULES_OVERVIEW.md) - 订阅体系总览
- [READING_STACK_OVERVIEW.md](READING_STACK_OVERVIEW.md) - 阅读栈总览
- [SITE_INTEL_OVERVIEW.md](SITE_INTEL_OVERVIEW.md) - 站点智能栈总览
- [TV_WALL_PLAYBACK_OVERVIEW.md](TV_WALL_PLAYBACK_OVERVIEW.md) - 电视墙播放策略
- [DOWNLOAD_MEDIA_PIPELINE_OVERVIEW.md](DOWNLOAD_MEDIA_PIPELINE_OVERVIEW.md) - 下载媒体流水线
- [AI_CENTER_UI_OVERVIEW.md](AI_CENTER_UI_OVERVIEW.md) - AI 中心 UI 总览
- [PRE_RELEASE_CHECK_NOTES.md](PRE_RELEASE_CHECK_NOTES.md) - 预发布检查笔记
- [PRE_RELEASE_UI_CHECKLIST.md](PRE_RELEASE_UI_CHECKLIST.md) - UI 检查清单
- [PRE_RELEASE_SMOKE_SCENARIOS.md](PRE_RELEASE_SMOKE_SCENARIOS.md) - 冒烟测试脚本
- [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) - 已知限制文档
- [GETTING_STARTED.md](GETTING_STARTED.md) - 新用户上手指南