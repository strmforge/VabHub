# DEPLOY_WITH_DOCKER_NOTES.md

## 1. 现有 Docker 相关文件清单

### 1.1 Dockerfile 文件
- `backend/Dockerfile`：后端服务的 Dockerfile
- `frontend/Dockerfile`：前端服务的 Dockerfile
- `services/intel_center/Dockerfile`：intel_center 服务的 Dockerfile（旧，可能不再适用）
- `services/mesh_scheduler/Dockerfile`：mesh_scheduler 服务的 Dockerfile（旧，可能不再适用）

### 1.2 Docker Compose 文件
- `docker-compose.yml`：主 docker-compose 文件，包含完整的服务定义
- `docker-compose.prod.yml`：生产环境 docker-compose 文件

### 1.3 部署相关文档
- `docs/DOCKER_DEPLOYMENT.md`：现有的 Docker 部署文档
- `docs/INSTALL_GUIDE.md`：安装指南
- `docs/manga-source-phase2/DEPLOYMENT.md`：特定模块的部署文档（旧，可能不再适用）

## 2. 文档与配置评估

### 2.1 现有 Docker 配置评估
- 旧版 `docker-compose.yml` 使用端口 8000（后端）和 8080（前端），与当前文档中的端口 8092 不匹配
- 配置文件结构与当前项目结构基本匹配（backend/frontend 分离）
- 环境变量配置与当前 CONFIG_OVERVIEW.md 中的配置项存在差异

### 2.2 现有部署文档评估
- `docs/DOCKER_DEPLOYMENT.md` 可能已过时，需要更新以匹配最新的 Docker 配置
- `docs/INSTALL_GUIDE.md` 可能包含多种安装方式，需要统一为只推荐 Docker

## 3. 复用/废弃/重写决策

### 3.1 复用决策
- 复用 `backend/Dockerfile` 和 `frontend/Dockerfile`，但可能需要更新
- 复用 `docker-compose.yml` 的基本结构，但需要更新端口、环境变量等配置

### 3.2 废弃决策
- 废弃 `services/intel_center/Dockerfile` 和 `services/mesh_scheduler/Dockerfile`，这些服务可能已集成到主应用或不再需要
- 废弃 `docs/manga-source-phase2/DEPLOYMENT.md`，这是特定模块的旧部署文档

### 3.3 重写决策
- 重写 `docs/DOCKER_DEPLOYMENT.md` 为 `docs/DEPLOY_WITH_DOCKER.md`，作为新的官方部署指南
- 更新 `docker-compose.yml` 以匹配当前端口（8092）和环境变量配置
- 创建新的 `.env.docker.example` 文件，与 CONFIG_OVERVIEW.md 中的配置项保持一致

## 4. v1 拓扑决策

### 4.1 容器列表
- `vabhub-db`：PostgreSQL 数据库容器
- `vabhub-redis`：Redis 缓存容器（可选）
- `vabhub-backend`：后端服务容器
- `vabhub-frontend`：前端服务容器

### 4.2 镜像使用
- 数据库和缓存使用官方镜像
- 后端和前端使用本地构建镜像（使用现有 Dockerfile）

### 4.3 卷挂载约定
- `vabhub_db_data`：PostgreSQL 数据目录
- `vabhub_redis_data`：Redis 数据目录
- `vabhub_data`：应用数据目录
- `vabhub_logs`：应用日志目录

### 4.4 端口与网络
- 后端端口：8092（对外暴露）
- 前端端口：80（对外暴露）
- 使用默认 bridge 网络

## 5. 环境变量来源
- 使用 `.env.docker` 文件，基于 `.env.docker.example` 模板
- 所有必填项对齐 CONFIG_OVERVIEW.md 中的 "[required]" 字段

## 6. 后续步骤
1. 更新 `docker-compose.yml` 以匹配当前配置
2. 创建 `.env.docker.example` 文件
3. 编写 `docs/DEPLOY_WITH_DOCKER.md` 官方部署指南
4. 更新 README 和 GETTING_STARTED，统一部署口径
5. 执行 Docker 部署验证
6. 更新已知限制和相关文档

## 7. v2/v3 可能扩展

- 支持外部 Postgres（不随 compose 起 DB）
- 支持 Traefik / Nginx 反向代理示例
- 支持使用预构建镜像而不是本地 build
- 支持 compose profiles 区分"轻量版/完整版"
- 支持多实例/多节点部署指导
- 支持更完善的日志/监控/备份工具集成
- 提供 k8s Helm Chart 支持
- 支持自动更新机制