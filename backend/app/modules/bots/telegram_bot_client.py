"""
Telegram Bot Client
BOT-TELEGRAM 实现

封装 Telegram Bot API 调用，提供：
- send_message: 发送文本消息
- send_photo: 发送图片
- answer_callback_query: 响应回调查询
- get_updates: 长轮询获取更新
"""

from typing import Any, Optional
import httpx
from loguru import logger

from app.core.config import settings


class TelegramBotClient:
    """Telegram Bot API 客户端"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.timeout = 60  # 长轮询超时
    
    async def _request(
        self,
        method: str,
        data: Optional[dict] = None,
        timeout: Optional[float] = None,
    ) -> dict[str, Any]:
        """发送 API 请求"""
        url = f"{self.base_url}/{method}"
        
        # 配置代理
        proxies = None
        if settings.TELEGRAM_BOT_PROXY:
            proxies = {
                "http://": settings.TELEGRAM_BOT_PROXY,
                "https://": settings.TELEGRAM_BOT_PROXY,
            }
            logger.debug(f"[telegram] using proxy: {settings.TELEGRAM_BOT_PROXY}")
        
        try:
            async with httpx.AsyncClient(
                timeout=timeout or 30,
                proxies=proxies
            ) as client:
                resp = await client.post(url, json=data or {})
                resp.raise_for_status()
                result = resp.json()
                
                if not result.get("ok"):
                    logger.warning(f"[telegram] API error: {result.get('description')}")
                    
                return result
        except httpx.HTTPError as e:
            logger.error(f"[telegram] request failed: {e}")
            raise
    
    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        parse_mode: str = "Markdown",
        reply_markup: Optional[dict] = None,
        disable_web_page_preview: bool = False,
    ) -> bool:
        """
        发送文本消息
        
        Args:
            chat_id: 目标 Chat ID
            text: 消息文本
            parse_mode: 解析模式 (Markdown/HTML)
            reply_markup: 回复键盘
            disable_web_page_preview: 禁用链接预览
            
        Returns:
            是否发送成功
        """
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }
        
        if reply_markup:
            data["reply_markup"] = reply_markup
        
        try:
            result = await self._request("sendMessage", data)
            return result.get("ok", False)
        except Exception as e:
            logger.error(f"[telegram] send_message failed: {e}")
            return False
    
    async def send_photo(
        self,
        chat_id: int | str,
        photo: str,  # URL or file_id
        caption: Optional[str] = None,
        parse_mode: str = "Markdown",
        reply_markup: Optional[dict] = None,
    ) -> bool:
        """发送图片"""
        data = {
            "chat_id": chat_id,
            "photo": photo,
            "parse_mode": parse_mode,
        }
        
        if caption:
            data["caption"] = caption
        if reply_markup:
            data["reply_markup"] = reply_markup
        
        try:
            result = await self._request("sendPhoto", data)
            return result.get("ok", False)
        except Exception as e:
            logger.error(f"[telegram] send_photo failed: {e}")
            return False
    
    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False,
    ) -> bool:
        """响应回调查询（按钮点击）"""
        data = {
            "callback_query_id": callback_query_id,
            "show_alert": show_alert,
        }
        
        if text:
            data["text"] = text
        
        try:
            result = await self._request("answerCallbackQuery", data)
            return result.get("ok", False)
        except Exception as e:
            logger.error(f"[telegram] answer_callback_query failed: {e}")
            return False
    
    async def get_updates(
        self,
        offset: Optional[int] = None,
        timeout: int = 30,
        allowed_updates: Optional[list[str]] = None,
    ) -> list[dict]:
        """
        长轮询获取更新
        
        Args:
            offset: 更新偏移量
            timeout: 长轮询超时（秒）
            allowed_updates: 允许的更新类型
            
        Returns:
            更新列表
        """
        data = {
            "timeout": timeout,
        }
        
        if offset is not None:
            data["offset"] = offset
        if allowed_updates:
            data["allowed_updates"] = allowed_updates
        
        try:
            result = await self._request("getUpdates", data, timeout=timeout + 10)
            return result.get("result", [])
        except Exception as e:
            logger.error(f"[telegram] get_updates failed: {e}")
            return []
    
    async def get_me(self) -> Optional[dict]:
        """获取 Bot 信息"""
        try:
            result = await self._request("getMe")
            return result.get("result")
        except Exception:
            return None
    
    async def set_my_commands(self, commands: list[dict]) -> bool:
        """设置 Bot 命令列表"""
        try:
            result = await self._request("setMyCommands", {"commands": commands})
            return result.get("ok", False)
        except Exception as e:
            logger.error(f"[telegram] set_my_commands failed: {e}")
            return False
    
    async def edit_message_text(
        self,
        chat_id: int | str,
        message_id: int,
        text: str,
        parse_mode: str = "Markdown",
        reply_markup: Optional[dict] = None,
        disable_web_page_preview: bool = True,
    ) -> bool:
        """编辑消息文本"""
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }
        
        if reply_markup:
            data["reply_markup"] = reply_markup
        
        try:
            result = await self._request("editMessageText", data)
            return result.get("ok", False)
        except Exception as e:
            logger.error(f"[telegram] edit_message_text failed: {e}")
            return False
    
    async def delete_message(
        self,
        chat_id: int | str,
        message_id: int,
    ) -> bool:
        """删除消息"""
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
        }
        
        try:
            result = await self._request("deleteMessage", data)
            return result.get("ok", False)
        except Exception as e:
            logger.error(f"[telegram] delete_message failed: {e}")
            return False


# ============== 全局单例 ==============

_telegram_bot_client: Optional[TelegramBotClient] = None


def get_telegram_bot_client() -> Optional[TelegramBotClient]:
    """
    获取 Telegram Bot Client 单例
    
    如果未配置 TELEGRAM_BOT_TOKEN，返回 None
    """
    global _telegram_bot_client
    
    if _telegram_bot_client is None:
        token = settings.TELEGRAM_BOT_TOKEN
        if token:
            _telegram_bot_client = TelegramBotClient(token)
            logger.info("[telegram] bot client initialized")
        else:
            logger.debug("[telegram] bot not configured (TELEGRAM_BOT_TOKEN not set)")
    
    return _telegram_bot_client


def reset_telegram_bot_client():
    """重置客户端（用于测试或配置变更）"""
    global _telegram_bot_client
    _telegram_bot_client = None
