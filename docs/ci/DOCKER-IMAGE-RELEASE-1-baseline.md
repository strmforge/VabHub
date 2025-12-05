# DOCKER-IMAGE-RELEASE-1 Baseline

**任务**: 0.0.1-rc1 官方 Docker 镜像发布  
**日期**: 2025-12-06

---

## 1. 当前状态

### 1.1 架构概述

VabHub 采用 **All-in-One 单镜像架构**（CI-DOCKER-ONE-IMAGE-1 实现）：
- 前后端合一，单个容器提供完整服务
- 镜像：`ghcr.io/strmforge/vabhub`
- 默认端口：52180

### 1.2 文件现状

| 文件 | 架构 | 说明 |
|------|------|------|
| `docker-compose.yml` | All-in-One | ✅ 正确，用于开发/本地构建 |
| `docker-compose.prod.yml` | 双镜像 (旧) | ⚠️ 需更新为 All-in-One |
| `.github/workflows/ci.yml` | All-in-One | ✅ 已配置构建推送 |
| `Dockerfile` (根目录) | All-in-One | ✅ 多阶段构建 |

### 1.3 CI 触发条件

当前 `ci.yml` 的 Docker 构建触发：
- `push` 到 `main` 分支 → 推送 `latest` + `sha` 标签
- `push` tag `v*` → 推送版本标签

---

## 2. 镜像命名 & Tag 策略

### 2.1 Registry

- **Registry**: GHCR (ghcr.io)
- **Namespace**: `strmforge` (github.repository_owner)

### 2.2 镜像名

| 镜像 | 用途 |
|------|------|
| `ghcr.io/strmforge/vabhub` | All-in-One 主镜像 |

### 2.3 Tag 策略

| 触发 | Tag | 示例 |
|------|-----|------|
| push main | `latest`, `<sha>` | `latest`, `11d4d56` |
| push v* tag | `<version>`, `<sha>` | `v0.0.1-rc1`, `11d4d56` |

---

## 3. 待办事项

1. **更新 docker-compose.prod.yml**：改为 All-in-One 架构，移除 build 块
2. **更新 .env.docker.example**：添加 `VABHUB_VERSION` 变量
3. **更新文档**：DEPLOY_WITH_DOCKER.md, README.md
4. **创建报告**：DOCKER-IMAGE-RELEASE-1-report.md

---

## 4. 参考文档

- `docs/ci/DOCKER-SMOKE-RUN-1-report.md`
- `docs/ci/RELEASE-RC1-1-report.md`
- `docs/ci/CI-DOCKER-CONTEXT-FIX-1-report.md`
