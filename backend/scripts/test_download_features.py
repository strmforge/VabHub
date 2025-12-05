"""
测试下载管理新功能
包括批量操作、队列管理、速度限制
"""

import asyncio
import httpx
from pathlib import Path
from loguru import logger

BASE_URL = "http://localhost:8001/api"
TIMEOUT = 10.0

# 测试数据 - 优先使用真实任务ID
TEST_TASK_IDS = []

# 尝试从文件加载真实任务ID
def load_test_task_ids():
    """从文件加载测试任务ID"""
    global TEST_TASK_IDS
    task_id_file = Path(__file__).parent / "test_task_ids.txt"
    if task_id_file.exists():
        try:
            with open(task_id_file, "r", encoding="utf-8") as f:
                TEST_TASK_IDS = [line.strip() for line in f if line.strip()]
            logger.info(f"从文件加载了 {len(TEST_TASK_IDS)} 个真实任务ID")
        except Exception as e:
            logger.warning(f"加载任务ID文件失败: {e}")
    
    # 如果没有真实任务ID，使用测试ID
    if not TEST_TASK_IDS:
        TEST_TASK_IDS = ["test-task-1", "test-task-2", "test-task-3"]
        logger.warning("使用测试任务ID（可能不存在）")

# 加载任务ID
load_test_task_ids()


async def test_batch_operations():
    """测试批量操作"""
    logger.info("="*60)
    logger.info("测试批量操作功能")
    logger.info("="*60)
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # 测试批量暂停
        logger.info("\n1. 测试批量暂停...")
        try:
            response = await client.post(
                f"{BASE_URL}/downloads/batch/pause",
                json={"task_ids": TEST_TASK_IDS}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.success(f"✓ 批量暂停成功: {data.get('message', '')}")
                else:
                    logger.warning(f"✗ 批量暂停失败: {data.get('error_message', '')}")
            else:
                logger.warning(f"✗ 批量暂停失败: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"✗ 批量暂停异常: {e}")
        
        # 测试批量恢复
        logger.info("\n2. 测试批量恢复...")
        try:
            response = await client.post(
                f"{BASE_URL}/downloads/batch/resume",
                json={"task_ids": TEST_TASK_IDS}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.success(f"✓ 批量恢复成功: {data.get('message', '')}")
                else:
                    logger.warning(f"✗ 批量恢复失败: {data.get('error_message', '')}")
            else:
                logger.warning(f"✗ 批量恢复失败: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"✗ 批量恢复异常: {e}")
        
        # 测试批量删除（不删除文件）
        logger.info("\n3. 测试批量删除（不删除文件）...")
        try:
            response = await client.post(
                f"{BASE_URL}/downloads/batch/delete",
                json={"task_ids": TEST_TASK_IDS, "delete_files": False}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.success(f"✓ 批量删除成功: {data.get('message', '')}")
                else:
                    logger.warning(f"✗ 批量删除失败: {data.get('error_message', '')}")
            else:
                logger.warning(f"✗ 批量删除失败: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"✗ 批量删除异常: {e}")


async def test_queue_management():
    """测试队列管理"""
    logger.info("\n" + "="*60)
    logger.info("测试队列管理功能")
    logger.info("="*60)
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        test_task_id = TEST_TASK_IDS[0]
        
        # 测试队列上移
        logger.info("\n1. 测试队列上移...")
        try:
            response = await client.post(f"{BASE_URL}/downloads/{test_task_id}/queue/up")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.success(f"✓ 队列上移成功: {data.get('message', '')}")
                else:
                    logger.warning(f"✗ 队列上移失败: {data.get('error_message', '')}")
            else:
                logger.warning(f"✗ 队列上移失败: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"✗ 队列上移异常: {e}")
        
        # 测试队列下移
        logger.info("\n2. 测试队列下移...")
        try:
            response = await client.post(f"{BASE_URL}/downloads/{test_task_id}/queue/down")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.success(f"✓ 队列下移成功: {data.get('message', '')}")
                else:
                    logger.warning(f"✗ 队列下移失败: {data.get('error_message', '')}")
            else:
                logger.warning(f"✗ 队列下移失败: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"✗ 队列下移异常: {e}")
        
        # 测试队列置顶
        logger.info("\n3. 测试队列置顶...")
        try:
            response = await client.post(f"{BASE_URL}/downloads/{test_task_id}/queue/top")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.success(f"✓ 队列置顶成功: {data.get('message', '')}")
                else:
                    logger.warning(f"✗ 队列置顶失败: {data.get('error_message', '')}")
            else:
                logger.warning(f"✗ 队列置顶失败: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"✗ 队列置顶异常: {e}")


async def test_speed_limits():
    """测试速度限制"""
    logger.info("\n" + "="*60)
    logger.info("测试速度限制功能")
    logger.info("="*60)
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # 测试设置全局速度限制
        logger.info("\n1. 测试设置全局速度限制（qBittorrent）...")
        try:
            response = await client.put(
                f"{BASE_URL}/downloads/speed-limit/global?downloader=qBittorrent",
                json={"download_limit": 10.0, "upload_limit": 5.0}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.success(f"✓ 设置全局速度限制成功: {data.get('message', '')}")
                else:
                    logger.warning(f"✗ 设置全局速度限制失败: {data.get('error_message', '')}")
            else:
                logger.warning(f"✗ 设置全局速度限制失败: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"✗ 设置全局速度限制异常: {e}")
        
        # 测试获取全局速度限制
        logger.info("\n2. 测试获取全局速度限制（qBittorrent）...")
        try:
            response = await client.get(
                f"{BASE_URL}/downloads/speed-limit/global?downloader=qBittorrent"
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    limits = data.get("data", {})
                    logger.success(f"✓ 获取全局速度限制成功: 下载={limits.get('download_limit')}MB/s, 上传={limits.get('upload_limit')}MB/s")
                else:
                    logger.warning(f"✗ 获取全局速度限制失败: {data.get('error_message', '')}")
            else:
                logger.warning(f"✗ 获取全局速度限制失败: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"✗ 获取全局速度限制异常: {e}")
        
        # 测试设置任务速度限制
        logger.info("\n3. 测试设置任务速度限制...")
        try:
            test_task_id = TEST_TASK_IDS[0]
            response = await client.put(
                f"{BASE_URL}/downloads/{test_task_id}/speed-limit",
                json={"download_limit": 5.0, "upload_limit": 2.0}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.success(f"✓ 设置任务速度限制成功: {data.get('message', '')}")
                else:
                    logger.warning(f"✗ 设置任务速度限制失败: {data.get('error_message', '')}")
            else:
                logger.warning(f"✗ 设置任务速度限制失败: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"✗ 设置任务速度限制异常: {e}")


async def main():
    """主函数"""
    logger.info("开始测试下载管理新功能...")
    logger.info(f"测试URL: {BASE_URL}")
    logger.info(f"测试任务ID: {TEST_TASK_IDS}")
    
    # 测试批量操作
    await test_batch_operations()
    
    # 测试队列管理
    await test_queue_management()
    
    # 测试速度限制
    await test_speed_limits()
    
    logger.info("\n" + "="*60)
    logger.info("测试完成！")
    logger.info("="*60)
    logger.info("\n提示：")
    logger.info("1. 如果某些测试失败，可能是因为测试任务不存在")
    logger.info("2. 确保下载器服务正在运行")
    logger.info("3. 检查下载器配置是否正确")


if __name__ == "__main__":
    asyncio.run(main())

