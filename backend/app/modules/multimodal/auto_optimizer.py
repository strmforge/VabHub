"""
多模态分析自动化优化器
自动调整TTL和并发数
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.multimodal_metrics import MultimodalOptimizationHistory
from app.modules.multimodal.metrics_storage import MetricsStorage
from app.modules.multimodal.cache_optimizer import CacheOptimizer
from app.modules.multimodal.concurrency_optimizer import ConcurrencyOptimizer


class AutoOptimizer:
    """自动化优化器"""
    
    def __init__(self, db: AsyncSession):
        """
        初始化自动化优化器
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.metrics_storage = MetricsStorage(db)
        self.cache_optimizer = CacheOptimizer()
        self.concurrency_optimizer = ConcurrencyOptimizer()
        
        # 优化配置
        self.optimization_config = {
            "cache_ttl": {
                "enabled": True,
                "target_hit_rate": 0.8,
                "check_interval": 3600,  # 1小时检查一次
                "min_ttl_multiplier": 0.5,
                "max_ttl_multiplier": 3.0
            },
            "concurrency": {
                "enabled": True,
                "target_avg_duration": 1.0,
                "check_interval": 3600,  # 1小时检查一次
                "min_concurrent": 1,
                "max_concurrent": 10
            }
        }
        
        # 当前优化状态
        self.current_ttl = {
            "video_analysis": 86400,
            "audio_analysis": 86400,
            "text_analysis": 3600,
            "feature_fusion": 3600,
            "similarity_calculation": 3600
        }
        
        self.current_concurrency = {
            "video_analysis": 3,
            "audio_analysis": 3,
            "text_analysis": 10,
            "feature_fusion": 5,
            "similarity_calculation": 5
        }
    
    async def optimize_all(self) -> Dict[str, Any]:
        """
        优化所有操作
        
        Returns:
            优化结果
        """
        try:
            results = {
                "cache_ttl": {},
                "concurrency": {},
                "timestamp": datetime.now().isoformat()
            }
            
            operations = [
                "video_analysis",
                "audio_analysis",
                "text_analysis",
                "feature_fusion",
                "similarity_calculation"
            ]
            
            # 优化缓存TTL
            if self.optimization_config["cache_ttl"]["enabled"]:
                for operation in operations:
                    try:
                        result = await self.optimize_cache_ttl(operation)
                        if result:
                            results["cache_ttl"][operation] = result
                    except Exception as e:
                        logger.error(f"优化{operation}的缓存TTL失败: {e}")
            
            # 优化并发数
            if self.optimization_config["concurrency"]["enabled"]:
                for operation in operations:
                    try:
                        result = await self.optimize_concurrency(operation)
                        if result:
                            results["concurrency"][operation] = result
                    except Exception as e:
                        logger.error(f"优化{operation}的并发数失败: {e}")
            
            return results
        except Exception as e:
            logger.error(f"优化所有操作失败: {e}")
            return {}
    
    async def optimize_cache_ttl(self, operation: str) -> Optional[Dict[str, Any]]:
        """
        优化缓存TTL
        
        Args:
            operation: 操作类型
            
        Returns:
            优化结果
        """
        try:
            config = self.optimization_config["cache_ttl"]
            target_hit_rate = config["target_hit_rate"]
            
            # 获取优化建议
            optimization = await self.cache_optimizer.optimize_cache_ttl(
                operation, target_hit_rate
            )
            
            if "error" in optimization:
                return None
            
            current_ttl = self.current_ttl.get(operation, 3600)
            recommended_ttl = optimization.get("recommended_ttl", current_ttl)
            
            # 检查是否需要优化
            ttl_multiplier = recommended_ttl / current_ttl if current_ttl > 0 else 1.0
            
            if (ttl_multiplier < config["min_ttl_multiplier"] or 
                ttl_multiplier > config["max_ttl_multiplier"]):
                # 变化太大，不进行优化
                return None
            
            # 如果变化小于10%，不进行优化
            if abs(ttl_multiplier - 1.0) < 0.1:
                return None
            
            # 获取优化前的指标
            before_metrics = await self.metrics_storage.get_metrics_statistics(
                operation=operation,
                start_time=datetime.now() - timedelta(hours=1)
            )
            
            # 更新TTL
            self.current_ttl[operation] = recommended_ttl
            
            # 记录优化历史
            optimization_history = MultimodalOptimizationHistory(
                operation=operation,
                optimization_type="cache_ttl",
                old_value=current_ttl,
                new_value=recommended_ttl,
                reason=optimization.get("recommendation", ""),
                timestamp=datetime.now(),
                improvement=(ttl_multiplier - 1.0) * 100,
                before_metrics=before_metrics.get(operation, {}),
                after_metrics={},  # 优化后的指标需要等待一段时间才能获取
                extra_metadata={
                    "target_hit_rate": target_hit_rate,
                    "current_hit_rate": optimization.get("current_hit_rate", 0.0)
                }
            )
            
            self.db.add(optimization_history)
            await self.db.flush()
            
            logger.info(f"优化{operation}的缓存TTL: {current_ttl} -> {recommended_ttl}")
            
            return {
                "operation": operation,
                "old_value": current_ttl,
                "new_value": recommended_ttl,
                "improvement": (ttl_multiplier - 1.0) * 100,
                "reason": optimization.get("recommendation", "")
            }
        except Exception as e:
            logger.error(f"优化{operation}的缓存TTL失败: {e}")
            return None
    
    async def optimize_concurrency(self, operation: str) -> Optional[Dict[str, Any]]:
        """
        优化并发数
        
        Args:
            operation: 操作类型
            
        Returns:
            优化结果
        """
        try:
            config = self.optimization_config["concurrency"]
            target_avg_duration = config["target_avg_duration"]
            
            # 获取优化建议
            optimization = await self.concurrency_optimizer.optimize_concurrency(
                operation, target_avg_duration
            )
            
            if "error" in optimization:
                return None
            
            current_concurrent = self.current_concurrency.get(operation, 3)
            recommended_concurrent = optimization.get("recommended_concurrent", current_concurrent)
            
            # 检查是否在允许范围内
            if (recommended_concurrent < config["min_concurrent"] or
                recommended_concurrent > config["max_concurrent"]):
                return None
            
            # 如果变化小于1，不进行优化
            if abs(recommended_concurrent - current_concurrent) < 1:
                return None
            
            # 获取优化前的指标
            before_metrics = await self.metrics_storage.get_metrics_statistics(
                operation=operation,
                start_time=datetime.now() - timedelta(hours=1)
            )
            
            # 更新并发数
            self.current_concurrency[operation] = recommended_concurrent
            
            # 记录优化历史
            improvement = 0.0
            if current_concurrent > 0:
                improvement = ((current_concurrent - recommended_concurrent) / current_concurrent) * 100
            
            optimization_history = MultimodalOptimizationHistory(
                operation=operation,
                optimization_type="concurrency",
                old_value=float(current_concurrent),
                new_value=float(recommended_concurrent),
                reason=optimization.get("recommendation", ""),
                timestamp=datetime.now(),
                improvement=improvement,
                before_metrics=before_metrics.get(operation, {}),
                after_metrics={},  # 优化后的指标需要等待一段时间才能获取
                extra_metadata={
                    "target_avg_duration": target_avg_duration,
                    "current_avg_duration": optimization.get("current_avg_duration", 0.0)
                }
            )
            
            self.db.add(optimization_history)
            await self.db.flush()
            
            logger.info(f"优化{operation}的并发数: {current_concurrent} -> {recommended_concurrent}")
            
            return {
                "operation": operation,
                "old_value": current_concurrent,
                "new_value": recommended_concurrent,
                "improvement": improvement,
                "reason": optimization.get("recommendation", "")
            }
        except Exception as e:
            logger.error(f"优化{operation}的并发数失败: {e}")
            return None
    
    async def start_auto_optimization(self, interval: int = 3600):
        """
        启动自动优化任务
        
        Args:
            interval: 优化间隔（秒，默认1小时）
        """
        logger.info(f"启动自动优化任务，间隔: {interval}秒")
        
        while True:
            try:
                await asyncio.sleep(interval)
                logger.info("开始自动优化...")
                results = await self.optimize_all()
                logger.info(f"自动优化完成: {results}")
            except Exception as e:
                logger.error(f"自动优化失败: {e}")
    
    def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {
            "cache_ttl": self.current_ttl.copy(),
            "concurrency": self.current_concurrency.copy(),
            "optimization_config": self.optimization_config.copy()
        }
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        if "cache_ttl" in config:
            self.optimization_config["cache_ttl"].update(config["cache_ttl"])
        if "concurrency" in config:
            self.optimization_config["concurrency"].update(config["concurrency"])

