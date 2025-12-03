"""
多模态分析并发优化器
提供并发策略优化和动态调整功能
"""

from typing import Dict, List, Optional, Any
from loguru import logger
import asyncio
import time
from datetime import datetime, timedelta

try:
    from app.modules.multimodal.metrics import MultimodalMetrics
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    logger.warning("性能监控系统不可用，并发优化功能将受限")


class ConcurrencyOptimizer:
    """并发优化器"""
    
    def __init__(self):
        """初始化并发优化器"""
        self._optimal_concurrency = {
            "video_analysis": 3,
            "audio_analysis": 3,
            "text_analysis": 10,  # 文本分析可以更高并发
            "feature_fusion": 5,
            "similarity_calculation": 5
        }
    
    async def analyze_concurrency_performance(self, operation: str) -> Dict[str, Any]:
        """
        分析并发性能
        
        Args:
            operation: 操作类型
            
        Returns:
            并发性能分析结果
        """
        if not METRICS_AVAILABLE:
            return {"error": "性能监控系统不可用"}
        
        try:
            metrics = MultimodalMetrics.get_metrics(operation)
            time_series = MultimodalMetrics.get_time_series(operation, minutes=60)
            
            # 分析并发数和响应时间的关系
            concurrency_analysis = {
                "operation": operation,
                "max_concurrent": metrics.get("max_concurrent", 0),
                "avg_duration": metrics.get("avg_duration", 0.0),
                "total_requests": metrics.get("total_requests", 0),
                "recommendations": []
            }
            
            # 分析时间序列数据
            if time_series:
                # 按并发数分组统计
                concurrency_groups = {}
                for item in time_series:
                    concurrent = item.get("concurrent", 0)
                    if concurrent not in concurrency_groups:
                        concurrency_groups[concurrent] = {
                            "count": 0,
                            "total_duration": 0.0,
                            "errors": 0
                        }
                    concurrency_groups[concurrent]["count"] += 1
                    concurrency_groups[concurrent]["total_duration"] += item.get("duration", 0.0)
                    if item.get("error"):
                        concurrency_groups[concurrent]["errors"] += 1
                
                # 计算每个并发数的平均响应时间
                for concurrent, stats in concurrency_groups.items():
                    if stats["count"] > 0:
                        stats["avg_duration"] = stats["total_duration"] / stats["count"]
                        stats["error_rate"] = stats["errors"] / stats["count"]
                
                concurrency_analysis["concurrency_groups"] = concurrency_groups
                
                # 生成优化建议
                if metrics.get("max_concurrent", 0) > 10:
                    concurrency_analysis["recommendations"].append("当前最大并发数较高，建议适当降低以优化资源使用")
                elif metrics.get("max_concurrent", 0) < 2:
                    concurrency_analysis["recommendations"].append("当前最大并发数较低，可以适当增加以提高吞吐量")
            
            return concurrency_analysis
            
        except Exception as e:
            logger.error(f"分析并发性能失败: {e}")
            return {"error": str(e)}
    
    async def optimize_concurrency(self, operation: str, target_avg_duration: float = 1.0) -> Dict[str, Any]:
        """
        优化并发数
        
        Args:
            operation: 操作类型
            target_avg_duration: 目标平均响应时间（秒，默认1.0秒）
            
        Returns:
            优化建议
        """
        if not METRICS_AVAILABLE:
            return {"error": "性能监控系统不可用"}
        
        try:
            metrics = MultimodalMetrics.get_metrics(operation)
            current_avg_duration = metrics.get("avg_duration", 0.0)
            current_max_concurrent = metrics.get("max_concurrent", 0)
            
            # 计算建议的并发数
            if current_avg_duration > target_avg_duration:
                # 当前平均响应时间高于目标，建议减少并发数
                recommended_concurrent = max(1, int(current_max_concurrent * 0.8))
            else:
                # 当前平均响应时间低于目标，可以适当增加并发数
                recommended_concurrent = min(10, int(current_max_concurrent * 1.2) if current_max_concurrent > 0 else 3)
            
            # 根据操作类型确定基础并发数
            base_concurrent = self._optimal_concurrency.get(operation, 3)
            
            # 如果建议的并发数与基础并发数差异较大，使用建议值
            if abs(recommended_concurrent - base_concurrent) > 2:
                final_recommended = recommended_concurrent
            else:
                final_recommended = base_concurrent
            
            return {
                "operation": operation,
                "current_avg_duration": current_avg_duration,
                "target_avg_duration": target_avg_duration,
                "current_max_concurrent": current_max_concurrent,
                "base_concurrent": base_concurrent,
                "recommended_concurrent": final_recommended,
                "recommendation": f"建议将{operation}的最大并发数调整为{final_recommended}"
            }
            
        except Exception as e:
            logger.error(f"优化并发数失败: {e}")
            return {"error": str(e)}
    
    async def get_optimal_concurrency(self, operation: str) -> int:
        """
        获取最优并发数
        
        Args:
            operation: 操作类型
            
        Returns:
            最优并发数
        """
        # 基于性能数据动态调整
        if METRICS_AVAILABLE:
            optimization = await self.optimize_concurrency(operation)
            if "recommended_concurrent" in optimization:
                return optimization["recommended_concurrent"]
        
        # 返回默认值
        return self._optimal_concurrency.get(operation, 3)
    
    async def monitor_concurrency(self, operation: str, duration: int = 60) -> Dict[str, Any]:
        """
        监控并发性能
        
        Args:
            operation: 操作类型
            duration: 监控时长（秒，默认60秒）
            
        Returns:
            监控结果
        """
        if not METRICS_AVAILABLE:
            return {"error": "性能监控系统不可用"}
        
        try:
            start_time = time.time()
            metrics_start = MultimodalMetrics.get_metrics(operation)
            
            # 等待指定时长
            await asyncio.sleep(duration)
            
            metrics_end = MultimodalMetrics.get_metrics(operation)
            
            # 计算增量
            delta_requests = metrics_end.get("total_requests", 0) - metrics_start.get("total_requests", 0)
            delta_errors = metrics_end.get("error_count", 0) - metrics_start.get("error_count", 0)
            delta_duration = metrics_end.get("total_time", 0.0) - metrics_start.get("total_time", 0.0)
            
            # 计算平均指标
            avg_duration = delta_duration / delta_requests if delta_requests > 0 else 0.0
            error_rate = delta_errors / delta_requests if delta_requests > 0 else 0.0
            requests_per_second = delta_requests / duration if duration > 0 else 0.0
            
            return {
                "operation": operation,
                "duration": duration,
                "total_requests": delta_requests,
                "requests_per_second": requests_per_second,
                "avg_duration": avg_duration,
                "error_count": delta_errors,
                "error_rate": error_rate,
                "max_concurrent": metrics_end.get("max_concurrent", 0)
            }
            
        except Exception as e:
            logger.error(f"监控并发性能失败: {e}")
            return {"error": str(e)}

