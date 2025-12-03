"""
漫画源类型枚举
"""
from enum import Enum


class MangaSourceType(str, Enum):
    """漫画源类型"""
    OPDS = "OPDS"                 # Komga/Kavita 等都支持 OPDS
    SUWAYOMI = "SUWAYOMI"         # Suwayomi / Tachiyomi-Server 风格
    KOMGA = "KOMGA"               # 若未来直接对接 Komga API
    GENERIC_HTTP = "GENERIC_HTTP" # 预留：通用 HTTP 源

