# 部署指南

## 概述

本文档说明如何部署 Manga Source Phase 2 功能，包括数据库迁移、环境配置和Docker部署。

## 自动迁移

Manga Source Phase 2 使用自动迁移系统，首次启动时会自动执行所需的数据库变更。

### 迁移内容

- 添加 `last_remote_chapter_id` 字段到 `user_manga_follow` 表
- 更新通知 Schema 支持远程追更
- 初始化默认配置

### 迁移执行

迁移会在应用启动时自动运行，无需手动干预：

```bash
# 启动应用，迁移自动执行
docker-compose up -d

# 查看迁移日志
docker logs vabhub_container | grep "migration"
```

## 环境配置

### 必需环境变量

```bash
# 基础配置
DATABASE_URL=sqlite:///./vabhub.db
SECRET_KEY=your-secret-key-here

# 通知配置（可选）
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

### 漫画源配置（可选）

可以通过环境变量预配置漫画源：

```bash
# Komga 源
MANGA_SOURCE_KOMGA_URL=http://komga:8080
MANGA_SOURCE_KOMGA_USERNAME=admin
MANGA_SOURCE_KOMGA_PASSWORD=password

# OPDS 源
MANGA_SOURCE_OPDS_URL=https://example.com/opds
MANGA_SOURCE_OPDS_USERNAME=user
MANGA_SOURCE_OPDS_PASSWORD=pass

# Suwayomi 源
MANGA_SOURCE_SUWAYOMI_URL=http://suwayomi:4567
MANGA_SOURCE_SUWAYOMI_API_KEY=api-key
```

## Docker 部署

### 使用 Docker Compose（推荐）

```yaml
# docker-compose.yml
version: '3.8'

services:
  vabhub:
    image: vabhub/vabhub:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./vabhub.db
      - SECRET_KEY=${SECRET_KEY}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    depends_on:
      - komga
    networks:
      - manga-network

  komga:
    image: gotson/komga:latest
    ports:
      - "8080:8080"
    volumes:
      - ./komga-data:/config
      - ./manga:/data
    environment:
      - KOMGA_SERVER_HOST=0.0.0.0
    networks:
      - manga-network

networks:
  manga-network:
    driver: bridge

volumes:
  komga-data:
  manga:
```

### 部署步骤

1. **准备环境文件**
   ```bash
   # .env
   SECRET_KEY=your-very-secret-key-here
   TELEGRAM_BOT_TOKEN=your-bot-token
   TELEGRAM_CHAT_ID=your-chat-id
   ```

2. **启动服务**
   ```bash
   docker-compose up -d
   ```

3. **验证部署**
   ```bash
   # 检查服务状态
   docker-compose ps
   
   # 查看应用日志
   docker-compose logs vabhub
   ```

4. **配置漫画源**
   - 访问 `http://localhost:8000`
   - 进入漫画中心 → 外部源管理
   - 添加和配置漫画源

## 手动部署

### 1. 环境准备

```bash
# Python 3.9+
python --version

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据库初始化

```bash
# 运行迁移
python -m app.core.migrations.run_all

# 或手动运行特定迁移
python -m app.core.migrations.run manga_remote_follow
```

### 3. 启动应用

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 配置验证

### 检查迁移状态

```bash
# 检查数据库迁移
python -c "
from app.core.database import engine
from sqlalchemy import text
import asyncio

async def check():
    async with engine.begin() as conn:
        result = await conn.execute(text('SELECT last_remote_chapter_id FROM user_manga_follow LIMIT 1'))
        print('Migration successful: column exists')

asyncio.run(check())
"
```

### 测试漫画源连接

```bash
# 测试 API 端点
curl "http://localhost:8000/api/manga/remote/sources"

# 测试搜索功能
curl "http://localhost:8000/api/manga/remote/aggregated-search?q=test"
```

## 性能优化

### 数据库优化

```bash
# SQLite 优化（生产环境）
export DATABASE_URL="sqlite:///./vabhub.db?timeout=30&check_same_thread=false"

# PostgreSQL 优化（推荐）
export DATABASE_URL="postgresql://user:pass@localhost/vabhub?pool_size=20&max_overflow=30"
```

### 缓存配置

```bash
# Redis 缓存（可选）
export REDIS_URL="redis://localhost:6379/0"
export CACHE_TTL=3600
```

### 并发设置

```bash
# 工作进程数
export WORKERS=4

# 搜索超时设置
export SEARCH_TIMEOUT=30
```

## 监控和日志

### 日志配置

```bash
# 日志级别
export LOG_LEVEL=INFO

# 日志文件
export LOG_FILE=/app/logs/vabhub.log

# 调试模式
export DEBUG=false
```

### 健康检查

```bash
# 应用健康检查
curl "http://localhost:8000/health"

# 数据库连接检查
curl "http://localhost:8000/health/db"
```

### 监控指标

```bash
# 启用指标收集
export METRICS_ENABLED=true

# 访问指标端点
curl "http://localhost:8000/metrics"
```

## 备份和恢复

### 数据备份

```bash
# SQLite 备份
cp vabhub.db backup/vabhub-$(date +%Y%m%d).db

# PostgreSQL 备份
pg_dump vabhub > backup/vabhub-$(date +%Y%m%d).sql
```

### 配置备份

```bash
# 备份漫画源配置
sqlite3 vabhub.db ".dump manga_sources" > backup/sources-$(date +%Y%m%d).sql

# 备份追更数据
sqlite3 vabhub.db ".dump user_manga_follow" > backup/follows-$(date +%Y%m%d).sql
```

## 故障排除

### 常见部署问题

1. **迁移失败**
   ```bash
   # 检查数据库权限
   ls -la vabhub.db
   
   # 手动执行迁移
   python -m app.core.migrations.run_all --force
   ```

2. **漫画源连接失败**
   ```bash
   # 检查网络连接
   docker exec vabhub ping komga
   
   # 检查环境变量
   docker exec vabhub env | grep MANGA_SOURCE
   ```

3. **性能问题**
   ```bash
   # 检查资源使用
   docker stats vabhub
   
   # 优化数据库
   sqlite3 vabhub.db "VACUUM; ANALYZE;"
   ```

### 日志分析

```bash
# 查看错误日志
docker logs vabhub | grep ERROR

# 查看搜索日志
docker logs vabhub | grep "aggregated_search"

# 查看同步日志
docker logs vabhub | grep "follow_sync"
```

## 升级指南

### 从旧版本升级

1. **备份数据**
   ```bash
   # 备份数据库
   cp vabhub.db backup/vabhub-before-upgrade.db
   ```

2. **更新应用**
   ```bash
   # 拉取最新镜像
   docker-compose pull vabhub
   
   # 或更新代码
   git pull origin main
   pip install -r requirements.txt
   ```

3. **运行迁移**
   ```bash
   # 重启服务，自动迁移
   docker-compose up -d
   
   # 检查迁移状态
   docker logs vabhub | grep migration
   ```

### 版本兼容性

| VabHub 版本 | Manga Source 版本 | 兼容性 |
|-------------|-------------------|--------|
| 1.0.x | Phase 1 | ✅ |
| 1.1.x | Phase 2 | ✅ |
| 1.2.x | Phase 2+ | ✅ |

## 安全配置

### HTTPS 配置

```bash
# 使用反向代理
export USE_HTTPS=true
export TRUSTED_PROXIES=nginx,traefik
```

### 访问控制

```bash
# 启用认证
export AUTH_ENABLED=true
export JWT_SECRET_KEY=your-jwt-secret
```

### 网络安全

```yaml
# 限制容器网络访问
services:
  vabhub:
    networks:
      - internal
      - external
    # 只暴露必要端口
    ports:
      - "8000:8000"
```

部署完成后，请参考 [用户指南](./USER_GUIDE.md) 开始使用 Manga Source 功能。
