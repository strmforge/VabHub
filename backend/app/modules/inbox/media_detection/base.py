"""
媒体类型检测器基类

定义检测器接口和基础类型。
"""

from typing import Protocol, Optional, Literal, NamedTuple
from pathlib import Path

from app.modules.inbox.models import InboxItem

# 媒体类型字面量
MediaTypeLiteral = Literal[
    "movie", "tv", "anime", "music", "audiobook", 
    "ebook", "novel_txt", "comic", "unknown"
]


class MediaTypeGuess(NamedTuple):
    """
    媒体类型猜测结果
    """
    media_type: MediaTypeLiteral  # 猜测的媒体类型
    score: float  # 置信度分数（0.0-1.0）
    reason: str  # 判断原因


class MediaTypeDetector(Protocol):
    """
    媒体类型检测器协议
    
    所有检测器都应实现此接口。
    """
    
    name: str  # 检测器名称
    
    def guess(self, item: InboxItem) -> Optional[MediaTypeGuess]:
        """
        猜测文件的媒体类型
        
        Args:
            item: 待检测的项目
        
        Returns:
            Optional[MediaTypeGuess]: 如果无法判断，返回 None；否则返回猜测结果
        """
        ...

