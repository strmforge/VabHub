# DOCKER-RELEASE-1: 版本号驱动的 Docker 镜像发布

## 背景与目标

### 问题

原有 CI 流程在每次 push main 时都会构建并推送 Docker 镜像，导致：
- GHCR 中产生大量 commit SHA 标签的镜像
- 难以区分正式发布版本和临时构建
- 频繁的镜像推送增加 CI 时间

### 目标

1. **CI 只验证，不发布**：常规 push 只做 Docker build 验证，不推送镜像
2. **版本驱动发布**：仅在打 git tag 时才构建并推送镜像
3. **版本一致性**：tag 必须与代码中的版本号匹配

## 版本号来源

### 单一版本源（Single Source of Truth）

```
backend/app/core/version.py
```

```python
APP_VERSION = "0.1.0-rc1"
```

### 版本读取脚本

```bash
python backend/scripts/print_version.py
# 输出: 0.1.0-rc1
```

### 版本管理工具

```bash
# 查看当前版本
python tools/bump_version.py --get

# 升级版本号
python tools/bump_version.py --patch   # 0.1.0 -> 0.1.1
python tools/bump_version.py --minor   # 0.1.0 -> 0.2.0
python tools/bump_version.py --major   # 0.1.0 -> 1.0.0
python tools/bump_version.py --set 0.2.0-rc1  # 直接设置
```

## 两条流水线

### 1. VabHub CI (`ci.yml`)

**触发条件**：push 任意分支 / PR

**行为**：
- 运行后端 CI 检查（dev_check_backend.sh）
- 运行前端 CI 检查（pnpm run dev_check）
- **仅构建 Docker 镜像，不推送**

```yaml
# ci.yml 中的 docker-build job
push: false  # 只验证构建，不推送
```

### 2. Docker Release (`docker-release.yml`)

**触发条件**：推送 `v*` tag

**行为**：
1. 读取代码中的版本号
2. 校验 tag 与版本号一致性
3. 构建并推送镜像到 **GHCR + Docker Hub（双仓库）**

## 镜像发布目标（双仓库策略）

发布时同时推送到两个仓库，共 4 个 tag：

### GHCR (GitHub Container Registry)

| Tag | 示例 |
|-----|------|
| 版本号 | `ghcr.io/strmforge/vabhub:0.1.0-rc1` |
| latest | `ghcr.io/strmforge/vabhub:latest` |

### Docker Hub

| Tag | 示例 |
|-----|------|
| 版本号 | `strmforge/vabhub:0.1.0-rc1` |
| latest | `strmforge/vabhub:latest` |

### 所需 GitHub Secrets

在仓库 Settings → Secrets and variables → Actions 中配置：

| Secret 名称 | 说明 |
|------------|------|
| `DOCKERHUB_USERNAME` | Docker Hub 用户名 |
| `DOCKERHUB_TOKEN` | Docker Hub Access Token（非密码） |

> 💡 `GITHUB_TOKEN` 由 GitHub Actions 自动提供，无需手动配置。

## 发布步骤

```bash
# 1. 修改版本号
python tools/bump_version.py --set 0.1.0-rc2
# 或手动编辑 backend/app/core/version.py

# 2. 提交代码
git add .
git commit -m "chore: bump version to 0.1.0-rc2"
git push origin main

# 3. 打 tag 触发发布
git tag v0.1.0-rc2
git push origin v0.1.0-rc2

# 之后 CI 自动完成：
# - 检查 tag 与 APP_VERSION 一致
# - 构建 Docker 镜像
# - 推送到 GHCR + Docker Hub（共 4 个 tag）
#   - ghcr.io/strmforge/vabhub:0.1.0-rc2
#   - ghcr.io/strmforge/vabhub:latest
#   - strmforge/vabhub:0.1.0-rc2
#   - strmforge/vabhub:latest
```

## 验收点

### 不改版本号时（任意 push / PR）

- ✅ 回归 CI 正常运行
- ✅ Docker 只 build，不 push
- ✅ GHCR / Docker Hub 不会出现新 tag

### 改版本号 + 打 tag 时

- ✅ Docker Release workflow 被触发
- ✅ GHCR 出现两个 tag：`<version>`、`latest`
- ✅ Docker Hub 同样出现两个 tag：`<version>`、`latest`

## 其他 Workflow 状态

| Workflow | `push` 设置 | 说明 |
|----------|------------|------|
| `ci.yml` | `false` | 仅 build 验证 |
| `docker-release.yml` | `true` | 发布专用 |
| `docker-build-and-push.yml` | `false` | [DEPRECATED] 已禁用推送 |
| `test-all.yml` | N/A | 无 Docker 步骤 |

## 防呆机制

### Tag 与版本号一致性检查

如果打的 tag 与代码版本号不一致，发布 workflow 会失败：

```
❌ ERROR: Tag and code version mismatch!

请确保以下两步骤已完成：
1. 修改 backend/app/core/version.py 中的 APP_VERSION
2. 提交代码后再打 tag
```

## FAQ

### Q: 版本号写错了怎么办？

删除错误的 tag，修正版本号后重新打 tag：

```bash
# 删除远程 tag
git push origin :refs/tags/v0.1.0-wrong

# 删除本地 tag
git tag -d v0.1.0-wrong

# 修正版本号后重新打 tag
python tools/bump_version.py --set 0.1.0-correct
git add .
git commit -m "fix: correct version number"
git tag v0.1.0-correct
git push origin main v0.1.0-correct
```

### Q: 想重新构建同版本镜像怎么办？

**推荐**：使用新的补丁版本号（如 `0.1.0-rc1` → `0.1.0-rc2`）

如必须重建同版本：
1. 在 GHCR 中删除旧镜像 tag
2. 删除并重新创建 git tag

### Q: 如何选择 tag 格式？

- 正式版本：`v1.0.0`
- 候选版本：`v1.0.0-rc1`
- 预览版本：`v1.0.0-alpha1`、`v1.0.0-beta1`

## 相关文件

- `.github/workflows/ci.yml` - 主 CI 流水线（仅 build）
- `.github/workflows/docker-release.yml` - 版本发布流水线
- `backend/app/core/version.py` - 版本号定义
- `backend/scripts/print_version.py` - 版本号读取脚本
- `tools/bump_version.py` - 版本号管理工具
