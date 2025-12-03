# VabHub 安装指南

> LAUNCH-1 L1-2 实现

## 系统要求

- Docker 20.10+ 或 Docker Compose 2.0+
- 至少 2GB 内存
- 至少 10GB 磁盘空间（根据媒体库大小调整）

## 快速开始

### 1. Docker Compose 部署（推荐）

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  vabhub:
    image: vabhub/vabhub:latest
    container_name: vabhub
    restart: unless-stopped
    ports:
      - "8092:8092"
    volumes:
      # 数据目录
      - ./data:/app/data
      # 媒体库目录（根据实际情况调整）
      - /path/to/novels:/data/novels
      - /path/to/audiobooks:/data/audiobooks
      - /path/to/music:/data/music
      - /path/to/comics:/data/comics
    environment:
      - TZ=Asia/Shanghai
    env_file:
      - .env

  # 可选：Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: vabhub-redis
    restart: unless-stopped
    volumes:
      - ./redis-data:/data
```

### 2. 环境变量配置

创建 `.env` 文件：

```bash
# ==================== 基础配置 ====================
APP_NAME=VabHub
DEBUG=false
LOG_LEVEL=INFO

# ==================== 数据库配置 ====================
# SQLite（默认，适合单机使用）
DATABASE_URL=sqlite:///./data/vabhub.db

# PostgreSQL（可选，适合多实例部署）
# DATABASE_URL=postgresql://vabhub:your_password@localhost:5432/vabhub

# ==================== Redis 配置 ====================
REDIS_ENABLED=true
REDIS_URL=redis://redis:6379/0

# ==================== 存储路径配置 ====================
# 电子书/小说库
EBOOK_LIBRARY_ROOT=/data/novels

# 漫画库
COMIC_LIBRARY_ROOT=/data/comics

# 音乐库
MUSIC_LIBRARY_ROOT=/data/music

# TTS 输出目录
SMART_TTS_OUTPUT_ROOT=/app/data/tts_output

# ==================== TTS 配置（可选） ====================
SMART_TTS_ENABLED=false
SMART_TTS_PROVIDER=edge_tts
# SMART_TTS_DEFAULT_VOICE=zh-CN-XiaoxiaoNeural

# ==================== 外部 API 配置（可选） ====================
# TMDB API Key（用于影视元数据）
# TMDB_API_KEY=your_tmdb_api_key

# ==================== 安全配置 ====================
# 以下密钥会在首次启动时自动生成，无需手动配置
# SECRET_KEY=
# JWT_SECRET_KEY=
# API_TOKEN=
```

### 3. 启动服务

```bash
# 启动
docker-compose up -d

# 查看日志
docker-compose logs -f vabhub

# 停止
docker-compose down
```

### 4. 首次访问

1. 打开浏览器访问 `http://your-nas-ip:8092`
2. 系统会自动进入 Onboarding 向导
3. 按照向导完成：
   - 选择语言和时区
   - 创建管理员账号
   - 配置存储路径
   - 检测外部服务

## NAS 目录结构建议

```
/data/vabhub/
├── novels/           # 小说/电子书
│   ├── 作者名/
│   │   └── 书名.epub
│   └── ...
├── audiobooks/       # 有声书
│   ├── 书名/
│   │   ├── 01.mp3
│   │   └── ...
│   └── ...
├── music/            # 音乐
│   ├── 艺人名/
│   │   └── 专辑名/
│   │       └── 歌曲.flac
│   └── ...
├── comics/           # 漫画
│   ├── 漫画名/
│   │   ├── 第1话/
│   │   │   └── 001.jpg
│   │   └── ...
│   └── ...
└── tts_output/       # TTS 输出（自动生成）
```

## 默认账号

首次启动时，系统会引导创建管理员账号。

如果跳过了 Onboarding，可以使用以下默认账号：
- 用户名：`admin`
- 密码：`admin123`

**重要：请在首次登录后立即修改密码！**

## 常见问题

### Q: 如何更新 VabHub？

```bash
docker-compose pull
docker-compose up -d
```

### Q: 数据库如何备份？

SQLite 数据库文件位于 `./data/vabhub.db`，直接复制即可备份。

也可以使用 API 导出配置和用户数据：
```bash
# 导出配置
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8092/api/admin/backup/config > config_backup.json

# 导出用户数据
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8092/api/admin/backup/user_data > user_data_backup.json
```

### Q: 如何配置 TTS？

1. 在 `.env` 中设置：
   ```bash
   SMART_TTS_ENABLED=true
   SMART_TTS_PROVIDER=edge_tts
   ```
2. 重启服务
3. 在小说详情页点击"生成有声书"

### Q: 如何添加漫画源？

1. 登录管理员账号
2. 进入"系统控制台" → "漫画源配置"
3. 添加漫画源

## 进阶配置

### 使用 PostgreSQL

```bash
# docker-compose.yml 添加 PostgreSQL 服务
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: vabhub
      POSTGRES_PASSWORD: your_password
      POSTGRES_DB: vabhub
    volumes:
      - ./postgres-data:/var/lib/postgresql/data

# .env 修改数据库连接
DATABASE_URL=postgresql://vabhub:your_password@postgres:5432/vabhub
```

### 配置反向代理（Nginx）

```nginx
server {
    listen 80;
    server_name vabhub.example.com;

    location / {
        proxy_pass http://127.0.0.1:8092;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 相关文档

- [Runner 配置指南](./RUNNERS_OVERVIEW.md)
- [备份与恢复](./BACKUP_AND_RESTORE.md)
- [UX 组件指南](./UX_GUIDELINE_OVERVIEW.md)
