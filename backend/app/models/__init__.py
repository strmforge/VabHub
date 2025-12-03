"""
数据模型
"""

from app.models.user import User
from app.models.media import Media, MediaFile
from app.models.subscription import Subscription
from app.models.subscription_history import SubscriptionHistory
from app.models.download import DownloadTask
from app.models.upload import UploadTask, UploadProgress, UploadTaskStatus
from app.models.workflow import Workflow, WorkflowExecution
from app.models.site import Site
from app.models.site_icon import SiteIcon
from app.models.site_domain import SiteDomainConfig
from app.models.ai_site_adapter import AISiteAdapter
from app.models.notification import Notification
from app.models.music import Music, MusicFile, MusicSubscription, MusicTrack, MusicPlaylist, MusicLibrary  # VabHub特色功能（包含统一收件箱导入）
from app.models.search_history import SearchHistory
from app.models.settings import SystemSetting
from app.models.hnr import HNRDetection, HNRTask, HNRSignature
from app.models.cache import CacheEntry  # L3数据库缓存
from app.models.identification_history import IdentificationHistory  # 媒体识别历史记录
from app.models.cloud_storage import CloudStorage, CloudStorageAuth  # 云存储
from app.models.rss_subscription import RSSSubscription, RSSItem  # RSS订阅
from app.models.rsshub_simple import RSSHubSource, RSSHubComposite, UserRSSHubSubscription  # RSSHub集成（简化版本）
from app.models.subtitle import Subtitle, SubtitleDownloadHistory  # 字幕
from app.models.multimodal_metrics import (
    MultimodalPerformanceMetric,
    MultimodalPerformanceAlert,
    MultimodalOptimizationHistory
)  # 多模态分析性能指标
from app.models.media_server import (
    MediaServer,
    MediaServerSyncHistory,
    MediaServerItem,
    MediaServerPlaybackSession
)  # 媒体服务器
from app.models.scheduler_task import (
    SchedulerTask,
    SchedulerTaskExecution
)  # 调度器任务
from app.models.storage_monitor import (
    StorageDirectory,
    StorageUsageHistory,
    StorageAlert
)  # 存储监控
from app.models.strm import (
    STRMWorkflowTask,
    STRMFile,
    STRMFileTree,
    STRMLifeEvent,
    STRMConfig
)  # STRM文件生成系统
from app.models.directory import Directory  # 目录配置
from app.models.dashboard import DashboardLayout, DashboardWidget  # 仪表盘布局
from app.models.backup import BackupRecord  # 备份记录
from app.models.transfer_history import TransferHistory  # 转移历史记录
from app.models.intel_local import (
    HRCase,
    SiteGuardProfile,
    InboxEvent,
    SiteGuardEvent,
    InboxCursor,
    TorrentIndex,
)  # Local Intel
from app.models.ai_site_adapter import AISiteAdapter  # 站点 AI 适配配置
from app.models.inbox import InboxRunLog  # 统一收件箱运行日志
from app.models.ebook import EBook, EBookFile  # 电子书
from app.models.audiobook import AudiobookFile  # 有声书
from app.models.comic import Comic, ComicFile  # 漫画
from app.models.tts_job import TTSJob  # TTS 任务
from app.models.tts_work_profile import TTSWorkProfile  # TTS 作品级配置
from app.models.tts_voice_preset import TTSVoicePreset  # TTS 声线预设
from app.models.tts_storage_cleanup_log import TTSStorageCleanupLog  # TTS 存储清理日志
from app.models.user_audiobook_progress import UserAudiobookProgress  # 用户有声书播放进度
from app.models.user_novel_reading_progress import UserNovelReadingProgress  # 用户小说阅读进度
from app.models.novel_inbox_import_log import NovelInboxImportLog  # 小说 Inbox 导入日志
from app.models.user_notification import UserNotification  # 用户通知
from app.models.manga_source import MangaSource  # 漫画源配置
from app.models.manga_series_local import MangaSeriesLocal  # 本地漫画系列
from app.models.manga_chapter_local import MangaChapterLocal  # 本地漫画章节
from app.models.manga_reading_progress import MangaReadingProgress  # 漫画阅读进度
from app.models.manga_download_job import MangaDownloadJob  # 漫画下载任务
from app.models.user_favorite_media import UserFavoriteMedia  # 用户收藏媒体
from app.models.user_manga_follow import UserMangaFollow  # 用户漫画追更
from app.models.music_chart_source import MusicChartSource  # 音乐榜单源
from app.models.music_chart import MusicChart  # 音乐榜单
from app.models.music_chart_item import MusicChartItem  # 音乐榜单条目
from app.models.user_music_subscription import UserMusicSubscription  # 用户音乐订阅
from app.models.music_download_job import MusicDownloadJob  # 音乐下载任务
from app.models.user_notify_preference import UserNotifyPreference  # 用户通知偏好
from app.models.user_notify_snooze import UserNotifySnooze  # 用户通知静音
from app.models.plugin import Plugin, PluginStatus  # 插件系统
from app.models.plugin_config import PluginConfig  # 插件配置（PLUGIN-UX-3）

__all__ = [
    "User",
    "Media",
    "MediaFile",
    "Subscription",
    "DownloadTask",
    "UploadTask",  # 上传任务
    "UploadProgress",  # 上传进度
    "UploadTaskStatus",  # 上传任务状态
    "Workflow",
    "WorkflowExecution",
    "Site",
    "Notification",
    "MusicSubscription",  # VabHub特色功能
    "MusicTrack",
    "RSSSubscription",  # RSS订阅
    "RSSItem",  # RSS项
    "Subtitle",  # 字幕
    "SubtitleDownloadHistory",  # 字幕下载历史
    "MusicPlaylist",
    "MusicLibrary",
    "SearchHistory",
    "SystemSetting",
    "HNRDetection",
    "HNRTask",
    "HNRSignature",
    "CacheEntry",  # L3数据库缓存
    "IdentificationHistory",  # 媒体识别历史记录
    "CloudStorage",  # 云存储
    "CloudStorageAuth",  # 云存储认证
    "MultimodalPerformanceMetric",  # 多模态分析性能指标
    "MultimodalPerformanceAlert",  # 多模态分析性能告警
    "MultimodalOptimizationHistory",  # 多模态分析优化历史
    "MediaServer",  # 媒体服务器
    "MediaServerSyncHistory",  # 媒体服务器同步历史
    "MediaServerItem",  # 媒体服务器媒体项
    "MediaServerPlaybackSession",  # 媒体服务器播放会话
    "SchedulerTask",  # 调度器任务
    "SchedulerTaskExecution",  # 调度器任务执行历史
    "StorageDirectory",  # 存储目录
    "StorageUsageHistory",  # 存储使用历史
    "StorageAlert",  # 存储预警
    "STRMWorkflowTask",  # STRM工作流任务
    "STRMFile",  # STRM文件记录
    "STRMFileTree",  # STRM文件树记录
    "STRMLifeEvent",  # STRM生命周期事件
    "STRMConfig",  # STRM系统配置
    "Directory",  # 目录配置
    "DashboardLayout",  # 仪表盘布局
    "DashboardWidget",  # 仪表盘组件
    "BackupRecord",  # 备份记录
    "TransferHistory",  # 转移历史记录
    "RSSHubSource",  # RSSHub源
    "RSSHubComposite",  # RSSHub组合订阅
    "UserRSSHubSubscription",  # 用户RSSHub订阅状态
    "SiteIcon",  # 站点图标
    "SiteDomainConfig",  # 站点域名配置
    "SubscriptionHistory",  # 订阅历史记录
    "HRCase",  # Local Intel HR 案例
    "SiteGuardProfile",  # Local Intel 站点防护配置
    "InboxEvent",  # Local Intel 站内信事件
    "SiteGuardEvent",  # Local Intel 风控事件
    "InboxCursor",  # Local Intel 站内信游标
    "TorrentIndex",  # Local Intel PT 种子索引（Phase 9）
    "AISiteAdapter",  # 站点 AI 适配配置
    "EBook",  # 电子书
    "EBookFile",  # 电子书文件
    "AudiobookFile",  # 有声书文件
    "Comic",  # 漫画
    "ComicFile",  # 漫画文件
    "Music",  # 音乐
    "MusicFile",  # 音乐文件
    "TTSJob",  # TTS 任务
    "TTSWorkProfile",  # TTS 作品级配置
    "TTSVoicePreset",  # TTS 声线预设
    "TTSStorageCleanupLog",  # TTS 存储清理日志
    "UserAudiobookProgress",  # 用户有声书播放进度
    "UserNovelReadingProgress",  # 用户小说阅读进度
    "NovelInboxImportLog",  # 小说 Inbox 导入日志
    "UserNotification",  # 用户通知
    "MangaSource",  # 漫画源配置
    "MangaSeriesLocal",  # 本地漫画系列
    "MangaChapterLocal",  # 本地漫画章节
    "MangaReadingProgress",  # 漫画阅读进度
    "MangaDownloadJob",  # 漫画下载任务
    "UserFavoriteMedia",  # 用户收藏媒体
    "UserMangaFollow",  # 用户漫画追更
    "MusicChartSource",  # 音乐榜单源
    "MusicChart",  # 音乐榜单
    "MusicChartItem",  # 音乐榜单条目
    "UserMusicSubscription",  # 用户音乐订阅
    "MusicDownloadJob",  # 音乐下载任务
    "UserNotifyPreference",  # 用户通知偏好
    "UserNotifySnooze",  # 用户通知静音
    "Plugin",  # 插件
    "PluginStatus",  # 插件状态
    "PluginConfig",  # 插件配置（PLUGIN-UX-3）
    "PluginAuditLog",  # 插件审计日志（PLUGIN-SAFETY-1）
]

