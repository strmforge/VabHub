"""
115网盘Token持久化测试脚本
测试token保存到数据库和从数据库加载功能
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

from app.core.database import AsyncSessionLocal
from app.modules.cloud_storage.service import CloudStorageService
from app.core.cloud_key_manager import get_key_manager
from loguru import logger


async def test_token_persist():
    """测试115网盘token持久化"""
    logger.info("="*60)
    logger.info("115网盘Token持久化测试")
    logger.info("="*60)
    
    # 获取密钥
    key_manager = get_key_manager()
    keys = key_manager.get_115_keys()
    
    if not keys:
        logger.error("❌ 115网盘密钥未配置")
        return
    
    logger.info("✅ 密钥已加载")
    
    async with AsyncSessionLocal() as db:
        service = CloudStorageService(db)
        
        try:
            # 步骤1: 查找或创建115网盘存储配置
            logger.info("")
            logger.info("="*60)
            logger.info("步骤1: 查找或创建115网盘存储配置")
            logger.info("="*60)
            
            storages = await service.list_storages(provider="115")
            if storages:
                storage = storages[0]
                logger.info(f"✅ 找到现有存储配置: {storage.name} (ID: {storage.id})")
            else:
                logger.info("创建新的115网盘存储配置...")
                storage_data = {
                    "name": "115网盘",
                    "provider": "115",
                    "enabled": True
                }
                storage = await service.create_storage(storage_data)
                if storage:
                    logger.info(f"✅ 创建存储配置成功: {storage.name} (ID: {storage.id})")
                else:
                    logger.error("❌ 创建存储配置失败")
                    return
            
            storage_id = storage.id
            
            # 检查当前token状态
            logger.info("")
            logger.info("当前Token状态:")
            logger.info(f"   Access Token: {storage.access_token[:30] + '...' if storage.access_token else 'None'}")
            logger.info(f"   Refresh Token: {storage.refresh_token[:30] + '...' if storage.refresh_token else 'None'}")
            logger.info(f"   Expires At: {storage.expires_at}")
            logger.info(f"   User ID: {storage.user_id}")
            logger.info(f"   User Name: {storage.user_name}")
            logger.info("")
            
            # 步骤2: 初始化Provider（应该从数据库加载token）
            logger.info("="*60)
            logger.info("步骤2: 初始化Provider（从数据库加载token）")
            logger.info("="*60)
            
            success = await service.initialize_provider(storage_id)
            if success:
                logger.info("✅ Provider初始化成功")
                
                # 获取provider并检查token
                provider = service._get_provider(storage)
                if provider.access_token:
                    logger.info("✅ Token已从数据库加载")
                    logger.info(f"   Access Token: {provider.access_token[:30]}...")
                    logger.info(f"   User ID: {provider.user_id}")
                    logger.info(f"   User Name: {provider.user_name}")
                    
                    # 验证token是否有效
                    is_authenticated = await provider.is_authenticated()
                    if is_authenticated:
                        logger.info("✅ Token有效，无需重新登录")
                    else:
                        logger.warning("⚠️  Token已过期或无效，需要重新登录")
                        logger.info("")
                        logger.info("请运行以下命令重新登录:")
                        logger.info("  python backend/scripts/test_115_qrcode.py")
                else:
                    logger.warning("⚠️  数据库中没有保存的token，需要首次登录")
                    logger.info("")
                    logger.info("请运行以下命令进行首次登录:")
                    logger.info("  python backend/scripts/test_115_qrcode.py")
            else:
                logger.error("❌ Provider初始化失败")
                return
            
            # 步骤3: 测试token刷新（如果token存在）
            if storage.refresh_token:
                logger.info("")
                logger.info("="*60)
                logger.info("步骤3: 测试Token刷新和持久化")
                logger.info("="*60)
                
                provider = service._get_provider(storage)
                if provider.refresh_token:
                    logger.info("尝试刷新token...")
                    success = await provider.refresh_token()
                    if success:
                        logger.info("✅ Token刷新成功")
                        
                        # 从数据库重新加载，验证token是否已保存
                        await db.refresh(storage)
                        if storage.access_token == provider.access_token:
                            logger.info("✅ Token已成功保存到数据库")
                            logger.info(f"   数据库中的Token: {storage.access_token[:30]}...")
                        else:
                            logger.warning("⚠️  Token保存验证失败")
                    else:
                        logger.warning("⚠️  Token刷新失败（可能是token已过期）")
            
            logger.info("")
            logger.info("="*60)
            logger.info("✅ Token持久化测试完成")
            logger.info("="*60)
            logger.info("")
            logger.info("说明:")
            logger.info("1. Token会在登录成功后自动保存到数据库")
            logger.info("2. Token会在刷新后自动更新到数据库")
            logger.info("3. 初始化Provider时会自动从数据库加载token")
            logger.info("4. 重启应用后，token会自动恢复，无需重新登录")
            
        except Exception as e:
            logger.error(f"❌ 测试过程中发生错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_token_persist())

