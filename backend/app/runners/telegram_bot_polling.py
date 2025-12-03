"""
Telegram Bot 长轮询 Runner
BOT-TELEGRAM 实现

运行方式：
    python -m app.runners.telegram_bot_polling
    
参数：
    --timeout: 长轮询超时时间（秒），默认 30
"""

import asyncio
import argparse
from loguru import logger

from app.core.config import settings
from app.modules.bots.telegram_bot_client import get_telegram_bot_client
from app.modules.bots.telegram_bot_handlers import handle_update, setup_bot_commands
from app.services.runner_heartbeat import runner_context


RUNNER_NAME = "telegram_bot_polling"


async def run_polling(timeout: int = 30):
    """
    运行长轮询
    
    Args:
        timeout: 长轮询超时时间（秒）
    """
    # 检查配置
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("[telegram-bot] TELEGRAM_BOT_TOKEN not configured, exiting")
        return
    
    if not settings.TELEGRAM_BOT_ENABLED:
        logger.warning("[telegram-bot] Bot is disabled (TELEGRAM_BOT_ENABLED=false), exiting")
        return
    
    client = get_telegram_bot_client()
    if not client:
        logger.error("[telegram-bot] Failed to initialize bot client")
        return
    
    # 获取 Bot 信息
    bot_info = await client.get_me()
    if bot_info:
        logger.info(f"[telegram-bot] Bot started: @{bot_info.get('username', 'unknown')}")
    else:
        logger.warning("[telegram-bot] Failed to get bot info, continuing anyway")
    
    # 设置命令列表
    await setup_bot_commands()
    
    # 开始长轮询
    offset = None
    logger.info(f"[telegram-bot] Starting long polling (timeout={timeout}s)")
    
    while True:
        try:
            updates = await client.get_updates(
                offset=offset,
                timeout=timeout,
                allowed_updates=["message", "callback_query"],
            )
            
            for update in updates:
                update_id = update.get("update_id")
                if update_id:
                    offset = update_id + 1
                
                # 异步处理更新
                asyncio.create_task(handle_update(update))
                
        except asyncio.CancelledError:
            logger.info("[telegram-bot] Polling cancelled, shutting down")
            break
        except Exception as e:
            logger.error(f"[telegram-bot] Polling error: {e}")
            await asyncio.sleep(5)  # 出错后等待 5 秒再重试


async def main(timeout: int = 30):
    """主入口"""
    logger.info(f"[telegram-bot] Runner starting...")
    
    async with runner_context(RUNNER_NAME, runner_type="bot"):
        await run_polling(timeout)


def cli():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="Telegram Bot Polling Runner")
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Long polling timeout in seconds (default: 30)",
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(main(timeout=args.timeout))
    except KeyboardInterrupt:
        logger.info("[telegram-bot] Interrupted by user")


if __name__ == "__main__":
    cli()
