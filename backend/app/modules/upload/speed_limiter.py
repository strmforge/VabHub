"""
上传速度限制器
实现上传速度限制和动态调整分片大小
"""

import asyncio
import time
from typing import Optional
from loguru import logger


class SpeedLimiter:
    """上传速度限制器"""
    
    def __init__(self, speed_limit: Optional[int] = None):
        """
        初始化速度限制器
        
        Args:
            speed_limit: 速度限制（字节/秒，None表示无限制）
        """
        self.speed_limit = speed_limit
        self.start_time: Optional[float] = None
        self.uploaded_bytes = 0
        self.last_check_time: Optional[float] = None
        self.current_speed = 0.0
    
    def start(self):
        """开始计时"""
        self.start_time = time.time()
        self.last_check_time = self.start_time
        self.uploaded_bytes = 0
        self.current_speed = 0.0
    
    async def wait_if_needed(self, chunk_size: int):
        """
        如果需要，等待以限制速度
        
        Args:
            chunk_size: 即将上传的块大小（字节）
        """
        if not self.speed_limit:
            return
        
        if not self.start_time:
            self.start()
        
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # 计算当前速度
        if elapsed > 0:
            self.current_speed = self.uploaded_bytes / elapsed
        
        # 如果速度超过限制，计算需要等待的时间
        if self.current_speed > self.speed_limit:
            # 计算应该花费的时间
            expected_time = self.uploaded_bytes / self.speed_limit
            
            # 计算需要等待的时间
            wait_time = expected_time - elapsed
            
            if wait_time > 0:
                logger.debug(f"速度限制: 当前速度 {self.current_speed/1024/1024:.2f} MB/s, 限制 {self.speed_limit/1024/1024:.2f} MB/s, 等待 {wait_time:.2f} 秒")
                await asyncio.sleep(wait_time)
        
        # 更新已上传字节数
        self.uploaded_bytes += chunk_size
        self.last_check_time = current_time
    
    def get_current_speed(self) -> float:
        """获取当前速度（字节/秒）"""
        if not self.start_time:
            return 0.0
        
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        if elapsed > 0:
            return self.uploaded_bytes / elapsed
        
        return 0.0
    
    def reset(self):
        """重置计数器"""
        self.start_time = None
        self.uploaded_bytes = 0
        self.last_check_time = None
        self.current_speed = 0.0


def calculate_optimal_part_size(
    file_size: int,
    speed_limit: Optional[int] = None,
    min_part_size: int = 5 * 1024 * 1024,  # 5MB
    max_part_size: int = 100 * 1024 * 1024,  # 100MB
    default_part_size: int = 10 * 1024 * 1024  # 10MB
) -> int:
    """
    根据文件大小和速度限制计算最优分片大小
    
    Args:
        file_size: 文件大小（字节）
        speed_limit: 速度限制（字节/秒，可选）
        min_part_size: 最小分片大小（字节）
        max_part_size: 最大分片大小（字节）
        default_part_size: 默认分片大小（字节）
    
    Returns:
        最优分片大小（字节）
    """
    # 如果没有速度限制，使用默认分片大小
    if not speed_limit:
        return default_part_size
    
    # 根据速度限制动态调整分片大小
    # 速度越快，分片可以越大
    # 速度越慢，分片应该越小（减少重传成本）
    
    # 计算目标分片上传时间（秒）
    target_upload_time = 10.0  # 目标每个分片上传时间10秒
    
    # 计算最优分片大小
    optimal_size = int(speed_limit * target_upload_time)
    
    # 限制在最小和最大之间
    optimal_size = max(min_part_size, min(optimal_size, max_part_size))
    
    # 确保不超过文件大小
    optimal_size = min(optimal_size, file_size)
    
    logger.debug(f"计算最优分片大小: 文件大小={file_size/1024/1024:.2f} MB, 速度限制={speed_limit/1024/1024:.2f} MB/s, 最优分片={optimal_size/1024/1024:.2f} MB")
    
    return optimal_size

