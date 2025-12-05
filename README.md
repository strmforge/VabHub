# VabHub - 本地优先的智能媒体自动化中枢

> 面向 NAS/PT 玩家的「搜索 · 下载 · 媒体库」一体化平台

![Version](https://img.shields.io/badge/version-0.0.1--rc1-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![Vue](https://img.shields.io/badge/vue-3.0+-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

> **当前状态**: VabHub 处于 `0.0.1-rc1` 试用阶段，推荐通过 Docker 部署体验。  
> **官方镜像**:  
> - Docker Hub: `strmforge/vabhub:latest`（推荐）  
> - GHCR: `ghcr.io/strmforge/vabhub:latest`  
> 
> 简要步骤：参考 [`docs/releases/0.0.1-rc1.md`](docs/releases/0.0.1-rc1.md) 与 [`docs/user/DEPLOY_WITH_DOCKER.md`](docs/user/DEPLOY_WITH_DOCKER.md)。

## 🎯 项目简介

VabHub 是面向 **NAS/PT 玩家** 的本地优先媒体自动化中枢，打通 PT 站点 → 下载器 → 云盘 → 媒体库 → 阅读/听书 → 通知的完整链路。

核心理念：**Local-first、自托管、站点 AI 适配**。

## 🌟 核心特色

| 模块 | 特色 |
|------|------|
| 📺 **影视中心** | 电视墙、115 播放、本地 + 云盘统一管理 |
| 📚 **阅读 & 听书** | TXT → EBook → TTS → 有声书，统一进度 |
| 📖 **漫画中心** | 第三方源接入（Komga/Kavita/OPDS）+ 追更通知 |
| 🎵 **音乐订阅** | PT / RSSHub 榜单自动循环订阅 |
| 🧠 **Local Intel** | 本地智能大脑：HR/HNR 决策、站点保护、全站索引 |
| 🤖 **AI 中心** | 5 个 AI 助手（订阅/故障/整理/阅读），只读建议不自动执行 |
| 🔌 **插件生态** | Plugin Hub + 插件中心，可扩展 |

## 🚀 快速开始

### Docker 部署（官方推荐）

VabHub 仅提供 Docker 部署方式的官方支持。

#### 1. 克隆项目
```bash
git clone https://github.com/your-username/vabhub.git
cd vabhub
```

#### 2. 配置环境变量
```bash
cp .env.docker.example .env.docker
# 编辑 .env.docker 文件，配置必要参数
```

#### 3. Docker Compose 配置示例

以下是 VabHub 的核心 Docker Compose 配置，完整配置请参考仓库中的 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  # VabHub 主应用 (All-in-One 单镜像)
  vabhub:
    image: ghcr.io/strmforge/vabhub:latest
    environment:
      - DATABASE_URL=postgresql://vabhub:${DB_PASSWORD}@db:5432/vabhub
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - vabhub_data:/app/data
    ports:
      - "52180:52180"
    depends_on:
      - db
      - redis

  # PostgreSQL 数据库
  db:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: vabhub
      POSTGRES_USER: vabhub
      POSTGRES_PASSWORD: ${DB_PASSWORD}  # ⚠️ 在 .env.docker 中设置
    volumes:
      - vabhub_db_data:/var/lib/postgresql/data

  # Redis 缓存
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - vabhub_redis_data:/data
```

#### 4. 启动服务
```bash
docker compose up -d
```

默认访问地址：
- 前端：http://localhost:80
- 后端：http://localhost:8092
- API 文档：http://localhost:8092/docs

#### 服务说明

| 服务 | 用途 | 端口 | 挂载卷 |
|------|------|------|--------|
| `db` | PostgreSQL 数据库，存储所有应用数据 | 无（内部网络） | `vabhub_db_data` |
| `redis` | Redis 缓存，提高应用性能 | 无（内部网络） | `vabhub_redis_data` |
| `backend` | 后端服务，处理核心业务逻辑 | 8092 | `vabhub_data`（应用数据）、`vabhub_logs`（日志） |
| `frontend` | 前端服务，提供用户界面 | 80 | 无 |

## 📚 文档

- **完整部署指南**：[docs/user/DEPLOY_WITH_DOCKER.md](docs/user/DEPLOY_WITH_DOCKER.md)
- **用户快速上手**：[docs/user/GETTING_STARTED.md](docs/user/GETTING_STARTED.md)
- **系统总览**：[docs/VABHUB_SYSTEM_OVERVIEW.md](docs/VABHUB_SYSTEM_OVERVIEW.md)
- **完整文档索引**：[docs/INDEX.md](docs/INDEX.md)

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issues 和 Pull Requests！

详情请查看 [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)

## 📞 联系方式

- 项目主页：[GitHub Repository](https://github.com/your-username/vabhub)
- 问题反馈：[GitHub Issues](https://github.com/your-username/vabhub/issues)

---

**让我们一起努力，打造更好的智能媒体管理平台！** 🚀