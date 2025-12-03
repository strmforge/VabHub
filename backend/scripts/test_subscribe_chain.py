"""
测试 SubscribeChain 功能
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

from app.chain.subscribe import SubscribeChain
from loguru import logger


async def test_subscribe_chain():
    """测试 SubscribeChain 功能"""
    logger.info("="*50)
    logger.info("开始测试 SubscribeChain")
    logger.info("="*50)
    
    chain = SubscribeChain()
    
    # 测试1: 列出所有订阅
    logger.info("\n测试1: 列出所有订阅")
    try:
        subscriptions = await chain.list_subscriptions()
        logger.info(f"找到 {len(subscriptions)} 个订阅")
        for sub in subscriptions[:5]:  # 只显示前5个
            logger.info(f"  - {sub['title']} ({sub['media_type']}) - 状态: {sub['status']}")
    except Exception as e:
        logger.error(f"测试1失败: {e}")
    
    # 测试2: 列出电影订阅
    logger.info("\n测试2: 列出电影订阅")
    try:
        subscriptions = await chain.list_subscriptions(media_type="movie")
        logger.info(f"找到 {len(subscriptions)} 个电影订阅")
    except Exception as e:
        logger.error(f"测试2失败: {e}")
    
    # 测试3: 列出活跃订阅
    logger.info("\n测试3: 列出活跃订阅")
    try:
        subscriptions = await chain.list_subscriptions(status="active")
        logger.info(f"找到 {len(subscriptions)} 个活跃订阅")
    except Exception as e:
        logger.error(f"测试3失败: {e}")
    
    # 测试4: 获取订阅详情（如果有订阅）
    if subscriptions:
        subscription_id = subscriptions[0]['id']
        logger.info(f"\n测试4: 获取订阅详情 (ID: {subscription_id})")
        try:
            subscription = await chain.get_subscription(subscription_id)
            if subscription:
                logger.info(f"订阅标题: {subscription['title']}")
                logger.info(f"媒体类型: {subscription['media_type']}")
                logger.info(f"状态: {subscription['status']}")
            else:
                logger.warning("订阅不存在")
        except Exception as e:
            logger.error(f"测试4失败: {e}")
    
    logger.info("\n" + "="*50)
    logger.info("SubscribeChain 测试完成")
    logger.info("="*50)


if __name__ == "__main__":
    asyncio.run(test_subscribe_chain())
