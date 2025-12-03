"""
TTS Storage Cleanup Runner CLI

命令行工具：自动清理 TTS 存储目录
用法：python -m app.cli.run_tts_storage_cleanup --mode=auto --dry-run
"""
import asyncio
import argparse
import sys
from loguru import logger

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.modules.tts.storage_runner import run_scheduled_cleanup


def setup_logging():
    """配置日志输出到标准输出"""
    logger.remove()  # 移除默认处理器
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )


def format_bytes(bytes_count: int) -> str:
    """格式化字节数为可读字符串"""
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 ** 2:
        return f"{bytes_count / 1024:.2f} KB"
    elif bytes_count < 1024 ** 3:
        return f"{bytes_count / (1024 ** 2):.2f} MB"
    else:
        return f"{bytes_count / (1024 ** 3):.2f} GB"


async def main_async(mode: str, dry_run: bool):
    """
    主异步函数
    
    Args:
        mode: 运行模式，"auto" 或 "manual"
        dry_run: 是否只预览不实际删除
    """
    logger.info("=" * 60)
    logger.info("VabHub TTS Storage Cleanup Runner")
    logger.info("=" * 60)
    logger.info(f"运行模式：{mode}")
    logger.info(f"Dry Run：{'是（仅预览）' if dry_run else '否（实际删除）'}")
    logger.info("")
    
    try:
        # 创建数据库会话
        async with AsyncSessionLocal() as db:
            # 调用现有的 storage_runner
            if mode == "manual":
                # 手动模式：强制执行，忽略间隔和警告级别检查
                result = await run_scheduled_cleanup(
                    db=db,
                    settings=settings,
                    force=True,
                    dry_run_override=dry_run
                )
            else:
                # auto 模式：遵循配置的策略
                result = await run_scheduled_cleanup(
                    db=db,
                    settings=settings,
                    force=False,
                    dry_run_override=dry_run
                )
            
            # 打印执行结果
            logger.info("")
            logger.info("=" * 60)
            logger.info("执行结果")
            logger.info("=" * 60)
            logger.info(f"状态：{result.status}")
            
            if result.reason:
                logger.info(f"原因：{result.reason}")
            
            if result.status == "skipped":
                reason_map = {
                    "auto_disabled": "自动清理未启用",
                    "too_soon": "距离上次执行时间太短",
                    "below_warn": "存储占用未达到警告级别",
                    "no_root": "存储根目录不存在",
                    "scan_error": "扫描存储目录失败",
                    "nothing_to_clean": "没有需要清理的文件",
                    "plan_error": "构建清理计划失败",
                    "dry_run": "预览模式（未实际删除）"
                }
                reason_text = reason_map.get(result.reason, result.reason or "未知原因")
                logger.info(f"跳过原因：{reason_text}")
            elif result.status == "success":
                logger.info(f"删除文件数：{result.deleted_files_count}")
                logger.info(f"释放空间：{format_bytes(result.freed_bytes)}")
                if dry_run:
                    logger.info("（预览模式，未实际删除）")
            elif result.status == "failed":
                logger.error("清理失败")
            
            logger.info(f"开始时间：{result.started_at}")
            logger.info(f"结束时间：{result.finished_at}")
            logger.info("=" * 60)
            
            # 返回退出码：失败时返回非 0
            if result.status == "failed":
                return 1
            return 0
            
    except Exception as e:
        logger.error("执行过程中发生错误：", exc_info=True)
        logger.error(f"错误详情：{str(e)}")
        return 1


def cli_entry():
    """CLI 入口函数"""
    parser = argparse.ArgumentParser(
        description="VabHub TTS Storage Cleanup Runner - 自动清理 TTS 存储目录",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 自动模式，预览（不实际删除）
  python -m app.cli.run_tts_storage_cleanup --mode=auto --dry-run
  
  # 自动模式，实际执行
  python -m app.cli.run_tts_storage_cleanup --mode=auto
  
  # 手动模式，强制执行（忽略间隔和警告级别）
  python -m app.cli.run_tts_storage_cleanup --mode=manual
        """
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["auto", "manual"],
        default="auto",
        help="运行模式：auto（遵循配置策略）或 manual（强制执行，默认：auto）"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览模式：只计算将要删除的文件和释放空间，不实际删除"
    )
    
    args = parser.parse_args()
    
    # 配置日志
    setup_logging()
    
    # 运行异步主函数
    exit_code = asyncio.run(main_async(
        mode=args.mode,
        dry_run=args.dry_run
    ))
    
    sys.exit(exit_code)


if __name__ == "__main__":
    cli_entry()

