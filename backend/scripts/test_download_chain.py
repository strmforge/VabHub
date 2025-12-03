"""
测试 DownloadChain 功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
backend_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.chain.download import DownloadChain
from loguru import logger


async def test_download_chain():
    """测试 DownloadChain 功能"""
    logger.info("="*50)
    logger.info("开始测试 DownloadChain")
    logger.info("="*50)
    
    chain = DownloadChain()
    
    # 测试1: 列出所有下载任务
    logger.info("\n测试1: 列出所有下载任务")
    try:
        downloads = await chain.list_downloads()
        logger.info(f"找到 {len(downloads)} 个下载任务")
        for download in downloads[:5]:  # 只显示前5个
            logger.info(f"  - {download.get('title')} - 状态: {download.get('status')}")
    except Exception as e:
        logger.error(f"测试1失败: {e}")
    
    # 测试2: 列出下载中的任务
    logger.info("\n测试2: 列出下载中的任务")
    try:
        downloads = await chain.list_downloads(status="downloading")
        logger.info(f"找到 {len(downloads)} 个下载中的任务")
    except Exception as e:
        logger.error(f"测试2失败: {e}")
    
    # 测试3: 列出已完成的任务
    logger.info("\n测试3: 列出已完成的任务")
    try:
        downloads = await chain.list_downloads(status="completed")
        logger.info(f"找到 {len(downloads)} 个已完成的任务")
    except Exception as e:
        logger.error(f"测试3失败: {e}")
    
    # 测试4: 获取下载详情（如果有下载任务）
    if downloads:
        download_id = downloads[0].get('id')
        if download_id:
            logger.info(f"\n测试4: 获取下载详情 (ID: {download_id})")
            try:
                download = await chain.get_download(download_id)
                if download:
                    logger.info(f"下载标题: {download.get('title')}")
                    logger.info(f"状态: {download.get('status')}")
                    logger.info(f"进度: {download.get('progress')}%")
                else:
                    logger.warning("下载任务不存在")
            except Exception as e:
                logger.error(f"测试4失败: {e}")
    
    logger.info("\n" + "="*50)
    logger.info("DownloadChain 测试完成")
    logger.info("="*50)


if __name__ == "__main__":
    asyncio.run(test_download_chain())

