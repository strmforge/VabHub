# Docker 部署指南

> RELEASE-1 R4-2 实现

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/vabhub/vabhub.git
cd vabhub
```

### 2. 配置环境变量

```bash
cp .env.example .env

# 编辑 .env，至少修改以下配置：
# - DB_PASSWORD（数据库密码）
# - SECRET_KEY（应用密钥）
# - JWT_SECRET_KEY（JWT 密钥）
```

### 3. 启动服务

```bash
docker compose up -d
```

### 4. 访问应用

- 前端：http://localhost:8080
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 配置详解

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DB_NAME` | 数据库名称 | vabhub |
| `DB_USER` | 数据库用户 | vabhub |
| `DB_PASSWORD` | 数据库密码 | vabhub_password |
| `SECRET_KEY` | 应用密钥 | - |
| `JWT_SECRET_KEY` | JWT 密钥 | - |
| `APP_DEMO_MODE` | Demo 模式 | false |
| `VITE_API_BASE_URL` | 前端 API 地址 | http://localhost:8000/api |

### 数据卷

| 卷名 | 用途 |
|------|------|
| `vabhub_db_data` | PostgreSQL 数据 |
| `vabhub_redis_data` | Redis 数据 |
| `vabhub_data` | 应用数据（元数据等） |
| `vabhub_logs` | 日志文件 |

## 生产部署

### 使用生产配置

```bash
# 使用生产 compose 文件
docker compose -f docker-compose.prod.yml up -d
```

### 配置 HTTPS

1. 准备 SSL 证书：
```bash
mkdir -p certs
cp /path/to/fullchain.pem certs/
cp /path/to/privkey.pem certs/
```

2. 修改 `docker/nginx-prod.conf`，取消 HTTPS server 块的注释

3. 修改 `docker-compose.prod.yml`，取消证书挂载的注释

4. 重启服务：
```bash
docker compose -f docker-compose.prod.yml restart proxy
```

### 挂载媒体目录

```yaml
# docker-compose.prod.yml
backend:
  volumes:
    - /your/media/path:/media:ro
```

## Demo 模式

适合快速体验，无需配置外部服务：

```bash
# .env
APP_DEMO_MODE=true

# 启动后初始化 Demo 数据
docker compose exec backend python -m app.runners.demo_seed
```

详见 [Demo 模式文档](./DEMO_MODE_OVERVIEW.md)

## 常用命令

```bash
# 查看日志
docker compose logs -f backend
docker compose logs -f frontend

# 重启服务
docker compose restart backend

# 停止服务
docker compose down

# 停止并删除数据卷（慎用！）
docker compose down -v

# 更新镜像
docker compose pull
docker compose up -d

# 进入容器
docker compose exec backend bash
docker compose exec db psql -U vabhub
```

## 升级版本

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建镜像
docker compose build

# 3. 重启服务
docker compose up -d

# 4. 如有数据库迁移（未来版本）
# docker compose exec backend alembic upgrade head
```

## 故障排查

### 后端无法连接数据库

```bash
# 检查数据库容器状态
docker compose ps db

# 查看数据库日志
docker compose logs db

# 手动测试连接
docker compose exec backend python -c "from app.core.database import engine; print(engine.url)"
```

### 前端无法连接后端

1. 检查 `VITE_API_BASE_URL` 配置
2. 检查浏览器控制台网络请求
3. 确认后端健康检查：`curl http://localhost:8000/api/health`

### 端口被占用

```bash
# 修改 docker-compose.yml 中的端口映射
ports:
  - "8081:80"  # 改为其他端口
```

## 资源需求

| 服务 | 最小内存 | 推荐内存 |
|------|----------|----------|
| PostgreSQL | 256MB | 512MB |
| Redis | 64MB | 128MB |
| Backend | 256MB | 512MB |
| Frontend | 64MB | 128MB |
| **总计** | **640MB** | **1.3GB** |

## 相关文档

- [安装指南](./INSTALL_GUIDE.md)
- [Demo 模式](./DEMO_MODE_OVERVIEW.md)
- [Runner 配置](./RUNNERS_OVERVIEW.md)
- [备份恢复](./BACKUP_AND_RESTORE.md)
