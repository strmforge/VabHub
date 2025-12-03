"""
Bark 告警适配器
OPS-2A 实现
"""

import httpx
from urllib.parse import urljoin
from loguru import logger

from app.modules.alert_channels.base import BaseAlertChannelAdapter


class BarkAlertAdapter(BaseAlertChannelAdapter):
    """Bark 推送告警适配器"""

    async def send(self, title: str, body: str) -> None:
        """
        通过 Bark 发送告警
        
        需要配置:
            server: Bark 服务器地址 (如 https://api.day.app/<key>/)
            sound: 可选的提示音 (默认 alarm)
            group: 可选的分组名称
        """
        server = self.get_config("server", "").rstrip("/")
        sound = self.get_config("sound", "alarm")
        group = self.get_config("group", "VabHub")

        if not server:
            logger.warning(f"[bark] channel {self.channel.name} missing server")
            return

        # Bark URL 格式: https://api.day.app/<key>/<title>/<body>
        # 或者用 POST JSON
        url = f"{server}/push"
        payload = {
            "title": title,
            "body": body,
            "sound": sound,
            "group": group,
            "icon": "https://raw.githubusercontent.com/vabhub/vabhub/main/docs/logo.png",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                logger.info(f"[bark] sent alert to {self.channel.name}")
        except httpx.HTTPError as e:
            logger.error(f"[bark] failed to send alert: {e}")
            raise
