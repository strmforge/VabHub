# BACKEND-REGRESSION-HEALTH-1 P0 现状巡检

## 问题描述

Backend Regression workflow 中 `/health` 持续返回 503，导致 API 探活失败。

## 当前 /health 实现分析

### 路由位置
`backend/main.py` 第 363-369 行：
```python
@app.get("/health")
async def health_check():
    """健康检查"""
    health_checker = get_health_checker()
    result = await health_checker.check_all()
    status_code = 200 if result["status"] == "healthy" else 503
    return JSONResponse(content=result, status_code=status_code)
```

### 健康检查器
`backend/app/core/health.py` - `HealthChecker` 类

注册的检查项：
1. **database** - 数据库连接检查 (`SELECT 1`)
2. **cache** - L1+L2 缓存检查
3. **cache_l3** - L3 数据库缓存检查（已禁用，返回 warning）
4. **disk** - 磁盘空间检查

### 状态判定逻辑
```python
if result.get("status") == "unhealthy":
    overall_status = "unhealthy"
elif result.get("status") == "warning" and overall_status == "healthy":
    overall_status = "warning"
```

## CI 场景复现

### 环境变量
```bash
VABHUB_CI=1
DATABASE_URL=sqlite:///./.ci_data/vabhub_regression.db
REDIS_ENABLED=false
```

### 实际健康检查结果
```
Status: warning
Checks:
  database: {'status': 'healthy', 'message': '数据库连接正常'}
  cache: {'status': 'healthy', 'message': '缓存系统正常 (3级缓存)'}
  cache_l3: {'status': 'warning', 'message': 'L3缓存检查暂时不可用'}
  disk: {'status': 'healthy', 'message': '磁盘空间: 10.4% 已使用'}
```

## 根因

1. **cache_l3** 检查始终返回 `warning`（因为 SQLAlchemy mapper 冲突被禁用）
2. 整体状态变为 `warning`
3. `main.py` 判断：`200 if status == "healthy" else 503`
4. `warning` ≠ `healthy` → 返回 503

## 修复方案

1. **修改 HTTP 状态码判定逻辑**：
   - `healthy` → 200
   - `warning` → 200（警告不影响服务可用性）
   - `unhealthy` → 503

2. **CI 模式特殊处理**（可选）：
   - 当 `VABHUB_CI=1` 时，只检查硬性条件（database）
   - 软性条件（cache_l3、optional services）只在 JSON 中体现

---

*Created: 2025-12-06*
