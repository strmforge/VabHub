# BACKEND-REGRESSION-SQLITE-FIX-1 P0 现状巡检

## 问题描述

Backend Regression workflow 中 API 启动失败，报错：
```
sqlite3.OperationalError: unable to open database file
```

## 现状分析

### 1. SQLite 默认 URL

在 `backend/app/core/config.py` 中：
```python
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "sqlite:///./vabhub.db"  # 开发环境使用SQLite
)
```

### 2. database.py 初始化逻辑

```python
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(
        settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://"),
        ...
    )
```

**问题**：没有检查/创建 SQLite 文件的父目录。

### 3. Backend Regression workflow

位置：`.github/workflows/test-all.yml`

```yaml
- name: Start backend server
  working-directory: backend
  env:
    DATABASE_URL: sqlite:///$(pwd)/vabhub_ci.db
  run: |
    uvicorn main:app --host 0.0.0.0 --port 8100 > ../uvicorn.log 2>&1 &
```

**问题**：
1. `$(pwd)` 在 YAML env 定义中可能不会正确展开
2. 即使路径正确，如果父目录不存在也会失败

### 4. 本地复现

```powershell
$env:DATABASE_URL = "sqlite:///./nonexistent_dir/vabhub_ci.db"
cd backend
python -c "import asyncio; from app.core.database import init_db; asyncio.run(init_db())"
```

报错：
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unable to open database file
```

## 根因

当 SQLite 数据库文件路径的父目录不存在时，SQLite 不会自动创建目录，导致 `unable to open database file` 错误。

## 修复方案

1. **P1**：在 `database.py` 中检测到 SQLite URL 时，自动创建父目录
2. **P2**：在 Backend Regression workflow 中显式设置正确的 DATABASE_URL 路径

---

*Created: 2025-12-06*
