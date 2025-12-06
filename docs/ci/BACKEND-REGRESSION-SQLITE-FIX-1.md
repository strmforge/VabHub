# BACKEND-REGRESSION-SQLITE-FIX-1

## 问题描述

Backend Regression 工作流中 API 启动失败，报错：

```
sqlite3.OperationalError: unable to open database file
```

## 根因

1. **SQLite 数据库目录未创建**：当 `DATABASE_URL` 指向一个不存在的目录时，SQLite 不会自动创建父目录
2. **Workflow 中的 shell 展开问题**：`DATABASE_URL: sqlite:///$(pwd)/vabhub_ci.db` 在 YAML env 定义中可能不会正确展开

## 解决方案

### 1. 数据库模块自动创建目录

在 `backend/app/core/database.py` 中新增 `_ensure_sqlite_dir()` 函数：

```python
def _ensure_sqlite_dir(url: str) -> None:
    """确保 SQLite 数据库文件的父目录存在"""
    if not url.startswith("sqlite"):
        return
    
    path_part = url.split("///", 1)
    if len(path_part) < 2 or not path_part[1]:
        return
    
    db_path = Path(path_part[1])
    if db_path.parent and db_path.parent != Path("."):
        db_path.parent.mkdir(parents=True, exist_ok=True)
```

### 2. Backend Regression workflow 显式配置

在 `.github/workflows/test-all.yml` 中：

```yaml
- name: Prepare CI data directory
  run: |
    mkdir -p .ci_data

- name: Start backend server
  env:
    DATABASE_URL: "sqlite:///./.ci_data/vabhub_regression.db"
```

## 本地回归验证

```bash
# 清理环境
unset DATABASE_URL
rm -rf backend/.ci_data

# 模拟 CI 启动
cd backend
export DATABASE_URL="sqlite:///./.ci_data/vabhub_regression.db"
uvicorn main:app --host 0.0.0.0 --port 8100 &

# 探活
curl http://127.0.0.1:8100/health
```

## 测试覆盖

新增测试文件：`backend/tests/core/test_database_sqlite_dev.py`

- `test_creates_parent_directory` - 验证自动创建目录
- `test_ignores_postgres_url` - 验证不影响 PostgreSQL
- `test_ignores_memory_database` - 验证内存数据库
- `test_handles_relative_path` - 验证相对路径
- `test_existing_directory_no_error` - 验证目录已存在时不报错
- `test_handles_sqlite_without_aiosqlite` - 验证纯 sqlite:// URL

## 影响范围

- ✅ 开发模式 SQLite：自动创建数据库目录
- ✅ CI 回归测试：使用显式路径
- ❌ Docker 部署：不受影响（使用 PostgreSQL）
- ❌ 生产环境：不受影响（使用 PostgreSQL）

---

*Created: 2025-12-06*
