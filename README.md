# VabHub - 本地优先的智能媒体自动化中枢

> 面向 NAS/PT 玩家的「搜索 · 下载 · 媒体库」一体化平台

![Version](https://img.shields.io/badge/version-0.1.0--rc1-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![Vue](https://img.shields.io/badge/vue-3.0+-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

## 🎯 项目简介

VabHub 是面向 **NAS/PT 玩家** 的本地优先媒体自动化中枢，打通 PT 站点 → 下载器 → 云盘 → 媒体库 → 阅读/听书 → 通知的完整链路。

对标 MoviePilot，更强调 **Local-first、自托管、站点 AI 适配**。

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

```bash
# 1. 克隆项目
git clone https://github.com/your-username/vabhub.git
cd vabhub

# 2. 配置环境变量
cp .env.docker.example .env.docker
# 编辑 .env.docker 文件，配置必要参数

# 3. 启动服务
docker compose up -d
```

默认访问地址：
- 前端：http://localhost:80
- 后端：http://localhost:8092
- API 文档：http://localhost:8092/docs

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