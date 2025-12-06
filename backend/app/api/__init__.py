"""
API路由模块
"""

from fastapi import APIRouter
from app.api import (
    auth,
    search,
    subscription,
    download,
    downloader,  # 下载器管理
    gateway,  # 网关签名
    ruleset,  # 规则集管理
    scraper,  # 刮削器管理
    secrets,  # 密钥管理
    dashboard,
    workflow,
    site,
    site_manager,  # 站点管理 (SITE-MANAGER-1)
    # notification,  # 通知API - 临时注释调试
    # notifications,  # 用户通知API - 临时注释调试
    # notifications_user,  # 用户通知API - 临时注释调试（FastAPI错误）
    calendar,
    music,  # VabHub特色功能：音乐管理
    media,  # 媒体搜索和TMDB集成
    media_search,  # TMDB搜索API（MEDIA-ORGANIZE-1）
    websocket,  # WebSocket实时更新
    settings,  # 系统设置
    hnr,  # HNR检测系统
    charts,  # 榜单系统（音乐+影视）
    recommendation,  # 推荐系统（整合过往版本）
    media_identification,  # 媒体识别（整合过往版本）
    health,  # 健康检查
    scheduler,  # 定时任务管理
    cloud_storage,  # 云存储（115网盘、RClone、OpenList）
    performance,  # 性能监控
    rss,  # RSS订阅
    media_renamer,  # 媒体文件重命名和整理
    subtitle,  # 字幕管理
    subtitle_settings,  # 字幕设置
    douban,  # 豆瓣API集成
    duplicate_detection,  # 重复文件检测
    quality_comparison,  # 文件质量比较
    seeding,  # 做种管理
    multimodal,
    storage,
    library,  # 媒体库（兼容性端点）
    tasks,  # 任务管理
    bangumi,  # Bangumi API集成
    log_center,  # 实时日志中心
    directory,  # 目录配置
    plugins,  # 插件热更新
    multimodal_metrics,  # 多模态分析性能监控
    multimodal_optimization,  # 多模态分析优化
    multimodal_history,  # 多模态分析历史数据和告警
    multimodal_auto_optimization,  # 多模态分析自动化优化
    media_server,  # 媒体服务器
    storage_monitor,  # 存储监控
    upload,  # 上传任务管理
    strm,  # STRM文件管理
    backup,  # 备份系统
    logs,  # 日志查看器
    file_cleaner,  # 文件清理
    file_browser,  # 文件浏览器
    transfer_history,  # 转移历史记录
    category,  # 分类配置管理
    system_update,  # 系统更新管理
    ocr,  # OCR功能
    subscription_refresh,  # 订阅刷新监控
    graphql,  # GraphQL API
    system_settings,  # 系统设置
    system_selfcheck,  # 系统自检
    scraping_switches,  # 刮削开关设置
    rsshub,  # RSSHub集成
    site_domain,  # 站点域名管理
    site_profile,  # 站点配置文件管理
    monitoring,  # 系统监控
    decision,  # 下载决策调试
    intel,  # Local Intel 系统
    tvwall_smart_open,  # 电视墙智能打开 (TVWALL-LOCAL-LIB-PLAY-1)
    global_rules,  # 全局规则设置 (SETTINGS-RULES-1)API（Phase 6）
    local_intel_admin,
    external_indexer_debug,  # 外部索引桥接调试
    ext_indexer,  # 外部索引管理
    site_ai_adapter,  # 站点 AI 适配管理
    smart_health,  # 智能子系统健康检查
    ebook,  # 电子书管理
    audiobook,  # 有声书管理
    novel_demo,  # 小说导入 Demo（开发用）
    inbox_dev,  # 统一收件箱 Dev API
    tts_regen,  # TTS 重新生成 Dev API
    tts_jobs,  # TTS Jobs Dev API
    tts_work_profile,  # TTS 作品级配置 Dev API
    tts_voice_presets,  # TTS 声线预设 Dev API
    tts_work_batch,  # TTS 作品批量应用预设 Dev API
    admin_library_settings,  # 媒体库设置管理（只读）
    admin_tts_settings,  # TTS 设置管理（只读）
    tts_playground,  # TTS Playground Dev API
    tts_user_flow,  # 用户版 TTS Flow API
    tts_user_batch,  # 用户批量 TTS API
    tts_storage,  # TTS 存储管理 Dev API
    # notifications_user,  # 用户通知 API - 临时注释调试（FastAPI错误）
    work,  # 作品中心（Work Hub）
    work_links,  # 作品关联管理（Work Link）
    audiobooks,  # 有声书文件播放 API
    user_audiobooks,  # 用户有声书播放进度 API
    # video_progress,  # 视频播放进度 API - 临时注释调试（FastAPI错误）
    novel_center,  # 小说中心聚合 API
    novel_inbox,  # 小说 Inbox 管理 API
    audiobook_center,  # 有声书中心聚合 API
    novel_reader,  # 小说阅读器 API
    my_shelf,  # 我的书架 API
    remote_video_115,  # 115 远程视频播放 API
    # player_wall,  # 电视墙 API - 临时注释调试（缺少media_file模块）
    manga_source_admin,  # 漫画源管理 API
    manga_remote,  # 远程漫画浏览 API
    manga_local,  # 本地漫画库 API
    manga_progress,  # 漫画阅读进度 API
    manga_sync,  # 漫画同步 API
    manga_follow,  # 漫画追更 API
    reading_hub,  # 阅读中心 API
    # music_chart_admin,  # 音乐榜单管理 API - 临时注释调试（缺少get_async_session）
    # music_subscription,  # 音乐订阅 API - 临时注释调试（缺少get_async_session）
    home,  # 首页仪表盘 API
    task_center,  # 任务中心 API
    admin_status,  # 系统运维状态 API
    global_search,  # 全局搜索 API
    config_admin,  # 配置管理 API
    onboarding,  # Onboarding API
    version,  # 版本信息 API
    system_health,  # 系统健康检查 API
    alert_channels,  # 告警渠道 API
    user_notify_channels,  # 用户通知渠道 API
    user_telegram,  # Telegram 绑定 API
    notify_preferences,  # 通知偏好 API
    # notify_test,  # 通知测试 API - 暂时禁用，等待修复
    self_check,  # 自检 API
    plugin_admin,  # 插件管理 API
    plugin_config,  # 插件配置 API（PLUGIN-UX-3）
    plugin_api,  # 插件对外 API（PLUGIN-UX-3）
    workflow_extensions,  # Workflow 扩展 API
    plugin_panels,  # 插件面板 API
    plugin_hub,  # Plugin Hub API
    cookiecloud,  # CookieCloud API (COOKIECLOUD-1)
    subscription_defaults,  # 默认订阅配置 API (SUBS-RULES-1 P2)
    filter_rule_groups,  # 过滤规则组 API (SUBS-RULES-1 P3)
    ai_orchestrator,  # AI Orchestrator API (FUTURE-AI-ORCHESTRATOR-1)
    ai_subs_workflow,  # AI 订阅工作流 API (FUTURE-AI-SUBS-WORKFLOW-1)
    ai_log_doctor,  # AI 故障医生 API (FUTURE-AI-LOG-DOCTOR-1)
    ai_cleanup_advisor,  # AI 整理顾问 API (FUTURE-AI-CLEANUP-ADVISOR-1)
    ai_reading_assistant,  # AI 阅读助手 API (FUTURE-AI-READING-ASSISTANT-1)
    admin_system,  # 系统管理 API (DEPLOY-UPGRADE-1)
)

# 创建主API路由器
api_router = APIRouter()

# 注册各个功能模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(search.router, prefix="/search", tags=["搜索"])
api_router.include_router(rss.router, prefix="/rss", tags=["RSS订阅"])
api_router.include_router(subscription.router, prefix="/subscriptions", tags=["订阅"])
api_router.include_router(download.router, prefix="/downloads", tags=["下载"])
api_router.include_router(downloader.router, tags=["下载器管理"])  # 下载器管理（路由已包含/dl前缀）
api_router.include_router(gateway.router, tags=["网关"])  # 网关签名（路由已包含/gateway前缀）
api_router.include_router(ruleset.router, tags=["规则集"])  # 规则集管理（路由已包含/ruleset前缀）
api_router.include_router(scraper.router, tags=["刮削器"])  # 刮削器管理（路由已包含/scraper前缀）
api_router.include_router(secrets.router, tags=["密钥管理"])  # 密钥管理（路由已包含/secrets前缀）
api_router.include_router(tasks.router, prefix="/tasks", tags=["任务管理"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["仪表盘"])
api_router.include_router(workflow.router, prefix="/workflows", tags=["工作流"])
api_router.include_router(site.router, prefix="/sites", tags=["站点管理"])
# api_router.include_router(notification.router, prefix="/notifications", tags=["通知"])  # 暂时禁用，等待修复
# api_router.include_router(notifications.router, prefix="/api/notifications", tags=["用户通知"])  # 暂时禁用，存在Schema冲突
api_router.include_router(calendar.router, prefix="/calendar", tags=["日历"])
api_router.include_router(music.router, prefix="/music", tags=["音乐"])  # VabHub特色功能
api_router.include_router(media.router, prefix="/media", tags=["媒体"])  # 媒体搜索和TMDB集成
api_router.include_router(media_search.router, prefix="/media", tags=["媒体搜索"])  # TMDB搜索API（MEDIA-ORGANIZE-1）
api_router.include_router(settings.router, prefix="/settings", tags=["系统设置"])
api_router.include_router(hnr.router, prefix="/hnr", tags=["HNR检测"])  # HNR检测系统
api_router.include_router(charts.router, prefix="/charts", tags=["榜单"])  # 榜单系统（音乐+影视）
api_router.include_router(recommendation.router, prefix="/recommendations", tags=["推荐"])  # 推荐系统（整合过往版本）
api_router.include_router(media_identification.router, prefix="/media-identification", tags=["媒体识别"])  # 媒体识别（整合过往版本）
api_router.include_router(health.router, prefix="/health", tags=["健康检查"])  # 健康检查系统
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["定时任务"])  # 定时任务管理
api_router.include_router(cloud_storage.router, prefix="/cloud-storage", tags=["云存储"])  # 云存储（115网盘、RClone、OpenList）
api_router.include_router(performance.router, tags=["性能监控"])  # 性能监控（路由已包含/performance前缀）
api_router.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])  # WebSocket实时更新
api_router.include_router(media_renamer.router, prefix="/media-renamer", tags=["媒体文件管理"])  # 媒体文件重命名和整理
api_router.include_router(subtitle.router, prefix="/subtitle", tags=["字幕管理"])  # 字幕管理（注意：路由前缀是/subtitle，不是/subtitles）
api_router.include_router(subtitle_settings.router, prefix="/subtitle-settings", tags=["字幕设置"])  # 字幕设置
api_router.include_router(douban.router, prefix="/douban", tags=["豆瓣"])  # 豆瓣API集成
api_router.include_router(duplicate_detection.router, prefix="/duplicate-detection", tags=["重复文件检测"])  # 重复文件检测
api_router.include_router(quality_comparison.router, prefix="/quality-comparison", tags=["文件质量比较"])  # 文件质量比较
api_router.include_router(seeding.router, prefix="/seeding", tags=["做种管理"])  # 做种管理
api_router.include_router(decision.router, prefix="/decision", tags=["下载决策"])
api_router.include_router(multimodal.router, prefix="/multimodal", tags=["多模态分析"])  # 多模态分析
api_router.include_router(multimodal_metrics.router, prefix="/multimodal/metrics", tags=["多模态分析性能监控"])  # 多模态分析性能监控
api_router.include_router(multimodal_optimization.router, prefix="/multimodal/optimization", tags=["多模态分析优化"])  # 多模态分析优化
api_router.include_router(multimodal_history.router, prefix="/multimodal/history", tags=["多模态分析历史数据和告警"])  # 多模态分析历史数据和告警
api_router.include_router(multimodal_auto_optimization.router, prefix="/multimodal/auto-optimization", tags=["多模态分析自动化优化"])  # 多模态分析自动化优化
api_router.include_router(media_server.router, prefix="/media-servers", tags=["媒体服务器"])  # 媒体服务器
api_router.include_router(library.router, prefix="/library", tags=["媒体库"])  # 媒体库（兼容性端点）
api_router.include_router(storage_monitor.router, prefix="/storage-monitor", tags=["存储监控"])  # 存储监控
api_router.include_router(storage.router, prefix="/storage", tags=["存储管理"])  # 存储管理（状态和配置）
api_router.include_router(upload.router, tags=["上传任务"])  # 上传任务管理
api_router.include_router(strm.router, tags=["STRM"])  # STRM文件管理（路由已包含/strm前缀）
api_router.include_router(directory.router, prefix="/directories", tags=["目录配置"])  # 目录配置
api_router.include_router(plugins.router, prefix="/plugins", tags=["插件管理"])  # 插件热更新
api_router.include_router(backup.router, tags=["备份"])  # 备份系统（路由已包含/backup前缀）
api_router.include_router(logs.router, tags=["日志"])  # 日志查看器（路由已包含/logs前缀）
api_router.include_router(file_cleaner.router, tags=["文件清理"])  # 文件清理（路由已包含/file-cleaner前缀）
api_router.include_router(file_browser.router, tags=["文件浏览器"])  # 文件浏览器（路由已包含/file-browser前缀）
api_router.include_router(transfer_history.router, tags=["转移历史"])  # 转移历史记录（路由已包含/transfer-history前缀）
api_router.include_router(category.router, tags=["分类配置"])  # 分类配置管理（路由已包含/category前缀）
api_router.include_router(system_update.router, tags=["系统更新"])  # 系统更新管理（路由已包含/system前缀）
# 注意: site.router 已在上方 line 172 以 prefix="/sites" 注册，此处不再重复注册
# api_router.include_router(site.router)  # 重复注册会导致 /{site_id} 路由捕获所有顶层路径
api_router.include_router(site_manager.router, prefix="/sites", tags=["站点管理"])  # 站点管理 (SITE-MANAGER-1)
api_router.include_router(subscription_refresh.router)  # 订阅刷新监控（路由已包含/subscription-refresh前缀）
api_router.include_router(log_center.router)  # 实时日志中心（路由已包含/log-center前缀）
api_router.include_router(graphql.router)  # GraphQL API（路由已包含/graphql前缀）
api_router.include_router(bangumi.router, prefix="/bangumi", tags=["Bangumi"])  # Bangumi API集成
api_router.include_router(system_settings.router)  # 系统设置（路由已包含/system前缀）
api_router.include_router(scraping_switches.router)  # 刮削开关设置（路由已包含/system/setting前缀）
api_router.include_router(rsshub.router, prefix="/rsshub", tags=["RSSHub"])  # RSSHub集成
api_router.include_router(site_domain.router, tags=["站点域名管理"])  # 站点域名管理（路由已包含/sites/{site_id}/domains前缀）
api_router.include_router(site_profile.router, tags=["站点配置文件"])  # 站点配置文件管理（路由已包含/sites/{site_id}/profile前缀）
api_router.include_router(monitoring.router)  # 系统监控（路由已包含/monitoring前缀）
api_router.include_router(system_selfcheck.router, prefix="/system", tags=["系统自检"])
api_router.include_router(intel.router)  # Local Intel API（路由已包含/intel前缀）
api_router.include_router(local_intel_admin.router)
api_router.include_router(global_rules.router, prefix="/api/settings/rules", tags=["全局规则"])  # 全局规则设置 (SETTINGS-RULES-1)
api_router.include_router(external_indexer_debug.router)  # 外部索引桥接调试（路由已包含/api/debug/ext-indexer前缀）
api_router.include_router(ext_indexer.router)  # 外部索引管理（路由已包含/api/ext-indexer前缀）
api_router.include_router(site_ai_adapter.router)  # 站点 AI 适配管理（路由已包含/api/admin/site-ai-adapter前缀）
api_router.include_router(smart_health.router, prefix="/smart", tags=["智能子系统"])  # 智能子系统健康检查
api_router.include_router(ebook.router, prefix="/ebooks", tags=["电子书管理"])  # 电子书管理
api_router.include_router(audiobook.router, prefix="/audiobooks", tags=["有声书管理"])  # 有声书管理
api_router.include_router(novel_demo.router, prefix="/dev/novel", tags=["小说导入Demo"])  # 小说导入 Demo（开发用）
api_router.include_router(inbox_dev.router, prefix="/dev/inbox", tags=["统一收件箱Dev"])  # 统一收件箱 Dev API
api_router.include_router(tts_regen.router, prefix="/dev/tts", tags=["TTS重新生成"])  # TTS 重新生成 Dev API
api_router.include_router(tts_jobs.router, prefix="/dev/tts/jobs", tags=["TTS任务管理"])  # TTS Jobs Dev API
api_router.include_router(tts_work_profile.router, prefix="/dev/tts", tags=["TTS作品配置"])  # TTS 作品级配置 Dev API
api_router.include_router(tts_voice_presets.router, prefix="/dev/tts", tags=["TTS声线预设"])  # TTS 声线预设 Dev API
api_router.include_router(tts_work_batch.router, prefix="/dev/tts", tags=["TTS批量应用"])  # TTS 作品批量应用预设 Dev API
api_router.include_router(admin_library_settings.router, prefix="/admin/settings/library", tags=["媒体库设置"])  # 媒体库设置管理（只读）
api_router.include_router(admin_tts_settings.router, prefix="/admin/settings/tts", tags=["TTS设置"])  # TTS 设置管理（只读）
api_router.include_router(tts_playground.router, prefix="/dev/tts", tags=["TTS Dev"])  # TTS Playground Dev API
api_router.include_router(tts_user_flow.router, prefix="/tts", tags=["TTS"])  # 用户版 TTS Flow API
api_router.include_router(tts_user_batch.router, prefix="/tts/batch", tags=["TTS"])  # 用户批量 TTS API
api_router.include_router(tts_storage.router, prefix="/dev", tags=["TTS存储（Dev）"])  # TTS 存储管理 Dev API
# api_router.include_router(notifications_user.router, prefix="/user/notifications", tags=["用户通知"])  # 暂时禁用，存在Schema冲突
api_router.include_router(work.router, prefix="/work", tags=["作品中心"])  # 作品中心（Work Hub）
api_router.include_router(work_links.router, tags=["作品关联管理"])  # 作品关联管理（Work Link）
api_router.include_router(audiobooks.router, prefix="/audiobooks", tags=["有声书播放"])  # 有声书文件播放 API
api_router.include_router(user_audiobooks.router, prefix="/user/audiobooks", tags=["用户有声书"])  # 用户有声书播放进度 API
# api_router.include_router(video_progress.router, prefix="/api/video-progress", tags=["视频播放进度"])  # 暂时禁用，存在Schema冲突
api_router.include_router(novel_center.router, prefix="/novels/center", tags=["小说中心"])  # 小说中心聚合 API
api_router.include_router(novel_inbox.router, prefix="/api", tags=["小说 Inbox（Dev）"])  # 小说 Inbox 管理 API
api_router.include_router(audiobook_center.router, prefix="/audiobooks", tags=["有声书中心"])  # 有声书中心聚合 API
api_router.include_router(novel_reader.router, prefix="/api", tags=["小说阅读器"])  # 小说阅读器 API
api_router.include_router(my_shelf.router, prefix="/user", tags=["我的书架"])  # 我的书架 API
api_router.include_router(remote_video_115.router, prefix="/api", tags=["115远程播放"])  # 115 远程视频播放 API
# api_router.include_router(player_wall.router, prefix="/api/player", tags=["电视墙"])  # 暂时禁用，缺少media_file模块
api_router.include_router(manga_source_admin.router, tags=["漫画源管理"])  # 漫画源管理 API（路由已包含前缀）
api_router.include_router(manga_remote.router, tags=["远程漫画"])  # 远程漫画浏览 API（路由已包含前缀）
api_router.include_router(manga_local.router, tags=["本地漫画库"])  # 本地漫画库 API（路由已包含前缀）
api_router.include_router(manga_progress.router, tags=["漫画阅读进度"])  # 漫画阅读进度 API（路由已包含前缀）
api_router.include_router(manga_sync.router, tags=["漫画同步"])  # 漫画同步 API（路由已包含前缀）
api_router.include_router(manga_follow.router, tags=["漫画追更"])  # 漫画追更 API（路由已包含前缀）
api_router.include_router(reading_hub.router, tags=["阅读中心"])  # 阅读中心 API（路由已包含前缀）
# api_router.include_router(music_chart_admin.router, tags=["音乐榜单管理"])  # 暂时禁用，缺少get_async_session
# api_router.include_router(music_subscription.router, tags=["音乐订阅"])  # 暂时禁用，缺少get_async_session
api_router.include_router(home.router, tags=["首页"])  # 首页仪表盘 API（路由已包含前缀）
api_router.include_router(task_center.router, tags=["任务中心"])  # 任务中心 API（路由已包含前缀）
api_router.include_router(admin_status.router, tags=["系统运维"])  # 系统运维状态 API（路由已包含前缀）
api_router.include_router(global_search.router, tags=["全局搜索"])  # 全局搜索 API（路由已包含前缀）
api_router.include_router(config_admin.router, tags=["配置管理"])  # 配置管理 API（路由已包含前缀）
api_router.include_router(onboarding.router, tags=["Onboarding"])  # Onboarding API（路由已包含前缀）
api_router.include_router(version.router, tags=["版本"])  # 版本信息 API
api_router.include_router(system_health.router, tags=["系统健康"])  # 系统健康检查 API
api_router.include_router(alert_channels.router, tags=["告警渠道"])  # 告警渠道 API
api_router.include_router(user_notify_channels.router, tags=["用户通知渠道"])  # 用户通知渠道 API
api_router.include_router(user_telegram.router, tags=["Telegram绑定"])  # Telegram 绑定 API
api_router.include_router(notify_preferences.router, tags=["通知偏好"])  # 通知偏好 API（路由已包含前缀）
# api_router.include_router(notify_test.router, tags=["通知测试"])  # 通知测试 API - 暂时禁用，等待修复
api_router.include_router(self_check.router, tags=["自检"])  # 自检 API（路由已包含前缀）
api_router.include_router(plugin_admin.router, tags=["插件管理"])  # 插件管理 API（路由已包含前缀）
api_router.include_router(plugin_config.router, tags=["插件配置"])  # 插件配置 API（PLUGIN-UX-3）
api_router.include_router(plugin_api.router, tags=["插件API"])  # 插件对外 API（PLUGIN-UX-3）
api_router.include_router(workflow_extensions.router, tags=["Workflow扩展"])  # Workflow 扩展 API（路由已包含前缀）
api_router.include_router(plugin_panels.router, tags=["插件面板"])  # 插件面板 API（路由已包含前缀）
api_router.include_router(plugin_hub.router, tags=["Plugin Hub"])  # Plugin Hub API（路由已包含前缀）
api_router.include_router(cookiecloud.router, tags=["CookieCloud"])  # CookieCloud API (COOKIECLOUD-1)
api_router.include_router(subscription_defaults.router, tags=["默认订阅配置"])  # 默认订阅配置 API (SUBS-RULES-1 P2)
api_router.include_router(filter_rule_groups.router, tags=["过滤规则组"])  # 过滤规则组 API (SUBS-RULES-1 P3)
api_router.include_router(ai_orchestrator.router, prefix="/ai/orchestrator", tags=["AI Orchestrator"])  # AI 总控 API (FUTURE-AI-ORCHESTRATOR-1)
api_router.include_router(ai_subs_workflow.router, tags=["AI 订阅工作流"])  # AI 订阅工作流 API (FUTURE-AI-SUBS-WORKFLOW-1)
api_router.include_router(ai_log_doctor.router, tags=["AI 故障医生"])  # AI 故障医生 API (FUTURE-AI-LOG-DOCTOR-1)
api_router.include_router(ai_cleanup_advisor.router, tags=["AI 整理顾问"])  # AI 整理顾问 API (FUTURE-AI-CLEANUP-ADVISOR-1)
api_router.include_router(ai_reading_assistant.router, tags=["AI 阅读助手"])  # AI 阅读助手 API (FUTURE-AI-READING-ASSISTANT-1)
api_router.include_router(admin_system.router, tags=["系统管理"])  # 系统管理 API (DEPLOY-UPGRADE-1)
