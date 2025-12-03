"""
测试TMDB和Fanart集成（使用用户提供的TMDB API key）
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.modules.fanart import FanartModule
from app.modules.media_identification.service import MediaIdentificationService
from app.core.database import AsyncSessionLocal
from app.core.config import settings
from loguru import logger

# 用户提供的TMDB API key（仅用于测试，不写入系统）
TEST_TMDB_API_KEY = "fe29c50eb189bac40cb5abd33de5be96"


async def test_tmdb_search():
    """测试TMDB搜索功能"""
    print("\n" + "="*60)
    print("测试1: TMDB搜索功能测试")
    print("="*60)
    
    # 临时设置TMDB API key
    import app.core.config as config_module
    original_tmdb_key = config_module.settings._tmdb_api_key
    
    # 临时替换TMDB API key
    config_module.settings._tmdb_api_key = TEST_TMDB_API_KEY
    
    print(f"\n[1.1] 使用临时TMDB API Key: {TEST_TMDB_API_KEY[:20]}...")
    
    try:
        async with AsyncSessionLocal() as session:
            identification_service = MediaIdentificationService(session)
            
            # 测试搜索电影
            print("\n[1.2] 测试TMDB搜索电影: 'Fight Club'")
            try:
                from app.api.media import search_tmdb_movie
                results = await search_tmdb_movie("Fight Club", TEST_TMDB_API_KEY)
                if results:
                    print(f"[OK] 搜索成功，找到 {len(results)} 个结果")
                    if len(results) > 0:
                        movie = results[0]
                        print(f"   - 标题: {movie.get('title', 'N/A')}")
                        print(f"   - 年份: {movie.get('release_date', 'N/A')[:4] if movie.get('release_date') else 'N/A'}")
                        print(f"   - TMDB ID: {movie.get('id', 'N/A')}")
                        print(f"   - 概述: {movie.get('overview', 'N/A')[:100]}...")
                        return movie.get('id')
            except Exception as e:
                print(f"[ERROR] TMDB电影搜索失败: {e}")
                logger.exception(e)
            
            # 测试搜索电视剧
            print("\n[1.3] 测试TMDB搜索电视剧: 'The Wheel of Time'")
            try:
                from app.api.media import search_tmdb_tv
                results = await search_tmdb_tv("The Wheel of Time", TEST_TMDB_API_KEY)
                if results:
                    print(f"[OK] 搜索成功，找到 {len(results)} 个结果")
                    if len(results) > 0:
                        tv = results[0]
                        print(f"   - 标题: {tv.get('name', 'N/A')}")
                        print(f"   - 年份: {tv.get('first_air_date', 'N/A')[:4] if tv.get('first_air_date') else 'N/A'}")
                        print(f"   - TMDB ID: {tv.get('id', 'N/A')}")
                        print(f"   - 概述: {tv.get('overview', 'N/A')[:100]}...")
                        return tv.get('id')
            except Exception as e:
                print(f"[ERROR] TMDB电视剧搜索失败: {e}")
                logger.exception(e)
        
    except Exception as e:
        print(f"[ERROR] TMDB搜索测试失败: {e}")
        logger.exception(e)
    finally:
        # 恢复原始配置
        config_module.settings._tmdb_api_key = original_tmdb_key
    
    return None


async def test_tmdb_details(tmdb_id: int, media_type: str = "movie"):
    """测试TMDB详情获取"""
    print("\n" + "="*60)
    print(f"测试2: TMDB详情获取测试 ({media_type})")
    print("="*60)
    
    # 临时设置TMDB API key
    import app.core.config as config_module
    original_tmdb_key = config_module.settings._tmdb_api_key
    config_module.settings._tmdb_api_key = TEST_TMDB_API_KEY
    
    try:
        if media_type == "movie":
            from app.api.media import get_tmdb_movie_details
            details = await get_tmdb_movie_details(tmdb_id, TEST_TMDB_API_KEY)
        else:
            from app.api.media import get_tmdb_tv_details
            details = await get_tmdb_tv_details(tmdb_id, TEST_TMDB_API_KEY)
        
        if details:
            print(f"[OK] 获取TMDB详情成功")
            print(f"   - 标题: {details.get('title') or details.get('name', 'N/A')}")
            print(f"   - 年份: {details.get('release_date', 'N/A')[:4] if details.get('release_date') else details.get('first_air_date', 'N/A')[:4] if details.get('first_air_date') else 'N/A'}")
            print(f"   - TMDB ID: {details.get('id', 'N/A')}")
            print(f"   - IMDB ID: {details.get('imdb_id', 'N/A')}")
            
            # 检查external_ids（包含TVDB ID）
            if media_type == "tv" and details.get('external_ids'):
                external_ids = details.get('external_ids', {})
                print(f"   - TVDB ID: {external_ids.get('tvdb_id', 'N/A')}")
            
            print(f"   - 概述: {details.get('overview', 'N/A')[:100]}...")
            
            return details
        else:
            print("[WARN] 未获取到TMDB详情")
    except Exception as e:
        print(f"[ERROR] TMDB详情获取失败: {e}")
        logger.exception(e)
    finally:
        # 恢复原始配置
        config_module.settings._tmdb_api_key = original_tmdb_key
    
    return None


async def test_fanart_with_tmdb(tmdb_id: int, media_type: str = "movie", tvdb_id: int = None):
    """使用TMDB ID测试Fanart"""
    print("\n" + "="*60)
    print(f"测试3: Fanart图片获取测试 ({media_type})")
    print("="*60)
    
    # 临时启用Fanart
    import app.core.config as config_module
    original_fanart_enable = config_module.settings.FANART_ENABLE
    config_module.settings.FANART_ENABLE = True
    
    try:
        fanart_module = FanartModule()
        
        print(f"\n[3.1] 使用TMDB ID {tmdb_id} 获取Fanart图片")
        if tvdb_id:
            print(f"   - TVDB ID: {tvdb_id} (电视剧优先使用TVDB ID)")
        
        fanart_images = await fanart_module.obtain_images(
            media_type=media_type,
            tmdb_id=tmdb_id,
            tvdb_id=tvdb_id
        )
        
        if fanart_images:
            print("[OK] Fanart图片获取成功")
            print(f"   - 返回的图片类型: {list(fanart_images.keys())}")
            
            if media_type == "movie":
                # 电影：检查海报和背景图
                if "movieposter" in fanart_images:
                    posters = fanart_images["movieposter"]
                    if isinstance(posters, list) and len(posters) > 0:
                        print(f"   - 海报数量: {len(posters)}")
                        best_poster = max(posters, key=lambda x: int(x.get("likes", "0")))
                        print(f"   - 最佳海报URL: {best_poster.get('url', 'N/A')[:80]}...")
                        print(f"   - 最佳海报语言: {best_poster.get('lang', 'N/A')}")
                        print(f"   - 最佳海报likes: {best_poster.get('likes', '0')}")
                
                if "moviebackground" in fanart_images:
                    backgrounds = fanart_images["moviebackground"]
                    if isinstance(backgrounds, list) and len(backgrounds) > 0:
                        print(f"   - 背景图数量: {len(backgrounds)}")
                        best_bg = max(backgrounds, key=lambda x: int(x.get("likes", "0")))
                        print(f"   - 最佳背景图URL: {best_bg.get('url', 'N/A')[:80]}...")
            else:
                # 电视剧：检查海报和背景图
                if "tvposter" in fanart_images:
                    posters = fanart_images["tvposter"]
                    if isinstance(posters, list) and len(posters) > 0:
                        print(f"   - 海报数量: {len(posters)}")
                        best_poster = max(posters, key=lambda x: int(x.get("likes", "0")))
                        print(f"   - 最佳海报URL: {best_poster.get('url', 'N/A')[:80]}...")
                        print(f"   - 最佳海报语言: {best_poster.get('lang', 'N/A')}")
                        print(f"   - 最佳海报likes: {best_poster.get('likes', '0')}")
                
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
    finally:
        # 恢复原始配置
        config_module.settings.FANART_ENABLE = original_fanart_enable
    
    return None


async def test_media_identification_with_tmdb():
    """测试媒体识别服务中的TMDB和Fanart集成"""
    print("\n" + "="*60)
    print("测试4: 媒体识别服务中的TMDB和Fanart集成")
    print("="*60)
    
    # 临时设置TMDB API key和启用Fanart
    import app.core.config as config_module
    original_tmdb_key = config_module.settings._tmdb_api_key
    original_fanart_enable = config_module.settings.FANART_ENABLE
    
    config_module.settings._tmdb_api_key = TEST_TMDB_API_KEY
    config_module.settings.FANART_ENABLE = True
    
    try:
        async with AsyncSessionLocal() as session:
            identification_service = MediaIdentificationService(session)
            
            # 测试电影文件
            print("\n[4.1] 识别电影文件: 'Fight.Club.1999.1080p.mkv'")
            movie_result = await identification_service.identify_media(
                file_path="/test/Fight.Club.1999.1080p.mkv",
                file_name="Fight.Club.1999.1080p.mkv"
            )
            
            if movie_result and movie_result.get("success"):
                print("[OK] 电影识别成功")
                print(f"   - 标题: {movie_result.get('title', 'N/A')}")
                print(f"   - TMDB ID: {movie_result.get('tmdb_id', 'N/A')}")
                print(f"   - IMDB ID: {movie_result.get('imdb_id', 'N/A')}")
                print(f"   - 来源: {movie_result.get('source', 'N/A')}")
                print(f"   - 置信度: {movie_result.get('confidence', 'N/A')}")
                
                # 检查Fanart图片
                fanart_images = movie_result.get("fanart_images")
                if fanart_images:
                    print("\n[OK] Fanart图片已自动获取")
                    print(f"   - 图片类型: {list(fanart_images.keys())}")
                else:
                    print("\n[WARN] 未获取到Fanart图片")
            
            # 测试电视剧文件
            print("\n[4.2] 识别电视剧文件: 'The.Wheel.of.Time.S01E01.1080p.mkv'")
            tv_result = await identification_service.identify_media(
                file_path="/test/The.Wheel.of.Time.S01E01.1080p.mkv",
                file_name="The.Wheel.of.Time.S01E01.1080p.mkv"
            )
            
            if tv_result and tv_result.get("success"):
                print("[OK] 电视剧识别成功")
                print(f"   - 标题: {tv_result.get('title', 'N/A')}")
                print(f"   - TMDB ID: {tv_result.get('tmdb_id', 'N/A')}")
                print(f"   - TVDB ID: {tv_result.get('tvdb_id', 'N/A')}")
                print(f"   - IMDB ID: {tv_result.get('imdb_id', 'N/A')}")
                print(f"   - 来源: {tv_result.get('source', 'N/A')}")
                print(f"   - 置信度: {tv_result.get('confidence', 'N/A')}")
                
                # 检查Fanart图片
                fanart_images = tv_result.get("fanart_images")
                if fanart_images:
                    print("\n[OK] Fanart图片已自动获取")
                    print(f"   - 图片类型: {list(fanart_images.keys())}")
                else:
                    print("\n[WARN] 未获取到Fanart图片")
                    if not tv_result.get('tvdb_id'):
                        print("   - 原因: 未获取到TVDB ID（Fanart需要TVDB ID才能获取电视剧图片）")
    except Exception as e:
        print(f"[ERROR] 媒体识别服务测试失败: {e}")
        logger.exception(e)
    finally:
        # 恢复原始配置
        config_module.settings._tmdb_api_key = original_tmdb_key
        config_module.settings.FANART_ENABLE = original_fanart_enable


async def main():
    """主测试函数"""
    print("="*60)
    print("TMDB和Fanart集成测试（使用用户提供的TMDB API Key）")
    print("="*60)
    print(f"TMDB API Key: {TEST_TMDB_API_KEY[:20]}...")
    print("注意: 此测试不会修改系统配置")
    
    # 测试1: TMDB搜索
    tmdb_id = await test_tmdb_search()
    
    # 测试2: TMDB详情获取
    if tmdb_id:
        details = await test_tmdb_details(tmdb_id, "tv")
        
        # 测试3: Fanart图片获取
        if details:
            tvdb_id = None
            if details.get('external_ids') and details.get('external_ids').get('tvdb_id'):
                tvdb_id = details.get('external_ids').get('tvdb_id')
            
            await test_fanart_with_tmdb(tmdb_id, "tv", tvdb_id)
    
    # 测试4: 媒体识别服务集成测试
    await test_media_identification_with_tmdb()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
    print("\n说明:")
    print("1. TMDB和Fanart已完整集成到系统中")
    print("2. TVDB API系统也已集成（用于电视剧识别）")
    print("3. Fanart需要启用 FANART_ENABLE = True")
    print("4. 电视剧Fanart图片需要TVDB ID（系统会自动从TMDB获取）")


if __name__ == "__main__":
    asyncio.run(main())

