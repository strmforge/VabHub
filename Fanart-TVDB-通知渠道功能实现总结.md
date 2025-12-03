# Fanart、TVDB、多通知渠道功能实现总结

**生成时间**: 2025-01-XX  
**功能范围**: Fanart集成、TVDB集成、多通知渠道增强

---

## 📋 一、功能实现状态检查

### 1.1 Fanart集成

**当前状态**: ⚠️ **配置存在，但实现缺失**

**发现**:
- ✅ 配置项存在：`FANART_ENABLE`, `FANART_LANG`（在`app/core/config.py`中）
- ✅ 系统设置API支持Fanart配置（在`app/api/system_settings.py`中）
- ❌ **没有Fanart API客户端实现**
- ❌ **没有Fanart模块**（`app/modules/fanart/`不存在）
- ❌ **没有集成到媒体识别服务**

**MoviePilot参考**:
- `MoviePilot/MoviePilot-2/app/modules/fanart/__init__.py` - 完整的Fanart模块实现
- 支持电影和电视剧图片获取
- 支持语言优先级选择
- 支持季图片处理

**需要实现**:
1. ✅ Fanart API客户端（`app/modules/fanart/client.py`）
2. ✅ Fanart服务（`app/modules/fanart/service.py`）
3. ✅ 集成到媒体识别服务

### 1.2 TVDB集成

**当前状态**: ⚠️ **部分实现，需要完善**

**发现**:
- ✅ 模型中有`tvdb_id`字段（subscription, media, transfer_history等）
- ✅ API中有`tvdb_id`参数支持
- ❌ **没有TVDB API客户端实现**
- ❌ **没有TVDB模块**（`app/modules/tvdb/`或`app/modules/thetvdb/`不存在）
- ❌ **没有集成到媒体识别服务**

**MoviePilot参考**:
- `MoviePilot/MoviePilot-2/app/modules/thetvdb/tvdb_v4_official.py` - TVDB V4 API客户端
- 支持认证、剧集信息、季信息、集信息等

**需要实现**:
1. ✅ TVDB V4 API客户端（`app/modules/tvdb/client.py`）
2. ✅ TVDB服务（`app/modules/tvdb/service.py`）
3. ✅ 集成到媒体识别服务

### 1.3 多通知渠道增强

**当前状态**: ⚠️ **部分实现，需要添加新渠道**

**发现**:
- ✅ 已实现：Telegram, WeChat
- ✅ 通知渠道管理器存在（`app/modules/notification/channels.py`）
- ❌ **缺失渠道**：Slack, VoceChat, SynologyChat

**MoviePilot参考**:
- `MoviePilot/MoviePilot-2/app/modules/slack/slack.py` - Slack通知实现
- `MoviePilot/MoviePilot-2/app/modules/vocechat/vocechat.py` - VoceChat通知实现
- `MoviePilot/MoviePilot-2/app/modules/synologychat/synologychat.py` - SynologyChat通知实现

**需要实现**:
1. ✅ Slack通知渠道（`app/modules/notification/channels/slack.py`）
2. ✅ VoceChat通知渠道（`app/modules/notification/channels/vocechat.py`）
3. ✅ SynologyChat通知渠道（`app/modules/notification/channels/synologychat.py`）
4. ✅ 更新通知渠道管理器

---

## 📋 二、实施计划

### 2.1 优先级排序

1. **Fanart集成** - 🟡 中优先级（配置已存在，实现缺失）
2. **TVDB集成** - 🟡 中优先级（部分实现，需要完善）
3. **多通知渠道增强** - 🟡 中优先级（已有基础，需要扩展）

### 2.2 实施步骤

#### 第一阶段：Fanart集成（1-2天）

1. **创建Fanart模块结构**
   ```
   app/modules/fanart/
   ├── __init__.py
   ├── client.py      # Fanart API客户端
   └── service.py     # Fanart服务
   ```

2. **实现Fanart API客户端**
   - 支持电影图片获取（通过TMDB ID）
   - 支持电视剧图片获取（通过TVDB ID）
   - 支持语言优先级选择
   - 支持图片类型过滤（poster, fanart, banner等）

3. **集成到媒体识别服务**
   - 在媒体识别时调用Fanart获取图片
   - 仅在`FANART_ENABLE=True`时启用

#### 第二阶段：TVDB集成（2-3天）

1. **创建TVDB模块结构**
   ```
   app/modules/tvdb/
   ├── __init__.py
   ├── client.py      # TVDB V4 API客户端
   └── service.py     # TVDB服务
   ```

2. **实现TVDB V4 API客户端**
   - 支持认证（API Key + PIN）
   - 支持剧集信息获取
   - 支持季信息获取
   - 支持集信息获取
   - 支持搜索功能

3. **集成到媒体识别服务**
   - 在识别电视剧时调用TVDB获取元数据
   - 补充TMDB缺失的电视剧信息

#### 第三阶段：多通知渠道增强（2-3天）

1. **实现Slack通知渠道**
   - 支持Webhook方式发送消息
   - 支持Socket Mode（可选）
   - 支持消息格式化

2. **实现VoceChat通知渠道**
   - 支持API方式发送消息
   - 支持频道和用户指定
   - 支持Markdown格式

3. **实现SynologyChat通知渠道**
   - 支持Webhook方式发送消息
   - 支持用户ID指定
   - 支持图片和链接

4. **更新通知渠道管理器**
   - 注册新渠道
   - 更新配置管理

---

## 📋 三、技术细节

### 3.1 Fanart API

**API端点**:
- 电影: `https://webservice.fanart.tv/v3/movies/{tmdb_id}?api_key={api_key}`
- 电视剧: `https://webservice.fanart.tv/v3/tv/{tvdb_id}?api_key={api_key}`

**图片类型**:
- `movieposter`, `movielogo`, `hdmovielogo`, `moviedisc`, `hdmoviedisc`
- `moviebackground`, `moviebanner`, `movieart`, `moviethumb`
- `tvposter`, `tvlogo`, `hdtvlogo`, `clearlogo`, `hdclearart`
- `showbackground`, `tvbanner`, `tvthumb`, `seasonposter`, `seasonbanner`, `seasonthumb`

**语言优先级**:
- 优先使用配置的语言列表（`FANART_LANG`）
- 其次使用中文（zh）
- 再次使用英文（en）
- 最后使用likes最多的图片

### 3.2 TVDB V4 API

**认证**:
- 端点: `https://api4.thetvdb.com/v4/login`
- 方法: POST
- 参数: `{"apikey": "...", "pin": "..."}`
- 返回: `{"data": {"token": "..."}}`

**主要端点**:
- 搜索: `GET /v4/search?query={query}`
- 剧集信息: `GET /v4/series/{id}`
- 剧集扩展信息: `GET /v4/series/{id}/extended`
- 季信息: `GET /v4/series/{id}/seasons`
- 集信息: `GET /v4/series/{id}/episodes`

### 3.3 通知渠道API

**Slack**:
- Webhook: `https://hooks.slack.com/services/{webhook_url}`
- 或使用Socket Mode（需要OAuth Token和App Token）

**VoceChat**:
- API: `POST {host}/api/bot`
- Headers: `x-api-key: {api_key}`
- Body: Markdown格式消息

**SynologyChat**:
- Webhook: `POST {webhook_url}`
- Body: `text={message}&file_url={image_url}&user_ids={user_ids}`

---

## 📋 四、配置项

### 4.1 Fanart配置

```python
# app/core/config.py
FANART_ENABLE: bool = False  # 是否启用Fanart
FANART_LANG: str = "zh,en"   # 语言优先级（逗号分隔）
FANART_API_KEY: Optional[str] = None  # Fanart API密钥
```

### 4.2 TVDB配置

```python
# app/core/config.py
TVDB_ENABLE: bool = False  # 是否启用TVDB
TVDB_API_KEY: Optional[str] = None  # TVDB API密钥
TVDB_PIN: Optional[str] = None  # TVDB PIN（可选）
```

### 4.3 通知渠道配置

```python
# 通过通知服务配置
SLACK_WEBHOOK_URL: Optional[str] = None
SLACK_OAUTH_TOKEN: Optional[str] = None  # Socket Mode使用
SLACK_APP_TOKEN: Optional[str] = None  # Socket Mode使用

VOCECHAT_HOST: Optional[str] = None
VOCECHAT_API_KEY: Optional[str] = None
VOCECHAT_CHANNEL_ID: Optional[str] = None

SYNOLOGYCHAT_WEBHOOK: Optional[str] = None
SYNOLOGYCHAT_TOKEN: Optional[str] = None
```

---

## 📋 五、总结

### 5.1 当前状态

- ✅ **Fanart**: 配置存在，实现缺失
- ✅ **TVDB**: 部分实现（字段存在），API客户端缺失
- ✅ **通知渠道**: 基础实现存在，需要添加新渠道

### 5.2 实施优先级

1. **Fanart集成** - 中优先级（1-2天）
2. **TVDB集成** - 中优先级（2-3天）
3. **多通知渠道增强** - 中优先级（2-3天）

### 5.3 预计工作量

- **总工作量**: 5-8天
- **代码量**: 约2000-3000行
- **测试工作量**: 1-2天

---

**报告生成时间**: 2025-01-XX  
**报告版本**: 1.0

