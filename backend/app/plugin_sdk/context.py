"""
插件运行时上下文

PLUGIN-SDK-1 实现
"""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class PluginContext(BaseModel):
    """
    插件运行时上下文
    
    每个插件在加载时都会获得一个独立的上下文对象，
    包含插件的基本信息和运行时配置。
    
    Attributes:
        plugin_id: 插件唯一标识（如 vabhub.example.hello_world）
        plugin_name: 插件显示名称
        data_dir: 插件专属数据目录路径
        logger_name: 插件专用 logger 名称
        app_version: 主系统版本号
        base_url: 主系统基础 URL
    """
    
    plugin_id: str = Field(..., description="插件唯一标识")
    plugin_name: str = Field(default="", description="插件显示名称")
    data_dir: Path = Field(..., description="插件专属数据目录")
    logger_name: str = Field(..., description="Logger 名称")
    app_version: Optional[str] = Field(default=None, description="主系统版本")
    base_url: Optional[str] = Field(default=None, description="主系统 Base URL")
    
    class Config:
        arbitrary_types_allowed = True
    
    def get_config_path(self, filename: str = "config.json") -> Path:
        """获取插件配置文件路径"""
        return self.data_dir / filename
    
    def get_cache_dir(self) -> Path:
        """获取插件缓存目录"""
        cache_dir = self.data_dir / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    def get_log_dir(self) -> Path:
        """获取插件日志目录"""
        log_dir = self.data_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
