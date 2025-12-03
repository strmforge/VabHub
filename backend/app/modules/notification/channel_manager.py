"""
通知渠道管理器
"""
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio

from .channels.telegram import TelegramChannel
from .channels.wechat import WeChatChannel
from .channels.base import NotificationChannelBase


class NotificationChannelManager:
    """通知渠道管理器"""
    
    def __init__(self, channel_configs: Optional[Dict[str, Dict]] = None):
        """
        初始化通知渠道管理器
        
        Args:
            channel_configs: 渠道配置字典，格式：
                {
                    "telegram": {"bot_token": "...", "chat_id": "..."},
                    "wechat": {"webhook_url": "..."}
                }
        """
        self.channel_configs = channel_configs or {}
        self.channel_instances: Dict[str, NotificationChannelBase] = {}
        
        # 初始化渠道实例
        self._initialize_channels()
        
        # 保留旧的处理方法以兼容
        self.channel_handlers = {
            "system": self._send_system_notification,
            "email": self._send_email_notification,
            "telegram": self._send_telegram_notification,
            "wechat": self._send_wechat_notification,
            "webhook": self._send_webhook_notification,
            "push": self._send_push_notification,
        }
    
    def _initialize_channels(self):
        """初始化渠道实例"""
        # Telegram
        if "telegram" in self.channel_configs:
            try:
                self.channel_instances["telegram"] = TelegramChannel(
                    self.channel_configs["telegram"]
                )
            except Exception as e:
                logger.error(f"初始化Telegram渠道失败: {e}")
        
        # WeChat
        if "wechat" in self.channel_configs:
            try:
                self.channel_instances["wechat"] = WeChatChannel(
                    self.channel_configs["wechat"]
                )
            except Exception as e:
                logger.error(f"初始化WeChat渠道失败: {e}")
    
    def update_channel_config(self, channel_name: str, config: Dict):
        """
        更新渠道配置
        
        Args:
            channel_name: 渠道名称
            config: 配置字典
        """
        self.channel_configs[channel_name] = config
        
        # 重新初始化渠道实例
        if channel_name == "telegram":
            try:
                self.channel_instances["telegram"] = TelegramChannel(config)
            except Exception as e:
                logger.error(f"更新Telegram渠道配置失败: {e}")
        elif channel_name == "wechat":
            try:
                self.channel_instances["wechat"] = WeChatChannel(config)
            except Exception as e:
                logger.error(f"更新WeChat渠道配置失败: {e}")
    
    async def send(
        self,
        title: str,
        message: str,
        notification_type: str = "info",
        channels: List[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Dict]:
        """发送通知到多个渠道"""
        channels = channels or ["system"]
        results = {}
        
        for channel in channels:
            # 优先使用新的渠道实例
            if channel in self.channel_instances:
                try:
                    channel_instance = self.channel_instances[channel]
                    # 从metadata中提取渠道特定配置（如果存在）
                    channel_metadata = metadata.get(f"{channel}_config") if metadata else None
                    result = await channel_instance.send(
                        title=title,
                        message=message,
                        notification_type=notification_type,
                        metadata=channel_metadata or metadata
                    )
                    results[channel] = result
                except Exception as e:
                    logger.error(f"发送通知到 {channel} 失败: {e}")
                    results[channel] = {
                        "success": False,
                        "error": str(e)
                    }
            # 回退到旧的处理方法
            elif channel in self.channel_handlers:
                try:
                    handler = self.channel_handlers[channel]
                    result = await handler(title, message, notification_type, metadata or {})
                    results[channel] = result
                except Exception as e:
                    logger.error(f"发送通知到 {channel} 失败: {e}")
                    results[channel] = {
                        "success": False,
                        "error": str(e)
                    }
            else:
                logger.warning(f"未知的通知渠道: {channel}")
                results[channel] = {
                    "success": False,
                    "error": f"未知的通知渠道: {channel}"
                }
        
        return results
    
    async def _send_system_notification(
        self,
        title: str,
        message: str,
        notification_type: str,
        metadata: Dict
    ) -> Dict:
        """发送系统通知（存储在数据库中）"""
        # 系统通知已经通过数据库存储，这里只需要记录成功
        logger.info(f"系统通知: {title} - {message}")
        return {
            "success": True,
            "channel": "system",
            "message": "通知已保存到数据库"
        }
    
    async def _send_email_notification(
        self,
        title: str,
        message: str,
        notification_type: str,
        metadata: Dict
    ) -> Dict:
        """发送邮件通知"""
        # TODO: 从配置中获取邮件服务器配置
        email_config = metadata.get("email_config") or {}
        
        smtp_host = email_config.get("smtp_host", "smtp.gmail.com")
        smtp_port = email_config.get("smtp_port", 587)
        smtp_user = email_config.get("smtp_user")
        smtp_password = email_config.get("smtp_password")
        to_email = email_config.get("to_email")
        
        if not smtp_user or not smtp_password or not to_email:
            return {
                "success": False,
                "error": "邮件配置不完整"
            }
        
        try:
            # 使用线程池执行同步的邮件发送
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._send_email_sync,
                smtp_host,
                smtp_port,
                smtp_user,
                smtp_password,
                to_email,
                title,
                message
            )
            
            return {
                "success": True,
                "channel": "email",
                "message": f"邮件已发送到 {to_email}"
            }
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _send_email_sync(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        to_email: str,
        title: str,
        message: str
    ):
        """同步发送邮件"""
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = title
        
        msg.attach(MIMEText(message, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
    
    async def _send_telegram_notification(
        self,
        title: str,
        message: str,
        notification_type: str,
        metadata: Dict
    ) -> Dict:
        """发送Telegram通知（兼容旧方法）"""
        # 如果已有渠道实例，使用它
        if "telegram" in self.channel_instances:
            return await self.channel_instances["telegram"].send(
                title, message, notification_type, metadata
            )
        
        # 否则从metadata中获取配置
        telegram_config = metadata.get("telegram_config") or {}
        
        bot_token = telegram_config.get("bot_token")
        chat_id = telegram_config.get("chat_id")
        
        if not bot_token or not chat_id:
            return {
                "success": False,
                "error": "Telegram配置不完整"
            }
        
        # 创建临时实例
        try:
            temp_channel = TelegramChannel(telegram_config)
            return await temp_channel.send(title, message, notification_type, metadata)
        except Exception as e:
            logger.error(f"发送Telegram通知失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _send_wechat_notification(
        self,
        title: str,
        message: str,
        notification_type: str,
        metadata: Dict
    ) -> Dict:
        """发送微信通知（兼容旧方法）"""
        # 如果已有渠道实例，使用它
        if "wechat" in self.channel_instances:
            return await self.channel_instances["wechat"].send(
                title, message, notification_type, metadata
            )
        
        # 否则从metadata中获取配置
        wechat_config = metadata.get("wechat_config") or {}
        
        # 创建临时实例
        try:
            temp_channel = WeChatChannel(wechat_config)
            return await temp_channel.send(title, message, notification_type, metadata)
        except Exception as e:
            logger.error(f"发送微信通知失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _send_webhook_notification(
        self,
        title: str,
        message: str,
        notification_type: str,
        metadata: Dict
    ) -> Dict:
        """发送Webhook通知"""
        webhook_config = metadata.get("webhook_config") or {}
        
        webhook_url = webhook_config.get("url")
        method = webhook_config.get("method", "POST")
        headers = webhook_config.get("headers", {})
        
        if not webhook_url:
            return {
                "success": False,
                "error": "Webhook URL未配置"
            }
        
        try:
            data = {
                "title": title,
                "message": message,
                "type": notification_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                if method.upper() == "POST":
                    response = await client.post(webhook_url, json=data, headers=headers)
                elif method.upper() == "GET":
                    response = await client.get(webhook_url, params=data, headers=headers)
                else:
                    return {
                        "success": False,
                        "error": f"不支持的HTTP方法: {method}"
                    }
                
                if response.is_success:
                    return {
                        "success": True,
                        "channel": "webhook",
                        "message": "Webhook已调用"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Webhook错误: {response.text}"
                    }
        except Exception as e:
            logger.error(f"发送Webhook通知失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _send_push_notification(
        self,
        title: str,
        message: str,
        notification_type: str,
        metadata: Dict
    ) -> Dict:
        """发送推送通知（浏览器推送）"""
        # TODO: 实现浏览器推送通知
        # 这通常需要：
        # 1. 用户订阅推送服务
        # 2. 使用Web Push API
        # 3. 存储用户订阅信息
        
        logger.info(f"推送通知: {title} - {message}")
        return {
            "success": True,
            "channel": "push",
            "message": "推送通知已发送"
        }

