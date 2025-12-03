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

### 步骤 3：启动服务

使用 docker-compose 启动所有服务：

```bash
docker compose up -d
```

### 步骤 4：访问应用

等待服务启动完成（约 30 秒），然后在浏览器中访问：

- 前端页面：http://<宿主机 IP>:80
- 后端 API：http://<宿主机 IP>:8092
- API 文档：http://<宿主机 IP>:8092/docs

## §2. 目录与卷说明

| 宿主机路径 | 容器内路径 | 用途 |
|------------|------------|------|
| 自动创建的 Docker 卷 | `/var/lib/postgresql/data` | PostgreSQL 数据库数据 |
| 自动创建的 Docker 卷 | `/data` | Redis 缓存数据 |
| 自动创建的 Docker 卷 | `/app/data` | VabHub 应用数据（媒体库、配置等） |
| 自动创建的 Docker 卷 | `/app/logs` | VabHub 应用日志 |

### 自定义媒体库路径（可选）

如果您希望将媒体库数据存储在自定义路径，可以修改 `docker-compose.yml`，添加自定义卷挂载：

```yaml
volumes:
  - /path/to/your/medias:/app/data
```

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
