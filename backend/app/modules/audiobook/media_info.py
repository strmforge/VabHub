"""
音频文件元数据解析工具

从音频文件中提取基础元数据信息（时长、码率、采样率、声道数等）。
使用 mutagen 库进行解析，如果未安装则优雅降级。
"""

from pathlib import Path
from typing import Optional, NamedTuple
from loguru import logger


class AudioMeta(NamedTuple):
    """音频元数据"""
    duration_seconds: Optional[int]
    bitrate_kbps: Optional[int]
    sample_rate_hz: Optional[int]
    channels: Optional[int]


def probe_audio_file(path: Path) -> AudioMeta:
    """
    尝试解析音频文件的基础信息，不抛异常。
    
    解析失败时，所有字段返回 None。
    
    Args:
        path: 音频文件路径
    
    Returns:
        AudioMeta: 包含 duration_seconds, bitrate_kbps, sample_rate_hz, channels
    """
    try:
        import mutagen
    except ImportError:
        # mutagen 未安装，返回空信息
        logger.debug(f"mutagen 未安装，跳过音频元数据解析: {path}")
        return AudioMeta(None, None, None, None)
    
    try:
        audio = mutagen.File(str(path))
        if audio is None:
            logger.debug(f"无法识别音频文件格式: {path}")
            return AudioMeta(None, None, None, None)
        
        # 获取音频信息
        info = audio.info
        
        # 时长（秒）
        duration = getattr(info, "length", None)
        duration_seconds = int(duration) if duration is not None else None
        
        # 比特率（通常以 bps 表示，转换为 kbps）
        bitrate = getattr(info, "bitrate", None)
        if bitrate is not None:
            # bitrate 可能是 bps，转换为 kbps
            bitrate_kbps = int(bitrate / 1000) if bitrate > 1000 else bitrate
        else:
            bitrate_kbps = None
        
        # 采样率（Hz）
        sample_rate = getattr(info, "sample_rate", None)
        sample_rate_hz = int(sample_rate) if sample_rate is not None else None
        
        # 声道数
        channels = getattr(info, "channels", None)
        channels = int(channels) if channels is not None else None
        
        logger.debug(
            f"音频元数据解析成功: {path} - "
            f"时长={duration_seconds}s, 码率={bitrate_kbps}kbps, "
            f"采样率={sample_rate_hz}Hz, 声道数={channels}"
        )
        
        return AudioMeta(
            duration_seconds=duration_seconds,
            bitrate_kbps=bitrate_kbps,
            sample_rate_hz=sample_rate_hz,
            channels=channels,
        )
        
    except Exception as e:
        # 解析失败，记录日志但不影响主流程
        logger.warning(f"解析音频文件元数据失败: {path}, 错误: {e}")
        return AudioMeta(None, None, None, None)

