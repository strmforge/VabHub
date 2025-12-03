"""
API性能监控服务
提供API响应时间、错误率等性能指标的监控和历史记录
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque, defaultdict
from loguru import logger

from app.core.middleware import PerformanceMonitoringMiddleware


class APIMonitor:
    """API性能监控服务"""
    
    def __init__(self):
        # 历史数据存储（内存中，最近1000条）
        self.response_time_history = defaultdict(lambda: deque(maxlen=1000))
        self.error_history = deque(maxlen=1000)
        self.request_count_history = defaultdict(lambda: deque(maxlen=1000))
    
    def get_performance_metrics(
        self,
        middleware: Optional[PerformanceMonitoringMiddleware] = None,
        endpoint: Optional[str] = None
    ) -> Dict:
        """
        获取API性能指标
        
        Args:
            middleware: 性能监控中间件实例
            endpoint: 端点路径（可选，用于过滤）
        
        Returns:
            API性能指标数据
        """
        if not middleware:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "total_requests": 0,
                    "total_errors": 0,
                    "error_rate": 0.0,
                    "avg_response_time": 0.0
                },
                "endpoints": {}
            }
        
        # 获取汇总信息
        summary = middleware.get_summary()
        
        # 获取所有端点指标
        all_metrics = middleware.get_metrics()
        
        # 如果指定了端点，只返回该端点的指标
        if endpoint:
            filtered_metrics = {
                k: v for k, v in all_metrics.items()
                if endpoint in k
            }
        else:
            filtered_metrics = all_metrics
        
        # 保存到历史记录
        self._save_to_history(summary, filtered_metrics)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": summary,
            "endpoints": filtered_metrics
        }
    
    def _save_to_history(self, summary: Dict, endpoints: Dict):
        """保存到历史记录"""
        timestamp = datetime.utcnow()
        
        # 保存汇总信息
        for endpoint_key, metrics in endpoints.items():
            if "response_times" in metrics and metrics["response_times"]:
                avg_time = sum(metrics["response_times"]) / len(metrics["response_times"])
                self.response_time_history[endpoint_key].append({
                    "timestamp": timestamp.isoformat(),
                    "avg_response_time": round(avg_time, 3),
                    "count": metrics.get("request_count", 0)
                })
            
            if "request_count" in metrics:
                self.request_count_history[endpoint_key].append({
                    "timestamp": timestamp.isoformat(),
                    "count": metrics["request_count"]
                })
        
        # 保存错误信息
        if summary.get("total_errors", 0) > 0:
            self.error_history.append({
                "timestamp": timestamp.isoformat(),
                "error_count": summary["total_errors"],
                "error_rate": summary.get("error_rate", 0.0)
            })
    
    def get_response_time_history(self, endpoint: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """获取响应时间历史记录"""
        if endpoint:
            return list(self.response_time_history.get(endpoint, []))[-limit:]
        else:
            # 返回所有端点的历史记录
            result = {}
            for key, history in self.response_time_history.items():
                result[key] = list(history)[-limit:]
            return result
    
    def get_error_history(self, limit: int = 100) -> List[Dict]:
        """获取错误历史记录"""
        return list(self.error_history)[-limit:]
    
    def get_request_count_history(self, endpoint: Optional[str] = None, limit: int = 100) -> Dict:
        """获取请求数量历史记录"""
        if endpoint:
            return list(self.request_count_history.get(endpoint, []))[-limit:]
        else:
            result = {}
            for key, history in self.request_count_history.items():
                result[key] = list(history)[-limit:]
            return result
    
    def get_slow_endpoints(self, threshold: float = 1.0, limit: int = 10) -> List[Dict]:
        """获取慢端点列表"""
        slow_endpoints = []
        
        for endpoint_key, history in self.response_time_history.items():
            if history:
                latest = history[-1]
                if latest.get("avg_response_time", 0) > threshold:
                    slow_endpoints.append({
                        "endpoint": endpoint_key,
                        "avg_response_time": latest["avg_response_time"],
                        "count": latest.get("count", 0),
                        "timestamp": latest["timestamp"]
                    })
        
        # 按响应时间排序
        slow_endpoints.sort(key=lambda x: x["avg_response_time"], reverse=True)
        return slow_endpoints[:limit]
    
    def get_error_endpoints(self, limit: int = 10) -> List[Dict]:
        """获取错误端点列表"""
        error_endpoints = []
        
        # 从错误历史中提取端点信息
        if self.error_history:
            for error_record in list(self.error_history)[-limit:]:
                error_endpoints.append({
                    "timestamp": error_record.get("timestamp", ""),
                    "error_count": error_record.get("error_count", 0),
                    "error_rate": error_record.get("error_rate", 0.0)
                })
        
        return error_endpoints


# 全局API监控实例
_api_monitor: Optional[APIMonitor] = None


def get_api_monitor() -> APIMonitor:
    """获取API监控实例（单例）"""
    global _api_monitor
    if _api_monitor is None:
        _api_monitor = APIMonitor()
    return _api_monitor

