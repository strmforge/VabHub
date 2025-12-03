from __future__ import annotations

from typing import Optional, Set

# === 基础媒体类型常量 ===
MEDIA_TYPE_MOVIE = "movie"
MEDIA_TYPE_TV = "tv"
MEDIA_TYPE_ANIME = "anime"
MEDIA_TYPE_MUSIC = "music"
MEDIA_TYPE_SHORT_DRAMA = "short_drama"
MEDIA_TYPE_EBOOK = "ebook"
MEDIA_TYPE_AUDIOBOOK = "audiobook"
MEDIA_TYPE_COMIC = "comic"
MEDIA_TYPE_UNKNOWN = "unknown"

# 统一的媒体类型集合（便于循环生成缓存键等场景）
MEDIA_TYPE_CHOICES: Set[str] = {
    MEDIA_TYPE_MOVIE,
    MEDIA_TYPE_TV,
    MEDIA_TYPE_ANIME,
    MEDIA_TYPE_MUSIC,
    MEDIA_TYPE_SHORT_DRAMA,
    MEDIA_TYPE_EBOOK,
    MEDIA_TYPE_AUDIOBOOK,
    MEDIA_TYPE_COMIC,
}

# === 派生集合 & 判断方法 ===
TV_LIKE_MEDIA_TYPES: Set[str] = {
    MEDIA_TYPE_TV,
    MEDIA_TYPE_SHORT_DRAMA,
}

SERIES_MEDIA_TYPES: Set[str] = TV_LIKE_MEDIA_TYPES | {MEDIA_TYPE_ANIME}


def normalize_media_type(value: Optional[str], default: str = MEDIA_TYPE_UNKNOWN) -> str:
    """
    统一媒体类型字符串，便于新增类型时集中管理。
    
    支持常见变体：
    - "ebook" / "EBOOK" / "Book" / "book" -> "ebook"
    - "movie" / "Movie" / "MOVIE" -> "movie"
    - 等等
    """
    if not value:
        return default
    lower_value = value.lower().strip()
    
    # 特殊映射：处理常见变体
    variant_map = {
        "book": MEDIA_TYPE_EBOOK,
        "books": MEDIA_TYPE_EBOOK,
        "电子书": MEDIA_TYPE_EBOOK,
        "audiobook": MEDIA_TYPE_AUDIOBOOK,
        "audio_book": MEDIA_TYPE_AUDIOBOOK,
        "audio book": MEDIA_TYPE_AUDIOBOOK,
        "有声书": MEDIA_TYPE_AUDIOBOOK,
        "有聲書": MEDIA_TYPE_AUDIOBOOK,
    }
    
    if lower_value in variant_map:
        return variant_map[lower_value]
    
    if lower_value in MEDIA_TYPE_CHOICES:
        return lower_value
    return default


def is_tv_like(value: Optional[str]) -> bool:
    """返回该媒体类型是否属于“剧集类”（电视剧 / 短剧）。"""
    return bool(value and value.lower() in TV_LIKE_MEDIA_TYPES)


def is_series_type(value: Optional[str]) -> bool:
    """返回该媒体类型是否属于“连载类”（剧集、短剧、动漫等）。"""
    return bool(value and value.lower() in SERIES_MEDIA_TYPES)


