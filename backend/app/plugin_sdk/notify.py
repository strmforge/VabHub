"""
插件通知客户端

PLUGIN-SDK-1 实现
"""

from typing import Any, Optional
from loguru import logger

from app.plugin_sdk.context import PluginContext


class NotifyClient:
    """
    插件通知客户端
    
    封装主系统的通知服务，允许插件发送通知。
    
    Example:
        await sdk.notify.send(
            user_id=1,
            title="任务完成",
            message="您的任务已处理完成",
            payload={"task_id": 123}
        )
    """
    
    def __init__(self, ctx: PluginContext):
        """
        初始化通知客户端
        
        Args:
            ctx: 插件上下文
        """
        self._ctx = ctx
    
    async def send(
        self,
        user_id: int,
        *,
        title: str,
        message: str,
        notification_type: Optional[str] = None,
        media_type: Optional[str] = None,
        target_id: Optional[int] = None,
        payload: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        发送通知给指定用户
        
        Args:
            user_id: 用户 ID
            title: 通知标题
            message: 通知内容
            notification_type: 通知类型（可选，默认为 SYSTEM_MESSAGE）
            media_type: 媒体类型（可选）
            target_id: 目标 ID（可选）
            payload: 额外数据（可选）
            
        Returns:
            是否发送成功
        """
        try:
            from app.core.database import get_session
            from app.models.enums.notification_type import NotificationType
            from app.schemas.user_notification import UserNotificationCreate
            from app.services.notification_service import NotificationService
            
            # 确定通知类型
            try:
                ntype = NotificationType(notification_type) if notification_type else NotificationType.SYSTEM_MESSAGE
            except ValueError:
                ntype = NotificationType.SYSTEM_MESSAGE
            
            # 构建 payload，添加来源信息
            final_payload = payload or {}
            final_payload["_source_plugin"] = self._ctx.plugin_id
            
            async for session in get_session():
                notification_data = UserNotificationCreate(
                    user_id=user_id,
                    type=ntype,
                    media_type=media_type,
                    target_id=target_id,
                    title=title,
                    message=message,
                    payload=final_payload,
                )
                await NotificationService.create_notification(session, notification_data)
                logger.debug(f"[plugin:{self._ctx.plugin_id}] Notification sent to user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"[plugin:{self._ctx.plugin_id}] Failed to send notification: {e}")
            return False
    
    async def send_to_users(
        self,
        user_ids: list[int],
        *,
        title: str,
        message: str,
        notification_type: Optional[str] = None,
        media_type: Optional[str] = None,
        target_id: Optional[int] = None,
        payload: Optional[dict[str, Any]] = None,
    ) -> int:
        """
        发送通知给多个用户
        
        Args:
            user_ids: 用户 ID 列表
            title: 通知标题
            message: 通知内容
            notification_type: 通知类型
            media_type: 媒体类型
            target_id: 目标 ID
            payload: 额外数据
            
        Returns:
            成功发送的数量
        """
        success_count = 0
        for user_id in user_ids:
            if await self.send(
                user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                media_type=media_type,
                target_id=target_id,
                payload=payload,
            ):
                success_count += 1
        return success_count
    
    async def broadcast(
        self,
        *,
        title: str,
        message: str,
        notification_type: Optional[str] = None,
        payload: Optional[dict[str, Any]] = None,
    ) -> int:
        """
        广播通知给所有用户（管理员功能）
        
        注意：此功能需要谨慎使用，避免滥发通知。
        
        Args:
            title: 通知标题
            message: 通知内容
            notification_type: 通知类型
            payload: 额外数据
            
        Returns:
            成功发送的数量
        """
        try:
            from app.core.database import get_session
            from sqlalchemy import select
            from app.models.user import User
            
            async for session in get_session():
                # 获取所有活跃用户
                stmt = select(User.id).where(User.is_active == True)
                result = await session.execute(stmt)
                user_ids = [row[0] for row in result.fetchall()]
                
                return await self.send_to_users(
                    user_ids,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    payload=payload,
                )
                
        except Exception as e:
            logger.error(f"[plugin:{self._ctx.plugin_id}] Broadcast failed: {e}")
            return 0
