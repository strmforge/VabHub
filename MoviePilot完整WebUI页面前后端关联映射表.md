# MoviePilot 完整 WebUI 页面前后端关联映射表

## 📋 目录
1. [概述](#概述)
2. [页面路由列表](#页面路由列表)
3. [详细页面映射](#详细页面映射)
4. [API端点分类](#api端点分类)
5. [数据流转图](#数据流转图)
6. [开发指南](#开发指南)

---

## 概述

本文档提供了 MoviePilot 所有 WebUI 页面与后端 API 端点的完整映射关系，便于开发时快速查找和参考。

### 架构模式
- **前端**: Vue 3 + Vuetify 3 + TypeScript
- **后端**: FastAPI + SQLAlchemy + Chain 模式
- **数据流**: 前端组件 → API 调用 → 后端端点 → Chain 层 → 数据层

---

## 页面路由列表

| 路由路径 | 页面文件 | 页面名称 | 主要功能 |
|---------|---------|---------|---------|
| `/dashboard` | `pages/dashboard.vue` | 仪表盘 | 系统监控、媒体统计、下载统计 |
| `/recommend` | `pages/recommend.vue` | 推荐 | 媒体推荐、热门内容 |
| `/discover` | `pages/discover.vue` | 发现 | 媒体发现、搜索、浏览 |
| `/resource` | `pages/resource.vue` | 资源 | 资源搜索、下载管理 |
| `/subscribe/movie` | `pages/subscribe.vue` | 订阅（电影） | 电影订阅管理 |
| `/subscribe/tv` | `pages/subscribe.vue` | 订阅（电视剧） | 电视剧订阅管理 |
| `/subscribe-share` | `pages/subscribe-share.vue` | 订阅分享 | 订阅分享管理 |
| `/workflow` | `pages/workflow.vue` | 工作流 | 工作流管理 |
| `/calendar` | `pages/calendar.vue` | 日历 | 媒体日历、播出时间 |
| `/downloading` | `pages/downloading.vue` | 下载中 | 下载任务管理 |
| `/history` | `pages/history.vue` | 历史记录 | 下载历史、整理历史 |
| `/site` | `pages/site.vue` | 站点管理 | PT站点管理 |
| `/user` | `pages/user.vue` | 用户管理 | 用户列表、权限管理 |
| `/profile` | `pages/profile.vue` | 个人资料 | 用户个人信息 |
| `/plugins` | `pages/plugin.vue` | 插件中心 | 插件管理 |
| `/setting` | `pages/setting.vue` | 系统设置 | 系统配置 |
| `/browse/:paths+` | `pages/browse.vue` | 文件浏览 | 文件浏览器 |
| `/credits/:paths+` | `pages/credits.vue` | 演职员 | 演职员信息 |
| `/person` | `pages/person.vue` | 人物详情 | 人物信息 |
| `/media` | `pages/media.vue` | 媒体详情 | 媒体信息详情 |
| `/filemanager` | `pages/filemanager.vue` | 文件管理 | 文件管理器 |
| `/apps` | `pages/appcenter.vue` | 应用中心 | 应用管理 |
| `/login` | `pages/login.vue` | 登录 | 用户登录 |

---

## 详细页面映射

### 1. 仪表盘 (Dashboard)

#### 页面文件
- **主页面**: `pages/dashboard.vue`
- **视图组件**: 
  - `views/dashboard/AnalyticsCpu.vue`
  - `views/dashboard/AnalyticsMemory.vue`
  - `views/dashboard/AnalyticsNetwork.vue`
  - `views/dashboard/AnalyticsStorage.vue`
  - `views/dashboard/AnalyticsMediaStatistic.vue`
  - `views/dashboard/AnalyticsScheduler.vue`
  - `views/dashboard/MediaServerLatest.vue`
  - `views/dashboard/MediaServerPlaying.vue`
  - `views/dashboard/MediaServerLibrary.vue`

#### API 端点映射

| 前端调用 | 后端端点 | 方法 | 功能 | 响应模型 |
|---------|---------|------|------|---------|
| `api.get('/user/config/Dashboard')` | `/user/config/Dashboard` | GET | 获取仪表盘配置 | `schemas.Response` |
| `api.post('/user/config/Dashboard', data)` | `/user/config/Dashboard` | POST | 保存仪表盘配置 | `schemas.Response` |
| `api.get('/user/config/DashboardOrder')` | `/user/config/DashboardOrder` | GET | 获取仪表盘顺序 | `schemas.Response` |
| `api.post('/user/config/DashboardOrder', data)` | `/user/config/DashboardOrder` | POST | 保存仪表盘顺序 | `schemas.Response` |
| `api.get('/plugin/dashboard/meta')` | `/plugin/dashboard/meta` | GET | 获取插件仪表盘元信息 | `List[dict]` |
| `api.get('/plugin/dashboard/${id}')` | `/plugin/dashboard/{id}` | GET | 获取插件仪表盘数据 | `dict` |
| `api.get('/dashboard/statistic')` | `/dashboard/statistic` | GET | 获取媒体统计 | `schemas.Statistic` |
| `api.get('/dashboard/storage')` | `/dashboard/storage` | GET | 获取存储空间 | `schemas.Storage` |
| `api.get('/dashboard/processes')` | `/dashboard/processes` | GET | 获取进程信息 | `List[schemas.ProcessInfo]` |
| `api.get('/dashboard/downloader')` | `/dashboard/downloader` | GET | 获取下载器信息 | `schemas.DownloaderInfo` |
| `api.get('/dashboard/schedule')` | `/dashboard/schedule` | GET | 获取后台服务 | `List[schemas.ScheduleInfo]` |
| `api.get('/dashboard/transfer')` | `/dashboard/transfer` | GET | 获取文件整理统计 | `List[int]` |
| `api.get('/dashboard/cpu')` | `/dashboard/cpu` | GET | 获取CPU使用率 | `int` |
| `api.get('/dashboard/memory')` | `/dashboard/memory` | GET | 获取内存使用量 | `List[int]` |
| `api.get('/dashboard/network')` | `/dashboard/network` | GET | 获取网络流量 | `List[int]` |
| `api.get('/mediaserver/latest')` | `/mediaserver/latest` | GET | 获取最新入库条目 | `List[schemas.MediaServerPlayItem]` |
| `api.get('/mediaserver/playing')` | `/mediaserver/playing` | GET | 获取正在播放条目 | `List[schemas.MediaServerPlayItem]` |
| `api.get('/mediaserver/library')` | `/mediaserver/library` | GET | 获取媒体库列表 | `List[schemas.MediaServerLibrary]` |

#### 后端实现
- **API层**: `app/api/endpoints/dashboard.py`
- **Chain层**: `app/chain/dashboard.py` (DashboardChain)
- **数据模型**: `app/schemas/types.py` (Statistic, Storage, ProcessInfo, DownloaderInfo, ScheduleInfo)

---

### 2. 订阅管理 (Subscribe)

#### 页面文件
- **主页面**: `pages/subscribe.vue`
- **视图组件**:
  - `views/subscribe/SubscribeListView.vue`
  - `views/subscribe/SubscribePopularView.vue`
  - `views/subscribe/SubscribeShareView.vue`
  - `views/subscribe/FullCalendarView.vue`
- **对话框组件**:
  - `components/dialog/SubscribeEditDialog.vue`
  - `components/dialog/SubscribeSeasonDialog.vue`
  - `components/dialog/SubscribeShareDialog.vue`
  - `components/dialog/SubscribeHistoryDialog.vue`
  - `components/dialog/SubscribeFilesDialog.vue`
  - `components/dialog/SubscribeShareStatisticsDialog.vue`

#### API 端点映射

| 前端调用 | 后端端点 | 方法 | 功能 | 响应模型 |
|---------|---------|------|------|---------|
| `api.get('subscribe/')` | `/subscribe/` | GET | 获取所有订阅 | `List[schemas.Subscribe]` |
| `api.get('subscribe/media/${mediaid}')` | `/subscribe/media/{mediaid}` | GET | 获取媒体订阅信息 | `schemas.Subscribe` |
| `api.post('subscribe/', data)` | `/subscribe/` | POST | 创建新订阅 | `schemas.Response` |
| `api.put('subscribe/', data)` | `/subscribe/` | PUT | 更新订阅信息 | `schemas.Response` |
| `api.delete('subscribe/${id}')` | `/subscribe/{id}` | DELETE | 删除订阅 | `schemas.Response` |
| `api.put('subscribe/status/${id}?state=R')` | `/subscribe/status/{subid}` | PUT | 更新订阅状态（启用） | `schemas.Response` |
| `api.put('subscribe/status/${id}?state=S')` | `/subscribe/status/{subid}` | PUT | 更新订阅状态（暂停） | `schemas.Response` |
| `api.put('subscribe/status/${id}?state=P')` | `/subscribe/status/{subid}` | PUT | 更新订阅状态（待定） | `schemas.Response` |
| `api.get('subscribe/refresh')` | `/subscribe/refresh` | GET | 刷新所有订阅 | `schemas.Response` |
| `api.get('subscribe/reset/${id}')` | `/subscribe/reset/{subid}` | GET | 重置订阅 | `schemas.Response` |
| `api.get('subscribe/history/${id}')` | `/subscribe/history/{subid}` | GET | 获取订阅历史 | `List[schemas.SubscribeHistory]` |
| `api.get('subscribe/search')` | `/subscribe/search` | GET | 搜索订阅 | `List[schemas.Subscribe]` |
| `api.get('subscribe/popular')` | `/subscribe/popular` | GET | 获取热门订阅 | `List[schemas.Subscribe]` |
| `api.get('subscribe/share')` | `/subscribe/share` | GET | 获取订阅分享 | `List[schemas.SubscribeShare]` |
| `api.get('media/groups/${tmdbid}')` | `/media/groups/{tmdbid}` | GET | 获取剧集组信息 | `List[dict]` |
| `api.get('site/rss')` | `/site/rss` | GET | 获取RSS站点列表 | `List[schemas.Site]` |
| `api.get('download/clients')` | `/download/clients` | GET | 获取下载器列表 | `List[dict]` |
| `api.get('system/setting/DefaultMovieSubscribeConfig')` | `/system/setting/DefaultMovieSubscribeConfig` | GET | 获取默认电影订阅配置 | `schemas.Response` |
| `api.post('system/setting/DefaultMovieSubscribeConfig', data)` | `/system/setting/DefaultMovieSubscribeConfig` | POST | 保存默认电影订阅配置 | `schemas.Response` |
| `api.get('system/setting/DefaultTvSubscribeConfig')` | `/system/setting/DefaultTvSubscribeConfig` | GET | 获取默认电视剧订阅配置 | `schemas.Response` |
| `api.post('system/setting/DefaultTvSubscribeConfig', data)` | `/system/setting/DefaultTvSubscribeConfig` | POST | 保存默认电视剧订阅配置 | `schemas.Response` |
| `api.get('system/setting/UserFilterRuleGroups')` | `/system/setting/UserFilterRuleGroups` | GET | 获取过滤规则组 | `schemas.Response` |

#### 后端实现
- **API层**: `app/api/endpoints/subscribe.py`
- **Chain层**: `app/chain/subscribe.py` (SubscribeChain)
- **数据模型**: `app/db/models/subscribe.py` (Subscribe)
- **操作层**: `app/db/subscribe_oper.py` (SubscribeOper)

---

### 3. 下载管理 (Downloading)

#### 页面文件
- **主页面**: `pages/downloading.vue`
- **视图组件**: `views/reorganize/DownloadingListView.vue`

#### API 端点映射

| 前端调用 | 后端端点 | 方法 | 功能 | 响应模型 |
|---------|---------|------|------|---------|
| `api.get('download/clients')` | `/download/clients` | GET | 获取可用下载器 | `List[dict]` |
| `api.get('download/')` | `/download/` | GET | 获取正在下载的任务 | `List[schemas.DownloadingTorrent]` |
| `api.post('download/', data)` | `/download/` | POST | 添加下载（含媒体信息） | `schemas.Response` |
| `api.post('download/add', data)` | `/download/add` | POST | 添加下载（不含媒体信息） | `schemas.Response` |
| `api.get('download/start/${hashString}')` | `/download/start/{hashString}` | GET | 开始任务 | `schemas.Response` |
| `api.get('download/stop/${hashString}')` | `/download/stop/{hashString}` | GET | 暂停任务 | `schemas.Response` |
| `api.delete('download/${hashString}')` | `/download/{hashString}` | DELETE | 删除下载任务 | `schemas.Response` |

#### 后端实现
- **API层**: `app/api/endpoints/download.py`
- **Chain层**: `app/chain/download.py` (DownloadChain)
- **数据模型**: `app/db/models/downloadhistory.py` (DownloadHistory)

---

### 4. 历史记录 (History)

#### 页面文件
- **主页面**: `pages/history.vue`
- **视图组件**: `views/reorganize/TransferHistoryView.vue`

#### API 端点映射

| 前端调用 | 后端端点 | 方法 | 功能 | 响应模型 |
|---------|---------|------|------|---------|
| `api.get('history/download', {params})` | `/history/download` | GET | 查询下载历史记录 | `List[schemas.DownloadHistory]` |
| `api.delete('history/download', data)` | `/history/download` | DELETE | 删除下载历史记录 | `schemas.Response` |
| `api.get('history/transfer', {params})` | `/history/transfer` | GET | 查询整理记录 | `schemas.Response` |
| `api.delete('history/transfer?deletesrc=${deleteSrc}&deletedest=${deleteDest}', data)` | `/history/transfer` | DELETE | 删除整理记录 | `schemas.Response` |
| `api.get('history/empty/transfer')` | `/history/empty/transfer` | GET | 清空整理记录 | `schemas.Response` |
| `api.get('system/setting/Storages')` | `/system/setting/Storages` | GET | 获取存储配置 | `schemas.Response` |

#### 后端实现
- **API层**: `app/api/endpoints/history.py`
- **数据模型**: 
  - `app/db/models/downloadhistory.py` (DownloadHistory)
  - `app/db/models/transferhistory.py` (TransferHistory)

---

### 5. 站点管理 (Site)

#### 页面文件
- **主页面**: `pages/site.vue`
- **视图组件**: `views/site/SiteCardListView.vue`

#### API 端点映射

| 前端调用 | 后端端点 | 方法 | 功能 | 响应模型 |
|---------|---------|------|------|---------|
| `api.get('site/')` | `/site/` | GET | 获取所有站点 | `List[schemas.Site]` |
| `api.post('site/', data)` | `/site/` | POST | 新增站点 | `schemas.Response` |
| `api.put('site/', data)` | `/site/` | PUT | 更新站点 | `schemas.Response` |
| `api.delete('site/${id}')` | `/site/{id}` | DELETE | 删除站点 | `schemas.Response` |
| `api.get('site/cookiecloud')` | `/site/cookiecloud` | GET | CookieCloud同步 | `schemas.Response` |
| `api.get('site/reset')` | `/site/reset` | GET | 重置站点 | `schemas.Response` |
| `api.post('site/priorities', data)` | `/site/priorities` | POST | 批量更新站点优先级 | `schemas.Response` |
| `api.get('site/cookie/${site_id}')` | `/site/cookie/{site_id}` | GET | 更新站点Cookie&UA | `schemas.Response` |
| `api.get('site/userdata/latest')` | `/site/userdata/latest` | GET | 获取最新用户数据 | `List[schemas.SiteUserData]` |
| `api.get('site/statistic')` | `/site/statistic` | GET | 获取站点统计 | `schemas.Response` |
| `api.get('site/statistic/${domain}')` | `/site/statistic/{domain}` | GET | 获取指定站点统计 | `schemas.Response` |
| `api.get('site/rss')` | `/site/rss` | GET | 获取RSS站点列表 | `List[schemas.Site]` |

#### 后端实现
- **API层**: `app/api/endpoints/site.py`
- **Chain层**: `app/chain/site.py` (SiteChain)
- **数据模型**: `app/db/models/site.py` (Site)

---

### 6. 工作流 (Workflow)

#### 页面文件
- **主页面**: `pages/workflow.vue`
- **视图组件**:
  - `views/workflow/WorkflowListView.vue`
  - `views/workflow/WorkflowShareView.vue`

#### API 端点映射

| 前端调用 | 后端端点 | 方法 | 功能 | 响应模型 |
|---------|---------|------|------|---------|
| `api.get('workflow/')` | `/workflow/` | GET | 获取所有工作流 | `List[schemas.Workflow]` |
| `api.post('workflow/', data)` | `/workflow/` | POST | 创建工作流 | `schemas.Response` |
| `api.put('workflow/', data)` | `/workflow/` | PUT | 更新工作流 | `schemas.Response` |
| `api.delete('workflow/${id}')` | `/workflow/{id}` | DELETE | 删除工作流 | `schemas.Response` |
| `api.get('workflow/event_types')` | `/workflow/event_types` | GET | 获取所有事件类型 | `List[dict]` |
| `api.get('workflow/actions')` | `/workflow/actions` | GET | 获取所有动作 | `List[dict]` |
| `api.get('workflow/plugin/actions')` | `/workflow/plugin/actions` | GET | 查询插件动作 | `List[dict]` |
| `api.post('workflow/share', data)` | `/workflow/share` | POST | 分享工作流 | `schemas.Response` |
| `api.delete('workflow/share/${share_id}')` | `/workflow/share/{share_id}` | DELETE | 删除分享 | `schemas.Response` |
| `api.get('workflow/share')` | `/workflow/share` | GET | 获取工作流分享 | `List[schemas.WorkflowShare]` |

#### 后端实现
- **API层**: `app/api/endpoints/workflow.py`
- **Chain层**: `app/chain/workflow.py` (WorkflowChain)
- **数据模型**: `app/db/models/workflow.py` (Workflow)

---

### 7. 发现 (Discover)

#### 页面文件
- **主页面**: `pages/discover.vue`
- **视图组件**:
  - `views/discover/MediaDetailView.vue`
  - `views/discover/MediaCardListView.vue`
  - `views/discover/MediaCardSlideView.vue`
  - `views/discover/PersonDetailView.vue`
  - `views/discover/PersonCardListView.vue`
  - `views/discover/PersonCardSlideView.vue`
  - `views/discover/TheMovieDbView.vue`
  - `views/discover/DoubanView.vue`
  - `views/discover/BangumiView.vue`
  - `views/discover/ExtraSourceView.vue`

#### API 端点映射

| 前端调用 | 后端端点 | 方法 | 功能 | 响应模型 |
|---------|---------|------|------|---------|
| `api.get('discover/source')` | `/discover/source` | GET | 获取探索数据源 | `List[schemas.DiscoverMediaSource]` |
| `api.get('discover/bangumi')` | `/discover/bangumi` | GET | 探索Bangumi | `List[schemas.MediaInfo]` |
| `api.get('discover/douban_movies')` | `/discover/douban_movies` | GET | 探索豆瓣电影 | `List[schemas.MediaInfo]` |
| `api.get('discover/douban_tvs')` | `/discover/douban_tvs` | GET | 探索豆瓣剧集 | `List[schemas.MediaInfo]` |
| `api.get('discover/tmdb_movies')` | `/discover/tmdb_movies` | GET | 探索TMDB电影 | `List[schemas.MediaInfo]` |
| `api.get('discover/tmdb_tvs')` | `/discover/tmdb_tvs` | GET | 探索TMDB剧集 | `List[schemas.MediaInfo]` |
| `api.get('media/${mediaid}')` | `/media/{mediaid}` | GET | 获取媒体详情 | `schemas.MediaInfo` |
| `api.get('media/search')` | `/media/search` | GET | 搜索媒体/人物信息 | `List[dict]` |
| `api.get('tmdb/${tmdbid}/${season}')` | `/tmdb/seasons/{tmdbid}` | GET | 获取TMDB所有季 | `List[schemas.TmdbSeason]` |
| `api.get('tmdb/similar/${tmdbid}/${type_name}')` | `/tmdb/similar/{tmdbid}/{type_name}` | GET | 获取类似电影/电视剧 | `List[schemas.MediaInfo]` |
| `api.get('tmdb/recommend/${tmdbid}/${type_name}')` | `/tmdb/recommend/{tmdbid}/{type_name}` | GET | 获取推荐电影/电视剧 | `List[schemas.MediaInfo]` |
| `api.get('tmdb/credits/${tmdbid}/${type_name}')` | `/tmdb/credits/{tmdbid}/{type_name}` | GET | 获取演员阵容 | `List[schemas.MediaPerson]` |
| `api.get('tmdb/person/${person_id}')` | `/tmdb/person/{person_id}` | GET | 获取人物详情 | `schemas.MediaPerson` |
| `api.get('douban/${doubanid}')` | `/douban/{doubanid}` | GET | 获取豆瓣详情 | `schemas.MediaInfo` |
| `api.get('douban/credits/${doubanid}/${type_name}')` | `/douban/credits/{doubanid}/{type_name}` | GET | 获取豆瓣演员阵容 | `List[schemas.MediaPerson]` |
| `api.get('douban/recommend/${doubanid}/${type_name}')` | `/douban/recommend/{doubanid}/{type_name}` | GET | 获取豆瓣推荐 | `List[schemas.MediaInfo]` |
| `api.get('bangumi/${bangumiid}')` | `/bangumi/{bangumiid}` | GET | 获取Bangumi详情 | `schemas.MediaInfo` |
| `api.get('bangumi/credits/${bangumiid}')` | `/bangumi/credits/{bangumiid}` | GET | 获取Bangumi演职员表 | `List[schemas.MediaPerson]` |
| `api.get('bangumi/recommend/${bangumiid}')` | `/bangumi/recommend/{bangumiid}` | GET | 获取Bangumi推荐 | `List[schemas.MediaInfo]` |
| `api.get('site/')` | `/site/` | GET | 获取站点列表 | `List[schemas.Site]` |
| `api.get('system/setting/IndexerSites')` | `/system/setting/IndexerSites` | GET | 获取索引站点 | `schemas.Response` |
| `api.post('mediaserver/exists_remote', data)` | `/mediaserver/exists_remote` | POST | 查询已存在的剧集信息 | `Dict[int, list]` |
| `api.get('mediaserver/exists')` | `/mediaserver/exists` | GET | 查询本地是否存在 | `schemas.Response` |
| `api.post('mediaserver/notexists', data)` | `/mediaserver/notexists` | POST | 查询媒体库缺失信息 | `List[schemas.NotExistMediaInfo]` |
| `api.get('mediaserver/play/${itemid}')` | `/mediaserver/play/{itemid}` | GET | 在线播放 | `schemas.Response` |

#### 后端实现
- **API层**: 
  - `app/api/endpoints/discover.py`
  - `app/api/endpoints/media.py`
  - `app/api/endpoints/tmdb.py`
  - `app/api/endpoints/douban.py`
  - `app/api/endpoints/bangumi.py`
  - `app/api/endpoints/mediaserver.py`
- **Chain层**: 
  - `app/chain/media.py` (MediaChain)
  - `app/chain/tmdb.py` (TmdbChain)

---

### 8. 资源搜索 (Resource)

#### 页面文件
- **主页面**: `pages/resource.vue`

#### API 端点映射

| 前端调用 | 后端端点 | 方法 | 功能 | 响应模型 |
|---------|---------|------|------|---------|
| `api.get('search/last')` | `/search/last` | GET | 查询搜索结果 | `List[schemas.Context]` |
| `api.get('search/media/${keyword}')` | `/search/media/{mediaid}` | GET | 精确搜索资源 | `schemas.Response` |
| `api.get('search/title')` | `/search/title` | GET | 标题搜索资源 | `schemas.Response` |

#### 后端实现
- **API层**: `app/api/endpoints/search.py`
- **Chain层**: `app/chain/search.py` (SearchChain)

---

### 9. 推荐 (Recommend)

#### 页面文件
- **主页面**: `pages/recommend.vue`

#### API 端点映射

| 前端调用 | 后端端点 | 方法 | 功能 | 响应模型 |
|---------|---------|------|------|---------|
| `api.get('recommend/source')` | `/recommend/source` | GET | 获取推荐数据源 | `List[schemas.RecommendMediaSource]` |
| `api.get('recommend/bangumi_calendar')` | `/recommend/bangumi_calendar` | GET | Bangumi每日放送 | `List[schemas.MediaInfo]` |
| `api.get('recommend/douban_showing')` | `/recommend/douban_showing` | GET | 豆瓣正在热映 | `List[schemas.MediaInfo]` |
| `api.get('recommend/douban_movies')` | `/recommend/douban_movies` | GET | 豆瓣电影 | `List[schemas.MediaInfo]` |
| `api.get('recommend/douban_tvs')` | `/recommend/douban_tvs` | GET | 豆瓣剧集 | `List[schemas.MediaInfo]` |
| `api.get('recommend/douban_movie_top250')` | `/recommend/douban_movie_top250` | GET | 豆瓣电影TOP250 | `List[schemas.MediaInfo]` |
| `api.get('recommend/douban_tv_weekly_chinese')` | `/recommend/douban_tv_weekly_chinese` | GET | 豆瓣国产剧集周榜 | `List[schemas.MediaInfo]` |
| `api.get('recommend/douban_tv_weekly_global')` | `/recommend/douban_tv_weekly_global` | GET | 豆瓣全球剧集周榜 | `List[schemas.MediaInfo]` |
| `api.get('recommend/tmdb_movies')` | `/recommend/tmdb_movies` | GET | TMDB电影 | `List[schemas.MediaInfo]` |
| `api.get('recommend/tmdb_tvs')` | `/recommend/tmdb_tvs` | GET | TMDB剧集 | `List[schemas.MediaInfo]` |
| `api.get('/user/config/Recommend')` | `/user/config/Recommend` | GET | 获取推荐配置 | `schemas.Response` |
| `api.post('/user/config/Recommend', data)` | `/user/config/Recommend` | POST | 保存推荐配置 | `schemas.Response` |

#### 后端实现
- **API层**: `app/api/endpoints/recommend.py`
- **Chain层**: `app/chain/recommend.py` (RecommendChain)

---

### 10. 文件管理 (FileManager)

#### 页面文件
- **主页面**: `pages/filemanager.vue`
- **视图组件**: `views/reorganize/FileBrowserView.vue`
- **组件**: `components/FileBrowser.vue`

#### API 端点映射

| 前端调用 | 后端端点 | 方法 | 功能 | 响应模型 |
|---------|---------|------|------|---------|
| `api.post('storage/list', data)` | `/storage/list` | POST | 获取文件列表 | `List[schemas.FileItem]` |
| `api.post('storage/delete', data)` | `/storage/delete` | POST | 删除文件/目录 | `schemas.Response` |
| `api.post('storage/mkdir', data)` | `/storage/mkdir` | POST | 创建目录 | `schemas.Response` |
| `api.post('storage/rename', data)` | `/storage/rename` | POST | 重命名文件/目录 | `schemas.Response` |
| `api.post('storage/move', data)` | `/storage/move` | POST | 移动文件/目录 | `schemas.Response` |
| `api.post('storage/copy', data)` | `/storage/copy` | POST | 复制文件/目录 | `schemas.Response` |
| `api.post('storage/download', data)` | `/storage/download` | POST | 下载文件 | `StreamingResponse` |
| `api.post('storage/image', data)` | `/storage/image` | POST | 预览图片 | `StreamingResponse` |
| `api.get('storage/qrcode/${name}')` | `/storage/qrcode/{name}` | GET | 生成二维码（115网盘） | `schemas.Response` |
| `api.get('storage/check/${name}')` | `/storage/check/{name}` | GET | 检查登录状态（115网盘） | `schemas.Response` |
| `api.post('storage/save/${name}', data)` | `/storage/save/{name}` | POST | 保存存储配置 | `schemas.Response` |
| `api.get('storage/reset/${name}')` | `/storage/reset/{name}` | GET | 重置存储配置 | `schemas.Response` |

#### 后端实现
- **API层**: `app/api/endpoints/storage.py`
- **Chain层**: `app/chain/storage.py` (StorageChain)
- **存储模块**: 
  - `app/chain/modules/u115/` (115网盘)
  - `app/chain/modules/rclone/` (RClone)
  - `app/chain/modules/local/` (本地存储)

---

### 11. 用户管理 (User)

#### 页面文件
- **主页面**: `pages/user.vue`
- **视图组件**:
  - `views/user/UserListView.vue`
  - `views/user/UserProfileView.vue`

#### API 端点映射

| 前端调用 | 后端端点 | 方法 | 功能 | 响应模型 |
|---------|---------|------|------|---------|
| `api.get('user/')` | `/user/` | GET | 获取所有用户 | `List[schemas.User]` |
| `api.post('user/', data)` | `/user/` | POST | 新增用户 | `schemas.Response` |
| `api.put('user/', data)` | `/user/` | PUT | 更新用户 | `schemas.Response` |
| `api.delete('user/${id}')` | `/user/{id}` | DELETE | 删除用户 | `schemas.Response` |
| `api.get('user/current')` | `/user/current` | GET | 获取当前登录用户信息 | `schemas.User` |
| `api.post('user/avatar/${user_id}', data)` | `/user/avatar/{user_id}` | POST | 上传用户头像 | `schemas.Response` |
| `api.get('user/config/${key}')` | `/user/config/{key}` | GET | 获取用户配置 | `schemas.Response` |
| `api.post('user/config/${key}', data)` | `/user/config/{key}` | POST | 保存用户配置 | `schemas.Response` |

#### 后端实现
- **API层**: `app/api/endpoints/user.py`
- **数据模型**: `app/db/models/user.py` (User)

---

### 12. 插件管理 (Plugin)

#### 页面文件
- **主页面**: `pages/plugin.vue`
- **视图组件**: `views/plugin/PluginCardListView.vue`

#### API 端点映射

| 前端调用 | 后端端点 | 方法 | 功能 | 响应模型 |
|---------|---------|------|------|---------|
| `api.get('plugin/')` | `/plugin/` | GET | 获取所有插件 | `List[schemas.Plugin]` |
| `api.get('plugin/install/${id}')` | `/plugin/install/{id}` | GET | 安装插件 | `schemas.Response` |
| `api.get('plugin/uninstall/${id}')` | `/plugin/uninstall/{id}` | GET | 卸载插件 | `schemas.Response` |
| `api.get('plugin/statistic')` | `/plugin/statistic` | GET | 获取插件统计 | `schemas.Response` |
| `api.get('plugin/folders')` | `/plugin/folders` | GET | 获取插件文件夹 | `schemas.Response` |
| `api.post('plugin/folders', data)` | `/plugin/folders` | POST | 保存插件文件夹 | `schemas.Response` |
| `api.get('/user/config/PluginOrder')` | `/user/config/PluginOrder` | GET | 获取插件顺序 | `schemas.Response` |
| `api.post('/user/config/PluginOrder', data)` | `/user/config/PluginOrder` | POST | 保存插件顺序 | `schemas.Response` |

#### 后端实现
- **API层**: `app/api/endpoints/plugin.py`
- **核心**: `app/core/plugin.py` (PluginManager)

---

### 13. 系统设置 (Setting)

#### 页面文件
- **主页面**: `pages/setting.vue`
- **视图组件**:
  - `views/setting/AccountSettingDirectory.vue`
  - `views/setting/AccountSettingNotification.vue`
  - `views/setting/AccountSettingRule.vue`
  - `views/setting/AccountSettingSearch.vue`
  - `views/setting/AccountSettingService.vue`
  - `views/setting/AccountSettingSite.vue`
  - `views/setting/AccountSettingSubscribe.vue`
  - `views/setting/AccountSettingSystem.vue`

#### API 端点映射

| 前端调用 | 后端端点 | 方法 | 功能 | 响应模型 |
|---------|---------|------|------|---------|
| `api.get('system/setting/${key}')` | `/system/setting/{key}` | GET | 查询系统设置 | `schemas.Response` |
| `api.post('system/setting/${key}', data)` | `/system/setting/{key}` | POST | 更新系统设置 | `schemas.Response` |
| `api.get('system/global')` | `/system/global` | GET | 查询非敏感系统设置 | `schemas.Response` |
| `api.get('system/env')` | `/system/env` | GET | 查询系统配置 | `schemas.Response` |
| `api.post('system/env', data)` | `/system/env` | POST | 更新系统配置 | `schemas.Response` |
| `api.get('system/ruletest')` | `/system/ruletest` | GET | 过滤规则测试 | `schemas.Response` |
| `api.get('system/nettest')` | `/system/nettest` | GET | 测试网络连通性 | `schemas.Response` |
| `api.get('system/modulelist')` | `/system/modulelist` | GET | 查询已加载的模块ID列表 | `schemas.Response` |
| `api.get('system/moduletest/${moduleid}')` | `/system/moduletest/{moduleid}` | GET | 模块可用性测试 | `schemas.Response` |
| `api.get('system/restart')` | `/system/restart` | GET | 重启系统 | `schemas.Response` |
| `api.get('system/runscheduler')` | `/system/runscheduler` | GET | 运行服务 | `schemas.Response` |

#### 后端实现
- **API层**: `app/api/endpoints/system.py`
- **Chain层**: `app/chain/system.py` (SystemChain)

---

### 14. 登录 (Login)

#### 页面文件
- **主页面**: `pages/login.vue`

#### API 端点映射

| 前端调用 | 后端端点 | 方法 | 功能 | 响应模型 |
|---------|---------|------|------|---------|
| `api.post('login/access-token', data)` | `/login/access-token` | POST | 获取token | `schemas.Token` |
| `api.get('login/wallpaper')` | `/login/wallpaper` | GET | 登录页面电影海报 | `schemas.Response` |
| `api.get('login/wallpapers')` | `/login/wallpapers` | GET | 登录页面电影海报列表 | `List[str]` |
| `api.post('/message/webpush/subscribe', data)` | `/message/webpush/subscribe` | POST | 客户端webpush通知订阅 | `schemas.Response` |

#### 后端实现
- **API层**: `app/api/endpoints/login.py`
- **API层**: `app/api/endpoints/message.py`

---

## API端点分类

### 按功能分类

#### 1. 认证相关
- `/login/access-token` - 获取token
- `/login/wallpaper` - 登录页面电影海报
- `/user/current` - 获取当前登录用户信息

#### 2. 订阅相关
- `/subscribe/` - 订阅CRUD
- `/subscribe/media/{mediaid}` - 获取媒体订阅信息
- `/subscribe/status/{subid}` - 更新订阅状态
- `/subscribe/refresh` - 刷新所有订阅
- `/subscribe/history/{subid}` - 获取订阅历史

#### 3. 下载相关
- `/download/` - 下载任务管理
- `/download/clients` - 获取可用下载器
- `/download/start/{hashString}` - 开始任务
- `/download/stop/{hashString}` - 暂停任务

#### 4. 媒体相关
- `/media/{mediaid}` - 获取媒体详情
- `/media/search` - 搜索媒体/人物信息
- `/media/recognize` - 识别媒体信息
- `/tmdb/` - TMDB相关API
- `/douban/` - 豆瓣相关API
- `/bangumi/` - Bangumi相关API

#### 5. 搜索相关
- `/search/last` - 查询搜索结果
- `/search/media/{mediaid}` - 精确搜索资源
- `/search/title` - 标题搜索资源

#### 6. 站点相关
- `/site/` - 站点CRUD
- `/site/cookiecloud` - CookieCloud同步
- `/site/statistic` - 获取站点统计
- `/site/userdata/latest` - 获取最新用户数据

#### 7. 工作流相关
- `/workflow/` - 工作流CRUD
- `/workflow/event_types` - 获取所有事件类型
- `/workflow/actions` - 获取所有动作
- `/workflow/share` - 工作流分享

#### 8. 存储相关
- `/storage/list` - 获取文件列表
- `/storage/delete` - 删除文件/目录
- `/storage/mkdir` - 创建目录
- `/storage/qrcode/{name}` - 生成二维码（115网盘）
- `/storage/check/{name}` - 检查登录状态（115网盘）

#### 9. 系统相关
- `/system/setting/{key}` - 系统设置
- `/system/global` - 查询非敏感系统设置
- `/system/env` - 查询系统配置
- `/system/restart` - 重启系统
- `/system/runscheduler` - 运行服务

#### 10. 用户相关
- `/user/` - 用户CRUD
- `/user/config/{key}` - 用户配置
- `/user/avatar/{user_id}` - 上传用户头像

#### 11. 插件相关
- `/plugin/` - 插件管理
- `/plugin/install/{id}` - 安装插件
- `/plugin/uninstall/{id}` - 卸载插件
- `/plugin/statistic` - 获取插件统计

#### 12. 仪表盘相关
- `/dashboard/statistic` - 获取媒体统计
- `/dashboard/storage` - 获取存储空间
- `/dashboard/processes` - 获取进程信息
- `/dashboard/downloader` - 获取下载器信息
- `/dashboard/cpu` - 获取CPU使用率
- `/dashboard/memory` - 获取内存使用量
- `/dashboard/network` - 获取网络流量

#### 13. 媒体服务器相关
- `/mediaserver/latest` - 获取最新入库条目
- `/mediaserver/playing` - 获取正在播放条目
- `/mediaserver/library` - 获取媒体库列表
- `/mediaserver/exists` - 查询本地是否存在
- `/mediaserver/exists_remote` - 查询已存在的剧集信息
- `/mediaserver/notexists` - 查询媒体库缺失信息
- `/mediaserver/play/{itemid}` - 在线播放

#### 14. 历史记录相关
- `/history/download` - 查询下载历史记录
- `/history/transfer` - 查询整理记录
- `/history/empty/transfer` - 清空整理记录

#### 15. 推荐相关
- `/recommend/source` - 获取推荐数据源
- `/recommend/bangumi_calendar` - Bangumi每日放送
- `/recommend/douban_showing` - 豆瓣正在热映
- `/recommend/douban_movies` - 豆瓣电影
- `/recommend/douban_tvs` - 豆瓣剧集
- `/recommend/tmdb_movies` - TMDB电影
- `/recommend/tmdb_tvs` - TMDB剧集

#### 16. 发现相关
- `/discover/source` - 获取探索数据源
- `/discover/bangumi` - 探索Bangumi
- `/discover/douban_movies` - 探索豆瓣电影
- `/discover/douban_tvs` - 探索豆瓣剧集
- `/discover/tmdb_movies` - 探索TMDB电影
- `/discover/tmdb_tvs` - 探索TMDB剧集

#### 17. 种子相关
- `/torrent/cache` - 获取种子缓存
- `/torrent/cache/{domain}/{torrent_hash}` - 删除指定种子缓存

---

## 数据流转图

### 通用数据流转模式

```
┌─────────────────────────────────────────────────────────────┐
│                     前端层 (Vue 3)                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  页面组件 (Page Component)                           │  │
│  │  - dashboard.vue                                     │  │
│  │  - subscribe.vue                                     │  │
│  │  - downloading.vue                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  视图组件 (View Component)                           │  │
│  │  - SubscribeListView.vue                             │  │
│  │  - DownloadingListView.vue                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API 调用层 (api.get/post/put/delete)                │  │
│  │  - api.get('subscribe/')                             │  │
│  │  - api.post('download/', data)                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         ↓ HTTP Request
┌─────────────────────────────────────────────────────────────┐
│                     后端层 (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API 端点层 (app/api/endpoints/)                     │  │
│  │  - subscribe.py::read_subscribes                     │  │
│  │  - download.py::current                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Chain 层 (app/chain/)                               │  │
│  │  - SubscribeChain                                    │  │
│  │  - DownloadChain                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  数据操作层 (app/db/)                                │  │
│  │  - subscribe_oper.py                                 │  │
│  │  - downloadhistory_oper.py                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  数据模型层 (app/db/models/)                         │  │
│  │  - subscribe.py::Subscribe                           │  │
│  │  - downloadhistory.py::DownloadHistory               │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  数据模式层 (app/schemas/)                           │  │
│  │  - schemas.Subscribe                                 │  │
│  │  - schemas.DownloadHistory                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         ↓ HTTP Response
┌─────────────────────────────────────────────────────────────┐
│                     前端层 (Vue 3)                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  数据渲染 (Component)                                │  │
│  │  - SubscribeCard.vue                                 │  │
│  │  - DownloadingCard.vue                               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 开发指南

### 1. 添加新页面

#### 步骤
1. **创建页面文件**: 在 `src/pages/` 目录下创建新的 Vue 组件
2. **添加路由**: 在 `src/router/index.ts` 中添加路由配置
3. **创建视图组件**: 在 `src/views/` 目录下创建视图组件（如需要）
4. **创建API端点**: 在 `app/api/endpoints/` 目录下创建API端点文件
5. **实现Chain层**: 在 `app/chain/` 目录下实现Chain层逻辑
6. **创建数据模型**: 在 `app/db/models/` 目录下创建数据模型（如需要）

#### 示例
```typescript
// src/pages/my-page.vue
<script setup lang="ts">
import api from '@/api'

const data = ref([])

async function loadData() {
  data.value = await api.get('my-api/')
}
</script>

<template>
  <div>
    <!-- 页面内容 -->
  </div>
</template>
```

```python
# app/api/endpoints/my_api.py
from fastapi import APIRouter, Depends
from app import schemas
from app.core.security import verify_token

router = APIRouter()

@router.get("/", summary="获取数据", response_model=List[schemas.MyModel])
async def get_data(
    _: schemas.TokenPayload = Depends(verify_token)
) -> Any:
    """获取数据"""
    return []
```

### 2. 添加新API端点

#### 步骤
1. **在API端点文件中添加端点**: 在对应的 `app/api/endpoints/` 文件中添加新的端点
2. **实现Chain层逻辑**: 在对应的 `app/chain/` 文件中实现业务逻辑
3. **更新前端API调用**: 在前端组件中调用新的API端点

#### 示例
```python
# app/api/endpoints/subscribe.py
@router.get("/new-endpoint", summary="新端点", response_model=schemas.Response)
async def new_endpoint(
    db: AsyncSession = Depends(get_async_db),
    _: schemas.TokenPayload = Depends(verify_token)
) -> Any:
    """新端点"""
    result = await SubscribeChain().new_method()
    return schemas.Response(success=True, data=result)
```

```typescript
// src/views/subscribe/SubscribeListView.vue
async function callNewEndpoint() {
  const result = await api.get('subscribe/new-endpoint')
  // 处理结果
}
```

### 3. 调试技巧

#### 前端调试
1. **使用浏览器开发者工具**: 查看网络请求和响应
2. **使用Vue DevTools**: 查看组件状态和Props
3. **添加console.log**: 在关键位置添加日志

#### 后端调试
1. **使用FastAPI文档**: 访问 `/docs` 查看API文档并测试
2. **查看日志**: 查看后端日志文件
3. **使用调试器**: 使用Python调试器（如pdb）进行调试

### 4. 常见问题

#### 问题1: API调用失败
- **检查**: API端点路径是否正确
- **检查**: 请求方法（GET/POST/PUT/DELETE）是否正确
- **检查**: 请求参数是否正确
- **检查**: 认证token是否有效

#### 问题2: 数据格式不匹配
- **检查**: 后端响应模型是否与前端期望一致
- **检查**: 前端数据模型是否与后端一致
- **检查**: 数据序列化/反序列化是否正确

#### 问题3: 权限问题
- **检查**: 用户是否有权限访问该API
- **检查**: API端点是否需要认证
- **检查**: 用户角色是否正确

---

## 总结

本文档提供了 MoviePilot 所有 WebUI 页面与后端 API 端点的完整映射关系，包括：

1. **页面路由列表**: 所有页面的路由路径和文件位置
2. **详细页面映射**: 每个页面对应的API端点和使用方法
3. **API端点分类**: 按功能分类的API端点列表
4. **数据流转图**: 前后端数据流转的完整流程
5. **开发指南**: 添加新页面和API端点的步骤和示例

### 关键要点

1. **统一的API调用方式**: 使用 `api.get/post/put/delete` 进行API调用
2. **Chain模式**: 后端使用Chain模式统一处理业务逻辑
3. **数据模型统一**: 前后端使用相同的数据模型（Pydantic Schema）
4. **认证机制**: 使用JWT token进行认证
5. **错误处理**: 统一的错误处理机制

### 下一步

1. **参考本文档**: 在开发新功能时参考本文档
2. **更新文档**: 添加新功能时及时更新本文档
3. **优化代码**: 根据本文档优化现有代码
4. **测试验证**: 确保所有API端点正常工作

---

**文档版本**: 1.0  
**最后更新**: 2025-01-XX  
**维护者**: AI Assistant

