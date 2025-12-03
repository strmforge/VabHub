"""
Webhook 告警适配器
OPS-2A 实现
"""

import httpx
from loguru import logger

from app.modules.alert_channels.base import BaseAlertChannelAdapter


class WebhookAlertAdapter(BaseAlertChannelAdapter):
    """通用 Webhook 告警适配器"""

    async def send(self, title: str, body: str) -> None:
        """
        通过 Webhook 发送告警
        
        需要配置:
            url: Webhook URL
            method: HTTP 方法 (默认 POST)
            headers: 可选的额外 Headers
        """
        url = self.get_config("url")
        method = self.get_config("method", "POST").upper()
        headers = self.get_config("headers", {})

        if not url:
            logger.warning(f"[webhook] channel {self.channel.name} missing url")
            return

        payload = {
            "title": title,
            "body": body,
            "channel_name": self.channel.name,
            "severity": str(self.channel.min_severity.value) if self.channel.min_severity else "warning",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if method == "GET":
                    resp = await client.get(url, params=payload, headers=headers)
                else:
                    resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                logger.info(f"[webhook] sent alert to {self.channel.name}")
        except httpx.HTTPError as e:
            logger.error(f"[webhook] failed to send alert: {e}")
            raise
