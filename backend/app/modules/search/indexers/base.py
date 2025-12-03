"""
索引器基类
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from loguru import logger


class IndexerConfig(BaseModel):
    """索引器配置"""
    name: str
    base_url: str
    enabled: bool = True
    timeout: int = 30
    max_errors: int = 5
    # 公开站点配置
    is_public: bool = True
    # 私有站点配置
    cookie: Optional[str] = None
    api_key: Optional[str] = None
    user_agent: Optional[str] = None
    # 流控配置
    rate_limit: Optional[int] = None  # 每分钟请求数
    rate_interval: Optional[int] = None  # 请求间隔（秒）


class IndexerBase(ABC):
    """索引器基类"""
    
    def __init__(self, config: IndexerConfig):
        self.config = config
        self.name = config.name
        self.base_url = config.base_url
        self.enabled = config.enabled
        self.timeout = config.timeout
        self.max_errors = config.max_errors
        self.error_count = 0
        self.last_check: Optional[datetime] = None
        self.last_search: Optional[datetime] = None
    
    @abstractmethod
    async def search(
        self,
        query: str,
        media_type: Optional[str] = None,
        year: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        搜索资源
        
        Args:
            query: 搜索关键词
            media_type: 媒体类型 (movie, tv, anime等)
            year: 年份
            **kwargs: 其他搜索参数
        
        Returns:
            搜索结果列表
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            是否健康
        """
        pass
    
    def is_healthy(self) -> bool:
        """检查索引器是否健康"""
        return self.enabled and self.error_count < self.max_errors
    
    def record_error(self):
        """记录错误"""
        self.error_count += 1
        if self.error_count >= self.max_errors:
            self.enabled = False
            logger.warning(f"索引器 {self.name} 因错误过多被禁用")
    
    def reset_errors(self):
        """重置错误计数"""
        self.error_count = 0
        self.enabled = True
    
    def get_status(self) -> Dict[str, Any]:
        """获取索引器状态"""
        return {
            'name': self.name,
            'base_url': self.base_url,
            'enabled': self.enabled,
            'healthy': self.is_healthy(),
            'error_count': self.error_count,
            'max_errors': self.max_errors,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'last_search': self.last_search.isoformat() if self.last_search else None
        }

