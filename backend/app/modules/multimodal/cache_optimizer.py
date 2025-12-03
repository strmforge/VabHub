"""
多模态分析缓存优化器
提供缓存策略优化和缓存预热功能
"""

from typing import Dict, List, Optional, Any
from loguru import logger
import asyncio
from datetime import datetime, timedelta

try:
    from app.core.cache import get_cache
    from app.modules.multimodal.metrics import MultimodalMetrics
    CACHE_AVAILABLE = True
    METRICS_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    METRICS_AVAILABLE = False
    logger.warning("缓存系统或性能监控系统不可用，缓存优化功能将受限")


class CacheOptimizer:
    """缓存优化器"""
    
    def __init__(self):
        """初始化缓存优化器"""
        if CACHE_AVAILABLE:
            self.cache = get_cache()
        else:
            self.cache = None
    
    async def analyze_cache_performance(self) -> Dict[str, Any]:
        """
        分析缓存性能
        
        Returns:
            缓存性能分析结果
        """
        if not METRICS_AVAILABLE:
            return {"error": "性能监控系统不可用"}
        
        try:
            cache_stats = MultimodalMetrics.get_cache_stats()
            
            # 分析缓存命中率
            analysis = {
                "overall_cache_hit_rate": cache_stats.get("cache_hit_rate", 0.0),
                "total_requests": cache_stats.get("total_requests", 0),
                "cache_hits": cache_stats.get("cache_hits", 0),
                "cache_misses": cache_stats.get("cache_misses", 0),
                "operations": {},
                "recommendations": []
            }
            
            # 分析每个操作的缓存性能
            for operation, stats in cache_stats.get("operations", {}).items():
                operation_analysis = {
                    "cache_hit_rate": stats.get("cache_hit_rate", 0.0),
                    "total_requests": stats.get("total_requests", 0),
                    "cache_hits": stats.get("cache_hits", 0),
                    "cache_misses": stats.get("cache_misses", 0)
                }
                
                # 生成优化建议
                if operation_analysis["cache_hit_rate"] < 0.5:
                    operation_analysis["recommendation"] = "缓存命中率较低，建议增加缓存TTL或优化缓存键生成策略"
                elif operation_analysis["cache_hit_rate"] < 0.7:
                    operation_analysis["recommendation"] = "缓存命中率中等，可以考虑优化缓存策略"
                else:
                    operation_analysis["recommendation"] = "缓存命中率良好"
                
                analysis["operations"][operation] = operation_analysis
            
            # 生成总体优化建议
            if analysis["overall_cache_hit_rate"] < 0.5:
                analysis["recommendations"].append("总体缓存命中率较低，建议检查缓存配置和TTL设置")
            elif analysis["overall_cache_hit_rate"] < 0.7:
                analysis["recommendations"].append("总体缓存命中率中等，建议优化缓存策略")
            else:
                analysis["recommendations"].append("总体缓存命中率良好，缓存策略运行正常")
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析缓存性能失败: {e}")
            return {"error": str(e)}
    
    async def optimize_cache_ttl(self, operation: str, target_hit_rate: float = 0.8) -> Dict[str, Any]:
        """
        优化缓存TTL
        
        Args:
            operation: 操作类型
            target_hit_rate: 目标缓存命中率（默认0.8）
            
        Returns:
            优化建议
        """
        if not METRICS_AVAILABLE:
            return {"error": "性能监控系统不可用"}
        
        try:
            metrics = MultimodalMetrics.get_metrics(operation)
            current_hit_rate = metrics.get("cache_hit_rate", 0.0)
            
            # 计算建议的TTL
            if current_hit_rate < target_hit_rate:
                # 当前命中率低于目标，建议增加TTL
                recommended_ttl_multiplier = target_hit_rate / current_hit_rate if current_hit_rate > 0 else 2.0
                recommended_ttl_multiplier = min(recommended_ttl_multiplier, 3.0)  # 最多增加3倍
            else:
                # 当前命中率高于目标，可以适当减少TTL
                recommended_ttl_multiplier = 1.0
            
            # 根据操作类型确定基础TTL
            base_ttl = {
                "video_analysis": 86400,  # 24小时
                "audio_analysis": 86400,  # 24小时
                "text_analysis": 3600,    # 1小时
                "feature_fusion": 3600,   # 1小时
                "similarity_calculation": 3600  # 1小时
            }.get(operation, 3600)
            
            recommended_ttl = int(base_ttl * recommended_ttl_multiplier)
            
            return {
                "operation": operation,
                "current_hit_rate": current_hit_rate,
                "target_hit_rate": target_hit_rate,
                "current_ttl": base_ttl,
                "recommended_ttl": recommended_ttl,
                "ttl_multiplier": recommended_ttl_multiplier,
                "recommendation": f"建议将{operation}的缓存TTL调整为{recommended_ttl}秒（{recommended_ttl/3600:.1f}小时）"
            }
            
        except Exception as e:
            logger.error(f"优化缓存TTL失败: {e}")
            return {"error": str(e)}
    
    async def warmup_cache(self, file_paths: List[str], operation: str = "video_analysis") -> Dict[str, Any]:
        """
        缓存预热
        
        Args:
            file_paths: 文件路径列表
            operation: 操作类型（video_analysis, audio_analysis）
            
        Returns:
            预热结果
        """
        try:
            if operation == "video_analysis":
                from app.modules.multimodal.video_analyzer import VideoAnalyzer
                analyzer = VideoAnalyzer(enable_cache=True, cache_ttl=86400, max_concurrent=3)
                
                results = []
                for file_path in file_paths:
                    try:
                        result = await analyzer.analyze_video(file_path, detect_scenes=True)
                        results.append({
                            "file_path": file_path,
                            "success": "error" not in result,
                            "cached": False  # 预热时总是未缓存
                        })
                    except Exception as e:
                        logger.error(f"预热缓存失败: {file_path}, 错误: {e}")
                        results.append({
                            "file_path": file_path,
                            "success": False,
                            "error": str(e)
                        })
                
                return {
                    "operation": operation,
                    "total_files": len(file_paths),
                    "success_count": sum(1 for r in results if r.get("success")),
                    "failure_count": sum(1 for r in results if not r.get("success")),
                    "results": results
                }
                
            elif operation == "audio_analysis":
                from app.modules.multimodal.audio_analyzer import AudioAnalyzer
                analyzer = AudioAnalyzer(enable_cache=True, cache_ttl=86400, max_concurrent=3)
                
                results = []
                for file_path in file_paths:
                    try:
                        result = await analyzer.analyze_audio(file_path, extract_features=True)
                        results.append({
                            "file_path": file_path,
                            "success": "error" not in result,
                            "cached": False
                        })
                    except Exception as e:
                        logger.error(f"预热缓存失败: {file_path}, 错误: {e}")
                        results.append({
                            "file_path": file_path,
                            "success": False,
                            "error": str(e)
                        })
                
                return {
                    "operation": operation,
                    "total_files": len(file_paths),
                    "success_count": sum(1 for r in results if r.get("success")),
                    "failure_count": sum(1 for r in results if not r.get("success")),
                    "results": results
                }
            else:
                return {"error": f"不支持的操作类型: {operation}"}
                
        except Exception as e:
            logger.error(f"缓存预热失败: {e}")
            return {"error": str(e)}
    
    async def cleanup_stale_cache(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        清理过期缓存
        
        Args:
            operation: 操作类型，如果为None则清理所有操作的缓存
            
        Returns:
            清理结果
        """
        if not CACHE_AVAILABLE:
            return {"error": "缓存系统不可用"}
        
        try:
            # 这里需要根据实际的缓存实现来清理
            # 暂时返回占位符
            return {
                "operation": operation or "all",
                "cleaned_count": 0,
                "message": "缓存清理功能待实现"
            }
        except Exception as e:
            logger.error(f"清理过期缓存失败: {e}")
            return {"error": str(e)}

