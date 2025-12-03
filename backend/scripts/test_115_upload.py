"""
115网盘上传功能测试脚本
测试OSS上传、秒传、断点续传等功能
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


async def test_115_upload():
    """测试115网盘上传功能"""
    logger.info("="*60)
    logger.info("115网盘上传功能测试")
    logger.info("="*60)
    
    # 获取密钥
    key_manager = get_key_manager()
    keys = key_manager.get_115_keys()
    
    if not keys:
        logger.error("❌ 115网盘密钥未配置，请先运行 setup_115_keys.py")
        return
    
    logger.info("✅ 密钥已加载")
    
    # 创建Provider
    provider = Cloud115Provider()
    
    # 初始化
    credentials = {
        "app_id": keys.get("app_id"),
        "app_key": keys.get("app_key"),
        "app_secret": keys.get("app_secret")  # 可选
    }
    
    success = await provider.initialize(credentials)
    if not success:
        logger.error("❌ Provider初始化失败")
        return
    
    logger.info("✅ Provider初始化成功")
    
    # 检查是否已认证
    if not await provider.is_authenticated():
        logger.warning("⚠️  未认证，需要先进行二维码登录")
        logger.info("   生成二维码...")
        
        qr_content, qr_url = await provider.generate_qr_code()
        if qr_content:
            logger.info(f"   二维码URL: {qr_url}")
            logger.info("   请使用115网盘APP扫描二维码登录")
            logger.info("   等待登录...")
            
            # 检查登录状态
            max_attempts = 60  # 最多等待60次（5分钟）
            for i in range(max_attempts):
                await asyncio.sleep(5)
                status, message, token_data = await provider.check_qr_status()
                
                if status == 2:  # 登录成功
                    logger.info("✅ 登录成功")
                    break
                elif status == -1:  # 失败
                    logger.error(f"❌ 登录失败: {message}")
                    return
                else:
                    logger.info(f"   状态: {message} ({i+1}/{max_attempts})")
            else:
                logger.error("❌ 登录超时")
                return
        else:
            logger.error("❌ 生成二维码失败")
            return
    else:
        logger.info("✅ 已认证")
    
    # 测试上传（需要准备测试文件）
    test_file_path = input("请输入测试文件路径（直接回车跳过上传测试）: ").strip()
    
    if test_file_path:
        test_file = Path(test_file_path)
        if not test_file.exists():
            logger.error(f"❌ 文件不存在: {test_file_path}")
            return
        
        logger.info(f"📤 开始上传: {test_file.name}")
        logger.info(f"   文件大小: {test_file.stat().st_size / 1024 / 1024:.2f}MB")
        
        # 进度回调
        def progress_callback(progress: float):
            logger.info(f"   上传进度: {progress:.1f}%")
        
        # 上传到根目录
        remote_path = f"/{test_file.name}"
        
        success = await provider.upload_file(
            local_path=str(test_file),
            remote_path=remote_path,
            progress_callback=progress_callback
        )
        
        if success:
            logger.info("✅ 上传成功")
        else:
            logger.error("❌ 上传失败")
    else:
        logger.info("⏭️  跳过上传测试")
    
    # 测试文件列表
    logger.info("📁 测试文件列表...")
    files = await provider.list_files(path="/")
    logger.info(f"   根目录文件数: {len(files)}")
    for file_info in files[:10]:  # 只显示前10个
        logger.info(f"   - {file_info.name} ({file_info.type})")
    
    # 测试存储使用情况
    logger.info("💾 测试存储使用情况...")
    usage = await provider.get_storage_usage()
    if usage:
        logger.info(f"   总容量: {usage.total / 1024 / 1024 / 1024 / 1024:.2f}TB")
        logger.info(f"   已使用: {usage.used / 1024 / 1024 / 1024 / 1024:.2f}TB")
        logger.info(f"   可用容量: {usage.available / 1024 / 1024 / 1024 / 1024:.2f}TB")
        logger.info(f"   使用率: {usage.percentage:.2f}%")
    else:
        logger.warning("⚠️  获取存储使用情况失败")
    
    # 关闭
    await provider.close()
    
    logger.info("="*60)
    logger.info("测试完成")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(test_115_upload())

