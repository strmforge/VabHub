"""
115网盘用户信息测试脚本
使用已获取的access_token测试用户信息API
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

from app.core.cloud_storage.providers.cloud_115 import Cloud115Provider
from app.core.cloud_key_manager import get_key_manager
from loguru import logger
import aiohttp
import json


async def test_user_info():
    """测试115网盘用户信息API"""
    logger.info("="*60)
    logger.info("115网盘用户信息测试")
    logger.info("="*60)
    
    # 获取密钥
    key_manager = get_key_manager()
    keys = key_manager.get_115_keys()
    
    if not keys:
        logger.error("❌ 115网盘密钥未配置")
        return
    
    logger.info("✅ 密钥已加载")
    
    # 创建Provider
    provider = Cloud115Provider()
    
    # 初始化
    credentials = {
        "app_id": keys.get("app_id"),
        "app_key": keys.get("app_key"),
        "app_secret": keys.get("app_secret")
    }
    
    success = await provider.initialize(credentials)
    if not success:
        logger.error("❌ Provider初始化失败")
        return
    
    logger.info("✅ Provider初始化成功")
    
    # 检查是否已认证
    is_authenticated = await provider.is_authenticated()
    if not is_authenticated:
        logger.error("❌ 未认证，请先运行 test_115_qrcode.py 进行登录")
        return
    
    logger.info("✅ 已认证")
    logger.info(f"   Access Token: {provider.access_token[:20]}...")
    logger.info("")
    
    # 测试获取用户信息
    logger.info("测试获取用户信息...")
    await provider._get_user_info()
    
    if provider.user_id:
        logger.info("✅ 获取用户信息成功")
        logger.info(f"   User ID: {provider.user_id}")
        logger.info(f"   User Name: {provider.user_name}")
    else:
        logger.warning("⚠️  用户信息为空")
        
        # 尝试直接调用API查看响应
        logger.info("")
        logger.info("尝试直接调用API查看响应...")
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {provider.access_token}",
                "User-Agent": "W115Storage/2.0"
            }
            
            # 尝试不同的API端点
            endpoints = [
                "https://proapi.115.com/user/info",
                "https://webapi.115.com/user/info",
                "https://api.115.com/user/info",
            ]
            
            for endpoint in endpoints:
                logger.info(f"尝试端点: {endpoint}")
                try:
                    async with session.get(endpoint, headers=headers) as response:
                        response_text = await response.text()
                        logger.info(f"   状态码: {response.status}")
                        logger.info(f"   响应类型: {response.headers.get('Content-Type', 'unknown')}")
                        logger.info(f"   响应内容: {response_text[:500]}")
                        
                        if response.status == 200:
                            try:
                                result = json.loads(response_text)
                                logger.info(f"   JSON解析成功: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
                            except:
                                logger.warning("   响应不是JSON格式")
                except Exception as e:
                    logger.error(f"   请求失败: {e}")
                
                logger.info("")
    
    await provider.close()
    
    logger.info("="*60)
    logger.info("测试完成")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(test_user_info())

