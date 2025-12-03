"""
调试漫画模块导入过程
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import(module_name):
    """测试导入单个模块"""
    try:
        module = __import__(module_name)
        print(f"✅ {module_name} 导入成功")
        return True
    except ImportError as e:
        print(f"❌ {module_name} 导入失败: {e}")
        return False
    except Exception as e:
        print(f"⚠️  {module_name} 导入异常: {e}")
        return False

def main():
    print("=== 测试漫画模块导入 ===")
    
    # 测试核心漫画模块
    modules_to_test = [
        "app.api.manga_sync",
        "app.api.manga_local", 
        "app.api.manga_remote",
        "app.api.manga_progress",
        "app.api.manga_source_admin",
        "app.api.reading_hub",
        "app.api",  # 主API路由器
    ]
    
    results = {}
    for module_name in modules_to_test:
        results[module_name] = test_import(module_name)
    
    # 如果模块导入成功，检查路由器属性
    print("\n=== 检查路由器属性 ===")
    for module_name in modules_to_test:
        if results[module_name]:
            try:
                module = sys.modules[module_name]
                if hasattr(module, 'router'):
                    router = module.router
                    print(f"✅ {module_name} 有router属性")
                    if hasattr(router, 'routes'):
                        print(f"   路由数量: {len(router.routes)}")
                        # 显示前几个路由路径
                        for i, route in enumerate(router.routes[:3]):
                            if hasattr(route, 'path'):
                                print(f"   路由{i+1}: {route.path}")
                else:
                    print(f"❌ {module_name} 没有router属性")
            except Exception as e:
                print(f"⚠️  检查{module_name}路由器失败: {e}")
    
    # 检查API路由器中的漫画路由
    print("\n=== 检查API路由器中的漫画路由 ===")
    try:
        import app.api
        api_module = sys.modules['app.api']
        if hasattr(api_module, 'api_router'):
            api_router = api_module.api_router
            print(f"✅ api_router 存在")
            
            # 统计漫画相关路由
            manga_routes = []
            for route in api_router.routes:
                if hasattr(route, 'path') and route.path:
                    path_str = str(route.path)
                    if 'manga' in path_str or 'reading' in path_str:
                        manga_routes.append(path_str)
            
            print(f"API路由器中漫画相关路由数量: {len(manga_routes)}")
            if manga_routes:
                print("漫画路由:")
                for route in manga_routes[:10]:
                    print(f"  - {route}")
            else:
                print("❌ API路由器中没有漫画相关路由")
        else:
            print("❌ api_router 不存在")
    except Exception as e:
        print(f"❌ 检查API路由器失败: {e}")

if __name__ == "__main__":
    main()