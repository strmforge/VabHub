"""
媒体文件质量比较器
"""

import os
import re
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from loguru import logger
from app.core.cache import get_cache


@dataclass
class QualityInfo:
    """文件质量信息"""
    file_path: str
    file_size: int
    resolution: Optional[str] = None  # 如 "1080p", "4K"
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None
    codec: Optional[str] = None  # 如 "H.264", "H.265"
    bitrate: Optional[int] = None  # 比特率（bps）
    quality_score: float = 0.0  # 质量评分（0-100）


class QualityComparator:
    """媒体文件质量比较器"""
    
    def __init__(self):
        """初始化质量比较器"""
        self.cache = get_cache()
    
    # 分辨率优先级（数字越大优先级越高）
    RESOLUTION_PRIORITY = {
        "4K": 8,
        "2160p": 8,
        "1440p": 7,
        "1080p": 6,
        "720p": 5,
        "480p": 4,
        "360p": 3,
        "240p": 2,
        "144p": 1
    }
    
    # 编码器优先级（数字越大优先级越高）
    CODEC_PRIORITY = {
        "H.265": 3,
        "HEVC": 3,
        "x265": 3,
        "H.264": 2,
        "AVC": 2,
        "x264": 2,
        "VP9": 2,
        "AV1": 4,
        "H.266": 5,
        "VVC": 5
    }
    
    def extract_quality_from_filename(self, filename: str) -> Dict[str, Optional[str]]:
        """
        从文件名提取质量信息
        
        Args:
            filename: 文件名
            
        Returns:
            质量信息字典
        """
        quality_info: Dict[str, Optional[str]] = {
            "resolution": None,
            "codec": None
        }
        
        filename_upper = filename.upper()
        
        # 提取分辨率
        resolution_patterns = [
            r'(\d+)P',  # 1080p, 720p
            r'(\d+)I',  # 1080i
            r'4K',
            r'2160P',
            r'1440P'
        ]
        
        for pattern in resolution_patterns:
            match = re.search(pattern, filename_upper)
            if match:
                if '4K' in pattern or '2160P' in pattern:
                    quality_info["resolution"] = "4K"
                elif '1440P' in pattern:
                    quality_info["resolution"] = "1440p"
                else:
                    res = match.group(1) if match.groups() else None
                    if res:
                        quality_info["resolution"] = f"{res}p"
                break
        
        # 提取编码器
        codec_patterns = [
            r'H\.?265',
            r'HEVC',
            r'X265',
            r'H\.?264',
            r'AVC',
            r'X264',
            r'VP9',
            r'AV1',
            r'H\.?266',
            r'VVC'
        ]
        
        for pattern in codec_patterns:
            if re.search(pattern, filename_upper):
                codec_map = {
                    'H.265': 'H.265',
                    'HEVC': 'H.265',
                    'X265': 'H.265',
                    'H.264': 'H.264',
                    'AVC': 'H.264',
                    'X264': 'H.264',
                    'VP9': 'VP9',
                    'AV1': 'AV1',
                    'H.266': 'H.266',
                    'VVC': 'H.266'
                }
                quality_info["codec"] = codec_map.get(pattern.replace(r'\.?', '.').replace(r'\?', ''), pattern)
                break
        
        return quality_info
    
    def parse_resolution(self, resolution: str) -> Tuple[Optional[int], Optional[int]]:
        """
        解析分辨率字符串
        
        Args:
            resolution: 分辨率字符串，如 "1080p", "1920x1080"
            
        Returns:
            (宽度, 高度)
        """
        if not resolution:
            return None, None
        
        # 尝试解析 "1920x1080" 格式
        match = re.match(r'(\d+)x(\d+)', resolution)
        if match:
            return int(match.group(1)), int(match.group(2))
        
        # 尝试解析 "1080p" 格式
        match = re.match(r'(\d+)p', resolution, re.IGNORECASE)
        if match:
            height = int(match.group(1))
            # 根据高度估算宽度（常见比例）
            if height == 2160 or height == 3840:
                return 3840, 2160  # 4K
            elif height == 1440:
                return 2560, 1440  # 1440p
            elif height == 1080:
                return 1920, 1080  # 1080p
            elif height == 720:
                return 1280, 720   # 720p
            elif height == 480:
                return 854, 480    # 480p
            else:
                # 默认16:9比例
                width = int(height * 16 / 9)
                return width, height
        
        return None, None
    
    def calculate_quality_score(self, quality_info: QualityInfo) -> float:
        """
        计算质量评分
        
        Args:
            quality_info: 质量信息
            
        Returns:
            质量评分（0-100）
        """
        score = 0.0
        
        # 分辨率评分（0-60分）
        if quality_info.resolution:
            resolution_priority = self.RESOLUTION_PRIORITY.get(quality_info.resolution, 0)
            score += resolution_priority * 7.5  # 最高60分
        
        # 编码器评分（0-30分）
        if quality_info.codec:
            codec_priority = self.CODEC_PRIORITY.get(quality_info.codec, 0)
            score += codec_priority * 6  # 最高30分
        
        # 文件大小评分（0-10分，基于分辨率估算合理大小）
        if quality_info.file_size and quality_info.resolution:
            estimated_size = self._estimate_file_size(quality_info.resolution)
            if estimated_size:
                size_ratio = min(quality_info.file_size / estimated_size, 2.0)  # 最多2倍
                score += min(size_ratio * 5, 10)  # 最高10分
        
        return min(score, 100.0)
    
    def _estimate_file_size(self, resolution: str) -> Optional[int]:
        """
        估算文件大小（基于分辨率，假设90分钟电影）
        
        Args:
            resolution: 分辨率
            
        Returns:
            估算的文件大小（字节）
        """
        # 基于分辨率的平均比特率估算（Mbps）
        bitrate_map = {
            "4K": 25,      # 25 Mbps
            "2160p": 25,
            "1440p": 12,   # 12 Mbps
            "1080p": 8,    # 8 Mbps
            "720p": 5,     # 5 Mbps
            "480p": 2,     # 2 Mbps
            "360p": 1,     # 1 Mbps
            "240p": 0.5    # 0.5 Mbps
        }
        
        bitrate_mbps = bitrate_map.get(resolution, 8)
        # 90分钟 = 5400秒
        # 文件大小 = 比特率 * 时间 / 8（转换为字节）
        estimated_size = int(bitrate_mbps * 1_000_000 * 5400 / 8)
        return estimated_size
    
    async def get_quality_info(self, file_path: str, use_cache: bool = True) -> QualityInfo:
        """
        获取文件质量信息（带缓存）
        
        Args:
            file_path: 文件路径
            use_cache: 是否使用缓存
            
        Returns:
            质量信息
        """
        # 生成缓存键
        cache_key = self.cache.generate_key("quality_info", file_path=file_path)
        
        # 尝试从缓存获取
        if use_cache:
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                # 将字典转换回QualityInfo对象
                return QualityInfo(**cached_result)
        
        filename = Path(file_path).name
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        # 从文件名提取质量信息
        quality_from_name = self.extract_quality_from_filename(filename)
        
        quality_info = QualityInfo(
            file_path=file_path,
            file_size=file_size,
            resolution=quality_from_name.get("resolution"),
            codec=quality_from_name.get("codec")
        )
        
        # 解析分辨率
        if quality_info.resolution:
            width, height = self.parse_resolution(quality_info.resolution)
            quality_info.resolution_width = width
            quality_info.resolution_height = height
        
        # 计算质量评分
        quality_info.quality_score = self.calculate_quality_score(quality_info)
        
        # 缓存结果（24小时）
        if use_cache:
            await self.cache.set(cache_key, {
                "file_path": quality_info.file_path,
                "file_size": quality_info.file_size,
                "resolution": quality_info.resolution,
                "resolution_width": quality_info.resolution_width,
                "resolution_height": quality_info.resolution_height,
                "codec": quality_info.codec,
                "bitrate": quality_info.bitrate,
                "quality_score": quality_info.quality_score
            }, ttl=86400)
        
        return quality_info
    
    def get_quality_info_sync(self, file_path: str) -> QualityInfo:
        """
        获取文件质量信息（同步版本，用于向后兼容）
        
        Args:
            file_path: 文件路径
            
        Returns:
            质量信息
        """
        filename = Path(file_path).name
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        # 从文件名提取质量信息
        quality_from_name = self.extract_quality_from_filename(filename)
        
        quality_info = QualityInfo(
            file_path=file_path,
            file_size=file_size,
            resolution=quality_from_name.get("resolution"),
            codec=quality_from_name.get("codec")
        )
        
        # 解析分辨率
        if quality_info.resolution:
            width, height = self.parse_resolution(quality_info.resolution)
            quality_info.resolution_width = width
            quality_info.resolution_height = height
        
        # 计算质量评分
        quality_info.quality_score = self.calculate_quality_score(quality_info)
        
        return quality_info
    
    async def compare_files(self, file_paths: List[str]) -> List[QualityInfo]:
        """
        比较多个文件的质量（异步版本，带缓存）
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            质量信息列表，按质量评分降序排列
        """
        import asyncio
        
        # 并发获取质量信息
        tasks = [self.get_quality_info(file_path) for file_path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        quality_infos = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"获取文件质量信息失败: {file_paths[i]}, 错误: {result}")
            else:
                quality_infos.append(result)
        
        # 按质量评分降序排列
        quality_infos.sort(key=lambda x: x.quality_score, reverse=True)
        
        return quality_infos
    
    def compare_files_sync(self, file_paths: List[str]) -> List[QualityInfo]:
        """
        比较多个文件的质量（同步版本，用于向后兼容）
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            质量信息列表，按质量评分降序排列
        """
        quality_infos = []
        
        for file_path in file_paths:
            try:
                quality_info = self.get_quality_info_sync(file_path)
                quality_infos.append(quality_info)
            except Exception as e:
                logger.error(f"获取文件质量信息失败: {file_path}, 错误: {e}")
        
        # 按质量评分降序排列
        quality_infos.sort(key=lambda x: x.quality_score, reverse=True)
        
        return quality_infos
    
    async def get_best_quality_file(self, file_paths: List[str]) -> Optional[QualityInfo]:
        """
        获取质量最好的文件（异步版本）
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            质量最好的文件信息，如果列表为空则返回None
        """
        quality_infos = await self.compare_files(file_paths)
        return quality_infos[0] if quality_infos else None
    
    def get_best_quality_file_sync(self, file_paths: List[str]) -> Optional[QualityInfo]:
        """
        获取质量最好的文件（同步版本，用于向后兼容）
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            质量最好的文件信息，如果列表为空则返回None
        """
        quality_infos = self.compare_files_sync(file_paths)
        return quality_infos[0] if quality_infos else None

