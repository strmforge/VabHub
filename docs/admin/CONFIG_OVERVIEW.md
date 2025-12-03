# VabHub 配置总览

> 本文件帮助新用户和新 AI/IDE 快速理解 VabHub 的配置体系。  
> 详细配置说明请以 `backend/app/core/config.py` 和 `.env.example` 为准。

---

## 1. 快速开始

### 1.1 最小配置集（必须配置）

只需配置以下 3 项即可启动 VabHub：

```bash
# .env 文件
SECRET_KEY=your-strong-random-secret-key-here
JWT_SECRET_KEY=another-strong-random-secret-key-here
DATABASE_URL=sqlite:///./vabhub.db  # 或 PostgreSQL 连接串
```

> **提示**：首次启动时，SECRET_KEY 和 JWT_SECRET_KEY 会被 SecretManager 自动替换为随机生成的安全密钥。

### 1.2 建议配置（推荐补充）

```bash
# TMDB API Key（影视元数据必需）
TMDB_API_KEY=your-tmdb-api-key

# 服务地址
APP_BASE_URL=http://localhost:8092
APP_WEB_BASE_URL=http://localhost:5173
PORT=8092

# Redis（缓存加速）
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true
```

---

## 2. 配置分组概览

### 2.1 Core & Database（核心配置）

| 配置项 | 说明 | 必要性 |
|--------|------|--------|
| `SECRET_KEY` | 应用加密密钥 | **必填** |
| `JWT_SECRET_KEY` | JWT 签名密钥 | **必填** |
| `DATABASE_URL` | 数据库连接字符串 | **必填** |
| `REDIS_URL` | Redis 连接地址 | 建议 |
| `PORT` | 后端服务端口 | 建议 |

### 2.2 存储 & 媒体库路径

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `STORAGE_PATH` | 数据存储根目录 | `./data` |
| `MOVIE_LIBRARY_ROOT` | 电影媒体库 | `./data/library/movies` |
| `TV_LIBRARY_ROOT` | 电视剧媒体库 | `./data/library/tv` |
| `EBOOK_LIBRARY_ROOT` | 电子书库 | `./data/ebooks` |
| `INBOX_ROOT` | 收件箱目录 | `./data/inbox` |

> 所有路径都支持绝对路径，如 `/mnt/media/movies` 或 `/115/电影`。

### 2.3 外部 API

| 配置项 | 说明 | 获取方式 |
|--------|------|----------|
| `TMDB_API_KEY` | TMDB 元数据 API | [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api) |
| `FANART_API_KEY` | Fanart 图片 API | 已内置默认 Key |
| `TVDB_V4_API_KEY` | TVDB API | 已内置默认 Key |
| `OPENSUBTITLES_*` | 字幕下载 API | 可选配置 |

### 2.4 下载器 & 站点

下载器配置通过 Web UI 设置界面配置，无需在 `.env` 中手动配置。

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `TORRENT_TAG` | VabHub 种子标签 | `VABHUB` |
| `INTEL_ENABLED` | Local Intel 智能保护 | `true` |
| `INTEL_HR_GUARD_ENABLED` | HR 风险保护 | `true` |

---

## 3. AI & 推荐系统配置

### 3.1 AI Orchestrator（AI 总控）

AI 总控层用于驱动 AI 订阅助手、AI 故障医生、AI 整理顾问、AI 阅读助手等功能。

```bash
# === AI Orchestrator ===
# [optional] 总控开关
AI_ORCH_ENABLED=false

# [recommended] LLM API 配置（启用 AI 功能时建议配置）
AI_ORCH_LLM_ENDPOINT=https://api.openai.com/v1/chat/completions
AI_ORCH_LLM_API_KEY=your-api-key
AI_ORCH_LLM_MODEL=gpt-4o-mini

# [optional] 超时和 Token 限制
AI_ORCH_LLM_TIMEOUT=30
AI_ORCH_LLM_MAX_TOKENS=2048

# [optional] 调试日志
AI_ORCH_DEBUG_LOG=false
```

**支持的 LLM 服务**：
- OpenAI API（gpt-4o, gpt-4o-mini）
- Azure OpenAI
- 硅基流动（qwen-plus, deepseek-chat）
- 任何 OpenAI 兼容 API

**重要说明**：
- 未配置 LLM 时，AI 功能使用 **Dummy 模式**（仅支持预设场景）
- 所有 AI 输出仅为 **只读建议**，不会自动执行任何操作
- 无 GPU 环境不影响 AI Orchestrator 使用

### 3.2 深度学习推荐系统

推荐系统用于个性化媒体推荐，需要 GPU 加速效果更佳。

```bash
# === 深度学习推荐 ===
# [optional] 推荐系统开关
DEEP_LEARNING_ENABLED=true

# [optional] GPU 加速（无 GPU 自动回退 CPU）
DEEP_LEARNING_GPU_ENABLED=true

# [optional] 模型类型：ncf / deepfm / autoencoder
DEEP_LEARNING_MODEL_TYPE=ncf

# [optional] 模型存储路径
DEEP_LEARNING_MODEL_PATH=./models/deep_learning
```

**说明**：
- 无 GPU 环境可正常使用，训练速度较慢
- 推荐系统是可选功能，不影响核心功能

---

## 4. Telegram & 通知配置

### 4.1 Telegram Bot

```bash
# === Telegram Bot ===
# [recommended] 从 @BotFather 获取
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_BOT_ENABLED=true

# [optional] 代理设置
TELEGRAM_BOT_PROXY=http://127.0.0.1:7890

# [optional] 用户白名单（Telegram ID 或用户名，逗号分隔）
TELEGRAM_BOT_ALLOWED_USERS=123456789,username
```

### 4.2 通知推送控制

```bash
# === 通知推送 ===
# [optional] 订阅命中通知
NOTIFY_TELEGRAM_DOWNLOAD_SUBSCRIPTION=false

# [optional] 下载完成通知
NOTIFY_TELEGRAM_DOWNLOAD_COMPLETION=false

# [optional] HR 风险通知（建议开启）
NOTIFY_TELEGRAM_DOWNLOAD_HR_RISK=true
```

---

## 5. 常见配置场景

### 场景 A：最小安装（只用媒体库）

```bash
SECRET_KEY=random-secret
JWT_SECRET_KEY=random-jwt-secret
DATABASE_URL=sqlite:///./vabhub.db
TMDB_API_KEY=your-tmdb-key
```

### 场景 B：启用 Telegram 通知

```bash
# 场景 A 基础上添加
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_BOT_ENABLED=true
NOTIFY_TELEGRAM_DOWNLOAD_HR_RISK=true
```

### 场景 C：启用 AI 订阅助手

```bash
# 场景 B 基础上添加
AI_ORCH_ENABLED=true
AI_ORCH_LLM_ENDPOINT=https://api.openai.com/v1/chat/completions
AI_ORCH_LLM_API_KEY=your-openai-key
AI_ORCH_LLM_MODEL=gpt-4o-mini
```

### 场景 D：完整功能（含推荐系统 + GPU）

```bash
# 场景 C 基础上添加
DEEP_LEARNING_ENABLED=true
DEEP_LEARNING_GPU_ENABLED=true
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379/0
```

---

## 6. 配置文件位置

| 文件 | 用途 |
|------|------|
| `.env` | 用户实际配置（从 .env.example 复制） |
| `.env.example` | 配置模板和说明 |
| `backend/app/core/config.py` | 配置定义和默认值 |

---

## 7. 配置验证

启动后可通过以下方式验证配置：

```bash
# 检查关键配置
cd backend && python -c "
from app.core.config import settings
print('=== 配置检查 ===')
print(f'DATABASE_URL: {settings.DATABASE_URL[:30]}...')
print(f'TMDB_API_KEY: {\"已配置\" if settings.TMDB_API_KEY else \"未配置\"}')
print(f'AI_ORCH_ENABLED: {settings.AI_ORCH_ENABLED}')
print(f'TELEGRAM_BOT_ENABLED: {settings.TELEGRAM_BOT_ENABLED}')
"
```

或访问 API 健康检查端点：

```bash
curl http://localhost:8092/api/health
curl http://localhost:8092/api/ai/orchestrator/status
```

---

## 8. 相关文档

- **系统总览**：`docs/VABHUB_SYSTEM_OVERVIEW.md`
- **自检指南**：`docs/SYSTEM_SELF_CHECK_GUIDE.md`
- **AI 功能概览**：`docs/FUTURE_AI_OVERVIEW.md`
- **前端路由**：`docs/FRONTEND_MAP.md`

---

*最后更新：2025-12-02 CONFIG-SELF-CHECK-1*
