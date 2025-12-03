"""
从下载器获取真实任务
从Transmission获取现有的真实下载任务，用于测试
"""

import asyncio
import httpx
import sys
from pathlib import Path
from loguru import logger

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

BASE_URL = "http://localhost:8001/api"
TIMEOUT = 30.0


async def get_transmission_torrents():
    """从Transmission获取真实任务"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            # 获取Transmission统计信息
            response = await client.get(f"{BASE_URL}/dl/transmission/stats")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    stats = data.get("data", {})
                    logger.info(f"Transmission统计: 总任务数={stats.get('total', 0)}, 下载中={stats.get('downloading', 0)}")
            
            # 尝试获取Transmission的任务列表（如果API支持）
            # 注意：这需要根据实际的API端点调整
            logger.info("\n提示：")
            logger.info("1. 如果Transmission中有正在下载的任务，它们应该已经在数据库中")
            logger.info("2. 检查下载列表，找到有downloader_hash的任务")
            logger.info("3. 使用这些任务ID进行测试")
            
    except Exception as e:
        logger.error(f"获取Transmission任务异常: {e}")


async def find_tasks_with_hash():
    """查找有downloader_hash的任务"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            response = await client.get(f"{BASE_URL}/downloads/")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    downloads = data.get("data", {}).get("items", []) or data.get("data", [])
                    
                    tasks_with_hash = []
                    for download in downloads:
                        task_id = download.get("id") or download.get("task_id")
                        downloader_hash = download.get("downloader_hash")
                        title = download.get("title", "未知")
                        status = download.get("status", "未知")
                        downloader = download.get("downloader", "未知")
                        
                        if downloader_hash:
                            tasks_with_hash.append({
                                "id": task_id,
                                "title": title,
                                "status": status,
                                "downloader": downloader,
                                "hash": downloader_hash
                            })
                    
                    if tasks_with_hash:
                        logger.info(f"\n找到 {len(tasks_with_hash)} 个有hash的任务:")
                        logger.info("="*60)
                        
                        task_ids = []
                        for i, task in enumerate(tasks_with_hash[:5], 1):  # 只显示前5个
                            logger.info(f"{i}. {task['title']}")
                            logger.info(f"   ID: {task['id']}")
                            logger.info(f"   状态: {task['status']}")
                            logger.info(f"   下载器: {task['downloader']}")
                            logger.info(f"   Hash: {task['hash'][:40]}...")
                            logger.info("")
                            task_ids.append(task['id'])
                        
                        # 保存到文件
                        if task_ids:
                            output_file = Path(__file__).parent / "test_task_ids.txt"
                            with open(output_file, "w", encoding="utf-8") as f:
                                for task_id in task_ids:
                                    f.write(f"{task_id}\n")
                            logger.info(f"任务ID已保存到: {output_file}")
                            logger.info("\n现在可以运行测试脚本:")
                            logger.info("python VabHub/backend/scripts/test_download_features.py")
                    else:
                        logger.warning("\n未找到有downloader_hash的任务")
                        logger.info("\n可能的原因：")
                        logger.info("1. 所有任务都创建失败")
                        logger.info("2. 下载器中没有正在下载的任务")
                        logger.info("3. 任务还没有同步到数据库")
                        logger.info("\n建议：")
                        logger.info("1. 在下载器中手动添加一个任务")
                        logger.info("2. 等待任务同步到数据库")
                        logger.info("3. 或者使用有效的磁力链接创建新任务")
                    
                    return tasks_with_hash
    except Exception as e:
        logger.error(f"查找任务异常: {e}")
    
    return []


async def main():
    """主函数"""
    logger.info("="*60)
    logger.info("从下载器获取真实任务")
    logger.info("="*60)
    logger.info("")
    
    # 查找有hash的任务
    tasks = await find_tasks_with_hash()
    
    if not tasks:
        # 尝试从Transmission获取
        await get_transmission_torrents()


if __name__ == "__main__":
    asyncio.run(main())

