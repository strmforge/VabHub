"""
通知类型枚举
"""
from enum import Enum


class NotificationType(str, Enum):
    """通知类型"""
    MANGA_NEW_CHAPTER = "MANGA_NEW_CHAPTER"
    # 预留后续：
    NOVEL_NEW_CHAPTER = "NOVEL_NEW_CHAPTER"
    AUDIOBOOK_NEW_TRACK = "AUDIOBOOK_NEW_TRACK"
    SYSTEM_MESSAGE = "SYSTEM_MESSAGE"
    # TTS/有声书相关：
    TTS_JOB_COMPLETED = "TTS_JOB_COMPLETED"   # TTS 任务完成
    TTS_JOB_FAILED = "TTS_JOB_FAILED"         # TTS 任务失败
    AUDIOBOOK_READY = "AUDIOBOOK_READY"       # 有声书整体就绪
    # 漫画追更相关：
    MANGA_UPDATED = "MANGA_UPDATED"           # 漫画更新通知
    MANGA_SYNC_FAILED = "MANGA_SYNC_FAILED"   # 漫画同步失败通知
    # 阅读相关通知：
    READING_EBOOK_IMPORTED = "READING_EBOOK_IMPORTED"  # 电子书导入完成
    # 音乐相关：
    MUSIC_CHART_UPDATED = "MUSIC_CHART_UPDATED"           # 音乐榜单更新
    MUSIC_NEW_TRACKS_QUEUED = "MUSIC_NEW_TRACKS_QUEUED"   # 新音乐任务已排队
    MUSIC_NEW_TRACKS_DOWNLOADING = "MUSIC_NEW_TRACKS_DOWNLOADING"  # 新音乐正在下载
    MUSIC_NEW_TRACKS_READY = "MUSIC_NEW_TRACKS_READY"     # 新音乐已就绪
    # 下载相关通知：
    DOWNLOAD_SUBSCRIPTION_MATCHED = "DOWNLOAD_SUBSCRIPTION_MATCHED"  # 订阅命中并创建下载任务
    DOWNLOAD_TASK_COMPLETED = "DOWNLOAD_TASK_COMPLETED"              # 下载任务完成
    DOWNLOAD_HR_RISK = "DOWNLOAD_HR_RISK"                            # HR/H&R 风险预警