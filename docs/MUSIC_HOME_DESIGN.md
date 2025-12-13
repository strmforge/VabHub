# 音乐首页设计文档

> 本文件记录音乐首页的榜单来源、与其他模块的关系和后续扩展方向。
> 创建于 0.0.3 DISCOVER-MUSIC-HOME

---

## 1. 当前音乐榜单来源

### 1.1 RSSHub 榜单

| 榜单 | RSSHub 路由 | 状态 |
|------|-------------|------|
| 网易云热歌榜 | `/netease/playlist/3778678` | 预留 |
| QQ 音乐热歌榜 | `/tencent/qq/...` | 预留 |

### 1.2 本地榜单配置

通过数据库 `music_charts` 表配置的自定义榜单源。

---

## 2. API 响应结构

### 2.1 `/api/music/home` 响应

```json
{
  "sections": [
    {
      "id": "netease_hot",
      "title": "网易云热歌榜",
      "source": "rsshub/netease",
      "items": [...],
      "description": "来自 RSSHub 的网易云音乐热歌榜"
    }
  ],
  "has_rsshub": true,
  "has_local_charts": false,
  "message": null
}
```

### 2.2 `MusicChartItem` 结构

```json
{
  "id": "track_123",
  "title": "歌曲名",
  "artist": "艺术家",
  "album": "专辑名",
  "cover_url": "https://...",
  "rank": 1,
  "external_url": "https://music.163.com/...",
  "source": "netease"
}
```

---

## 3. 与其他模块的关系

### 3.1 与 MUSIC-AUTOLOOP 的差异

| 模块 | 职责 |
|------|------|
| **音乐首页** | 展示榜单/推荐，帮助用户发现新音乐 |
| **MUSIC-AUTOLOOP** | 自动下载订阅的榜单内容 |

### 3.2 与 TG-BOT-MUSIC 的关系

- 音乐首页提供 Web 界面的榜单浏览
- TG-BOT-MUSIC 提供 Telegram 端的交互式音乐控制
- 两者共享底层的音乐库 API

---

## 4. 后续扩展方向

### 4.1 MUSIC-DISCOVER-2 预留

- [ ] 接入更多榜单源（Spotify、Apple Music、Billboard）
- [ ] 支持榜单歌曲一键搜索 PT 资源
- [ ] 与规则中心联动，从榜单创建下载规则

### 4.2 推荐算法

- [ ] 基于用户播放历史的个性化推荐
- [ ] 相似艺术家/专辑推荐

---

## 5. 相关文件

- `backend/app/services/music_discover_service.py` - 音乐榜单聚合服务
- `backend/app/api/music_home.py` - 音乐首页 API
- `frontend/src/pages/MusicCenter.vue` - 音乐中心前端
- `frontend/src/services/api.ts` - `musicHomeApi` 定义

---

## 6. 配置说明

### 6.1 启用 RSSHub 榜单

```env
RSSHUB_ENABLED=true
RSSHUB_BASE_URL=https://rsshub.app
```

### 6.2 空状态处理

当无可用榜单源时，前端显示引导信息：
- "RSSHub 未启用，请在设置中配置 RSSHub 源以获取音乐榜单"
- 提供跳转到设置页的按钮

---

*最后更新：2025-12-13 DISCOVER-MUSIC-HOME-0.0.3*
