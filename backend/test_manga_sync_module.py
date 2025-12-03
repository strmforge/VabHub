#!/usr/bin/env python3
"""
直接测试漫画同步模块的导入和路由定义
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_manga_sync_module():
    """测试漫画同步模块的导入和路由定义"""
    
    try:
        # 尝试导入漫画同步模块
        print("🔍 尝试导入漫画同步模块...")
        from app.api import manga_sync
        print("✅ 漫画同步模块导入成功")
        
        # 检查路由器的属性
        router = manga_sync.router
        print(f"📊 路由器信息:")
        print(f"   前缀(prefix): {router.prefix}")
        print(f"   标签(tags): {router.tags}")
        print(f"   路由数量: {len(router.routes)}")
        
        # 检查路由详情
        print(f"\n🔍 路由详情:")
        for i, route in enumerate(router.routes):
            print(f"   {i+1}. 路径: {route.path}")
            print(f"      方法: {route.methods}")
            if hasattr(route, 'endpoint'):
                print(f"      端点: {route.endpoint}")
            print()
        
        # 检查是否包含预期的路由
        expected_paths = [
            "/api/manga/local/sync/series/{series_id}",
            "/api/manga/local/sync/favorites"
        ]
        
        actual_paths = [route.path for route in router.routes]
        missing_paths = []
        
        for expected in expected_paths:
            if expected not in actual_paths:
                missing_paths.append(expected)
        
        if missing_paths:
            print(f"❌ 缺少预期路由: {missing_paths}")
            return False
        else:
            print(f"✅ 所有预期路由都存在!")
            return True
            
    except ImportError as e:
        print(f"❌ 导入漫画同步模块失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

def test_api_init_import():
    """测试app/api/__init__.py中的导入"""
    
    try:
        print("\n🔍 测试app/api/__init__.py中的导入...")
        
        # 检查导入语句
        init_file_path = os.path.join(os.path.dirname(__file__), "app", "api", "__init__.py")
        
        with open(init_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含manga_sync导入
        if "manga_sync" in content:
            print("✅ manga_sync模块在__init__.py中已导入")
            
            # 检查导入位置
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "manga_sync" in line and "import" in line:
                    print(f"   导入位置: 第{i+1}行 - {line.strip()}")
                    break
        else:
            print("❌ manga_sync模块未在__init__.py中导入")
            return False
        
        # 检查路由注册
        if "api_router.include_router(manga_sync.router" in content:
            print("✅ manga_sync路由已注册到api_router")
            
            # 检查注册语句详情
            for i, line in enumerate(lines):
                if "api_router.include_router(manga_sync.router" in line:
                    print(f"   注册位置: 第{i+1}行 - {line.strip()}")
                    
                    # 检查是否包含tags参数
                    if 'tags=[' in line and '漫画同步' in line:
                        print("   ✅ 包含正确的tags参数")
                    else:
                        print("   ⚠️ 可能缺少tags参数或参数不正确")
                    break
        else:
            print("❌ manga_sync路由未注册到api_router")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 测试__init__.py导入时发生错误: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始测试漫画同步模块...")
    
    module_success = test_manga_sync_module()
    init_success = test_api_init_import()
    
    if module_success and init_success:
        print("\n🎉 所有测试通过! 漫画同步模块配置正确")
        sys.exit(0)
    else:
        print("\n❌ 测试失败，请检查模块配置")
        sys.exit(1)