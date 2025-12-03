"""
架构组件测试脚本
测试缓存系统、健康检查等新架构组件
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.cache import get_cache, cached
from app.core.health import get_health_checker
from loguru import logger


async def test_cache_system():
    """测试缓存系统"""
    print("\n" + "="*50)
    print("测试缓存系统")
    print("="*50)
    
    cache = get_cache()
    
    # 测试1: 基本设置和获取
    print("\n1. 测试基本设置和获取...")
    await cache.set("test_key", "test_value", ttl=60)
    value = await cache.get("test_key")
    assert value == "test_value", f"缓存获取失败: 期望 'test_value', 得到 '{value}'"
    print("   ✅ 基本设置和获取测试通过")
    
    # 测试2: 缓存过期
    print("\n2. 测试缓存过期...")
    await cache.set("test_expire", "expire_value", ttl=1)
    await asyncio.sleep(2)
    value = await cache.get("test_expire")
    assert value is None, f"缓存未过期: 期望 None, 得到 '{value}'"
    print("   ✅ 缓存过期测试通过")
    
    # 测试3: 键生成器
    print("\n3. 测试键生成器...")
    key1 = cache.generate_key("test", "arg1", "arg2", param1="value1", param2="value2")
    key2 = cache.generate_key("test", "arg1", "arg2", param1="value1", param2="value2")
    assert key1 == key2, "相同参数应生成相同键"
    print(f"   生成的键: {key1}")
    print("   ✅ 键生成器测试通过")
    
    # 测试4: 缓存装饰器
    print("\n4. 测试缓存装饰器...")
    call_count = 0
    
    @cached(ttl=60, key_prefix="test_decorator")
    async def test_function(arg1: str, arg2: int):
        nonlocal call_count
        call_count += 1
        return f"result_{arg1}_{arg2}"
    
    result1 = await test_function("test", 123)
    result2 = await test_function("test", 123)
    assert call_count == 1, f"函数应该只调用一次，实际调用 {call_count} 次"
    assert result1 == result2 == "result_test_123", "缓存装饰器结果不正确"
    print("   ✅ 缓存装饰器测试通过")
    
    # 测试5: 缓存删除
    print("\n5. 测试缓存删除...")
    await cache.set("test_delete", "delete_value", ttl=60)
    await cache.delete("test_delete")
    value = await cache.get("test_delete")
    assert value is None, "缓存删除失败"
    print("   ✅ 缓存删除测试通过")
    
    print("\n✅ 缓存系统测试全部通过！")


async def test_health_checker():
    """测试健康检查系统"""
    print("\n" + "="*50)
    print("测试健康检查系统")
    print("="*50)
    
    health_checker = get_health_checker()
    
    # 测试1: 完整健康检查
    print("\n1. 测试完整健康检查...")
    result = await health_checker.check_all()
    print(f"   整体状态: {result['status']}")
    print(f"   检查项数量: {len(result['checks'])}")
    for check_name, check_result in result['checks'].items():
        status = check_result.get('status', 'unknown')
        message = check_result.get('message', '')
        print(f"   - {check_name}: {status} - {message}")
    print("   ✅ 完整健康检查测试通过")
    
    # 测试2: 单项健康检查
    print("\n2. 测试单项健康检查...")
    db_check = await health_checker.check("database")
    if db_check:
        print(f"   数据库检查: {db_check['status']} - {db_check['message']}")
    cache_check = await health_checker.check("cache")
    if cache_check:
        print(f"   缓存检查: {cache_check['status']} - {cache_check['message']}")
    print("   ✅ 单项健康检查测试通过")
    
    # 测试3: 注册自定义检查
    print("\n3. 测试自定义健康检查...")
    
    async def custom_check():
        return {
            "status": "healthy",
            "message": "自定义检查通过"
        }
    
    health_checker.register_check("custom", custom_check)
    custom_result = await health_checker.check("custom")
    assert custom_result is not None, "自定义检查未注册"
    assert custom_result['status'] == "healthy", "自定义检查结果不正确"
    print("   ✅ 自定义健康检查测试通过")
    
    print("\n✅ 健康检查系统测试全部通过！")


async def test_cache_integration():
    """测试缓存集成（模拟实际使用场景）"""
    print("\n" + "="*50)
    print("测试缓存集成")
    print("="*50)
    
    cache = get_cache()
    
    # 模拟Media API缓存
    print("\n1. 模拟Media API缓存...")
    media_data = {
        "id": 12345,
        "title": "测试电影",
        "year": 2024
    }
    cache_key = cache.generate_key("tmdb_movie_details", tmdb_id=12345)
    await cache.set(cache_key, media_data, ttl=86400)
    cached_media = await cache.get(cache_key)
    assert cached_media == media_data, "Media API缓存失败"
    print("   ✅ Media API缓存测试通过")
    
    # 模拟Music Service缓存
    print("\n2. 模拟Music Service缓存...")
    music_results = [
        {"id": "1", "title": "测试歌曲1", "artist": "测试艺术家1"},
        {"id": "2", "title": "测试歌曲2", "artist": "测试艺术家2"}
    ]
    cache_key = cache.generate_key(
        "music_search",
        query="测试",
        search_type="all",
        platform="all",
        limit=20
    )
    await cache.set(cache_key, music_results, ttl=1800)
    cached_music = await cache.get(cache_key)
    assert cached_music == music_results, "Music Service缓存失败"
    print("   ✅ Music Service缓存测试通过")
    
    # 模拟Dashboard Service缓存
    print("\n3. 模拟Dashboard Service缓存...")
    dashboard_data = {
        "system_stats": {"cpu": 50.0, "memory": 60.0},
        "media_stats": {"total": 100},
        "download_stats": {"active": 5}
    }
    cache_key = cache.generate_key("dashboard_data")
    await cache.set(cache_key, dashboard_data, ttl=30)
    cached_dashboard = await cache.get(cache_key)
    assert cached_dashboard == dashboard_data, "Dashboard Service缓存失败"
    print("   ✅ Dashboard Service缓存测试通过")
    
    print("\n✅ 缓存集成测试全部通过！")


async def main():
    """主测试函数"""
    print("="*50)
    print("VabHub 架构组件测试")
    print("="*50)
    
    try:
        # 测试缓存系统
        await test_cache_system()
        
        # 测试健康检查系统
        await test_health_checker()
        
        # 测试缓存集成
        await test_cache_integration()
        
        print("\n" + "="*50)
        print("✅ 所有测试通过！")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

