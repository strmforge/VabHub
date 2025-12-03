"""
检查下载任务状态
查看任务详情，包括下载器hash等信息
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
TIMEOUT = 10.0


async def check_downloads():
    """检查下载任务状态"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            response = await client.get(f"{BASE_URL}/downloads/")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    downloads = data.get("data", {}).get("items", []) or data.get("data", [])
                    
                    logger.info(f"找到 {len(downloads)} 个下载任务\n")
                    
                    for i, download in enumerate(downloads[:10], 1):  # 只显示前10个
                        task_id = download.get("id") or download.get("task_id")
                        title = download.get("title", "未知")
                        status = download.get("status", "未知")
                        downloader = download.get("downloader", "未知")
                        downloader_hash = download.get("downloader_hash", "")
                        
                        logger.info(f"{i}. {title}")
                        logger.info(f"   ID: {task_id}")
                        logger.info(f"   状态: {status}")
                        logger.info(f"   下载器: {downloader}")
                        logger.info(f"   Hash: {downloader_hash[:30] if downloader_hash else 'None'}...")
                        logger.info("")
                    
                    return downloads
                else:
                    logger.warning(f"获取下载列表失败: {data.get('error_message', '未知错误')}")
            else:
                logger.warning(f"获取下载列表失败: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"获取下载列表异常: {e}")
    
    return []


async def check_task_detail(task_id: str):
    """检查任务详情"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            response = await client.get(f"{BASE_URL}/downloads/{task_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    task = data.get("data", {})
                    logger.info(f"任务详情: {task_id}")
                    logger.info(f"  标题: {task.get('title', '未知')}")
                    logger.info(f"  状态: {task.get('status', '未知')}")
                    logger.info(f"  下载器: {task.get('downloader', '未知')}")
                    logger.info(f"  Hash: {task.get('downloader_hash', 'None')}")
                    logger.info(f"  进度: {task.get('progress', 0)}%")
                    return task
                else:
                    logger.warning(f"获取任务详情失败: {data.get('error_message', '未知错误')}")
            else:
                logger.warning(f"获取任务详情失败: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"获取任务详情异常: {e}")
    
    return None


async def main():
    """主函数"""
    logger.info("="*60)
    logger.info("检查下载任务状态")
    logger.info("="*60)
    logger.info("")
    
    # 检查所有下载任务
    downloads = await check_downloads()
    
    # 如果有任务ID文件，检查这些任务
    task_id_file = Path(__file__).parent / "test_task_ids.txt"
    if task_id_file.exists():
        logger.info("\n检查测试任务详情:")
        logger.info("="*60)
        try:
            with open(task_id_file, "r", encoding="utf-8") as f:
                task_ids = [line.strip() for line in f if line.strip()]
            
            for task_id in task_ids:
                await check_task_detail(task_id)
                logger.info("")
        except Exception as e:
            logger.error(f"读取任务ID文件失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())

