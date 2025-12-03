"""
TTS Job Runner CLI

命令行工具：批量执行 TTS Job
用法：python -m app.cli.run_tts_jobs --max-jobs=5
"""
import asyncio
import argparse
import sys
from loguru import logger

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.modules.tts.job_runner import run_batch_jobs


def setup_logging():
    """配置日志输出到标准输出"""
    logger.remove()  # 移除默认处理器
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )


async def main_async(max_jobs: int, stop_when_empty: bool = True):
    """
    主异步函数
    
    Args:
        max_jobs: 最多处理的 Job 数量
        stop_when_empty: 当没有 queued Job 时是否立即退出
    """
    logger.info("=" * 60)
    logger.info("VabHub TTS Job Runner")
    logger.info("=" * 60)
    logger.info(f"配置：最多处理 {max_jobs} 个 Job")
    logger.info(f"停止策略：{'无任务时立即退出' if stop_when_empty else '继续轮询'}")
    logger.info("")
    
    try:
        # 创建数据库会话
        async with AsyncSessionLocal() as db:
            # 调用现有的 job_runner
            result = await run_batch_jobs(
                db=db,
                settings=settings,
                max_jobs=max_jobs
            )
            
            # 打印执行结果
            logger.info("")
            logger.info("=" * 60)
            logger.info("执行结果汇总")
            logger.info("=" * 60)
            logger.info(f"尝试处理的 Job 数：{result.total_jobs}")
            logger.info(f"实际执行的 Job 数：{result.run_jobs}")
            logger.info(f"成功完成的 Job 数：{result.succeeded_jobs}")
            logger.info(f"部分完成的 Job 数：{result.partial_jobs}（可继续执行）")
            logger.info(f"失败的 Job 数：{result.failed_jobs}")
            
            if result.last_job_id:
                logger.info(f"最后处理的 Job ID：{result.last_job_id}")
            
            if result.total_jobs == 0:
                logger.info("")
                logger.info("提示：当前没有待处理的 TTS Job")
            
            logger.info("=" * 60)
            
            # 返回退出码：如果有失败的 Job，返回非 0
            if result.failed_jobs > 0:
                return 1
            return 0
            
    except Exception as e:
        logger.error("执行过程中发生错误：", exc_info=True)
        logger.error(f"错误详情：{str(e)}")
        return 1


def cli_entry():
    """CLI 入口函数"""
    parser = argparse.ArgumentParser(
        description="VabHub TTS Job Runner - 批量执行 TTS Job",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python -m app.cli.run_tts_jobs --max-jobs=5
  python -m app.cli.run_tts_jobs --max-jobs=10 --no-stop-when-empty
        """
    )
    
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=settings.SMART_TTS_JOB_RUNNER_MAX_JOBS_PER_RUN,
        help=f"单次执行最多处理的 Job 数量（默认：{settings.SMART_TTS_JOB_RUNNER_MAX_JOBS_PER_RUN}）"
    )
    
    parser.add_argument(
        "--no-stop-when-empty",
        action="store_true",
        help="当没有 queued Job 时不立即退出（继续轮询，不推荐）"
    )
    
    args = parser.parse_args()
    
    # 配置日志
    setup_logging()
    
    # 运行异步主函数
    exit_code = asyncio.run(main_async(
        max_jobs=args.max_jobs,
        stop_when_empty=not args.no_stop_when_empty
    ))
    
    sys.exit(exit_code)


if __name__ == "__main__":
    cli_entry()

