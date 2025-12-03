# VabHub - 本地优先的智能媒体自动化中枢

> 面向 NAS/PT 玩家的「搜索 · 下载 · 媒体库」一体化平台

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![Vue](https://img.shields.io/badge/vue-3.0+-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

## 🎯 项目简介

VabHub 是面向 **NAS/PT 玩家** 的本地优先媒体自动化中枢，打通 PT 站点 → 下载器 → 云盘 → 媒体库 → 阅读/听书 → 通知的完整链路。

### 🌟 核心特色

| 模块 | 特色 |
|------|------|
| 📺 **影视中心** | 电视墙、115 播放、本地 + 云盘统一管理 |
| 📚 **阅读 & 听书** | TXT → EBook → TTS → 有声书，统一进度 |
| 📖 **漫画中心** | 第三方源接入（Komga/Kavita/OPDS）+ 追更通知 |
| 🎵 **音乐订阅** | PT / RSSHub 榜单自动循环订阅 |
| 🧠 **Local Intel** | 本地智能大脑：HR/HNR 决策、站点保护、全站索引 |
| 🤖 **AI 中心** | 5 个 AI 助手（订阅/故障/整理/阅读），只读建议不自动执行 |
| 🔌 **插件生态** | Plugin Hub + 插件中心，可扩展 |

对标 MoviePilot，更强调 **Local-first、自托管、站点 AI 适配**。

## 当前内部 RC 版本

- 推荐参考版本：**VabHub 0.1.0-rc1**（内部预发布）
- 适用场景：项目作者、自托管玩家的试用环境 / 功能体验环境
- 详细说明：见 [docs/RELEASE_NOTES_0.1.0-rc1.md](docs/RELEASE_NOTES_0.1.0-rc1.md)

> 📖 **快速上手**：[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)  
> 📋 **系统总览**：[docs/VABHUB_SYSTEM_OVERVIEW.md](docs/VABHUB_SYSTEM_OVERVIEW.md)

## ✨ 核心特性

### 🚀 核心功能
- **🔍 智能搜索系统** - 多站点资源聚合搜索，支持高级筛选和实时进度
- **📺 订阅管理** - 完整的电影/电视剧订阅系统，支持自动下载和洗版
- **⬇️ 下载管理** - 多下载器支持（qBittorrent、Transmission等），实时监控
- **📊 仪表盘** - 系统监控、存储监控、媒体统计、下载状态聚合
- **🔄 工作流系统** - 可视化工作流设计，事件驱动的自动化
- **📅 日历功能** - 订阅发布时间管理，媒体更新提醒
- **🌐 PT站点管理** - CookieCloud同步，站点用户数据追踪
- **🔔 通知系统** - 多渠道通知（微信、邮件、Telegram、Webhook等）

### 🎨 特色功能
- **🎵 音乐管理系统** ⭐ **VabHub独有特色功能**
  - 多平台音乐搜索（Spotify、Apple Music、QQ音乐、网易云等）
  - 音乐榜单（QQ音乐、网易云、TME由你音乐榜、Billboard中国等）
  - 音乐订阅（艺术家、专辑、播放列表订阅）
  - 音乐库管理（扫描、统计、分类）
  - 音乐推荐（基于用户行为的个性化推荐）
  - 播放列表管理
- **🤖 AI增强推荐** - 基于用户行为的个性化推荐
- **☁️ 云存储集成** - 支持115、123、阿里云盘等多云存储
- **🔌 插件系统** - 丰富的插件生态，支持自定义插件开发
- **📱 响应式设计** - 完美适配桌面、平板、移动设备
- **🌍 国际化支持** - 多语言支持，动态语言切换
- **🔐 权限系统** - 基于角色的细粒度权限控制

## 📁 项目结构

```
VabHub/
├── backend/                 # 后端服务（FastAPI）
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心功能
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务服务
│   │   ├── modules/        # 功能模块
│   │   │   ├── search/     # 搜索模块
│   │   │   ├── subscription/ # 订阅模块
│   │   │   ├── download/   # 下载模块
│   │   │   ├── workflow/   # 工作流模块
│   │   │   └── notification/ # 通知模块
│   │   └── plugins/        # 插件系统
│   ├── config/             # 配置文件
│   ├── database/           # 数据库迁移
│   └── main.py             # 应用入口
├── frontend/               # 前端应用（Vue 3）
│   ├── src/
│   │   ├── api/            # API客户端
│   │   ├── components/     # UI组件
│   │   ├── pages/          # 页面
│   │   ├── stores/         # 状态管理
│   │   ├── router/         # 路由配置
│   │   └── utils/          # 工具函数
│   └── package.json
├── docker/                 # Docker配置
├── docs/                   # 项目文档
├── tests/                  # 测试文件
├── requirements.txt        # Python依赖
└── docker-compose.yml      # Docker Compose配置
```

## 🚀 快速开始

### Docker部署（官方推荐）

#### 1. 克隆项目
```bash
git clone https://github.com/your-username/vabhub.git
cd vabhub
```

#### 2. 配置环境变量
```bash
cp .env.docker.example .env.docker
# 编辑.env.docker文件，配置必要参数
```

#### 3. 启动服务
```bash
docker-compose up -d
```

默认访问地址：
- 前端：http://localhost:80
- 后端：http://localhost:8092
- API文档：http://localhost:8092/docs

### 本地开发（仅开发者）

> 📝 **开发者专用**
> 以下步骤仅适用于本地开发和调试，不建议普通用户使用。

#### 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (或 SQLite)
- Redis 6+ (可选，用于缓存)

### 本地开发

#### 1. 克隆项目
```bash
cd VabHub
```

#### 2. 后端设置
```bash
# 安装Python依赖
pip install -r requirements.txt

# 配置环境变量（可选）
cp .env.example .env
# 编辑 .env 文件，配置数据库、Redis等
# 注意：密钥（SECRET_KEY、JWT_SECRET_KEY、API_TOKEN）会在首次启动时自动生成

# 初始化数据库
python backend/manage.py init_db

# 运行结构迁移（建议先 dry-run 再执行）
python backend/scripts/migrate.py --dry-run
python backend/scripts/migrate.py

# 启动后端服务
python backend/main.py
# 首次启动时，系统会自动生成随机密钥并保存到 ./data/.vabhub_secrets.json
```

### 可选依赖开关与运行模式

- `REDIS_ENABLED`：默认为 `true`。若未部署 Redis，可设置为 `false`，系统会自动退化到内存 + 数据库缓存，并只在首次启动时提示 Warning。
- `RSSHUB_ENABLED` / `RSSHUB_BASE_URL`：用于统一控制 RSSHub 功能，当 `RSSHUB_ENABLED=false` 时，相关 API 与 Scheduler 会优雅跳过并返回 “RSSHub 已禁用” 提示。
- **下载器模拟模式**：如果未配置 qBittorrent/Transmission 主机或凭据，后端会自动进入“模拟模式”——创建的下载任务只记录在数据库中，`/api/downloads` 的 `meta.simulation_mode` 会返回 `true`，方便前端提示“当前未连接真实下载器”。如需让 `backend/scripts/test_all.py` 自动跳过需要真实下载器的用例，可设置环境变量 `DOWNLOAD_SIMULATION_MODE=true`。

后端服务默认运行在 `http://localhost:8092`
API文档地址：`http://localhost:8092/docs`

#### 3. 前端设置
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务默认运行在 `http://localhost:5173`

### Docker部署

```bash
# 使用Docker Compose一键启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

**密钥管理**：
- 首次启动时，系统会自动生成随机密钥
- 密钥存储在容器内的 `./data/.vabhub_secrets.json`
- 生产环境建议使用环境变量或Docker secrets设置密钥：
  ```yaml
  # docker-compose.yml
  services:
    vabhub:
      environment:
        - SECRET_KEY=${SECRET_KEY}
        - JWT_SECRET_KEY=${JWT_SECRET_KEY}
        - API_TOKEN=${API_TOKEN}
      volumes:
        - ./data:/app/data  # 持久化密钥文件
  ```

访问地址：
- 前端：http://localhost:5173（开发）或 http://localhost:3000（生产）
- 后端API：http://localhost:8092
- API文档：http://localhost:8092/docs

**详细密钥管理指南请查看：[密钥管理使用指南.md](密钥管理使用指南.md)**

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

前端将运行在 http://localhost:5173

**详细的前端开发指南请查看：[frontend/启动指南.md](frontend/启动指南.md)**

## 📚 文档入口

| 文档 | 用途 |
|------|------|
| [GETTING_STARTED.md](docs/GETTING_STARTED.md) | 新用户上手指南 |
| [VABHUB_SYSTEM_OVERVIEW.md](docs/VABHUB_SYSTEM_OVERVIEW.md) | 系统总览（模块地图） |
| [CONFIG_OVERVIEW.md](docs/CONFIG_OVERVIEW.md) | 配置分组与场景 |
| [SYSTEM_SELF_CHECK_GUIDE.md](docs/SYSTEM_SELF_CHECK_GUIDE.md) | 健康检查与故障排查 |
| [FUTURE_AI_OVERVIEW.md](docs/FUTURE_AI_OVERVIEW.md) | AI 架构与模式 |
| [FRONTEND_MAP.md](docs/FRONTEND_MAP.md) | 前端路由结构 |
| [VABHUB_FEATURE_HISTORY_MAP.md](docs/VABHUB_FEATURE_HISTORY_MAP.md) | 历史功能对照表 |

## 🧑‍💻 贡献指南

- 提交代码/文档前，请阅读 [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md)
- 文档修改后可运行 `npm run md:lint` 检查格式

## 📖 功能模块

### 1. 搜索系统
- 多站点资源聚合搜索
- 高级筛选（类型、质量、大小、日期等）
- 实时搜索进度（SSE）
- 搜索历史记录
- 智能搜索建议

### 2. 订阅管理
- 电影/电视剧订阅
- 订阅规则配置
- 自动下载和洗版
- 订阅状态管理
- 批量操作

### 3. 下载管理
- 多下载器支持
- 实时进度监控
- 批量操作
- 下载历史
- HNR风险检测

### 4. 工作流系统
- 可视化工作流设计
- 事件驱动自动化
- 条件判断
- 工作流模板市场
- 工作流历史

### 5. 仪表盘
- 系统资源监控（CPU/内存/磁盘/网络）
- 存储空间监控
- 媒体统计图表
- 下载器状态聚合
- 调度器状态

### 6. PT站点管理
- 站点CRUD操作
- CookieCloud同步
- 站点用户数据追踪
- 站点统计信息

### 7. 通知系统
- 多渠道通知（微信、邮件、Telegram、Webhook等）
- 通知模板系统
- 通知规则配置

### 8. 日历功能
- 订阅发布时间展示
- 媒体更新提醒
- 自定义事件管理

### 9. 音乐管理系统 ⭐ VabHub独有特色
- **多平台音乐搜索**
  - Spotify、Apple Music、QQ音乐、网易云音乐等
  - 支持歌曲、专辑、艺术家搜索
  - 跨平台搜索结果聚合
- **音乐榜单**
  - QQ音乐排行榜
  - 网易云音乐排行榜
  - TME由你音乐榜
  - Billboard中国榜
  - 实时榜单更新
- **音乐订阅**
  - 艺术家新作品订阅
  - 专辑发布订阅
  - 播放列表订阅
  - 流派订阅
  - 自动下载新发布内容
- **音乐库管理**
  - 本地音乐库扫描
  - 音乐文件元数据识别
  - 音乐库统计（曲目数、艺术家数、专辑数等）
  - 按质量、流派分类统计
- **音乐推荐**
  - 基于用户行为的个性化推荐
  - 协同过滤推荐
  - 内容推荐
  - 混合推荐算法
- **播放列表管理**
  - 创建自定义播放列表
  - 播放列表分享
  - 播放列表导入/导出

## 🔧 配置说明

### 环境变量

创建 `.env` 文件，配置以下变量：

```env
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/vabhub
# 或使用SQLite
# DATABASE_URL=sqlite:///./vabhub.db

# Redis配置（可选）
REDIS_URL=redis://localhost:6379/0

# 安全配置（首次启动时自动生成，无需手动配置）
# SECRET_KEY=your-secret-key-here  # 可选：通过环境变量覆盖
# JWT_SECRET_KEY=your-jwt-secret-key  # 可选：通过环境变量覆盖
# API_TOKEN=your-api-token  # 可选：通过环境变量覆盖
# 
# 注意：系统会在首次启动时自动生成随机密钥，存储在 ./data/.vabhub_secrets.json
# 生产环境建议使用环境变量设置密钥，更安全

# 应用配置
APP_NAME=VabHub
APP_VERSION=1.0.0
DEBUG=True

# 文件存储
STORAGE_PATH=/data/vabhub
```

## 📚 开发指南

### 后端开发

- 使用FastAPI框架
- 遵循RESTful API设计
- 所有API都有自动文档
- 支持异步处理

### 前端开发

- 使用Vue 3 + Composition API
- 采用Vuetify 3 UI框架
- 状态管理使用Pinia
- 路由使用Vue Router
- 提供 `/graphql-explorer`（侧边菜单「GraphQL 实验室」）用于调试 /graphql 查询

### 插件开发

- 插件位于仓库根目录 `plugins/`
- 开发规范详见 `docs/PLUGIN_PDK.md`
- 可在前端“系统 → 插件管理”页面热重载、查看状态并编辑配置

## 🧪 测试

### 常规测试

```bash
# 后端单元测试
pytest backend/tests/

# 前端单元测试
cd frontend
npm run test

# Makefile 汇总
make test
```

### 快速回归（推荐）

在本地或 CI 中启用后端服务后，使用一键脚本即可串联核心链路：

```bash
API_BASE_URL=http://127.0.0.1:8100 python backend/scripts/test_all.py --skip-music-execute

# 同步生成前端“系统自检”可读取的报告
API_BASE_URL=http://127.0.0.1:8100 python backend/scripts/test_all.py \
  --skip-music-execute \
  --report-path reports/test_all-latest.json
```

如需验证真实音乐下载链路，可再执行一次不带 `--skip-music-execute` 的完整命令。

生成报告后，可在前端侧边栏进入「系统自检」页面或调用 `GET /api/system/selfcheck` / GraphQL `systemSelfCheck` 查询，快速了解当前依赖配置、Schema 自愈结果以及最近一次回归的摘要。

## 📝 更新日志

### v1.0.0 (2025-01-XX)
- ✨ 初始版本发布
- ✅ 完整的搜索系统
- ✅ 订阅管理系统
- ✅ 下载管理
- ✅ 工作流系统
- ✅ 仪表盘
- ✅ PT站点管理
- ✅ 通知系统
- ✅ 日历功能

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- 感谢所有贡献者的支持

## 📞 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [GitHub Issues]
- 文档: [项目文档]

---

**让我们一起努力，打造更好的智能媒体管理平台！** 🚀

