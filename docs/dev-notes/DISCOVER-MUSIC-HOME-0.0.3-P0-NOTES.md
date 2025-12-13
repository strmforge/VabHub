# P0 现状巡检笔记 - DISCOVER-MUSIC-HOME-0.0.3

> 本文件为 0.0.3 任务的 P0 阶段巡检记录，不做任何行为变更，仅供后续 Phase 参考。

## 1. 发现页当前数据源

### 后端 (`backend/app/api/discover.py`)
- **当前仅支持 TMDB**，使用 `settings.TMDB_API_KEY` 获取 key
- Key 来源：优先从加密存储读取，其次从 `TMDB_API_KEY` 环境变量
- 返回结构 `DiscoverHomeResponse`:
  - `tmdb_configured: bool` - 是否配置了 key
  - `tmdb_message: str | None` - 提示信息
  - `sections: List[DiscoverSection]` - 内容区块（本周热门电影/剧集、流行电影/剧集）
- 缓存 TTL: 30 分钟
- **无公共 key 概念**，直接使用用户私有 key

### 前端 (`frontend/src/pages/Discover.vue`)
- 调用 `/api/discover/home` 获取首页热门
- 下方有 TMDB/豆瓣/Bangumi 三个 Tab，但仅为**搜索入口**，不是热门榜单
- 空状态处理：`tmdbConfigured=false` 时显示引导去配置

## 2. 豆瓣/Bangumi 现有能力

### 豆瓣 (`backend/app/api/douban.py`)
- **已有完整 API**：
  - `/douban/search` - 搜索
  - `/douban/hot/movie` - 热门电影
  - `/douban/hot/tv` - 热门电视剧
  - `/douban/top250` - TOP250
- 使用 `DoubanClient` (modules/douban/client.py)
- **无需 API Key**，直接爬取豆瓣数据

### Bangumi (`backend/app/api/bangumi.py` + `core/bangumi_client.py`)
- **已有完整 API**：
  - `/bangumi/search` - 搜索
  - `/bangumi/calendar` - 每日放送
  - `/bangumi/popular` - 热门动漫
- 使用公共 API `api.bgm.tv`，**无需 Key**
- 缓存：搜索 1h，日历 1h，热门 6h

## 3. 音乐中心当前状态

### 后端
- 已有音乐库 API（专辑/艺术家/曲目）
- 已有音乐订阅 API (`music_subscription.py`, `music_chart_admin.py`)
- **榜单数据来源**：需要管理员预先配置榜单源

### 前端 (`frontend/src/pages/MusicCenter.vue`)
- 三个 Tab：「我的音乐」「榜单 & 订阅」「音乐任务」
- 「榜单 & 订阅」Tab 已有 UI 骨架：
  - 左侧：榜单选择器 + 我的订阅列表
  - 右侧：榜单歌曲列表
- **缺失内容**：
  - 无默认公共榜单数据
  - 空库时无引导说明
  - 榜单依赖管理员手动添加

## 4. 版本与文档现状

- `backend/app/core/version.py`: `APP_VERSION = "0.0.2"` ✅
- `CHANGELOG.md`: 有 0.0.2 条目 ✅
- `docs/FRONTEND_MAP.md`: 有 0.0.2 UI 基线描述 ✅
- `docs/VABHUB_SYSTEM_OVERVIEW.md`: 有 0.0.2 里程碑 ✅

## 5. P1-PZ 实施要点

### P1: 公共 Metadata Key 配置层
- 新增 `PUBLIC_TMDB_DISCOVER_KEY` 环境变量
- 新增 `get_tmdb_key_for_discover()` helper（公共优先）
- 豆瓣/Bangumi 无需 key，直接可用

### P2: 发现页后端聚合服务
- 重构 `/discover/home` 为多源聚合
- 添加豆瓣热门、Bangumi 热门番剧 section
- 返回 `has_public_keys` / `has_private_keys` 标识

### P3: 发现页前端重构
- 顶部显示数据源状态
- 横向滚动卡片列表
- 单源失败不影响整体

### P4: 音乐中心首页
- 后端：新增 `/api/music/home` 返回默认榜单
- 前端：空库时显示引导说明

---
*P0 巡检完成，未做任何代码变更*
