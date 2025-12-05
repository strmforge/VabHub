"""
详细调试漫画模块导入和注册问题
"""
import traceback
from fastapi import FastAPI

# 创建FastAPI应用
app = FastAPI()

# 测试导入各个漫画模块
modules_to_test = [
    "app.api.manga_sync",
    "app.api.manga_local", 
    "app.api.manga_remote",
    "app.api.manga_source_admin",
    "app.api.manga_progress",
    "app.api.reading_hub"
]

print("=== 测试漫画模块导入 ===")
for module_name in modules_to_test:
    try:
        module = __import__(module_name, fromlist=['router'])
        router = getattr(module, 'router', None)
        if router:
            print(f"✅ {module_name}: 导入成功")
            print(f"   前缀: {getattr(router, 'prefix', '无')}")
            print(f"   标签: {getattr(router, 'tags', [])}")
            print(f"   路由数量: {len(router.routes) if hasattr(router, 'routes') else '未知'}")
            
            # 尝试注册到应用
            try:
                app.include_router(router, tags=getattr(router, 'tags', []))
                print("   ✅ 注册到FastAPI成功")
            except Exception as e:
                print(f"   ❌ 注册失败: {e}")
                traceback.print_exc()
        else:
            print(f"❌ {module_name}: 没有找到router属性")
    except Exception as e:
        print(f"❌ {module_name}: 导入失败 - {e}")
        traceback.print_exc()

print("\n=== 检查FastAPI应用的路由 ===")
print(f"应用路由数量: {len(app.routes)}")

# 获取OpenAPI规范
try:
    openapi_spec = app.openapi()
    paths = list(openapi_spec["paths"].keys())
    print(f"OpenAPI路径数量: {len(paths)}")
    
    # 检查漫画相关路径
    manga_paths = [p for p in paths if 'manga' in p]
    print(f"漫画相关路径数量: {len(manga_paths)}")
    for path in manga_paths:
        print(f"  - {path}")
        
except Exception as e:
    print(f"获取OpenAPI规范失败: {e}")
    traceback.print_exc()

print("\n=== 检查API路由器导入 ===")
try:
    from app.api import api_router
    print("✅ api_router导入成功")
    print(f"主路由器路由数量: {len(api_router.routes)}")
    
    # 检查主路由器中的漫画相关路由
    manga_routes = []
    for route in api_router.routes:
        if hasattr(route, 'path'):
            path = getattr(route, 'path', '')
            if 'manga' in str(path):
                manga_routes.append(path)
    
    print(f"主路由器中漫画相关路由数量: {len(manga_routes)}")
    for route in manga_routes:
        print(f"  - {route}")
        
except Exception as e:
    print(f"❌ api_router导入失败: {e}")
    traceback.print_exc()