"""
系统健康检查 Runner
OPS-1D 实现

用法:
    python -m app.runners.ops_health_check           # 单次执行
    python -m app.runners.ops_health_check --loop    # 循环模式
    python -m app.runners.ops_health_check --loop --interval 300  # 每 5 分钟
"""

import argparse
import asyncio
from loguru import logger

from app.core.database import async_session_factory
from app.services.runner_heartbeat import runner_context
from app.services.system_health_service import run_all_health_checks, get_health_summary
from app.services.system_health_notify import check_and_notify_health_status


async def _run_once():
    """执行一次健康检查"""
    logger.info("开始执行系统健康检查...")
    
    async with async_session_factory() as session:
        checks = await run_all_health_checks(session)
        summary = await get_health_summary(session)
        
        # 输出汇总
        logger.info("=" * 50)
        logger.info(f"健康检查完成: {summary.total_checks} 项")
        logger.info(f"  ✅ OK: {summary.ok_count}")
        logger.info(f"  ⚠️  Warning: {summary.warning_count}")
        logger.info(f"  ❌ Error: {summary.error_count}")
        logger.info(f"  ❓ Unknown: {summary.unknown_count}")
        logger.info(f"整体状态: {summary.overall_status.upper()}")
        logger.info("=" * 50)
        
        # 输出错误详情
        if summary.error_count > 0:
            logger.warning("错误详情:")
            for check in summary.checks:
                if check.status == "error":
                    logger.warning(f"  - {check.key}: {check.last_error}")
        
        # 检查并发送通知（带降频）
        await check_and_notify_health_status(session, summary)
        
        return summary


async def _main_async(args: argparse.Namespace):
    """异步主入口"""
    recommended_interval = args.interval // 60 if args.loop else 5
    
    async with runner_context("ops_health_check", runner_type="scheduled", recommended_interval_min=recommended_interval):
        if args.loop:
            logger.info(f"循环模式，间隔 {args.interval} 秒")
            while True:
                try:
                    await _run_once()
                except Exception as e:
                    logger.error(f"健康检查失败: {e}")
                
                await asyncio.sleep(args.interval)
        else:
            await _run_once()


def main():
    parser = argparse.ArgumentParser(description="VabHub 系统健康检查 Runner")
    parser.add_argument(
        "--loop",
        action="store_true",
        help="循环运行模式",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="循环间隔（秒），默认 300",
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("VabHub Ops Health Check Runner")
    logger.info("=" * 60)
    
    asyncio.run(_main_async(args))


if __name__ == "__main__":
    main()
