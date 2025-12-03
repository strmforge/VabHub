"""
临时测试脚本：使用TVDB API key测试TVDB和Fanart集成
不写入系统配置，仅用于测试
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.modules.thetvdb import TheTvDbModule
from app.modules.fanart import FanartModule
from app.modules.media_identification.service import MediaIdentificationService
from app.core.database import AsyncSessionLocal
from loguru import logger

# 临时TVDB API key（仅用于测试，不写入系统）
TEST_TVDB_API_KEY = "fe29c50eb189bac40cb5abd33de5be96"
TEST_TVDB_API_PIN = ""  # PIN可选


async def test_tvdb_direct():
    """直接测试TVDB模块"""
    print("\n" + "="*60)
    print("测试1: TVDB模块直接测试")
    print("="*60)
    
    try:
        # 创建TVDB模块实例
        tvdb_module = TheTvDbModule()
        
        # 临时设置API key（仅用于测试）
        import app.core.config as config_module
        original_key = config_module.settings._tvdb_api_key
        original_pin = config_module.settings._tvdb_api_pin
        
        # 临时替换API key
        config_module.settings._tvdb_api_key = TEST_TVDB_API_KEY
        config_module.settings._tvdb_api_pin = TEST_TVDB_API_PIN
        
        print(f"\n[1.1] 使用临时TVDB API Key: {TEST_TVDB_API_KEY[:20]}...")
        
        # 测试搜索
        print("\n[1.2] 测试TVDB搜索: 'The Wheel of Time'")
        try:
            results = await tvdb_module.search_tvdb("The Wheel of Time")
            if results:
                print(f"[OK] 搜索成功，找到 {len(results)} 个结果")
                if len(results) > 0:
                    best_match = results[0]
                    print(f"   - 最佳匹配: {best_match.get('name', 'N/A')}")
                    print(f"   - TVDB ID: {best_match.get('id', 'N/A')}")
                    print(f"   - 年份: {best_match.get('year', 'N/A')}")
                    
                    # 测试获取详细信息
                    tvdb_id = best_match.get('id')
                    if tvdb_id:
                        print(f"\n[1.3] 测试获取TVDB详细信息: TVDB ID {tvdb_id}")
                        tvdb_info = await tvdb_module.tvdb_info(tvdb_id)
                        if tvdb_info:
                            print("[OK] 获取TVDB信息成功")
                            print(f"   - 标题: {tvdb_info.get('name', 'N/A')}")
                            print(f"   - 年份: {tvdb_info.get('year', 'N/A')}")
                            print(f"   - 概述: {tvdb_info.get('overview', 'N/A')[:100]}...")
                            if tvdb_info.get('image'):
                                print(f"   - 海报: {tvdb_info.get('image', 'N/A')[:80]}...")
                            if tvdb_info.get('remoteIds'):
                                print(f"   - 外部ID: {tvdb_info.get('remoteIds', [])}")
                            
                            return tvdb_id, tvdb_info
                        else:
                            print("[WARN] 获取TVDB信息失败")
            else:
                print("[WARN] 搜索未返回结果")
        except Exception as e:
            print(f"[ERROR] TVDB搜索失败: {e}")
            logger.exception(e)
        
        # 恢复原始配置
        config_module.settings._tvdb_api_key = original_key
        config_module.settings._tvdb_api_pin = original_pin
        
    except Exception as e:
        print(f"[ERROR] TVDB模块测试失败: {e}")
        logger.exception(e)
    
    return None, None


async def test_fanart_with_tvdb_id(tvdb_id: int):
    """使用TVDB ID测试Fanart"""
    print("\n" + "="*60)
    print("测试2: Fanart模块测试（使用TVDB ID）")
    print("="*60)
    
    if not tvdb_id:
        print("[WARN] 缺少TVDB ID，跳过Fanart测试")
        return
    
    try:
        # 创建Fanart模块实例
        fanart_module = FanartModule()
        
        # 临时启用Fanart（仅用于测试）
        import app.core.config as config_module
        original_enable = config_module.settings.FANART_ENABLE
        
        # 临时启用
        config_module.settings.FANART_ENABLE = True
        
        print(f"\n[2.1] 使用TVDB ID {tvdb_id} 获取Fanart图片")
        try:
            fanart_images = await fanart_module.obtain_images(
                media_type="tv",
                tmdb_id=None,
                tvdb_id=tvdb_id
            )
            
            if fanart_images:
                print("[OK] Fanart图片获取成功")
                print(f"   - 返回的图片类型: {list(fanart_images.keys())}")
                
                # 检查海报
                if "tvposter" in fanart_images:
                    posters = fanart_images["tvposter"]
                    if isinstance(posters, list) and len(posters) > 0:
                        print(f"   - 海报数量: {len(posters)}")
                        best_poster = max(posters, key=lambda x: int(x.get("likes", "0")))
                        print(f"   - 最佳海报URL: {best_poster.get('url', 'N/A')[:80]}...")
                        print(f"   - 最佳海报语言: {best_poster.get('lang', 'N/A')}")
                        print(f"   - 最佳海报likes: {best_poster.get('likes', '0')}")
                
                # 检查背景图
                if "showbackground" in fanart_images:
                    backgrounds = fanart_images["showbackground"]
                    if isinstance(backgrounds, list) and len(backgrounds) > 0:
                        print(f"   - 背景图数量: {len(backgrounds)}")
                        best_bg = max(backgrounds, key=lambda x: int(x.get("likes", "0")))
                        print(f"   - 最佳背景图URL: {best_bg.get('url', 'N/A')[:80]}...")
                
                return fanart_images
            else:
                print("[WARN] 未获取到Fanart图片")
        except Exception as e:
            print(f"[ERROR] Fanart图片获取失败: {e}")
            logger.exception(e)
        
        # 恢复原始配置
        config_module.settings.FANART_ENABLE = original_enable
        
    except Exception as e:
        print(f"[ERROR] Fanart模块测试失败: {e}")
        logger.exception(e)
    
    return None


async def test_media_identification_with_tvdb():
    """测试媒体识别服务中的TVDB和Fanart集成"""
    print("\n" + "="*60)
    print("测试3: 媒体识别服务中的TVDB和Fanart集成")
    print("="*60)
    
    try:
        # 临时设置API key和启用Fanart
        import app.core.config as config_module
        original_tvdb_key = config_module.settings._tvdb_api_key
        original_tvdb_pin = config_module.settings._tvdb_api_pin
        original_fanart_enable = config_module.settings.FANART_ENABLE
        
        # 临时替换
        config_module.settings._tvdb_api_key = TEST_TVDB_API_KEY
        config_module.settings._tvdb_api_pin = TEST_TVDB_API_PIN
        config_module.settings.FANART_ENABLE = True
        
        async with AsyncSessionLocal() as session:
            identification_service = MediaIdentificationService(session)
            
            # 测试电视剧文件
            test_file_path = "/test/The.Wheel.of.Time.S01E01.1080p.mkv"
            test_file_name = "The.Wheel.of.Time.S01E01.1080p.mkv"
            
            print(f"\n[3.1] 识别文件: {test_file_name}")
            result = await identification_service.identify_media(
                file_path=test_file_path,
                file_name=test_file_name
            )
            
            if result and result.get("success"):
                print("[OK] 媒体识别成功")
                print(f"   - 标题: {result.get('title', 'N/A')}")
                print(f"   - TVDB ID: {result.get('tvdb_id', 'N/A')}")
                print(f"   - TMDB ID: {result.get('tmdb_id', 'N/A')}")
                print(f"   - IMDB ID: {result.get('imdb_id', 'N/A')}")
                print(f"   - 来源: {result.get('source', 'N/A')}")
                print(f"   - 置信度: {result.get('confidence', 'N/A')}")
                
                # 检查Fanart图片
                fanart_images = result.get("fanart_images")
                if fanart_images:
                    print("\n[OK] Fanart图片已自动获取")
                    print(f"   - 图片类型: {list(fanart_images.keys())}")
                    if fanart_images.get("poster"):
                        print(f"   - 海报URL: {fanart_images['poster'][:80]}...")
                    if fanart_images.get("backdrop"):
                        print(f"   - 背景图URL: {fanart_images['backdrop'][:80]}...")
                else:
                    print("\n[WARN] 未获取到Fanart图片")
            else:
                print("[WARN] 媒体识别失败或未找到匹配")
        
        # 恢复原始配置
        config_module.settings._tvdb_api_key = original_tvdb_key
        config_module.settings._tvdb_api_pin = original_tvdb_pin
        config_module.settings.FANART_ENABLE = original_fanart_enable
        
    except Exception as e:
        print(f"[ERROR] 媒体识别服务测试失败: {e}")
        logger.exception(e)


async def main():
    """主测试函数"""
    print("="*60)
    print("TVDB和Fanart集成测试（使用临时API Key）")
    print("="*60)
    print(f"TVDB API Key: {TEST_TVDB_API_KEY[:20]}...")
    print("注意: 此测试不会修改系统配置")
    
    # 测试1: TVDB直接测试
    tvdb_id, tvdb_info = await test_tvdb_direct()
    
    # 测试2: Fanart测试
    if tvdb_id:
        fanart_images = await test_fanart_with_tvdb_id(tvdb_id)
    else:
        print("\n[WARN] 跳过Fanart测试（缺少TVDB ID）")
    
    # 测试3: 媒体识别服务集成测试
    await test_media_identification_with_tvdb()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

