"""
Telegram Bot 上下文对象
BOT-TELEGRAM Phase 2

封装 Update 信息和便捷方法，供 Handler 使用
"""

from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.user import User


class TelegramUpdateContext:
    """
    Telegram 更新上下文
    
    封装一次 Update 的所有信息，提供便捷方法
    """
    
    def __init__(
        self,
        update: dict[str, Any],
        session: AsyncSession,
        bot_client: Any,  # TelegramBotClient
    ):
        self.update = update
        self.session = session
        self.bot_client = bot_client
        
        # 解析 message
        self.message = update.get("message")
        self.callback_query = update.get("callback_query")
        
        # 提取核心字段
        if self.message:
            self.chat_id = self.message.get("chat", {}).get("id")
            self.from_user_id = self.message.get("from", {}).get("id")
            self.message_id = self.message.get("message_id")
            self._raw_text = self.message.get("text", "")
        elif self.callback_query:
            self.chat_id = self.callback_query.get("message", {}).get("chat", {}).get("id")
            self.from_user_id = self.callback_query.get("from", {}).get("id")
            self.message_id = self.callback_query.get("message", {}).get("message_id")
            self._raw_text = ""
        else:
            self.chat_id = None
            self.from_user_id = None
            self.message_id = None
            self._raw_text = ""
        
        # 解析命令和参数
        self.text = self._raw_text.strip()
        self.command: Optional[str] = None
        self.args: str = ""
        
        if self.text.startswith("/"):
            parts = self.text.split(maxsplit=1)
            # 去掉 @bot_username
            self.command = parts[0].lower().split("@")[0]
            self.args = parts[1] if len(parts) > 1 else ""
        
        # 回调数据
        self.callback_id: Optional[str] = None
        self.callback_data: str = ""
        if self.callback_query:
            self.callback_id = self.callback_query.get("id")
            self.callback_data = self.callback_query.get("data", "")
        
        # 用户信息
        self._from_user = self.message.get("from", {}) if self.message else \
                          self.callback_query.get("from", {}) if self.callback_query else {}
        self.username = self._from_user.get("username")
        self.first_name = self._from_user.get("first_name")
        self.last_name = self._from_user.get("last_name")
        self.language_code = self._from_user.get("language_code")
        
        # 绑定的 VabHub 用户（需要外部注入）
        self.app_user: Optional[User] = None
    
    @property
    def is_command(self) -> bool:
        """是否是命令消息"""
        return self.command is not None
    
    @property
    def is_callback(self) -> bool:
        """是否是回调查询"""
        return self.callback_query is not None
    
    @property
    def is_bound(self) -> bool:
        """用户是否已绑定 VabHub"""
        return self.app_user is not None
    
    @property
    def is_admin(self) -> bool:
        """用户是否是管理员"""
        if not self.app_user:
            return False
        return getattr(self.app_user, "is_superuser", False)
    
    # ============== 便捷回复方法 ==============
    
    async def reply_text(
        self,
        text: str,
        reply_markup: Optional[dict] = None,
        parse_mode: str = "Markdown",
        disable_preview: bool = True,
    ) -> bool:
        """回复文本消息"""
        if not self.chat_id or not self.bot_client:
            return False
        return await self.bot_client.send_message(
            self.chat_id,
            text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_preview,
        )
    
    async def reply_photo(
        self,
        photo: str,
        caption: Optional[str] = None,
        reply_markup: Optional[dict] = None,
    ) -> bool:
        """回复图片"""
        if not self.chat_id or not self.bot_client:
            return False
        return await self.bot_client.send_photo(
            self.chat_id,
            photo,
            caption=caption,
            reply_markup=reply_markup,
        )
    
    async def edit_message_text(
        self,
        text: str,
        reply_markup: Optional[dict] = None,
        parse_mode: str = "Markdown",
    ) -> bool:
        """编辑消息文本（用于回调后更新消息）"""
        if not self.chat_id or not self.message_id or not self.bot_client:
            return False
        return await self.bot_client.edit_message_text(
            self.chat_id,
            self.message_id,
            text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )
    
    async def answer_callback(
        self,
        text: Optional[str] = None,
        show_alert: bool = False,
    ) -> bool:
        """响应回调查询"""
        if not self.callback_id or not self.bot_client:
            return False
        return await self.bot_client.answer_callback_query(
            self.callback_id,
            text=text,
            show_alert=show_alert,
        )
    
    async def delete_message(self) -> bool:
        """删除当前消息"""
        if not self.chat_id or not self.message_id or not self.bot_client:
            return False
        return await self.bot_client.delete_message(self.chat_id, self.message_id)
