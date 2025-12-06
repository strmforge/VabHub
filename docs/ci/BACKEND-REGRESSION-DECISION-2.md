# BACKEND-REGRESSION-DECISION-2

## 问题描述

`test_decision_minimal.py` 在 CI 环境下返回 405 错误：
```
Client error '405 Method Not Allowed' for url '.../api/v1/subscriptions'
```

## 根因

**API 前缀不匹配**：

| 配置位置 | 值 | 说明 |
|----------|-----|------|
| `app/core/config.py` | `/api` | 后端实际使用 |
| `api_test_config.py` (旧) | `/api/v1` | 脚本默认值（过时） |

后端 `API_PREFIX` 已从 `/api/v1` 改为 `/api`，但测试脚本配置未同步更新。

## 解决方案

### 1. 修复 `api_test_config.py`

```python
# 旧
API_PREFIX = os.environ.get("API_PREFIX", "/api/v1")

# 新
API_PREFIX = os.environ.get("API_PREFIX", "/api")
```

### 2. 修复 `test_decision_minimal.py`

- 移除 `sites: ["test_site"]`（类型不匹配，`List[str]` vs `List[int]`）
- 添加 `print_http_error()` 函数输出详细错误
- 使用 `try/except HTTPStatusError` 包装关键 API 调用
- 添加 `IS_CI` 环境检测

## 验证方法

```bash
# 单跑决策最小回归
python backend/scripts/test_decision_minimal.py

# 跑完整 CI 辅助脚本
python backend/scripts/test_all.py --skip-music-execute
```

## 影响范围

| 环境 | 影响 |
|------|------|
| CI (Backend Regression) | ✅ 修复：脚本使用正确的 API 前缀 |
| 本地开发 | ✅ 无破坏性变更 |
| 生产环境 | ✅ 无影响 |

## 相关文件

- `backend/scripts/api_test_config.py` - API 配置
- `backend/scripts/test_decision_minimal.py` - 决策最小测试
- `docs/dev-notes/BACKEND-REGRESSION-DECISION-2-P0.md` - 问题分析

---

*Created: 2025-12-06*
