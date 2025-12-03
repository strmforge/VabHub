"""
更新Transmission配置
将Transmission配置更新为指定的IP地址
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

# Transmission配置
TRANSMISSION_CONFIG = {
    "host": "192.168.51.105",
    "port": 9091,
    "username": "haishuai",
    "password": "China1987"
}

# qBittorrent配置
QBITTORRENT_CONFIG = {
    "host": "192.168.51.105",
    "port": 8080,
    "username": "admin",
    "password": "China1987"
}


async def update_transmission_config():
    """更新Transmission配置"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            settings = {
                "transmission_host": TRANSMISSION_CONFIG["host"],
                "transmission_port": TRANSMISSION_CONFIG["port"],
                "transmission_username": TRANSMISSION_CONFIG["username"],
                "transmission_password": TRANSMISSION_CONFIG["password"]
            }
            
            logger.info("更新Transmission配置...")
            logger.info(f"  主机: {TRANSMISSION_CONFIG['host']}")
            logger.info(f"  端口: {TRANSMISSION_CONFIG['port']}")
            logger.info(f"  用户名: {TRANSMISSION_CONFIG['username'] or '未设置'}")
            logger.info(f"  密码: {'已设置' if TRANSMISSION_CONFIG['password'] else '未设置'}")
            logger.info("")
            
            for key, value in settings.items():
                response = await client.put(
                    f"{BASE_URL}/settings/{key}",
                    json={"value": str(value)}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        logger.success(f"✓ {key} = {value}")
                    else:
                        logger.warning(f"✗ {key} 设置失败: {data.get('error_message', '未知错误')}")
                else:
                    logger.warning(f"✗ {key} 设置失败: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"更新Transmission配置失败: {e}")


async def update_qbittorrent_config():
    """更新qBittorrent配置"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            settings = {
                "qbittorrent_host": QBITTORRENT_CONFIG["host"],
                "qbittorrent_port": QBITTORRENT_CONFIG["port"],
                "qbittorrent_username": QBITTORRENT_CONFIG["username"],
                "qbittorrent_password": QBITTORRENT_CONFIG["password"]
            }
            
            logger.info("更新qBittorrent配置...")
            logger.info(f"  主机: {QBITTORRENT_CONFIG['host']}")
            logger.info(f"  端口: {QBITTORRENT_CONFIG['port']}")
            logger.info(f"  用户名: {QBITTORRENT_CONFIG['username'] or '未设置'}")
            logger.info(f"  密码: {'已设置' if QBITTORRENT_CONFIG['password'] else '未设置'}")
            logger.info("")
            
            for key, value in settings.items():
                response = await client.put(
                    f"{BASE_URL}/settings/{key}",
                    json={"value": str(value)}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        logger.success(f"✓ {key} = {value}")
                    else:
                        logger.warning(f"✗ {key} 设置失败: {data.get('error_message', '未知错误')}")
                else:
                    logger.warning(f"✗ {key} 设置失败: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"更新qBittorrent配置失败: {e}")


async def test_qbittorrent_connection():
    """测试qBittorrent连接"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            # 获取下载器实例列表
            response = await client.get(f"{BASE_URL}/dl/instances")
            if response.status_code == 200:
                response_data = response.json()
                # 处理统一响应格式
                if isinstance(response_data, dict):
                    if response_data.get("success") and "data" in response_data:
                        data = response_data["data"]
                        if isinstance(data, dict) and "instances" in data:
                            instances = data["instances"]
                        elif isinstance(data, list):
                            instances = data
                        else:
                            instances = []
                    else:
                        instances = response_data.get("data", [])
                elif isinstance(response_data, list):
                    instances = response_data
                else:
                    instances = []
                
                if not isinstance(instances, list):
                    logger.warning(f"下载器实例数据格式错误: {type(instances)}")
                    return
                
                # 测试qBittorrent连接
                for instance in instances:
                    if isinstance(instance, dict) and instance.get("type") == "qBittorrent":
                        instance_id = instance.get("id")
                        instance_name = instance.get("name", instance_id)
                        
                        logger.info(f"测试 qBittorrent ({instance_name}):")
                        
                        # 测试连接
                        test_response = await client.post(f"{BASE_URL}/dl/{instance_id}/test")
                        if test_response.status_code == 200:
                            test_data = test_response.json()
                            if test_data.get("success"):
                                logger.success(f"✓ qBittorrent 连接测试成功")
                                
                                # 获取统计信息
                                stats_response = await client.get(f"{BASE_URL}/dl/{instance_id}/stats")
                                if stats_response.status_code == 200:
                                    stats_data = stats_response.json()
                                    if stats_data.get("success"):
                                        stats = stats_data.get("data", {})
                                        logger.info(f"  总任务数: {stats.get('total', 0)}")
                                        logger.info(f"  下载中: {stats.get('downloading', 0)}")
                                        logger.info(f"  已完成: {stats.get('completed', 0)}")
                                        logger.info(f"  已暂停: {stats.get('paused', 0)}")
                            else:
                                error_msg = test_data.get("error_message", "未知错误")
                                logger.warning(f"✗ qBittorrent 连接测试失败: {error_msg}")
                        else:
                            logger.warning(f"✗ qBittorrent 连接测试失败: HTTP {test_response.status_code}")
    except Exception as e:
        logger.error(f"测试qBittorrent连接失败: {e}")


async def test_transmission_connection():
    """测试Transmission连接"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            # 获取下载器实例列表
            response = await client.get(f"{BASE_URL}/dl/instances")
            if response.status_code == 200:
                response_data = response.json()
                # 处理统一响应格式
                if isinstance(response_data, dict):
                    if response_data.get("success") and "data" in response_data:
                        data = response_data["data"]
                        if isinstance(data, dict) and "instances" in data:
                            instances = data["instances"]
                        elif isinstance(data, list):
                            instances = data
                        else:
                            instances = []
                    else:
                        instances = response_data.get("data", [])
                elif isinstance(response_data, list):
                    instances = response_data
                else:
                    instances = []
                
                if not isinstance(instances, list):
                    logger.warning(f"下载器实例数据格式错误: {type(instances)}")
                    return
                
                logger.info(f"找到 {len(instances)} 个下载器实例\n")
                
                # 测试Transmission连接
                for instance in instances:
                    if isinstance(instance, dict) and instance.get("type") == "Transmission":
                        instance_id = instance.get("id")
                        instance_name = instance.get("name", instance_id)
                        
                        logger.info(f"测试 Transmission ({instance_name}):")
                        
                        # 测试连接
                        test_response = await client.post(f"{BASE_URL}/dl/{instance_id}/test")
                        if test_response.status_code == 200:
                            test_data = test_response.json()
                            if test_data.get("success"):
                                logger.success(f"✓ Transmission 连接测试成功")
                                
                                # 获取统计信息
                                stats_response = await client.get(f"{BASE_URL}/dl/{instance_id}/stats")
                                if stats_response.status_code == 200:
                                    stats_data = stats_response.json()
                                    if stats_data.get("success"):
                                        stats = stats_data.get("data", {})
                                        logger.info(f"  总任务数: {stats.get('total', 0)}")
                                        logger.info(f"  下载中: {stats.get('downloading', 0)}")
                                        logger.info(f"  已完成: {stats.get('completed', 0)}")
                                        logger.info(f"  已暂停: {stats.get('paused', 0)}")
                            else:
                                error_msg = test_data.get("error_message", "未知错误")
                                logger.warning(f"✗ Transmission 连接测试失败: {error_msg}")
                        else:
                            logger.warning(f"✗ Transmission 连接测试失败: HTTP {test_response.status_code}")
    except Exception as e:
        logger.error(f"测试Transmission连接失败: {e}")


async def main():
    """主函数"""
    logger.info("="*60)
    logger.info("更新下载器配置")
    logger.info("="*60)
    logger.info("")
    
    # 更新Transmission配置
    await update_transmission_config()
    
    logger.info("")
    # 更新qBittorrent配置
    await update_qbittorrent_config()
    
    logger.info("")
    logger.info("="*60)
    logger.info("测试下载器连接")
    logger.info("="*60)
    logger.info("")
    
    # 测试qBittorrent连接
    await test_qbittorrent_connection()
    
    logger.info("")
    # 测试Transmission连接
    await test_transmission_connection()
    
    logger.info("")
    logger.info("="*60)
    logger.info("配置完成")
    logger.info("="*60)
    logger.info("")
    logger.info("提示：")
    logger.info("1. 如果连接失败，请检查：")
    logger.info("   - 下载器服务是否正在运行")
    logger.info("   - 网络连接是否正常")
    logger.info("   - 用户名和密码是否正确")
    logger.info("2. 配置更新后，可以运行测试脚本验证功能")


if __name__ == "__main__":
    asyncio.run(main())

