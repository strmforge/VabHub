"""
测试豆瓣回退机制
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.modules.media_identification.service import MediaIdentificationService
from app.core.database import AsyncSessionLocal
from loguru import logger


async def test_douban_fallback():
    """测试豆瓣回退机制"""
    print("\n" + "="*60)
    print("豆瓣回退机制测试")
    print("="*60)
    
    async with AsyncSessionLocal() as session:
        service = MediaIdentificationService(session)
        
        # 测试用例1：中文电影（TMDB可能失败，豆瓣应该成功）
        print("\n[1] 测试中文电影识别（豆瓣回退）...")
        test_cases = [
            {
                "name": "中文电影",
                "file_path": "/test/肖申克的救赎 (1994).mkv",
                "expected_source": ["tmdb", "douban"]
            },
            {
                "name": "中文电视剧",
                "file_path": "/test/权力的游戏 S01E01.mkv",
                "expected_source": ["tmdb", "douban", "tvdb"]
            },
            {
                "name": "英文电影",
                "file_path": "/test/The Matrix (1999).mkv",
                "expected_source": ["tmdb"]
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n测试用例 {i}: {test_case['name']}")
            print(f"文件路径: {test_case['file_path']}")
            
            try:
                result = await service.identify_media(
                    file_path=test_case['file_path'],
                    file_name=Path(test_case['file_path']).name
                )
                
                if result and result.get("success"):
                    source = result.get("source", "unknown")
                    title = result.get("title", "未知")
                    year = result.get("year", "未知")
                    
                    print(f"✅ 识别成功")
                    print(f"   标题: {title}")
                    print(f"   年份: {year}")
                    print(f"   数据源: {source}")
                    
                    # 检查数据源是否符合预期
                    if source in test_case['expected_source']:
                        print(f"   ✅ 数据源符合预期: {source}")
                    else:
                        print(f"   ⚠️  数据源不符合预期: {source} (期望: {test_case['expected_source']})")
                    
                    # 如果是豆瓣回退，检查是否有豆瓣ID
                    if source == "douban":
                        douban_id = result.get("douban_id")
                        if douban_id:
                            print(f"   ✅ 豆瓣ID: {douban_id}")
                        else:
                            print(f"   ⚠️  缺少豆瓣ID")
                        
                        rating = result.get("rating")
                        if rating:
                            print(f"   [OK] 豆瓣评分: {rating}")
                else:
                    error = result.get("error", "未知错误") if result else "识别失败"
                    print(f"[FAIL] 识别失败: {error}")
                    
            except Exception as e:
                logger.error(f"测试用例 {i} 失败: {e}")
                print(f"[FAIL] 测试失败: {e}")
        
        print("\n" + "="*60)
        print("[OK] 豆瓣回退机制测试完成")
        print("="*60)
        print("\n注意: 实际测试结果取决于TMDB API Key配置和网络连接")
        print("如果TMDB API Key未配置，将直接使用豆瓣回退")


if __name__ == "__main__":
    try:
        asyncio.run(test_douban_fallback())
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

