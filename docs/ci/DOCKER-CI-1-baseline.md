# DOCKER-CI-1 Baseline Report

**Date**: 2025-12-05  
**Status**: Implemented

## P0: 现有 Docker 架构巡检

### Docker 相关文件位置

| 文件 | 路径 | 用途 |
|------|------|------|
| docker-compose.yml | 根目录 | 编排所有服务 |
| backend Dockerfile | `backend/Dockerfile` | 后端多阶段构建 |
| frontend Dockerfile | `frontend/Dockerfile` | 前端多阶段构建 (node → nginx) |
| intel_center Dockerfile | `services/intel_center/Dockerfile` | 可选微服务 |
| mesh_scheduler Dockerfile | `services/mesh_scheduler/Dockerfile` | 可选微服务 |

### 服务架构

```
┌─────────────────────────────────────────────────────────────┐
│                    docker-compose.yml                        │
├─────────────┬─────────────┬─────────────┬──────────────────┤
│     db      │    redis    │   backend   │     frontend     │
│ postgres:14 │  redis:7    │  本地构建    │     本地构建      │
│   :5432     │   :6379     │    :8092    │       :80        │
└─────────────┴─────────────┴─────────────┴──────────────────┘
```

### 当前构建配置

**后端服务** (`backend`):
```yaml
build:
  context: ./backend
  dockerfile: Dockerfile
```

**前端服务** (`frontend`):
```yaml
build:
  context: ./frontend
  dockerfile: Dockerfile
  args:
    - VITE_API_BASE_URL=${VITE_API_BASE_URL:-http://localhost:8092/api}
```

### 现有镜像命名 (目标)

基于仓库所有者 `strmforge`，镜像命名规则：

| 服务 | GHCR 镜像地址 |
|------|---------------|
| backend | `ghcr.io/strmforge/vabhub-backend` |
| frontend | `ghcr.io/strmforge/vabhub-frontend` |

---

## P1: 镜像命名 & Tag 策略设计

### Registry 选择

使用 **GitHub Container Registry (GHCR)**:
- 与 GitHub 仓库紧密集成
- 使用 `GITHUB_TOKEN` 无需额外配置
- 支持公开/私有镜像

### Tag 规则

| Tag 类型 | 触发条件 | 示例 |
|----------|----------|------|
| `latest` | push 到 main 分支 | `ghcr.io/strmforge/vabhub-backend:latest` |
| `${{ github.sha }}` | 每次构建 | `ghcr.io/strmforge/vabhub-backend:abc1234` |
| `${{ github.ref_name }}` | push 版本 tag | `ghcr.io/strmforge/vabhub-backend:v0.1.0-rc1` |

### 触发条件

```yaml
on:
  push:
    branches:
      - main
    tags:
      - 'v*'
  workflow_dispatch:  # 支持手动触发
```

---

## P2-P3: Docker CI Workflow 结构

### 工作流设计

```
┌─────────────┐     ┌─────────────┐
│ backend-ci  │     │ frontend-ci │
│ dev_check   │     │  dev_check  │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └───────┬───────────┘
               │
               ▼
       ┌───────────────┐
       │ docker-build  │
       │ (needs: both) │
       │  build+push   │
       └───────────────┘
```

### CI 检查内容

**后端 CI**:
- `./scripts/dev_check_backend.sh` (默认模式)
- Ruff lint + mypy + pytest (不含 integration/slow)

**前端 CI**:
- `pnpm run dev_check`
- vue-tsc 类型检查 + eslint 代码检查

---

## P4: docker-compose 对齐策略

### 生产部署方式

```yaml
services:
  backend:
    image: ghcr.io/strmforge/vabhub-backend:latest
    # build: 注释掉或保留用于本地开发
  frontend:
    image: ghcr.io/strmforge/vabhub-frontend:latest
```

### 升级命令

```bash
# 拉取最新镜像
docker compose pull

# 重启服务
docker compose up -d
```

---

## P6: 与 BACKEND-CI-* 的协同

### 依赖关系

```
docker-build job
    └── needs: [backend-ci, frontend-ci]
            │
            ├── backend-ci: ./scripts/dev_check_backend.sh
            │   └── Ruff ✅ → mypy ✅ → pytest (default mode) ✅
            │
            └── frontend-ci: pnpm run dev_check
                └── vue-tsc ✅ → eslint ✅
```

### 约定

1. **CI 必须全绿才能构建镜像** - docker-build job 依赖 CI job 成功
2. **使用默认模式而非 full 模式** - 避免 integration 测试影响构建频率
3. **禁止为了过 CI 删测试或放宽规则**

---

## 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `.github/workflows/docker-build-and-push.yml` | 新增 | Docker CI 工作流 |
| `docker-compose.yml` | 修改 | 添加 image 字段 |
| `frontend/package.json` | 修改 | 添加 dev_check 脚本 |
| `docs/ci/DOCKER-CI-1-baseline.md` | 新增 | 本文档 |
| `docs/user/DEPLOY_WITH_DOCKER.md` | 修改 | 添加 CI 自动构建章节 |
