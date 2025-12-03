# 用户通知渠道接入指南

VabHub 支持多种通知渠道，让你在不同平台上接收媒体更新、任务完成等通知。

## 渠道能力对比

| 渠道 | 富文本 | 交互按钮 | 点击跳转 | 适合场景 |
|------|--------|----------|----------|----------|
| **Web 内置** | ✅ | ✅ | ✅ | 日常使用，功能最完整 |
| **Telegram Bot** | ✅ Markdown | ✅ Inline 按钮 | ✅ | 移动端实时推送 |
| **Webhook** | ✅ JSON | ❌（由接收端处理） | ✅ URL | 自动化集成 |
| **Bark** | ❌ 纯文本 | ❌ | ✅ 单 URL | iOS 简洁推送 |

## Web 内置通知

Web 内置通知是默认启用的，无需额外配置。

### 功能
- 页面右上角通知铃铛图标
- 未读通知数量徽章
- 通知列表，支持按类型筛选
- 操作按钮（打开详情、标记已读等）
- 实时轮询更新

### 访问
- 点击页面顶部的 🔔 图标
- 或访问「设置 → 通知中心」

## Telegram Bot

Telegram Bot 是推荐的移动端通知方式，支持丰富的交互功能。

### 配置步骤

1. **绑定账号**
   - 在 VabHub 「设置 → 通知渠道」页面
   - 点击「添加 Telegram」获取绑定码
   - 在 Telegram 中搜索你的 Bot（由管理员部署）
   - 发送 `/start <绑定码>` 完成绑定

2. **验证绑定**
   - 绑定成功后，Bot 会发送确认消息
   - 在渠道管理页面可以看到已绑定状态

### 通知示例

```
*《海贼王》有新章节*

站点: CopyManga
最新: 第 1100 话

🔗 [查看详情](https://...)

[📖 打开漫画] [✅ 标记已读]
```

### 支持的通知类型
- 漫画更新
- 小说新章节
- TTS 有声书就绪
- 音乐新曲目
- 系统告警

详细 Bot 使用指南：[BOT_TELEGRAM_GUIDE.md](./BOT_TELEGRAM_GUIDE.md)

## Webhook

Webhook 适合与第三方服务集成，如企业微信、钉钉、飞书等。

### 配置步骤

1. **添加 Webhook 渠道**
   - 在「设置 → 通知渠道」页面
   - 点击「添加 Webhook」
   - 填写配置：
     - **URL**: 接收通知的 HTTP 端点
     - **方法**: POST（推荐）或 GET
     - **密钥**: 可选，用于验证请求来源
     - **Headers**: 可选，自定义请求头

2. **测试 Webhook**
   - 保存后点击「测试」按钮
   - 检查目标服务是否收到请求

### Payload 格式

VabHub 发送的 Webhook payload 遵循以下标准格式：

```json
{
  "source": "vabhub",
  "event_type": "MANGA_UPDATED",
  "severity": "info",
  "title": "《海贼王》有新章节",
  "message": "站点: CopyManga\n最新: 第 1100 话",
  "media_type": "manga",
  "target_id": 123,
  "time": "2025-11-26T12:34:56Z",
  "web_url": "https://your-vabhub.com/manga/123",
  "actions": [
    {
      "id": "open_manga",
      "label": "打开漫画",
      "type": "open_manga",
      "url": "https://your-vabhub.com/manga/123"
    },
    {
      "id": "mark_read",
      "label": "标记已读",
      "type": "api_call",
      "api_path": "/api/manga/local/series/123/mark_read",
      "api_method": "POST"
    }
  ],
  "raw_payload": { ... }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `source` | string | 固定为 "vabhub" |
| `event_type` | string | 事件类型（见下方列表） |
| `severity` | string | 严重程度：info/warning/error |
| `title` | string | 通知标题 |
| `message` | string | 通知内容 |
| `media_type` | string | 媒体类型：manga/novel/audiobook/music |
| `target_id` | number | 目标资源 ID |
| `time` | string | ISO 8601 时间戳 |
| `web_url` | string | Web 详情页 URL |
| `actions` | array | 可用动作列表 |
| `raw_payload` | object | 原始附加数据 |

### 事件类型

| event_type | 说明 |
|------------|------|
| `MANGA_UPDATED` | 漫画更新 |
| `MANGA_NEW_CHAPTER` | 漫画新章节 |
| `NOVEL_NEW_CHAPTER` | 小说新章节 |
| `AUDIOBOOK_READY` | 有声书就绪 |
| `TTS_JOB_COMPLETED` | TTS 任务完成 |
| `TTS_JOB_FAILED` | TTS 任务失败 |
| `MUSIC_NEW_TRACK` | 音乐新曲目 |
| `SYSTEM_ALERT` | 系统告警 |

### 集成示例

#### 飞书机器人

```python
# 飞书 Webhook 中间件示例
import json
import requests

def vabhub_to_feishu(vabhub_payload):
    """将 VabHub payload 转换为飞书格式"""
    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": vabhub_payload["title"]}
            },
            "elements": [
                {"tag": "div", "text": {"tag": "plain_text", "content": vabhub_payload["message"]}},
                {"tag": "action", "actions": [
                    {"tag": "button", "text": {"tag": "plain_text", "content": "查看详情"}, 
                     "url": vabhub_payload.get("web_url", "")}
                ]}
            ]
        }
    }
```

#### 钉钉机器人

```python
def vabhub_to_dingtalk(vabhub_payload):
    """将 VabHub payload 转换为钉钉格式"""
    return {
        "msgtype": "actionCard",
        "actionCard": {
            "title": vabhub_payload["title"],
            "text": vabhub_payload["message"],
            "singleTitle": "查看详情",
            "singleURL": vabhub_payload.get("web_url", "")
        }
    }
```

## Bark

Bark 是一个简洁的 iOS 推送服务，适合只需要简单通知提醒的场景。

### 配置步骤

1. **安装 Bark App**
   - 在 App Store 搜索「Bark」并安装
   - 打开 App，获取推送地址（形如 `https://api.day.app/YOUR_KEY`）

2. **添加 Bark 渠道**
   - 在「设置 → 通知渠道」页面
   - 点击「添加 Bark」
   - 填写配置：
     - **服务器**: Bark 推送地址（如 `https://api.day.app/YOUR_KEY`）
     - **声音**: 推送提示音（可选）
     - **分组**: 通知分组名称（默认 VabHub）

3. **测试推送**
   - 保存后点击「测试」按钮
   - 检查手机是否收到推送

### 通知效果

由于 Bark 不支持按钮，VabHub 会：
- 将主要动作的 URL 设为点击跳转地址
- 其他动作以文本形式附加在消息末尾

```
《海贼王》有新章节

站点: CopyManga
最新: 第 1100 话

其他操作（请在 Web 端进行）：
• 标记已读
```

点击通知会直接打开漫画详情页。

### 自建 Bark 服务器

如果你有自己的服务器，可以部署私有 Bark 后端：

```bash
docker run -d --name bark -p 8080:8080 finab/bark-server
```

然后将服务器地址设为 `http://your-server:8080/YOUR_DEVICE_KEY`

## 通知偏好设置

在「设置 → 通知偏好」页面，你可以精细控制：

### 按事件类型
- 漫画更新通知
- 小说新章节通知
- 有声书就绪通知
- TTS 任务通知
- 系统告警通知

### 按渠道
- 每种事件类型可单独开关 Web/Telegram/Webhook/Bark

### 静音模式
- 全局静音
- 临时静音（30分钟/1小时/2小时/4小时/今晚）
- 按媒体静音（不再接收某部漫画的更新通知）

## 常见问题

### Q: Telegram 通知没有收到？
1. 检查 Bot 是否已绑定（发送 `/start` 确认）
2. 检查通知偏好中 Telegram 渠道是否启用
3. 检查是否处于静音模式

### Q: Webhook 返回错误？
1. 检查 URL 是否可访问
2. 检查目标服务是否正确处理 JSON payload
3. 查看 VabHub 日志获取详细错误信息

### Q: Bark 点击通知没有跳转？
1. 确保 VabHub 配置了 `FRONTEND_URL` 环境变量
2. 确保手机网络可以访问该 URL

## 相关文档

- [Telegram Bot 使用指南](./BOT_TELEGRAM_GUIDE.md)
- [通知偏好系统概述](./NOTIFY_PREFERENCES_OVERVIEW.md)
- [运维告警渠道配置](./OPS_ALERT_CHANNELS.md)
