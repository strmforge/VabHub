"""
多模态分析性能告警系统
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload

from app.models.multimodal_metrics import MultimodalPerformanceAlert
from app.models.notification import Notification
from app.modules.multimodal.metrics_storage import MetricsStorage


class AlertType(str, Enum):
    """告警类型"""
    CACHE_HIT_RATE_LOW = "cache_hit_rate_low"  # 缓存命中率低
    RESPONSE_TIME_HIGH = "response_time_high"  # 响应时间高
    ERROR_RATE_HIGH = "error_rate_high"  # 错误率高
    CONCURRENT_HIGH = "concurrent_high"  # 并发数高
    CACHE_HIT_RATE_VERY_LOW = "cache_hit_rate_very_low"  # 缓存命中率极低
    RESPONSE_TIME_VERY_HIGH = "response_time_very_high"  # 响应时间极高
    ERROR_RATE_VERY_HIGH = "error_rate_very_high"  # 错误率极高


class AlertSeverity(str, Enum):
    """告警严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertSystem:
    """性能告警系统"""
    
    # 默认阈值
    DEFAULT_THRESHOLDS = {
        "cache_hit_rate_low": 0.5,  # 缓存命中率低于50%
        "cache_hit_rate_very_low": 0.3,  # 缓存命中率低于30%
        "response_time_high": 5.0,  # 响应时间高于5秒
        "response_time_very_high": 10.0,  # 响应时间高于10秒
        "error_rate_high": 0.1,  # 错误率高于10%
        "error_rate_very_high": 0.2,  # 错误率高于20%
        "concurrent_high": 10,  # 并发数高于10
    }
    
    def __init__(self, db: AsyncSession, thresholds: Optional[Dict[str, float]] = None):
        """
        初始化告警系统
        
        Args:
            db: 数据库会话
            thresholds: 自定义阈值
        """
        self.db = db
        self.metrics_storage = MetricsStorage(db)
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS.copy()
    
    async def check_alerts(
        self,
        operation: Optional[str] = None,
        time_window: int = 300  # 5分钟
    ) -> List[MultimodalPerformanceAlert]:
        """
        检查告警
        
        Args:
            operation: 操作类型，如果为None则检查所有操作
            time_window: 时间窗口（秒）
            
        Returns:
            告警列表
        """
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(seconds=time_window)
            
            # 获取性能指标统计
            statistics = await self.metrics_storage.get_metrics_statistics(
                operation=operation,
                start_time=start_time,
                end_time=end_time
            )
            
            alerts = []
            
            for op, stats in statistics.items():
                # 检查缓存命中率
                if stats["cache_hit_rate"] < self.thresholds.get("cache_hit_rate_very_low", 0.3):
                    alert = await self._create_alert(
                        operation=op,
                        alert_type=AlertType.CACHE_HIT_RATE_VERY_LOW,
                        severity=AlertSeverity.CRITICAL,
                        message=f"{op}的缓存命中率极低: {stats['cache_hit_rate']:.2%}",
                        threshold=self.thresholds.get("cache_hit_rate_very_low", 0.3),
                        actual_value=stats["cache_hit_rate"]
                    )
                    if alert:
                        alerts.append(alert)
                elif stats["cache_hit_rate"] < self.thresholds.get("cache_hit_rate_low", 0.5):
                    alert = await self._create_alert(
                        operation=op,
                        alert_type=AlertType.CACHE_HIT_RATE_LOW,
                        severity=AlertSeverity.WARNING,
                        message=f"{op}的缓存命中率较低: {stats['cache_hit_rate']:.2%}",
                        threshold=self.thresholds.get("cache_hit_rate_low", 0.5),
                        actual_value=stats["cache_hit_rate"]
                    )
                    if alert:
                        alerts.append(alert)
                
                # 检查响应时间
                if stats["avg_duration"] > self.thresholds.get("response_time_very_high", 10.0):
                    alert = await self._create_alert(
                        operation=op,
                        alert_type=AlertType.RESPONSE_TIME_VERY_HIGH,
                        severity=AlertSeverity.CRITICAL,
                        message=f"{op}的平均响应时间极高: {stats['avg_duration']:.2f}秒",
                        threshold=self.thresholds.get("response_time_very_high", 10.0),
                        actual_value=stats["avg_duration"]
                    )
                    if alert:
                        alerts.append(alert)
                elif stats["avg_duration"] > self.thresholds.get("response_time_high", 5.0):
                    alert = await self._create_alert(
                        operation=op,
                        alert_type=AlertType.RESPONSE_TIME_HIGH,
                        severity=AlertSeverity.WARNING,
                        message=f"{op}的平均响应时间较高: {stats['avg_duration']:.2f}秒",
                        threshold=self.thresholds.get("response_time_high", 5.0),
                        actual_value=stats["avg_duration"]
                    )
                    if alert:
                        alerts.append(alert)
                
                # 检查错误率
                if stats["error_rate"] > self.thresholds.get("error_rate_very_high", 0.2):
                    alert = await self._create_alert(
                        operation=op,
                        alert_type=AlertType.ERROR_RATE_VERY_HIGH,
                        severity=AlertSeverity.CRITICAL,
                        message=f"{op}的错误率极高: {stats['error_rate']:.2%}",
                        threshold=self.thresholds.get("error_rate_very_high", 0.2),
                        actual_value=stats["error_rate"]
                    )
                    if alert:
                        alerts.append(alert)
                elif stats["error_rate"] > self.thresholds.get("error_rate_high", 0.1):
                    alert = await self._create_alert(
                        operation=op,
                        alert_type=AlertType.ERROR_RATE_HIGH,
                        severity=AlertSeverity.WARNING,
                        message=f"{op}的错误率较高: {stats['error_rate']:.2%}",
                        threshold=self.thresholds.get("error_rate_high", 0.1),
                        actual_value=stats["error_rate"]
                    )
                    if alert:
                        alerts.append(alert)
                
                # 检查并发数
                if stats["max_concurrent"] > self.thresholds.get("concurrent_high", 10):
                    alert = await self._create_alert(
                        operation=op,
                        alert_type=AlertType.CONCURRENT_HIGH,
                        severity=AlertSeverity.WARNING,
                        message=f"{op}的并发数较高: {stats['max_concurrent']}",
                        threshold=self.thresholds.get("concurrent_high", 10),
                        actual_value=stats["max_concurrent"]
                    )
                    if alert:
                        alerts.append(alert)
            
            return alerts
        except Exception as e:
            logger.error(f"检查告警失败: {e}")
            return []
    
    async def _create_alert(
        self,
        operation: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        threshold: float,
        actual_value: float
    ) -> Optional[MultimodalPerformanceAlert]:
        """
        创建告警
        
        Args:
            operation: 操作类型
            alert_type: 告警类型
            severity: 严重程度
            message: 告警消息
            threshold: 阈值
            actual_value: 实际值
            
        Returns:
            告警记录，如果已存在相同告警则返回None
        """
        try:
            # 检查是否已有未解决的相同告警（最近5分钟内）
            five_minutes_ago = datetime.now() - timedelta(minutes=5)
            existing_alert = await self.db.execute(
                select(MultimodalPerformanceAlert).where(
                    and_(
                        MultimodalPerformanceAlert.operation == operation,
                        MultimodalPerformanceAlert.alert_type == alert_type.value,
                        MultimodalPerformanceAlert.resolved == False,
                        MultimodalPerformanceAlert.timestamp >= five_minutes_ago
                    )
                )
            )
            
            if existing_alert.scalar_one_or_none():
                # 已存在相同告警，不重复创建
                return None
            
            # 创建新告警
            alert = MultimodalPerformanceAlert(
                operation=operation,
                alert_type=alert_type.value,
                severity=severity.value,
                message=message,
                threshold=threshold,
                actual_value=actual_value,
                timestamp=datetime.now(),
                resolved=False,
                extra_metadata={
                    "operation": operation,
                    "alert_type": alert_type.value,
                    "severity": severity.value
                }
            )
            
            self.db.add(alert)
            await self.db.flush()
            
            # 创建通知
            await self._create_notification(alert)
            
            logger.warning(f"性能告警: {message}")
            return alert
        except Exception as e:
            logger.error(f"创建告警失败: {e}")
            return None
    
    async def _create_notification(self, alert: MultimodalPerformanceAlert):
        """
        创建通知
        
        Args:
            alert: 告警记录
        """
        try:
            # 根据严重程度确定通知类型
            notification_type = "warning"
            if alert.severity == "critical":
                notification_type = "error"
            elif alert.severity == "info":
                notification_type = "info"
            
            notification = Notification(
                title=f"多模态分析性能告警: {alert.operation}",
                message=alert.message,
                type=notification_type,
                level=alert.severity,
                is_read=False,
                created_at=datetime.now(),
                extra_metadata={
                    "alert_id": alert.id,
                    "operation": alert.operation,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity
                }
            )
            self.db.add(notification)
            await self.db.flush()
        except Exception as e:
            logger.error(f"创建通知失败: {e}")
    
    async def resolve_alert(self, alert_id: int, resolved_by: str = "system") -> bool:
        """
        解决告警
        
        Args:
            alert_id: 告警ID
            resolved_by: 解决人
            
        Returns:
            是否成功
        """
        try:
            alert = await self.db.get(MultimodalPerformanceAlert, alert_id)
            if not alert:
                return False
            
            alert.resolved = True
            alert.resolved_at = datetime.now()
            alert.resolved_by = resolved_by
            
            await self.db.flush()
            logger.info(f"告警已解决: {alert_id} by {resolved_by}")
            return True
        except Exception as e:
            logger.error(f"解决告警失败: {e}")
            return False
    
    async def get_alerts(
        self,
        operation: Optional[str] = None,
        alert_type: Optional[str] = None,
        resolved: Optional[bool] = None,
        limit: int = 100
    ) -> List[MultimodalPerformanceAlert]:
        """
        获取告警列表
        
        Args:
            operation: 操作类型
            alert_type: 告警类型
            resolved: 是否已解决
            limit: 限制数量
            
        Returns:
            告警列表
        """
        try:
            query = select(MultimodalPerformanceAlert)
            
            conditions = []
            if operation:
                conditions.append(MultimodalPerformanceAlert.operation == operation)
            if alert_type:
                conditions.append(MultimodalPerformanceAlert.alert_type == alert_type)
            if resolved is not None:
                conditions.append(MultimodalPerformanceAlert.resolved == resolved)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.order_by(desc(MultimodalPerformanceAlert.timestamp)).limit(limit)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"获取告警列表失败: {e}")
            return []

