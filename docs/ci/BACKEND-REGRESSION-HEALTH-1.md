# BACKEND-REGRESSION-HEALTH-1

## 问题描述

Backend Regression workflow 中 `/health` 端点持续返回 503，导致 API 探活失败，即使数据库连接正常。

## 根因分析

1. **健康检查状态码逻辑过于严格**：
   ```python
   # 原逻辑
   status_code = 200 if result["status"] == "healthy" else 503
   ```
   
2. **L3 缓存检查始终返回 `warning`**（因 SQLAlchemy mapper 冲突被禁用）

3. **结果**：整体状态为 `warning`，而 `warning ≠ healthy` → 返回 503

## 解决方案

### 1. 重新定义状态码规则

```python
# 新逻辑：warning 不影响服务可用性
status_code = 503 if result["status"] == "unhealthy" else 200
```

状态定义：
- **healthy**：所有检查通过 → HTTP 200
- **warning**：有非关键组件异常，但不影响核心功能 → HTTP 200
- **unhealthy**：关键组件失败，服务不可用 → HTTP 503

### 2. 增加运行模式检测

响应新增 `mode` 字段：
- `ci`：CI 环境（`VABHUB_CI=1`）
- `dev`：开发环境（使用 SQLite）
- `prod`：生产环境（使用 PostgreSQL）

### 3. 改进 CI 等待脚本

- 超时从 60s 增加到 90s
- 添加详细的 HTTP 状态码输出
- 失败时输出健康检查响应和 uvicorn 日志

## 示例响应

```json
{
  "status": "warning",
  "mode": "ci",
  "timestamp": "2025-12-06T06:52:35.000000",
  "checks": {
    "database": {"status": "healthy", "message": "数据库连接正常"},
    "cache": {"status": "healthy", "message": "缓存系统正常 (3级缓存)"},
    "cache_l3": {"status": "warning", "message": "L3缓存检查暂时不可用"},
    "disk": {"status": "healthy", "message": "磁盘空间: 10.4% 已使用"}
  }
}
```

## 影响范围

| 环境 | 影响 |
|------|------|
| CI (Backend Regression) | ✅ 修复：`warning` 状态不再导致 503 |
| 开发环境 | ✅ 无破坏性变更 |
| 生产环境 (Docker) | ✅ 无破坏性变更，行为更合理 |

## 测试覆盖

新增测试文件：`backend/tests/core/test_health_endpoint.py`

- 状态码逻辑测试（healthy/warning/unhealthy）
- 运行模式检测测试
- 响应结构测试
- 集成测试

## 相关文件

- `backend/main.py` - 健康检查端点
- `backend/app/core/health.py` - 健康检查器实现
- `.github/workflows/test-all.yml` - Backend Regression workflow

---

*Created: 2025-12-06*
