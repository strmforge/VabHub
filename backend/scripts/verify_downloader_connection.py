"""
验证下载器连接
确保下载器服务正在运行且配置正确
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


async def check_backend_service():
    """检查后端服务"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL.replace('/api', '')}/health")
            if response.status_code == 200:
                logger.success("✓ 后端服务运行正常")
                return True
            else:
                logger.error(f"✗ 后端服务响应异常: HTTP {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"✗ 无法连接到后端服务: {e}")
        logger.info("请先启动后端服务: cd VabHub/backend && python main.py")
        return False


async def get_downloader_instances():
    """获取下载器实例列表"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{BASE_URL}/dl/instances")
            
            if response.status_code == 200:
                response_data = response.json()
                # 处理统一响应格式
                if isinstance(response_data, dict):
                    if response_data.get("success") and "data" in response_data:
                        data = response_data["data"]
                        # 检查是否是嵌套的instances
                        if isinstance(data, dict) and "instances" in data:
                            instances = data["instances"]
                        elif isinstance(data, list):
                            instances = data
                        else:
                            instances = []
                    else:
                        instances = response_data.get("data", [])
                        if isinstance(instances, dict) and "instances" in instances:
                            instances = instances["instances"]
                elif isinstance(response_data, list):
                    instances = response_data
                else:
                    instances = []
                
                if isinstance(instances, list):
                    return instances
                else:
                    logger.warning(f"下载器实例数据格式错误: {type(instances)}")
                    logger.debug(f"响应数据: {response_data}")
                    return []
            else:
                logger.warning(f"获取下载器实例失败: HTTP {response.status_code}")
                return []
    except Exception as e:
        logger.error(f"获取下载器实例异常: {e}")
        return []


async def test_downloader_connection(instance_id: str, instance_type: str):
    """测试下载器连接"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(f"{BASE_URL}/dl/{instance_id}/test")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.success(f"✓ {instance_type} 连接测试成功 (ID: {instance_id})")
                    return True
                else:
                    error_msg = data.get("error_message", "未知错误")
                    logger.warning(f"✗ {instance_type} 连接测试失败 (ID: {instance_id}): {error_msg}")
                    return False
            else:
                logger.warning(f"✗ {instance_type} 连接测试失败 (ID: {instance_id}): HTTP {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"✗ {instance_type} 连接测试异常 (ID: {instance_id}): {e}")
        return False


async def get_downloader_stats(instance_id: str, instance_type: str):
    """获取下载器统计信息"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{BASE_URL}/dl/{instance_id}/stats")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    stats = data.get("data", {})
                    logger.info(f"  - 总任务数: {stats.get('total', 0)}")
                    logger.info(f"  - 下载中: {stats.get('downloading', 0)}")
                    logger.info(f"  - 已完成: {stats.get('completed', 0)}")
                    logger.info(f"  - 已暂停: {stats.get('paused', 0)}")
                    return True
                else:
                    logger.warning(f"  - 获取统计信息失败: {data.get('error_message', '未知错误')}")
                    return False
            else:
                logger.warning(f"  - 获取统计信息失败: HTTP {response.status_code}")
                return False
    except Exception as e:
        logger.warning(f"  - 获取统计信息异常: {e}")
        return False


async def check_downloader_settings():
    """检查下载器配置"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # 检查qBittorrent配置
            qb_settings = {}
            for key in ["qbittorrent_host", "qbittorrent_port", "qbittorrent_username", "qbittorrent_password"]:
                response = await client.get(f"{BASE_URL}/settings/{key}")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        qb_settings[key] = data.get("data", {}).get("value", "")
            
            logger.info("\nqBittorrent 配置:")
            logger.info(f"  - 主机: {qb_settings.get('qbittorrent_host', '未配置')}")
            logger.info(f"  - 端口: {qb_settings.get('qbittorrent_port', '未配置')}")
            logger.info(f"  - 用户名: {qb_settings.get('qbittorrent_username', '未配置')}")
            logger.info(f"  - 密码: {'已配置' if qb_settings.get('qbittorrent_password') else '未配置'}")
            
            # 检查Transmission配置
            tr_settings = {}
            for key in ["transmission_host", "transmission_port", "transmission_username", "transmission_password"]:
                response = await client.get(f"{BASE_URL}/settings/{key}")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        tr_settings[key] = data.get("data", {}).get("value", "")
            
            logger.info("\nTransmission 配置:")
            logger.info(f"  - 主机: {tr_settings.get('transmission_host', '未配置')}")
            logger.info(f"  - 端口: {tr_settings.get('transmission_port', '未配置')}")
            logger.info(f"  - 用户名: {tr_settings.get('transmission_username', '未配置')}")
            logger.info(f"  - 密码: {'已配置' if tr_settings.get('transmission_password') else '未配置'}")
            
    except Exception as e:
        logger.warning(f"检查下载器配置异常: {e}")


async def main():
    """主函数"""
    logger.info("="*60)
    logger.info("验证下载器连接")
    logger.info("="*60)
    
    # 1. 检查后端服务
    logger.info("\n1. 检查后端服务...")
    if not await check_backend_service():
        return
    
    # 2. 检查下载器配置
    logger.info("\n2. 检查下载器配置...")
    await check_downloader_settings()
    
    # 3. 获取下载器实例
    logger.info("\n3. 获取下载器实例...")
    instances = await get_downloader_instances()
    
    if not instances:
        logger.warning("未找到任何下载器实例")
        logger.info("\n可能的原因：")
        logger.info("1. 下载器服务未运行")
        logger.info("2. 下载器配置不正确")
        logger.info("3. 后端无法连接到下载器")
        logger.info("\n建议：")
        logger.info("1. 运行配置脚本: python VabHub/backend/scripts/setup_test_environment.py")
        logger.info("2. 检查下载器服务是否正在运行")
        logger.info("3. 检查下载器配置是否正确")
        return
    
    logger.info(f"找到 {len(instances)} 个下载器实例\n")
    
    # 4. 测试每个下载器连接
    logger.info("4. 测试下载器连接...")
    success_count = 0
    
    for instance in instances:
        if isinstance(instance, dict):
            instance_id = instance.get("id")
            instance_type = instance.get("type", "Unknown")
            instance_name = instance.get("name", instance_id)
            
            logger.info(f"\n测试 {instance_type} ({instance_name}):")
            
            # 测试连接
            if await test_downloader_connection(instance_id, instance_type):
                success_count += 1
                # 获取统计信息
                await get_downloader_stats(instance_id, instance_type)
    
    # 总结
    logger.info("\n" + "="*60)
    logger.info("验证结果")
    logger.info("="*60)
    logger.info(f"总实例数: {len(instances)}")
    logger.info(f"连接成功: {success_count}")
    logger.info(f"连接失败: {len(instances) - success_count}")
    
    if success_count == len(instances):
        logger.success("\n✓ 所有下载器连接正常")
    elif success_count > 0:
        logger.warning(f"\n⚠ 部分下载器连接失败 ({len(instances) - success_count} 个)")
    else:
        logger.error("\n✗ 所有下载器连接失败")
        logger.info("\n请检查：")
        logger.info("1. 下载器服务是否正在运行")
        logger.info("2. 下载器配置是否正确（主机、端口、用户名、密码）")
        logger.info("3. 网络连接是否正常")
        logger.info("4. 防火墙设置是否阻止了连接")


if __name__ == "__main__":
    asyncio.run(main())

