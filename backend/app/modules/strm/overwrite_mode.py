"""
STRM文件覆盖模式
参考MoviePilot的实现
"""

from enum import Enum
from typing import Optional
from pathlib import Path
from loguru import logger


class OverwriteMode(str, Enum):
    """覆盖模式"""
    NEVER = "never"  # 从不覆盖
    ALWAYS = "always"  # 总是覆盖
    SIZE = "size"  # 按大小覆盖（大覆盖小）


class OverwriteHandler:
    """覆盖模式处理器"""
    
    @staticmethod
    async def should_overwrite(
        existing_path: Path,
        overwrite_mode: OverwriteMode,
        new_file_size: Optional[int] = None
    ) -> tuple[bool, str]:
        """
        检查是否应该覆盖现有文件
        
        Args:
            existing_path: 现有文件路径
            overwrite_mode: 覆盖模式
            new_file_size: 新文件大小（字节），用于size模式比较
        
        Returns:
            (是否覆盖, 原因说明)
        """
        # 如果文件不存在，直接覆盖（创建新文件）
        if not existing_path.exists():
            return True, "文件不存在，创建新文件"
        
        if overwrite_mode == OverwriteMode.NEVER:
            return False, "覆盖模式为never，跳过覆盖"
        
        elif overwrite_mode == OverwriteMode.ALWAYS:
            return True, "覆盖模式为always，直接覆盖"
        
        elif overwrite_mode == OverwriteMode.SIZE:
            if new_file_size is None:
                logger.warning(f"覆盖模式为size，但未提供新文件大小，跳过覆盖: {existing_path}")
                return False, "覆盖模式为size，但未提供新文件大小"
            
            # 获取现有文件大小
            try:
                existing_size = existing_path.stat().st_size
            except Exception as e:
                logger.error(f"获取现有文件大小失败: {e}")
                return False, f"获取现有文件大小失败: {e}"
            
            # 比较文件大小
            if new_file_size > existing_size:
                return True, f"新文件更大 ({new_file_size} > {existing_size})，覆盖现有文件"
            else:
                return False, f"现有文件更大或相等 ({existing_size} >= {new_file_size})，跳过覆盖"
        
        else:
            logger.warning(f"未知的覆盖模式: {overwrite_mode}")
            return False, f"未知的覆盖模式: {overwrite_mode}"

