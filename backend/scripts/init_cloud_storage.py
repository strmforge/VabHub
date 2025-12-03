"""
初始化云存储密钥
使用环境变量或加密存储的115网盘开发者密钥
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
backend_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.core.cloud_key_manager import get_key_manager
from loguru import logger


def init_115_keys():
    """初始化115网盘密钥（从环境变量读取，只需要AppID和AppKey）"""
    key_manager = get_key_manager()
    
    # 从环境变量读取115网盘开发者密钥（安全方式）
    # 115网盘API只需要AppID和AppKey，AppSecret是可选的
    app_id = os.getenv("CLOUD115_APP_ID") or os.getenv("VABHUB_115_APP_ID")
    app_key = os.getenv("CLOUD115_APP_KEY") or os.getenv("VABHUB_115_APP_KEY")
    app_secret = os.getenv("CLOUD115_APP_SECRET") or os.getenv("VABHUB_115_APP_SECRET")
    
    # 如果没有从环境变量获取到，检查是否已存储在加密文件中
    if not app_id or not app_key:
        existing_keys = key_manager.get_115_keys()
        if existing_keys:
            logger.info("✅ 115网盘密钥已存在于加密存储中")
            logger.info("   如需更新密钥，请设置环境变量后重新运行此脚本")
            return
        else:
            logger.error("❌ 115网盘密钥未配置！")
            logger.error("   115网盘API只需要AppID和AppKey（AppSecret可选）")
            logger.error("")
            logger.error("   请设置以下环境变量：")
            logger.error("   - CLOUD115_APP_ID 或 VABHUB_115_APP_ID")
            logger.error("   - CLOUD115_APP_KEY 或 VABHUB_115_APP_KEY")
            logger.error("   - CLOUD115_APP_SECRET 或 VABHUB_115_APP_SECRET (可选)")
            raise ValueError("115网盘密钥未配置")
    
    # 设置密钥（会自动加密存储）
    key_manager.set_115_keys(
        app_id=app_id,
        app_key=app_key,
        app_secret=app_secret  # 可选
    )
    
    logger.info("✅ 115网盘密钥已初始化并加密存储")
    logger.info(f"   AppID: {app_id}")
    logger.info(f"   AppKey: {app_key[:10]}...")
    if app_secret:
        logger.info(f"   AppSecret: {app_secret[:10]}... (可选)")
    logger.info("   ⚠️ 密钥已加密存储到: ~/.vabhub/cloud_keys.encrypted")
    logger.info("   ℹ️  说明: 115网盘API只需要AppID和AppKey，AppSecret通常不需要")


def main():
    """主函数"""
    logger.info("="*50)
    logger.info("初始化云存储密钥")
    logger.info("="*50)
    
    try:
        # 初始化115网盘密钥
        init_115_keys()
        
        logger.info("="*50)
        logger.info("✅ 云存储密钥初始化完成")
        logger.info("="*50)
    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

