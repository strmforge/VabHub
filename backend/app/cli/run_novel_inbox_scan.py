"""
小说 Inbox 扫描 CLI

命令行工具：扫描 Inbox 目录中的小说文件并导入
用法：python -m app.cli.run_novel_inbox_scan --max-files=20 --generate-tts
"""
import asyncio
import argparse
import sys
from pathlib import Path
from typing import Optional
from loguru import logger

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.modules.novel.inbox_service import scan_novel_inbox_for_root


def setup_logging():
    """配置日志输出到标准输出"""
    logger.remove()  # 移除默认处理器
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )


async def main_async(max_files: Optional[int], generate_tts: bool):
    """
    主异步函数
    
    Args:
        max_files: 最多处理的文件数量（None 表示不限制）
        generate_tts: 是否自动创建 TTS Job
    """
    logger.info("=" * 60)
    logger.info("VabHub 小说 Inbox 扫描")
    logger.info("=" * 60)
    logger.info(f"Inbox 根目录: {settings.INBOX_ROOT}")
    logger.info(f"最多处理文件数: {max_files if max_files else '不限制'}")
    logger.info(f"自动创建 TTS Job: {'是' if generate_tts else '否'}")
    logger.info("")
    
    try:
        # 检查配置
        if not settings.INBOX_ENABLE_NOVEL_TXT:
            logger.warning("小说 TXT 处理已禁用（INBOX_ENABLE_NOVEL_TXT=false），退出")
            return 1
        
        # 创建数据库会话
        async with AsyncSessionLocal() as db:
            # 扫描 Inbox 根目录
            root_dir = Path(settings.INBOX_ROOT)
            
            result = await scan_novel_inbox_for_root(
                db=db,
                settings=settings,
                root_dir=root_dir,
                generate_tts=generate_tts,
                max_files=max_files
            )
            
            # 打印执行结果
            logger.info("")
            logger.info("=" * 60)
            logger.info("扫描结果汇总")
            logger.info("=" * 60)
            logger.info(f"扫描到的文件数：{result.scanned_files}")
            logger.info(f"成功导入数：{result.imported_count}")
            logger.info(f"跳过（已导入）：{result.skipped_already_imported}")
            logger.info(f"跳过（之前失败）：{result.skipped_failed_before}")
            logger.info(f"跳过（不支持格式）：{result.skipped_unsupported}")
            logger.info(f"失败数：{result.failed_count}")
            logger.info(f"创建的 TTS Job 数：{result.tts_jobs_created}")
            logger.info("=" * 60)
            
            # 返回退出码：如果有失败的，返回非 0
            if result.failed_count > 0:
                return 1
            return 0
            
    except Exception as e:
        logger.error("执行过程中发生错误：", exc_info=True)
        logger.error(f"错误详情：{str(e)}")
        return 1


def cli_entry():
    """CLI 入口函数"""
    parser = argparse.ArgumentParser(
        description="VabHub 小说 Inbox 扫描 - 扫描 Inbox 目录中的小说文件并导入",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python -m app.cli.run_novel_inbox_scan
  python -m app.cli.run_novel_inbox_scan --max-files=20
  python -m app.cli.run_novel_inbox_scan --max-files=20 --generate-tts
        """
    )
    
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="最多处理的文件数量（默认：不限制）"
    )
    
    parser.add_argument(
        "--generate-tts",
        action="store_true",
        help="自动为导入的 EBook 创建 TTS Job"
    )
    
    args = parser.parse_args()
    
    # 配置日志
    setup_logging()
    
    # 运行异步主函数
    exit_code = asyncio.run(main_async(
        max_files=args.max_files,
        generate_tts=args.generate_tts
    ))
    
    sys.exit(exit_code)


if __name__ == "__main__":
    cli_entry()

