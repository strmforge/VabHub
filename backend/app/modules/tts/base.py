"""
TTS 抽象层：定义协议与数据结构
"""

from pathlib import Path
from typing import Protocol, Optional
from pydantic import BaseModel


class TTSRequest(BaseModel):
    """TTS 请求"""
    text: str
    language: Optional[str] = None
    voice: Optional[str] = None
    speed: Optional[float] = None
    pitch: Optional[float] = None
    
    # 元信息，仅用于日志 / 命名，不参与请求体
    ebook_id: Optional[int] = None
    chapter_index: Optional[int] = None
    chapter_title: Optional[str] = None


class TTSResult:
    """TTS 结果"""
    def __init__(self, audio_path: Path, duration_seconds: Optional[int] = None):
        self.audio_path = audio_path
        self.duration_seconds = duration_seconds


class TTSEngine(Protocol):
    """TTS 引擎协议"""
    
    async def synthesize(self, request: TTSRequest, target_path: Path) -> TTSResult:
        """
        合成语音
        
        Args:
            request: TTS 请求
            target_path: 目标音频文件路径
        
        Returns:
            TTSResult: 包含音频路径和时长（可选）
        """
        ...

