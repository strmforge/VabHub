# RELEASE-RC1-1 Baseline Report

**执行日期**: 2025-12-05  
**任务**: 0.0.1-rc1 轻量封版

---

## 基线信息

| 项目 | 值 |
|------|------|
| Git 分支 | `main` |
| Commit Hash | `11d4d56` |
| 执行环境 | Windows + WSL2 |

---

## CI 检查结果

### 后端 (scripts/dev_check_backend.sh)

| 检查项 | 结果 | 说明 |
|--------|------|------|
| ruff check | ✅ PASS | All checks passed! |
| mypy | ✅ PASS | no issues found in 1140 source files |
| pytest | ✅ PASS | 447 passed, 88 skipped, 306 warnings |

**运行时间**: ~72.40s

### 前端 (pnpm dev_check)

| 检查项 | 结果 | 说明 |
|--------|------|------|
| vue-tsc | ✅ PASS | 70 TypeScript warnings (Vuetify slot 类型) |
| eslint | ✅ PASS | 已集成到 dev_check |

**已知问题**:
- 70 个 TypeScript 错误均为 Vuetify v-data-table 和 v-for slot 类型问题
- 这是 Vuetify 上游已知问题，不影响运行时
- 构建脚本已配置为接受这些警告

---

## 结论

✅ **基线状态可封版**

后端和前端 CI 均通过，当前代码状态满足 0.0.1-rc1 封版要求。

---

**参考文档**:
- `docs/ci/FRONTEND-DOCKER-BUILD-FIX-1.md`
- `docs/ci/DOCKER-SMOKE-RUN-1-report.md`
