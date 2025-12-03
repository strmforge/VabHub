# MusicCenter Phase 2 & 3 - 音乐榜单订阅系统

> **Phase 3 已完成**：完整的 PT 搜索 → 下载 → 导入 → 去重链路

## 概述

MusicCenter 实现了从公共音乐榜单到用户订阅再到自动搜索下载的完整链路：

```
公共榜单 → 用户订阅 → PT 搜索 → 下载 → 导入 → 去重 → 通知
```

## 数据模型

### 核心模型

| 模型 | 说明 | 文件 |
|------|------|------|
| `MusicChartSource` | 榜单数据源（如 Apple Music、网易云） | `backend/app/models/music_chart_source.py` |
| `MusicChart` | 具体榜单（如"华语热歌榜"） | `backend/app/models/music_chart.py` |
| `MusicChartItem` | 榜单中的曲目条目 | `backend/app/models/music_chart_item.py` |
| `UserMusicSubscription` | 用户订阅配置 | `backend/app/models/user_music_subscription.py` |
| `MusicDownloadJob` | 音乐下载任务记录 | `backend/app/models/music_download_job.py` |

### 关系图

```
MusicChartSource (1) ──< MusicChart (N)
                              │
                              ├──< MusicChartItem (N)
                              │
                              └──< UserMusicSubscription (N) ──< MusicDownloadJob (N)
```

## API 端点

### 管理 API（Dev）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/dev/music/charts/sources` | 获取榜单源列表 |
| POST | `/api/dev/music/charts/sources` | 创建榜单源 |
| GET | `/api/dev/music/charts/list` | 获取榜单列表 |
| POST | `/api/dev/music/charts/` | 创建榜单 |
| GET | `/api/dev/music/charts/{id}` | 获取榜单详情 |
| GET | `/api/dev/music/charts/{id}/items` | 获取榜单条目 |
| POST | `/api/dev/music/charts/{id}/sync` | 手动同步榜单 |

### 用户 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/music/subscriptions` | 获取我的订阅列表 |
| POST | `/api/music/subscriptions` | 创建订阅 |
| PUT | `/api/music/subscriptions/{id}` | 更新订阅 |
| DELETE | `/api/music/subscriptions/{id}` | 删除订阅 |
| POST | `/api/music/subscriptions/{id}/pause` | 暂停订阅 |
| POST | `/api/music/subscriptions/{id}/resume` | 恢复订阅 |
| POST | `/api/music/subscriptions/{id}/run_once` | 手动运行一次 |
| GET | `/api/music/subscriptions/jobs` | 获取下载任务列表 |

## Runner 使用

### 榜单同步 Runner

同步所有启用的音乐榜单：

```bash
# 单次运行
python -m app.runners.music_chart_sync

# 只同步指定源
python -m app.runners.music_chart_sync --source-id 1

# 强制同步（忽略间隔）
python -m app.runners.music_chart_sync --force

# 循环模式（每小时）
python -m app.runners.music_chart_sync --loop --loop-interval 3600
```

### 订阅同步 Runner

处理用户订阅，搜索和下载新曲目：

```bash
# 单次运行
python -m app.runners.music_subscription_sync

# 包含暂停的订阅
python -m app.runners.music_subscription_sync --include-paused

# 循环模式（每 30 分钟）
python -m app.runners.music_subscription_sync --loop --loop-interval 1800
```

### 推荐的 Systemd Timer 配置

```ini
# /etc/systemd/system/vabhub-music-chart-sync.timer
[Unit]
Description=VabHub Music Chart Sync Timer

[Timer]
OnCalendar=*:0/60
Persistent=true

[Install]
WantedBy=timers.target
```

```ini
# /etc/systemd/system/vabhub-music-subscription-sync.timer
[Unit]
Description=VabHub Music Subscription Sync Timer

[Timer]
OnCalendar=*:0/30
Persistent=true

[Install]
WantedBy=timers.target
```

## 榜单抓取适配器

### 支持的平台

| 平台 | 抓取器 | 状态 |
|------|--------|------|
| `dummy` | DummyChartFetcher | 测试用，返回模拟数据 |
| `apple_music` | AppleMusicChartFetcher | 需要 developer_token |
| `itunes` | AppleMusicChartFetcher | 同上 |
| `custom_rss` | RSSChartFetcher | 支持任意 RSS 源 |
| `rsshub` | RSSChartFetcher | 支持 RSSHub 输出 |
| `netease` | DummyChartFetcher | 占位，待实现 |
| `qqmusic` | DummyChartFetcher | 占位，待实现 |
| `spotify` | DummyChartFetcher | 占位，待实现 |

### 添加新平台

1. 在 `backend/app/modules/music_charts/` 创建新的抓取器文件
2. 继承 `BaseChartFetcher` 并实现 `fetch_chart_items` 方法
3. 在 `factory.py` 的 `FETCHER_REGISTRY` 中注册

```python
# 示例：netease_fetcher.py
from app.modules.music_charts.base import BaseChartFetcher, ChartFetchResult

class NeteaseChartFetcher(BaseChartFetcher):
    async def fetch_chart_items(self, chart: MusicChart) -> ChartFetchResult:
        # 实现抓取逻辑
        pass
```

## 通知类型

| 类型 | 说明 |
|------|------|
| `MUSIC_CHART_UPDATED` | 榜单有新曲目 |
| `MUSIC_NEW_TRACKS_QUEUED` | 新曲目已加入搜索队列 |
| `MUSIC_NEW_TRACKS_DOWNLOADING` | 新曲目正在下载 |
| `MUSIC_NEW_TRACKS_READY` | 新曲目已就绪 |

## 前端页面

MusicCenter 页面现在包含三个主标签：

1. **我的音乐** - 本地音乐库浏览（专辑/艺术家/曲目）
2. **榜单 & 订阅** - 浏览榜单、管理订阅
3. **音乐任务** - 查看下载任务状态

## 配置示例

### 创建榜单源

```json
POST /api/dev/music/charts/sources
{
  "platform": "apple_music",
  "display_name": "Apple Music",
  "config": {
    "developer_token": "your_token_here",
    "storefront": "cn"
  },
  "is_enabled": true
}
```

### 创建榜单

```json
POST /api/dev/music/charts/
{
  "source_id": 1,
  "chart_key": "top-songs",
  "display_name": "热门歌曲榜",
  "region": "CN",
  "chart_type": "hot",
  "fetch_interval_minutes": 60,
  "max_items": 100
}
```

### 创建订阅

```json
POST /api/music/subscriptions
{
  "chart_id": 1,
  "auto_search": true,
  "auto_download": false,
  "max_new_tracks_per_run": 10,
  "quality_preference": "flac",
  "preferred_sites": "orpheus,redacted"
}
```

## Phase 3 新增功能

### PT 搜索集成

- ✅ `music_indexer_service.py` - 音乐专用 PT 搜索服务
- ✅ 整合 External Indexer，支持多站点搜索
- ✅ 智能关键词构建（艺术家 + 标题 + 专辑）
- ✅ 质量评分系统（格式、比特率、做种数）

### 下载调度

- ✅ `music_download_dispatcher.py` - 下载调度 Runner
- ✅ `music_download_status_sync.py` - 状态同步 Runner
- ✅ 复用现有 DownloadService 和下载器

### 自动导入

- ✅ `music_import_service.py` - 音乐导入服务
- ✅ 使用 mutagen 解析音频元数据
- ✅ 自动创建 Music/MusicFile 记录

### 去重与质量优选

- ✅ 基于艺术家+标题+专辑的曲目匹配
- ✅ 格式优先级：FLAC > APE > WAV > AAC > MP3
- ✅ 自动升级更高质量版本
- ✅ 跳过低质量重复文件

### 多平台抓取器

- ✅ `netease_fetcher.py` - 网易云音乐（需要 NeteaseCloudMusicApi）
- ✅ `spotify_fetcher.py` - Spotify（需要 API 凭据）
- 🔲 `qqmusic_fetcher.py` - QQ 音乐（占位）

### 前端增强

- ✅ 任务状态筛选
- ✅ 详细任务信息展示（站点、做种数、评分）
- ✅ 重试/跳过操作
- ✅ 订阅覆盖统计 API

## Phase 3 Runner 命令

### 下载调度

```bash
# 单次运行
python -m app.runners.music_download_dispatcher

# 指定下载器
python -m app.runners.music_download_dispatcher --client qbittorrent

# 干跑模式（只打印不执行）
python -m app.runners.music_download_dispatcher --dry-run

# 循环模式
python -m app.runners.music_download_dispatcher --loop --loop-interval 300
```

### 状态同步

```bash
# 单次运行
python -m app.runners.music_download_status_sync

# 循环模式
python -m app.runners.music_download_status_sync --loop --loop-interval 300
```

## 推荐的调度配置

```bash
# 每小时同步榜单
0 * * * * python -m app.runners.music_chart_sync

# 每 30 分钟处理订阅
*/30 * * * * python -m app.runners.music_subscription_sync

# 每 5 分钟调度下载
*/5 * * * * python -m app.runners.music_download_dispatcher --limit 20

# 每 5 分钟同步下载状态
*/5 * * * * python -m app.runners.music_download_status_sync --limit 50
```

## 任务状态流转

```
pending → searching → found → submitted → downloading → importing → completed
                   ↘ not_found → failed
                              ↘ skipped_duplicate
```

| 状态 | 说明 |
|------|------|
| `pending` | 等待 PT 搜索 |
| `searching` | 正在搜索 PT |
| `found` | 找到资源，等待下载 |
| `not_found` | 未找到资源 |
| `submitted` | 已提交到下载器 |
| `downloading` | 下载中 |
| `importing` | 导入中 |
| `completed` | 完成（已入库） |
| `failed` | 失败 |
| `skipped_duplicate` | 跳过（本地已有） |

## 待完成功能

- [ ] QQ 音乐抓取器实现
- [ ] 下载完成后自动重命名
- [ ] 更精细的质量偏好配置
- [ ] 批量操作（批量重试/跳过）
