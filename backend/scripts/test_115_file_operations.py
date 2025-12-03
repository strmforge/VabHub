"""
115网盘文件操作测试脚本
测试文件列表、上传、下载、移动、复制、重命名等功能
"""

import asyncio
import sys
from pathlib import Path
import tempfile
import os

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


async def test_file_operations():
    """测试115网盘文件操作"""
    logger.info("="*60)
    logger.info("115网盘文件操作测试")
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
        logger.info("")
        logger.info("运行登录脚本:")
        logger.info("  python backend/scripts/test_115_qrcode.py")
        logger.info("")
        logger.info("登录成功后，再运行此测试脚本")
        await provider.close()
        return
    
    logger.info("✅ 已认证")
    logger.info(f"   User ID: {provider.user_id}")
    logger.info(f"   User Name: {provider.user_name}")
    logger.info("")
    
    try:
        # 测试1: 文件列表
        logger.info("="*60)
        logger.info("测试1: 文件列表")
        logger.info("="*60)
        files = await provider.list_files("/")
        logger.info(f"✅ 根目录文件数量: {len(files)}")
        if files:
            logger.info("前5个文件/目录:")
            for i, f in enumerate(files[:5], 1):
                logger.info(f"  {i}. {f.name} ({f.type}) - ID: {f.id}")
        logger.info("")
        
        # 测试2: 创建测试文件夹
        logger.info("="*60)
        logger.info("测试2: 创建测试文件夹")
        logger.info("="*60)
        test_folder = await provider.create_folder("/", "VabHub测试")
        if test_folder:
            logger.info(f"✅ 创建测试文件夹成功: {test_folder.name} (ID: {test_folder.id})")
            test_folder_path = f"/{test_folder.name}"
        else:
            logger.warning("⚠️  创建测试文件夹失败，可能已存在")
            # 尝试查找已存在的文件夹
            files = await provider.list_files("/")
            for f in files:
                if f.name == "VabHub测试" and f.type == "dir":
                    test_folder_path = f"/{f.name}"
                    logger.info(f"✅ 使用已存在的测试文件夹: {test_folder_path}")
                    break
            else:
                logger.error("❌ 无法创建或找到测试文件夹")
                return
        logger.info("")
        
        # 测试3: 创建测试文件（用于后续测试）
        logger.info("="*60)
        logger.info("测试3: 创建测试文件")
        logger.info("="*60)
        test_file_content = "VabHub 115网盘测试文件内容\nThis is a test file for 115 cloud storage operations.".encode('utf-8')
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as tmp_file:
            tmp_file.write(test_file_content)
            tmp_file_path = tmp_file.name
        
        try:
            remote_path = f"{test_folder_path}/test_file.txt"
            logger.info(f"上传测试文件: {tmp_file_path} -> {remote_path}")
            success = await provider.upload_file(tmp_file_path, remote_path)
            if success:
                logger.info("✅ 上传测试文件成功")
                # 获取上传后的文件信息
                files = await provider.list_files(test_folder_path)
                test_file = None
                for f in files:
                    if f.name == "test_file.txt":
                        test_file = f
                        break
                if test_file:
                    logger.info(f"   文件ID: {test_file.id}")
                    logger.info(f"   文件大小: {test_file.size} bytes")
                else:
                    logger.warning("⚠️  无法找到上传的文件")
            else:
                logger.error("❌ 上传测试文件失败")
                return
        finally:
            # 清理临时文件
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
        logger.info("")
        
        if not test_file:
            logger.error("❌ 无法获取测试文件信息，跳过后续测试")
            return
        
        # 测试4: 重命名文件
        logger.info("="*60)
        logger.info("测试4: 重命名文件")
        logger.info("="*60)
        new_name = "test_file_renamed.txt"
        logger.info(f"重命名文件: test_file.txt -> {new_name}")
        success = await provider.rename_file(test_file.id, new_name)
        if success:
            logger.info("✅ 重命名文件成功")
            # 验证重命名
            files = await provider.list_files(test_folder_path)
            renamed_file = None
            for f in files:
                if f.name == new_name:
                    renamed_file = f
                    break
            if renamed_file:
                logger.info(f"   验证成功: 文件已重命名为 {renamed_file.name}")
                test_file = renamed_file  # 更新test_file引用
            else:
                logger.warning("⚠️  重命名后无法找到文件")
        else:
            logger.error("❌ 重命名文件失败")
        logger.info("")
        
        # 测试5: 创建目标文件夹
        logger.info("="*60)
        logger.info("测试5: 创建目标文件夹（用于移动/复制测试）")
        logger.info("="*60)
        target_folder = await provider.create_folder("/", "VabHub目标文件夹")
        if target_folder:
            logger.info(f"✅ 创建目标文件夹成功: {target_folder.name} (ID: {target_folder.id})")
            target_folder_path = f"/{target_folder.name}"
        else:
            logger.warning("⚠️  创建目标文件夹失败，可能已存在")
            files = await provider.list_files("/")
            for f in files:
                if f.name == "VabHub目标文件夹" and f.type == "dir":
                    target_folder_path = f"/{f.name}"
                    logger.info(f"✅ 使用已存在的目标文件夹: {target_folder_path}")
                    break
            else:
                logger.error("❌ 无法创建或找到目标文件夹")
                return
        logger.info("")
        
        # 测试6: 复制文件
        logger.info("="*60)
        logger.info("测试6: 复制文件")
        logger.info("="*60)
        copied_name = "test_file_copied.txt"
        logger.info(f"复制文件: {test_file.name} -> {target_folder_path}/{copied_name}")
        success = await provider.copy_file(test_file.id, target_folder_path, copied_name)
        if success:
            logger.info("✅ 复制文件成功")
            # 验证复制
            files = await provider.list_files(target_folder_path)
            copied_file = None
            for f in files:
                if f.name == copied_name:
                    copied_file = f
                    break
            if copied_file:
                logger.info(f"   验证成功: 文件已复制到 {target_folder_path}/{copied_file.name}")
            else:
                logger.warning("⚠️  复制后无法找到文件")
        else:
            logger.error("❌ 复制文件失败")
        logger.info("")
        
        # 测试7: 移动文件
        logger.info("="*60)
        logger.info("测试7: 移动文件")
        logger.info("="*60)
        moved_name = "test_file_moved.txt"
        logger.info(f"移动文件: {test_file.name} -> {target_folder_path}/{moved_name}")
        success = await provider.move_file(test_file.id, target_folder_path, moved_name)
        if success:
            logger.info("✅ 移动文件成功")
            # 验证移动（原位置应该没有文件了）
            files = await provider.list_files(test_folder_path)
            found_in_original = any(f.name == test_file.name or f.name == new_name for f in files)
            if not found_in_original:
                logger.info("   验证成功: 文件已从原位置移除")
            else:
                logger.warning("⚠️  文件仍在原位置")
            
            # 验证移动（新位置应该有文件）
            files = await provider.list_files(target_folder_path)
            moved_file = None
            for f in files:
                if f.name == moved_name:
                    moved_file = f
                    break
            if moved_file:
                logger.info(f"   验证成功: 文件已移动到 {target_folder_path}/{moved_file.name}")
            else:
                logger.warning("⚠️  移动后无法在新位置找到文件")
        else:
            logger.error("❌ 移动文件失败")
        logger.info("")
        
        # 测试8: 下载文件
        logger.info("="*60)
        logger.info("测试8: 下载文件")
        logger.info("="*60)
        if moved_file:
            download_file = moved_file
        elif copied_file:
            download_file = copied_file
        else:
            logger.warning("⚠️  没有可下载的文件，跳过下载测试")
            download_file = None
        
        if download_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp_download:
                download_path = tmp_download.name
            
            try:
                logger.info(f"下载文件: {download_file.name} -> {download_path}")
                success = await provider.download_file(download_file.id, download_path)
                if success:
                    logger.info("✅ 下载文件成功")
                    # 验证下载的文件内容
                    with open(download_path, 'rb') as f:
                        downloaded_content = f.read()
                    if downloaded_content == test_file_content:
                        logger.info("   验证成功: 下载的文件内容正确")
                    else:
                        logger.warning("⚠️  下载的文件内容不匹配")
                else:
                    logger.error("❌ 下载文件失败")
            finally:
                if os.path.exists(download_path):
                    os.unlink(download_path)
        logger.info("")
        
        # 测试9: 获取存储使用情况
        logger.info("="*60)
        logger.info("测试9: 获取存储使用情况")
        logger.info("="*60)
        usage = await provider.get_storage_usage()
        if usage:
            logger.info("✅ 获取存储使用情况成功")
            logger.info(f"   总容量: {usage.total / (1024**3):.2f} GB")
            logger.info(f"   已使用: {usage.used / (1024**3):.2f} GB")
            logger.info(f"   可用空间: {usage.available / (1024**3):.2f} GB")
            logger.info(f"   使用率: {usage.percentage:.2f}%")
        else:
            logger.warning("⚠️  无法获取存储使用情况")
        logger.info("")
        
        logger.info("="*60)
        logger.info("✅ 所有测试完成")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await provider.close()


if __name__ == "__main__":
    asyncio.run(test_file_operations())

