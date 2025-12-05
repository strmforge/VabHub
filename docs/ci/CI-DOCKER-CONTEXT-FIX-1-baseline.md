# CI-DOCKER-CONTEXT-FIX-1 Baseline

**任务**: 修复 docker-build-and-push.yml 中的 context 访问问题  
**日期**: 2025-12-05

---

## 1. 背景

在 RELEASE-RC1-1 完成后，IDE lint 持续报告 `.github/workflows/docker-build-and-push.yml` 中存在 "Context access might be invalid" 警告。

参考文档：
- `docs/ci/DOCKER-SMOKE-RUN-1-report.md`
- `docs/ci/RELEASE-RC1-1-report.md`

---

## 2. 相关文件

| 文件 | 状态 | 说明 |
|------|------|------|
| `.github/workflows/docker-build-and-push.yml` | ⚠️ 有问题 | 废弃的旧双镜像构建流程 |
| `.github/workflows/ci.yml` | ✅ 正常 | 当前主 CI（All-in-One 架构） |
| `docker-compose.yml` | ✅ 正常 | All-in-One 架构配置 |
| `Dockerfile` | ✅ 正常 | 根目录 All-in-One Dockerfile |

---

## 3. 问题分析

### 3.1 workflow 架构差异

| 属性 | docker-build-and-push.yml (废弃) | ci.yml (当前) |
|------|----------------------------------|---------------|
| 状态 | DEPRECATED | 活跃 |
| 架构 | 双镜像 (backend + frontend) | All-in-One 单镜像 |
| context | `./backend`, `./frontend` | `.` (根目录) |
| Dockerfile | 分离的 | 根目录 `Dockerfile` |

### 3.2 具体问题

#### 问题 1: 未定义的 input 引用

**位置**: 第 31, 58, 103-106 行

```yaml
# workflow_dispatch 只定义了:
inputs:
  deprecated_warning:
    description: '⚠️ This workflow is deprecated...'
    ...

# 但代码中引用了不存在的 skip_ci:
if: ${{ github.event.inputs.skip_ci != 'true' }}
```

**原因**: `skip_ci` input 在此 workflow 中从未定义。

#### 问题 2: env.STORE_PATH lint 警告

**位置**: 第 86 行

```yaml
- name: Get pnpm store directory
  run: echo "STORE_PATH=$(pnpm store path --silent)" >> $GITHUB_ENV

- name: Setup pnpm cache
  with:
    path: ${{ env.STORE_PATH }}  # <- lint 可能无法静态分析
```

**原因**: 静态 lint 工具无法确认 `STORE_PATH` 在此 step 之前已设置。

---

## 4. 修复策略

由于此 workflow 已废弃（DEPRECATED），采用最小修复策略：

1. **移除对 `skip_ci` 的引用** - 因为此 workflow 只能手动触发，不需要 skip 逻辑
2. **简化 job 条件** - 移除复杂的 needs 结果判断
3. **保持废弃标记** - 不恢复自动触发

---

## 5. 预期结果

修复后：
- ✅ GitHub Actions lint 警告消除
- ✅ workflow 语法合法
- ✅ 废弃状态保持，不影响主 CI (ci.yml)
