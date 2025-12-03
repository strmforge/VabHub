"""
视频分析器
提供视频内容分析功能（简化版）
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from loguru import logger
import subprocess
import json
import os
import asyncio
from datetime import datetime
import hashlib
from functools import lru_cache

# 可选依赖：OpenCV用于视频场景检测
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV未安装，视频场景检测功能将不可用")

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


class VideoAnalyzer:
    """视频分析器（简化版，使用MediaInfo和FFmpeg）"""
    
    def __init__(self, enable_cache: bool = True, cache_ttl: int = 86400, max_concurrent: int = 3):
        """
        初始化视频分析器
        
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
            logger.info(f"视频分析器已启用缓存（TTL: {cache_ttl}秒）")
    
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
        
        logger.warning("FFmpeg未找到，部分视频分析功能可能不可用")
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
        
        logger.warning("MediaInfo未找到，部分视频分析功能可能不可用")
        return None
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希（用于缓存键）"""
        try:
            # 使用文件的修改时间和大小作为哈希的一部分（更快）
            stat = os.stat(file_path)
            hash_input = f"{file_path}:{stat.st_mtime}:{stat.st_size}"
            return hashlib.md5(hash_input.encode()).hexdigest()
        except Exception as e:
            logger.warning(f"计算文件哈希失败: {e}")
            # 回退到简单的路径哈希
            return hashlib.md5(file_path.encode()).hexdigest()
    
    async def analyze_video(self, video_path: str, detect_scenes: bool = True) -> Dict[str, Any]:
        """
        分析视频内容（带缓存和性能监控）
        
        Args:
            video_path: 视频文件路径
            detect_scenes: 是否检测场景（默认True）
            
        Returns:
            分析结果字典
        """
        start_time = time.time()
        cache_hit = False
        error_occurred = False
        try:
            # 检查缓存
            if self.enable_cache:
                cache_key = self.cache.generate_key(
                    "multimodal:video:analysis",
                    video_path,
                    detect_scenes=detect_scenes
                )
                cached_result = await self.cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"从缓存获取视频分析结果: {video_path}")
                    cache_hit = True
                    # 记录性能指标（异步）
                    if METRICS_AVAILABLE:
                        duration = time.time() - start_time
                        # 使用异步方法记录（如果支持数据库存储）
                        try:
                            await MultimodalMetrics.record_request_async(
                                operation="video_analysis",
                                cache_hit=True,
                                duration=duration,
                                error=False,
                                concurrent=0
                            )
                        except:
                            # 回退到同步方法
                            MultimodalMetrics.record_request(
                                operation="video_analysis",
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
                    if not os.path.exists(video_path):
                        raise FileNotFoundError(f"视频文件不存在: {video_path}")
                    
                    # 并发获取元数据和信息
                    metadata_task = self._get_video_metadata(video_path)
                    video_info_task = self._get_video_info(video_path)
                    metadata, video_info = await asyncio.gather(metadata_task, video_info_task)
                    
                    # 场景检测（可选，如果OpenCV可用）
                    scenes = []
                    if detect_scenes and OPENCV_AVAILABLE:
                        try:
                            scenes = await self.detect_scenes(video_path)
                        except Exception as e:
                            logger.warning(f"场景检测失败: {e}")
                    
                    # 分析结果
                    analysis_result = {
                        "video_path": video_path,
                        "metadata": metadata,
                        "video_info": video_info,
                        "scenes": scenes,  # 场景检测结果
                        "objects": [],  # 对象识别（简化版，暂不实现）
                        "quality_score": self._calculate_quality_score(video_info),
                        "analysis_timestamp": datetime.utcnow().isoformat() if hasattr(datetime, 'utcnow') else None
                    }
                    
                    # 存入缓存
                    if self.enable_cache:
                        await self.cache.set(cache_key, analysis_result, self.cache_ttl)
                    
                    # 记录性能指标
                    if METRICS_AVAILABLE:
                        duration = time.time() - start_time
                        MultimodalMetrics.record_request(
                            operation="video_analysis",
                            cache_hit=False,
                            duration=duration,
                            error=False,
                            concurrent=self._current_concurrent
                        )
                    
                    return analysis_result
                    
                except Exception as e:
                    logger.error(f"视频分析失败: {video_path}, 错误: {e}")
                    error_occurred = True
                    # 记录错误
                    if METRICS_AVAILABLE:
                        duration = time.time() - start_time
                        MultimodalMetrics.record_request(
                            operation="video_analysis",
                            cache_hit=False,
                            duration=duration,
                            error=True,
                            concurrent=self._current_concurrent
                        )
                    return {
                        "video_path": video_path,
                        "error": str(e),
                        "analysis_timestamp": None
                    }
                finally:
                    self._current_concurrent -= 1
        except Exception as e:
            error_occurred = True
            # 记录错误
            if METRICS_AVAILABLE:
                duration = time.time() - start_time
                MultimodalMetrics.record_request(
                    operation="video_analysis",
                    cache_hit=cache_hit,
                    duration=duration,
                    error=True,
                    concurrent=0
                )
            raise
    
    async def _get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """获取视频元数据（使用MediaInfo）"""
        if not self.mediainfo_path:
            return {}
        
        try:
            result = subprocess.run(
                [self.mediainfo_path, "--Output=JSON", video_path],
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
            logger.error(f"获取视频元数据失败: {e}")
            return {}
    
    async def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频信息（使用FFprobe）"""
        if not self.ffmpeg_path:
            return {}
        
        try:
            # 使用ffprobe获取视频信息
            ffprobe_path = self.ffmpeg_path.replace("ffmpeg", "ffprobe")
            if not os.path.exists(ffprobe_path):
                ffprobe_path = "ffprobe"
            
            result = subprocess.run(
                [
                    ffprobe_path,
                    "-v", "error",
                    "-show_entries", "stream=width,height,r_frame_rate,codec_name,bit_rate,duration",
                    "-show_entries", "format=duration,size,bit_rate",
                    "-of", "json",
                    video_path
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
            logger.error(f"获取视频信息失败: {e}")
            return {}
    
    def _parse_ffprobe_output(self, ffprobe_output: Dict) -> Dict[str, Any]:
        """解析FFprobe输出"""
        video_info = {
            "width": 0,
            "height": 0,
            "fps": 0,
            "codec": "",
            "bitrate": 0,
            "duration": 0,
            "file_size": 0
        }
        
        try:
            # 解析视频流信息
            streams = ffprobe_output.get("streams", [])
            for stream in streams:
                if stream.get("codec_type") == "video":
                    video_info["width"] = stream.get("width", 0)
                    video_info["height"] = stream.get("height", 0)
                    video_info["codec"] = stream.get("codec_name", "")
                    
                    # 解析帧率
                    r_frame_rate = stream.get("r_frame_rate", "0/1")
                    if "/" in r_frame_rate:
                        num, den = map(int, r_frame_rate.split("/"))
                        if den > 0:
                            video_info["fps"] = num / den
                    
                    # 解析比特率
                    bit_rate = stream.get("bit_rate")
                    if bit_rate:
                        video_info["bitrate"] = int(bit_rate)
                    
                    # 解析时长
                    duration = stream.get("duration")
                    if duration:
                        video_info["duration"] = float(duration)
            
            # 解析格式信息
            format_info = ffprobe_output.get("format", {})
            if format_info:
                duration = format_info.get("duration")
                if duration:
                    video_info["duration"] = float(duration)
                
                size = format_info.get("size")
                if size:
                    video_info["file_size"] = int(size)
                
                bit_rate = format_info.get("bit_rate")
                if bit_rate and not video_info["bitrate"]:
                    video_info["bitrate"] = int(bit_rate)
        
        except Exception as e:
            logger.error(f"解析FFprobe输出失败: {e}")
        
        return video_info
    
    def _calculate_quality_score(self, video_info: Dict[str, Any]) -> float:
        """计算视频质量评分（0-100）"""
        score = 0.0
        
        # 分辨率评分（0-60分）
        width = video_info.get("width", 0)
        height = video_info.get("height", 0)
        if width and height:
            if width >= 3840 and height >= 2160:
                score += 60  # 4K
            elif width >= 1920 and height >= 1080:
                score += 50  # 1080p
            elif width >= 1280 and height >= 720:
                score += 40  # 720p
            elif width >= 854 and height >= 480:
                score += 30  # 480p
            else:
                score += 20  # 其他
        
        # 编码器评分（0-20分）
        codec = video_info.get("codec", "").lower()
        if "hevc" in codec or "h265" in codec:
            score += 20
        elif "avc" in codec or "h264" in codec:
            score += 15
        elif "vp9" in codec:
            score += 18
        elif "av1" in codec:
            score += 20
        else:
            score += 10
        
        # 比特率评分（0-20分）
        bitrate = video_info.get("bitrate", 0)
        if bitrate > 0:
            # 根据分辨率估算合理比特率
            if width >= 3840:
                ideal_bitrate = 25_000_000  # 25 Mbps for 4K
            elif width >= 1920:
                ideal_bitrate = 8_000_000  # 8 Mbps for 1080p
            elif width >= 1280:
                ideal_bitrate = 5_000_000  # 5 Mbps for 720p
            else:
                ideal_bitrate = 2_000_000  # 2 Mbps for 480p
            
            bitrate_ratio = min(bitrate / ideal_bitrate, 2.0)
            score += min(bitrate_ratio * 10, 20)
        
        return min(score, 100.0)
    
    async def detect_scenes(
        self, 
        video_path: str,
        min_scene_length: float = 2.0,
        threshold: float = 30.0
    ) -> List[Dict[str, Any]]:
        """
        检测视频场景（使用OpenCV或简化版）
        
        Args:
            video_path: 视频文件路径
            min_scene_length: 最小场景长度（秒）
            threshold: 场景检测阈值（0-100）
            
        Returns:
            场景列表
        """
        if not OPENCV_AVAILABLE:
            logger.warning("OpenCV未安装，无法进行场景检测")
            return []
        
        try:
            if not os.path.exists(video_path):
                logger.error(f"视频文件不存在: {video_path}")
                return []
            
            # 打开视频文件
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                logger.error(f"无法打开视频文件: {video_path}")
                return []
            
            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30.0  # 默认帧率
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= 0:
                logger.warning(f"无法获取视频总帧数: {video_path}")
                cap.release()
                return []
            
            duration = total_frames / fps
            
            # 场景检测
            scenes = []
            current_scene_start = 0.0
            last_hist = None
            frame_idx = 0
            
            # 为了性能，可以跳帧处理（每N帧处理一次）
            frame_skip = max(1, int(fps / 2))  # 每秒处理2帧
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 跳帧处理
                if frame_idx % frame_skip != 0:
                    frame_idx += 1
                    continue
                
                # 计算当前帧的直方图
                hist = cv2.calcHist([frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
                hist = cv2.normalize(hist, hist).flatten()
                
                if last_hist is not None:
                    # 计算直方图差异（使用相关性）
                    diff = cv2.compareHist(last_hist, hist, cv2.HISTCMP_CORREL)
                    
                    # 如果差异超过阈值，认为是一个新场景
                    # diff范围是0-1，值越小表示差异越大
                    if diff < (1.0 - threshold / 100.0):
                        current_time = frame_idx / fps
                        
                        # 检查场景长度是否足够
                        if current_time - current_scene_start >= min_scene_length:
                            scene_end = current_time
                            
                            # 创建场景片段
                            scene = {
                                "start_time": current_scene_start,
                                "end_time": scene_end,
                                "duration": scene_end - current_scene_start,
                                "description": f"Scene {len(scenes) + 1}",
                                "confidence": 1.0 - diff,
                                "frame_start": int(current_scene_start * fps),
                                "frame_end": int(scene_end * fps)
                            }
                            
                            scenes.append(scene)
                            current_scene_start = scene_end
                
                last_hist = hist
                frame_idx += 1
            
            # 添加最后一个场景
            if current_scene_start < duration:
                scene = {
                    "start_time": current_scene_start,
                    "end_time": duration,
                    "duration": duration - current_scene_start,
                    "description": f"Scene {len(scenes) + 1}",
                    "confidence": 1.0,
                    "frame_start": int(current_scene_start * fps),
                    "frame_end": total_frames
                }
                scenes.append(scene)
            
            cap.release()
            logger.info(f"检测到 {len(scenes)} 个场景 in {video_path}")
            return scenes
            
        except Exception as e:
            logger.error(f"视频场景检测失败: {video_path}, 错误: {e}")
            return []
    
    async def detect_objects(self, video_path: str) -> List[Dict[str, Any]]:
        """
        检测视频中的对象（简化版）
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            对象列表
        """
        # TODO: 实现对象检测
        # 当前返回空列表，未来可以使用YOLO或其他模型实现
        logger.info(f"对象检测功能暂未实现: {video_path}")
        return []

