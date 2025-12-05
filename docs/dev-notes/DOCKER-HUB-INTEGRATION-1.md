# DOCKER-HUB-INTEGRATION-1：CI 支持 Docker Hub 推送

## 任务完成状态：✅ 完成

## P0 现状巡检

### 当前 Workflow 文件

- **主 CI**: `.github/workflows/ci.yml`（活跃）
- **已废弃**: `.github/workflows/docker-build-and-push.yml`（DEPRECATED）

### 现有镜像 Tag 配置（修改前）

仅推送 GHCR：
- `ghcr.io/strmforge/vabhub:latest`（main 分支）
- `ghcr.io/strmforge/vabhub:<sha>`
- `ghcr.io/strmforge/vabhub:<version>`（版本 tag）

### dev_check 状态

- **前端**: `pnpm run dev_check` ✅ 通过

### 对标文案搜索

初始搜索发现 `README.md` 和 `VABHUB_SYSTEM_OVERVIEW.md` 中有对标其他平台的引用，已在 P6 中清理。

---

## P1-P3 实施记录

### 修改文件

- `.github/workflows/ci.yml`
  - 新增环境变量 `DOCKERHUB_IMAGE: strmforge/vabhub`
  - 新增 Docker Hub 登录步骤
  - 扩展 tags 同时推送 GHCR + Docker Hub

### Docker Hub 凭据

需在 GitHub Secrets 中配置：
- `DOCKERHUB_USERNAME`: Docker Hub 用户名
- `DOCKERHUB_TOKEN`: Docker Hub Personal Access Token

详见 `docs/ci/DOCKER_BUILD_PIPELINE.md`

---

## P4 验证记录

- GitHub Actions Run: 待推送后验证
- 本地拉取验证（推送后执行）:
  ```bash
  docker pull strmforge/vabhub:latest
  ```

---

## P6 文档清理记录

| 文件 | 处理方式 |
|------|----------|
| `README.md` | 改为 "核心理念：Local-first、自托管..." |
| `VABHUB_SYSTEM_OVERVIEW.md` | 改为 VabHub 自身定位描述 |

---

## 修改文件清单

1. `.github/workflows/ci.yml` - 添加 Docker Hub 支持
2. `docs/user/DEPLOY_WITH_DOCKER.md` - 添加 Docker Hub 拉取说明
3. `docs/VABHUB_SYSTEM_OVERVIEW.md` - 补充镜像托管说明 + 文案清理
4. `docs/ci/DOCKER_BUILD_PIPELINE.md` - 新建 CI 凭据配置文档
5. `CHANGELOG.md` - 添加变更记录
6. `README.md` - 更新镜像来源说明 + 文案清理

---

## 自检结果

```bash
# 前端
pnpm run dev_check  # ✅ 通过
```

---

**任务日期**: 2025-12-06  
**Lint 说明**: CI workflow 中的 `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` 警告是 IDE 无法验证 GitHub Secrets 导致的，不影响实际运行
