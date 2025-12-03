# VabHub Telegram Bot 使用指南

## 概述

VabHub Telegram Bot 是 VabHub 系统的 Telegram 机器人，提供以下核心功能：

- 📱 **通知推送**：接收系统通知、下载完成、TTS 生成等消息
- 📊 **状态查询**：查看系统整体运行状态
- ⬇️ **下载管理**：查看当前下载任务进度
- 📖 **阅读进度**：查看小说、有声书、漫画的阅读状态

## 配置步骤

### 1. 创建 Bot

1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/newbot` 创建新机器人
3. 按提示设置机器人名称和用户名
4. 获取 Bot Token（格式：`1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`）

### 2. 配置环境变量

在项目根目录的 `.env` 文件中添加：

```bash
# Telegram Bot 配置
# Bot Token（从 @BotFather 获取）
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
# 是否启用 Telegram Bot (true/false)
TELEGRAM_BOT_ENABLED=true
# 可选：代理地址，例如 http://127.0.0.1:7890
TELEGRAM_BOT_PROXY=
# 可选：白名单，填 Telegram 用户 ID 或用户名，逗号分隔
TELEGRAM_BOT_ALLOWED_USERS=
```

**配置说明：**
- `TELEGRAM_BOT_TOKEN`：必需，从 @BotFather 获取的 Token
- `TELEGRAM_BOT_ENABLED`：必需，设置为 `true` 启用 Bot
- `TELEGRAM_BOT_PROXY`：可选，如果需要通过代理访问 Telegram API
- `TELEGRAM_BOT_ALLOWED_USERS`：可选，限制只有特定用户可以绑定，支持用户 ID 和用户名

### 3. 启动 Bot

在项目根目录运行：

```bash
cd backend
python -m app.runners.telegram_bot_polling
```

Bot 启动后会显示：
```
[telegram-bot] Bot started: @your_bot_username
[telegram-bot] Polling for updates...
```

## 绑定流程

### 1. WebUI 生成绑定码

1. 打开 VabHub WebUI
2. 进入「设置 → 通知渠道 → Telegram」
3. 点击「生成绑定码」获取 6 位验证码

### 2. Telegram 绑定

1. 在 Telegram 中搜索你的 Bot 或点击 Bot 链接
2. 发送 `/start` 查看绑定说明
3. 发送 `/bind 123456`（替换为实际绑定码）
4. 绑定成功后即可使用所有功能

## 可用命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `/start` | 开始使用，显示主菜单 | `/start` |
| `/bind <code>` | 绑定账号 | `/bind 123456` |
| `/status` | 查看系统状态概览 | `/status` |
| `/downloads` | 查看当前下载任务 | `/downloads` |
| `/downloads failed` | 只看失败任务 | `/downloads failed` |
| `/downloads active` | 只看进行中任务 | `/downloads active` |
| `/reading` | 查看最近阅读/听书进度 | `/reading` |
| `/help` | 显示帮助信息 | `/help` |
| `/ping` | 检查 Bot 运行状态 | `/ping` |

### 命令示例

**查看系统状态：**
```
📊 VabHub 状态

下载任务：进行中 2 / 今日完成 5 / 失败 1
TTS 队列：等待 3 / 进行中 1
阅读活跃：小说 4 / 有声书 2 / 漫画 3
插件：启用 7 / 隔离 1
```

**查看下载任务：**
```
📥 当前下载任务（进行中 3 个 / 失败 1 个）

1. [进行中] 某某电影 (45%)
2. [进行中] 某某剧集 S01E03 (80%)
3. [失败] 某某音乐专辑 - 网络错误
```

## 安全建议

### 1. 基础安全
- 不要在公共代码仓库中暴露 Bot Token
- 定期更换 Bot Token（可在 @BotFather 中重新生成）
- 建议设置白名单限制绑定用户

### 2. 白名单配置

如果只有特定用户可以使用，配置白名单：

```bash
# 支持用户 ID 和用户名，逗号分隔
TELEGRAM_BOT_ALLOWED_USERS=123456789,987654321,@username1,username2
```

### 3. 代理使用

如果服务器无法直接访问 Telegram，配置代理：

```bash
# HTTP 代理
TELEGRAM_BOT_PROXY=http://127.0.0.1:7890

# SOCKS5 代理
TELEGRAM_BOT_PROXY=socks5://127.0.0.1:1080
```

## 故障排查

### Bot 没响应
1. 检查 `.env` 中的 `TELEGRAM_BOT_TOKEN` 是否正确
2. 确认 `TELEGRAM_BOT_ENABLED=true`
3. 检查网络连接，必要时配置代理
4. 查看后台日志：`tail -f logs/telegram_bot.log`

### 绑定失败
1. 检查绑定码是否过期（有效期 10 分钟）
2. 确认 WebUI 中已生成正确的绑定码
3. 检查是否在白名单内（如果配置了白名单）

### 命令异常
1. 确认账号已绑定：发送 `/ping` 检查状态
2. 查看后台日志中心获取详细错误信息
3. 重启 Bot 服务：`python -m app.runners.telegram_bot_polling`

### 网络问题
1. **中国大陆用户**：建议配置代理
2. **企业环境**：检查防火墙是否阻止 Telegram API
3. **Docker 部署**：确认容器网络可以访问互联网

## 高级配置

### Docker 部署

在 `docker-compose.yml` 中添加环境变量：

```yaml
services:
  backend:
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_BOT_ENABLED=true
      - TELEGRAM_BOT_PROXY=${TELEGRAM_BOT_PROXY}
      - TELEGRAM_BOT_ALLOWED_USERS=${TELEGRAM_BOT_ALLOWED_USERS}
```

### 日志配置

Bot 日志会输出到 VabHub 主日志中，可以通过日志中心查看：

- WebUI：「系统 → 日志中心」
- 文件：`logs/app.log`
- 过滤：使用 `telegram` 关键词过滤

## 开发说明

### 命令扩展

如需添加新命令：

1. 在 `backend/app/modules/bots/commands/` 目录创建新文件
2. 使用 `@router.command("/command")` 装饰器
3. 实现 `async def cmd_handler(ctx: TelegramUpdateContext)` 函数

### 消息格式

- 支持 Markdown 格式：`*粗体*`、`_斜体_`、`[链接](url)`
- 消息长度限制：4096 字符
- 支持内联按钮和回调查询

## 更新日志

### v1.0.0
- ✅ 基础绑定流程
- ✅ 系统状态查询
- ✅ 下载任务管理
- ✅ 阅读进度查看
- ✅ 白名单安全控制
- ✅ 代理网络支持

---

如有问题，请查看 VabHub 项目文档或提交 Issue。
