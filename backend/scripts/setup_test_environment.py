"""
测试环境配置脚本
配置测试用的下载器实例、API密钥等
"""

import asyncio
import httpx
from loguru import logger

BASE_URL = "http://localhost:8001/api"
TIMEOUT = 10.0

# 测试配置
TEST_CONFIG = {
    "qbittorrent": {
        "host": "localhost",
        "port": 8080,
        "username": "admin",
        "password": "adminadmin"
    },
    "transmission": {
        "host": "localhost",
        "port": 9091,
        "username": "",
        "password": ""
    },
    "tmdb_api_key": "fe29c50eb189bac40cb3abd33de5be96"
}


async def setup_downloader_settings(downloader: str, config: dict):
    """配置下载器设置"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # 设置下载器配置
            settings = {
                f"{downloader.lower()}_host": config["host"],
                f"{downloader.lower()}_port": config["port"],
                f"{downloader.lower()}_username": config["username"],
                f"{downloader.lower()}_password": config["password"]
            }
            
            for key, value in settings.items():
                response = await client.put(
                    f"{BASE_URL}/settings/{key}",
                    json={"value": str(value)}
                )
                if response.status_code == 200:
                    logger.info(f"✓ 设置 {key} = {value}")
                else:
                    logger.warning(f"✗ 设置 {key} 失败: {response.status_code}")
    except Exception as e:
        logger.error(f"配置下载器设置失败: {e}")


async def setup_tmdb_api_key(api_key: str):
    """配置TMDB API密钥"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.put(
                f"{BASE_URL}/settings/tmdb_api_key",
                json={"value": api_key}
            )
            if response.status_code == 200:
                logger.info("✓ TMDB API密钥已配置")
            else:
                logger.warning(f"✗ TMDB API密钥配置失败: {response.status_code}")
    except Exception as e:
        logger.error(f"配置TMDB API密钥失败: {e}")


async def test_downloader_connection(downloader: str):
    """测试下载器连接"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # 获取下载器实例列表
            response = await client.get(f"{BASE_URL}/dl/instances")
            if response.status_code == 200:
                response_data = response.json()
                # 处理统一响应格式
                if isinstance(response_data, dict):
                    if response_data.get("success") and "data" in response_data:
                        instances = response_data["data"]
                    else:
                        instances = response_data.get("data", [])
                elif isinstance(response_data, list):
                    instances = response_data
                else:
                    instances = []
                
                if not isinstance(instances, list):
                    logger.warning(f"下载器实例数据格式错误: {type(instances)}")
                    return
                
                logger.info(f"✓ 找到 {len(instances)} 个下载器实例")
                
                # 测试每个实例
                for instance in instances:
                    if isinstance(instance, dict) and instance.get("type") == downloader:
                        did = instance.get("id")
                        if did:
                            test_response = await client.post(f"{BASE_URL}/dl/{did}/test")
                            if test_response.status_code == 200:
                                logger.info(f"✓ {downloader} 连接测试成功 (ID: {did})")
                            else:
                                logger.warning(f"✗ {downloader} 连接测试失败 (ID: {did}, 状态码: {test_response.status_code})")
    except Exception as e:
        logger.error(f"测试下载器连接失败: {e}")


async def main():
    """主函数"""
    logger.info("开始配置测试环境...")
    
    # 配置下载器设置
    logger.info("\n配置下载器设置...")
    await setup_downloader_settings("qBittorrent", TEST_CONFIG["qbittorrent"])
    await setup_downloader_settings("Transmission", TEST_CONFIG["transmission"])
    
    # 配置TMDB API密钥
    logger.info("\n配置TMDB API密钥...")
    await setup_tmdb_api_key(TEST_CONFIG["tmdb_api_key"])
    
    # 测试下载器连接
    logger.info("\n测试下载器连接...")
    await test_downloader_connection("qBittorrent")
    await test_downloader_connection("Transmission")
    
    logger.info("\n测试环境配置完成！")
    logger.info("\n提示：")
    logger.info("1. 确保下载器服务正在运行")
    logger.info("2. 检查下载器配置是否正确")
    logger.info("3. 运行测试脚本验证功能")


if __name__ == "__main__":
    asyncio.run(main())

