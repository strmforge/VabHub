# Changelog

All notable changes to VabHub will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.0.1-rc1] - 2025-12-05

首次 RC 封版，基于版本号 `0.0.1`。

### Added

- **Docker 部署路线打通**
  - All-in-One 单镜像架构 (`ghcr.io/strmforge/vabhub:latest`)
  - `docker compose build && docker compose up -d` 一键部署
  - 默认端口 52180（避开常见下载器端口）
  - 详见 `docs/ci/DOCKER-SMOKE-RUN-1-report.md`

- **前端 Docker 构建链路**
  - `pnpm run build` 可通过
  - Docker 前端镜像可构建
  - 详见 `docs/ci/FRONTEND-DOCKER-BUILD-FIX-1.md`

- **CI 规范确定**
  - 后端：`scripts/dev_check_backend.sh`（ruff + mypy + pytest）
  - 前端：`pnpm dev_check`（vue-tsc + eslint）

- **核心功能模块**
  - 影视中心：电视墙、115 播放、本地 + 云盘统一管理
  - 阅读 & 听书：TXT → EBook → TTS → 有声书，统一进度
  - 漫画中心：第三方源接入 + 追更通知
  - 音乐订阅：PT / RSSHub 榜单自动订阅
  - Local Intel：本地智能大脑（HR/HNR 决策、站点保护）
  - AI 中心：5 个 AI 助手（只读建议不自动执行）
  - 插件生态：Plugin Hub + 插件中心

### Known Issues

- 前端 70 个 TypeScript 警告（Vuetify v-data-table slot 类型问题），为上游已知问题
- 部署文档以本地验证环境为准，异构 NAS 环境可能需要调整

### References

- 部署指南：`docs/user/DEPLOY_WITH_DOCKER.md`
- 系统总览：`docs/VABHUB_SYSTEM_OVERVIEW.md`
- CI 报告：`docs/ci/RELEASE-RC1-1-baseline.md`

---

## [Unreleased]

### Added

- **[ci] CI 支持同时推送 Docker Hub 镜像**
  - 新增 `strmforge/vabhub` 镜像（Docker Hub）
  - 保持 `ghcr.io/strmforge/vabhub` 镜像（GHCR）
  - 两个 Registry 的 tag 保持同步（latest / sha / version）
  - 详见 `docs/dev-notes/DOCKER-HUB-INTEGRATION-1.md`

### Fixed

- **[frontend] 修复 Docker 构建时缺失 downloads 组件导致的前端打包失败**
  - 根因：`.gitignore` 中 `downloads/` 规则过于宽泛，意外忽略了 `frontend/src/components/downloads/` 目录
  - 修复：将规则改为 `/downloads/` 只匹配根目录
  - 受影响组件：SpeedLimitDialog.vue, DownloadList.vue, DownloadProgressCard.vue
  - 详见 `docs/dev-notes/FRONTEND-DOWNLOADS-SPEEDLIMIT-1.md`

### Changed

- **[docs] 文档清理：使用 VabHub 自身定位**
  - README.md、VABHUB_SYSTEM_OVERVIEW.md 改为 VabHub 自身定位描述
  - 部署文档增加 Docker Hub 镜像拉取说明

### Planned

- 收紧 CI 要求（TypeScript 严格模式）
- 扩展功能模块
- 用户反馈迭代
