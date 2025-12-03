"""
音乐订阅同步 Runner

定时处理用户的音乐订阅，搜索和下载新曲目。

使用方式：
    python -m app.runners.music_subscription_sync
    python -m app.runners.music_subscription_sync --include-paused
    python -m app.runners.music_subscription_sync --loop --loop-interval 1800
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from loguru import logger

from app.services.runner_heartbeat import runner_context


async def run_sync(
    include_paused: bool = False,
    limit: Optional[int] = None,
):
    """执行一次订阅同步"""
    from app.core.database import async_session_maker
    from app.services.music_subscription_service import sync_all_active_subscriptions
    
    async with async_session_maker() as session:
        stats = await sync_all_active_subscriptions(
            session,
            include_paused=include_paused,
            limit=limit,
        )
        
        print("\n========== 订阅同步统计 ==========")
        print(f"处理订阅数: {stats['total_subscriptions']}")
        print(f"成功: {stats['success_count']}")
        print(f"失败: {stats['failed_count']}")
        print(f"新曲目: {stats['total_new_items']}")
        print(f"搜索任务: {stats['total_searches']}")
        print(f"下载任务: {stats['total_downloads']}")
        
        if stats['errors']:
            print("\n错误详情:")
            for error in stats['errors'][:5]:
                print(f"  - {error}")
            if len(stats['errors']) > 5:
                print(f"  ... 还有 {len(stats['errors']) - 5} 个错误")
        
        print("==================================\n")
        
        return stats


async def main():
    parser = argparse.ArgumentParser(description='音乐订阅同步工具')
    parser.add_argument('--include-paused', action='store_true', help='包含暂停的订阅')
    parser.add_argument('--limit', type=int, help='单次最多处理的订阅数')
    parser.add_argument('--loop', action='store_true', help='循环运行模式')
    parser.add_argument('--loop-interval', type=int, default=1800, help='循环间隔（秒），默认 1800')
    
    args = parser.parse_args()
    
    recommended_interval = args.loop_interval // 60 if args.loop else 30
    
    async with runner_context("music_subscription_sync", runner_type="scheduled", recommended_interval_min=recommended_interval):
        logger.info("音乐订阅同步 Runner 启动")
        
        if args.loop:
            logger.info(f"循环模式，间隔 {args.loop_interval} 秒")
            while True:
                try:
                    await run_sync(
                        include_paused=args.include_paused,
                        limit=args.limit,
                    )
                except Exception as e:
                    logger.error(f"同步失败: {e}")
                
                logger.info(f"等待 {args.loop_interval} 秒后继续...")
                await asyncio.sleep(args.loop_interval)
        else:
            await run_sync(
                include_paused=args.include_paused,
                limit=args.limit,
            )


if __name__ == '__main__':
    asyncio.run(main())
