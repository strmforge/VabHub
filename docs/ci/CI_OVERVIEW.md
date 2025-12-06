# VabHub CI 总览

> **一句话概括**：确保 VabHub 后端 `scripts/dev_check_backend.sh` 和前端 `pnpm dev_check` 在 CI 中被持续验证，Docker 镜像只在打版本 tag 时发布。

本文档面向新开发者和外部贡献者，帮助你在 5–10 分钟内理解 VabHub 的 CI / 测试 / 发版全链路。

---

## 1. Workflow 概览表

| Workflow | 文件 | 触发条件 | 主要功能 | Docker 行为 |
|----------|------|---------|----------|------------|
| **VabHub CI** | `ci.yml` | push 任意分支 / PR | 后端 dev_check + 前端 dev_check | build only（不推送） |
| **Docker Release** | `docker-release.yml` | push `v*` tag | 版本驱动的镜像发布 | build + push |
| **Backend Regression** | `test-all.yml` | 定时/手动触发 | 运行 `test_all.py` 回归测试 | 无 |
| **Release** | `release.yml` | push `v*` tag | 构建验证 + 创建 GitHub Release | build only |
| **[DEPRECATED]** | `docker-build-and-push.yml` | 手动触发 | 历史遗留，已禁用推送 | build only |

---

## 2. 检查内容矩阵

| 检查项 | ci.yml | test-all.yml | docker-release.yml | release.yml |
|--------|--------|--------------|-------------------|-------------|
| `scripts/dev_check_backend.sh` | ✅ | ❌ | ❌ | ❌ |
| 前端 `pnpm dev_check` | ✅ | ❌ | ❌ | ❌ |
| `backend/scripts/test_all.py` | ❌ | ✅ | ❌ | ❌ |
| Docker 构建验证 | ✅ | ❌ | ✅ | ✅ |
| Docker 推送镜像 | ❌ | ❌ | ✅ | ❌ |
| 创建 GitHub Release | ❌ | ❌ | ❌ | ✅ |

---

## 3. 本地开发者如何重现 CI 检查

### 3.1 后端检查（官方入口）

```bash
# 在项目根目录执行
bash scripts/dev_check_backend.sh
```

**执行内容**：
1. `ruff check` - 代码风格检查
2. `mypy` - 类型检查
3. `pytest -m "not integration and not slow"` - 单元测试（排除集成和慢测试）

### 3.2 前端检查（官方入口）

```bash
cd frontend
pnpm dev_check
```

**执行内容**：
- `vue-tsc --noEmit` - TypeScript 类型检查

> 💡 也可以分步执行：`pnpm lint` + `pnpm typecheck` + `pnpm build`

### 3.3 回归测试（最小冒烟测试）

```bash
# 确保后端已启动
cd backend
python scripts/test_all.py --skip-music-execute
```

**执行内容**（按顺序）：
1. `quick_test.py` - 快速健康检查
2. `test_functional.py` - 功能测试
3. `test_music_minimal.py` - 音乐模块最小测试
4. `test_graphql_minimal.py` - GraphQL 接口测试
5. `test_decision_minimal.py` - 决策层测试
6. `tests/test_plugins_api.py` - 插件 API 测试
7. `test_rsshub_minimal.py` - RSSHub 最小测试

---

## 4. CI 环境与本地环境的差异

### 4.1 CI 特有环境变量

| 变量 | CI 中的值 | 说明 |
|------|----------|------|
| `VABHUB_CI` | `1` | 标识 CI 环境，影响测试行为（如跳过 RSSHub 检查） |
| `API_BASE_URL` | `http://127.0.0.1:8100` | 回归测试中的 API 基础地址 |
| `API_PREFIX` | `/api` | API 前缀（与后端配置一致） |
| `REDIS_ENABLED` | `false` | CI 中禁用 Redis |

> 详细说明见 [ENV_AND_FLAGS.md](./ENV_AND_FLAGS.md)

### 4.2 CI 中的数据库

- CI 使用 SQLite 内存数据库
- 数据库路径：`.ci_data/vabhub_regression.db`

---

## 5. Docker 镜像发布规则

### 5.1 发布时机

**只有打 `v*` tag 时才会发布镜像**，例如：

```bash
git tag v0.1.0-rc2
git push origin v0.1.0-rc2
```

### 5.2 发布目标

| 仓库 | 镜像地址 |
|------|---------|
| GHCR | `ghcr.io/strmforge/vabhub:<version>` |
| Docker Hub | `strmforge/vabhub:<version>` |

每次发布会同时推送 4 个 tag：
- `ghcr.io/strmforge/vabhub:0.1.0-rc2`
- `ghcr.io/strmforge/vabhub:latest`
- `strmforge/vabhub:0.1.0-rc2`
- `strmforge/vabhub:latest`

### 5.3 版本一致性检查

CI 会自动检查 git tag 与代码中的版本号（`backend/app/core/version.py`）是否一致。
如果不一致，发布会失败。

> 详细说明见 [DOCKER-RELEASE-1.md](./DOCKER-RELEASE-1.md)

---

## 6. 资产清单

### 6.1 Workflow 文件

| 文件 | 状态 | 说明 |
|------|------|------|
| `.github/workflows/ci.yml` | ✅ 活跃 | 主 CI 流水线 |
| `.github/workflows/docker-release.yml` | ✅ 活跃 | 版本发布流水线 |
| `.github/workflows/test-all.yml` | ✅ 活跃 | 回归测试（定时/手动） |
| `.github/workflows/release.yml` | ✅ 活跃 | GitHub Release 创建 |
| `.github/workflows/docker-build-and-push.yml` | ⚠️ 废弃 | 仅保留供参考 |

### 6.2 关键脚本

| 脚本 | 用途 |
|------|------|
| `scripts/dev_check_backend.sh` | 后端质量门（Ruff + mypy + pytest） |
| `scripts/dev_check_frontend.sh` | 前端质量门（lint + typecheck + build） |
| `backend/scripts/test_all.py` | 一键回归测试 |
| `backend/scripts/print_version.py` | 版本号读取（供 CI 调用） |

### 6.3 测试脚本（test_all.py 调用）

| 脚本 | 说明 |
|------|------|
| `quick_test.py` | 快速健康检查 |
| `test_functional.py` | 功能测试 |
| `test_music_minimal.py` | 音乐模块最小测试 |
| `test_graphql_minimal.py` | GraphQL 接口测试 |
| `test_decision_minimal.py` | 决策层测试 |
| `test_rsshub_minimal.py` | RSSHub 最小测试 |

---

## 7. 历史报告与深入阅读

- [BACKEND-CI-1-initial-report.md](./BACKEND-CI-1-initial-report.md) - 后端首轮 CI 报告
- [RSSHUB-MINIMAL-1.md](./RSSHUB-MINIMAL-1.md) - RSSHub 最小检查行为说明
- [DOCKER-RELEASE-1.md](./DOCKER-RELEASE-1.md) - Docker 发版流水线设计

---

## 8. 常见问题

### Q: 本地测试通过但 CI 失败？

检查以下差异：
1. **环境变量**：CI 中 `VABHUB_CI=1`，可能影响测试行为
2. **API 前缀**：确认 `API_PREFIX=/api` 配置一致
3. **数据库**：CI 使用 SQLite，本地可能是 PostgreSQL

### Q: 如何跳过某些测试？

```bash
# 跳过音乐下载执行
python backend/scripts/test_all.py --skip-music-execute

# 跳过慢测试
pytest -m "not slow"
```

### Q: 如何触发 Docker 镜像发布？

```bash
# 1. 修改版本号
python tools/bump_version.py --set 0.1.0-rc2

# 2. 提交并打 tag
git add .
git commit -m "chore: bump version to 0.1.0-rc2"
git push origin main
git tag v0.1.0-rc2
git push origin v0.1.0-rc2
```

---

## 9. CI-OVERVIEW-1 任务总结

本文档由 **CI-OVERVIEW-1** 任务创建，主要完成：

1. 梳理现有 CI / 测试 / 发版链路
2. 编写面向新开发者的 CI 总览文档
3. 将 CI 信息挂钩到系统总览文档

### 对后续开发的建议

1. **新增 Workflow 时**：
   - 在本文档中添加对应条目
   - 遵循"只有发布 workflow 才能 `push: true`"的规范

2. **新增测试脚本时**：
   - 正确使用 `VABHUB_CI` 环境变量
   - 参考 [ENV_AND_FLAGS.md](./ENV_AND_FLAGS.md) 的规范

3. **修改 API 前缀时**：
   - 同步更新 `backend/app/core/config.py`
   - 同步更新 `backend/scripts/api_test_config.py`
   - 同步更新 CI workflow 中的 `API_PREFIX` 环境变量
