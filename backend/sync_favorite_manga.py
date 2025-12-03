#!/usr/bin/env python3
"""
漫画收藏追更 CLI 脚本

用于手动执行漫画收藏的批量追更，可配合 cron/cronjob/systemd timer 使用。

使用方法:
    python sync_favorite_manga.py

环境变量:
    VABHUB_CONFIG_PATH - 配置文件路径（可选）
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.database import AsyncSessionLocal
from app.services.manga_sync_service import sync_all_favorite_series
from loguru import logger


async def main():
    """主函数"""
    logger.info("开始执行漫画收藏批量追更...")
    
    try:
        # 使用数据库会话
        async with AsyncSessionLocal() as session:
            # 执行批量同步
            result = await sync_all_favorite_series(
                session=session,
                limit=50,  # 限制处理数量，避免一次处理太多
                download_new=False  # 不自动下载，只同步章节数据
            )
            
            # 输出结果
            if result.get("success"):
                processed = result.get("processed_series", 0)
                new_chapters = result.get("total_new_chapters", 0)
                
                logger.info(f"✅ 漫画收藏追更完成!")
                logger.info(f"   处理系列数: {processed}")
                logger.info(f"   新增章节数: {new_chapters}")
                
                if new_chapters > 0:
                    logger.info(f"   🎉 发现 {new_chapters} 个新章节，用户会收到通知")
                else:
                    logger.info(f"   💭 暂无新章节")
                
                # 输出详细信息
                details = result.get("details", [])
                if details:
                    logger.info("   详细结果:")
                    for detail in details:
                        series_title = detail.get("title", "未知系列")
                        new_count = detail.get("new_chapters", 0)
                        if new_count > 0:
                            logger.info(f"     - {series_title}: +{new_count} 话")
                
                return 0
            else:
                error_msg = result.get("error", "未知错误")
                logger.error(f"❌ 漫画收藏追更失败: {error_msg}")
                return 1
    
    except KeyboardInterrupt:
        logger.info("用户中断操作")
        return 130
    
    except Exception as e:
        logger.exception(f"❌ 执行过程中发生异常: {e}")
        return 1


if __name__ == "__main__":
    # 设置日志级别
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # 运行主函数并获取退出码
    exit_code = asyncio.run(main())
    sys.exit(exit_code)