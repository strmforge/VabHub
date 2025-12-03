"""
Loguru日志处理器 - 集成到实时日志中心
"""

import sys
from typing import Optional
from loguru import logger
from app.modules.log_center.service import get_log_center, LogLevel, LogSource


class WebSocketLogSink:
    """WebSocket日志接收器 - 将loguru日志转发到实时日志中心"""
    
    def __init__(self):
        self.log_center = get_log_center()
    
    def __call__(self, message):
        """日志接收器（loguru sink）"""
        try:
            record = message.record
            
            # 解析日志级别
            level_map = {
                "TRACE": LogLevel.DEBUG,
                "DEBUG": LogLevel.DEBUG,
                "INFO": LogLevel.INFO,
                "SUCCESS": LogLevel.INFO,
                "WARNING": LogLevel.WARNING,
                "ERROR": LogLevel.ERROR,
                "CRITICAL": LogLevel.CRITICAL
            }
            level = level_map.get(record["level"].name, LogLevel.INFO)
            
            # 解析日志来源
            source = self._parse_source(record["name"])
            
            # 解析组件名称
            component = record["name"].split(".")[-1] if "." in record["name"] else record["name"]
            
            # 获取日志消息
            log_message = str(message)
            
            # 异步添加到日志中心（使用线程安全的方式）
            import asyncio
            try:
                # 尝试获取当前事件循环
                loop = asyncio.get_running_loop()
                # 如果事件循环正在运行，创建任务
                loop.create_task(
                    self.log_center.add_log(
                        level=level.value,
                        message=log_message,
                        source=source.value,
                        component=component
                    )
                )
            except RuntimeError:
                # 如果没有运行中的事件循环，使用线程池
                import concurrent.futures
                import threading
                
                def run_async():
                    try:
                        asyncio.run(
                            self.log_center.add_log(
                                level=level.value,
                                message=log_message,
                                source=source.value,
                                component=component
                            )
                        )
                    except Exception:
                        pass
                
                # 在后台线程中运行
                thread = threading.Thread(target=run_async, daemon=True)
                thread.start()
        except Exception as e:
            # 避免日志处理本身出错导致循环
            print(f"日志处理器错误: {e}", file=sys.stderr)
    
    def _parse_source(self, name: str) -> LogSource:
        """从模块名称解析日志来源"""
        name_lower = name.lower()
        
        if "plugin" in name_lower:
            return LogSource.PLUGIN
        elif "downloader" in name_lower or "qbittorrent" in name_lower or "transmission" in name_lower:
            return LogSource.DOWNLOADER
        elif "media_server" in name_lower or "plex" in name_lower or "jellyfin" in name_lower or "emby" in name_lower:
            return LogSource.MEDIA_SERVER
        elif "scheduler" in name_lower or "task" in name_lower:
            return LogSource.SCHEDULER
        elif "api" in name_lower:
            return LogSource.API
        elif "search" in name_lower:
            return LogSource.SEARCH
        elif "subscription" in name_lower:
            return LogSource.SUBSCRIPTION
        elif "multimodal" in name_lower:
            return LogSource.MULTIMODAL
        else:
            return LogSource.CORE


# 全局日志接收器实例
_log_sink: Optional[WebSocketLogSink] = None


def setup_realtime_logging():
    """设置实时日志（在应用启动时调用）"""
    global _log_sink
    if _log_sink is None:
        _log_sink = WebSocketLogSink()
        # 添加loguru sink
        logger.add(
            _log_sink,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            enqueue=True,  # 异步处理，避免阻塞
            serialize=False  # 不序列化，直接处理
        )
    return _log_sink

