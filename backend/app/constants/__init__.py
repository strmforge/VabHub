"""
应用级常量模块。

目前主要用于集中管理媒体类型相关的常量，避免在不同模块中硬编码字符串。
"""

from .media_types import (  # noqa: F401
    MEDIA_TYPE_ANIME,
    MEDIA_TYPE_MOVIE,
    MEDIA_TYPE_MUSIC,
    MEDIA_TYPE_SHORT_DRAMA,
    MEDIA_TYPE_TV,
    MEDIA_TYPE_UNKNOWN,
    MEDIA_TYPE_CHOICES,
    SERIES_MEDIA_TYPES,
    TV_LIKE_MEDIA_TYPES,
    is_series_type,
    is_tv_like,
    normalize_media_type,
)


