"""
系统健康通知服务
OPS-1F + OPS-2A 实现
"""

from datetime import datetime
from typing import Any, Literal, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.schemas.system_health import SystemHealthSummary, SystemHealthCheckRead
from app.models.enums.alert_severity import AlertSeverity


def format_health_alert_message(
    check_key: str,
    status: str,
    error: Optional[str] = None,
    meta: Optional[dict[str, Any]] = None,
) -> tuple[str, str]:
    """
    格式化健康告警消息
    
    Returns:
        (title, body) 元组
    """
    severity_emoji = "❌" if status == "error" else "⚠️"
    severity_text = "错误" if status == "error" else "警告"
    
    title = f"系统健康告警：{check_key} ({severity_text})"
    
    lines = [
        f"检查项：{check_key}",
        f"严重级别：{status.upper()}",
    ]
    
    if error:
        lines.append(f"错误信息：{error}")
    
    if meta:
        # 添加元数据
        if "free_gb" in meta:
            lines.append(f"可用空间：{meta['free_gb']} GB ({meta.get('used_percent', 0):.1f}% 已用)")
        if "enabled_count" in meta:
            lines.append(f"启用数量：{meta['enabled_count']}")
    
    lines.append(f"时间：{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    body = "\n".join(lines)
    return title, body


async def notify_system_health_issue(
    session: AsyncSession,
    *,
    level: Literal["warning", "error"],
    message: str,
    check_key: Optional[str] = None,
    meta: Optional[dict[str, Any]] = None,
) -> None:
    """
    发送系统健康告警通知
    
    Args:
        session: 数据库会话
        level: 告警级别 (warning/error)
        message: 告警消息
        check_key: 检查项 key（用于渠道路由）
        meta: 额外元数据
    """
    # 1. 发送站内通知
    try:
        from app.services.notification_service import create_notification
        
        notification_type = f"SYSTEM_HEALTH_{level.upper()}"
        
        await create_notification(
            session,
            notification_type=notification_type,
            title=f"系统健康{'告警' if level == 'warning' else '错误'}",
            message=message,
            data=meta,
            user_id=None,
        )
        
        logger.info(f"[health-notify] sent web notification: {message[:100]}")
        
    except Exception as e:
        logger.warning(f"[health-notify] failed to send web notification: {e}")
    
    # 2. 广播到告警渠道（OPS-2A）
    if check_key:
        try:
            from app.services.alert_channel_service import broadcast_alert
            
            severity = AlertSeverity.ERROR if level == "error" else AlertSeverity.WARNING
            title = f"系统健康告警：{check_key}"
            
            await broadcast_alert(
                session,
                check_key=check_key,
                severity=severity,
                title=title,
                body=message,
            )
        except Exception as e:
            logger.warning(f"[health-notify] failed to broadcast to channels: {e}")


async def check_and_notify_health_status(
    session: AsyncSession,
    summary: SystemHealthSummary,
) -> None:
    """
    检查健康状态并发送通知（带降频）
    
    只在状态从正常变为异常时发送通知
    """
    from app.models.system_health import SystemHealthCheck
    from sqlalchemy import select, update
    
    # 获取上次通知状态
    result = await session.execute(
        select(SystemHealthCheck.last_notified_status).limit(1)
    )
    row = result.first()
    last_notified = row[0] if row else None
    
    current_status = summary.overall_status
    
    # 降频逻辑：只在状态恶化时通知
    should_notify = False
    notify_level: Literal["warning", "error"] = "warning"
    
    if current_status == "error":
        if last_notified != "error":
            should_notify = True
            notify_level = "error"
    elif current_status == "warning":
        if last_notified not in ("warning", "error"):
            should_notify = True
            notify_level = "warning"
    
    if should_notify:
        # 构建消息
        error_keys = [c.key for c in summary.checks if c.status == "error"]
        warning_keys = [c.key for c in summary.checks if c.status == "warning"]
        
        if notify_level == "error":
            message = f"系统健康检查发现 {summary.error_count} 项错误"
            if error_keys:
                message += f": {', '.join(error_keys[:5])}"
                if len(error_keys) > 5:
                    message += f" 等 {len(error_keys)} 项"
        else:
            message = f"系统健康检查发现 {summary.warning_count} 项警告"
            if warning_keys:
                message += f": {', '.join(warning_keys[:5])}"
                if len(warning_keys) > 5:
                    message += f" 等 {len(warning_keys)} 项"
        
        # 发送整体告警
        await notify_system_health_issue(
            session,
            level=notify_level,
            message=message,
            check_key="system.overall",
            meta={
                "error_count": summary.error_count,
                "warning_count": summary.warning_count,
                "error_keys": error_keys[:10],
                "warning_keys": warning_keys[:10],
            },
        )
        
        # 对每个异常检查项单独发送告警（用于渠道路由）
        for check in summary.checks:
            if check.status in ("error", "warning"):
                check_level: Literal["warning", "error"] = "error" if check.status == "error" else "warning"
                title, body = format_health_alert_message(
                    check.key,
                    check.status,
                    check.last_error,
                    check.meta,
                )
                try:
                    from app.services.alert_channel_service import broadcast_alert
                    severity = AlertSeverity.ERROR if check.status == "error" else AlertSeverity.WARNING
                    await broadcast_alert(session, check.key, severity, title, body)
                except Exception as e:
                    logger.warning(f"[health-notify] failed to broadcast {check.key}: {e}")
        
        # 更新上次通知状态
        await session.execute(
            update(SystemHealthCheck).values(last_notified_status=current_status)
        )
        await session.commit()
