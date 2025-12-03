"""
API密钥管理器
统一管理所有API密钥的加密存储和读取
使用CloudKeyManager进行加密存储
"""
from typing import Optional, Dict
from loguru import logger
from app.core.cloud_key_manager import get_key_manager


class APIKeyManager:
    """
    API密钥管理器
    统一管理TMDB、TVDB、Fanart等API密钥的加密存储
    """
    
    def __init__(self):
        """初始化API密钥管理器"""
        self.key_manager = get_key_manager()
    
    def get_tmdb_api_key(self, default: Optional[str] = None) -> str:
        """
        获取TMDB API Key（优先从加密存储读取）
        
        Args:
            default: 默认值（如果加密存储中没有）
            
        Returns:
            TMDB API Key
        """
        # 优先从加密存储读取
        api_data = self.key_manager.get_api_key("tmdb")
        if api_data and api_data.get("api_key"):
            return api_data["api_key"]
        
        # 如果没有，返回默认值
        return default or ""
    
    def set_tmdb_api_key(self, api_key: str):
        """
        设置TMDB API Key（加密存储）
        
        Args:
            api_key: TMDB API Key
        """
        self.key_manager.set_api_key("tmdb", api_key)
    
    def get_tvdb_api_key(self, default: Optional[str] = None) -> str:
        """
        获取TVDB API Key（优先从加密存储读取）
        
        Args:
            default: 默认值（如果加密存储中没有）
            
        Returns:
            TVDB API Key
        """
        # 优先从加密存储读取
        api_data = self.key_manager.get_api_key("tvdb")
        if api_data and api_data.get("api_key"):
            return api_data["api_key"]
        
        # 如果没有，返回默认值
        return default or "ed2aa66b-7899-4677-92a7-67bc9ce3d93a"
    
    def get_tvdb_api_pin(self, default: Optional[str] = None) -> str:
        """
        获取TVDB API PIN（优先从加密存储读取）
        
        Args:
            default: 默认值（如果加密存储中没有）
            
        Returns:
            TVDB API PIN
        """
        # 优先从加密存储读取
        api_data = self.key_manager.get_api_key("tvdb")
        if api_data and api_data.get("api_pin"):
            return api_data["api_pin"]
        
        # 如果没有，返回默认值
        return default or ""
    
    def set_tvdb_api_key(self, api_key: str, api_pin: Optional[str] = None):
        """
        设置TVDB API Key和PIN（加密存储）
        
        Args:
            api_key: TVDB API Key
            api_pin: TVDB API PIN（可选）
        """
        self.key_manager.set_api_key("tvdb", api_key, api_pin)
    
    def get_fanart_api_key(self, default: Optional[str] = None) -> str:
        """
        获取Fanart API Key（优先从加密存储读取）
        
        Args:
            default: 默认值（如果加密存储中没有）
            
        Returns:
            Fanart API Key
        """
        # 优先从加密存储读取
        api_data = self.key_manager.get_api_key("fanart")
        if api_data and api_data.get("api_key"):
            return api_data["api_key"]
        
        # 如果没有，返回默认值
        return default or "d2d31f9ecabea050fc7d68aa3146015f"
    
    def set_fanart_api_key(self, api_key: str):
        """
        设置Fanart API Key（加密存储）
        
        Args:
            api_key: Fanart API Key
        """
        self.key_manager.set_api_key("fanart", api_key)
    
    def initialize_default_keys(self):
        """
        初始化默认API密钥（如果加密存储中不存在）
        用于首次启动时自动保存内置默认值
        """
        # TVDB默认密钥
        if not self.key_manager.has_api_key("tvdb"):
            self.set_tvdb_api_key(
                "ed2aa66b-7899-4677-92a7-67bc9ce3d93a",
                ""
            )
            logger.info("已初始化TVDB默认API密钥（加密存储）")
        
        # Fanart默认密钥
        if not self.key_manager.has_api_key("fanart"):
            self.set_fanart_api_key("d2d31f9ecabea050fc7d68aa3146015f")
            logger.info("已初始化Fanart默认API密钥（加密存储）")
        
        # TMDB密钥由用户自己配置，不自动初始化


# 全局API密钥管理器实例
_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    """获取全局API密钥管理器实例"""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager

