"""
多模态分析性能监控
提供性能指标收集和统计功能
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
from loguru import logger
import time
import asyncio
from threading import Lock

# 性能指标存储
_metrics = {
    "video_analysis": {
        "total_requests": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "total_time": 0.0,
        "error_count": 0,
        "concurrent_requests": 0,
        "max_concurrent": 0
    },
    "audio_analysis": {
        "total_requests": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "total_time": 0.0,
        "error_count": 0,
        "concurrent_requests": 0,
        "max_concurrent": 0
    },
    "text_analysis": {
        "total_requests": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "total_time": 0.0,
        "error_count": 0
    },
    "feature_fusion": {
        "total_requests": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "total_time": 0.0,
        "error_count": 0
    },
    "similarity_calculation": {
        "total_requests": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "total_time": 0.0,
        "error_count": 0
    }
}

# 时间序列数据（最近1小时）
_time_series = {
    "video_analysis": [],
    "audio_analysis": [],
    "text_analysis": [],
    "feature_fusion": [],
    "similarity_calculation": []
}

# 锁，用于线程安全
_metrics_lock = Lock()


class MultimodalMetrics:
    """多模态分析性能指标"""
    
    # 数据库存储实例（可选）
    _storage_instance = None
    _storage_db = None
    
    @classmethod
    def set_storage(cls, storage_instance):
        """设置数据库存储实例"""
        cls._storage_instance = storage_instance
        if hasattr(storage_instance, 'db'):
            cls._storage_db = storage_instance.db
    
    @staticmethod
    def record_request(
        operation: str,
        cache_hit: bool = False,
        duration: float = 0.0,
        error: bool = False,
        concurrent: int = 0
    ):
        """
        记录请求指标（内存存储，数据库存储通过后台任务处理）
        
        Args:
            operation: 操作类型（video_analysis, audio_analysis, text_analysis, feature_fusion, similarity_calculation）
            cache_hit: 是否缓存命中
            duration: 请求持续时间（秒）
            error: 是否发生错误
            concurrent: 并发请求数
        """
        with _metrics_lock:
            if operation not in _metrics:
                logger.warning(f"未知的操作类型: {operation}")
                return
            
            metrics = _metrics[operation]
            metrics["total_requests"] += 1
            
            if cache_hit:
                metrics["cache_hits"] += 1
            else:
                metrics["cache_misses"] += 1
            
            metrics["total_time"] += duration
            
            if error:
                metrics["error_count"] += 1
            
            # 更新并发指标
            if "concurrent_requests" in metrics:
                metrics["concurrent_requests"] = concurrent
                metrics["max_concurrent"] = max(metrics["max_concurrent"], concurrent)
            
            # 记录时间序列数据
            if operation in _time_series:
                timestamp = datetime.now()
                _time_series[operation].append({
                    "timestamp": timestamp.isoformat(),
                    "cache_hit": cache_hit,
                    "duration": duration,
                    "error": error,
                    "concurrent": concurrent
                })
                
                # 只保留最近1小时的数据
                one_hour_ago = timestamp - timedelta(hours=1)
                _time_series[operation] = [
                    item for item in _time_series[operation]
                    if datetime.fromisoformat(item["timestamp"]) > one_hour_ago
                ]
    
    @classmethod
    async def record_request_async(
        cls,
        operation: str,
        cache_hit: bool = False,
        duration: float = 0.0,
        error: bool = False,
        concurrent: int = 0
    ):
        """
        异步记录请求指标（支持数据库存储）
        
        Args:
            operation: 操作类型
            cache_hit: 是否缓存命中
            duration: 请求持续时间（秒）
            error: 是否发生错误
            concurrent: 并发请求数
        """
        # 先记录到内存
        cls.record_request(operation, cache_hit, duration, error, concurrent)
        
        # 异步保存到数据库（如果已设置存储）
        if cls._storage_instance:
            try:
                await cls._storage_instance.save_metric(
                    operation=operation,
                    cache_hit=cache_hit,
                    duration=duration,
                    error=error,
                    concurrent=concurrent
                )
            except Exception as e:
                logger.debug(f"保存性能指标到数据库失败: {e}")
    
    @staticmethod
    def get_metrics(operation: Optional[str] = None) -> Dict[str, Any]:
        """
        获取性能指标
        
        Args:
            operation: 操作类型，如果为None则返回所有操作的指标
            
        Returns:
            性能指标字典
        """
        with _metrics_lock:
            if operation:
                if operation not in _metrics:
                    return {}
                
                metrics = _metrics[operation].copy()
                
                # 计算平均响应时间
                if metrics["total_requests"] > 0:
                    metrics["avg_duration"] = metrics["total_time"] / metrics["total_requests"]
                else:
                    metrics["avg_duration"] = 0.0
                
                # 计算缓存命中率
                total_cache_requests = metrics["cache_hits"] + metrics["cache_misses"]
                if total_cache_requests > 0:
                    metrics["cache_hit_rate"] = metrics["cache_hits"] / total_cache_requests
                else:
                    metrics["cache_hit_rate"] = 0.0
                
                # 计算错误率
                if metrics["total_requests"] > 0:
                    metrics["error_rate"] = metrics["error_count"] / metrics["total_requests"]
                else:
                    metrics["error_rate"] = 0.0
                
                return metrics
            else:
                # 返回所有操作的指标
                result = {}
                for op in _metrics.keys():
                    result[op] = MultimodalMetrics.get_metrics(op)
                return result
    
    @staticmethod
    def get_time_series(operation: str, minutes: int = 60) -> List[Dict[str, Any]]:
        """
        获取时间序列数据
        
        Args:
            operation: 操作类型
            minutes: 时间范围（分钟，默认60分钟）
            
        Returns:
            时间序列数据列表
        """
        with _metrics_lock:
            if operation not in _time_series:
                return []
            
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            return [
                item for item in _time_series[operation]
                if datetime.fromisoformat(item["timestamp"]) > cutoff_time
            ]
    
    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """获取缓存统计信息"""
        with _metrics_lock:
            stats = {
                "total_requests": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "cache_hit_rate": 0.0,
                "operations": {}
            }
            
            for operation, metrics in _metrics.items():
                operation_stats = {
                    "total_requests": metrics["total_requests"],
                    "cache_hits": metrics["cache_hits"],
                    "cache_misses": metrics["cache_misses"]
                }
                
                total_cache_requests = metrics["cache_hits"] + metrics["cache_misses"]
                if total_cache_requests > 0:
                    operation_stats["cache_hit_rate"] = metrics["cache_hits"] / total_cache_requests
                else:
                    operation_stats["cache_hit_rate"] = 0.0
                
                stats["total_requests"] += metrics["total_requests"]
                stats["cache_hits"] += metrics["cache_hits"]
                stats["cache_misses"] += metrics["cache_misses"]
                stats["operations"][operation] = operation_stats
            
            total_cache_requests = stats["cache_hits"] + stats["cache_misses"]
            if total_cache_requests > 0:
                stats["cache_hit_rate"] = stats["cache_hits"] / total_cache_requests
            
            return stats
    
    @staticmethod
    def get_performance_summary() -> Dict[str, Any]:
        """获取性能摘要"""
        with _metrics_lock:
            summary = {
                "timestamp": datetime.now().isoformat(),
                "operations": {},
                "overall": {
                    "total_requests": 0,
                    "total_errors": 0,
                    "total_duration": 0.0,
                    "avg_duration": 0.0,
                    "error_rate": 0.0
                },
                "cache": MultimodalMetrics.get_cache_stats()
            }
            
            for operation, metrics in _metrics.items():
                operation_summary = {
                    "total_requests": metrics["total_requests"],
                    "cache_hits": metrics["cache_hits"],
                    "cache_misses": metrics["cache_misses"],
                    "error_count": metrics["error_count"],
                    "total_duration": metrics["total_time"],
                    "avg_duration": metrics["total_time"] / metrics["total_requests"] if metrics["total_requests"] > 0 else 0.0,
                    "error_rate": metrics["error_count"] / metrics["total_requests"] if metrics["total_requests"] > 0 else 0.0
                }
                
                total_cache_requests = metrics["cache_hits"] + metrics["cache_misses"]
                if total_cache_requests > 0:
                    operation_summary["cache_hit_rate"] = metrics["cache_hits"] / total_cache_requests
                else:
                    operation_summary["cache_hit_rate"] = 0.0
                
                if "max_concurrent" in metrics:
                    operation_summary["max_concurrent"] = metrics["max_concurrent"]
                
                summary["operations"][operation] = operation_summary
                summary["overall"]["total_requests"] += metrics["total_requests"]
                summary["overall"]["total_errors"] += metrics["error_count"]
                summary["overall"]["total_duration"] += metrics["total_time"]
            
            if summary["overall"]["total_requests"] > 0:
                summary["overall"]["avg_duration"] = summary["overall"]["total_duration"] / summary["overall"]["total_requests"]
                summary["overall"]["error_rate"] = summary["overall"]["total_errors"] / summary["overall"]["total_requests"]
            
            return summary
    
    @staticmethod
    def reset_metrics():
        """重置所有指标"""
        with _metrics_lock:
            for operation in _metrics.keys():
                _metrics[operation] = {
                    "total_requests": 0,
                    "cache_hits": 0,
                    "cache_misses": 0,
                    "total_time": 0.0,
                    "error_count": 0,
                    "concurrent_requests": 0,
                    "max_concurrent": 0
                }
                _time_series[operation] = []
            logger.info("多模态分析性能指标已重置")


class PerformanceMonitor:
    """性能监控装饰器"""
    
    def __init__(self, operation: str):
        """
        初始化性能监控装饰器
        
        Args:
            operation: 操作类型
        """
        self.operation = operation
        self.start_time = None
        self.cache_hit = False
        self.error = False
    
    async def __aenter__(self):
        """进入上下文管理器"""
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器"""
        duration = time.time() - self.start_time if self.start_time else 0.0
        
        if exc_type is not None:
            self.error = True
        
        # 获取当前并发数（需要从分析器获取）
        concurrent = 0
        if self.operation in ["video_analysis", "audio_analysis"]:
            # 这里需要从分析器获取，暂时使用0
            pass
        
        MultimodalMetrics.record_request(
            operation=self.operation,
            cache_hit=self.cache_hit,
            duration=duration,
            error=self.error,
            concurrent=concurrent
        )
        
        return False  # 不抑制异常
    
    def set_cache_hit(self, cache_hit: bool = True):
        """设置缓存命中状态"""
        self.cache_hit = cache_hit

