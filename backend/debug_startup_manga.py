"""
调试后端服务启动过程中的漫画模块注册
"""
import traceback

# 模拟后端启动过程
print("=== 模拟后端启动过程 ===")

# 1. 导入主应用模块
try:
    from app.main import app
    print("✅ 主应用导入成功")
    
    # 检查应用的路由
    print(f"应用路由数量: {len(app.routes)}")
    
    # 查找漫画相关路由
    manga_routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            path = getattr(route, 'path', '')
            if 'manga' in str(path):
                manga_routes.append(path)
    
    print(f"漫画相关路由数量: {len(manga_routes)}")
    for route in manga_routes:
        print(f"  - {route}")
        
except Exception as e:
    print(f"❌ 主应用导入失败: {e}")
    traceback.print_exc()

print("\n=== 检查API路由器 ===")

# 2. 检查API路由器
try:
    from app.api import api_router
    print("✅ API路由器导入成功")
    print(f"API路由器路由数量: {len(api_router.routes)}")
    
    # 查找漫画相关路由
    manga_api_routes = []
    for route in api_router.routes:
        if hasattr(route, 'path'):
            path = getattr(route, 'path', '')
            if 'manga' in str(path):
                manga_api_routes.append(path)
    
    print(f"API路由器中漫画相关路由数量: {len(manga_api_routes)}")
    for route in manga_api_routes:
        print(f"  - {route}")
        
except Exception as e:
    print(f"❌ API路由器导入失败: {e}")
    traceback.print_exc()

print("\n=== 检查漫画模块导入 ===")

# 3. 检查各个漫画模块
try:
    from app.api import manga_sync, manga_local, manga_remote, manga_source_admin, manga_progress, reading_hub
    print("✅ 所有漫画模块导入成功")
    
    modules = [
        ("manga_sync", manga_sync),
        ("manga_local", manga_local),
        ("manga_remote", manga_remote),
        ("manga_source_admin", manga_source_admin),
        ("manga_progress", manga_progress),
        ("reading_hub", reading_hub)
    ]
    
    for name, module in modules:
        router = getattr(module, 'router', None)
        if router:
            print(f"✅ {name}: 路由器存在")
            print(f"   前缀: {getattr(router, 'prefix', '无')}")
            print(f"   标签: {getattr(router, 'tags', [])}")
            print(f"   路由数量: {len(router.routes) if hasattr(router, 'routes') else '未知'}")
        else:
            print(f"❌ {name}: 路由器不存在")
            
except Exception as e:
    print(f"❌ 漫画模块导入失败: {e}")
    traceback.print_exc()

print("\n=== 检查OpenAPI规范 ===")

# 4. 检查OpenAPI规范
try:
    openapi_spec = app.openapi()
    paths = list(openapi_spec["paths"].keys())
    print(f"OpenAPI路径总数: {len(paths)}")
    
    manga_paths = [p for p in paths if 'manga' in p]
    print(f"OpenAPI中漫画相关路径数量: {len(manga_paths)}")
    
    if manga_paths:
        print("漫画相关路径:")
        for path in manga_paths:
            print(f"  - {path}")
    else:
        print("❌ OpenAPI中没有漫画相关路径")
        
    # 检查标签
    tags = openapi_spec.get("tags", [])
    manga_tags = [t for t in tags if '漫画' in t.get('name', '')]
    print(f"OpenAPI中漫画相关标签数量: {len(manga_tags)}")
    for tag in manga_tags:
        print(f"  - {tag['name']}")
        
except Exception as e:
    print(f"❌ 获取OpenAPI规范失败: {e}")
    traceback.print_exc()

print("\n=== 总结 ===")
print("如果API路由器中有漫画路由但主应用中没有，说明路由注册有问题")
print("如果API路由器中也没有漫画路由，说明模块导入或注册有问题")