"""
测试 StorageChain 功能
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

from app.chain.storage import StorageChain
from loguru import logger


async def test_storage_chain():
    """测试 StorageChain 功能"""
    logger.info("="*50)
    logger.info("开始测试 StorageChain")
    logger.info("="*50)
    
    chain = StorageChain()
    
    # 测试1: 列出所有存储
    logger.info("\n测试1: 列出所有存储")
    try:
        storages = await chain.list_storages()
        logger.info(f"找到 {len(storages)} 个存储配置")
        for storage in storages:
            logger.info(f"  - {storage['name']} ({storage['provider']}) - ID: {storage['id']}")
    except Exception as e:
        logger.error(f"测试1失败: {e}")
    
    # 测试2: 获取存储详情（如果有存储）
    if storages:
        storage_id = storages[0]['id']
        logger.info(f"\n测试2: 获取存储详情 (ID: {storage_id})")
        try:
            storage = await chain.get_storage(storage_id)
            if storage:
                logger.info(f"存储名称: {storage['name']}")
                logger.info(f"提供商: {storage['provider']}")
                logger.info(f"启用状态: {storage['enabled']}")
            else:
                logger.warning("存储不存在")
        except Exception as e:
            logger.error(f"测试2失败: {e}")
        
        # 测试3: 列出文件（如果存储已配置）
        logger.info(f"\n测试3: 列出文件 (存储ID: {storage_id})")
        try:
            files = await chain.list_files(storage_id, path="/")
            logger.info(f"找到 {len(files)} 个文件/文件夹")
            for file in files[:5]:  # 只显示前5个
                logger.info(f"  - {file.get('name')} ({file.get('type')})")
        except Exception as e:
            logger.error(f"测试3失败: {e}")
        
        # 测试4: 获取存储使用情况
        logger.info(f"\n测试4: 获取存储使用情况 (存储ID: {storage_id})")
        try:
            usage = await chain.get_storage_usage(storage_id)
            if usage:
                logger.info(f"总容量: {usage['total']} 字节")
                logger.info(f"已使用: {usage['used']} 字节")
                logger.info(f"可用: {usage['available']} 字节")
                logger.info(f"使用率: {usage['percentage']}%")
            else:
                logger.warning("无法获取存储使用情况")
        except Exception as e:
            logger.error(f"测试4失败: {e}")
    
    logger.info("\n" + "="*50)
    logger.info("StorageChain 测试完成")
    logger.info("="*50)


if __name__ == "__main__":
    asyncio.run(test_storage_chain())

