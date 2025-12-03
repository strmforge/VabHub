# VabHub 系统功能完整报告

> 基于代码文件逐个分析生成，不依赖任何文档

**生成时间**: 2025-11-30
**分析范围**: 后端 API、模块、服务、前端页面、组件

---

## 一、核心架构概览

### 技术栈
- **后端**: Python FastAPI + SQLAlchemy + Pydantic
- **前端**: Vue 3 + Vuetify + TypeScript
- **数据库**: SQLite/PostgreSQL
- **实时通信**: WebSocket
- **API风格**: RESTful + GraphQL

### 目录结构
```
backend/
├── app/
│   ├── api/           # 140+ API路由文件
│   ├── chain/         # Chain模式处理链
│   ├── core/          # 核心基础设施
│   ├── models/        # 80+ 数据库模型
│   ├── modules/       # 60+ 功能模块
│   ├── services/      # 45+ 业务服务
│   ├── runners/       # 15+ 后台任务
│   └── plugin_sdk/    # 插件开发SDK
frontend/
├── src/
│   ├── pages/         # 70+ 页面组件
│   └── components/    # 100+ UI组件
```

---

## 二、媒体管理系统

### 2.1 影视媒体管理

#### 相关文件
- `api/media.py` (43KB) - 媒体核心API
- `api/media_search.py` - TMDB搜索
- `api/media_identification.py` - 媒体识别
- `api/media_renamer.py` - 文件重命名
- `api/media_server.py` - 媒体服务器集成
- `pages/MediaDetail.vue` (26KB) - 媒体详情页
- `pages/MediaIdentification.vue` - 媒体识别页
- `pages/MediaRenamer.vue` (25KB) - 重命名工具

#### 功能清单
1. **媒体搜索与识别**
   - TMDB/TVDB/Fanart 多源元数据
   - 智能文件名解析
   - 批量媒体识别
   - 识别历史记录

2. **媒体文件管理**
   - 自动重命名（支持多种命名模板）
   - NFO文件生成
   - 海报/背景图下载
   - 文件整理和归档

3. **媒体服务器集成**
   - Emby 集成
   - Jellyfin 集成
   - Plex 集成
   - 媒体库自动刷新

### 2.2 音乐管理系统

#### 相关文件
- `api/music.py` (46KB) - 音乐核心API
- `api/music_chart_admin.py` - 榜单管理
- `api/music_subscription.py` (31KB) - 音乐订阅
- `modules/music/` - 11个音乐相关模块
- `services/music_*.py` - 7个音乐服务
- `pages/MusicCenter.vue` (35KB) - 音乐中心
- `runners/music_*.py` - 5个音乐后台任务

#### 功能清单
1. **音乐库管理**
   - 本地音乐导入和扫描
   - 元数据提取（ID3、FLAC标签）
   - 封面自动下载
   - 歌词获取

2. **音乐订阅系统**
   - 艺人订阅追更
   - 专辑订阅
   - 新歌自动下载
   - 订阅状态同步

3. **音乐榜单系统**
   - 多平台榜单聚合
   - TME由你榜
   - Billboard China
   - 自动榜单同步

4. **音乐搜索**
   - 多站点聚合搜索
   - 无损音乐优先
   - 格式筛选

### 2.3 漫画系统

#### 相关文件
- `api/manga_local.py` (31KB) - 本地漫画库
- `api/manga_remote.py` - 远程漫画浏览
- `api/manga_follow.py` - 漫画追更
- `api/manga_sync.py` - 漫画同步
- `api/manga_source_admin.py` - 漫画源管理
- `api/manga_progress.py` - 阅读进度
- `modules/manga_sources/` - 漫画源模块
- `services/manga_*.py` - 8个漫画服务
- `runners/manga_*.py` - 4个漫画后台任务
- `pages/manga/` - 5个漫画页面

#### 功能清单
1. **本地漫画库**
   - 漫画系列管理
   - 章节管理
   - 封面自动识别
   - 元数据编辑

2. **远程漫画浏览**
   - 多漫画源支持
   - 远程章节预览
   - 一键下载到本地

3. **漫画追更**
   - 追更列表管理
   - 自动检查更新
   - 新章节通知
   - 自动下载新章节

4. **漫画阅读器**
   - 在线阅读
   - 阅读进度同步
   - 多种阅读模式

### 2.4 小说/电子书系统

#### 相关文件
- `api/novel_center.py` - 小说中心
- `api/novel_reader.py` - 小说阅读器
- `api/novel_inbox.py` - 小说收件箱
- `api/ebook.py` - 电子书管理
- `modules/novel/` - 11个小说模块
- `pages/NovelCenter.vue` (24KB) - 小说中心
- `pages/NovelReader.vue` (26KB) - 小说阅读器

#### 功能清单
1. **小说管理**
   - 小说导入
   - 元数据管理
   - 分类整理

2. **电子书管理**
   - EPUB格式支持
   - 电子书阅读
   - 进度同步

3. **小说阅读器**
   - 在线阅读
   - 阅读进度保存
   - 书签功能

### 2.5 有声书系统

#### 相关文件
- `api/audiobook.py` - 有声书管理
- `api/audiobook_center.py` (17KB) - 有声书中心
- `api/audiobooks.py` - 有声书播放
- `api/user_audiobooks.py` - 用户有声书进度
- `modules/audiobook/` - 有声书模块
- `pages/AudiobookCenter.vue` (21KB) - 有声书中心

#### 功能清单
1. **有声书管理**
   - 有声书导入
   - 章节管理
   - 元数据编辑

2. **有声书播放**
   - 在线播放
   - 播放进度同步
   - 播放速度调节

### 2.6 TTS 语音合成系统

#### 相关文件
- `api/tts_*.py` - 12个TTS相关API
- `modules/tts/` - 17个TTS模块
- `pages/TTSCenter.vue` (22KB) - TTS中心
- `pages/DevTTS*.vue` - 5个TTS开发页面

#### 功能清单
1. **TTS任务管理**
   - 批量TTS转换
   - 任务队列管理
   - 进度监控

2. **声线预设**
   - 多种声线选择
   - 自定义预设
   - 作品级配置

3. **TTS存储管理**
   - 生成文件管理
   - 自动清理策略
   - 存储统计

---

## 三、下载与订阅系统

### 3.1 下载管理

#### 相关文件
- `api/download.py` (41KB) - 下载核心API
- `api/downloader.py` - 下载器管理
- `api/decision.py` - 下载决策
- `core/downloaders/` - 下载器实现
  - `qbittorrent.py` (18KB)
  - `transmission.py` (16KB)
- `modules/download/` - 下载模块
- `pages/Downloads.vue` (41KB) - 下载管理页

#### 功能清单
1. **下载器支持**
   - qBittorrent 完整支持
   - Transmission 完整支持
   - 多下载器管理
   - 标签和目录配置

2. **下载任务管理**
   - 任务列表（实时刷新）
   - 任务控制（暂停/恢复/删除）
   - 标签管理
   - 分类管理

3. **下载决策引擎**
   - 智能决策（质量/大小/做种）
   - 重复检测
   - 规则过滤

### 3.2 订阅系统

#### 相关文件
- `api/subscription.py` (32KB) - 订阅核心API
- `api/subscription_refresh.py` - 订阅刷新
- `api/subscription_defaults.py` - 默认配置
- `modules/subscription/` - 6个订阅模块
- `services/user_subscription_overview_service.py`
- `runners/subscription_checker.py` - 订阅检查器
- `pages/Subscriptions.vue` - 订阅管理页

#### 功能清单
1. **订阅管理**
   - 影视订阅
   - 音乐订阅
   - 漫画订阅
   - 小说订阅

2. **订阅规则**
   - 质量规则
   - 大小规则
   - 关键词规则
   - 排除规则

3. **订阅刷新**
   - 自动刷新检查
   - 手动刷新
   - 刷新历史

### 3.3 RSS 订阅

#### 相关文件
- `api/rss.py` (20KB) - RSS订阅API
- `api/rsshub.py` - RSSHub集成
- `modules/rss/` - 5个RSS模块
- `modules/rsshub/` - 7个RSSHub模块
- `pages/RSSSubscriptions.vue` - RSS订阅页
- `pages/RSSHub.vue` (18KB) - RSSHub管理页

#### 功能清单
1. **RSS订阅管理**
   - 多RSS源支持
   - 自动解析
   - 规则匹配
   - 自动下载

2. **RSSHub集成**
   - 本地RSSHub实例
   - 路由管理
   - 定时刷新

---

## 四、站点与搜索系统

### 4.1 站点管理

#### 相关文件
- `api/site.py` (27KB) - 站点核心API
- `api/site_manager.py` (16KB) - 站点管理
- `api/site_domain.py` - 域名管理
- `api/site_profile.py` - 配置文件管理
- `api/site_ai_adapter.py` - AI适配器
- `modules/site/` - 站点模块
- `modules/site_manager/` - 站点管理模块
- `modules/site_domain/` - 域名模块
- `modules/site_profile/` - 配置文件模块
- `modules/site_icon/` - 图标模块
- `pages/Sites.vue` - 站点列表页
- `pages/SiteManager.vue` (19KB) - 站点管理页

#### 功能清单
1. **站点管理**
   - 站点添加/编辑/删除
   - 站点连接测试
   - Cookie管理
   - 多域名支持

2. **站点配置**
   - 配置文件模板
   - 自定义配置
   - 配置导入导出

3. **站点签到**
   - 自动签到
   - 签到统计
   - 签到通知

4. **AI站点适配**
   - 智能页面解析
   - 自动适配新站点

### 4.2 搜索系统

#### 相关文件
- `api/search.py` (28KB) - 搜索核心API
- `api/search_chain.py` - 搜索链
- `api/global_search.py` - 全局搜索
- `modules/search/` - 18个搜索模块
  - `engine.py` - 搜索引擎
  - `indexers/` - 索引器
  - `parsers/` - 解析器
  - `result_aggregator.py` - 结果聚合
  - `query_expander.py` - 查询扩展
- `services/global_search_service.py`
- `pages/Search.vue` (13KB) - 搜索页

#### 功能清单
1. **多站点搜索**
   - PT站点聚合搜索
   - 公开索引器搜索
   - 私有索引器搜索

2. **搜索优化**
   - 结果去重
   - 质量排序
   - 做种数优先

3. **全局搜索**
   - 跨媒体类型搜索
   - 快捷键触发 (Ctrl+K)
   - 即时结果跳转

### 4.3 CookieCloud 集成

#### 相关文件
- `api/cookiecloud.py` (17KB) - CookieCloud API
- `core/cookiecloud.py` - CookieCloud核心
- `modules/cookiecloud/` - CookieCloud模块

#### 功能清单
1. **Cookie同步**
   - 自动同步Cookie
   - 多站点支持
   - 加密传输

---

## 五、文件与存储系统

### 5.1 云存储集成

#### 相关文件
- `api/cloud_storage.py` (19KB) - 云存储API
- `api/cloud_storage_chain.py` - 存储链
- `core/cloud_storage/` - 云存储核心
  - `providers/cloud_115.py` (59KB) - 115网盘
  - `providers/cloud_115_api.py` (91KB) - 115 API
  - `providers/cloud_115_oauth.py` - OAuth认证
  - `providers/cloud_115_oss.py` - OSS上传
  - `providers/cloud_115_upload.py` - 上传管理
  - `providers/rclone.py` (15KB) - RClone
  - `providers/openlist.py` - OpenList
- `pages/CloudStorage.vue` - 云存储页

#### 功能清单
1. **115网盘集成**
   - OAuth2认证
   - 文件浏览
   - 文件上传（含断点续传）
   - 文件下载
   - 文件操作（复制/移动/删除）
   - 视频播放
   - 字幕列表

2. **RClone集成**
   - 多种存储后端
   - 文件同步
   - 挂载支持

3. **OpenList集成**
   - 文件列表
   - 文件访问

### 5.2 STRM 系统

#### 相关文件
- `api/strm.py` (45KB) - STRM核心API
- `modules/strm/` - 16个STRM模块
  - `generator.py` (40KB) - STRM生成器
  - `sync_manager.py` (47KB) - 同步管理
  - `task_manager.py` - 任务管理
  - `lifecycle_tracker.py` - 生命周期追踪
  - `file_operation_mode.py` - 文件操作模式
  - `subtitle_handler.py` - 字幕处理

#### 功能清单
1. **STRM文件生成**
   - 从115网盘生成STRM
   - 支持多种URL模式
   - 智能内外网适配
   - HMAC签名保护

2. **STRM同步**
   - 全量同步
   - 增量同步
   - 定时同步任务
   - 同步状态监控

3. **STRM生命周期**
   - 文件追踪
   - 自动删除过期文件
   - 覆盖模式支持

4. **字幕集成**
   - 自动检测115字幕
   - 字幕文件下载

### 5.3 文件浏览器

#### 相关文件
- `api/file_browser.py` (21KB) - 文件浏览API
- `modules/file_browser/` - 文件浏览模块
- `pages/FileBrowser.vue` (31KB) - 文件浏览器页

#### 功能清单
1. **本地文件浏览**
   - 目录导航
   - 文件预览
   - 文件操作

2. **文件操作**
   - 复制/移动/删除
   - 重命名
   - 创建目录

### 5.4 文件整理

#### 相关文件
- `api/transfer_history.py` (15KB) - 转移历史
- `api/file_cleaner.py` - 文件清理
- `modules/file_operation/` - 6个文件操作模块
- `modules/file_cleaner/` - 文件清理模块
- `pages/TransferHistory.vue` - 转移历史页

#### 功能清单
1. **文件整理**
   - 自动整理规则
   - 事件驱动整理
   - 定时扫描整理

2. **文件清理**
   - 过期文件清理
   - 空目录清理
   - 重复文件清理

3. **转移历史**
   - 完整转移记录
   - 历史查询
   - 操作回滚

### 5.5 存储监控

#### 相关文件
- `api/storage_monitor.py` (21KB) - 存储监控API
- `api/storage.py` - 存储管理
- `modules/storage_monitor/` - 存储监控模块
- `pages/StorageMonitor.vue` - 存储监控页

#### 功能清单
1. **磁盘监控**
   - 磁盘空间监控
   - 使用趋势分析
   - 告警阈值设置

2. **存储统计**
   - 文件类型统计
   - 目录大小分析

---

## 六、智能系统

### 6.1 推荐系统

#### 相关文件
- `api/recommendation.py` (32KB) - 推荐API
- `modules/recommendation/` - 16个推荐模块
  - `algorithms.py` (27KB) - 推荐算法
  - `deep_learning/` - 深度学习推荐
  - `realtime/` - 实时推荐
  - `service.py` (17KB) - 推荐服务
- `pages/Recommendations.vue` - 推荐页

#### 功能清单
1. **协同过滤推荐**
   - 基于用户行为
   - 基于内容相似度

2. **深度学习推荐**
   - 神经网络模型
   - 特征提取
   - 模型训练

3. **实时推荐**
   - 实时行为分析
   - 动态推荐更新

### 6.2 多模态分析

#### 相关文件
- `api/multimodal.py` (15KB) - 多模态API
- `api/multimodal_metrics.py` - 性能监控
- `api/multimodal_optimization.py` - 优化API
- `api/multimodal_history.py` - 历史数据
- `api/multimodal_auto_optimization.py` - 自动优化
- `modules/multimodal/` - 11个多模态模块
  - `video_analyzer.py` (22KB) - 视频分析
  - `audio_analyzer.py` (20KB) - 音频分析
  - `text_analyzer.py` (16KB) - 文本分析
  - `fusion.py` (19KB) - 多模态融合
- `pages/MultimodalMonitoring.vue` - 监控页

#### 功能清单

##### 1. 文本情感分析
- **TextBlob集成**：支持情感分析（polarity、subjectivity）
- **语言检测**：自动识别文本语言
- **回退机制**：如果TextBlob不可用，回退到基于关键词的简化版本
- **API兼容**：保持现有API不变

##### 2. 视频场景检测
- **OpenCV集成**：基于直方图差异的场景检测
- **性能优化**：跳帧处理（每秒处理2帧）
- **配置支持**：支持最小场景长度和阈值配置
- **回退机制**：如果OpenCV不可用，场景检测功能不影响其他功能

##### 3. 音频特征提取
- **librosa集成**：提取MFCC、Chroma、Spectral等特征
- **丰富特征**：节拍、调性、模式、能量、响度
- **情感特征**：估算语音性、原声性、器乐性
- **回退机制**：如果librosa不可用，音频特征提取功能不影响其他功能

##### 4. 多模态特征融合
- **特征融合器**：支持视频、音频、文本特征融合
- **相似度计算**：余弦相似度、欧氏距离
- **权重调整**：支持特征权重动态调整
- **sklearn集成**：可选依赖，手动实现回退

#### 可选依赖

| 库 | 版本 | 功能 |
|---|---|---|
| `textblob` | >=0.17.1 | 文本情感分析和语言检测 |
| `opencv-python` | >=4.8.0 | 视频场景检测 |
| `librosa` | >=0.10.0 | 音频特征提取 |
| `scikit-learn` | >=1.3.0 | 特征缩放和相似度计算 |

#### 使用示例
```python
# 文本情感分析
from app.modules.multimodal.text_analyzer import TextAnalyzer
analyzer = TextAnalyzer()
result = await analyzer.analyze_text("这是一部很棒的电影！")

# 视频场景检测
from app.modules.multimodal.video_analyzer import VideoAnalyzer
analyzer = VideoAnalyzer()
result = await analyzer.analyze_video("/path/to/video.mp4")

# 音频特征提取
from app.modules.multimodal.audio_analyzer import AudioAnalyzer
analyzer = AudioAnalyzer()
result = await analyzer.analyze_audio("/path/to/audio.mp3")

# 多模态特征融合
from app.modules.multimodal.fusion import MultimodalFeatureFusion
fusion = MultimodalFeatureFusion()
fused = fusion.fuse_features(video_features, audio_features, text_features)
similarity = fusion.calculate_similarity(features1, features2, method="cosine")
```

### 6.3 OCR 系统

#### 相关文件
- `api/ocr.py` - OCR API
- `core/ocr.py` (19KB) - OCR核心
- `modules/ocr/` - OCR模块

#### 功能清单
1. **文字识别**
   - 图片文字提取
   - 字幕OCR
   - 多语言支持

### 6.4 Local Intel 系统

#### 相关文件
- `api/intel.py` (16KB) - Intel API
- `api/local_intel_admin.py` - 管理API
- `core/intel_local/` - 28个Local Intel模块
- `pages/LocalIntel.vue` - Local Intel页

#### 功能清单
1. **本地情报分析**
   - 文件质量评估
   - 移动安全检查
   - 做种状态分析

2. **智能决策**
   - 下载决策
   - 清理决策
   - 整理决策

---

## 七、HNR与安全系统

### 7.1 HNR 检测系统

#### 相关文件
- `api/hnr.py` (21KB) - HNR API
- `modules/hnr/` - 7个HNR模块
- `modules/hr_case/` - HR案例模块
- `pages/HNRMonitoring.vue` - HNR监控页

#### 功能清单
1. **HNR监控**
   - HR状态追踪
   - 分享率监控
   - 做种时间监控

2. **HNR案例管理**
   - 案例列表
   - 状态更新
   - 风险预警

### 7.2 安全策略系统

#### 相关文件
- `modules/safety/` - 3个安全模块
  - `engine.py` - 安全策略引擎
  - `models.py` - 安全模型
  - `settings.py` - 安全设置

#### 功能清单
1. **安全策略引擎**
   - 下载前检查
   - 删除保护
   - 移动保护
   - 清理保护

2. **安全配置**
   - 全局安全设置
   - 站点级设置
   - 订阅级设置

### 7.3 做种管理

#### 相关文件
- `api/seeding.py` - 做种API
- `modules/seeding/` - 做种模块

#### 功能清单
1. **做种监控**
   - 做种任务列表
   - 分享率统计
   - 做种时间统计

---

## 八、自动化系统

### 8.1 定时任务调度

#### 相关文件
- `api/scheduler.py` - 调度API
- `core/scheduler.py` (40KB) - 调度器核心
- `pages/SchedulerMonitor.vue` - 调度监控页

#### 功能清单
1. **任务调度**
   - Cron表达式支持
   - 任务队列管理
   - 并发控制

2. **任务监控**
   - 任务状态
   - 执行历史
   - 错误日志

### 8.2 工作流系统

#### 相关文件
- `api/workflow.py` (15KB) - 工作流API
- `api/workflow_extensions.py` - 工作流扩展
- `chain/workflow.py` - 工作流链
- `modules/workflow/` - 工作流模块
- `pages/Workflows.vue` - 工作流页

#### 功能清单
1. **工作流定义**
   - 可视化编辑
   - 条件分支
   - 循环处理

2. **工作流执行**
   - 手动触发
   - 定时触发
   - 事件触发

### 8.3 后台任务 (Runners)

#### 相关文件
- `runners/` - 15个后台任务
  - `subscription_checker.py` - 订阅检查
  - `manga_follow_sync.py` - 漫画追更同步
  - `music_subscription_checker.py` - 音乐订阅检查
  - `music_download_dispatcher.py` - 音乐下载调度
  - `ops_health_check.py` - 健康检查
  - `qa_self_check.py` - 自检任务
  - `telegram_bot_polling.py` - Telegram轮询

#### 功能清单
1. **订阅检查器** - 定期检查订阅更新
2. **漫画追更同步** - 自动检查漫画更新
3. **音乐订阅检查** - 检查音乐订阅更新
4. **健康检查** - 系统健康状态检查
5. **自检任务** - 系统自动诊断

---

## 九、通知与机器人系统

### 9.1 通知系统

#### 相关文件
- `api/notification.py` (13KB) - 通知API
- `api/notifications_user.py` (17KB) - 用户通知
- `api/notify_preferences.py` - 通知偏好
- `api/notify_test.py` - 通知测试
- `api/alert_channels.py` - 告警渠道
- `api/user_notify_channels.py` - 用户渠道
- `modules/notification/` - 6个通知模块
- `services/notification_service.py` (29KB)
- `pages/Notifications.vue` - 通知页

#### 功能清单
1. **通知渠道**
   - 系统内通知
   - 邮件通知
   - Webhook通知
   - Telegram通知

2. **通知管理**
   - 通知列表
   - 未读标记
   - 通知偏好设置

3. **告警系统**
   - 告警规则
   - 告警渠道
   - 告警历史

### 9.2 Telegram Bot

#### 相关文件
- `api/user_telegram.py` - Telegram绑定
- `modules/bots/` - 19个Bot模块
  - `commands/` - 12个命令模块
    - `admin.py` - 管理员命令
    - `basic.py` (37KB) - 基础命令
    - `downloads.py` (22KB) - 下载命令
    - `music.py` (31KB) - 音乐命令
    - `reading.py` (23KB) - 阅读命令
    - `search.py` - 搜索命令
    - `shelf.py` - 书架命令
    - `subscriptions.py` - 订阅命令
- `runners/telegram_bot_polling.py`

#### 功能清单
1. **Bot命令**
   - /start - 开始使用
   - /search - 搜索资源
   - /downloads - 下载管理
   - /music - 音乐功能
   - /reading - 阅读功能
   - /subscriptions - 订阅管理
   - /admin - 管理员功能

2. **交互功能**
   - 内联键盘
   - 对话状态管理
   - 回调处理

---

## 十、插件系统

### 10.1 插件管理

#### 相关文件
- `api/plugins.py` (21KB) - 插件API
- `api/plugin_admin.py` - 插件管理
- `api/plugin_config.py` - 插件配置
- `api/plugin_api.py` - 插件对外API
- `api/plugin_panels.py` - 插件面板
- `api/plugin_hub.py` (16KB) - Plugin Hub
- `core/plugins/` - 6个插件核心模块
- `services/plugin_*.py` - 9个插件服务
- `pages/Plugins.vue` - 插件页

#### 功能清单
1. **插件市场 (Plugin Hub)**
   - 在线插件浏览
   - 一键安装
   - 版本管理

2. **插件管理**
   - 安装/卸载
   - 启用/禁用
   - 配置管理

3. **插件开发**
   - Plugin SDK
   - 事件系统
   - API扩展

### 10.2 Plugin SDK

#### 相关文件
- `plugin_sdk/` - 13个SDK模块
  - `api.py` - API客户端
  - `cloud115.py` - 115网盘接口
  - `download.py` - 下载接口
  - `events.py` - 事件系统
  - `media.py` - 媒体接口
  - `notify.py` - 通知接口
  - `http_client.py` - HTTP客户端

#### 功能清单
1. **SDK功能**
   - 媒体操作
   - 下载操作
   - 115网盘操作
   - 通知发送
   - 事件监听

---

## 十一、系统管理

### 11.1 系统设置

#### 相关文件
- `api/settings.py` (16KB) - 设置API
- `api/system_settings.py` (21KB) - 系统设置
- `api/global_rules.py` (17KB) - 全局规则
- `api/filter_rule_groups.py` - 过滤规则组
- `api/scraping_switches.py` - 刮削开关
- `api/directory.py` - 目录配置
- `api/category.py` - 分类配置
- `pages/Settings.vue` (55KB) - 设置页
- `pages/SystemSettings.vue` (18KB) - 系统设置页
- `pages/GlobalRulesSettings.vue` (32KB) - 全局规则页
- `pages/DirectoryConfig.vue` - 目录配置页
- `pages/CategoryConfig.vue` - 分类配置页

#### 功能清单
1. **基础设置**
   - 系统名称
   - 语言设置
   - 时区设置
   - 主题设置

2. **目录配置**
   - 下载目录
   - 媒体库目录
   - 临时目录

3. **分类配置**
   - 媒体分类
   - 分类规则

4. **全局规则**
   - 质量规则
   - 大小规则
   - 关键词规则

### 11.2 系统监控

#### 相关文件
- `api/health.py` - 健康检查
- `api/system_health.py` - 系统健康
- `api/smart_health.py` (37KB) - 智能健康检查
- `api/monitoring.py` - 系统监控
- `api/performance.py` - 性能监控
- `api/admin_status.py` - 运维状态
- `services/system_health_*.py` - 健康服务
- `services/health_checks.py`

#### 功能清单
1. **健康检查**
   - 服务状态
   - 数据库状态
   - 缓存状态
   - 下载器状态

2. **性能监控**
   - CPU使用率
   - 内存使用
   - 响应时间

3. **智能健康检查**
   - 子系统检查
   - 依赖检查
   - 自动诊断

### 11.3 日志系统

#### 相关文件
- `api/logs.py` - 日志API
- `api/log_center.py` - 实时日志中心
- `modules/log/` - 日志模块
- `modules/log_center/` - 日志中心模块
- `pages/LogCenter.vue` - 日志中心页

#### 功能清单
1. **日志查看**
   - 系统日志
   - 任务日志
   - 错误日志

2. **实时日志**
   - WebSocket推送
   - 日志过滤
   - 日志搜索

### 11.4 备份系统

#### 相关文件
- `api/backup.py` (17KB) - 备份API
- `modules/backup/` - 备份模块

#### 功能清单
1. **数据备份**
   - 数据库备份
   - 配置备份
   - 定时备份

2. **数据恢复**
   - 备份列表
   - 一键恢复

### 11.5 系统更新

#### 相关文件
- `api/system_update.py` - 系统更新API
- `api/version.py` - 版本信息
- `pages/SystemUpdate.vue` - 系统更新页

#### 功能清单
1. **版本管理**
   - 当前版本
   - 可用更新
   - 更新日志

2. **更新操作**
   - 在线更新
   - Docker支持

### 11.6 系统自检

#### 相关文件
- `api/self_check.py` - 自检API
- `api/system_selfcheck.py` - 系统自检
- `modules/system_selfcheck/` - 自检模块
- `services/self_check_service.py` (25KB)
- `runners/qa_self_check.py`
- `pages/SystemSelfCheck.vue` - 自检页

#### 功能清单
1. **自动诊断**
   - 配置检查
   - 连接检查
   - 功能检查

2. **问题修复**
   - 自动修复建议
   - 手动修复指引

---

## 十二、用户界面

### 12.1 首页仪表盘

#### 相关文件
- `api/dashboard.py` (19KB) - 仪表盘API
- `api/home.py` - 首页API
- `chain/dashboard.py` - 仪表盘链
- `services/home_dashboard_service.py` (17KB)
- `pages/Dashboard.vue` - 仪表盘页
- `pages/HomeDashboard.vue` (25KB) - 首页仪表盘

#### 功能清单
1. **仪表盘组件**
   - 系统状态卡片
   - 下载统计
   - 存储统计
   - 最近活动

2. **可拖拽布局**
   - 自定义布局
   - 组件显隐

### 12.2 发现页

#### 相关文件
- `pages/Discover.vue` (26KB) - 发现页

#### 功能清单
1. **内容发现**
   - 热门推荐
   - 最新更新
   - 分类浏览

### 12.3 日历

#### 相关文件
- `api/calendar.py` - 日历API
- `modules/calendar/` - 日历模块
- `pages/Calendar.vue` (13KB) - 日历页

#### 功能清单
1. **订阅日历**
   - 预计上映
   - 订阅更新
   - 下载计划

### 12.4 我的书架

#### 相关文件
- `api/my_shelf.py` (18KB) - 书架API
- `pages/MyShelf.vue` (16KB) - 我的书架页

#### 功能清单
1. **书架管理**
   - 收藏内容
   - 阅读进度
   - 分类管理

### 12.5 作品中心

#### 相关文件
- `api/work.py` (18KB) - 作品API
- `api/work_links.py` - 作品关联
- `pages/WorkDetail.vue` (79KB) - 作品详情页

#### 功能清单
1. **作品管理**
   - 作品详情
   - 多版本关联
   - 跨媒体关联

### 12.6 榜单系统

#### 相关文件
- `api/charts.py` - 榜单API
- `modules/charts/` - 7个榜单模块
- `modules/music_charts/` - 8个音乐榜单模块

#### 功能清单
1. **影视榜单**
   - 豆瓣榜单
   - TMDB榜单

2. **音乐榜单**
   - TME由你榜
   - Billboard China

### 12.7 Onboarding

#### 相关文件
- `api/onboarding.py` - Onboarding API
- `pages/OnboardingWizard.vue` - 引导向导页

#### 功能清单
1. **新手引导**
   - 初始配置向导
   - 功能介绍
   - 快速设置

---

## 十三、外部集成

### 13.1 豆瓣集成

#### 相关文件
- `api/douban.py` (18KB) - 豆瓣API
- `modules/douban/` - 豆瓣模块

#### 功能清单
1. **豆瓣搜索**
   - 电影搜索
   - 书籍搜索
   - 音乐搜索

2. **豆瓣元数据**
   - 评分信息
   - 演员信息
   - 剧情简介

### 13.2 Bangumi 集成

#### 相关文件
- `api/bangumi.py` - Bangumi API
- `core/bangumi_client.py` - Bangumi客户端

#### 功能清单
1. **番剧搜索**
   - 动画搜索
   - 条目详情

2. **进度同步**
   - 观看进度
   - 收藏状态

### 13.3 外部索引器

#### 相关文件
- `api/ext_indexer.py` - 外部索引API
- `api/external_indexer_debug.py` - 索引调试
- `core/ext_indexer/` - 10个外部索引模块
- `core/indexer_bridge/` - 9个索引桥接模块
- `external_indexer_engine/` - 外部索引引擎
- `pages/ExternalIndexer.vue` - 外部索引页

#### 功能清单
1. **索引器管理**
   - Jackett 支持
   - Prowlarr 支持
   - 自定义索引器

2. **索引桥接**
   - 统一接口
   - 结果转换

### 13.4 字幕服务

#### 相关文件
- `api/subtitle.py` - 字幕API
- `api/subtitle_settings.py` - 字幕设置
- `modules/subtitle/` - 5个字幕模块
- `pages/Subtitles.vue` (21KB) - 字幕页

#### 功能清单
1. **字幕搜索**
   - OpenSubtitles
   - 射手网
   - 字幕库

2. **字幕下载**
   - 自动匹配
   - 批量下载

3. **字幕管理**
   - 字幕列表
   - 字幕同步

---

## 十四、Chain 模式架构

### 相关文件
- `chain/base.py` - Chain基类
- `chain/manager.py` - Chain管理器
- `chain/download.py` - 下载链
- `chain/search.py` - 搜索链
- `chain/site.py` - 站点链
- `chain/storage.py` - 存储链
- `chain/subscribe.py` - 订阅链
- `chain/music.py` - 音乐链
- `chain/workflow.py` - 工作流链
- `chain/dashboard.py` - 仪表盘链

### 功能清单
1. **Chain模式**
   - 模块化处理链
   - 可扩展设计
   - 插件式架构

---

## 十五、GraphQL API

### 相关文件
- `api/graphql/` - GraphQL模块
- `graphql/` - GraphQL定义
- `pages/GraphQLExplorer.vue` - GraphQL浏览器

### 功能清单
1. **GraphQL支持**
   - Schema定义
   - 查询支持
   - 变更支持

---

## 十六、WebSocket 实时通信

### 相关文件
- `api/websocket.py` - WebSocket API
- `core/websocket.py` - WebSocket核心

### 功能清单
1. **实时推送**
   - 下载进度
   - 任务状态
   - 日志推送
   - 通知推送

---

## 十七、认证与授权

### 相关文件
- `api/auth.py` - 认证API
- `core/auth.py` - 认证核心
- `core/security.py` - 安全模块
- `pages/Login.vue` - 登录页

### 功能清单
1. **用户认证**
   - 登录/登出
   - Token管理
   - 会话管理

2. **权限控制**
   - 角色管理
   - 权限验证

---

## 十八、密钥管理

### 相关文件
- `api/secrets.py` - 密钥API
- `core/secret_manager.py` - 密钥管理器
- `core/api_key_manager.py` - API密钥管理
- `core/cloud_key_manager.py` - 云密钥管理

### 功能清单
1. **密钥存储**
   - 加密存储
   - 安全访问

2. **API密钥**
   - TMDB Key
   - Fanart Key
   - 其他API Key

---

## 系统统计

### 代码规模
- **后端API文件**: 140+
- **后端模块**: 60+
- **后端服务**: 45+
- **数据库模型**: 80+
- **后台任务**: 15+
- **前端页面**: 70+
- **前端组件**: 100+

### 主要功能模块数
1. **媒体管理**: 6大子系统
2. **下载订阅**: 3大子系统
3. **站点搜索**: 3大子系统
4. **文件存储**: 5大子系统
5. **智能系统**: 4大子系统
6. **自动化**: 3大子系统
7. **通知Bot**: 2大子系统
8. **系统管理**: 6大子系统

---

---

## 十九、补充功能（基于文档对比）

### 19.1 短剧系统

#### 相关文件
- `pages/ShortDrama.vue` (13KB) - 短剧工作台
- `modules/short_drama/` - 短剧模块
- `api/douban.py` - 豆瓣短剧搜索

#### 功能清单
1. **短剧工作台**
   - 短剧订阅管理
   - 短剧下载状态
   - 短剧插件配置

2. **短剧订阅**
   - 豆瓣短剧搜索
   - 自动下载追更

### 19.2 统一收件箱 (Inbox) 系统

#### 相关文件
- `api/inbox_dev.py` - Inbox API
- `modules/inbox/` - 12个Inbox模块
- `models/inbox.py` - Inbox模型

#### 功能清单
1. **自动文件导入**
   - TXT小说自动导入
   - EPUB自动识别
   - 视频文件自动整理
   - 音乐文件自动入库

2. **媒体类型检测**
   - 智能文件类型识别
   - 基于内容的分类

3. **导入流水线**
   - NovelToEbookPipeline
   - 自动归档到媒体库

### 19.3 统一阅读中心

#### 相关文件
- `api/reading_hub.py` - 阅读中心API
- `api/reading_favorite.py` - 阅读收藏
- `services/reading_hub_service.py` (32KB)
- `services/reading_favorite_service.py`

#### 功能清单
1. **聚合展示**
   - 小说阅读进度
   - 漫画阅读进度
   - 有声书听书进度

2. **统一收藏**
   - 跨媒体收藏
   - 阅读历史

3. **通知集成**
   - 漫画更新通知
   - 电子书导入通知
   - 有声书完成通知
   - TTS完成通知

### 19.4 Demo 模式

#### 相关文件
- `runners/demo_seed.py` (10KB) - Demo数据初始化
- `core/demo_guard.py` - Demo模式保护

#### 功能清单
1. **演示模式**
   - 无需配置外部服务
   - 预置Demo数据
   - 所有页面可浏览

### 19.5 订阅规则中心 (SUBS-RULES-1)

#### 相关文件
- `api/subscription_defaults.py` - 默认订阅配置
- `api/filter_rule_groups.py` - 过滤规则组
- `models/filter_rule_group.py` - 规则组模型
- `modules/subscription/rule_engine.py` - 规则引擎

#### 功能清单
1. **默认订阅配置**
   - 电影订阅默认配置
   - 剧集订阅默认配置
   - 音乐订阅默认配置

2. **过滤规则组**
   - 可视化规则编辑
   - 优先级规则组
   - 规则复用

### 19.6 媒体分类扩展

#### 相关文件
- `config/category.yaml` - 分类配置
- `api/category.py` - 分类API

#### 功能清单
1. **电子书分类**
   - 科幻/奇幻/言情/推理/非虚构/轻小说

2. **有声书分类**
   - 按原作类型分类

3. **漫画分类**
   - 日漫/国漫/美漫/韩漫

### 19.7 作品宇宙面板 (Work Hub Plus)

#### 相关文件
- `api/work.py` - 作品中心API
- `api/work_links.py` - 作品关联
- `pages/WorkDetail.vue` (79KB)

#### 功能清单
1. **作品关联**
   - 相关视频改编（电影/剧集/动漫/短剧）
   - 相关音乐（OST/主题曲）
   - 跨媒体关联

2. **手动关联**
   - 用户自定义关联
   - 批量关联管理

### 19.8 Local Intel 种子索引

#### 相关文件
- `core/intel_local/` - 28个Local Intel模块
- `api/intel.py` - Intel API

#### 功能清单
1. **种子索引**
   - 本地PT种子索引
   - 全站扫描+增量刷新
   - HR/Free状态追踪

2. **搜索增强**
   - 索引优先搜索
   - 站点补充搜索
   - HR过滤

### 19.9 运维监控增强 (OPS)

#### 相关文件
- `api/monitoring.py` - 监控API
- `api/admin_status.py` - 运维状态
- `api/alert_channels.py` - 告警渠道
- `services/system_health_*.py`
- `runners/ops_health_check.py`

#### 功能清单
1. **健康检查项**
   - 数据库连接检查
   - Redis缓存检查
   - 下载器检查
   - PT索引器检查
   - 漫画源检查
   - 音乐榜单源检查
   - 磁盘空间检查

2. **Runner SLA**
   - 成功/失败统计
   - 成功率可视化
   - 运行时长追踪

3. **告警渠道**
   - Telegram告警
   - Webhook告警
   - Bark告警

4. **体检报告**
   - JSON/Markdown格式
   - 一键生成

### 19.10 视频播放进度

#### 相关文件
- `api/video_progress.py` - 视频进度API
- `models/user_video_progress.py` - 进度模型

#### 功能清单
1. **播放进度同步**
   - 记录播放位置
   - 跨设备同步

### 19.11 115远程播放

#### 相关文件
- `api/remote_video_115.py` - 115远程播放API
- `pages/Remote115Player.vue` (17KB)
- `modules/remote_playback/` - 远程播放模块

#### 功能清单
1. **115视频播放**
   - 在线播放115视频
   - 字幕加载
   - 播放进度

### 19.12 电视墙 (Player Wall)

#### 相关文件
- `api/player_wall.py` - 电视墙API
- `services/player_wall_aggregation_service.py` (11KB)
- `pages/PlayerWall.vue` - 电视墙页面

#### 功能清单
1. **聚合展示**
   - 最近播放
   - 热门内容
   - 继续观看

---

## 二十、Telegram Bot 命令完整清单

基于文档 `BOT_TELEGRAM_COMMANDS_REFERENCE.md` 补充：

### 基础命令
- `/start` - 绑定账号/打开主菜单
- `/menu` - 打开主菜单
- `/help` - 显示帮助
- `/ping` - 检查Bot状态
- `/settings` - 账号设置

### 搜索功能
- `/search <关键词>` - 全局搜索
- 支持媒体类型：movie/tv/novel/manga/audiobook/music

### 影视订阅 (TG-BOT-2)
- `/subs` - 查看影视订阅
- `/sub_check <id>` - 手动检查订阅
- `/sub_toggle <id>` - 启用/停用订阅
- `/sub_search <关键字>` - 搜索并创建订阅

### 下载管理
- `/downloads` - 查看下载任务
- `/dl_pause <id>` - 暂停下载
- `/dl_resume <id>` - 恢复下载

### 音乐功能
- `/music_search <关键词>` - 音乐搜索
- `/music_sub` - 音乐订阅列表

### 阅读功能
- `/reading` - 阅读进度
- `/novel <id>` - 小说详情
- `/manga_follow` - 漫画追更列表

### 书架功能
- `/shelf` - 我的书架
- `/shelf_add <type> <id>` - 添加到书架

### 管理员命令
- `/admin` - 管理员菜单
- `/admin safety_status` - 安全策略状态
- `/admin health` - 系统健康
- `/admin runners` - Runner状态

---

## 系统统计（更新）

### 代码规模（最终统计）

| 类型 | 数量 |
|------|------|
| 后端API文件 | 140+ |
| 后端模块 | 70+ |
| 后端服务 | 50+ |
| 数据库模型 | 85+ |
| 后台任务 | 15+ |
| 前端页面 | 75+ |
| 前端组件 | 110+ |
| 文档文件 | 117+ |

### 主要功能模块数（更新）
1. **媒体管理**: 7大子系统（影视/音乐/漫画/小说/有声书/TTS/短剧）
2. **下载订阅**: 4大子系统（下载器/订阅/RSS/规则中心）
3. **站点搜索**: 4大子系统（站点管理/搜索引擎/CookieCloud/AI适配）
4. **文件存储**: 6大子系统（115网盘/STRM/文件浏览器/Inbox/存储监控/转移历史）
5. **智能系统**: 5大子系统（推荐/多模态/OCR/Local Intel/种子索引）
6. **安全系统**: 3大子系统（HNR检测/安全策略/做种管理）
7. **自动化**: 4大子系统（定时任务/工作流/后台Runner/Inbox自动导入）
8. **通知Bot**: 3大子系统（多渠道通知/Telegram Bot/告警系统）
9. **插件系统**: 3大子系统（Plugin Hub/Plugin SDK/事件系统）
10. **系统管理**: 8大子系统（设置/监控/日志/备份/更新/自检/运维/Demo模式）
11. **用户界面**: 8大子系统（仪表盘/发现页/日历/书架/作品中心/阅读中心/电视墙/榜单）
12. **外部集成**: 5大子系统（豆瓣/Bangumi/外部索引器/字幕服务/媒体服务器）

---

**报告完成**

此报告基于代码文件的逐一分析 + 117份项目文档的交叉对比生成，涵盖了VabHub系统的所有主要功能模块。每个功能都有对应的代码文件支撑，可以作为系统功能的完整参考。

### 文档对比发现的补充功能
- 短剧系统
- 统一收件箱 (Inbox)
- 统一阅读中心
- Demo 模式
- 订阅规则中心
- 媒体分类扩展
- 作品宇宙面板
- Local Intel 种子索引
- 运维监控增强
- 视频播放进度
- 115远程播放
- 电视墙
