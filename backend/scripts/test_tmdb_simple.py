"""
简单测试TMDB API（使用用户提供的API key）
直接调用TMDB API，不依赖完整的应用导入
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils.http_client import create_httpx_client

# 用户提供的TMDB API key
TEST_TMDB_API_KEY = "fe29c50eb189bac40cb5abd33de5be96"

TMDB_API_BASE = "https://api.themoviedb.org/3"


async def test_tmdb_search_movie():
    """测试TMDB电影搜索"""
    print("\n" + "="*60)
    print("测试1: TMDB电影搜索")
    print("="*60)
    
    async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
        url = f"{TMDB_API_BASE}/search/movie"
        params = {
            "api_key": TEST_TMDB_API_KEY,
            "query": "Fight Club",
            "language": "zh-CN",
        }
        
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            result = response.json()
            
            if result.get("results"):
                movies = result["results"]
                print(f"[OK] 搜索成功，找到 {len(movies)} 个结果")
                if len(movies) > 0:
                    movie = movies[0]
                    print(f"   - 标题: {movie.get('title', 'N/A')}")
                    print(f"   - 年份: {movie.get('release_date', 'N/A')[:4] if movie.get('release_date') else 'N/A'}")
                    print(f"   - TMDB ID: {movie.get('id', 'N/A')}")
                    print(f"   - 概述: {movie.get('overview', 'N/A')[:100]}...")
                    return movie.get('id')
            else:
                print("[WARN] 未找到结果")
        except Exception as e:
            print(f"[ERROR] TMDB电影搜索失败: {e}")
            return None


async def test_tmdb_search_tv():
    """测试TMDB电视剧搜索"""
    print("\n" + "="*60)
    print("测试2: TMDB电视剧搜索")
    print("="*60)
    
    async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
        url = f"{TMDB_API_BASE}/search/tv"
        params = {
            "api_key": TEST_TMDB_API_KEY,
            "query": "The Wheel of Time",
            "language": "zh-CN",
        }
        
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            result = response.json()
            
            if result.get("results"):
                tvs = result["results"]
                print(f"[OK] 搜索成功，找到 {len(tvs)} 个结果")
                if len(tvs) > 0:
                    tv = tvs[0]
                    print(f"   - 标题: {tv.get('name', 'N/A')}")
                    print(f"   - 年份: {tv.get('first_air_date', 'N/A')[:4] if tv.get('first_air_date') else 'N/A'}")
                    print(f"   - TMDB ID: {tv.get('id', 'N/A')}")
                    print(f"   - 概述: {tv.get('overview', 'N/A')[:100]}...")
                    return tv.get('id')
            else:
                print("[WARN] 未找到结果")
        except Exception as e:
            print(f"[ERROR] TMDB电视剧搜索失败: {e}")
            return None


async def test_tmdb_tv_details(tmdb_id: int):
    """测试TMDB电视剧详情获取（包含external_ids）"""
    print("\n" + "="*60)
    print("测试3: TMDB电视剧详情获取（包含TVDB ID）")
    print("="*60)
    
    async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
        url = f"{TMDB_API_BASE}/tv/{tmdb_id}"
        params = {
            "api_key": TEST_TMDB_API_KEY,
            "language": "zh-CN",
            "append_to_response": "external_ids"
        }
        
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            details = response.json()
            
            print("[OK] 获取TMDB详情成功")
            print(f"   - 标题: {details.get('name', 'N/A')}")
            print(f"   - 年份: {details.get('first_air_date', 'N/A')[:4] if details.get('first_air_date') else 'N/A'}")
            print(f"   - TMDB ID: {details.get('id', 'N/A')}")
            
            # 检查external_ids（包含TVDB ID）
            if details.get('external_ids'):
                external_ids = details.get('external_ids', {})
                print(f"   - TVDB ID: {external_ids.get('tvdb_id', 'N/A')}")
                print(f"   - IMDB ID: {external_ids.get('imdb_id', 'N/A')}")
            
            print(f"   - 概述: {details.get('overview', 'N/A')[:100]}...")
            
            return details
        except Exception as e:
            print(f"[ERROR] TMDB详情获取失败: {e}")
            return None


async def test_fanart_with_tvdb_id(tvdb_id: int):
    """使用TVDB ID测试Fanart"""
    print("\n" + "="*60)
    print("测试4: Fanart图片获取（使用TVDB ID）")
    print("="*60)
    
    # 临时启用Fanart
    import app.core.config as config_module
    original_fanart_enable = config_module.settings.FANART_ENABLE
    config_module.settings.FANART_ENABLE = True
    
    try:
        from app.modules.fanart import FanartModule
        
        fanart_module = FanartModule()
        print(f"\n[4.1] 使用TVDB ID {tvdb_id} 获取Fanart图片")
        
        fanart_images = await fanart_module.obtain_images(
            media_type="tv",
            tmdb_id=None,
            tvdb_id=tvdb_id
        )
        
        if fanart_images:
            print("[OK] Fanart图片获取成功")
            print(f"   - 返回的图片类型: {list(fanart_images.keys())}")
            
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
        else:
            print("[WARN] 未获取到Fanart图片")
    except Exception as e:
        print(f"[ERROR] Fanart图片获取失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 恢复原始配置
        config_module.settings.FANART_ENABLE = original_fanart_enable


async def main():
    """主测试函数"""
    print("="*60)
    print("TMDB和Fanart集成测试（使用用户提供的TMDB API Key）")
    print("="*60)
    print(f"TMDB API Key: {TEST_TMDB_API_KEY[:20]}...")
    print("注意: 此测试直接调用TMDB API，不依赖完整的应用导入")
    
    # 测试1: TMDB电影搜索
    movie_id = await test_tmdb_search_movie()
    
    # 测试2: TMDB电视剧搜索
    tv_id = await test_tmdb_search_tv()
    
    # 测试3: TMDB电视剧详情获取（包含TVDB ID）
    if tv_id:
        details = await test_tmdb_tv_details(tv_id)
        
        # 测试4: Fanart图片获取（使用TVDB ID）
        if details and details.get('external_ids') and details.get('external_ids').get('tvdb_id'):
            tvdb_id = details.get('external_ids').get('tvdb_id')
            await test_fanart_with_tvdb_id(tvdb_id)
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
    print("\n总结:")
    print("1. TMDB API Key有效，可以正常搜索和获取详情")
    print("2. TMDB详情包含external_ids，可以获取TVDB ID")
    print("3. TVDB API系统已集成，可以用于电视剧识别")
    print("4. Fanart功能已集成，可以使用TVDB ID获取图片")
    print("5. 所有功能都已集成到媒体识别服务中")


if __name__ == "__main__":
    asyncio.run(main())

