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

编辑 `.env.docker` 文件，**仅需修改**：

- `DB_PASSWORD`：数据库密码（必须修改）
- `TMDB_API_KEY`：媒体元数据获取（可选，推荐配置）

> **密钥自动生成**：`SECRET_KEY` 和 `JWT_SECRET_KEY` 无需手动配置，系统会在首次启动时自动生成并持久化到 `/app/data/.vabhub_secrets.json`。

### 步骤 3：Docker Compose 配置

VabHub 使用 Docker Compose 管理所有服务。采用 **All-in-One 单镜像架构**，只需配置一个主应用服务即可：

```yaml
# VabHub Docker Compose 配置 (All-in-One 架构)
# 默认端口: 52180 (避开 8080/7878/8989/9091 等常见下载器端口)
version: '3.8'

services:
  # VabHub 主应用 (前端 + 后端合一)
  vabhub:
    image: strmforge/vabhub:latest  # Docker Hub（推荐）或 ghcr.io/strmforge/vabhub:latest
    container_name: vabhub
    environment:
      - DATABASE_URL=postgresql://${DB_USER:-vabhub}:${DB_PASSWORD}@db:5432/${DB_NAME:-vabhub}  # ⚠️ 在 .env.docker 中设置 DB_PASSWORD
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY:-change-this-in-production}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-change-this-in-production}
      - APP_DEMO_MODE=${APP_DEMO_MODE:-false}
      - APP_BASE_URL=${APP_BASE_URL:-http://localhost:52180}
      - VABHUB_PORT=${VABHUB_PORT:-52180}
      - TZ=Asia/Shanghai
    volumes:
      - vabhub_data:/app/data
      - vabhub_logs:/app/logs
      # Docker Socket - 用于 UI 升级功能 (可选)
      - /var/run/docker.sock:/var/run/docker.sock:ro
    ports:
      - "${VABHUB_PORT:-52180}:${VABHUB_PORT:-52180}"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - vabhub-internal
    restart: unless-stopped

  # PostgreSQL 数据库
  db:
    image: postgres:14-alpine
    container_name: vabhub-db
    environment:
      POSTGRES_DB: ${DB_NAME:-vabhub}
      POSTGRES_USER: ${DB_USER:-vabhub}
      POSTGRES_PASSWORD: ${DB_PASSWORD}  # ⚠️ 必须在 .env.docker 中设置
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

  # Redis 缓存
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

- **应用首页**：http://<宿主机 IP>:52180
- **API 文档**：http://<宿主机 IP>:52180/docs

> 默认端口为 **52180**（避开常见下载器端口），可通过环境变量 `VABHUB_PORT` 修改。

### 步骤 6：初始管理员

VabHub 会在首次启动时自动创建管理员账号：

**方式一：查看容器日志（推荐）**

如果未设置 `SUPERUSER_PASSWORD`，系统会生成随机密码并输出到日志：

```bash
docker logs vabhub | grep "初始管理员"
```

输出示例：
```
🔐 初始管理员账号已创建
   用户名: admin
   密码: xK8mN3pQ2wR5tY7z
⚠️  请尽快登录后修改密码！
```

**方式二：环境变量预设置**

在 `.env.docker` 中添加：

```bash
SUPERUSER_NAME=admin
SUPERUSER_PASSWORD=你的自定义密码
```

然后用设置的用户名和密码登录即可。

## §1.5 使用官方镜像部署（生产环境推荐）

对于生产环境，推荐使用 `docker-compose.prod.yml` 配合官方镜像：

**官方镜像地址（二选一）**：

| Registry | 镜像地址 | 说明 |
|----------|----------|------|
| **Docker Hub** | `strmforge/vabhub:latest` | 推荐普通用户使用，国内访问速度更快 |
| **GHCR** | `ghcr.io/strmforge/vabhub:latest` | 与 GitHub 源码绑定，适合开发者 |

### 步骤 1：配置环境变量

```bash
cp .env.docker.example .env.docker
```

编辑 `.env.docker`，设置镜像版本：

```bash
# 设置要使用的镜像版本
VABHUB_VERSION=0.0.1-rc1
```

### 步骤 2：拉取官方镜像

```bash
# 从 Docker Hub 拉取（推荐）
docker pull strmforge/vabhub:latest

# 或从 GHCR 拉取
docker pull ghcr.io/strmforge/vabhub:latest

# 使用 compose 拉取
docker compose -f docker-compose.prod.yml --env-file .env.docker pull
```

### 步骤 3：启动服务

```bash
docker compose -f docker-compose.prod.yml --env-file .env.docker up -d
```

### 步骤 4：冒烟检查

```bash
# 检查服务状态
docker compose -f docker-compose.prod.yml ps

# 检查健康端点
curl http://localhost:52180/health

# 访问首页
# http://<宿主机 IP>:52180
```

### 升级方式

修改 `.env.docker` 中的 `VABHUB_VERSION`，然后：

```bash
docker compose -f docker-compose.prod.yml --env-file .env.docker pull
docker compose -f docker-compose.prod.yml --env-file .env.docker up -d
```

---

## §2. Docker Compose 详解

### 2.1 核心服务说明

VabHub 采用 **All-in-One 单镜像架构**，前端和后端合并在一个容器中：

| 服务 | 镜像 | 端口 | 功能 |
|------|------|------|------|
| `vabhub` | `ghcr.io/strmforge/vabhub:latest` | 52180:52180 | 主应用（前端 + 后端） |
| `db` | `postgres:14-alpine` | 无（内部网络） | PostgreSQL 数据库 |
| `redis` | `redis:7-alpine` | 无（内部网络） | Redis 缓存 |

### 2.2 端口配置

默认端口 `52180` 是精心选择的"冷门端口"，避开以下常见端口冲突：
- `8080` - 常用 Web 服务
- `7878` - Radarr
- `8989` - Sonarr
- `9091` - Transmission

#### 修改端口

在 `.env.docker` 中设置：

```bash
VABHUB_PORT=3020
APP_BASE_URL=http://localhost:3020
```

端口配置为**内外同步**，容器内监听端口与宿主机映射端口相同。

### 2.3 升级方式

**推荐：UI 一键升级**

在管理界面 > 系统升级页面，点击「立即升级」按钮即可完成升级。

**备选：手动命令**

```bash
docker compose pull && docker compose up -d
```

### 2.4 自定义配置选项

#### 2.4.1 自定义端口

修改 `.env.docker` 中的端口配置：

```bash
# 修改应用端口
VABHUB_PORT=52180

# 修改应用基础 URL
APP_BASE_URL=http://localhost:8080
```

或直接修改 `docker-compose.yml`：

```yaml
vabhub:
  ports:
    - "9000:8000"  # 宿主机端口:容器端口
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

## §3. 环境变量说明

### 必填项

| 变量名 | 说明 |
|--------|------|
| `DB_PASSWORD` | 数据库密码（必须修改，禁止使用默认值） |

### 推荐设置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `SUPERUSER_NAME` | `admin` | 初始管理员用户名 |
| `SUPERUSER_PASSWORD` | 自动生成 | 初始管理员密码，强烈建议设置 |
| `TMDB_API_KEY` | - | 影视元数据获取，不配置影响海报显示 |

### 可选配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `VABHUB_PORT` | `52180` | 应用端口 |
| `APP_BASE_URL` | `http://localhost:52180` | 应用基础 URL |
| `TZ` | `Asia/Shanghai` | 时区 |

### 高级配置（一般无需修改）

| 变量名 | 说明 |
|--------|------|
| `SECRET_KEY` | 应用密钥，**自动生成并持久化** |
| `JWT_SECRET_KEY` | JWT 密钥，**自动生成并持久化** |

> 完整环境变量说明请参考 `docs/admin/CONFIG_OVERVIEW.md`。

## §4. 升级与备份

### 升级 VabHub（推荐：使用预构建镜像）

VabHub 在 CI 通过后会自动构建并推送 Docker 镜像到 GHCR。推荐使用预构建镜像进行升级：

```bash
# 拉取最新镜像
docker compose pull

# 重启服务
docker compose up -d
```

镜像地址（二选一）：
- **Docker Hub**：`strmforge/vabhub:latest`（推荐，访问速度快）
- **GHCR**：`ghcr.io/strmforge/vabhub:latest`（与源码绑定）

### 升级 VabHub（本地构建）

如果需要本地构建（开发/自定义场景）：

1. 获取最新代码：
   ```bash
git pull
   ```

2. 重新构建并启动服务：
   ```bash
docker compose up -d --build
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

### Q7: 如何获取初始管理员密码？

VabHub 在首次启动时自动创建管理员账号：

1. 查看容器日志：`docker logs vabhub | grep "初始管理员"`
2. 或在 `.env.docker` 中设置 `SUPERUSER_PASSWORD` 后重启

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
