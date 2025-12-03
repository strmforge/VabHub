"""
存储监控服务
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import psutil
import os
from pathlib import Path

from app.models.storage_monitor import StorageDirectory, StorageUsageHistory, StorageAlert
from app.core.cache import get_cache
from loguru import logger


class StorageMonitorService:
    """存储监控服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache = get_cache()
    
    async def create_directory(
        self,
        name: str,
        path: str,
        enabled: bool = True,
        alert_threshold: float = 80.0,
        description: Optional[str] = None
    ) -> StorageDirectory:
        """创建存储目录配置"""
        # 验证路径是否存在
        if not os.path.exists(path):
            raise ValueError(f"路径不存在: {path}")
        
        # 检查路径是否已存在
        existing = await self.db.execute(
            select(StorageDirectory).where(StorageDirectory.path == path)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"路径已存在: {path}")
        
        directory = StorageDirectory(
            name=name,
            path=path,
            enabled=enabled,
            alert_threshold=alert_threshold,
            description=description
        )
        self.db.add(directory)
        await self.db.flush()
        await self.db.refresh(directory)
        
        return directory
    
    async def list_directories(
        self,
        enabled: Optional[bool] = None
    ) -> List[StorageDirectory]:
        """获取存储目录列表"""
        query = select(StorageDirectory).order_by(StorageDirectory.created_at.desc())
        if enabled is not None:
            query = query.where(StorageDirectory.enabled == enabled)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_directory(self, directory_id: int) -> Optional[StorageDirectory]:
        """获取存储目录详情"""
        result = await self.db.execute(
            select(StorageDirectory).where(StorageDirectory.id == directory_id)
        )
        return result.scalar_one_or_none()
    
    async def update_directory(
        self,
        directory_id: int,
        name: Optional[str] = None,
        enabled: Optional[bool] = None,
        alert_threshold: Optional[float] = None,
        description: Optional[str] = None
    ) -> Optional[StorageDirectory]:
        """更新存储目录配置"""
        directory = await self.get_directory(directory_id)
        if not directory:
            return None
        
        if name is not None:
            directory.name = name
        if enabled is not None:
            directory.enabled = enabled
        if alert_threshold is not None:
            directory.alert_threshold = alert_threshold
        if description is not None:
            directory.description = description
        
        directory.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(directory)
        
        return directory
    
    async def delete_directory(self, directory_id: int) -> bool:
        """删除存储目录配置"""
        directory = await self.get_directory(directory_id)
        if not directory:
            return False
        
        await self.db.delete(directory)
        await self.db.flush()
        
        return True
    
    async def get_directory_usage(self, path: str) -> Optional[Dict]:
        """获取目录使用情况"""
        try:
            if not os.path.exists(path):
                return None
            
            usage = psutil.disk_usage(path)
            return {
                "path": path,
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "usage_percent": round((usage.used / usage.total) * 100, 2) if usage.total > 0 else 0.0
            }
        except Exception as e:
            logger.error(f"获取目录使用情况失败: {path} - {e}")
            return None
    
    async def record_usage_history(self, directory_id: int, path: str) -> Optional[StorageUsageHistory]:
        """记录存储使用历史"""
        usage = await self.get_directory_usage(path)
        if not usage:
            return None
        
        history = StorageUsageHistory(
            directory_id=directory_id,
            path=path,
            total_bytes=usage["total_bytes"],
            used_bytes=usage["used_bytes"],
            free_bytes=usage["free_bytes"],
            usage_percent=usage["usage_percent"]
        )
        self.db.add(history)
        await self.db.flush()
        await self.db.refresh(history)
        
        return history
    
    async def check_and_create_alerts(self, directory_id: int, path: str) -> List[StorageAlert]:
        """检查并创建预警"""
        directory = await self.get_directory(directory_id)
        if not directory or not directory.enabled:
            return []
        
        usage = await self.get_directory_usage(path)
        if not usage:
            return []
        
        alerts = []
        usage_percent = usage["usage_percent"]
        threshold = directory.alert_threshold
        
        # 检查是否超过阈值
        if usage_percent >= threshold:
            # 检查是否已有未解决的预警
            existing = await self.db.execute(
                select(StorageAlert).where(
                    and_(
                        StorageAlert.directory_id == directory_id,
                        StorageAlert.resolved == False,
                        StorageAlert.alert_type == "threshold_exceeded"
                    )
                )
            )
            if not existing.scalar_one_or_none():
                # 确定预警类型
                if usage_percent >= 95:
                    alert_type = "critical"
                    message = f"存储空间严重不足！使用率: {usage_percent:.2f}%"
                elif usage_percent >= 90:
                    alert_type = "low_space"
                    message = f"存储空间不足！使用率: {usage_percent:.2f}%"
                else:
                    alert_type = "threshold_exceeded"
                    message = f"存储使用率超过预警阈值！使用率: {usage_percent:.2f}%，阈值: {threshold:.2f}%"
                
                alert = StorageAlert(
                    directory_id=directory_id,
                    path=path,
                    alert_type=alert_type,
                    usage_percent=usage_percent,
                    threshold=threshold,
                    message=message
                )
                self.db.add(alert)
                alerts.append(alert)
        
        await self.db.flush()
        return alerts
    
    async def get_usage_history(
        self,
        directory_id: Optional[int] = None,
        path: Optional[str] = None,
        hours: int = 24
    ) -> List[StorageUsageHistory]:
        """获取存储使用历史"""
        query = select(StorageUsageHistory).where(
            StorageUsageHistory.recorded_at >= datetime.utcnow() - timedelta(hours=hours)
        ).order_by(StorageUsageHistory.recorded_at.desc())
        
        if directory_id:
            query = query.where(StorageUsageHistory.directory_id == directory_id)
        if path:
            query = query.where(StorageUsageHistory.path == path)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_usage_trends(
        self,
        directory_id: Optional[int] = None,
        path: Optional[str] = None,
        days: int = 7
    ) -> Dict:
        """获取存储使用趋势（用于图表）"""
        # 获取历史数据
        hours = days * 24
        history = await self.get_usage_history(directory_id, path, hours)
        
        # 按时间分组（每小时一个数据点）
        trends = {}
        for record in history:
            # 按小时分组
            hour_key = record.recorded_at.replace(minute=0, second=0, microsecond=0)
            if hour_key not in trends:
                trends[hour_key] = {
                    "timestamp": hour_key.isoformat(),
                    "total_bytes": record.total_bytes,
                    "used_bytes": record.used_bytes,
                    "free_bytes": record.free_bytes,
                    "usage_percent": record.usage_percent,
                    "count": 1
                }
            else:
                # 取平均值
                trends[hour_key]["used_bytes"] = (
                    trends[hour_key]["used_bytes"] * trends[hour_key]["count"] + record.used_bytes
                ) / (trends[hour_key]["count"] + 1)
                trends[hour_key]["free_bytes"] = (
                    trends[hour_key]["free_bytes"] * trends[hour_key]["count"] + record.free_bytes
                ) / (trends[hour_key]["count"] + 1)
                trends[hour_key]["usage_percent"] = (
                    trends[hour_key]["usage_percent"] * trends[hour_key]["count"] + record.usage_percent
                ) / (trends[hour_key]["count"] + 1)
                trends[hour_key]["count"] += 1
        
        # 转换为列表并排序
        trend_list = sorted(trends.values(), key=lambda x: x["timestamp"])
        
        return {
            "trends": trend_list,
            "days": days,
            "total_points": len(trend_list)
        }
    
    async def get_all_directories_usage(self) -> List[Dict]:
        """获取所有目录的使用情况"""
        directories = await self.list_directories(enabled=True)
        results = []
        
        for directory in directories:
            usage = await self.get_directory_usage(directory.path)
            if usage:
                results.append({
                    "directory_id": directory.id,
                    "name": directory.name,
                    "path": directory.path,
                    "enabled": directory.enabled,
                    "alert_threshold": directory.alert_threshold,
                    **usage
                })
        
        return results
    
    async def get_alerts(
        self,
        directory_id: Optional[int] = None,
        resolved: Optional[bool] = None,
        alert_type: Optional[str] = None
    ) -> List[StorageAlert]:
        """获取预警列表"""
        query = select(StorageAlert).order_by(StorageAlert.created_at.desc())
        
        if directory_id:
            query = query.where(StorageAlert.directory_id == directory_id)
        if resolved is not None:
            query = query.where(StorageAlert.resolved == resolved)
        if alert_type:
            query = query.where(StorageAlert.alert_type == alert_type)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def resolve_alert(self, alert_id: int) -> Optional[StorageAlert]:
        """解决预警"""
        result = await self.db.execute(
            select(StorageAlert).where(StorageAlert.id == alert_id)
        )
        alert = result.scalar_one_or_none()
        if not alert:
            return None
        
        alert.resolved = True
        alert.resolved_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(alert)
        
        return alert
    
    async def get_statistics(self) -> Dict:
        """获取存储监控统计信息"""
        # 获取目录总数
        total_dirs = await self.db.execute(
            select(func.count(StorageDirectory.id))
        )
        total_directories = total_dirs.scalar() or 0
        
        # 获取启用的目录数
        enabled_dirs = await self.db.execute(
            select(func.count(StorageDirectory.id)).where(StorageDirectory.enabled == True)
        )
        enabled_directories = enabled_dirs.scalar() or 0
        
        # 获取未解决的预警数
        unresolved_alerts = await self.db.execute(
            select(func.count(StorageAlert.id)).where(StorageAlert.resolved == False)
        )
        unresolved_count = unresolved_alerts.scalar() or 0
        
        # 获取所有启用的目录使用情况
        directories_usage = await self.get_all_directories_usage()
        total_space = sum(d["total_bytes"] for d in directories_usage)
        total_used = sum(d["used_bytes"] for d in directories_usage)
        total_free = sum(d["free_bytes"] for d in directories_usage)
        
        return {
            "total_directories": total_directories,
            "enabled_directories": enabled_directories,
            "unresolved_alerts": unresolved_count,
            "total_space_bytes": total_space,
            "total_used_bytes": total_used,
            "total_free_bytes": total_free,
            "total_usage_percent": round((total_used / total_space) * 100, 2) if total_space > 0 else 0.0,
            "directories": directories_usage
        }

