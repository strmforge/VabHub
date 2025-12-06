# VabHub CI 文档索引

本目录包含 VabHub 持续集成（CI）相关的所有文档。

---

## 📖 阅读顺序建议

1. **先看总览** → [CI_OVERVIEW.md](./CI_OVERVIEW.md)
2. **需要了解环境变量** → [ENV_AND_FLAGS.md](./ENV_AND_FLAGS.md)
3. **需要特定细节** → 查看对应子文档

---

## 📋 文档清单

### 核心文档

| 文档 | 说明 |
|------|------|
| [CI_OVERVIEW.md](./CI_OVERVIEW.md) | **CI 总览**（新人必读） |
| [ENV_AND_FLAGS.md](./ENV_AND_FLAGS.md) | CI 环境变量与 Flag 规范 |
| [DOCKER-RELEASE-1.md](./DOCKER-RELEASE-1.md) | Docker 发版流水线设计 |

### 测试相关

| 文档 | 说明 |
|------|------|
| [RSSHUB-MINIMAL-1.md](./RSSHUB-MINIMAL-1.md) | RSSHub 最小检查行为说明 |
| [BACKEND-REGRESSION-DECISION-1.md](./BACKEND-REGRESSION-DECISION-1.md) | Decision 层回归测试 |
| [BACKEND-REGRESSION-MUSIC-1.md](./BACKEND-REGRESSION-MUSIC-1.md) | 音乐模块回归测试 |

### 历史报告

| 文档 | 说明 |
|------|------|
| [BACKEND-CI-1-initial-report.md](./BACKEND-CI-1-initial-report.md) | 后端首轮 CI 报告 |
| [BACKEND-CI-2-full-green-report.md](./BACKEND-CI-2-full-green-report.md) | 后端 CI 第二轮全绿报告 |
| [BACKEND-CI-3-full-green-report.md](./BACKEND-CI-3-full-green-report.md) | 后端 CI 第三轮全绿报告 |
| [CI-FINAL-1-report.md](./CI-FINAL-1-report.md) | CI 最终报告 |

### Docker 相关

| 文档 | 说明 |
|------|------|
| [DOCKER-RELEASE-1.md](./DOCKER-RELEASE-1.md) | 版本号驱动的 Docker 发布 |
| [DOCKER-SMOKE-RUN-1-report.md](./DOCKER-SMOKE-RUN-1-report.md) | Docker 冒烟测试报告 |
| [CI-DOCKER-ONE-IMAGE-1-baseline.md](./CI-DOCKER-ONE-IMAGE-1-baseline.md) | All-in-One 镜像方案 |

---

## 🔗 快速链接

- **Workflow 文件**：`.github/workflows/`
- **后端质量门**：`scripts/dev_check_backend.sh`
- **前端质量门**：`frontend/` 下 `pnpm dev_check`
- **回归测试**：`backend/scripts/test_all.py`

---

## 📌 常用命令

```bash
# 后端检查
bash scripts/dev_check_backend.sh

# 前端检查
cd frontend && pnpm dev_check

# 回归测试
cd backend && python scripts/test_all.py --skip-music-execute

# 查看版本号
python backend/scripts/print_version.py
```

---

## 🆕 新增文档指南

如果你需要添加新的 CI 相关文档：

1. 在本目录创建 `.md` 文件
2. 在本 README 的"文档清单"中添加条目
3. 如果是新的 Workflow 或重要变更，同步更新 [CI_OVERVIEW.md](./CI_OVERVIEW.md)
