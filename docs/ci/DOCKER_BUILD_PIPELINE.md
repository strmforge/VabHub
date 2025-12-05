# VabHub Docker 构建 Pipeline 说明

## 概述

VabHub 使用 GitHub Actions 自动构建并推送 Docker 镜像到两个 Registry：
- **GHCR** (GitHub Container Registry): `ghcr.io/strmforge/vabhub`
- **Docker Hub**: `strmforge/vabhub`

## Workflow 文件

主 CI workflow: `.github/workflows/ci.yml`

### 触发条件

- `push` 到任意分支
- `push` 版本 tag (`v*`)
- `pull_request`
- 手动触发 (`workflow_dispatch`)

### Docker 构建条件

仅在以下情况下执行 Docker 构建与推送：
- push 到 `main` 分支
- push 版本 tag（如 `v0.0.1-rc1`）
- 且后端 CI 和前端 CI 均通过

## Docker Registry 凭据配置

### GHCR (GitHub Container Registry)

- **凭据**: 使用内置的 `GITHUB_TOKEN`
- **无需额外配置**

### Docker Hub

需要在 GitHub 仓库的 Settings → Secrets and variables → Actions 中配置：

| Secret 名称 | 说明 |
|-------------|------|
| `DOCKERHUB_USERNAME` | Docker Hub 用户名（如 `strmforge`） |
| `DOCKERHUB_TOKEN` | Docker Hub Personal Access Token |

#### 获取 Docker Hub Token

1. 登录 [Docker Hub](https://hub.docker.com/)
2. 进入 Account Settings → Security → Access Tokens
3. 点击 "New Access Token"
4. 选择权限为 "Read, Write, Delete"
5. 复制生成的 Token

## 镜像 Tag 策略

| 触发条件 | GHCR Tag | Docker Hub Tag |
|----------|----------|----------------|
| push main | `ghcr.io/strmforge/vabhub:latest`<br>`ghcr.io/strmforge/vabhub:<sha>` | `strmforge/vabhub:latest`<br>`strmforge/vabhub:<sha>` |
| push v* tag | `ghcr.io/strmforge/vabhub:<version>`<br>`ghcr.io/strmforge/vabhub:<sha>` | `strmforge/vabhub:<version>`<br>`strmforge/vabhub:<sha>` |

## 拉取镜像

```bash
# 从 Docker Hub（推荐，国内访问更快）
docker pull strmforge/vabhub:latest

# 从 GHCR
docker pull ghcr.io/strmforge/vabhub:latest

# 指定版本
docker pull strmforge/vabhub:v0.0.1-rc1
```

## 故障排查

### Docker Hub 登录失败

检查 GitHub Secrets 是否正确配置：
- `DOCKERHUB_USERNAME` 是否为有效用户名
- `DOCKERHUB_TOKEN` 是否过期或权限不足

### 镜像推送失败

- 确认 Docker Hub 仓库 `strmforge/vabhub` 存在
- 确认 Token 有 write 权限

---

**更新日期**: 2025-12-06  
**相关任务**: DOCKER-HUB-INTEGRATION-1
