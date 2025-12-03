"""
字幕模块
"""

from .service import SubtitleService
from .matcher import SubtitleMatcher
from .sources import OpenSubtitlesClient, SubHDClient, SubtitleSource
from .sources_shooter import ShooterClient

__all__ = ["SubtitleService", "SubtitleMatcher", "OpenSubtitlesClient", "SubHDClient", "ShooterClient", "SubtitleSource"]

