# Docker 镜像版本策略（VabHub）

> 版本 0.0.3 - DISCOVER-MUSIC-HOME

## 目标

- 避免"每次提交都发布镜像"导致 DockerHub/GHCR 版本爆炸
- 允许用户始终使用 `:latest`，并在需要时通过拉取更新获得新版本
- 发布行为必须与 VabHub 版本号严格绑定

---

## 规则

### 1. 只有当版本号文件发生变更时，CI 才允许 push 镜像

版本号文件位置：`backend/app/core/version.py`

```python
APP_VERSION = "0.0.3"  # 变更此值触发镜像发布
```

### 2. Push 时同时发布 4 个 tag

```
ghcr.io/strmforge/vabhub:${VERSION}
ghcr.io/strmforge/vabhub:latest
strmforge/vabhub:${VERSION}
strmforge/vabhub:latest
```

### 3. 未变更版本号的提交

- 只允许 build（验证 Dockerfile 可用）
- **不允许 push**

---

## 用户如何更新

### 推荐方式

```bash
docker compose pull
docker compose up -d
```

### 使用 Portainer

1. 进入 Containers 页面
2. 选择 vabhub 容器
3. 点击 "Recreate" 并勾选 "Pull latest image"

### 使用 Watchtower（自动更新）

```yaml
services:
  watchtower:
    image: containrrr/watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - WATCHTOWER_CLEANUP=true
      - WATCHTOWER_POLL_INTERVAL=86400  # 每天检查一次
    restart: unless-stopped
```

> ⚠️ 只有在"版本变更才 push"的策略下，Watchtower 才有意义。

---

## 开发者如何发布新版本

1. 修改版本号：`backend/app/core/version.py`

```python
APP_VERSION = "0.0.3"  # → "0.0.4"
```

2. 同步更新前端版本：`frontend/src/layouts/components/AppDrawer.vue`

```typescript
const appVersion = '0.0.4'
```

3. 更新 CHANGELOG.md

4. 提交并 push main

5. CI 检测到版本变更后自动 push 镜像并更新 `:latest`

---

## CI Workflow 配置

### docker-build.yml（每次提交只 build 不 push）

```yaml
name: docker-build

on:
  push:
    branches: [ "main" ]
  pull_request:

jobs:
  build_only:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build image (no push)
        uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: strmforge/vabhub:ci
```

### docker-release.yml（版本变更时 push）

```yaml
name: docker-release

on:
  push:
    branches: [ "main" ]
  workflow_dispatch:

jobs:
  release_if_version_changed:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2

      - name: Detect version bump
        id: ver
        run: |
          git diff --name-only HEAD~1..HEAD > changed.txt
          if grep -q "backend/app/core/version.py" changed.txt; then
            echo "bumped=1" >> $GITHUB_OUTPUT
          else
            echo "bumped=0" >> $GITHUB_OUTPUT
          fi

      - name: Stop if no version bump
        if: steps.ver.outputs.bumped != '1'
        run: |
          echo "No version bump detected. Skip docker push."
          exit 0

      - name: Read VERSION
        id: v
        run: |
          VERSION=$(grep -oP 'APP_VERSION\s*=\s*"\K[^"]+' backend/app/core/version.py)
          echo "version=$VERSION" >> $GITHUB_OUTPUT

      - name: Login GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Login DockerHub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ghcr.io/strmforge/vabhub:${{ steps.v.outputs.version }}
            ghcr.io/strmforge/vabhub:latest
            strmforge/vabhub:${{ steps.v.outputs.version }}
            strmforge/vabhub:latest
```

---

## 注意

- 0.0.x 阶段版本号由项目负责人指挥变更
- 不允许 IDE 为了"看起来有进度"频繁 bump 版本号
- 正式版保留给 0.1.0 及以后

---

*最后更新：2025-12-13 VabHub 0.0.3*
