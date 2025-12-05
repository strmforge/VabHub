# CI-DOCKER-ONE-IMAGE-1 Baseline Report

**Date**: 2025-12-05  
**Status**: In Progress

## P0: 现有 CI & Docker 基线巡检

### Workflow 文件清单

| 文件名 | 显示名称 | 触发条件 | 功能 |
|--------|----------|----------|------|
| `ci.yml` | VabHub CI | push (所有分支), pull_request | 后端 dev_check + 前端 dev_check |
| `docker-build-and-push.yml` | Docker Build & Push | push main/tags, workflow_dispatch | 后端/前端 CI + Docker 构建推送 |
| `test-all.yml` | Backend Regression | push main/master, pull_request | 启动后端服务 + 运行回归测试 |
| `release.yml` | Release | push tags v* | 构建验证 + Docker 构建 + 创建 Release |

### 当前 Docker 镜像

| 镜像 | 用途 |
|------|------|
| `ghcr.io/strmforge/vabhub-backend:latest` | 后端 FastAPI 服务 |
| `ghcr.io/strmforge/vabhub-frontend:latest` | 前端 Nginx + 静态文件 |

### 问题分析

1. **重复 CI**: `ci.yml` 和 `docker-build-and-push.yml` 都有后端/前端 CI 检查
2. **重复触发**: push main 会同时触发多个 workflow
3. **双镜像部署复杂**: 需要两个服务（backend + frontend）协调

---

## P1: CI 精简方案

### 目标架构

| Workflow | 新状态 | 说明 |
|----------|--------|------|
| `ci.yml` | ✅ 主 CI，扩展 | 合并 Docker 构建，成为唯一主流水线 |
| `docker-build-and-push.yml` | ❌ 废弃 | 逻辑合并进 ci.yml |
| `test-all.yml` | ➜ 仅 schedule/手动 | 改为夜间回归或手动触发 |
| `release.yml` | ✅ 保留 | 仅在 tag 时触发，创建 GitHub Release |

### 新主 CI 结构

```
VabHub CI (ci.yml)
├── backend-ci     → dev_check_backend.sh
├── frontend-ci    → pnpm dev_check
└── docker-build   → needs: [backend-ci, frontend-ci]
                   → 仅 push main/tags 时执行
                   → 构建单一 All-in-One 镜像
```

---

## P3: 单镜像打包设计

### All-in-One 镜像架构

```
ghcr.io/strmforge/vabhub:latest
├── /app/backend/          ← FastAPI 应用 + Python 依赖
├── /app/frontend_dist/    ← Vue 构建产物 (静态文件)
└── 入口: uvicorn + FastAPI 同时提供:
    ├── /api/*             ← API 路由
    └── /*                 ← 静态文件 (前端 SPA)
```

### Tag 规则

| Tag | 触发条件 |
|-----|----------|
| `ghcr.io/strmforge/vabhub:latest` | push main |
| `ghcr.io/strmforge/vabhub:${{ github.sha }}` | 每次构建 |
| `ghcr.io/strmforge/vabhub:${{ github.ref_name }}` | push tag (如 v0.1.0) |

### 端口映射

- 容器内: `8000` (uvicorn)
- 宿主机: 用户自定义 (如 `8080:8000`)

---

## P5: docker-compose 新结构

### 旧结构 (双服务)

```yaml
services:
  backend:
    image: ghcr.io/strmforge/vabhub-backend:latest
  frontend:
    image: ghcr.io/strmforge/vabhub-frontend:latest
```

### 新结构 (单服务)

```yaml
services:
  vabhub:
    image: ghcr.io/strmforge/vabhub:latest
    ports:
      - "8080:8000"
  db:
    image: postgres:14-alpine
  redis:
    image: redis:7-alpine
```

---

## 实施进度

| 阶段 | 状态 |
|------|------|
| P0: 基线巡检 | ✅ 完成 |
| P1: 精简方案 | ✅ 完成 |
| P2: CI 合并 | ✅ 完成 |
| P3: 单镜像设计 | ✅ 完成 |
| P4: All-in-One Dockerfile | ✅ 完成 |
| P5: docker-compose 更新 | ✅ 完成 |
| P6: CI Docker 构建更新 | ✅ 完成 |
| P7: 冒烟测试 | ✅ 完成 |
| PZ: 文档更新 | ✅ 完成 |

---

## 最终架构

### CI Workflow

```
VabHub CI (ci.yml) - 唯一主流水线
├── backend-ci     → ./scripts/dev_check_backend.sh
├── frontend-ci    → pnpm run dev_check
└── docker-build   → needs: [backend-ci, frontend-ci]
                   → 仅 push main/tags 时执行
                   → 构建 ghcr.io/strmforge/vabhub:latest
```

### Docker 镜像

**新镜像 (All-in-One)**:
- `ghcr.io/strmforge/vabhub:latest`
- `ghcr.io/strmforge/vabhub:${{ github.sha }}`
- `ghcr.io/strmforge/vabhub:${{ github.ref_name }}`

**废弃镜像**:
- `ghcr.io/strmforge/vabhub-backend` (不再构建)
- `ghcr.io/strmforge/vabhub-frontend` (不再构建)

### docker-compose

```yaml
services:
  vabhub:    # All-in-One 应用
    image: ghcr.io/strmforge/vabhub:latest
    ports: ["8080:8000"]
  db:        # PostgreSQL
  redis:     # Redis
```

### 部署命令

```bash
# 升级
docker compose pull && docker compose up -d

# 首次部署
docker compose up -d
```
