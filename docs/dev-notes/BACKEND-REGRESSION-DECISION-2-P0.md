# BACKEND-REGRESSION-DECISION-2 P0 现状巡检

## 问题描述

`test_decision_minimal.py` 在 CI 环境下返回 405 错误：
```
Client error '405 Method Not Allowed' for url '.../api/v1/subscriptions'
```

## 脚本现状

### 调用的 API

| 步骤 | 脚本调用 | 方法 |
|------|----------|------|
| 1 | `POST /api/v1/subscriptions` | 创建订阅 |
| 2 | `POST /api/v1/decision/dry-run` | 决策 Dry-Run |
| 3 | `DELETE /api/v1/subscriptions/{id}` | 删除订阅 |

### `api_test_config.py` 配置

```python
API_PREFIX = os.environ.get("API_PREFIX", "/api/v1")  # 默认 /api/v1
```

## 后端实际路由

### `app/core/config.py`

```python
API_PREFIX: str = "/api"  # 已移除 /v1 前缀
```

### 订阅路由（`app/api/subscription.py` + `__init__.py`）

| 路由 | 方法 | 说明 |
|------|------|------|
| `POST /api/subscriptions` | 创建订阅 | ✅ 存在 |
| `GET /api/subscriptions` | 列表订阅 | ✅ 存在 |
| `GET /api/subscriptions/{id}` | 获取订阅 | ✅ 存在 |
| `PUT /api/subscriptions/{id}` | 更新订阅 | ✅ 存在 |
| `DELETE /api/subscriptions/{id}` | 删除订阅 | ✅ 存在 |

### 决策路由（`app/api/decision.py` + `__init__.py`）

| 路由 | 方法 | 说明 |
|------|------|------|
| `POST /api/decision/dry-run` | 决策 Dry-Run | ✅ 存在 |

## 根因分析

### 问题所在

**API 前缀不匹配**：

- 脚本使用：`/api/v1` (默认值)
- 后端实际：`/api` (配置文件已移除 `/v1`)

所以脚本调用的 `POST /api/v1/subscriptions` 实际上不存在，返回 405。

### 谁对谁错

这是**脚本配置过时**的问题，不是后端 bug：

1. 后端 `API_PREFIX` 已经从 `/api/v1` 改为 `/api`（配置文件有注释说明）
2. `api_test_config.py` 的默认值仍然是旧的 `/api/v1`
3. 订阅和决策相关的 API 都已正确实现

## 修复方案

### 方案选择：方案 A（推荐）

不改后端路由，修改测试脚本配置：

1. **修改 `api_test_config.py`**：将默认 `API_PREFIX` 从 `/api/v1` 改为 `/api`
2. **保留脚本逻辑**：脚本的创建/决策/删除流程是合理的，不需要改用纯 Dry-Run
3. **增强错误输出**：添加 HTTP 错误详情输出

### 额外发现

脚本中 `sites` 字段类型不匹配：
- 脚本传入：`["test_site"]` (字符串列表)
- Schema 期望：`List[int]` (整数列表)

但这会导致 422 (Validation Error)，不是 405。修复前缀后需要同时修复这个问题。

---

## 解决方案小结（已实施）

### 修改文件

1. **`backend/scripts/api_test_config.py`**：
   - `API_PREFIX` 默认值从 `/api/v1` 改为 `/api`

2. **`backend/scripts/test_decision_minimal.py`**：
   - 移除 `sites: ["test_site"]`（类型不匹配）
   - 添加 `print_http_error()` 函数
   - 使用 `try/except HTTPStatusError` 包装 API 调用
   - 添加 `IS_CI` 环境检测

### 验证结果

- ✅ 语法检查通过
- ✅ API 路径正确（`/api/subscriptions` 而非 `/api/v1/subscriptions`）
- ✅ 错误输出增强

---

*Created: 2025-12-06*
*Updated: 2025-12-06 - 已完成修复*
