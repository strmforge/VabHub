#!/usr/bin/env python3
"""
调试FastAPI应用启动过程中的漫画API注册问题
"""

import sys
import os
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_fastapi_startup():
    """测试FastAPI应用启动过程"""
    
    print("🚀 开始测试FastAPI应用启动...")
    
    try:
        # 导入主应用
        from app.main import app
        
        print("✅ FastAPI应用导入成功")
        
        # 检查应用的路由器
        print(f"\n🔍 检查应用路由器:")
        print(f"   路由器数量: {len(app.routes)}")
        
        # 获取所有路由
        routes_info = []
        for route in app.routes:
            route_info = {
                "path": getattr(route, 'path', 'N/A'),
                "methods": getattr(route, 'methods', 'N/A'),
                "name": getattr(route, 'name', 'N/A'),
                "tags": getattr(route, 'tags', [])
            }
            routes_info.append(route_info)
        
        # 过滤出漫画相关的路由
        manga_routes = []
        for route in routes_info:
            path = route["path"]
            if path and ("/manga/" in path or "/reading/" in path):
                manga_routes.append(route)
        
        print(f"\n📊 漫画相关路由统计:")
        print(f"   总路由数量: {len(routes_info)}")
        print(f"   漫画相关路由数量: {len(manga_routes)}")
        
        if manga_routes:
            print(f"\n📋 漫画相关路由详情:")
            for i, route in enumerate(manga_routes[:10], 1):  # 只显示前10个
                print(f"   {i}. {route['path']} - {route['methods']} - {route['tags']}")
            
            if len(manga_routes) > 10:
                print(f"   ... 还有 {len(manga_routes) - 10} 个漫画路由")
        else:
            print("❌ 未找到任何漫画相关路由")
        
        # 检查OpenAPI规范
        print(f"\n🔍 检查OpenAPI规范...")
        
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
        )
        
        # 统计路径和标签
        paths_count = len(openapi_schema.get("paths", {}))
        tags_count = len(openapi_schema.get("tags", []))
        
        print(f"   OpenAPI路径数量: {paths_count}")
        print(f"   OpenAPI标签数量: {tags_count}")
        
        # 检查漫画相关标签
        manga_tags = []
        for tag in openapi_schema.get("tags", []):
            tag_name = tag.get("name", "")
            if "漫画" in tag_name or "manga" in tag_name.lower():
                manga_tags.append(tag_name)
        
        print(f"   漫画相关标签: {manga_tags}")
        
        # 检查漫画相关路径
        manga_paths = []
        for path, methods in openapi_schema.get("paths", {}).items():
            if "/manga/" in path or "/reading/" in path:
                manga_paths.append(path)
        
        print(f"   漫画相关路径数量: {len(manga_paths)}")
        
        if manga_paths:
            print(f"\n📋 漫画相关路径详情:")
            for i, path in enumerate(manga_paths[:10], 1):
                print(f"   {i}. {path}")
            
            if len(manga_paths) > 10:
                print(f"   ... 还有 {len(manga_paths) - 10} 个漫画路径")
        else:
            print("❌ 未找到任何漫画相关路径")
        
        # 检查API路由器的注册
        print(f"\n🔍 检查API路由器注册...")
        
        # 导入API路由器
        from app.api import api_router
        
        print(f"   API路由器包含的路由数量: {len(api_router.routes)}")
        
        # 检查漫画模块是否在API路由器中
        manga_api_routes = []
        for route in api_router.routes:
            path = getattr(route, 'path', '')
            if "/manga/" in path or "/reading/" in path:
                manga_api_routes.append(path)
        
        print(f"   API路由器中的漫画路由数量: {len(manga_api_routes)}")
        
        if manga_api_routes:
            print(f"\n📋 API路由器中的漫画路由:")
            for i, path in enumerate(manga_api_routes[:10], 1):
                print(f"   {i}. {path}")
        else:
            print("❌ API路由器中未找到漫画路由")
        
        return True
        
    except Exception as e:
        print(f"❌ FastAPI应用启动测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_manga_module_registration():
    """测试漫画模块的注册过程"""
    
    print(f"\n🔍 测试漫画模块注册过程...")
    
    try:
        # 导入漫画模块
        from app.api import manga_sync, manga_local, manga_remote, manga_progress, manga_source_admin, reading_hub
        
        modules = [
            ("manga_sync", manga_sync),
            ("manga_local", manga_local),
            ("manga_remote", manga_remote),
            ("manga_progress", manga_progress),
            ("manga_source_admin", manga_source_admin),
            ("reading_hub", reading_hub)
        ]
        
        print("✅ 所有漫画模块导入成功")
        
        # 检查每个模块的路由器
        for name, module in modules:
            router = module.router
            print(f"\n📊 {name} 路由器信息:")
            print(f"   前缀: {router.prefix}")
            print(f"   标签: {router.tags}")
            print(f"   路由数量: {len(router.routes)}")
            
            # 显示路由详情
            for i, route in enumerate(router.routes[:3], 1):  # 只显示前3个
                path = getattr(route, 'path', 'N/A')
                methods = getattr(route, 'methods', 'N/A')
                print(f"      {i}. {path} - {methods}")
            
            if len(router.routes) > 3:
                print(f"      ... 还有 {len(router.routes) - 3} 个路由")
        
        return True
        
    except Exception as e:
        print(f"❌ 漫画模块注册测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    
    print("🚀 开始调试FastAPI应用启动过程中的漫画API注册问题...")
    
    # 测试FastAPI应用启动
    startup_success = await test_fastapi_startup()
    
    # 测试漫画模块注册
    registration_success = await test_manga_module_registration()
    
    if startup_success and registration_success:
        print("\n🎉 所有测试通过!")
        print("\n💡 问题分析:")
        print("   如果模块导入成功但API未注册，可能是:")
        print("   1. 应用启动过程中遇到运行时错误")
        print("   2. 数据库连接问题导致模块初始化失败")
        print("   3. 路由注册过程中的异常被静默处理")
    else:
        print("\n❌ 测试失败，请检查相关错误信息")

if __name__ == "__main__":
    asyncio.run(main())