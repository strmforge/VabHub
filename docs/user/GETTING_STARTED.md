# VabHub 新用户上手指南

> 面向会玩 NAS/PT 的玩家，从零到跑通核心流程。

---

## 1. VabHub 是什么？

VabHub 是一个面向 **NAS/PT 玩家** 的本地优先「搜索 · 下载 · 媒体库」自动化中枢：

- **统一管理**：影视、剧集、音乐、小说、漫画、有声书、下载任务、通知、第三方源
- **打通全链路**：PT 站点 → RSSHub → 下载器 → 云盘（115 等） → 本地媒体库 → Telegram Bot
- **本地大脑**：Local Intel 本地智能索引 + HR/HNR 安全决策，不依赖云端
- **AI 辅助**：外部 LLM + 本地 AI 器官，提供订阅助手、故障医生、整理顾问、阅读助手（只读建议，不自动执行）
- **插件生态**：Plugin Hub + 插件中心，可扩展

核心理念：**Local-first、自托管、站点 AI 适配、插件生态**。

---

## 2. 快速跑起来（最小配置）

> ⚠️ **官方部署说明**
> 当前版本 VabHub 官方推荐、也是唯一维护的部署方式是：**Docker / docker-compose 部署**。
> 其他运行方式（裸机 Python、k8s 等）仅面向开发者/高级用户，暂不提供详细教程。

### 2.1 推荐：Docker 部署（官方支持）

#### 详细部署步骤

##### 1. 克隆仓库
```bash
git clone https://github.com/your-username/vabhub.git
cd vabhub
```

##### 2. 准备环境变量

```bash
# 复制环境变量模板
cp .env.docker.example .env.docker
```

**编辑 `.env.docker` 文件，配置必要参数**：

```bash
# 媒体信息服务
TMDB_API_KEY=your-tmdb-key  # 从 https://www.themoviedb.org/ 获取

# 安全密钥（必须修改）
SECRET_KEY=your-strong-random-string  # 建议使用 openssl rand -hex 32 生成
JWT_SECRET_KEY=another-strong-random-string  # 建议使用 openssl rand -hex 32 生成

# 应用配置
APP_BASE_URL=http://localhost:8092  # 后端访问地址
APP_WEB_BASE_URL=http://localhost:80  # 前端访问地址
VITE_API_BASE_URL=http://localhost:8092/api  # 前端调用后端的 API 地址
```

##### 3. 检查 Docker 配置

VabHub 使用 Docker Compose 管理多个服务，核心服务包括：

| 服务 | 功能 | 端口 | 挂载卷 |
|------|------|------|--------|
| `db` | PostgreSQL 数据库 | 无（内部网络） | `vabhub_db_data` |
| `redis` | 缓存服务 | 无（内部网络） | `vabhub_redis_data` |
| `backend` | 后端应用 | 8092 | `vabhub_data`（应用数据）、`vabhub_logs`（日志） |
| `frontend` | 前端应用 | 80 | 无 |

##### 4. 启动服务

```bash
# 启动所有服务（后台运行）
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志（可选）
docker compose logs -f
```

##### 5. 首次访问

服务启动后，通过以下地址访问：

- **前端 UI**：http://localhost:80
- **后端 API**：http://localhost:8092
- **API 文档**：http://localhost:8092/docs

**部署后第一次打开 VabHub**：
1. 访问 API 文档（http://localhost:8092/docs）创建初始用户
2. 用创建的用户登录前端 UI
3. 查看首页 Dashboard 确认系统状态
4. 进入「系统 & 设置」页面配置下载器和站点
5. 进入「站点管理」添加 PT 站点

##### 6. 后续操作

- **停止服务**：`docker compose down`
- **重启服务**：`docker compose restart`
- **更新服务**：`git pull && docker compose up -d --build`

**完整 Docker 部署指南**：请阅读 [DEPLOY_WITH_DOCKER.md](DEPLOY_WITH_DOCKER.md)

### 2.2 本地开发（仅开发者）

> 📝 **开发者专用**
> 以下步骤仅适用于本地开发和调试，不建议普通用户使用。

#### 准备环境

- Python 3.11+ / Node.js 18+
- PostgreSQL 14+（或 SQLite）
- Redis 6+（可选，用于缓存加速）

#### 本地开发启动

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env，至少配置：
# SECRET_KEY=your-random-secret
# JWT_SECRET_KEY=another-random-secret
# DATABASE_URL=sqlite:///./vabhub.db
# TMDB_API_KEY=your-tmdb-key

# 后端
cd backend && python -m app.main
# 默认运行在 http://localhost:8092

# 前端
cd frontend && pnpm install && pnpm run dev
# 默认运行在 http://localhost:5173
```

### 2.4 配置下载器和站点

1. 打开 Web UI → **设置** → 配置至少一个下载器（qBittorrent 等）
2. 打开 **站点管理** → 添加至少一个 PT 站点

> 💡 详细配置说明请参考 [CONFIG_OVERVIEW.md](CONFIG_OVERVIEW.md)

---

## 3. 第一次登录建议你点什么？

按左侧导航分组，推荐的上手路径：

### 📺 影视中心
- 点开 **电视墙**，看媒体库是否正常展示
- 如果配置了 115 云盘，试试远程播放
- **短剧工作台** 用于短剧内容管理
- 电视墙播放策略（局域网/外网/115）详见 [TV_WALL_PLAYBACK_OVERVIEW.md](TV_WALL_PLAYBACK_OVERVIEW.md)

### ⬇️ 下载 & 订阅
- 进入 **搜索**，试一次多站点聚合搜索
- 添加一个简单的 **订阅**（如某部电视剧）
- 看看 **下载中心** 的任务状态
- 如果你想理解从"想看某片子"到"电视墙里能点开播放"中间到底发生了什么，请参考 [DOWNLOAD_MEDIA_PIPELINE_OVERVIEW.md](DOWNLOAD_MEDIA_PIPELINE_OVERVIEW.md)
- 想了解订阅 / 规则 / RSSHub / 工作流模块如何配合，请参考 [SUBS_RULES_OVERVIEW.md](SUBS_RULES_OVERVIEW.md)

### 📚 阅读 & 听书
- 把一个 TXT 小说导入 **小说中心**
- 转换成 EBook，再用 TTS 生成有声书
- 在 **有声书中心** 听一章
- 想了解小说/有声书/漫画/书架/AI 阅读助手的完整关系，请参考 [READING_STACK_OVERVIEW.md](READING_STACK_OVERVIEW.md)

### 📖 漫画中心
- 进入 **源管理**，配好一个第三方源（Komga/Kavita/OPDS）
- 打开 **漫画库**，浏览和追更
- 漫画追更与通知机制详见 [READING_STACK_OVERVIEW.md](READING_STACK_OVERVIEW.md)

### 🎵 音乐中心
- 体验 **音乐榜单** 和 **音乐订阅**
- 如果配了 RSSHub，可以试试自动循环订阅

### 🤖 AI 中心
- 点开 **AI 故障医生**，看系统诊断报告
- 点开 **AI 阅读助手**，看阅读计划建议
- 所有 AI 输出仅为只读建议，不会自动执行任何操作
- 想了解架构层（Orchestrator/LLM/工具）→ [FUTURE_AI_OVERVIEW.md](FUTURE_AI_OVERVIEW.md)
- 想了解 UI 层（页面/模式/使用路径）→ [AI_CENTER_UI_OVERVIEW.md](AI_CENTER_UI_OVERVIEW.md)

### 🌐 站点 & 插件
- **站点墙** 查看站点状态和做种统计
- **插件中心** 浏览可用插件
- 想深入理解站点管理、Local Intel 和 HR 安全策略如何配合，请参考 [SITE_INTEL_OVERVIEW.md](SITE_INTEL_OVERVIEW.md)

### ⚙️ 系统 & 设置
- **设置** 页面配置下载规则、HR 策略、外部服务
- **通知中心** 查看系统通知
- **日志中心** 排查问题

---

## 4. 如果要用 Telegram / AI / 推荐？

### 4.1 Telegram Bot

```bash
# .env 中添加
TELEGRAM_BOT_TOKEN=your-bot-token   # 从 @BotFather 获取
TELEGRAM_BOT_ENABLED=true
TELEGRAM_BOT_PROXY=http://127.0.0.1:7890  # 国内环境需要代理
```

配置后可通过 Telegram 控制阅读、下载、接收通知。

### 4.2 AI Orchestrator

```bash
# .env 中添加
AI_ORCH_ENABLED=true
AI_ORCH_LLM_ENDPOINT=https://api.openai.com/v1/chat/completions
AI_ORCH_LLM_API_KEY=your-api-key
AI_ORCH_LLM_MODEL=gpt-4o-mini
```

支持 OpenAI / Azure / 硅基流动等 OpenAI 兼容 API。  
未配置时使用 Dummy 模式（仅支持预设场景）。

> 详见 [CONFIG_OVERVIEW.md §3.1](CONFIG_OVERVIEW.md)

### 4.3 深度学习推荐

推荐系统是可选功能，有 GPU 效果更佳，无 GPU 也可运行（CPU 模式）。

```bash
DEEP_LEARNING_ENABLED=true
DEEP_LEARNING_GPU_ENABLED=true  # 无 GPU 时设为 false
```

---

## 5. 常见问题 & 自检入口

### 5.1 快速健康检查

```bash
# 后端服务
curl http://localhost:8092/api/health

# AI 总控状态
curl http://localhost:8092/api/ai/orchestrator/status
```

### 5.2 详细自检

- **5 分钟基础检查**：[SYSTEM_SELF_CHECK_GUIDE.md §1](SYSTEM_SELF_CHECK_GUIDE.md)
- **15 分钟深度检查**：[SYSTEM_SELF_CHECK_GUIDE.md §2](SYSTEM_SELF_CHECK_GUIDE.md)
- **AI 专项检查**：[SYSTEM_SELF_CHECK_GUIDE.md §3](SYSTEM_SELF_CHECK_GUIDE.md)

### 5.3 更多文档

| 文档 | 用途 |
|------|------|
| [VABHUB_SYSTEM_OVERVIEW.md](VABHUB_SYSTEM_OVERVIEW.md) | 系统总览（模块地图） |
| [CONFIG_OVERVIEW.md](CONFIG_OVERVIEW.md) | 配置分组与场景 |
| [FUTURE_AI_OVERVIEW.md](FUTURE_AI_OVERVIEW.md) | AI 架构与模式 |
| [FRONTEND_MAP.md](FRONTEND_MAP.md) | 前端路由结构 |
| [PRE_RELEASE_CHECK_NOTES.md](PRE_RELEASE_CHECK_NOTES.md) | 预发布检查笔记，记录当前版本的检查结果和问题 |
| [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) | 已知限制文档，记录当前版本的限制和暂不处理事项 |

### 5.4 进阶建议

在深入使用 VabHub 之前，建议先阅读：
- [PRE_RELEASE_CHECK_NOTES.md](PRE_RELEASE_CHECK_NOTES.md)：了解当前版本的检查结果和已知问题
- [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md)：了解当前版本的限制和暂不处理事项

---

*最后更新：2025-12-03 PRE-RELEASE-CHECK-1*
