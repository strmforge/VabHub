"""
Telegram 告警适配器
OPS-2A 实现
"""

import httpx
from loguru import logger

from app.modules.alert_channels.base import BaseAlertChannelAdapter


class TelegramAlertAdapter(BaseAlertChannelAdapter):
    """Telegram Bot 告警适配器"""

    async def send(self, title: str, body: str) -> None:
        """
        通过 Telegram Bot 发送告警
        
        需要配置:
            bot_token: Telegram Bot Token
            chat_id: 目标 Chat ID
        """
        bot_token = self.get_config("bot_token")
        chat_id = self.get_config("chat_id")

        if not bot_token or not chat_id:
            logger.warning(f"[telegram] channel {self.channel.name} missing bot_token or chat_id")
            return

        # 组装消息
        text = f"🚨 *{title}*\n\n{body}"

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                logger.info(f"[telegram] sent alert to {self.channel.name}")
        except httpx.HTTPError as e:
            logger.error(f"[telegram] failed to send alert: {e}")
            raise
