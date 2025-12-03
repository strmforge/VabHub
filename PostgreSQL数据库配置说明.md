# PostgreSQL数据库配置说明

## 📋 概述

VabHub现在**默认使用PostgreSQL数据库**，提供更好的性能、可靠性和功能支持。

**更新日期**: 2025-11-08  
**状态**: ✅ PostgreSQL已设置为默认数据库

---

## 🗄️ 数据库支持

### 支持的数据库
1. **PostgreSQL**（默认，推荐用于生产环境）✅
2. **SQLite**（可选，用于开发/测试）

### 为什么默认使用PostgreSQL？

#### 1. 性能优势
- **并发性能**: PostgreSQL支持高并发读写
- **连接池**: 内置连接池，支持更多并发连接
- **索引优化**: 更强大的索引类型和优化

#### 2. 功能优势
- **JSON支持**: 原生JSON/JSONB支持
- **全文搜索**: 内置全文搜索功能
- **触发器**: 支持数据库触发器
- **分区表**: 支持表分区（大规模数据）

#### 3. 可靠性
- **ACID事务**: 完整的事务支持
- **数据完整性**: 强大的约束和验证
- **备份恢复**: 完善的备份恢复机制

#### 4. 生产环境
- **扩展性**: 支持大规模数据
- **稳定性**: 企业级稳定性
- **社区支持**: 活跃的社区和文档

---

## 🔧 配置说明

### 环境变量配置

#### PostgreSQL配置（默认）
```bash
# .env 文件
DATABASE_URL=postgresql://vabhub:vabhub@localhost:5432/vabhub
```

#### SQLite配置（开发/测试）
```bash
# .env 文件
DATABASE_URL=sqlite:///./vabhub.db
```

### 数据库URL格式

#### PostgreSQL
```
postgresql://用户名:密码@主机:端口/数据库名
```

示例：
- `postgresql://vabhub:vabhub@localhost:5432/vabhub`
- `postgresql://user:pass@192.168.1.100:5432/vabhub`
- `postgresql://user:pass@db.example.com:5432/vabhub`

#### SQLite
```
sqlite:///./数据库文件名.db
```

示例：
- `sqlite:///./vabhub.db`
- `sqlite:///./data/vabhub.db`

---

## 🚀 快速开始

### 1. 安装PostgreSQL

#### Windows
```bash
# 下载并安装PostgreSQL
# https://www.postgresql.org/download/windows/
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

#### macOS
```bash
brew install postgresql
brew services start postgresql
```

### 2. 创建数据库

```bash
# 连接到PostgreSQL
psql -U postgres

# 创建数据库和用户
CREATE DATABASE vabhub;
CREATE USER vabhub WITH PASSWORD 'vabhub';
GRANT ALL PRIVILEGES ON DATABASE vabhub TO vabhub;
\q
```

### 3. 配置环境变量

创建 `.env` 文件：
```bash
DATABASE_URL=postgresql://vabhub:vabhub@localhost:5432/vabhub
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

**必需的依赖**：
- `asyncpg` - PostgreSQL异步驱动
- `sqlalchemy` - ORM框架

### 5. 初始化数据库

```bash
# 运行数据库初始化
python -m app.core.database init
```

或使用迁移脚本：
```bash
# PostgreSQL迁移
python migrate_add_cache_table_postgresql.py
```

---

## 📊 数据库连接配置

### 连接池配置

PostgreSQL连接池配置（在 `app/core/database.py` 中）：
- **pool_size**: 10（连接池大小）
- **max_overflow**: 20（最大溢出连接数）
- **pool_pre_ping**: True（连接前ping，确保连接有效）

### 性能优化

1. **连接池**: 自动管理数据库连接
2. **异步操作**: 使用asyncpg进行异步数据库操作
3. **索引优化**: 自动创建必要的索引
4. **查询优化**: SQLAlchemy自动优化查询

---

## 🔍 数据库模型

### 支持的模型
- User（用户）
- Media（媒体）
- Subscription（订阅）
- DownloadTask（下载任务）
- Workflow（工作流）
- Site（站点）
- Notification（通知）
- MusicSubscription（音乐订阅）
- CacheEntry（L3缓存）⭐

### 表结构

所有表都支持：
- **自动时间戳**: `created_at`, `updated_at`
- **索引优化**: 自动创建必要索引
- **约束验证**: 数据完整性约束

---

## 🛠️ 迁移脚本

### PostgreSQL迁移脚本

#### 缓存表迁移
```bash
python migrate_add_cache_table_postgresql.py
```

#### 其他迁移
- 所有迁移脚本都支持PostgreSQL
- 自动检测数据库类型
- 使用SQLAlchemy进行跨数据库兼容

---

## 📈 性能对比

### PostgreSQL vs SQLite

| 特性 | PostgreSQL | SQLite |
|------|------------|--------|
| **并发** | ✅ 高并发 | ❌ 单连接 |
| **性能** | ✅ 高性能 | ⚠️ 中等 |
| **容量** | ✅ 大容量 | ⚠️ 有限 |
| **功能** | ✅ 丰富 | ⚠️ 基础 |
| **生产环境** | ✅ 推荐 | ❌ 不推荐 |
| **开发环境** | ✅ 可用 | ✅ 简单 |

---

## 🔒 安全建议

### 1. 数据库用户权限
```sql
-- 创建专用用户
CREATE USER vabhub WITH PASSWORD 'strong-password';

-- 授予必要权限
GRANT CONNECT ON DATABASE vabhub TO vabhub;
GRANT USAGE ON SCHEMA public TO vabhub;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO vabhub;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO vabhub;
```

### 2. 连接加密
```bash
# 使用SSL连接
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

### 3. 防火墙配置
- 限制数据库端口访问
- 仅允许应用服务器访问

---

## 🐛 故障排除

### 常见问题

#### 1. 连接失败
```
错误: could not connect to server
```

**解决方案**:
- 检查PostgreSQL服务是否运行
- 检查数据库URL配置
- 检查防火墙设置

#### 2. 认证失败
```
错误: password authentication failed
```

**解决方案**:
- 检查用户名和密码
- 检查 `pg_hba.conf` 配置

#### 3. 数据库不存在
```
错误: database "vabhub" does not exist
```

**解决方案**:
```bash
# 创建数据库
createdb vabhub
```

---

## ✅ 总结

### 优势
1. ✅ **默认PostgreSQL**: 更好的性能和功能
2. ✅ **生产就绪**: 适合生产环境使用
3. ✅ **向后兼容**: 仍支持SQLite（开发/测试）
4. ✅ **自动配置**: 自动检测和配置数据库类型

### 推荐配置
- **生产环境**: PostgreSQL ✅
- **开发环境**: PostgreSQL 或 SQLite
- **测试环境**: SQLite（快速测试）

---

**最后更新**: 2025-11-08  
**状态**: ✅ PostgreSQL已设置为默认数据库

