# VabHub - 本地优先的智能媒体自动化中枢

> 面向 NAS/PT 玩家的「搜索 · 下载 · 媒体库」一体化平台

![Version](https://img.shields.io/badge/version-0.1.0--rc1-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![Vue](https://img.shields.io/badge/vue-3.0+-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-strmforge%2Fvabhub-blue?logo=docker)](https://hub.docker.com/r/strmforge/vabhub)

> **当前状态**: VabHub 处于 `0.1.0-rc1` 试用阶段，推荐通过 Docker 部署体验。  
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
git clone https://github.com/strmforge/vabhub.git
cd vabhub
```

#### 2. 配置环境变量
```bash
cp .env.docker.example .env.docker
# 编辑 .env.docker，仅需修改 DB_PASSWORD
```

#### 3. 修改挂载路径

编辑 `docker-compose.yml`，将 `/volume1/...` 改为你的实际路径：

```yaml
services:
  vabhub:
    image: strmforge/vabhub:latest
    volumes:
      # 应用数据 + 自动生成的密钥
      - /your/path/vabhub/app-data:/app/data
      # 媒体库根目录
      - /your/path/media:/media
      # 下载目录
      - /your/path/downloads:/downloads
    ports:
      - "52180:52180"
```

#### 4. 启动服务
```bash
docker compose up -d
```

#### 5. 首次登录

默认访问地址：http://localhost:52180

初始管理员账号：
- 如果设置了 `SUPERUSER_PASSWORD`，使用 `admin` + 你设置的密码登录
- 如果未设置，查看容器日志获取自动生成的密码：
  ```bash
  docker logs vabhub | grep "初始管理员"
  ```

#### 服务说明

| 服务 | 用途 | 端口 |
|------|------|------|
| `vabhub` | VabHub 主应用（前后端合一） | 52180 |
| `db` | PostgreSQL 数据库 | 无（内部网络） |
| `redis` | Redis 缓存 | 无（内部网络） |

## 📚 文档

- **Docker 部署指南**：[docs/user/DEPLOY_WITH_DOCKER.md](docs/user/DEPLOY_WITH_DOCKER.md)
- **新用户上手**：[docs/user/GETTING_STARTED.md](docs/user/GETTING_STARTED.md)
- **系统总览**：[docs/VABHUB_SYSTEM_OVERVIEW.md](docs/VABHUB_SYSTEM_OVERVIEW.md)
- **CI 与发版**：[docs/ci/CI_OVERVIEW.md](docs/ci/CI_OVERVIEW.md)
- **文档索引**：[docs/INDEX.md](docs/INDEX.md)

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issues 和 Pull Requests！

详情请查看 [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)

## 📞 联系方式

- 项目主页：[GitHub Repository](https://github.com/strmforge/vabhub)
- 问题反馈：[GitHub Issues](https://github.com/strmforge/vabhub/issues)

---

**让我们一起努力，打造更好的智能媒体管理平台！** 🚀
