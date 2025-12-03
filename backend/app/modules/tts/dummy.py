"""
Dummy TTS 引擎（开发用）

不做真实 TTS 调用，只创建占位文件。
"""

from pathlib import Path
from typing import Optional
from loguru import logger
import wave
import struct

from .base import TTSRequest, TTSResult, TTSEngine
from .usage_tracker import record_success, record_error


class DummyTTSEngine:
    """Dummy TTS 引擎（开发用）"""
    
    async def synthesize(self, request: TTSRequest, target_path: Path) -> TTSResult:
        """
        合成语音（Dummy 实现）
        
        创建一个极短的 WAV 文件（1 秒静音）作为占位。
        """
        try:
            # 确保目录存在
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建 1 秒静音 WAV 文件
            sample_rate = 44100
            duration_seconds = 1
            num_samples = sample_rate * duration_seconds
            
            with wave.open(str(target_path), 'wb') as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                
                # 写入静音数据（全零）
                silence = struct.pack('h', 0) * num_samples
                wav_file.writeframes(silence)
            
            logger.info(
                f"[DummyTTSEngine] synthesize called for "
                f"ebook_id={request.ebook_id} chapter={request.chapter_index} "
                f"title={request.chapter_title}, output={target_path}"
            )
            
            result = TTSResult(
                audio_path=target_path,
                duration_seconds=duration_seconds
            )
            
            # 记录成功
            record_success(provider="dummy")
            
            return result
            
        except Exception as e:
            logger.error(f"[DummyTTSEngine] 创建占位文件失败: {e}", exc_info=True)
            # 如果 WAV 创建失败，尝试创建一个空文件
            try:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text("DUMMY AUDIO")
                logger.warning(f"[DummyTTSEngine] 已创建占位文本文件: {target_path}")
                
                result = TTSResult(audio_path=target_path, duration_seconds=None)
                
                # 记录成功（虽然降级了，但最终还是成功了）
                record_success(provider="dummy")
                
                return result
            except Exception as e2:
                logger.error(f"[DummyTTSEngine] 创建占位文件也失败: {e2}", exc_info=True)
                
                # 记录失败
                record_error(e2, provider="dummy")
                
                raise

