"""
115网盘二维码扫描测试脚本
测试PKCE认证流程：生成二维码、检查登录状态
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


def generate_qr_code_image(qr_content: str) -> str:
    """生成二维码图片（Base64编码）"""
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
        
        # 转换为Base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        logger.error(f"生成二维码图片失败: {e}")
        return None


async def test_115_qrcode():
    """测试115网盘二维码扫描功能"""
    logger.info("="*60)
    logger.info("115网盘二维码扫描测试")
    logger.info("="*60)
    
    # 获取密钥
    key_manager = get_key_manager()
    keys = key_manager.get_115_keys()
    
    if not keys:
        logger.error("❌ 115网盘密钥未配置，请先运行 setup_115_keys.py")
        logger.error("")
        logger.error("设置密钥:")
        logger.error("  export VABHUB_115_APP_ID='100197729'")
        logger.error("  export VABHUB_115_APP_KEY='d099625d59aba2a79e70b81fc4589b26'")
        logger.error("  python backend/scripts/setup_115_keys.py --from-env")
        return
    
    logger.info("✅ 密钥已加载")
    logger.info(f"   AppID: {keys.get('app_id')}")
    logger.info(f"   AppKey: {keys.get('app_key')[:10]}...")
    
    # 创建Provider
    provider = Cloud115Provider()
    
    # 初始化
    credentials = {
        "app_id": keys.get("app_id"),
        "app_key": keys.get("app_key"),
        "app_secret": keys.get("app_secret")  # 可选
    }
    
    logger.info("")
    logger.info("初始化Provider...")
    success = await provider.initialize(credentials)
    if not success:
        logger.error("❌ Provider初始化失败")
        return
    
    logger.info("✅ Provider初始化成功")
    
    # 检查是否已认证
    is_authenticated = await provider.is_authenticated()
    if is_authenticated:
        logger.info("✅ 已认证，访问令牌有效")
        logger.info(f"   User ID: {provider.user_id}")
        logger.info(f"   User Name: {provider.user_name}")
        logger.info("")
        logger.info("如需重新登录，请先删除现有的访问令牌")
        return
    
    logger.info("")
    logger.info("未认证，开始二维码登录流程...")
    logger.info("")
    
    try:
        # 生成二维码
        logger.info("📱 生成二维码...")
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
        
        # 生成二维码图片（Base64）
        qr_image = generate_qr_code_image(qr_content)
        if qr_image:
            logger.info("二维码图片（Base64）已生成")
            logger.info("（可以在支持Base64的浏览器中查看）")
        
        # 保存二维码图片到文件
        try:
            qr_file = Path(__file__).parent.parent.parent / "115_qrcode.png"
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
            logger.info(f"✅ 二维码图片已保存: {qr_file}")
        except Exception as e:
            logger.warning(f"保存二维码图片失败: {e}")
        
        logger.info("")
        logger.info("="*60)
        logger.info("开始实时监测登录状态...")
        logger.info("请使用115网盘APP扫描二维码并确认登录")
        logger.info("="*60)
        logger.info("")
        
        # 实时检查登录状态（持续监测）
        max_attempts = 120  # 最多等待10分钟（每5秒检查一次）
        last_status = -1
        
        for i in range(max_attempts):
            status, message, token_data = await provider.check_qr_status()
            
            # 只在状态变化时输出详细信息
            if status != last_status:
                if status == 0:
                    logger.info(f"📱 [{i+1}/{max_attempts}] 状态: 等待扫码...")
                elif status == 1:
                    logger.info(f"✅ [{i+1}/{max_attempts}] 状态: 已扫码，等待确认...")
                elif status == 2:
                    logger.info("")
                    logger.info("="*60)
                    logger.info("✅ 检测到登录确认！正在获取访问令牌...")
                    logger.info("="*60)
                    logger.info("")
                    
                    # 登录成功，token_data已经包含在返回值中
                    if token_data:
                        logger.info("✅ 登录成功！")
                        logger.info("")
                        logger.info("访问令牌信息:")
                        logger.info(f"   Access Token: {token_data.get('access_token', '')[:20]}...")
                        logger.info(f"   Refresh Token: {token_data.get('refresh_token', '')[:20]}...")
                        logger.info(f"   User ID: {token_data.get('user_id')}")
                        logger.info(f"   User Name: {token_data.get('user_name')}")
                        logger.info("")
                        logger.info("✅ 认证信息已保存到Provider")
                        
                        # 验证认证状态
                        is_authenticated = await provider.is_authenticated()
                        if is_authenticated:
                            logger.info("✅ 认证状态验证成功")
                            
                            # 测试获取用户信息
                            logger.info("")
                            logger.info("测试获取用户信息...")
                            await provider._get_user_info()
                            logger.info(f"   User ID: {provider.user_id}")
                            logger.info(f"   User Name: {provider.user_name}")
                        else:
                            logger.error("❌ 认证状态验证失败")
                    else:
                        logger.error("❌ 获取访问令牌失败")
                    
                    break
                elif status == -1:
                    logger.error(f"❌ [{i+1}/{max_attempts}] 登录失败: {message}")
                    logger.info("")
                    logger.info("请重新运行脚本生成新的二维码")
                    break
                
                last_status = status
            else:
                # 状态未变化，只显示进度（每10次显示一次）
                if (i + 1) % 10 == 0:
                    if status == 0:
                        logger.info(f"⏳ [{i+1}/{max_attempts}] 仍在等待扫码...")
                    elif status == 1:
                        logger.info(f"⏳ [{i+1}/{max_attempts}] 仍在等待确认...")
            
            # 等待5秒后继续检查
            await asyncio.sleep(5)
        else:
            logger.error("")
            logger.error("❌ 登录超时（10分钟）")
            logger.info("")
            logger.info("请重新运行脚本生成新的二维码")
    
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 关闭Provider
        await provider.close()
        logger.info("")
        logger.info("="*60)
        logger.info("测试完成")
        logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(test_115_qrcode())

