"""
通知分类体系

为用户通知系统提供分类功能，支持按类别过滤和统计
"""

from enum import Enum
from typing import Dict

from app.models.enums.notification_type import NotificationType


class NotificationCategory(str, Enum):
    """通知分类"""
    READING = "reading"      # 阅读相关：漫画、小说、有声书
    DOWNLOAD = "download"    # 下载相关：音乐下载、文件下载
    MUSIC = "music"          # 音乐相关：榜单更新、新音乐
    PLUGIN = "plugin"        # 插件相关：插件安装、更新、错误
    SYSTEM = "system"        # 系统相关：系统消息、版本更新、错误
    OTHER = "other"          # 其他未分类通知


# 通知类型到分类的映射
NOTIFICATION_TYPE_CATEGORY_MAP: Dict[NotificationType, NotificationCategory] = {
    # 阅读相关
    NotificationType.MANGA_NEW_CHAPTER: NotificationCategory.READING,
    NotificationType.NOVEL_NEW_CHAPTER: NotificationCategory.READING,
    NotificationType.AUDIOBOOK_NEW_TRACK: NotificationCategory.READING,
    NotificationType.MANGA_UPDATED: NotificationCategory.READING,
    NotificationType.MANGA_SYNC_FAILED: NotificationCategory.READING,
    NotificationType.READING_EBOOK_IMPORTED: NotificationCategory.READING,
    NotificationType.AUDIOBOOK_READY: NotificationCategory.READING,
    
    # TTS 相关（归类为阅读，因为与有声书相关）
    NotificationType.TTS_JOB_COMPLETED: NotificationCategory.READING,
    NotificationType.TTS_JOB_FAILED: NotificationCategory.READING,
    
    # 音乐相关
    NotificationType.MUSIC_CHART_UPDATED: NotificationCategory.MUSIC,
    NotificationType.MUSIC_NEW_TRACKS_QUEUED: NotificationCategory.MUSIC,
    NotificationType.MUSIC_NEW_TRACKS_DOWNLOADING: NotificationCategory.DOWNLOAD,
    NotificationType.MUSIC_NEW_TRACKS_READY: NotificationCategory.MUSIC,
    
    # 系统相关
    NotificationType.SYSTEM_MESSAGE: NotificationCategory.SYSTEM,
    
    # 下载相关
    NotificationType.DOWNLOAD_SUBSCRIPTION_MATCHED: NotificationCategory.DOWNLOAD,
    NotificationType.DOWNLOAD_TASK_COMPLETED: NotificationCategory.DOWNLOAD,
    NotificationType.DOWNLOAD_HR_RISK: NotificationCategory.DOWNLOAD,
}


def get_notification_category(notification_type: NotificationType) -> NotificationCategory:
    """
    根据通知类型获取分类
    
    Args:
        notification_type: 通知类型
        
    Returns:
        通知分类，未找到则返回 OTHER
    """
    return NOTIFICATION_TYPE_CATEGORY_MAP.get(notification_type, NotificationCategory.OTHER)


def get_types_by_category(category: NotificationCategory) -> list[NotificationType]:
    """
    根据分类获取所有相关的通知类型
    
    Args:
        category: 通知分类
        
    Returns:
        该分类下的所有通知类型列表
    """
    return [
        notification_type 
        for notification_type, cat in NOTIFICATION_TYPE_CATEGORY_MAP.items()
        if cat == category
    ]


# 获取所有分类及其包含的类型数量（用于统计展示）
CATEGORY_STATS = {
    category: len(get_types_by_category(category))
    for category in NotificationCategory
}


# 前端友好的分类显示名称
CATEGORY_DISPLAY_NAMES = {
    NotificationCategory.READING: "阅读",
    NotificationCategory.DOWNLOAD: "下载", 
    NotificationCategory.MUSIC: "音乐",
    NotificationCategory.PLUGIN: "插件",
    NotificationCategory.SYSTEM: "系统",
    NotificationCategory.OTHER: "其他"
}


# 分类对应的图标（用于前端显示）
CATEGORY_ICONS = {
    NotificationCategory.READING: "mdi-book-open-variant",
    NotificationCategory.DOWNLOAD: "mdi-download",
    NotificationCategory.MUSIC: "mdi-music",
    NotificationCategory.PLUGIN: "mdi-puzzle",
    NotificationCategory.SYSTEM: "mdi-cog",
    NotificationCategory.OTHER: "mdi-bell"
}


# 分类对应的颜色（用于前端显示）
CATEGORY_COLORS = {
    NotificationCategory.READING: "primary",
    NotificationCategory.DOWNLOAD: "success",
    NotificationCategory.MUSIC: "purple",
    NotificationCategory.PLUGIN: "orange",
    NotificationCategory.SYSTEM: "grey",
    NotificationCategory.OTHER: "blue-grey"
}
