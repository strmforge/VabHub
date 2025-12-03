# VabHub 文档中心

> 个人 NAS 媒体管理中心

## 快速入门 🚀

| 文档 | 说明 | 适用人群 |
|------|------|----------|
| [Docker 部署指南](./DOCKER_DEPLOYMENT.md) | Docker Compose 一键部署 | **所有用户** |
| [Demo 模式](./DEMO_MODE_OVERVIEW.md) | 无需外部依赖快速体验 | 新用户 |
| [安装指南](./INSTALL_GUIDE.md) | 详细安装配置说明 | 进阶用户 |

## 功能模块 📚

### 核心功能

| 文档 | 说明 |
|------|------|
| [首页仪表盘](./HOME_DASHBOARD_OVERVIEW.md) | 首页总览功能说明 |
| [任务中心](./TASK_CENTER_OVERVIEW.md) | 下载/同步任务管理 |
| [系统控制台](./ADMIN_DASHBOARD_OVERVIEW.md) | 系统管理与监控 |
| [阅读中心](./READING_CENTER_OVERVIEW.md) | 小说/漫画阅读 |

### 媒体模块

| 文档 | 说明 |
|------|------|
| [小说 TTS](./NOVEL_TTS_MODULE_OVERVIEW.md) | 小说语音合成 |
| [音乐中心](./MUSIC_MODULE_OVERVIEW.md) | 音乐管理与播放 |
| [全局搜索](./GLOBAL_SEARCH_OVERVIEW.md) | 跨模块搜索功能 |

## 插件开发 🧩

| 文档 | 说明 | 适用人群 |
|------|------|----------|
| [Plugin SDK 开发指南](./PLUGIN_SDK_OVERVIEW.md) | SDK + EventBus 插件开发 | **插件开发者** |
| [Plugin Hub 使用指南](./PLUGIN_HUB_OVERVIEW.md) | 插件市场与安装 | 用户/开发者 |
| [DEV SDK 架构](./DEV_SDK_OVERVIEW.md) | 插件系统总体架构 | 开发者 |
| [Hello Plugin 教程](./DEV_SDK_QUICKSTART_HELLO_PLUGIN.md) | 快速入门教程 | 插件开发者 |

## 运维指南 🔧

| 文档 | 说明 | 适用人群 |
|------|------|----------|
| [运行监控 & 故障自检](./OPS_MONITORING_OVERVIEW.md) | 系统健康检查与 Runner 状态监控 | 运维 |
| [Runner 配置](./RUNNERS_OVERVIEW.md) | 后台任务调度配置 | 运维/开发 |
| [备份恢复](./BACKUP_AND_RESTORE.md) | 数据备份与恢复 | 运维 |
| [UX 组件指南](./UX_GUIDELINE_OVERVIEW.md) | UI 组件开发规范 | 开发者 |

## 配置文件 ⚙️

| 文件 | 位置 | 说明 |
|------|------|------|
| `.env.example` | 根目录 | 环境变量模板 |
| `docker-compose.yml` | 根目录 | 开发环境 Docker 配置 |
| `docker-compose.prod.yml` | 根目录 | 生产环境 Docker 配置 |

## 目录结构

```
vabhub/
├── backend/           # 后端 FastAPI 应用
│   ├── app/
│   │   ├── api/       # API 路由
│   │   ├── core/      # 核心配置
│   │   ├── models/    # 数据模型
│   │   ├── runners/   # 后台任务
│   │   └── ...
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/          # 前端 Vue3 应用
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── docs/              # 文档
├── docker/            # Docker 配置文件
├── tools/             # 工具脚本
├── docker-compose.yml
└── .env.example
```

## 版本信息

- 当前版本：**v0.9.0**
- API 版本端点：`GET /api/version`

## 获取帮助

- 遇到问题？查看 [Docker 部署指南](./DOCKER_DEPLOYMENT.md#故障排查)
- 想贡献代码？查看 [UX 组件指南](./UX_GUIDELINE_OVERVIEW.md)
