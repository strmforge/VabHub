# VabHub 数据库连接策略

> 防止 PostgreSQL 连接耗尽 (`too many clients already`)

---

## 1. 连接池配置

### 1.1 PostgreSQL 生产配置

```python
# backend/app/core/database.py
engine = create_async_engine(
    db_url,
    pool_pre_ping=True,   # 连接前 ping，确保连接有效
    pool_size=5,          # 基础连接池大小
    max_overflow=10,      # 最大溢出连接数（总共最多 15 连接）
    pool_timeout=30,      # 获取连接超时（秒）
    pool_recycle=1800,    # 30 分钟回收连接
)
```

### 1.2 参数说明

| 参数 | 值 | 说明 |
|------|-----|------|
| `pool_size` | 5 | 保持的最小连接数 |
| `max_overflow` | 10 | 额外允许的连接数 |
| `pool_timeout` | 30 | 等待可用连接的最大时间 |
| `pool_recycle` | 1800 | 连接最大存活时间（防止连接老化） |
| `pool_pre_ping` | True | 使用前检查连接是否有效 |

---

## 2. Session 生命周期规范

### 2.1 API 端点（依赖注入）

```python
# ✅ 正确：使用依赖注入
@router.get("/example")
async def example(db: AsyncSession = Depends(get_db)):
    result = await db.execute(...)
    return result
# Session 自动在请求结束后关闭
```

### 2.2 后台任务/Scheduler

```python
# ✅ 正确：使用 async with 确保关闭
async def background_task():
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(...)
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise
    # Session 在 with 块结束时自动关闭

# ❌ 错误：常驻 Session
class BadService:
    def __init__(self):
        self.db = AsyncSessionLocal()  # 永远不会关闭！
```

### 2.3 服务类

```python
# ✅ 正确：每次操作创建新 Session
class GoodService:
    async def do_something(self):
        async with AsyncSessionLocal() as db:
            # 操作数据库
            pass

# ❌ 错误：在 __init__ 中创建 Session
class BadService:
    def __init__(self, db: AsyncSession):
        self.db = db  # 如果服务是单例，Session 会泄漏
```

---

## 3. 常见问题排查

### 3.1 `too many clients already`

**原因**：连接池耗尽或连接泄漏

**排查步骤**：
1. 检查 PostgreSQL 最大连接数：`SHOW max_connections;`
2. 检查当前连接数：`SELECT count(*) FROM pg_stat_activity;`
3. 检查连接来源：`SELECT * FROM pg_stat_activity WHERE state != 'idle';`

**解决方案**：
- 降低 `pool_size` 和 `max_overflow`
- 检查后台任务是否正确关闭 Session
- 增加 PostgreSQL `max_connections`（默认 100）

### 3.2 连接超时

**原因**：所有连接都在使用中，等待超时

**解决方案**：
- 增加 `pool_timeout`
- 优化慢查询
- 检查是否有长时间持有连接的代码

---

## 4. Docker Compose 配置建议

```yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_MAX_CONNECTIONS: "100"  # 默认 100，可根据需要调整
    command: >
      postgres
      -c max_connections=100
      -c shared_buffers=256MB
```

---

*最后更新: 2025-12-13 VabHub 0.0.3*
