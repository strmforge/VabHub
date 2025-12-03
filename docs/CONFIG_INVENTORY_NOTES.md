# VabHub 配置清单盘点（内部笔记）

> 内部开发用笔记，CONFIG-SELF-CHECK-1 阶段产物  
> 更新于 2025-12-02

---

## 1. 配置分组总览

| 分组 | 配置数量 | 必填 | 建议 | 可选 |
|------|----------|------|------|------|
| Core & Database | 15 | 3 | 5 | 7 |
| 下载 & 存储 & 路径 | 18 | 0 | 3 | 15 |
| TTS & 有声书 | 22 | 0 | 0 | 22 |
| 外部 API（TMDB/Fanart/字幕） | 12 | 1 | 3 | 8 |
| 深度学习 & 推荐 | 18 | 0 | 0 | 18 |
| Local Intel & External Indexer | 15 | 0 | 2 | 13 |
| 插件系统 | 12 | 0 | 1 | 11 |
| Telegram & 通知 | 9 | 0 | 2 | 7 |
| AI Orchestrator | 8 | 0 | 2 | 6 |
| 其它 / 高级 / 开发 | ~20 | 0 | 2 | ~18 |

---

## 2. 分组详细清单

### 2.1 Core & Database

| 变量名 | 用途 | 必填 | 默认值 |
|--------|------|------|--------|
| `SECRET_KEY` | 应用密钥 | ✅ | 需修改 |
| `JWT_SECRET_KEY` | JWT 密钥 | ✅ | 需修改 |
| `DATABASE_URL` | 数据库连接 | ✅ | sqlite:///./vabhub.db |
| `APP_BASE_URL` | 后端基础 URL | 建议 | http://localhost:8080 |
| `APP_WEB_BASE_URL` | 前端基础 URL | 建议 | http://localhost:5173 |
| `PORT` | 服务端口 | 建议 | 8092 |
| `REDIS_URL` | Redis 连接 | 建议 | redis://localhost:6379/0 |
| `REDIS_ENABLED` | 启用 Redis | 建议 | true |
| `DEBUG` | 调试模式 | 可选 | true |
| `LOG_LEVEL` | 日志级别 | 可选 | INFO |
| `APP_DEMO_MODE` | Demo 模式 | 可选 | false |
| `WORKERS` | 工作进程数 | 可选 | 4 |
| `DB_WAL_ENABLE` | SQLite WAL | 可选 | true |
| `CORS_ORIGINS` | CORS 白名单 | 可选 | 预设列表 |
| `BIG_MEMORY_MODE` | 大内存模式 | 可选 | false |

### 2.2 下载 & 存储 & 路径

| 变量名 | 用途 | 必填 | 默认值 |
|--------|------|------|--------|
| `STORAGE_PATH` | 数据存储路径 | 建议 | ./data |
| `TEMP_PATH` | 临时文件路径 | 建议 | ./tmp |
| `MOVIE_LIBRARY_ROOT` | 电影库路径 | 建议 | ./data/library/movies |
| `TV_LIBRARY_ROOT` | 电视剧库路径 | 可选 | ./data/library/tv |
| `ANIME_LIBRARY_ROOT` | 动漫库路径 | 可选 | ./data/library/anime |
| `COMIC_LIBRARY_ROOT` | 漫画库路径 | 可选 | ./data/library/comics |
| `MUSIC_LIBRARY_ROOT` | 音乐库路径 | 可选 | ./data/library/music |
| `SHORT_DRAMA_LIBRARY_ROOT` | 短剧库路径 | 可选 | None |
| `EBOOK_LIBRARY_ROOT` | 电子书库路径 | 可选 | ./data/ebooks |
| `NOVEL_UPLOAD_ROOT` | 小说上传路径 | 可选 | ./data/novel_uploads |
| `INBOX_ROOT` | 收件箱路径 | 可选 | ./data/inbox |
| `INBOX_ENABLE_*` | 收件箱媒体开关 | 可选 | 视类型 |
| `TORRENT_TAG` | 种子标签 | 可选 | VABHUB |
| `MAX_UPLOAD_SIZE` | 上传大小限制 | 可选 | 10GB |

### 2.3 TTS & 有声书

| 变量名 | 用途 | 必填 | 默认值 |
|--------|------|------|--------|
| `SMART_TTS_ENABLED` | 启用 TTS | 可选 | false |
| `SMART_TTS_PROVIDER` | TTS 提供商 | 可选 | dummy |
| `SMART_TTS_OUTPUT_ROOT` | TTS 输出路径 | 可选 | ./data/tts_output |
| `SMART_TTS_HTTP_*` | HTTP TTS 配置 | 可选 | 视具体项 |
| `SMART_TTS_STORAGE_*` | 存储阈值/清理 | 可选 | 视具体项 |
| `SMART_TTS_RATE_LIMIT_*` | TTS 限流 | 可选 | 视具体项 |
| `SMART_TTS_JOB_RUNNER_*` | Job Runner | 可选 | 视具体项 |

### 2.4 外部 API

| 变量名 | 用途 | 必填 | 默认值 |
|--------|------|------|--------|
| `TMDB_API_KEY` | TMDB API Key | ✅ | 空 |
| `TMDB_API_DOMAIN` | TMDB 域名 | 建议 | api.themoviedb.org |
| `TMDB_IMAGE_DOMAIN` | TMDB 图片域名 | 建议 | image.tmdb.org |
| `TMDB_LOCALE` | TMDB 语言 | 建议 | zh |
| `TVDB_V4_API_KEY` | TVDB API Key | 可选 | 内置默认 |
| `FANART_API_KEY` | Fanart API Key | 可选 | 内置默认 |
| `FANART_ENABLE` | 启用 Fanart | 可选 | false |
| `OPENSUBTITLES_*` | 字幕 API 配置 | 可选 | 空 |
| `OCR_HOST` | OCR 服务地址 | 可选 | movie-pilot.org |

### 2.5 深度学习 & 推荐

| 变量名 | 用途 | 必填 | 默认值 |
|--------|------|------|--------|
| `DEEP_LEARNING_ENABLED` | 启用深度学习 | 可选 | true |
| `DEEP_LEARNING_GPU_ENABLED` | 启用 GPU | 可选 | true |
| `DEEP_LEARNING_MODEL_TYPE` | 模型类型 | 可选 | ncf |
| `DEEP_LEARNING_MODEL_PATH` | 模型路径 | 可选 | ./models/deep_learning |
| `REALTIME_RECOMMENDATION_ENABLED` | 实时推荐 | 可选 | true |
| `AB_TESTING_ENABLED` | A/B 测试 | 可选 | true |
| 其它超参数 | 神经网络配置 | 可选 | 预设值 |

### 2.6 Local Intel & External Indexer

| 变量名 | 用途 | 必填 | 默认值 |
|--------|------|------|--------|
| `INTEL_ENABLED` | 启用 Intel | 建议 | true |
| `INTEL_MODE` | Intel 模式 | 建议 | local |
| `INTEL_HR_GUARD_ENABLED` | HR 保护 | 可选 | true |
| `INTEL_SITE_GUARD_ENABLED` | 站点防风控 | 可选 | true |
| `EXTERNAL_INDEXER_ENABLED` | 外部索引 | 可选 | false |
| `EXTERNAL_INDEXER_MODULE` | 索引模块 | 可选 | None |
| `AI_ADAPTER_ENABLED` | AI 站点适配 | 可选 | true |
| `AI_ADAPTER_ENDPOINT` | 适配 API | 可选 | 官方端点 |

### 2.7 插件系统

| 变量名 | 用途 | 必填 | 默认值 |
|--------|------|------|--------|
| `APP_PLUGINS_DIR` | 插件目录 | 建议 | plugins |
| `APP_PLUGINS_AUTO_SCAN` | 自动扫描 | 可选 | true |
| `APP_PLUGINS_AUTO_LOAD` | 自动加载 | 可选 | true |
| `APP_PLUGIN_HUB_URL` | 插件市场 URL | 可选 | 官方仓库 |
| `APP_PLUGIN_COMMUNITY_*` | 社区插件开关 | 可选 | true |
| `PLUGIN_AUTO_RELOAD` | 热重载 | 可选 | false |
| `PLUGIN_REMOTE_INSTALL_ENABLED` | 远程安装 | 可选 | false |

### 2.8 Telegram & 通知

| 变量名 | 用途 | 必填 | 默认值 |
|--------|------|------|--------|
| `TELEGRAM_BOT_TOKEN` | Bot Token | 建议* | 空 |
| `TELEGRAM_BOT_ENABLED` | 启用 Bot | 建议 | false |
| `TELEGRAM_BOT_WEBHOOK_URL` | Webhook URL | 可选 | 空 |
| `TELEGRAM_BOT_PROXY` | Bot 代理 | 可选 | 空 |
| `TELEGRAM_BOT_ALLOWED_USERS` | 用户白名单 | 可选 | 空 |
| `NOTIFY_TELEGRAM_DOWNLOAD_*` | 通知开关 | 可选 | 视类型 |

> *如启用 Bot 则必填

### 2.9 AI Orchestrator

| 变量名 | 用途 | 必填 | 默认值 |
|--------|------|------|--------|
| `AI_ORCH_ENABLED` | 启用 AI 总控 | 建议 | false |
| `AI_ORCH_LLM_PROVIDER` | LLM 提供者 | 可选 | http |
| `AI_ORCH_LLM_ENDPOINT` | LLM API 地址 | 建议* | 空 |
| `AI_ORCH_LLM_API_KEY` | LLM API Key | 建议* | 空 |
| `AI_ORCH_LLM_MODEL` | LLM 模型名 | 建议* | 空 |
| `AI_ORCH_LLM_TIMEOUT` | 请求超时 | 可选 | 30 |
| `AI_ORCH_LLM_MAX_TOKENS` | 最大 Token | 可选 | 2048 |
| `AI_ORCH_DEBUG_LOG` | 调试日志 | 可选 | false |

> *如启用 AI 总控且需完整 LLM 能力则建议配置

### 2.10 其它 / 高级

| 变量名 | 用途 | 必填 | 默认值 |
|--------|------|------|--------|
| `PROXY_HOST` | HTTP 代理 | 可选 | 空 |
| `GITHUB_PROXY` | GitHub 代理 | 可选 | 空 |
| `DOH_ENABLE` | DNS over HTTPS | 可选 | false |
| `VABHUB_AUTO_UPDATE` | 自动更新 | 可选 | false |
| `AUTO_UPDATE_RESOURCE` | 更新站点资源 | 可选 | true |
| `BACKUP_*` | 备份配置 | 可选 | 预设值 |
| `LOG_*` | 日志配置 | 可选 | 预设值 |
| `ENCODING_DETECTION_PERFORMANCE_MODE` | 编码检测 | 可选 | true |

---

## 3. .env.example 与 config.py 对照

### 已同步（配置项一致）
- Core & Database ✅
- 存储路径 ✅
- TTS 配置 ✅
- 外部 API ✅
- 深度学习 ✅
- Intel 配置 ✅
- Telegram & 通知 ✅
- AI Orchestrator ✅

### 需关注
- `RSSHUB_ENABLED` / `RSSHUB_BASE_URL` - .env.example 有，config.py 有
- `SMART_EBOOK_METADATA_*` - config.py 有，.env.example 缺失（可选功能）
- `VABHUB_TORRENT_LABELS` - config.py 有，.env.example 缺失

### 潜在冗余（仅记录，不在本任务处理）
- `LOG_BACKUP_COUNT` 在 config.py 中定义了两次（字符串和整数）

---

## 4. 配置优先级说明

1. **环境变量** > `.env` 文件 > `config.py` 默认值
2. **敏感信息**（API Key、Secret）优先从 `SecretManager` 加密存储读取
3. **动态密钥**（SECRET_KEY、JWT_SECRET_KEY、API_TOKEN）首次启动自动生成

---

*此文件为内部开发笔记，正式用户文档请参考 `CONFIG_OVERVIEW.md`*
