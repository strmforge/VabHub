"""
音乐榜单同步 Runner

定时同步所有启用的音乐榜单。

使用方式：
    python -m app.runners.music_chart_sync
    python -m app.runners.music_chart_sync --source-id 1
    python -m app.runners.music_chart_sync --loop --loop-interval 3600
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
    source_id: Optional[int] = None,
    limit: Optional[int] = None,
    force: bool = False,
):
    """执行一次榜单同步"""
    from app.core.database import async_session_maker
    from app.services.music_chart_service import sync_all_enabled_charts
    
    async with async_session_maker() as session:
        stats = await sync_all_enabled_charts(
            session,
            source_id=source_id,
            limit_per_run=limit,
            force=force,
        )
        
        print("\n========== 榜单同步统计 ==========")
        print(f"处理榜单数: {stats['total_charts']}")
        print(f"成功: {stats['success_count']}")
        print(f"失败: {stats['failed_count']}")
        print(f"新增条目: {stats['total_new_items']}")
        print(f"更新条目: {stats['total_updated_items']}")
        
        if stats['errors']:
            print("\n错误详情:")
            for error in stats['errors'][:5]:
                print(f"  - {error['chart_name']}: {error['error']}")
            if len(stats['errors']) > 5:
                print(f"  ... 还有 {len(stats['errors']) - 5} 个错误")
        
        print("==================================\n")
        
        return stats


async def main():
    parser = argparse.ArgumentParser(description='音乐榜单同步工具')
    parser.add_argument('--source-id', type=int, help='只同步指定源的榜单')
    parser.add_argument('--limit', type=int, help='单次最多同步的榜单数')
    parser.add_argument('--force', action='store_true', help='强制同步（忽略抓取间隔）')
    parser.add_argument('--loop', action='store_true', help='循环运行模式')
    parser.add_argument('--loop-interval', type=int, default=3600, help='循环间隔（秒），默认 3600')
    
    args = parser.parse_args()
    
    recommended_interval = args.loop_interval // 60 if args.loop else 60
    
    async with runner_context("music_chart_sync", runner_type="scheduled", recommended_interval_min=recommended_interval):
        logger.info("音乐榜单同步 Runner 启动")
        
        if args.loop:
            logger.info(f"循环模式，间隔 {args.loop_interval} 秒")
            while True:
                try:
                    await run_sync(
                        source_id=args.source_id,
                        limit=args.limit,
                        force=args.force,
                    )
                except Exception as e:
                    logger.error(f"同步失败: {e}")
                
                logger.info(f"等待 {args.loop_interval} 秒后继续...")
                await asyncio.sleep(args.loop_interval)
        else:
            await run_sync(
                source_id=args.source_id,
                limit=args.limit,
                force=args.force,
            )


if __name__ == '__main__':
    asyncio.run(main())
