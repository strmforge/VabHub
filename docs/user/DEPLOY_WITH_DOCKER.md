# VabHub Docker 部署指南

> ⚠️ **官方部署说明**
> 当前版本 VabHub 官方推荐、也是唯一维护的部署方式是：**Docker / docker-compose 部署**。
> 其他运行方式（裸机 Python、k8s 等）仅面向开发者/高级用户，暂不提供详细教程。

## §0. 使用前提

- 您需要具备 Docker 和 docker-compose 的基础知识
- 确保您的系统已经安装了 Docker 和 docker-compose
- 建议分配至少 4GB 内存和 20GB 磁盘空间用于部署

## §1. 快速开始（5 分钟部署）

### 步骤 1：获取项目文件

克隆仓库（推荐）：

```bash
git clone https://github.com/your-username/vabhub.git
cd vabhub
```

或下载发布包并解压。

### 步骤 2：配置环境变量

复制示例环境变量文件：

```bash
cp .env.docker.example .env.docker
```

编辑 `.env.docker` 文件，至少修改以下几个关键配置：

- `SECRET_KEY` 和 `JWT_SECRET_KEY`：设置为强随机字符串
- `TMDB_API_KEY`：填写您的 TMDB API Key（获取地址：https://www.themoviedb.org/settings/api）

### 步骤 3：Docker Compose 配置

VabHub 使用 Docker Compose 管理所有服务。以下是完整的 `docker-compose.yml` 示例，与仓库中提供的配置保持一致：

```yaml
# VabHub Docker Compose 配置
version: '3.8'

services:
  # PostgreSQL 数据库：存储应用数据
  db:
    image: postgres:14-alpine
    container_name: vabhub-db
    environment:
      POSTGRES_DB: ${DB_NAME:-vabhub}
      POSTGRES_USER: ${DB_USER:-vabhub}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-vabhub_password}
    volumes:
      - vabhub_db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-vabhub}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - vabhub-internal
    restart: unless-stopped

  # Redis 缓存：提高应用性能
  redis:
    image: redis:7-alpine
    container_name: vabhub-redis
    command: redis-server --appendonly yes
    volumes:
      - vabhub_redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - vabhub-internal
    restart: unless-stopped

  # 后端服务：处理核心业务逻辑
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: vabhub-backend
    environment:
      - DATABASE_URL=postgresql://${DB_USER:-vabhub}:${DB_PASSWORD:-vabhub_password}@db:5432/${DB_NAME:-vabhub}
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY:-change-this-in-production}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-change-this-in-production}
      - APP_DEMO_MODE=${APP_DEMO_MODE:-false}
      - APP_BASE_URL=${APP_BASE_URL:-http://localhost:8092}
      - PORT=${PORT:-8092}
      - WORKERS=${WORKERS:-4}
      - APP_WEB_BASE_URL=${APP_WEB_BASE_URL:-http://localhost:80}
    volumes:
      - vabhub_data:/app/data
      - vabhub_logs:/app/logs
    ports:
      - "8092:8092"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - vabhub-internal
    restart: unless-stopped

  # 前端服务：提供用户界面
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - VITE_API_BASE_URL=${VITE_API_BASE_URL:-http://localhost:8092/api}
    container_name: vabhub-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - vabhub-internal
    restart: unless-stopped

volumes:
  vabhub_db_data:
    name: vabhub_db_data
  vabhub_redis_data:
    name: vabhub_redis_data
  vabhub_data:
    name: vabhub_data
  vabhub_logs:
    name: vabhub_logs

networks:
  vabhub-internal:
    driver: bridge
```

### 步骤 4：启动服务

使用 docker-compose 启动所有服务：

```bash
# 启动所有服务（后台运行）
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志（可选）
docker compose logs -f
```

### 步骤 5：访问应用

等待服务启动完成（约 30 秒），然后在浏览器中访问：

- **前端页面**：http://<宿主机 IP>:80
- **后端 API**：http://<宿主机 IP>:8092
- **API 文档**：http://<宿主机 IP>:8092/docs

### 步骤 6：创建初始用户

首次部署后，通过以下方式创建初始用户：

1. 访问 API 文档：http://<宿主机 IP>:8092/docs
2. 找到 `/api/auth/register` 接口
3. 点击 "Try it out" 按钮
4. 填写用户名、邮箱和密码
5. 点击 "Execute" 按钮完成注册

## §2. Docker Compose 详解

### 2.1 核心服务说明

| 服务 | 镜像 | 端口 | 功能 |
|------|------|------|------|
| `db` | `postgres:14-alpine` | 无（内部网络） | PostgreSQL 数据库，存储所有应用数据 |
| `redis` | `redis:7-alpine` | 无（内部网络） | Redis 缓存，提高应用性能 |
| `backend` | 本地构建 | 8092 | 后端服务，处理核心业务逻辑 |
| `frontend` | 本地构建 | 80 | 前端服务，提供用户界面 |

### 2.2 自定义配置选项

#### 2.2.1 自定义端口

如果需要修改服务端口，可以编辑 `docker-compose.yml` 文件中的 `ports` 配置：

```yaml
# 修改前端端口为 8080
frontend:
  ports:
    - "8080:80"

# 修改后端端口为 9000
backend:
  ports:
    - "9000:8092"
```

同时需要修改 `.env.docker` 中的相应环境变量：

```bash
APP_BASE_URL=http://localhost:9000
APP_WEB_BASE_URL=http://localhost:8080
VITE_API_BASE_URL=http://localhost:9000/api
```

#### 2.2.2 自定义挂载路径

如果需要将数据存储在自定义路径，可以修改 `docker-compose.yml` 文件：

```yaml
volumes:
  vabhub_db_data:
    name: vabhub_db_data
    driver: local
    driver_opts:
      o: bind
      type: none
      device: /path/to/your/db/data
  vabhub_data:
    name: vabhub_data
    driver: local
    driver_opts:
      o: bind
      type: none
      device: /path/to/your/app/data
  vabhub_logs:
    name: vabhub_logs
    driver: local
    driver_opts:
      o: bind
      type: none
      device: /path/to/your/app/logs
```

#### 2.2.3 调整资源限制

可以为服务添加资源限制，避免占用过多系统资源：

```yaml
backend:
  # ... 其他配置 ...
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
      reservations:
        cpus: '1.0'
        memory: 2G
```

### 2.3 官方支持说明

**重要提示**：VabHub 官方推荐且唯一维护的部署方式是 **Docker / docker-compose 部署**。其他运行方式（裸机 Python、k8s 等）仅面向开发者/高级用户，暂不提供详细教程和官方支持。

所有 Docker Compose 配置示例与仓库中的 `docker-compose.yml` 文件保持一致。如果未来需要修改 Compose 配置，必须同步更新以下文档：

1. `README.md` - 快速开始部分的 Docker Compose 示例
2. `docs/user/GETTING_STARTED.md` - 详细部署步骤中的 Docker Compose 说明
3. `docs/user/DEPLOY_WITH_DOCKER.md` - 完整部署指南中的 Docker Compose 配置

## §3. 环境变量说明（精简版）

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `SECRET_KEY` | 是 | - | 应用密钥，首次启动会自动生成 |
| `JWT_SECRET_KEY` | 是 | - | JWT 密钥，首次启动会自动生成 |
| `DB_PASSWORD` | 是 | `vabhub_password` | 数据库密码 |
| `TMDB_API_KEY` | 是 | - | TMDB API Key，用于获取影视元数据 |
| `APP_BASE_URL` | 否 | `http://localhost:8092` | 应用基础 URL |
| `PORT` | 否 | `8092` | 后端服务端口 |
| `REDIS_ENABLED` | 否 | `true` | 是否启用 Redis 缓存 |
| `VITE_API_BASE_URL` | 否 | `http://localhost:8092/api` | 前端 API 基础 URL |

完整的环境变量说明请参考 `docs/CONFIG_OVERVIEW.md`。

## §4. 升级与备份

### 升级 VabHub

1. 获取最新代码：
   ```bash
git pull
   ```

2. 重新构建并启动服务：
   ```bash
docker compose pull && docker compose up -d --build
   ```

### 备份数据

重要数据主要存放在以下位置，建议定期备份：

- 数据库：自动创建的 `vabhub_db_data` 卷
- 应用数据：自动创建的 `vabhub_data` 卷

## §5. 常见问题（FAQ）

### Q1: 容器启动失败怎么办？

查看容器日志以获取详细错误信息：

```bash
docker compose logs
```

### Q2: 无法访问 Web 界面怎么办？

1. 检查容器状态：
   ```bash
docker compose ps
   ```

2. 确保端口未被占用：
   ```bash
# Linux/macOS
lsof -i :80
lsof -i :8092
# Windows
netstat -ano | findstr :80
netstat -ano | findstr :8092
   ```

3. 检查防火墙设置，确保端口已开放。

### Q3: 数据库连接失败怎么办？

1. 检查 `DATABASE_URL` 是否正确配置
2. 确保数据库容器正在运行：
   ```bash
docker compose ps db
   ```
3. 检查数据库密码是否与 docker-compose.yml 中一致

### Q4: 时区/时间不对怎么办？

在 `docker-compose.yml` 中为容器添加时区配置：

```yaml
environment:
  - TZ=Asia/Shanghai
volumes:
  - /etc/localtime:/etc/localtime:ro
```

### Q5: 第一次构建时间较长怎么办？

第一次构建需要拉取基础镜像和安装依赖，时间较长是正常现象。后续构建会利用 Docker 缓存，速度会明显加快。

### Q6: Docker Desktop 连接失败怎么办？

如果遇到 `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified` 错误：

1. 确保 Docker Desktop 已启动
2. 重启 Docker Desktop 服务
3. 检查 Docker 上下文是否正确：
   ```bash
docker context ls
docker context use desktop-linux
   ```

### Q7: 如何创建初始用户？

首次启动后，可通过以下方式创建初始用户：

1. 访问 API 文档：http://localhost:8092/docs
2. 找到 `/api/auth/register` 接口
3. 填写用户名、邮箱、密码进行注册

### Q8: 如何更新 VabHub 版本？

1. 拉取最新代码：
   ```bash
git pull
   ```

2. 重新构建并启动服务：
   ```bash
docker compose pull && docker compose up -d --build
   ```

## §6. 与其它文档的关系

- **功能使用**：请参考 `docs/GETTING_STARTED.md` 和 `docs/VABHUB_SYSTEM_OVERVIEW.md`
- **配置详解**：请参考 `docs/CONFIG_OVERVIEW.md`
- **健康检查**：请参考 `docs/SYSTEM_SELF_CHECK_GUIDE.md`
- **已知限制**：请参考 `docs/KNOWN_LIMITATIONS.md`

## §7. 开发者提示

如果您是开发者，想了解本地开发环境的搭建，请参考 `docs/DEVELOPER_GUIDE.md`（内部文档）。

## §8. 官方支持

如果您在 Docker 部署过程中遇到问题，可以通过以下方式获取支持：

- 查看项目文档
- 在 GitHub Issues 中提交问题
- 加入社区讨论

---

感谢您选择 VabHub！
