# VabHub Telegram Bot 使用指南

## 概述

VabHub Telegram Bot 是一个**命令行风格的 VabHub 终端**，让你可以在 Telegram 聊天框中控制系统的大部分功能：

- **账号绑定**: 通过绑定码关联 VabHub 账号
- **通知推送**: 接收漫画更新、下载完成等通知（支持操作按钮）
- **全局搜索**: 直接发送媒体名称搜索，支持媒体类型过滤（电影/漫画/音乐等）
- **订阅管理**: 管理漫画追更、音乐榜单等订阅，支持暂停/恢复/删除
- **下载控制**: 查看下载任务，支持状态过滤、重试/取消/删除
- **阅读中心**: 查看阅读进度，标记完成
- **音乐中心**: 管理音乐榜单订阅
- **运维管理**: 系统健康检查、告警查看、磁盘监控（管理员）
- **交互式菜单**: 通过按钮快速导航各功能模块

> 📚 详细命令参考：[BOT_TELEGRAM_COMMANDS_REFERENCE.md](./BOT_TELEGRAM_COMMANDS_REFERENCE.md)

## 创建 Telegram Bot

### 1. 通过 @BotFather 创建 Bot

1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/newbot`
3. 按提示输入 Bot 名称和用户名
4. 获取 **Bot Token**（格式如 `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`）

示例对话：
```
You: /newbot
BotFather: Alright, a new bot. How are we going to call it?
You: VabHub
BotFather: Good. Now let's choose a username for your bot...
You: VabHubBot
BotFather: Done! Congratulations on your new bot...
         Use this token to access the HTTP API:
         1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 2. 配置 Bot 权限（可选）

发送 `/mybots` → 选择你的 Bot → Bot Settings → Group Privacy → Turn off

这样 Bot 可以接收群组中的所有消息（如果需要群组功能）。

## 配置 VabHub

### 1. 环境变量

在 `.env` 文件中添加：

```env
# Telegram Bot Token（必填）
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# 是否启用 Bot（默认 false）
TELEGRAM_BOT_ENABLED=true
```

### 2. 运行 Bot Polling

#### 方式 1: 直接运行

```bash
cd backend
python -m app.runners.telegram_bot_polling
```

#### 方式 2: 使用 systemd

创建 `/etc/systemd/system/vabhub-telegram-bot.service`:

```ini
[Unit]
Description=VabHub Telegram Bot
After=network.target

[Service]
Type=simple
User=vabhub
WorkingDirectory=/path/to/vabhub/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python -m app.runners.telegram_bot_polling
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl enable vabhub-telegram-bot
sudo systemctl start vabhub-telegram-bot
```

#### 方式 3: Docker Compose

在 `docker-compose.yml` 中添加服务：

```yaml
services:
  telegram-bot:
    build:
      context: ./backend
    command: python -m app.runners.telegram_bot_polling
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_BOT_ENABLED=true
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - db
    restart: unless-stopped
```

## 用户绑定

### 1. 在 Web 界面生成绑定码

1. 登录 VabHub 网页端
2. 进入「设置 → 通知渠道」
3. 在 Telegram 绑定区域点击「获取绑定码」
4. 复制生成的绑定码（10 分钟内有效）

### 2. 在 Telegram 中绑定

向你的 VabHub Bot 发送：

```
/start YOUR_BINDING_CODE
```

绑定成功后会收到确认消息。

## Bot 命令

### 基础命令

| 命令 | 说明 |
|------|------|
| `/start` | 显示欢迎信息和主菜单 |
| `/start <code>` | 使用绑定码绑定账号 |
| `/menu` | 打开交互式主菜单 |
| `/help` | 显示帮助信息 |
| `/ping` | 检查 Bot 状态 |
| `/settings` | 账号设置 |

### 功能命令

| 命令 | 说明 |
|------|------|
| `/search <关键词>` | 搜索影视/漫画/音乐 |
| `/subscriptions` | 管理订阅（漫画追更、音乐榜单） |
| `/downloads` | 查看和控制下载任务 |
| `/reading` | 查看阅读进度 |
| `/recent` | 查看最近活动 |
| `/notify` | 通知偏好设置（开关各类通知、静音） |

### 管理员命令

| 命令 | 说明 |
|------|------|
| `/admin health` | 查看系统健康状态 |
| `/admin runners` | 查看 Runner 状态 |
| `/admin stats` | 查看系统统计 |
| `/admin whoami` | 查看当前用户信息 |

💡 **小技巧**: 直接发送媒体名称即可搜索，无需使用 `/search` 命令！

## 交互式菜单

发送 `/menu` 命令打开主菜单，通过按钮快速导航：

```
📱 VabHub 主菜单

[📚 阅读中心] [📺 影视中心]
[📖 小说/有声书] [📚 漫画中心]
[🎵 音乐中心]
[🔍 搜索] [🧩 订阅管理]
[⬇️ 下载任务] [⚙️ 设置]
```

每个子菜单都有返回按钮，方便快速切换。

## 搜索功能

### 基本搜索

直接发送媒体名称：
```
三体
```

或使用命令：
```
/search 周杰伦
```

### 搜索结果

搜索结果按类型分组展示，每个结果带有操作按钮：

- **📋 详情**: 查看更多信息
- **📌 追更**: 添加漫画追更
- **⬇️ 下载**: 添加到下载队列
- **🌐 网页**: 在浏览器中打开

## 订阅管理

发送 `/subscriptions` 查看所有订阅：

```
🧩 我的订阅

📚 漫画追更 (3)
  ✅ 进击的巨人
  ✅ 海贼王
  ⏸ 火影忍者

🎵 音乐榜单 (2)
  ✅ 网易云热歌榜
  ✅ QQ音乐新歌榜
```

每个订阅可以：
- **暂停/启用**: 临时停止或恢复同步
- **立即执行**: 手动触发一次同步
- **查看详情**: 查看同步状态和时间

## 下载任务

发送 `/downloads` 查看下载队列：

```
⬇️ 下载任务

⏳ [PT] 流浪地球2
🔄 [音乐] 周杰伦新专辑 (45%)
✅ [TTS] 三体有声书
❌ [PT] 某部电影

📊 进行中: 1 | 排队: 1 | 失败: 1

[🔄 刷新] [« 返回主菜单]
```

失败的任务可以点击「重试」或「跳过」。

## 通知类型

绑定成功后，你将自动接收以下通知：

| 类型 | 说明 |
|------|------|
| 漫画更新 | 追更的漫画有新章节 |
| TTS 完成 | 有声书 TTS 任务完成 |
| 音乐就绪 | 订阅的音乐新曲目已下载 |
| 下载完成 | 影视/音乐下载任务完成 |

### 通知操作按钮

通知消息可能带有操作按钮，让你无需打开网页就能快速处理：

```
📚 《进击的巨人》更新了 2 话

漫画有新章节更新，快去看看吧！

[🌐 打开] [✅ 标记已读]
```

支持的操作：
- **🌐 打开**: 在浏览器中打开详情页
- **⬇️ 下载**: 添加到下载队列
- **📌 订阅**: 添加追更/订阅
- **✅ 标记已读**: 将通知标记为已读

## 故障排除

### Bot 无响应

1. 检查 `TELEGRAM_BOT_ENABLED` 是否为 `true`
2. 检查 `TELEGRAM_BOT_TOKEN` 是否正确
3. 查看 Runner 日志：
   ```bash
   journalctl -u vabhub-telegram-bot -f
   ```

### 绑定码无效

- 绑定码有效期为 10 分钟
- 每次只能绑定一个账号
- 重新获取绑定码再试

### 收不到通知

1. 确认已启用 Telegram 通知渠道（在 Web 设置页查看）
2. 确认未 block Bot
3. 检查 Bot 服务是否正常运行

## 安全说明

- 绑定码一次性使用，使用后立即失效
- 每个 Telegram 账号只能绑定一个 VabHub 账号
- 解绑后通知渠道会自动禁用
- Bot 不存储任何敏感信息

## 相关文件

### 后端

**配置 & 客户端：**
- `backend/app/core/config.py` - 配置项 (TELEGRAM_BOT_*)
- `backend/app/modules/bots/telegram_bot_client.py` - Bot API 客户端

**路由 & 上下文（Phase 2）：**
- `backend/app/modules/bots/telegram_context.py` - 上下文对象
- `backend/app/modules/bots/telegram_router.py` - 命令路由器
- `backend/app/modules/bots/telegram_keyboard.py` - 键盘构建器

**命令模块（Phase 2）：**
- `backend/app/modules/bots/commands/basic.py` - 基础命令
- `backend/app/modules/bots/commands/menu.py` - 主菜单
- `backend/app/modules/bots/commands/search.py` - 搜索
- `backend/app/modules/bots/commands/subscriptions.py` - 订阅管理
- `backend/app/modules/bots/commands/downloads.py` - 下载任务
- `backend/app/modules/bots/commands/reading.py` - 阅读进度
- `backend/app/modules/bots/commands/admin.py` - 管理员命令
- `backend/app/modules/bots/commands/notif.py` - 通知回调

**Handler & Runner：**
- `backend/app/modules/bots/telegram_bot_handlers.py` - 消息处理入口
- `backend/app/runners/telegram_bot_polling.py` - Polling Runner

**绑定相关：**
- `backend/app/models/user_telegram_binding.py` - 绑定模型
- `backend/app/services/user_telegram_service.py` - 绑定服务
- `backend/app/api/user_telegram.py` - 绑定 API

**辅助服务（Phase 2）：**
- `backend/app/services/user_subscription_overview_service.py` - 订阅汇总
- `backend/app/services/bot_task_overview_service.py` - 任务汇总

### 前端

- `frontend/src/pages/settings/UserNotifyChannelsPage.vue` - 绑定界面 & Bot 使用说明
