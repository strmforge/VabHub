# CI-DOCKER-CONTEXT-FIX-1 Report

**任务**: 修复 docker-build-and-push.yml 中的 context 访问问题  
**日期**: 2025-12-05  
**版本**: 0.0.1-rc1（保持不变）

---

## 1. 背景

在 RELEASE-RC1-1 完成后，IDE lint 持续报告 `.github/workflows/docker-build-and-push.yml` 中存在 "Context access might be invalid" 警告。

参考文档：
- `docs/ci/CI-DOCKER-CONTEXT-FIX-1-baseline.md`
- `docs/ci/DOCKER-SMOKE-RUN-1-report.md`

---

## 2. 问题描述

| 行号 | 原代码 | 问题 |
|------|--------|------|
| 31 | `if: ${{ github.event.inputs.skip_ci != 'true' }}` | `skip_ci` input 未定义 |
| 58 | `if: ${{ github.event.inputs.skip_ci != 'true' }}` | `skip_ci` input 未定义 |
| 86 | `path: ${{ env.STORE_PATH }}` | 静态分析无法确认 env 变量 |
| 103-106 | `github.event.inputs.skip_ci == 'true'` | `skip_ci` input 未定义 |

---

## 3. 修改内容

### 3.1 移除无效的 skip_ci 引用

**原代码** (第 31 行):
```yaml
if: ${{ github.event.inputs.skip_ci != 'true' }}
```

**修改后**:
```yaml
# [DEPRECATED] 此 workflow 已废弃，移除无效的 skip_ci 判断
```

### 3.2 简化 docker-build 条件

**原代码** (第 103-106 行):
```yaml
if: |
  always() && 
  (github.event.inputs.skip_ci == 'true' || 
   (needs.backend-ci.result == 'success' && needs.frontend-ci.result == 'success'))
```

**修改后**:
```yaml
# [DEPRECATED] 简化条件判断，移除无效的 skip_ci 引用
if: |
  always() && 
  (needs.backend-ci.result == 'success' && needs.frontend-ci.result == 'success')
```

### 3.3 修复 env.STORE_PATH 静态检查警告

**原代码** (第 86 行):
```yaml
path: ${{ env.STORE_PATH }}
```

**修改后**:
```yaml
# 使用 pnpm 默认 store 路径，避免 env context 静态检查警告
path: ~/.local/share/pnpm/store
```

---

## 4. 验证情况

| 方法 | 结果 | 说明 |
|------|------|------|
| actionlint | ❌ 不可用 | 本地环境未安装 |
| act dry run | ❌ 不可用 | 本地环境未安装 |
| 人工审查 | ✅ 通过 | YAML 语法正确，context 引用已修复 |
| IDE lint | ✅ 通过 | 警告已消除 |

**后续验证**: 下次 push 到 GitHub 时观察 workflow 日志确认无报错。

---

## 5. 风险评估

| 风险 | 级别 | 说明 |
|------|------|------|
| 镜像功能变化 | 无 | 只修复 CI 配置，不改构建逻辑 |
| 构建失败 | 低 | 此 workflow 已废弃，实际 Docker 构建使用 ci.yml |
| pnpm 缓存失效 | 低 | 硬编码路径在 Ubuntu runner 上是标准位置 |

---

## 6. 文件变更

| 文件 | 变更类型 |
|------|----------|
| `.github/workflows/docker-build-and-push.yml` | 修改 |
| `docs/ci/CI-DOCKER-CONTEXT-FIX-1-baseline.md` | 新增 |
| `docs/ci/CI-DOCKER-CONTEXT-FIX-1-report.md` | 新增 |
| `docs/VABHUB_SYSTEM_OVERVIEW.md` | 轻量更新 |

---

## 7. 总结

✅ **修复完成**

- 移除了对未定义 `skip_ci` input 的 3 处引用
- 修复了 `env.STORE_PATH` 静态检查警告
- 保持 workflow 废弃状态，不影响主 CI (ci.yml)
- 版本保持 0.0.1-rc1，无需新 tag
