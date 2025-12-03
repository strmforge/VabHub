"""
实时日志中心服务
提供WebSocket实时日志推送、多源聚合、日志查询等功能
"""

import json
import asyncio
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
from collections import deque
from enum import Enum
from loguru import logger as loguru_logger
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogSource(str, Enum):
    """日志来源"""
    CORE = "core"
    PLUGIN = "plugin"
    DOWNLOADER = "downloader"
    MEDIA_SERVER = "media_server"
    SCHEDULER = "scheduler"
    API = "api"
    SEARCH = "search"
    SUBSCRIPTION = "subscription"
    MULTIMODAL = "multimodal"


class LogEntry:
    """日志条目"""
    
    def __init__(
        self,
        level: str,
        message: str,
        source: str = LogSource.CORE,
        component: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        self.level = level.upper()
        self.message = message
        self.source = source
        self.component = component or "unknown"
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "level": self.level,
            "message": self.message,
            "source": self.source,
            "component": self.component,
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


class LogCenter:
    """实时日志中心"""
    
    def __init__(self, max_entries: int = 10000):
        """
        初始化日志中心
        
        Args:
            max_entries: 最大日志条目数（内存缓存）
        """
        self.max_entries = max_entries
        self.entries: deque = deque(maxlen=max_entries)
        self.websockets: Set[WebSocket] = set()
        self.filters: Dict[WebSocket, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def add_log(
        self,
        level: str,
        message: str,
        source: str = LogSource.CORE,
        component: Optional[str] = None
    ):
        """
        添加日志条目
        
        Args:
            level: 日志级别
            message: 日志消息
            source: 日志来源
            component: 组件名称
        """
        entry = LogEntry(level, message, source, component)
        
        # 添加到内存缓存
        async with self._lock:
            self.entries.append(entry)
        
        # 广播到所有WebSocket客户端
        await self._broadcast_log(entry)
    
    async def _broadcast_log(self, entry: LogEntry):
        """广播日志到所有WebSocket客户端"""
        if not self.websockets:
            return
        
        entry_dict = entry.to_dict()
        entry_json = entry.to_json()
        
        # 过滤掉已断开的连接
        disconnected = set()
        
        for websocket in self.websockets:
            try:
                # 检查连接状态
                if websocket.client_state != WebSocketState.CONNECTED:
                    disconnected.add(websocket)
                    continue
                
                # 应用过滤器
                filters = self.filters.get(websocket, {})
                if self._should_filter(entry_dict, filters):
                    continue
                
                # 发送日志
                await websocket.send_text(entry_json)
                
            except Exception as e:
                loguru_logger.error(f"广播日志到WebSocket失败: {e}")
                disconnected.add(websocket)
        
        # 移除已断开的连接
        if disconnected:
            async with self._lock:
                self.websockets -= disconnected
                for ws in disconnected:
                    self.filters.pop(ws, None)
    
    def _should_filter(self, entry: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        检查日志是否应该被过滤
        
        Args:
            entry: 日志条目字典
            filters: 过滤器字典
        
        Returns:
            True表示应该过滤掉，False表示应该保留
        """
        # 级别过滤
        if "level" in filters:
            allowed_levels = filters["level"]
            if isinstance(allowed_levels, str):
                allowed_levels = [allowed_levels]
            if entry["level"] not in [l.upper() for l in allowed_levels]:
                return True
        
        # 来源过滤
        if "source" in filters:
            allowed_sources = filters["source"]
            if isinstance(allowed_sources, str):
                allowed_sources = [allowed_sources]
            if entry["source"] not in [s.lower() for s in allowed_sources]:
                return True
        
        # 组件过滤
        if "component" in filters:
            allowed_components = filters["component"]
            if isinstance(allowed_components, str):
                allowed_components = [allowed_components]
            if entry["component"] not in allowed_components:
                return True
        
        # 关键词过滤
        if "keyword" in filters:
            keyword = filters["keyword"].lower()
            if keyword not in entry["message"].lower():
                return True
        
        return False
    
    async def add_websocket(
        self,
        websocket: WebSocket,
        filters: Optional[Dict[str, Any]] = None
    ):
        """
        添加WebSocket连接
        
        Args:
            websocket: WebSocket连接
            filters: 过滤器字典
        """
        async with self._lock:
            self.websockets.add(websocket)
            if filters:
                self.filters[websocket] = filters
            else:
                self.filters[websocket] = {}
    
    async def remove_websocket(self, websocket: WebSocket):
        """移除WebSocket连接"""
        async with self._lock:
            self.websockets.discard(websocket)
            self.filters.pop(websocket, None)
    
    def update_filters(self, websocket: WebSocket, filters: Dict[str, Any]):
        """更新WebSocket的过滤器"""
        if websocket in self.websockets:
            self.filters[websocket] = filters
    
    async def get_logs(
        self,
        level: Optional[str] = None,
        source: Optional[str] = None,
        component: Optional[str] = None,
        keyword: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        查询日志
        
        Args:
            level: 日志级别过滤
            source: 日志来源过滤
            component: 组件过滤
            keyword: 关键词过滤
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制
        
        Returns:
            日志条目列表
        """
        filters = {}
        if level:
            filters["level"] = level.upper()
        if source:
            filters["source"] = source.lower()
        if component:
            filters["component"] = component
        if keyword:
            filters["keyword"] = keyword
        
        results = []
        async with self._lock:
            # 从最新到最旧遍历
            for entry in reversed(self.entries):
                entry_dict = entry.to_dict()
                
                # 时间过滤
                if start_time and entry.timestamp < start_time:
                    continue
                if end_time and entry.timestamp > end_time:
                    continue
                
                # 应用其他过滤器
                if self._should_filter(entry_dict, filters):
                    continue
                
                results.append(entry_dict)
                
                if len(results) >= limit:
                    break
        
        return results
    
    async def get_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取日志统计信息
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            统计信息字典
        """
        stats = {
            "total": 0,
            "by_level": {},
            "by_source": {},
            "error_count": 0,
            "warning_count": 0
        }
        
        async with self._lock:
            for entry in self.entries:
                # 时间过滤
                if start_time and entry.timestamp < start_time:
                    continue
                if end_time and entry.timestamp > end_time:
                    continue
                
                stats["total"] += 1
                
                # 按级别统计
                level = entry.level
                stats["by_level"][level] = stats["by_level"].get(level, 0) + 1
                
                # 按来源统计
                source = entry.source
                stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
                
                # 错误和警告计数
                if level == LogLevel.ERROR or level == LogLevel.CRITICAL:
                    stats["error_count"] += 1
                elif level == LogLevel.WARNING:
                    stats["warning_count"] += 1
        
        return stats
    
    async def clear_entries(self):
        """清空日志条目（仅限管理员）"""
        async with self._lock:
            self.entries.clear()
    
    async def export_logs(
        self,
        level: Optional[str] = None,
        source: Optional[str] = None,
        component: Optional[str] = None,
        keyword: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        format: str = "text"  # text, json, csv
    ) -> str:
        """
        导出日志
        
        Args:
            level: 日志级别过滤
            source: 日志来源过滤
            component: 组件过滤
            keyword: 关键词过滤
            start_time: 开始时间
            end_time: 结束时间
            format: 导出格式（text, json, csv）
        
        Returns:
            导出的日志内容
        """
        logs = await self.get_logs(
            level=level,
            source=source,
            component=component,
            keyword=keyword,
            start_time=start_time,
            end_time=end_time,
            limit=100000  # 导出时允许更多条目
        )
        
        if format == "json":
            return json.dumps(logs, ensure_ascii=False, indent=2, default=str)
        elif format == "csv":
            import csv
            import io
            output = io.StringIO()
            if logs:
                writer = csv.DictWriter(output, fieldnames=logs[0].keys())
                writer.writeheader()
                writer.writerows(logs)
            return output.getvalue()
        else:  # text
            lines = []
            for log in logs:
                timestamp = log["timestamp"]
                level = log["level"]
                source = log["source"]
                component = log["component"]
                message = log["message"]
                lines.append(f"[{timestamp}] {level} [{source}/{component}] {message}")
            return "\n".join(lines)


# 全局日志中心实例
_log_center: Optional[LogCenter] = None


def get_log_center() -> LogCenter:
    """获取日志中心实例（单例模式）"""
    global _log_center
    if _log_center is None:
        _log_center = LogCenter()
    return _log_center

