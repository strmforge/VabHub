"""
测试Fanart集成和NFO文件写入功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.modules.media_identification.service import MediaIdentificationService
from app.modules.media_renamer.nfo_writer import NFOWriter
from app.modules.fanart import FanartModule
from app.core.database import AsyncSessionLocal
from app.core.config import settings
from loguru import logger
import tempfile
import os


async def test_fanart_integration():
    """测试Fanart集成"""
    print("\n" + "="*60)
    print("测试1: Fanart集成")
    print("="*60)
    
    # 测试1.1: 验证Fanart模块初始化
    print("\n[1.1] 测试Fanart模块初始化...")
    try:
        fanart_module = FanartModule()
        print("[OK] Fanart模块初始化成功")
        print(f"   - API Key: {'已配置' if fanart_module.api_key else '未配置'}")
        print(f"   - Fanart启用: {settings.FANART_ENABLE}")
    except Exception as e:
        print(f"[ERROR] Fanart模块初始化失败: {e}")
        return False
    
    # 测试1.2: 测试Fanart图片获取（电视剧，使用TVDB ID）
    print("\n[1.2] 测试Fanart图片获取（电视剧，TVDB ID: 355730 - The Wheel of Time）...")
    try:
        fanart_images = await fanart_module.obtain_images(
            media_type="tv",
            tmdb_id=None,
            tvdb_id=355730
        )
        
        if fanart_images:
            print("[OK] Fanart图片获取成功")
            print(f"   - 返回的图片类型: {list(fanart_images.keys())}")
            
            # 检查图片数据
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
            print("[WARN] 未获取到Fanart图片（可能是API限制或网络问题）")
    except Exception as e:
        print(f"[ERROR] Fanart图片获取失败: {e}")
        logger.exception(e)
    
    # 测试1.3: 测试缓存机制
    print("\n[1.3] 测试Fanart缓存机制...")
    try:
        import time
        start_time = time.time()
        fanart_images_1 = await fanart_module.obtain_images(
            media_type="tv",
            tvdb_id=355730
        )
        first_request_time = time.time() - start_time
        
        start_time = time.time()
        fanart_images_2 = await fanart_module.obtain_images(
            media_type="tv",
            tvdb_id=355730
        )
        second_request_time = time.time() - start_time
        
        if second_request_time < first_request_time * 0.5:
            print("[OK] 缓存机制工作正常")
            print(f"   - 第一次请求时间: {first_request_time:.3f}秒")
            print(f"   - 第二次请求时间: {second_request_time:.3f}秒")
            print(f"   - 速度提升: {(1 - second_request_time/first_request_time)*100:.1f}%")
        else:
            print("[WARN] 缓存可能未生效（第二次请求时间未明显减少）")
    except Exception as e:
        print(f"[ERROR] 缓存测试失败: {e}")
        logger.exception(e)
    
    # 测试1.4: 测试媒体识别服务中的Fanart集成
    print("\n[1.4] 测试媒体识别服务中的Fanart集成...")
    try:
        async with AsyncSessionLocal() as session:
            identification_service = MediaIdentificationService(session)
            
            # 模拟一个电视剧文件
            test_file_path = "/test/The.Wheel.of.Time.S01E01.1080p.mkv"
            test_file_name = "The.Wheel.of.Time.S01E01.1080p.mkv"
            
            print(f"   识别文件: {test_file_name}")
            result = await identification_service.identify_media(
                file_path=test_file_path,
                file_name=test_file_name
            )
            
            if result and result.get("success"):
                print("[OK] 媒体识别成功")
                print(f"   - 标题: {result.get('title', 'N/A')}")
                print(f"   - TVDB ID: {result.get('tvdb_id', 'N/A')}")
                print(f"   - TMDB ID: {result.get('tmdb_id', 'N/A')}")
                
                fanart_images = result.get("fanart_images")
                if fanart_images:
                    print("[OK] Fanart图片已自动获取")
                    print(f"   - 图片类型: {list(fanart_images.keys())}")
                    if fanart_images.get("poster"):
                        print(f"   - 海报URL: {fanart_images['poster'][:80]}...")
                    if fanart_images.get("backdrop"):
                        print(f"   - 背景图URL: {fanart_images['backdrop'][:80]}...")
                else:
                    print("[WARN] 未获取到Fanart图片（可能是Fanart未启用或识别失败）")
            else:
                print("[WARN] 媒体识别失败或未找到匹配")
    except Exception as e:
        print(f"[ERROR] 媒体识别服务测试失败: {e}")
        logger.exception(e)
    
    return True


async def test_nfo_writing():
    """测试NFO文件写入"""
    print("\n" + "="*60)
    print("测试2: NFO文件写入")
    print("="*60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"\n使用临时目录: {temp_dir}")
    
    try:
        # 测试2.1: 测试电影NFO文件生成
        print("\n[2.1] 测试电影NFO文件生成...")
        try:
            nfo_writer = NFOWriter(format="emby")
            
            movie_file = os.path.join(temp_dir, "Fight.Club.1999.1080p.mkv")
            # 创建模拟文件
            Path(movie_file).touch()
            
            movie_info = {
                "title": "Fight Club",
                "year": 1999,
                "type": "movie",
                "tmdb_id": 550,
                "imdb_id": "tt0137523",
                "overview": "A ticking-time-bomb insomniac and a slippery soap salesman channel primal male aggression into a shocking new form of therapy.",
                "poster_url": "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
                "backdrop_url": "https://image.tmdb.org/t/p/w1280/87hTDiay2N2qWyX4am7XEHkhY41.jpg"
            }
            
            success = nfo_writer.write_nfo(movie_file, movie_info, overwrite=True)
            
            if success:
                nfo_file = Path(movie_file).with_suffix('.nfo')
                if nfo_file.exists():
                    print("[OK] 电影NFO文件生成成功")
                    print(f"   - NFO文件路径: {nfo_file}")
                    
                    # 读取并验证内容
                    nfo_content = nfo_file.read_text(encoding='utf-8')
                    print(f"   - 文件大小: {len(nfo_content)} 字节")
                    
                    # 验证关键字段
                    checks = {
                        "title": "Fight Club" in nfo_content,
                        "year": "1999" in nfo_content,
                        "tmdbid": "550" in nfo_content,
                        "imdbid": "tt0137523" in nfo_content,
                        "plot": "insomniac" in nfo_content.lower(),
                        "poster": "poster" in nfo_content.lower(),
                    }
                    
                    print("   - 内容验证:")
                    for key, passed in checks.items():
                        status = "[OK]" if passed else "[FAIL]"
                        print(f"     {status} {key}: {passed}")
                else:
                    print("[ERROR] NFO文件未生成")
            else:
                print("[ERROR] NFO文件写入失败")
        except Exception as e:
            print(f"[ERROR] 电影NFO测试失败: {e}")
            logger.exception(e)
        
        # 测试2.2: 测试电视剧单集NFO文件生成
        print("\n[2.2] 测试电视剧单集NFO文件生成...")
        try:
            tv_episode_file = os.path.join(temp_dir, "The.Wheel.of.Time.S01E01.1080p.mkv")
            Path(tv_episode_file).touch()
            
            tv_episode_info = {
                "title": "Leavetaking",
                "year": 2021,
                "type": "tv",
                "season": 1,
                "episode": 1,
                "tmdb_id": 71914,
                "tvdb_id": 355730,
                "imdb_id": "tt7462410",
                "overview": "Moiraine arrives in the Two Rivers and begins her search for the Dragon Reborn.",
                "poster_url": "https://image.tmdb.org/t/p/w500/...",
                "backdrop_url": "https://image.tmdb.org/t/p/w1280/..."
            }
            
            success = nfo_writer.write_nfo(tv_episode_file, tv_episode_info, overwrite=True)
            
            if success:
                nfo_file = Path(tv_episode_file).with_suffix('.nfo')
                if nfo_file.exists():
                    print("[OK] 电视剧单集NFO文件生成成功")
                    print(f"   - NFO文件路径: {nfo_file}")
                    
                    nfo_content = nfo_file.read_text(encoding='utf-8')
                    
                    # 验证关键字段
                    checks = {
                        "episodedetails": "<episodedetails" in nfo_content,
                        "title": "Leavetaking" in nfo_content,
                        "season": "<season>1</season>" in nfo_content,
                        "episode": "<episode>1</episode>" in nfo_content,
                        "tvdbid": "355730" in nfo_content,
                        "tmdbid": "71914" in nfo_content,
                        "imdbid": "tt7462410" in nfo_content,
                    }
                    
                    print("   - 内容验证:")
                    for key, passed in checks.items():
                        status = "[OK]" if passed else "[FAIL]"
                        print(f"     {status} {key}: {passed}")
                else:
                    print("[ERROR] NFO文件未生成")
            else:
                print("[ERROR] NFO文件写入失败")
        except Exception as e:
            print(f"[ERROR] 电视剧单集NFO测试失败: {e}")
            logger.exception(e)
        
        # 测试2.3: 测试电视剧整剧NFO文件生成
        print("\n[2.3] 测试电视剧整剧NFO文件生成...")
        try:
            tv_show_file = os.path.join(temp_dir, "The.Wheel.of.Time.2021.mkv")
            Path(tv_show_file).touch()
            
            tv_show_info = {
                "title": "The Wheel of Time",
                "year": 2021,
                "type": "tv",
                "tmdb_id": 71914,
                "tvdb_id": 355730,
                "imdb_id": "tt7462410",
                "overview": "Set in a high fantasy world where magic exists, but only some can access it...",
                "poster_url": "https://image.tmdb.org/t/p/w500/...",
                "backdrop_url": "https://image.tmdb.org/t/p/w1280/..."
            }
            
            success = nfo_writer.write_nfo(tv_show_file, tv_show_info, overwrite=True)
            
            if success:
                nfo_file = Path(tv_show_file).with_suffix('.nfo')
                if nfo_file.exists():
                    print("[OK] 电视剧整剧NFO文件生成成功")
                    print(f"   - NFO文件路径: {nfo_file}")
                    
                    nfo_content = nfo_file.read_text(encoding='utf-8')
                    
                    # 验证关键字段
                    checks = {
                        "tvshow": "<tvshow" in nfo_content,
                        "title": "The Wheel of Time" in nfo_content,
                        "year": "2021" in nfo_content,
                        "tvdbid": "355730" in nfo_content,
                        "tmdbid": "71914" in nfo_content,
                    }
                    
                    print("   - 内容验证:")
                    for key, passed in checks.items():
                        status = "[OK]" if passed else "[FAIL]"
                        print(f"     {status} {key}: {passed}")
                else:
                    print("[ERROR] NFO文件未生成")
            else:
                print("[ERROR] NFO文件写入失败")
        except Exception as e:
            print(f"[ERROR] 电视剧整剧NFO测试失败: {e}")
            logger.exception(e)
        
        # 测试2.4: 测试不同格式（Jellyfin/Plex）
        print("\n[2.4] 测试不同NFO格式...")
        for format_name in ["emby", "jellyfin", "plex"]:
            try:
                test_file = os.path.join(temp_dir, f"test_{format_name}.mkv")
                Path(test_file).touch()
                
                writer = NFOWriter(format=format_name)
                success = writer.write_nfo(test_file, movie_info, overwrite=True)
                
                if success:
                    nfo_file = Path(test_file).with_suffix('.nfo')
                    if nfo_file.exists():
                        print(f"[OK] {format_name.upper()}格式NFO生成成功")
                    else:
                        print(f"[ERROR] {format_name.upper()}格式NFO文件未生成")
                else:
                    print(f"[ERROR] {format_name.upper()}格式NFO写入失败")
            except Exception as e:
                print(f"[ERROR] {format_name.upper()}格式测试失败: {e}")
        
    finally:
        # 清理临时文件
        import shutil
        try:
            shutil.rmtree(temp_dir)
            print(f"\n[OK] 临时目录已清理: {temp_dir}")
        except:
            pass
    
    return True


async def main():
    """主测试函数"""
    print("="*60)
    print("Fanart集成和NFO文件写入功能测试")
    print("="*60)
    
    # 测试Fanart集成
    await test_fanart_integration()
    
    # 测试NFO文件写入
    await test_nfo_writing()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

