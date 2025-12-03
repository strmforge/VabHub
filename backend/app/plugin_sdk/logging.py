"""
插件专用 Logger

PLUGIN-SDK-1 实现
"""

from typing import Any
from loguru import logger


class PluginLogger:
    """
    插件专用 Logger
    
    封装 loguru，为插件提供命名空间隔离的日志记录。
    日志会自动添加 [plugin:<plugin_id>] 前缀。
    
    Example:
        log = PluginLogger("vabhub.plugin.my_plugin")
        log.info("Hello from plugin!")
        # Output: [plugin:my_plugin] Hello from plugin!
    """
    
    def __init__(self, logger_name: str):
        """
        初始化插件 Logger
        
        Args:
            logger_name: Logger 名称，格式为 vabhub.plugin.<plugin_id>
        """
        self._logger_name = logger_name
        # 从 logger_name 提取插件 ID 作为前缀
        parts = logger_name.split(".")
        self._prefix = f"[plugin:{parts[-1]}]" if parts else "[plugin]"
    
    def _format_message(self, message: str) -> str:
        """格式化消息，添加插件前缀"""
        return f"{self._prefix} {message}"
    
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录 DEBUG 级别日志"""
        logger.debug(self._format_message(message), *args, **kwargs)
    
    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录 INFO 级别日志"""
        logger.info(self._format_message(message), *args, **kwargs)
    
    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录 WARNING 级别日志"""
        logger.warning(self._format_message(message), *args, **kwargs)
    
    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录 ERROR 级别日志"""
        logger.error(self._format_message(message), *args, **kwargs)
    
    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录异常日志（包含堆栈跟踪）"""
        logger.exception(self._format_message(message), *args, **kwargs)
    
    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录 CRITICAL 级别日志"""
        logger.critical(self._format_message(message), *args, **kwargs)
    
    @property
    def name(self) -> str:
        """获取 Logger 名称"""
        return self._logger_name
