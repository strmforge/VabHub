"""
媒体类型枚举
"""
from enum import Enum


class MediaType(str, Enum):
    """媒体类型枚举"""
    MOVIE = "movie"
    TV = "tv"
    SHORT_DRAMA = "short_drama"
    MUSIC = "music"
    BOOK = "book"
    ANIME = "anime"  # 保留现有类型

    @property
    def supports_strm(self) -> bool:
        """判断该媒体类型是否支持 STRM"""
        return self in {
            MediaType.MOVIE,
            MediaType.TV,
            MediaType.SHORT_DRAMA,
            MediaType.MUSIC,
            MediaType.ANIME,  # 保留现有行为
        }

