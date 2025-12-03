"""
测试API端点
"""

import asyncio
import sys
from pathlib import Path
import httpx

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger

from scripts.api_test_config import API_BASE_URL, API_PREFIX as CONFIG_API_PREFIX

# API基础URL
PREFIX = CONFIG_API_PREFIX.rstrip("/")
BASE_URL = f"{API_BASE_URL}{PREFIX}" if PREFIX else API_BASE_URL


async def test_media_server_api():
    """测试媒体服务器API"""
    logger.info("=" * 60)
    logger.info("测试媒体服务器API")
    logger.info("=" * 60)
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 测试1: 获取媒体服务器列表
        logger.info("\n测试1: GET /media-servers/")
        try:
            response = await client.get("/media-servers/")
            logger.info(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 获取媒体服务器列表成功: {data.get('message')}")
                logger.info(f"   服务器数量: {len(data.get('data', []))}")
            else:
                logger.error(f"❌ 获取媒体服务器列表失败: {response.text}")
        except Exception as e:
            logger.error(f"❌ 请求失败: {e}")
        
        # 测试2: 创建媒体服务器
        logger.info("\n测试2: POST /media-servers/")
        try:
            server_data = {
                "name": "测试Jellyfin服务器",
                "server_type": "jellyfin",
                "url": "http://localhost:8096",
                "api_key": "test_api_key",
                "user_id": "test_user_id",
                "enabled": False
            }
            response = await client.post("/media-servers/", json=server_data)
            logger.info(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 创建媒体服务器成功: {data.get('message')}")
                server_id = data.get('data', {}).get('id')
                logger.info(f"   服务器ID: {server_id}")
            else:
                logger.error(f"❌ 创建媒体服务器失败: {response.text}")
                server_id = None
        except Exception as e:
            logger.error(f"❌ 请求失败: {e}")
            server_id = None
        
        if server_id:
            # 测试3: 获取媒体服务器详情
            logger.info(f"\n测试3: GET /media-servers/{server_id}")
            try:
                response = await client.get(f"/media-servers/{server_id}")
                logger.info(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ 获取媒体服务器详情成功: {data.get('message')}")
                else:
                    logger.error(f"❌ 获取媒体服务器详情失败: {response.text}")
            except Exception as e:
                logger.error(f"❌ 请求失败: {e}")
            
            # 测试4: 更新媒体服务器
            logger.info(f"\n测试4: PUT /media-servers/{server_id}")
            try:
                update_data = {
                    "name": "测试Jellyfin服务器（已更新）"
                }
                response = await client.put(f"/media-servers/{server_id}", json=update_data)
                logger.info(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ 更新媒体服务器成功: {data.get('message')}")
                else:
                    logger.error(f"❌ 更新媒体服务器失败: {response.text}")
            except Exception as e:
                logger.error(f"❌ 请求失败: {e}")
            
            # 测试5: 删除媒体服务器
            logger.info(f"\n测试5: DELETE /media-servers/{server_id}")
            try:
                response = await client.delete(f"/media-servers/{server_id}")
                logger.info(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ 删除媒体服务器成功: {data.get('message')}")
                else:
                    logger.error(f"❌ 删除媒体服务器失败: {response.text}")
            except Exception as e:
                logger.error(f"❌ 请求失败: {e}")


async def test_scheduler_api():
    """测试调度器API"""
    logger.info("=" * 60)
    logger.info("测试调度器API")
    logger.info("=" * 60)
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 测试1: 获取任务列表
        logger.info("\n测试1: GET /scheduler/jobs")
        try:
            response = await client.get("/scheduler/jobs")
            logger.info(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 获取任务列表成功: {data.get('message')}")
                jobs = data.get('data', [])
                logger.info(f"   任务数量: {len(jobs)}")
                for job in jobs[:5]:  # 只显示前5个
                    logger.info(f"   - {job.get('name')} ({job.get('id')}): {job.get('status')}")
            else:
                logger.error(f"❌ 获取任务列表失败: {response.text}")
        except Exception as e:
            logger.error(f"❌ 请求失败: {e}")
        
        # 测试2: 获取统计信息
        logger.info("\n测试2: GET /scheduler/statistics")
        try:
            response = await client.get("/scheduler/statistics")
            logger.info(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 获取统计信息成功: {data.get('message')}")
                stats = data.get('data', {})
                logger.info(f"   总任务数: {stats.get('total_tasks', 0)}")
                logger.info(f"   启用任务数: {stats.get('enabled_tasks', 0)}")
                logger.info(f"   总体成功率: {stats.get('overall_success_rate', 0):.2f}%")
            else:
                logger.error(f"❌ 获取统计信息失败: {response.text}")
        except Exception as e:
            logger.error(f"❌ 请求失败: {e}")
        
        # 测试3: 同步任务
        logger.info("\n测试3: POST /scheduler/sync")
        try:
            response = await client.post("/scheduler/sync")
            logger.info(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 同步任务成功: {data.get('message')}")
            else:
                logger.error(f"❌ 同步任务失败: {response.text}")
        except Exception as e:
            logger.error(f"❌ 请求失败: {e}")


async def main():
    """主测试函数"""
    logger.info("开始测试API端点...")
    logger.info(f"注意: 需要确保后端服务正在运行 ({API_BASE_URL})")
    
    # 测试媒体服务器API
    await test_media_server_api()
    
    # 测试调度器API
    await test_scheduler_api()
    
    logger.info("=" * 60)
    logger.info("所有API测试完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

