"""
插件统计服务
PLUGIN-REMOTE-1 实现

记录和统计插件使用行为
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from loguru import logger

from app.models.plugin import Plugin, PluginType


class PluginStatisticsService:
    """
    插件统计服务
    
    负责记录和统计插件的使用行为
    """
    
    @staticmethod
    async def increment_call_count(
        session: AsyncSession,
        plugin_id: str
    ) -> bool:
        """
        增加插件的调用次数
        
        Args:
            session: 数据库会话
            plugin_id: 插件 ID
            
        Returns:
            是否成功更新
        """
        try:
            stmt = (
                update(Plugin)
                .where(Plugin.name == plugin_id)
                .values(
                    call_count=Plugin.call_count + 1,
                    last_called_at=datetime.utcnow()
                )
            )
            result = await session.execute(stmt)
            await session.commit()
            
            success = result.rowcount > 0
            if success:
                logger.debug(f"[plugin-stats] Incremented call count for {plugin_id}")
            else:
                logger.warning(f"[plugin-stats] Plugin not found for call count update: {plugin_id}")
            
            return success
            
        except Exception as e:
            await session.rollback()
            logger.error(f"[plugin-stats] Error incrementing call count for {plugin_id}: {e}")
            return False
    
    @staticmethod
    async def increment_event_handled_count(
        session: AsyncSession,
        plugin_id: str
    ) -> bool:
        """
        增加远程插件的事件处理次数
        
        Args:
            session: 数据库会话
            plugin_id: 插件 ID
            
        Returns:
            是否成功更新
        """
        try:
            stmt = (
                update(Plugin)
                .where(Plugin.name == plugin_id)
                .values(
                    event_handled_count=Plugin.event_handled_count + 1,
                    last_called_at=datetime.utcnow()
                )
            )
            result = await session.execute(stmt)
            await session.commit()
            
            success = result.rowcount > 0
            if success:
                logger.debug(f"[plugin-stats] Incremented event handled count for {plugin_id}")
            else:
                logger.warning(f"[plugin-stats] Plugin not found for event count update: {plugin_id}")
            
            return success
            
        except Exception as e:
            await session.rollback()
            logger.error(f"[plugin-stats] Error incrementing event count for {plugin_id}: {e}")
            return False
    
    @staticmethod
    async def get_plugin_statistics(
        session: AsyncSession,
        plugin_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取单个插件的统计信息
        
        Args:
            session: 数据库会话
            plugin_id: 插件 ID
            
        Returns:
            统计信息或 None
        """
        try:
            stmt = select(Plugin).where(Plugin.name == plugin_id)
            result = await session.execute(stmt)
            plugin = result.scalar_one_or_none()
            
            if not plugin:
                return None
            
            return {
                "plugin_id": plugin.name,
                "plugin_type": plugin.plugin_type.value if hasattr(plugin, 'plugin_type') else "local",
                "call_count": getattr(plugin, 'call_count', 0),
                "event_handled_count": getattr(plugin, 'event_handled_count', 0),
                "last_called_at": plugin.last_called_at.isoformat() if plugin.last_called_at else None,
                "total_activity": getattr(plugin, 'call_count', 0) + getattr(plugin, 'event_handled_count', 0)
            }
            
        except Exception as e:
            logger.error(f"[plugin-stats] Error getting statistics for {plugin_id}: {e}")
            return None
    
    @staticmethod
    async def get_recent_activity(
        session: AsyncSession,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        获取最近的活动统计
        
        Args:
            session: 数据库会话
            hours: 统计时间范围（小时）
            
        Returns:
            活动统计信息
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # 查询最近有活动的插件
            stmt = select(Plugin).where(
                Plugin.last_called_at >= cutoff_time
            ).order_by(Plugin.last_called_at.desc())
            
            result = await session.execute(stmt)
            active_plugins = result.scalars().all()
            
            # 统计信息
            stats = {
                "time_range_hours": hours,
                "active_plugins_count": len(active_plugins),
                "total_calls": sum(getattr(p, 'call_count', 0) for p in active_plugins),
                "total_events": sum(getattr(p, 'event_handled_count', 0) for p in active_plugins),
                "recent_activity": []
            }
            
            # 详细活动列表
            for plugin in active_plugins:
                stats["recent_activity"].append({
                    "plugin_id": plugin.name,
                    "plugin_type": plugin.plugin_type.value if hasattr(plugin, 'plugin_type') else "local",
                    "last_called_at": plugin.last_called_at.isoformat(),
                    "call_count": getattr(plugin, 'call_count', 0),
                    "event_handled_count": getattr(plugin, 'event_handled_count', 0)
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"[plugin-stats] Error getting recent activity: {e}")
            return {
                "time_range_hours": hours,
                "active_plugins_count": 0,
                "total_calls": 0,
                "total_events": 0,
                "recent_activity": []
            }
    
    @staticmethod
    async def get_top_plugins(
        session: AsyncSession,
        metric: str = "total_activity",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取使用量最高的插件列表
        
        Args:
            session: 数据库会话
            metric: 排序指标 ("call_count", "event_handled_count", "total_activity")
            limit: 返回数量限制
            
        Returns:
            插件统计列表
        """
        try:
            # 构建排序表达式
            if metric == "call_count":
                order_by = Plugin.call_count.desc()
            elif metric == "event_handled_count":
                order_by = Plugin.event_handled_count.desc()
            else:  # total_activity
                order_by = (Plugin.call_count + Plugin.event_handled_count).desc()
            
            stmt = select(Plugin).where(
                Plugin.status == "ENABLED"
            ).order_by(order_by).limit(limit)
            
            result = await session.execute(stmt)
            plugins = result.scalars().all()
            
            return [
                {
                    "plugin_id": plugin.name,
                    "plugin_type": plugin.plugin_type.value if hasattr(plugin, 'plugin_type') else "local",
                    "call_count": getattr(plugin, 'call_count', 0),
                    "event_handled_count": getattr(plugin, 'event_handled_count', 0),
                    "total_activity": getattr(plugin, 'call_count', 0) + getattr(plugin, 'event_handled_count', 0),
                    "last_called_at": plugin.last_called_at.isoformat() if plugin.last_called_at else None
                }
                for plugin in plugins
            ]
            
        except Exception as e:
            logger.error(f"[plugin-stats] Error getting top plugins: {e}")
            return []
    
    @staticmethod
    async def reset_statistics(
        session: AsyncSession,
        plugin_id: str = None
    ) -> bool:
        """
        重置插件统计信息
        
        Args:
            session: 数据库会话
            plugin_id: 插件 ID，None 表示重置所有插件
            
        Returns:
            是否成功重置
        """
        try:
            if plugin_id:
                stmt = (
                    update(Plugin)
                    .where(Plugin.name == plugin_id)
                    .values(
                        call_count=0,
                        event_handled_count=0,
                        last_called_at=None
                    )
                )
            else:
                stmt = (
                    update(Plugin)
                    .values(
                        call_count=0,
                        event_handled_count=0,
                        last_called_at=None
                    )
                )
            
            result = await session.execute(stmt)
            await session.commit()
            
            logger.info(f"[plugin-stats] Reset statistics for {result.rowcount} plugins")
            return True
            
        except Exception as e:
            await session.rollback()
            logger.error(f"[plugin-stats] Error resetting statistics: {e}")
            return False


# 便捷函数
async def record_plugin_call(session: AsyncSession, plugin_id: str) -> bool:
    """记录插件调用"""
    return await PluginStatisticsService.increment_call_count(session, plugin_id)


async def record_plugin_event_handled(session: AsyncSession, plugin_id: str) -> bool:
    """记录插件事件处理"""
    return await PluginStatisticsService.increment_event_handled_count(session, plugin_id)


async def get_plugin_activity_summary(session: AsyncSession) -> Dict[str, Any]:
    """获取插件活动摘要"""
    recent_24h = await PluginStatisticsService.get_recent_activity(session, 24)
    recent_7d = await PluginStatisticsService.get_recent_activity(session, 24 * 7)
    
    return {
        "last_24_hours": recent_24h,
        "last_7_days": recent_7d,
        "top_plugins_today": await PluginStatisticsService.get_top_plugins(session, "total_activity", 5),
        "top_remote_plugins_today": await PluginStatisticsService.get_top_plugins(session, "event_handled_count", 5)
    }
