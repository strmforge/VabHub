"""
安全设置115网盘密钥
从环境变量读取密钥并加密存储
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


def setup_115_keys_from_env():
    """从环境变量设置115网盘密钥（只需要AppID和AppKey）"""
    key_manager = get_key_manager()
    
    # 从环境变量读取（优先使用VABHUB_前缀）
    app_id = os.getenv("VABHUB_115_APP_ID") or os.getenv("CLOUD115_APP_ID")
    app_key = os.getenv("VABHUB_115_APP_KEY") or os.getenv("CLOUD115_APP_KEY")
    # AppSecret是可选的，115网盘API不需要
    app_secret = os.getenv("VABHUB_115_APP_SECRET") or os.getenv("CLOUD115_APP_SECRET")
    
    if not app_id or not app_key:
        logger.error("❌ 环境变量未设置！")
        logger.error("")
        logger.error("115网盘只需要AppID和AppKey（AppSecret可选）")
        logger.error("")
        logger.error("请设置以下环境变量之一：")
        logger.error("")
        logger.error("方式1（推荐）:")
        logger.error("  export VABHUB_115_APP_ID='your_app_id'")
        logger.error("  export VABHUB_115_APP_KEY='your_app_key'")
        logger.error("")
        logger.error("方式2:")
        logger.error("  export CLOUD115_APP_ID='your_app_id'")
        logger.error("  export CLOUD115_APP_KEY='your_app_key'")
        logger.error("")
        logger.error("或在 .env 文件中设置：")
        logger.error("  VABHUB_115_APP_ID=your_app_id")
        logger.error("  VABHUB_115_APP_KEY=your_app_key")
        sys.exit(1)
    
    # 检查是否已存在密钥
    existing_keys = key_manager.get_115_keys()
    if existing_keys:
        logger.warning("⚠️  检测到已存在115网盘密钥")
        logger.info("   是否要更新？(y/n): ", end="")
        # 在非交互环境中，默认不更新
        try:
            response = input().strip().lower()
            if response != 'y':
                logger.info("   已取消更新")
                return
        except (EOFError, KeyboardInterrupt):
            logger.info("\n   已取消更新")
            return
    
    # 设置密钥（会自动加密存储）
    key_manager.set_115_keys(
        app_id=app_id,
        app_key=app_key,
        app_secret=app_secret  # 可选
    )
    
    logger.info("="*60)
    logger.info("✅ 115网盘密钥已成功加密存储")
    logger.info("="*60)
    logger.info(f"   AppID: {app_id}")
    logger.info(f"   AppKey: {app_key[:10]}...{app_key[-4:]}")
    if app_secret:
        logger.info(f"   AppSecret: {app_secret[:10]}...{app_secret[-4:]} (可选)")
    logger.info("")
    logger.info("📁 存储位置:")
    logger.info(f"   加密文件: ~/.vabhub/cloud_keys.encrypted")
    logger.info(f"   主密钥: ~/.vabhub/.master_key")
    logger.info("")
    logger.info("🔒 安全提示:")
    logger.info("   - 密钥已使用Fernet加密存储")
    logger.info("   - 请妥善保管主密钥文件")
    logger.info("   - 不要将密钥文件提交到Git仓库")
    logger.info("")
    logger.info("ℹ️  说明:")
    logger.info("   - 115网盘API只需要AppID和AppKey")
    logger.info("   - AppSecret是可选的，通常不需要")
    logger.info("="*60)


def setup_115_keys_interactive():
    """交互式设置115网盘密钥（只需要AppID和AppKey）"""
    key_manager = get_key_manager()
    
    logger.info("="*60)
    logger.info("115网盘密钥设置（交互式）")
    logger.info("="*60)
    logger.info("")
    logger.warning("⚠️  密钥将以加密形式存储")
    logger.info("")
    logger.info("ℹ️  说明: 115网盘API只需要AppID和AppKey，AppSecret是可选的")
    logger.info("")
    
    try:
        app_id = input("请输入 AppID: ").strip()
        if not app_id:
            logger.error("AppID不能为空")
            sys.exit(1)
        
        app_key = input("请输入 AppKey: ").strip()
        if not app_key:
            logger.error("AppKey不能为空")
            sys.exit(1)
        
        app_secret = input("请输入 AppSecret (可选，直接回车跳过): ").strip()
        if not app_secret:
            app_secret = None
            logger.info("   未设置AppSecret（115网盘API不需要）")
        
        # 设置密钥
        key_manager.set_115_keys(
            app_id=app_id,
            app_key=app_key,
            app_secret=app_secret
        )
        
        logger.info("")
        logger.info("✅ 115网盘密钥已成功加密存储")
        logger.info(f"   AppID: {app_id}")
        logger.info(f"   AppKey: {app_key[:10]}...{app_key[-4:]}")
        if app_secret:
            logger.info(f"   AppSecret: {app_secret[:10]}...{app_secret[-4:]} (可选)")
        
    except (EOFError, KeyboardInterrupt):
        logger.info("\n")
        logger.info("已取消设置")
        sys.exit(0)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="安全设置115网盘密钥")
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="交互式设置密钥"
    )
    parser.add_argument(
        "--from-env",
        action="store_true",
        help="从环境变量读取密钥（默认）"
    )
    
    args = parser.parse_args()
    
    if args.interactive:
        setup_115_keys_interactive()
    else:
        setup_115_keys_from_env()


if __name__ == "__main__":
    main()

