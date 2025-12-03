"""
手动测试API端点脚本
用于测试媒体服务器和调度器监控的API端点
"""

import asyncio
import httpx
from loguru import logger
import json

from scripts.api_test_config import API_BASE_URL, API_PREFIX as CONFIG_API_PREFIX, api_url


BASE_URL = API_BASE_URL
API_PREFIX = CONFIG_API_PREFIX


async def test_media_server_api():
    """测试媒体服务器API"""
    logger.info("=" * 60)
    logger.info("测试媒体服务器API")
    logger.info("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 测试1: 获取服务器列表
        logger.info("\n[测试1] GET /media-servers - 获取服务器列表")
        try:
            response = await client.get(api_url("/media-servers/"))
            logger.info(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                logger.error(f"❌ 失败: {response.text}")
        except Exception as e:
            logger.error(f"❌ 错误: {e}")
        
        # 测试2: 创建媒体服务器
        logger.info("\n[测试2] POST /media-servers - 创建媒体服务器")
        try:
            server_data = {
                "name": "测试Jellyfin服务器",
                "server_type": "jellyfin",
                "url": "http://localhost:8096",
                "api_key": "test_api_key",
                "user_id": "test_user_id",
                "enabled": False
            }
            response = await client.post(
                api_url("/media-servers/"),
                json=server_data
            )
            logger.info(f"状态码: {response.status_code}")
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"✅ 成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
                server_id = data.get("data", {}).get("id") if isinstance(data.get("data"), dict) else None
                if not server_id and isinstance(data, dict) and "id" in data:
                    server_id = data["id"]
                return server_id
            else:
                logger.error(f"❌ 失败: {response.text}")
        except Exception as e:
            logger.error(f"❌ 错误: {e}")
        
        server_id = None
        if 'server_id' in locals():
            server_id = locals()['server_id']
        
        if server_id:
            # 测试3: 获取服务器详情
            logger.info(f"\n[测试3] GET /media-servers/{server_id} - 获取服务器详情")
            try:
                response = await client.get(api_url(f"/media-servers/{server_id}"))
                logger.info(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ 成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
                else:
                    logger.error(f"❌ 失败: {response.text}")
            except Exception as e:
                logger.error(f"❌ 错误: {e}")
            
            # 测试4: 更新服务器
            logger.info(f"\n[测试4] PUT /media-servers/{server_id} - 更新服务器")
            try:
                update_data = {
                    "name": "测试Jellyfin服务器（已更新）"
                }
                response = await client.put(
                    api_url(f"/media-servers/{server_id}"),
                    json=update_data
                )
                logger.info(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ 成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
                else:
                    logger.error(f"❌ 失败: {response.text}")
            except Exception as e:
                logger.error(f"❌ 错误: {e}")
            
            # 测试5: 删除服务器
            logger.info(f"\n[测试5] DELETE /media-servers/{server_id} - 删除服务器")
            try:
                response = await client.delete(api_url(f"/media-servers/{server_id}"))
                logger.info(f"状态码: {response.status_code}")
                if response.status_code in [200, 204]:
                    logger.info("✅ 删除成功")
                else:
                    logger.error(f"❌ 失败: {response.text}")
            except Exception as e:
                logger.error(f"❌ 错误: {e}")
        
        logger.info("\n✅ 媒体服务器API测试完成")


async def test_scheduler_api():
    """测试调度器API"""
    logger.info("\n" + "=" * 60)
    logger.info("测试调度器API")
    logger.info("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 测试1: 获取任务列表
        logger.info("\n[测试1] GET /scheduler/jobs - 获取任务列表")
        try:
            response = await client.get(api_url("/scheduler/jobs"))
            logger.info(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                logger.error(f"❌ 失败: {response.text}")
        except Exception as e:
            logger.error(f"❌ 错误: {e}")
        
        # 测试2: 获取统计信息
        logger.info("\n[测试2] GET /scheduler/statistics - 获取统计信息")
        try:
            response = await client.get(api_url("/scheduler/statistics"))
            logger.info(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                logger.error(f"❌ 失败: {response.text}")
        except Exception as e:
            logger.error(f"❌ 错误: {e}")
        
        # 测试3: 同步任务
        logger.info("\n[测试3] POST /scheduler/sync - 同步任务")
        try:
            response = await client.post(api_url("/scheduler/sync"))
            logger.info(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                logger.error(f"❌ 失败: {response.text}")
        except Exception as e:
            logger.error(f"❌ 错误: {e}")
        
        logger.info("\n✅ 调度器API测试完成")


async def test_health_check():
    """测试健康检查"""
    logger.info("\n" + "=" * 60)
    logger.info("测试健康检查")
    logger.info("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            logger.info(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ 健康检查成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                logger.error(f"❌ 健康检查失败: {response.text}")
        except Exception as e:
            logger.error(f"❌ 错误: {e}")


async def main():
    """主测试函数"""
    logger.info("开始API端点测试...")
    logger.info(f"后端服务地址: {BASE_URL}")
    logger.info("")
    
    # 测试健康检查
    await test_health_check()
    
    # 测试媒体服务器API
    await test_media_server_api()
    
    # 测试调度器API
    await test_scheduler_api()
    
    logger.info("\n" + "=" * 60)
    logger.info("所有API测试完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

