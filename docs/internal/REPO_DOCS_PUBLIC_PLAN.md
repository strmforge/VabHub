# REPO_DOCS_PUBLIC_PLAN

## P0. 文档分类与现状

### 文档分类

#### A类：必须保留的SSoT/用户指南文档（25+个）
- docs/VABHUB_SYSTEM_OVERVIEW.md
- docs/FUTURE_AI_OVERVIEW.md
- docs/FRONTEND_MAP.md
- docs/user/DEPLOY_WITH_DOCKER.md
- docs/user/GETTING_STARTED.md
- docs/admin/SITE_INTEL_OVERVIEW.md
- docs/admin/SUBS_RULES_OVERVIEW.md
- docs/admin/READING_STACK_OVERVIEW.md
- docs/PRE_RELEASE_CHECK_NOTES.md
- docs/RELEASE_NOTES_0.1.0-rc1.md
- docs/VABHUB_FEATURE_HISTORY_MAP.md
- docs/INDEX.md
- README.md
- LICENSE
- CHANGELOG.md

#### B类：可合并删除的开发文档（150+个）
- 各种完成总结：如 Intel实施完整总结.md、STRM系统完整实现总结.md
- 实施计划与报告：如 Fanart集成和NFO文件写入实现总结.md、LocalRedirect模式傻瓜式配置完成总结.md
- 对比分析：如 MoviePilot与VabHub-1深度对比分析.md、MoviePilot架构深度分析与VabHub对比报告.md
- 测试报告：如 TMDB和Fanart集成测试完成总结.md、Fanart和NFO测试结果总结.md
- 技术实现：如 Chain模式实现完成总结.md、StorageChain实现总结.md
- MODULES_*_ANALYSIS_TEMP.md 系列文件
- 各种功能完成总结：如 DOWNLOAD_CENTER_UI_V2_P6_SUMMARY_REPORT.md、NOVEL_FLOW_TTS_1_COMPLETION.md

#### C类：纯测试/临时文件（20+个）
- README-测试验证.md
- START_HERE-测试验证.md
- README_快速开始.md
- SHELF-HUB-FINISH-1-E2E-CHECKLIST.md
- PRE_RELEASE_SMOKE_SCENARIOS.md
- PRE_RELEASE_UI_CHECKLIST.md

### 处理目标

将B/C类文档合并为少量总览文档后删除原件，不再推送到公开仓库，只保留A类核心文档。

## P1. 公开文档白名单

### 根目录保留
- README.md
- LICENSE
- CHANGELOG.md

### docs/目录保留
- docs/INDEX.md
- docs/VABHUB_SYSTEM_OVERVIEW.md
- docs/FUTURE_AI_OVERVIEW.md
- docs/FRONTEND_MAP.md
- docs/DEPLOY_WITH_DOCKER.md
- docs/GETTING_STARTED.md
- docs/SITE_INTEL_OVERVIEW.md
- docs/SUBS_RULES_OVERVIEW.md
- docs/READING_STACK_OVERVIEW.md
- docs/KNOWN_LIMITATIONS.md
- docs/PRE_RELEASE_CHECK_NOTES.md
- docs/RELEASE_NOTES_0.1.0-rc1.md
- docs/VABHUB_FEATURE_HISTORY_MAP.md

## P2. 开发文档汇总计划

### 汇总文档
1. docs/dev/LEGACY_IMPLEMENTATION_NOTES_STRM_115_MOVIEPILOT.md
   - 115网盘集成
   - STRM系统
   - MoviePilot分析与对比
   - 视频字幕处理

2. docs/dev/LEGACY_IMPLEMENTATION_NOTES_MISC.md
   - 订阅/RSSHub
   - 密钥管理
   - 配置体系
   - Chain模式
   - AI功能
   - 媒体处理
   - 搜索系统

### 汇总内容结构
- 每个主题2-5条bullet，概括最终结论/教训/关键设计决定
- 按主题划分，而非按原文档
- 只保留结论级知识，不复制原文

## P3. 清理计划

### 清理范围
- 删除所有B/C类文档
- 只保留A类和汇总文档
- 创建local-notes/目录存放临时文档
- 添加local-notes/到.gitignore

## P4. Docker Compose文档增强

### README.md
- 快速开始部分添加docker-compose.yml示例
- 说明核心服务用途、端口、挂载卷
- 提供docker compose up -d命令

### docs/user/GETTING_STARTED.md
- 详细Docker Compose部署步骤
- 准备.env.docker → 检查挂载路径 → 启动服务 → 首次访问

### docs/user/DEPLOY_WITH_DOCKER.md
- 完整部署指南
- 说明各种可选项
- 强调Docker是唯一官方支持方式

## P5. 验证计划

- 检查git status确认跟踪文件干净
- 验证docs/目录只包含白名单文档
- 测试Docker Compose配置语法
- 确认README→GETTING_STARTED→DEPLOY_WITH_DOCKER路线清晰

## P6. 最终输出

- 新快照：VabHub-RC1-202512032320.7z
- 更新文档：
  - docs/VABHUB_SYSTEM_OVERVIEW.md（里程碑）
  - docs/README_FOR_DOCS_AUTHORS.md（规则）
  - docs/PRE_RELEASE_CHECK_NOTES.md（检查项）
  - docs/VABHUB_FEATURE_HISTORY_MAP.md（标记）