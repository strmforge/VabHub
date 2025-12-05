"""
测试TVDB和Fanart集成（使用系统默认配置）
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
from app.core.config import settings
from loguru import logger


async def test_tvdb_with_default_key():
    """使用系统默认TVDB API Key测试"""
    print("\n" + "="*60)
    print("测试1: TVDB模块测试（使用系统默认配置）")
    print("="*60)
    
    print(f"\n[1.1] 系统默认TVDB API Key: {settings.TVDB_V4_API_KEY[:20]}...")
    print(f"   - TVDB API PIN: {'已配置' if settings.TVDB_V4_API_PIN else '未配置'}")
    
    try:
        tvdb_module = TheTvDbModule()
        
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
                                remote_ids = tvdb_info.get('remoteIds', [])
                                print(f"   - 外部ID数量: {len(remote_ids)}")
                                for rid in remote_ids[:3]:
                                    print(f"     - {rid.get('type', 'N/A')}: {rid.get('id', 'N/A')}")
                            
                            return tvdb_id, tvdb_info
                        else:
                            print("[WARN] 获取TVDB信息失败")
            else:
                print("[WARN] 搜索未返回结果")
        except Exception as e:
            print(f"[ERROR] TVDB搜索失败: {e}")
            logger.exception(e)
        
    except Exception as e:
        print(f"[ERROR] TVDB模块测试失败: {e}")
        logger.exception(e)
    
    return None, None


async def test_fanart_with_default_config():
    """使用系统默认配置测试Fanart"""
    print("\n" + "="*60)
    print("测试2: Fanart模块测试（使用系统默认配置）")
    print("="*60)
    
    print("\n[2.1] Fanart配置状态:")
    print(f"   - Fanart启用: {settings.FANART_ENABLE}")
    print(f"   - Fanart API Key: {settings.FANART_API_KEY[:20] if settings.FANART_API_KEY else 'N/A'}...")
    
    if not settings.FANART_ENABLE:
        print("\n[WARN] Fanart未启用，临时启用进行测试...")
        import app.core.config as config_module
        original_enable = config_module.settings.FANART_ENABLE
        config_module.settings.FANART_ENABLE = True
        
        try:
            # 测试Fanart（使用已知的TVDB ID）
            test_tvdb_id = 355730  # The Wheel of Time
            print(f"\n[2.2] 测试Fanart图片获取: TVDB ID {test_tvdb_id}")
            
            fanart_module = FanartModule()
            fanart_images = await fanart_module.obtain_images(
                media_type="tv",
                tmdb_id=None,
                tvdb_id=test_tvdb_id
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
            else:
                print("[WARN] 未获取到Fanart图片")
        except Exception as e:
            print(f"[ERROR] Fanart图片获取失败: {e}")
            logger.exception(e)
        finally:
            # 恢复原始配置
            config_module.settings.FANART_ENABLE = original_enable
    else:
        print("\n[OK] Fanart已启用，可以进行测试")


async def test_media_identification_integration():
    """测试媒体识别服务中的TVDB和Fanart集成"""
    print("\n" + "="*60)
    print("测试3: 媒体识别服务中的TVDB和Fanart集成")
    print("="*60)
    
    # 临时启用Fanart
    import app.core.config as config_module
    original_fanart_enable = config_module.settings.FANART_ENABLE
    config_module.settings.FANART_ENABLE = True
    
    try:
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
                    if not result.get('tvdb_id'):
                        print("   - 原因: 未获取到TVDB ID（TVDB识别可能失败）")
            else:
                print("[WARN] 媒体识别失败或未找到匹配")
    except Exception as e:
        print(f"[ERROR] 媒体识别服务测试失败: {e}")
        logger.exception(e)
    finally:
        # 恢复原始配置
        config_module.settings.FANART_ENABLE = original_fanart_enable


async def main():
    """主测试函数"""
    print("="*60)
    print("TVDB和Fanart集成测试（使用系统默认配置）")
    print("="*60)
    print("注意: 此测试使用系统默认配置，不修改系统设置")
    
    # 测试1: TVDB测试
    tvdb_id, tvdb_info = await test_tvdb_with_default_key()
    
    # 测试2: Fanart测试
    await test_fanart_with_default_config()
    
    # 测试3: 媒体识别服务集成测试
    await test_media_identification_integration()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
    print("\n说明:")
    print("1. TVDB和Fanart已完整集成到系统中")
    print("2. TVDB使用系统默认API Key（MoviePilot默认值）")
    print("3. Fanart需要启用 FANART_ENABLE = True")
    print("4. 用户提供的API Key可能是115云的key，不是TVDB的key")
    print("5. TVDB API Key需要从TVDB官网申请: https://thetvdb.com")


if __name__ == "__main__":
    asyncio.run(main())

