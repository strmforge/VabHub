"""
音频分析器
提供音频内容分析功能（简化版）
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from loguru import logger
import subprocess
import json
import os
from datetime import datetime
import hashlib
import asyncio
import time

# 可选依赖：librosa用于音频特征提取
try:
    import librosa
    import numpy as np
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("librosa未安装，音频特征提取功能将不可用")

# 导入缓存系统
try:
    from app.core.cache import get_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.warning("缓存系统不可用，将跳过缓存")

# 导入性能监控
try:
    from app.modules.multimodal.metrics import MultimodalMetrics
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    logger.warning("性能监控系统不可用，将跳过性能监控")


class AudioAnalyzer:
    """音频分析器（简化版，使用MediaInfo和FFmpeg）"""
    
    def __init__(self, enable_cache: bool = True, cache_ttl: int = 86400, max_concurrent: int = 3):
        """
        初始化音频分析器
        
        Args:
            enable_cache: 是否启用缓存
            cache_ttl: 缓存过期时间（秒，默认24小时）
            max_concurrent: 最大并发分析数（默认3）
        """
        self.ffmpeg_path = self._find_ffmpeg()
        self.mediainfo_path = self._find_mediainfo()
        self.enable_cache = enable_cache and CACHE_AVAILABLE
        self.cache_ttl = cache_ttl
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._current_concurrent = 0  # 当前并发数
        
        if self.enable_cache:
            self.cache = get_cache()
            logger.info(f"音频分析器已启用缓存（TTL: {cache_ttl}秒）")
    
    def _find_ffmpeg(self) -> Optional[str]:
        """查找FFmpeg路径"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return "ffmpeg"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # 尝试常见路径
        common_paths = [
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "C:\\ffmpeg\\bin\\ffmpeg.exe",
            "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        logger.warning("FFmpeg未找到，部分音频分析功能可能不可用")
        return None
    
    def _find_mediainfo(self) -> Optional[str]:
        """查找MediaInfo路径"""
        try:
            result = subprocess.run(
                ["mediainfo", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return "mediainfo"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # 尝试常见路径
        common_paths = [
            "/usr/bin/mediainfo",
            "/usr/local/bin/mediainfo",
            "C:\\Program Files\\MediaInfo\\MediaInfo.exe"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        logger.warning("MediaInfo未找到，部分音频分析功能可能不可用")
        return None
    
    async def analyze_audio(self, audio_path: str, extract_features: bool = True) -> Dict[str, Any]:
        """
        分析音频内容（带缓存和性能监控）
        
        Args:
            audio_path: 音频文件路径
            extract_features: 是否提取音频特征（默认True）
            
        Returns:
            分析结果字典
        """
        start_time = time.time()
        cache_hit = False
        try:
            # 检查缓存
            if self.enable_cache:
                cache_key = self.cache.generate_key(
                    "multimodal:audio:analysis",
                    audio_path,
                    extract_features=extract_features
                )
                cached_result = await self.cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"从缓存获取音频分析结果: {audio_path}")
                    cache_hit = True
                    # 记录性能指标
                    if METRICS_AVAILABLE:
                        duration = time.time() - start_time
                        MultimodalMetrics.record_request(
                            operation="audio_analysis",
                            cache_hit=True,
                            duration=duration,
                            error=False,
                            concurrent=0
                        )
                    return cached_result
            
            # 使用信号量限制并发
            async with self._semaphore:
                self._current_concurrent += 1
                try:
                    if not os.path.exists(audio_path):
                        raise FileNotFoundError(f"音频文件不存在: {audio_path}")
                    
                    # 并发获取元数据和信息
                    metadata_task = self._get_audio_metadata(audio_path)
                    audio_info_task = self._get_audio_info(audio_path)
                    metadata, audio_info = await asyncio.gather(metadata_task, audio_info_task)
                    
                    # 提取音频特征（如果librosa可用）
                    features = {}
                    if extract_features and LIBROSA_AVAILABLE:
                        try:
                            features = await self.extract_features(audio_path)
                        except Exception as e:
                            logger.warning(f"音频特征提取失败: {e}")
                    
                    # 分析结果
                    analysis_result = {
                        "audio_path": audio_path,
                        "metadata": metadata,
                        "audio_info": audio_info,
                        "features": features,  # 音频特征
                        "fingerprint": "",  # 音频指纹（简化版，暂不实现）
                        "quality_score": self._calculate_quality_score(audio_info),
                        "analysis_timestamp": datetime.utcnow().isoformat() if hasattr(datetime, 'utcnow') else None
                    }
                    
                    # 存入缓存
                    if self.enable_cache:
                        await self.cache.set(cache_key, analysis_result, self.cache_ttl)
                    
                    # 记录性能指标
                    if METRICS_AVAILABLE:
                        duration = time.time() - start_time
                        MultimodalMetrics.record_request(
                            operation="audio_analysis",
                            cache_hit=False,
                            duration=duration,
                            error=False,
                            concurrent=self._current_concurrent
                        )
                    
                    return analysis_result
                    
                except Exception as e:
                    logger.error(f"音频分析失败: {audio_path}, 错误: {e}")
                    if METRICS_AVAILABLE:
                        duration = time.time() - start_time
                        MultimodalMetrics.record_request(
                            operation="audio_analysis",
                            cache_hit=False,
                            duration=duration,
                            error=True,
                            concurrent=self._current_concurrent
                        )
                    return {
                        "audio_path": audio_path,
                        "error": str(e),
                        "analysis_timestamp": None
                    }
                finally:
                    self._current_concurrent -= 1
        except Exception as e:
            if METRICS_AVAILABLE:
                duration = time.time() - start_time
                MultimodalMetrics.record_request(
                    operation="audio_analysis",
                    cache_hit=cache_hit,
                    duration=duration,
                    error=True,
                    concurrent=0
                )
            raise
    
    async def _get_audio_metadata(self, audio_path: str) -> Dict[str, Any]:
        """获取音频元数据（使用MediaInfo）"""
        if not self.mediainfo_path:
            return {}
        
        try:
            result = subprocess.run(
                [self.mediainfo_path, "--Output=JSON", audio_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                metadata = json.loads(result.stdout)
                return metadata
            else:
                logger.warning(f"MediaInfo分析失败: {result.stderr}")
                return {}
        except Exception as e:
            logger.error(f"获取音频元数据失败: {e}")
            return {}
    
    async def _get_audio_info(self, audio_path: str) -> Dict[str, Any]:
        """获取音频信息（使用FFprobe）"""
        if not self.ffmpeg_path:
            return {}
        
        try:
            # 使用ffprobe获取音频信息
            ffprobe_path = self.ffmpeg_path.replace("ffmpeg", "ffprobe")
            if not os.path.exists(ffprobe_path):
                ffprobe_path = "ffprobe"
            
            result = subprocess.run(
                [
                    ffprobe_path,
                    "-v", "error",
                    "-show_entries", "stream=sample_rate,channels,codec_name,bit_rate,duration",
                    "-show_entries", "format=duration,size,bit_rate",
                    "-of", "json",
                    audio_path
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                return self._parse_ffprobe_output(info)
            else:
                logger.warning(f"FFprobe分析失败: {result.stderr}")
                return {}
        except Exception as e:
            logger.error(f"获取音频信息失败: {e}")
            return {}
    
    def _parse_ffprobe_output(self, ffprobe_output: Dict) -> Dict[str, Any]:
        """解析FFprobe输出"""
        audio_info = {
            "sample_rate": 0,
            "channels": 0,
            "codec": "",
            "bitrate": 0,
            "duration": 0,
            "file_size": 0
        }
        
        try:
            # 解析音频流信息
            streams = ffprobe_output.get("streams", [])
            for stream in streams:
                if stream.get("codec_type") == "audio":
                    audio_info["sample_rate"] = int(stream.get("sample_rate", 0))
                    audio_info["channels"] = int(stream.get("channels", 0))
                    audio_info["codec"] = stream.get("codec_name", "")
                    
                    # 解析比特率
                    bit_rate = stream.get("bit_rate")
                    if bit_rate:
                        audio_info["bitrate"] = int(bit_rate)
                    
                    # 解析时长
                    duration = stream.get("duration")
                    if duration:
                        audio_info["duration"] = float(duration)
            
            # 解析格式信息
            format_info = ffprobe_output.get("format", {})
            if format_info:
                duration = format_info.get("duration")
                if duration:
                    audio_info["duration"] = float(duration)
                
                size = format_info.get("size")
                if size:
                    audio_info["file_size"] = int(size)
                
                bit_rate = format_info.get("bit_rate")
                if bit_rate and not audio_info["bitrate"]:
                    audio_info["bitrate"] = int(bit_rate)
        
        except Exception as e:
            logger.error(f"解析FFprobe输出失败: {e}")
        
        return audio_info
    
    def _calculate_quality_score(self, audio_info: Dict[str, Any]) -> float:
        """计算音频质量评分（0-100）"""
        score = 0.0
        
        # 采样率评分（0-40分）
        sample_rate = audio_info.get("sample_rate", 0)
        if sample_rate >= 96000:
            score += 40  # 96kHz
        elif sample_rate >= 48000:
            score += 35  # 48kHz
        elif sample_rate >= 44100:
            score += 30  # 44.1kHz
        elif sample_rate >= 32000:
            score += 20  # 32kHz
        elif sample_rate >= 22050:
            score += 15  # 22.05kHz
        else:
            score += 10
        
        # 编码器评分（0-30分）
        codec = audio_info.get("codec", "").lower()
        if "flac" in codec:
            score += 30  # 无损
        elif "alac" in codec:
            score += 30  # 无损
        elif "ape" in codec:
            score += 30  # 无损
        elif "aac" in codec:
            score += 25  # 高质量有损
        elif "mp3" in codec:
            score += 20  # 标准有损
        elif "opus" in codec:
            score += 25  # 高质量有损
        else:
            score += 15
        
        # 比特率评分（0-30分）
        bitrate = audio_info.get("bitrate", 0)
        if bitrate > 0:
            # 根据编码器估算合理比特率
            if "flac" in codec or "alac" in codec:
                # 无损编码，比特率通常很高
                score += 30
            elif bitrate >= 320000:
                score += 30  # 320 kbps
            elif bitrate >= 256000:
                score += 25  # 256 kbps
            elif bitrate >= 192000:
                score += 20  # 192 kbps
            elif bitrate >= 128000:
                score += 15  # 128 kbps
            else:
                score += 10
        
        return min(score, 100.0)
    
    async def extract_features(self, audio_path: str) -> Dict[str, Any]:
        """
        提取音频特征（使用librosa或简化版）
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            音频特征字典
        """
        if not LIBROSA_AVAILABLE:
            logger.warning("librosa未安装，无法提取音频特征")
            return {}
        
        try:
            if not os.path.exists(audio_path):
                logger.error(f"音频文件不存在: {audio_path}")
                return {}
            
            # 加载音频文件
            y, sr = librosa.load(audio_path, sr=None)
            
            if len(y) == 0:
                logger.warning(f"音频文件为空: {audio_path}")
                return {}
            
            # 基本特征
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
            
            # 调性和模式
            chroma_mean = np.mean(chroma, axis=1)
            key_profile = np.argmax(chroma_mean)
            major_profile = np.sum(chroma_mean[0:7])
            minor_profile = np.sum(chroma_mean[7:12])
            
            key_map = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            key = key_map[key_profile] if key_profile < len(key_map) else 'C'
            mode = 'major' if major_profile > minor_profile else 'minor'
            
            # 能量特征
            energy = float(np.sum(y ** 2) / len(y))
            loudness = float(librosa.amplitude_to_db(np.mean(np.abs(y))))
            
            # 音色特征
            timbre = np.mean(mfcc[1:6], axis=1).tolist() if mfcc.shape[0] > 6 else []
            
            # 语音性、原声性、器乐性（基于特征估算）
            speechiness = float(np.mean(zero_crossing_rate) / 0.1)  # 归一化
            speechiness = min(1.0, max(0.0, speechiness))
            
            tonnetz = librosa.feature.tonnetz(y=y, sr=sr)
            acousticness = float(1.0 - min(1.0, np.mean(np.abs(tonnetz))))  # 估算
            acousticness = min(1.0, max(0.0, acousticness))
            
            instrumentalness = 0.0
            if speechiness < 0.5:
                instrumentalness = 1.0 - speechiness
            
            # 情感特征（简化）
            spectral_flux = float(np.mean(np.diff(spectral_centroid)**2))
            valence = float(0.5 - min(0.5, max(0.0, spectral_flux / 10000)))  # 估算
            arousal = float(np.mean(spectral_centroid) / (np.max(spectral_centroid) + 1e-6))  # 估算
            
            # 创建音频特征字典
            features = {
                "tempo": float(tempo),
                "key": key,
                "mode": mode,
                "energy": energy,
                "spectral_centroid": float(np.mean(spectral_centroid)),
                "spectral_rolloff": float(np.mean(spectral_rolloff)),
                "zero_crossing_rate": float(np.mean(zero_crossing_rate)),
                "mfcc_mean": np.mean(mfcc, axis=1).tolist(),
                "chroma_mean": np.mean(chroma, axis=1).tolist(),
                "timbre": timbre,
                "loudness": loudness,
                "speechiness": speechiness,
                "acousticness": acousticness,
                "instrumentalness": float(instrumentalness),
                "valence": valence,
                "arousal": arousal,
                "sample_rate": int(sr),
                "duration": float(len(y) / sr)
            }
            
            logger.info(f"提取音频特征成功: {audio_path}")
            return features
            
        except Exception as e:
            logger.error(f"音频特征提取失败: {audio_path}, 错误: {e}")
            return {}
    
    async def generate_fingerprint(self, audio_path: str) -> str:
        """
        生成音频指纹（简化版）
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            音频指纹字符串
        """
        # TODO: 实现音频指纹生成
        # 当前返回空字符串，未来可以使用chromaprint或其他库实现
        logger.info(f"音频指纹生成功能暂未实现: {audio_path}")
        return ""

