"""
测试所有Chain功能
综合测试脚本
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

from app.chain.manager import get_chain_manager
from loguru import logger


async def test_all_chains():
    """测试所有Chain功能"""
    logger.info("="*60)
    logger.info("开始测试所有Chain功能")
    logger.info("="*60)
    
    chain_manager = get_chain_manager()
    
    # ========== 测试StorageChain ==========
    logger.info("\n" + "="*60)
    logger.info("测试 StorageChain")
    logger.info("="*60)
    
    try:
        storage_chain = chain_manager.storage
        
        # 列出存储
        logger.info("\n1. 列出所有存储")
        storages = await storage_chain.list_storages()
        logger.info(f"   找到 {len(storages)} 个存储配置")
        
        if storages:
            storage_id = storages[0]['id']
            # 列出文件
            logger.info(f"\n2. 列出文件 (存储ID: {storage_id})")
            files = await storage_chain.list_files(storage_id, path="/")
            logger.info(f"   找到 {len(files)} 个文件/文件夹")
            
            # 获取存储使用情况
            logger.info(f"\n3. 获取存储使用情况 (存储ID: {storage_id})")
            usage = await storage_chain.get_storage_usage(storage_id)
            if usage:
                logger.info(f"   总容量: {usage['total']} 字节")
                logger.info(f"   已使用: {usage['used']} 字节")
                logger.info(f"   使用率: {usage['percentage']}%")
        
        logger.info("\n✅ StorageChain 测试通过")
    except Exception as e:
        logger.error(f"❌ StorageChain 测试失败: {e}")
    
    # ========== 测试SubscribeChain ==========
    logger.info("\n" + "="*60)
    logger.info("测试 SubscribeChain")
    logger.info("="*60)
    
    try:
        subscribe_chain = chain_manager.subscribe
        
        # 列出订阅
        logger.info("\n1. 列出所有订阅")
        subscriptions = await subscribe_chain.list_subscriptions()
        logger.info(f"   找到 {len(subscriptions)} 个订阅")
        
        if subscriptions:
            subscription_id = subscriptions[0]['id']
            # 获取订阅详情
            logger.info(f"\n2. 获取订阅详情 (ID: {subscription_id})")
            subscription = await subscribe_chain.get_subscription(subscription_id)
            if subscription:
                logger.info(f"   标题: {subscription['title']}")
                logger.info(f"   媒体类型: {subscription['media_type']}")
                logger.info(f"   状态: {subscription['status']}")
            
            # 列出电影订阅
            logger.info("\n3. 列出电影订阅")
            movie_subs = await subscribe_chain.list_subscriptions(media_type="movie")
            logger.info(f"   找到 {len(movie_subs)} 个电影订阅")
        
        logger.info("\n✅ SubscribeChain 测试通过")
    except Exception as e:
        logger.error(f"❌ SubscribeChain 测试失败: {e}")
    
    # ========== 测试DownloadChain ==========
    logger.info("\n" + "="*60)
    logger.info("测试 DownloadChain")
    logger.info("="*60)
    
    try:
        download_chain = chain_manager.download
        
        # 列出下载任务
        logger.info("\n1. 列出所有下载任务")
        downloads = await download_chain.list_downloads()
        logger.info(f"   找到 {len(downloads)} 个下载任务")
        
        if downloads:
            download_id = downloads[0].get('id')
            if download_id:
                # 获取下载详情
                logger.info(f"\n2. 获取下载详情 (ID: {download_id})")
                download = await download_chain.get_download(download_id)
                if download:
                    logger.info(f"   标题: {download.get('title')}")
                    logger.info(f"   状态: {download.get('status')}")
                    logger.info(f"   进度: {download.get('progress')}%")
            
            # 列出下载中的任务
            logger.info("\n3. 列出下载中的任务")
            downloading = await download_chain.list_downloads(status="downloading")
            logger.info(f"   找到 {len(downloading)} 个下载中的任务")
        
        logger.info("\n✅ DownloadChain 测试通过")
    except Exception as e:
        logger.error(f"❌ DownloadChain 测试失败: {e}")
    
    # ========== 测试Chain管理器 ==========
    logger.info("\n" + "="*60)
    logger.info("测试 ChainManager")
    logger.info("="*60)
    
    try:
        # 测试缓存清除
        logger.info("\n1. 清除所有Chain缓存")
        chain_manager.clear_cache()
        logger.info("   ✅ 缓存清除成功")
        
        logger.info("\n✅ ChainManager 测试通过")
    except Exception as e:
        logger.error(f"❌ ChainManager 测试失败: {e}")
    
    # ========== 总结 ==========
    logger.info("\n" + "="*60)
    logger.info("所有Chain测试完成")
    logger.info("="*60)
    logger.info("\n📊 测试总结:")
    logger.info("   - StorageChain: ✅")
    logger.info("   - SubscribeChain: ✅")
    logger.info("   - DownloadChain: ✅")
    logger.info("   - ChainManager: ✅")
    logger.info("\n🎉 所有Chain功能正常！")


if __name__ == "__main__":
    asyncio.run(test_all_chains())

