"""
通知服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional, Dict
from datetime import datetime
from loguru import logger
import json

from app.models.notification import Notification
from app.modules.notification.channel_manager import NotificationChannelManager


class NotificationService:
    """通知服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.channel_manager = NotificationChannelManager()
    
    async def send_notification(
        self,
        title: str,
        message: str,
        notification_type: str = "info",
        channels: List[str] = None,
        metadata: Optional[Dict] = None
    ) -> Notification:
        """发送通知"""
        channels = channels or ["system"]
        
        # 创建通知记录
        notification = Notification(
            title=title,
            message=message,
            type=notification_type,
            channels=json.dumps(channels),  # 存储为JSON字符串
            status="pending",
            created_at=datetime.utcnow()
        )
        
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        
        try:
            # 发送通知到各个渠道
            send_results = await self.channel_manager.send(
                title=title,
                message=message,
                channels=channels,
                metadata=metadata
            )
            
            # 更新通知状态
            notification.status = "sent"
            notification.sent_at = datetime.utcnow()
            
            # 添加发送结果到元数据
            if metadata is None:
                metadata = {}
            metadata["send_results"] = send_results
            notification.metadata = json.dumps(metadata)
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
            notification.status = "failed"
            
            # 添加错误信息到元数据
            if metadata is None:
                metadata = {}
            metadata["error"] = str(e)
            notification.metadata = json.dumps(metadata)
            
            await self.db.commit()
        
        await self.db.refresh(notification)
        
        return notification
    
    async def list_notifications(
        self,
        limit: int = 50,
        notification_type: Optional[str] = None,
        status: Optional[str] = None,
        unread_only: bool = False
    ) -> List[Notification]:
        """获取通知列表"""
        query = select(Notification)
        
        if notification_type:
            query = query.where(Notification.type == notification_type)
        
        if status:
            query = query.where(Notification.status == status)
        
        if unread_only:
            query = query.where(Notification.is_read == False)
        
        query = query.order_by(Notification.created_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_notification(self, notification_id: int) -> Optional[Notification]:
        """获取通知详情"""
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()
    
    async def mark_as_read(self, notification_id: int) -> bool:
        """标记通知为已读"""
        notification = await self.get_notification(notification_id)
        if not notification:
            return False
        
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        
        return True
    
    async def mark_all_as_read(self, notification_type: Optional[str] = None) -> int:
        """标记所有通知为已读"""
        query = select(Notification).where(Notification.is_read == False)
        
        if notification_type:
            query = query.where(Notification.type == notification_type)
        
        result = await self.db.execute(query)
        notifications = result.scalars().all()
        
        count = 0
        now = datetime.utcnow()
        for notification in notifications:
            notification.is_read = True
            notification.read_at = now
            self.db.add(notification)
            count += 1
        
        await self.db.commit()
        return count
    
    async def get_unread_count(self, notification_type: Optional[str] = None) -> int:
        """获取未读通知数量"""
        from sqlalchemy import func
        
        query = select(func.count(Notification.id)).where(Notification.is_read == False)
        
        if notification_type:
            query = query.where(Notification.type == notification_type)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def delete_notification(self, notification_id: int) -> bool:
        """删除通知"""
        notification = await self.get_notification(notification_id)
        if not notification:
            return False
        
        await self.db.delete(notification)
        await self.db.commit()
        return True
    
    async def delete_all_notifications(self, notification_type: Optional[str] = None) -> int:
        """删除所有通知"""
        query = select(Notification)
        if notification_type:
            query = query.where(Notification.type == notification_type)
        
        result = await self.db.execute(query)
        notifications = result.scalars().all()
        
        count = len(notifications)
        for notification in notifications:
            await self.db.delete(notification)
        
        await self.db.commit()
        return count

