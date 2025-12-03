# REPO_HYGIENE_NOTES

## P0: 现状巡检结果

### 1. 根目录文件分析

#### 核心用户入口文件
- ✅ README.md - 项目主文档
- ✅ docker-compose.yml - Docker 部署配置
- ✅ docker-compose.prod.yml - 生产环境 Docker 配置
- ✅ .env.example - 环境变量示例
- ✅ .env.docker.example - Docker 环境变量示例
- ✅ docs/ - 文档目录

#### 纯开发文档/设计记录
- ❌ 大量散落在根目录的开发文档和阶段任务书（数百个 .md 文件）
- ❌ 各种测试报告、修复总结、实施计划等
- ❌ 前端和后端的启动脚本
- ❌ 各种配置说明文件

#### 其他零散文件
- ❌ 各种批处理文件（.bat）
- ❌ 测试脚本
- ❌ 临时笔记和实验记录

### 2. docs 目录结构

- docs/ 下约 60 个 .md 文件

#### SSoT 文档（已确认的）
- VABHUB_SYSTEM_OVERVIEW.md
- DEPLOY_WITH_DOCKER.md
- GETTING_STARTED.md
- CONFIG_OVERVIEW.md
- SITE_INTEL_OVERVIEW.md
- SUBS_RULES_OVERVIEW.md
- READING_STACK_OVERVIEW.md
- FUTURE_AI_OVERVIEW.md
- FRONTEND_MAP.md
- README_FOR_DOCS_AUTHORS.md

#### 非 SSoT 开发文档
- 各种 Phase 任务书
- 实现笔记
- 实验记录
- 阶段分析报告
- 修复总结

### 3. LICENSE 状态

- ❌ 根目录缺失 LICENSE / LICENSE.md / COPYING 文件
- ✅ README.md 有 MIT License 徽章
- ✅ README.md 有 License 章节，但链接到不存在的 LICENSE 文件
- ✅ package.json（前端）中可能声明了 license
- ❌ 后端配置文件中未检查到 license 字段

### 4. 结论

- 当前仓库根目录对 GitHub 访客而言显得杂乱，包含大量开发文档和临时文件
- 开发文档数量接近几百个，主要分布在根目录和 docs/ 目录
- LICENSE 当前状态：缺失实体文件，仅在 README 中提及 MIT 协议

## P1: 文档分层与可见性策略

### 1. 文档受众层级

#### 用户向
- 安装、部署、基本功能说明
- GETTING_STARTED.md
- DEPLOY_WITH_DOCKER.md
- 简单功能概览

#### 高级用户/运维向
- CONFIG_OVERVIEW.md
- SITE_INTEL_OVERVIEW.md
- SUBS_RULES_OVERVIEW.md
- READING_STACK_OVERVIEW.md
- BACKUP_AND_RESTORE.md

#### 开发者/项目维护者向
- 详细 Phase 任务书
- 实现笔记
- 实验记录
- 设计文档

### 2. docs 子目录结构规划

```
docs/
├── user/          # 普通用户文档
├── admin/         # 高级用户/运维文档
├── dev/           # 开发者文档
├── internal/      # 内部文档（AI/IDE 使用）
└── INDEX.md       # 文档索引
```

### 3. GitHub 访客视角设计

- GitHub 仓库主页 → README.md → docs/INDEX.md
- 用户只需要点 1–2 次就能到达：
  - 如何部署（Docker-only）
  - 如何快速体验
  - 常见问题

### 4. 开发文档策略

- 根目录保持极简
- docs/ 内部合理分层
- README 清晰引导
- 开发文档仍在 repo，但普通用户不被打扰

## P2: 文档物理归类计划

### 1. 根目录清理

保留：
- README.md
- LICENSE（待添加）
- .env.example
- .env.docker.example
- docker-compose.yml
- docker-compose.prod.yml
- backend/（目录）
- frontend/（目录）
- docs/（目录）
- plugins/（目录）
- resources/（目录）
- services/（目录）
- tools/（目录）
- .gitignore
- .github/（目录）

迁移到 docs/dev/ 或 docs/internal/：
- 所有散落在根目录的 .md 文档
- 各种测试报告、修复总结、实施计划
- 前端和后端的启动脚本
- 各种配置说明文件

### 2. docs 目录迁移

#### 迁移到 docs/user/
- GETTING_STARTED.md
- DEPLOY_WITH_DOCKER.md
- README.md（docs 目录下的）

#### 迁移到 docs/admin/
- CONFIG_OVERVIEW.md
- SITE_INTEL_OVERVIEW.md
- SUBS_RULES_OVERVIEW.md
- READING_STACK_OVERVIEW.md
- BACKUP_AND_RESTORE.md
- RUNNERS_OVERVIEW.md
- BOT_TELEGRAM_GUIDE.md
- KNOWN_LIMITATIONS.md

#### 迁移到 docs/dev/
- 各种 Phase 任务书
- 实现笔记
- 实验记录
- 阶段分析报告
- 修复总结
- 前端和后端的开发指南
- API 文档

#### 保留在 docs/ 根目录
- VABHUB_SYSTEM_OVERVIEW.md
- FUTURE_AI_OVERVIEW.md
- FRONTEND_MAP.md
- README_FOR_DOCS_AUTHORS.md
- INDEX.md（新增）

## P3: README 瘦身计划

### 核心结构建议
1. 项目简介（1–2 段）
2. 功能概览（精简模块列表）
3. 快速开始（Docker-only 部署）
4. 截图 / Demo 链接（后续补充）
5. 文档入口（2–3 个核心文档）
6. License 信息

## P4: LICENSE 补齐计划

- 添加 MIT License 文件到根目录
- 更新 README.md 中的 License 链接
- 检查并更新 package.json 中的 license 字段

## P5: 校验计划

- 本地/CI 构建检查
- Docker 构建检查
- 文档链接检查

## P6: GitHub 视角验收计划

- 检查仓库主页整洁度
- 检查 README 清晰度
- 检查 docs 入口合理性
- 确认 License 可见性

## PZ: SSoT 更新计划

- 更新 VABHUB_SYSTEM_OVERVIEW.md 中的文档分层策略
- 更新 README_FOR_DOCS_AUTHORS.md 中的文档目录结构
- 更新 GETTING_STARTED.md 中的文档链接
- 更新 PRE_RELEASE_CHECK_NOTES.md 中的检查项