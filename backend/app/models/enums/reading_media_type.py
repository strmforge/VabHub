"""
统一阅读媒体类型枚举
"""
from enum import Enum


class ReadingMediaType(str, Enum):
    """阅读媒体类型"""
    NOVEL = "NOVEL"          # 文本电子书/小说
    AUDIOBOOK = "AUDIOBOOK"  # 有声书
    MANGA = "MANGA"          # 漫画

