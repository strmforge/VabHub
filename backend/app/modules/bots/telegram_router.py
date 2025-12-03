"""
Telegram Bot 命令路由器
BOT-TELEGRAM Phase 2
DEV-SDK-1 扩展

统一管理命令和回调分发，支持插件扩展
"""

from typing import Callable, Awaitable, Optional, Protocol
from loguru import logger

from app.modules.bots.telegram_context import TelegramUpdateContext


# Handler 类型定义
CommandHandler = Callable[[TelegramUpdateContext], Awaitable[None]]


# ============== 插件命令扩展接口 ==============

class BotCommandExtension(Protocol):
    """
    Bot 命令扩展接口
    
    插件实现此接口以扩展 Telegram Bot 命令
    """
    command: str  # 不含斜杠，如 'hello'
    
    async def handle(self, ctx: TelegramUpdateContext) -> None:
        """
        处理命令
        
        Args:
            ctx: Telegram 上下文对象
        """
        ...


class TelegramCommandRouter:
    """
    Telegram 命令路由器
    
    支持：
    - 命令注册：@router.command("/help")
    - 回调注册：@router.callback("menu:")
    - 纯文本 fallback
    """
    
    def __init__(self):
        self._commands: dict[str, CommandHandler] = {}
        self._callback_handlers: dict[str, CommandHandler] = {}
        self._fallback_handler: Optional[CommandHandler] = None
        self._require_bind_commands: set[str] = set()  # 需要绑定的命令
    
    def command(self, name: str, require_bind: bool = True):
        """
        注册命令处理器
        
        Args:
            name: 命令名（如 "/help" 或 "help"）
            require_bind: 是否需要绑定 VabHub 账号
        """
        if not name.startswith("/"):
            name = f"/{name}"
        
        def decorator(fn: CommandHandler):
            self._commands[name] = fn
            if require_bind:
                self._require_bind_commands.add(name)
            return fn
        return decorator
    
    def callback(self, prefix: str):
        """
        注册回调处理器
        
        Args:
            prefix: 回调数据前缀（如 "menu:" 匹配 "menu:reading"）
        """
        def decorator(fn: CommandHandler):
            self._callback_handlers[prefix] = fn
            return fn
        return decorator
    
    def set_fallback(self, fn: CommandHandler):
        """设置纯文本 fallback 处理器"""
        self._fallback_handler = fn
        return fn
    
    async def dispatch_update(self, ctx: TelegramUpdateContext) -> None:
        """
        分发 Update 到对应 Handler
        
        Args:
            ctx: 上下文对象
        """
        try:
            if ctx.is_callback:
                await self._dispatch_callback(ctx)
            elif ctx.is_command:
                await self._dispatch_command(ctx)
            elif ctx.text:
                await self._dispatch_fallback(ctx)
        except Exception as e:
            logger.error(f"[telegram-router] dispatch error: {e}", exc_info=True)
            try:
                await ctx.reply_text("❌ 处理请求时发生错误，请稍后重试")
            except Exception:
                pass
    
    async def _dispatch_command(self, ctx: TelegramUpdateContext) -> None:
        """分发命令"""
        command = ctx.command
        if not command:
            return
        
        handler = self._commands.get(command)
        if handler:
            # 内置命令
            if command in self._require_bind_commands and not ctx.is_bound:
                await self._reply_unbound(ctx)
                return
            await handler(ctx)
            return
        
        # 尝试插件命令
        plugin_cmd = await self._dispatch_plugin_command(ctx, command)
        if plugin_cmd:
            return
        
        # 未知命令
        await ctx.reply_text("未知命令，发送 /help 查看帮助")
    
    async def _dispatch_plugin_command(self, ctx: TelegramUpdateContext, command: str) -> bool:
        """
        分发插件命令
        
        Args:
            ctx: 上下文
            command: 命令名（含 /）
            
        Returns:
            是否找到并执行了插件命令
        """
        try:
            from app.services.plugin_registry import get_plugin_registry
            
            registry = get_plugin_registry()
            # 去掉斜杠
            cmd_name = command.lstrip("/")
            extension = registry.get_bot_command(cmd_name)
            
            if not extension:
                return False
            
            # 插件命令默认需要绑定
            if not ctx.is_bound:
                await self._reply_unbound(ctx)
                return True
            
            try:
                await extension.handle(ctx)
            except Exception as e:
                logger.error(f"[telegram-router] Plugin command {cmd_name} error: {e}", exc_info=True)
                await ctx.reply_text(f"❌ 插件命令执行失败: {str(e)[:100]}")
            
            return True
        except Exception as e:
            logger.warning(f"[telegram-router] Plugin command dispatch error: {e}")
            return False
    
    async def _dispatch_callback(self, ctx: TelegramUpdateContext) -> None:
        """分发回调"""
        data = ctx.callback_data
        if not data:
            await ctx.answer_callback()
            return
        
        # 按前缀匹配
        for prefix, handler in self._callback_handlers.items():
            if data.startswith(prefix):
                # 检查是否需要绑定（回调默认都需要）
                if not ctx.is_bound:
                    await ctx.answer_callback("请先绑定 VabHub 账号", show_alert=True)
                    return
                await handler(ctx)
                return
        
        # 无匹配处理器
        logger.warning(f"[telegram-router] unhandled callback: {data}")
        await ctx.answer_callback()
    
    async def _dispatch_fallback(self, ctx: TelegramUpdateContext) -> None:
        """分发纯文本"""
        if self._fallback_handler:
            # 检查绑定
            if not ctx.is_bound:
                await self._reply_unbound(ctx)
                return
            await self._fallback_handler(ctx)
    
    async def _reply_unbound(self, ctx: TelegramUpdateContext) -> None:
        """回复未绑定提示"""
        await ctx.reply_text(
            "你还没有绑定 VabHub 账号。\n\n"
            "请先在 VabHub 网页端：\n"
            "1. 进入「设置 → 通知渠道」\n"
            "2. 点击「获取绑定码」\n"
            "3. 然后发送 `/start <绑定码>` 给我"
        )


# ============== 全局路由器实例 ==============

router = TelegramCommandRouter()
