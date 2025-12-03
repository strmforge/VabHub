"""
Telegram通知渠道
"""
import httpx
from typing import Dict, Optional, Any
from loguru import logger
import re

from .base import NotificationChannelBase


class TelegramChannel(NotificationChannelBase):
    """Telegram通知渠道"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Telegram渠道
        
        Args:
            config: 配置字典，包含：
                - bot_token: Telegram Bot Token
                - chat_id: 聊天ID（可以是用户ID或群组ID）
                - parse_mode: 解析模式（Markdown或HTML，默认Markdown）
                - api_url: 自定义API URL（可选，用于代理）
        """
        super().__init__(config)
        self.bot_token = config.get("bot_token")
        self.chat_id = config.get("chat_id")
        self.parse_mode = config.get("parse_mode", "Markdown")
        self.api_url = config.get("api_url", "https://api.telegram.org")
        
        # Telegram MarkdownV2 需要转义的特殊字符
        self._escape_chars = r'_*[]()~`>#+-=|{}.!'
        self._markdown_escape_pattern = re.compile(f'([{re.escape(self._escape_chars)}])')
    
    def is_configured(self) -> bool:
        """检查是否已配置"""
        return bool(self.bot_token and self.chat_id)
    
    def validate_config(self) -> tuple[bool, Optional[str]]:
        """验证配置"""
        if not self.bot_token:
            return False, "Telegram Bot Token未配置"
        if not self.chat_id:
            return False, "Telegram Chat ID未配置"
        return True, None
    
    def _escape_markdown(self, text: str) -> str:
        """
        转义MarkdownV2特殊字符
        
        Args:
            text: 原始文本
        
        Returns:
            转义后的文本
        """
        if not isinstance(text, str):
            return str(text) if text is not None else ""
        return self._markdown_escape_pattern.sub(r'\\\1', text)
    
    def _format_message(self, title: str, message: str, notification_type: str) -> str:
        """
        格式化消息
        
        Args:
            title: 标题
            message: 内容
            notification_type: 通知类型
        
        Returns:
            格式化后的消息
        """
        # 根据通知类型添加emoji
        emoji_map = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅"
        }
        emoji = emoji_map.get(notification_type, "📢")
        
        if self.parse_mode == "MarkdownV2":
            # MarkdownV2需要转义
            title = self._escape_markdown(title)
            message = self._escape_markdown(message)
            text = f"{emoji} *{title}*\n\n{message}"
        elif self.parse_mode == "Markdown":
            # 标准Markdown
            text = f"{emoji} *{title}*\n\n{message}"
        elif self.parse_mode == "HTML":
            # HTML格式
            text = f"{emoji} <b>{title}</b>\n\n{message}"
        else:
            # 纯文本
            text = f"{emoji} {title}\n\n{message}"
        
        return text
    
    async def send(
        self,
        title: str,
        message: str,
        notification_type: str = "info",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        发送Telegram通知
        
        Args:
            title: 通知标题
            message: 通知内容
            notification_type: 通知类型
            metadata: 额外元数据（可包含link等）
        
        Returns:
            发送结果
        """
        if not self.is_configured():
            return {
                "success": False,
                "channel": "telegram",
                "error": "Telegram配置不完整"
            }
        
        try:
            # 格式化消息
            text = self._format_message(title, message, notification_type)
            
            # 添加链接（如果有）
            if metadata and metadata.get("link"):
                link = metadata.get("link")
                if self.parse_mode == "MarkdownV2":
                    link_text = self._escape_markdown("查看详情")
                    text = f"{text}\n\n[{link_text}]({link})"
                elif self.parse_mode == "Markdown":
                    text = f"{text}\n\n[查看详情]({link})"
                elif self.parse_mode == "HTML":
                    text = f"{text}\n\n<a href=\"{link}\">查看详情</a>"
                else:
                    text = f"{text}\n\n查看详情: {link}"
            
            # 构建API URL
            api_url = f"{self.api_url}/bot{self.bot_token}/sendMessage"
            
            # 准备请求数据
            payload = {
                "chat_id": self.chat_id,
                "text": text,
            }
            
            # 添加解析模式（如果不是纯文本）
            if self.parse_mode != "None":
                payload["parse_mode"] = self.parse_mode
            
            # 发送请求
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(api_url, json=payload)
                
                if response.is_success:
                    result = response.json()
                    if result.get("ok"):
                        return {
                            "success": True,
                            "channel": "telegram",
                            "message": "Telegram消息已发送",
                            "message_id": result.get("result", {}).get("message_id")
                        }
                    else:
                        error_description = result.get("description", "未知错误")
                        return {
                            "success": False,
                            "channel": "telegram",
                            "error": f"Telegram API错误: {error_description}"
                        }
                else:
                    return {
                        "success": False,
                        "channel": "telegram",
                        "error": f"HTTP错误: {response.status_code} - {response.text}"
                    }
        
        except httpx.TimeoutException:
            logger.error("Telegram通知发送超时")
            return {
                "success": False,
                "channel": "telegram",
                "error": "请求超时"
            }
        except Exception as e:
            logger.error(f"发送Telegram通知失败: {e}")
            return {
                "success": False,
                "channel": "telegram",
                "error": str(e)
            }
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        测试连接
        
        Returns:
            测试结果
        """
        return await self.send(
            title="测试通知",
            message="这是一条测试消息，用于验证Telegram配置是否正确。",
            notification_type="info"
        )

