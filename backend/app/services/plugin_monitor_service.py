"""
插件监控服务
PLUGIN-SAFETY-1 实现

提供插件错误监控、健康状态管理和自动隔离机制
"""

from datetime import datetime, timedelta
from typing import Optional, Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.plugin import Plugin
from app.models.plugin_audit import PluginAuditLog


class PluginMonitorService:
    """
    插件监控服务
    
    负责跟踪插件的错误情况，管理健康状态，并在必要时自动隔离插件。
    """
    
    # 错误阈值配置
    ERROR_THRESHOLD_WINDOW = timedelta(minutes=10)  # 时间窗口
    ERROR_THRESHOLD_COUNT = 5  # 10分钟内超过5次错误则自动隔离
    
    @staticmethod
    async def report_error(
        session: AsyncSession,
        plugin_id: str,
        context: dict[str, Any]
    ) -> None:
        """
        报告插件错误
        
        Args:
            session: 数据库会话
            plugin_id: 插件 ID
            context: 错误上下文，包含：
                - event: 事件类型（如 EventType.MANGA_UPDATED）
                - error: 错误信息
                - source: 错误来源（如 handler 名称）
        """
        try:
            # 更新插件的错误计数和最后错误时间
            now = datetime.utcnow()
            
            # 查询当前插件
            stmt = select(Plugin).where(Plugin.name == plugin_id)
            result = await session.execute(stmt)
            plugin = result.scalar_one_or_none()
            
            if not plugin:
                logger.warning(f"[plugin-monitor] Plugin not found: {plugin_id}")
                return
            
            # 更新错误信息
            update_stmt = (
                update(Plugin)
                .where(Plugin.name == plugin_id)
                .values(
                    error_count=Plugin.error_count + 1,
                    last_error_at=now,
                    last_error=context.get("error", "Unknown error")[:500]  # 限制长度
                )
            )
            await session.execute(update_stmt)
            
            # 检查是否需要自动隔离
            await PluginMonitorService._check_auto_quarantine(session, plugin_id, now)
            
            await session.commit()
            
            logger.info(
                f"[plugin-monitor] Error reported for {plugin_id}: "
                f"count={plugin.error_count + 1}, error={context.get('error', 'Unknown')[:100]}"
            )
            
        except Exception as e:
            logger.error(f"[plugin-monitor] Failed to report error for {plugin_id}: {e}", exc_info=True)
            await session.rollback()
    
    @staticmethod
    async def _check_auto_quarantine(
        session: AsyncSession,
        plugin_id: str,
        now: datetime
    ) -> None:
        """
        检查是否需要自动隔离插件
        
        Args:
            session: 数据库会话
            plugin_id: 插件 ID
            now: 当前时间
        """
        try:
            # 查询时间窗口内的错误次数
            window_start = now - PluginMonitorService.ERROR_THRESHOLD_WINDOW
            
            stmt = select(Plugin).where(
                Plugin.name == plugin_id,
                Plugin.last_error_at >= window_start
            )
            result = await session.execute(stmt)
            plugin = result.scalar_one_or_none()
            
            if not plugin:
                return
            
            # 如果错误次数超过阈值，自动隔离
            if plugin.error_count >= PluginMonitorService.ERROR_THRESHOLD_COUNT:
                await PluginMonitorService._quarantine_plugin(
                    session, plugin_id, 
                    f"Auto-quarantined: {plugin.error_count} errors in {PluginMonitorService.ERROR_THRESHOLD_WINDOW}"
                )
                
                logger.warning(
                    f"[plugin-monitor] Auto-quarantined plugin {plugin_id}: "
                    f"{plugin.error_count} errors in {PluginMonitorService.ERROR_THRESHOLD_WINDOW}"
                )
                
        except Exception as e:
            logger.error(f"[plugin-monitor] Failed to check auto-quarantine for {plugin_id}: {e}", exc_info=True)
    
    @staticmethod
    async def _quarantine_plugin(
        session: AsyncSession,
        plugin_id: str,
        reason: str
    ) -> None:
        """
        隔离插件
        
        Args:
            session: 数据库会话
            plugin_id: 插件 ID
            reason: 隔离原因
        """
        from app.services.plugin_registry import PluginRegistry
        
        stmt = (
            update(Plugin)
            .where(Plugin.name == plugin_id)
            .values(is_quarantined=True, last_error=reason)
        )
        await session.execute(stmt)
        
        # PLUGIN-SAFETY-1: 同步内存隔离状态
        registry = PluginRegistry()
        registry.quarantine_plugin(plugin_id)
    
    @staticmethod
    async def reset_errors(
        session: AsyncSession,
        plugin_id: str
    ) -> bool:
        """
        重置插件错误计数和隔离状态
        
        Args:
            session: 数据库会话
            plugin_id: 插件 ID
            
        Returns:
            是否成功重置
        """
        try:
            stmt = (
                update(Plugin)
                .where(Plugin.name == plugin_id)
                .values(
                    error_count=0,
                    last_error_at=None,
                    last_error=None,
                    is_quarantined=False
                )
            )
            result = await session.execute(stmt)
            await session.commit()
            
            if result.rowcount > 0:
                logger.info(f"[plugin-monitor] Reset errors for plugin: {plugin_id}")
                return True
            else:
                logger.warning(f"[plugin-monitor] Plugin not found for reset: {plugin_id}")
                return False
                
        except Exception as e:
            logger.error(f"[plugin-monitor] Failed to reset errors for {plugin_id}: {e}", exc_info=True)
            await session.rollback()
            return False
    
    @staticmethod
    async def record_audit(
        session: AsyncSession,
        plugin_id: str,
        action: str,
        payload: Optional[dict[str, Any]] = None
    ) -> None:
        """
        记录插件审计日志（异步，不阻塞主流程）
        
        Args:
            session: 数据库会话
            plugin_id: 插件 ID
            action: 操作类型
            payload: 操作参数（可选）
        """
        try:
            audit_log = PluginAuditLog(
                plugin_id=plugin_id,
                action=action,
                payload=payload
            )
            session.add(audit_log)
            await session.commit()
            
        except Exception as e:
            # 审计日志失败不应该影响主流程
            logger.warning(f"[plugin-monitor] Failed to record audit for {plugin_id}:{action}: {e}")
            await session.rollback()
    
    @staticmethod
    async def cleanup_old_audit_logs(
        session: AsyncSession,
        days_to_keep: int = 30
    ) -> int:
        """
        清理旧的审计日志
        
        Args:
            session: 数据库会话
            days_to_keep: 保留天数
            
        Returns:
            删除的记录数
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            from sqlalchemy import delete
            stmt = delete(PluginAuditLog).where(PluginAuditLog.created_at < cutoff_date)
            result = await session.execute(stmt)
            await session.commit()
            
            deleted_count = result.rowcount
            if deleted_count > 0:
                logger.info(f"[plugin-monitor] Cleaned up {deleted_count} old audit logs")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"[plugin-monitor] Failed to cleanup audit logs: {e}", exc_info=True)
            await session.rollback()
            return 0
