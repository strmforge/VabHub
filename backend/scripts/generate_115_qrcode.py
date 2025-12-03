"""
115网盘二维码生成脚本（简化版）
快速生成二维码供扫描测试
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
import qrcode
from io import BytesIO
import base64
from PIL import Image


def display_qr_code(qr_content: str):
    """显示二维码（在终端）"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=2,
            border=2,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)
        
        # 生成二维码图片
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 尝试在终端显示（如果支持）
        try:
            # 使用qrcode的终端显示功能
            qr.print_ascii(invert=True)
        except:
            # 如果终端不支持，保存为文件
            qr_file = Path(__file__).parent.parent.parent / "115_qrcode.png"
            img.save(qr_file)
            logger.info(f"二维码已保存到: {qr_file}")
            logger.info("请打开该图片文件扫描")
        
        return img
    except Exception as e:
        logger.error(f"生成二维码图片失败: {e}")
        return None


async def generate_qrcode():
    """生成115网盘二维码"""
    logger.info("="*60)
    logger.info("115网盘二维码生成")
    logger.info("="*60)
    
    # 获取密钥
    key_manager = get_key_manager()
    keys = key_manager.get_115_keys()
    
    if not keys:
        logger.error("❌ 115网盘密钥未配置")
        logger.error("请先运行: python backend/scripts/setup_115_keys.py --from-env")
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
    
    logger.info("初始化Provider...")
    success = await provider.initialize(credentials)
    if not success:
        logger.error("❌ Provider初始化失败")
        return
    
    logger.info("✅ Provider初始化成功")
    
    try:
        # 生成二维码
        logger.info("")
        logger.info("📱 正在生成二维码...")
        qr_content, qr_url = await provider.generate_qr_code()
        
        if not qr_content:
            logger.error("❌ 生成二维码失败")
            return
        
        logger.info("✅ 二维码生成成功")
        logger.info("")
        logger.info("="*60)
        logger.info("请使用115网盘APP扫描以下二维码")
        logger.info("="*60)
        logger.info("")
        logger.info(f"二维码URL: {qr_url}")
        logger.info("")
        logger.info("二维码内容:")
        logger.info(qr_content)
        logger.info("")
        
        # 显示二维码（终端）
        logger.info("="*60)
        logger.info("二维码（终端显示）:")
        logger.info("="*60)
        display_qr_code(qr_content)
        
        # 保存二维码图片
        qr_file = Path(__file__).parent.parent.parent / "115_qrcode.png"
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_content)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(qr_file)
            logger.info("")
            logger.info(f"✅ 二维码图片已保存: {qr_file}")
            logger.info("   可以使用图片查看器打开扫描")
        except Exception as e:
            logger.warning(f"保存二维码图片失败: {e}")
        
        logger.info("")
        logger.info("="*60)
        logger.info("二维码已生成，请使用115网盘APP扫描")
        logger.info("扫描后，运行 test_115_qrcode.py 检查登录状态")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ 生成二维码失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await provider.close()


if __name__ == "__main__":
    asyncio.run(generate_qrcode())

