"""
阅读状态统一枚举定义
SHELF-HUB-FINISH-1 实现

为 MyShelf、ReadingHub、Favorites 等阅读相关 API 提供统一的状态定义
"""

from typing import Literal, Optional
from enum import Enum


# ==================== 过滤状态枚举 (用于 MyShelf API) ====================
ReadingItemFilterStatus = Literal["active", "finished", "all"]

# ==================== 显示状态枚举 (用于 ReadingHub API) ====================
ReadingItemDisplayStatus = Literal["active", "not_started", "finished"]


class ReadingStatusHelper:
    """
    阅读状态辅助工具
    
    提供状态转换和验证的统一逻辑
    """
    
    @staticmethod
    def is_active_status(is_finished: bool, has_progress: bool) -> bool:
        """
        判断是否为活跃状态 (进行中或未开始)
        
        Args:
            is_finished: 是否已完成
            has_progress: 是否有进度记录
            
        Returns:
            是否为活跃状态
        """
        return not is_finished
    
    @staticmethod
    def get_display_status(is_finished: bool, has_progress: bool) -> ReadingItemDisplayStatus:
        """
        获取显示状态
        
        Args:
            is_finished: 是否已完成
            has_progress: 是否有进度记录
            
        Returns:
            显示状态
        """
        if is_finished:
            return "finished"
        elif has_progress:
            return "active"
        else:
            return "not_started"
    
    @staticmethod
    def validate_filter_status(status: Optional[str]) -> ReadingItemFilterStatus:
        """
        验证过滤状态
        
        Args:
            status: 状态字符串
            
        Returns:
            有效的过滤状态
            
        Raises:
            ValueError: 无效状态
        """
        valid_statuses = ["active", "finished", "all"]
        if status is None:
            return "all"
        if status not in valid_statuses:
            raise ValueError(f"无效的过滤状态: {status}，有效值为: {valid_statuses}")
        return status  # type: ignore
    
    @staticmethod
    def validate_display_status(status: str) -> ReadingItemDisplayStatus:
        """
        验证显示状态
        
        Args:
            status: 状态字符串
            
        Returns:
            有效的显示状态
            
        Raises:
            ValueError: 无效状态
        """
        valid_statuses = ["active", "not_started", "finished"]
        if status not in valid_statuses:
            raise ValueError(f"无效的显示状态: {status}，有效值为: {valid_statuses}")
        return status  # type: ignore
    
    @staticmethod
    def get_status_label(status: ReadingItemDisplayStatus) -> str:
        """
        获取状态标签 (用于前端显示)
        
        Args:
            status: 显示状态
            
        Returns:
            状态标签
        """
        labels = {
            "active": "进行中",
            "not_started": "未开始", 
            "finished": "已完成"
        }
        return labels.get(status, "未知")
    
    @staticmethod
    def get_status_color(status: ReadingItemDisplayStatus) -> str:
        """
        获取状态颜色 (用于前端显示)
        
        Args:
            status: 显示状态
            
        Returns:
            状态颜色
        """
        colors = {
            "active": "primary",      # 蓝色 - 进行中
            "not_started": "grey",    # 灰色 - 未开始
            "finished": "success"     # 绿色 - 已完成
        }
        return colors.get(status, "default")


# 便捷函数
def is_reading_active(is_finished: bool, has_progress: bool = True) -> bool:
    """判断阅读是否活跃 (进行中或未开始)"""
    return ReadingStatusHelper.is_active_status(is_finished, has_progress)


def get_reading_display_status(is_finished: bool, has_progress: bool) -> ReadingItemDisplayStatus:
    """获取阅读显示状态"""
    return ReadingStatusHelper.get_display_status(is_finished, has_progress)


def validate_reading_filter_status(status: Optional[str]) -> ReadingItemFilterStatus:
    """验证阅读过滤状态"""
    return ReadingStatusHelper.validate_filter_status(status)
