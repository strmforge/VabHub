"""
性能监控和优化
提供性能监控、缓存优化、数据库查询优化等功能
"""

import time
import asyncio
from typing import Dict, List, Optional, Callable, Any
from functools import wraps
from loguru import logger
from datetime import datetime, timedelta
from collections import defaultdict

# 性能统计
performance_stats = {
    "api_calls": defaultdict(list),
    "db_queries": defaultdict(list),
    "cache_hits": 0,
    "cache_misses": 0,
    "slow_queries": []
}


def monitor_performance(operation_name: str):
    """性能监控装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time
                performance_stats["api_calls"][operation_name].append(elapsed)
                
                # 记录慢操作
                if elapsed > 1.0:
                    logger.warning(f"慢操作: {operation_name} - {elapsed:.2f}s")
                    performance_stats["slow_queries"].append({
                        "operation": operation_name,
                        "duration": elapsed,
                        "timestamp": datetime.now()
                    })
                
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"操作失败: {operation_name} - {elapsed:.2f}s - {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                performance_stats["api_calls"][operation_name].append(elapsed)
                
                # 记录慢操作
                if elapsed > 1.0:
                    logger.warning(f"慢操作: {operation_name} - {elapsed:.2f}s")
                
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"操作失败: {operation_name} - {elapsed:.2f}s - {e}")
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def get_performance_stats() -> Dict[str, Any]:
    """获取性能统计"""
    stats = {
        "api_calls": {},
        "cache_stats": {
            "hits": performance_stats["cache_hits"],
            "misses": performance_stats["cache_misses"],
            "hit_rate": performance_stats["cache_hits"] / (performance_stats["cache_hits"] + performance_stats["cache_misses"]) if (performance_stats["cache_hits"] + performance_stats["cache_misses"]) > 0 else 0
        },
        "slow_queries": performance_stats["slow_queries"][-10:]  # 最近10个慢查询
    }
    
    # 计算API调用统计
    for operation, times in performance_stats["api_calls"].items():
        if times:
            stats["api_calls"][operation] = {
                "count": len(times),
                "avg": sum(times) / len(times),
                "min": min(times),
                "max": max(times),
                "total": sum(times)
            }
    
    return stats


def reset_performance_stats():
    """重置性能统计"""
    performance_stats["api_calls"].clear()
    performance_stats["cache_hits"] = 0
    performance_stats["cache_misses"] = 0
    performance_stats["slow_queries"].clear()


def record_cache_hit():
    """记录缓存命中"""
    performance_stats["cache_hits"] += 1


def record_cache_miss():
    """记录缓存未命中"""
    performance_stats["cache_misses"] += 1

