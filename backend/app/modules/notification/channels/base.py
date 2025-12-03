"""
通知渠道基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from loguru import logger


class NotificationChannelBase(ABC):
    """通知渠道基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化通知渠道
        
        Args:
            config: 渠道配置字典
        """
        self.config = config
        self.name = self.__class__.__name__.replace("Channel", "").lower()
    
    @abstractmethod
    async def send(
        self,
        title: str,
        message: str,
        notification_type: str = "info",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        发送通知
        
        Args:
            title: 通知标题
            message: 通知内容
            notification_type: 通知类型 (info, warning, error, success)
            metadata: 额外元数据
        
        Returns:
            发送结果字典，包含 success, channel, message, error 等字段
        """
        pass
    
    def is_configured(self) -> bool:
        """
        检查渠道是否已配置
        
        Returns:
            是否已配置
        """
        return True
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取渠道配置
        
        Returns:
            配置字典
        """
        return self.config
    
    def validate_config(self) -> tuple[bool, Optional[str]]:
        """
        验证配置是否有效
        
        Returns:
            (是否有效, 错误信息)
        """
        return True, None

