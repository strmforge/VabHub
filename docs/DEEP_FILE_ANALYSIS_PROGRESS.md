# VabHub 逐文件深入分析进度

## 分析状态
- **开始时间**: 2025-11-30
- **当前进度**: API文件分析中

---

## 一、API文件分析 (backend/app/api/)

### 已分析完成 (16/140+)

| 文件名 | 大小 | 核心功能 | 端点数量 |
|--------|------|----------|----------|
| `admin_library_settings.py` | 3.5KB | 媒体库设置只读总览（Inbox配置、媒体库根目录） | 1 GET |
| `admin_status.py` | 9.1KB | 系统运维状态（Runner状态、外部源状态、存储概览） | 4 GET |
| `admin_tts_settings.py` | 16.1KB | TTS设置总览（配置、健康状态、限流、使用统计、预设热度） | 1 GET |
| `alert_channels.py` | 3.1KB | 告警渠道CRUD（Telegram/Webhook/Bark） | 6 (CRUD+测试) |
| `audiobook.py` | 11.1KB | 有声书管理（列表、详情、统计、按作品查询） | 4 GET |
| `audiobook_center.py` | 16.9KB | 有声书中心聚合（TTS状态、听书进度、阅读进度联动） | 1 GET |
| `audiobooks.py` | 4.4KB | 有声书文件流式播放 | 1 GET |
| `auth.py` | 9.7KB | 认证（注册、登录、登出、获取当前用户） | 4 POST/GET |
| `backup.py` | 17.3KB | 备份系统（创建、列表、恢复、状态、配置导出、用户数据导出） | 7 |
| `bangumi.py` | 4.5KB | Bangumi动漫（搜索、详情、日历、热门） | 4 GET |
| `calendar.py` | 3.6KB | 日历事件（获取事件、订阅iCalendar） | 2 GET |
| `category.py` | 9.7KB | 分类配置（获取/更新YAML配置、预览分类、列表、重载） | 5 |
| `charts.py` | 11KB | 榜单（音乐榜单、影视榜单、Netflix周数、平台比较） | 8 |
| `cloud_storage.py` | 19.2KB | 云存储（CRUD、115二维码登录、文件列表、使用情况） | 10+ |
| `cloud_storage_chain.py` | 6.9KB | 云存储Chain模式版本 | 6 |
| `config_admin.py` | 3.3KB | 配置管理（Schema查询、校验、当前配置） | 3 GET/POST |
| `cookiecloud.py` | 17.5KB | CookieCloud（设置、同步、测试、状态、历史） | 8 |
| `dashboard.py` | 19KB | 仪表盘（综合数据、系统资源历史、布局管理） | 10+ |
| `decision.py` | 2.5KB | 下载决策调试（Dry-run） | 1 POST |
| `directory.py` | 12.9KB | 目录配置CRUD | 5 |
| `douban.py` | 17.7KB | 豆瓣API（搜索、详情、热门电影/电视剧） | 5+ |
| `download.py` | 41.5KB | 下载管理（列表、详情、暂停/恢复/删除、限速、队列操作、手动添加） | 20+ |
| `downloader.py` | 14.3KB | 下载器实例管理（qBittorrent/Transmission状态、测试） | 4 |
| `duplicate_detection.py` | 5.4KB | 重复文件检测与质量比较 | 2 POST |

### 关键发现

#### 1. 统一响应模型
所有API使用统一的`BaseResponse`格式：
```python
{
    "success": true,
    "message": "...",
    "data": {...},
    "timestamp": "..."
}
```

#### 2. 核心服务依赖
- `DashboardService` - 仪表盘数据聚合
- `DownloadService` - 下载任务管理
- `BackupService` - 备份管理
- `CookieCloudSyncService` - Cookie同步
- `CloudStorageService` - 云存储操作
- `SettingsService` - 系统设置

#### 3. 外部集成
- **豆瓣** - 影视搜索和详情
- **Bangumi** - 动漫数据
- **115网盘** - 二维码登录、文件操作
- **qBittorrent/Transmission** - 下载器控制
- **CookieCloud** - PT站点Cookie同步

#### 4. 特色功能
- **Local Intel状态追踪** - HR/站点状态集成到下载列表
- **TTS预设热度分析** - hot/sleeping/cold分类
- **仪表盘布局自定义** - 可拖拽Widget系统
- **备份配置导出** - 敏感字段掩码处理

---

## 待分析

### API文件 (剩余约116个)
- ebook.py, ext_indexer.py, file_browser.py, file_cleaner.py...
- filter_rule_groups.py, global_rules.py, global_search.py...
- health.py, hnr.py, home.py, inbox_dev.py, intel.py...
- library.py, log_center.py, logs.py...
- manga_*.py (6个), media*.py (5个)...
- multimodal*.py (5个), music*.py (3个)...
- notification*.py (4个), novel*.py (5个)...
- plugin*.py (6个), recommendation.py...
- rss*.py (2个), search*.py (2个), site*.py (6个)...
- strm.py, subscription*.py (3个)...
- tts_*.py (9个), workflow*.py (2个)...

### 其他目录
- `backend/app/modules/` - 70+模块
- `backend/app/services/` - 50+服务
- `backend/app/models/` - 85+模型
- `backend/app/runners/` - 15+后台任务
- `backend/app/core/` - 核心模块
- `frontend/src/pages/` - 75+页面
- `frontend/src/components/` - 110+组件

---

*此文件将随分析进度持续更新*
