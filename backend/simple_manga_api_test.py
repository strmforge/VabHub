#!/usr/bin/env python3
"""
简单测试漫画API注册问题
"""

import sys
import os
import requests
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_api_registration():
    """测试API注册"""
    
    print("🚀 开始测试漫画API注册...")
    
    # 等待后端服务启动
    print("⏳ 等待后端服务启动...")
    time.sleep(3)
    
    try:
        # 获取OpenAPI规范
        response = requests.get("http://localhost:8000/openapi.json")
        
        if response.status_code != 200:
            print(f"❌ 无法获取OpenAPI规范: {response.status_code}")
            return False
        
        openapi_schema = response.json()
        
        print("✅ OpenAPI规范获取成功")
        
        # 统计路径和标签
        paths_count = len(openapi_schema.get("paths", {}))
        tags_count = len(openapi_schema.get("tags", []))
        
        print(f"📊 OpenAPI统计:")
        print(f"   路径数量: {paths_count}")
        print(f"   标签数量: {tags_count}")
        
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
            print(f"\n📋 漫画相关路径:")
            for i, path in enumerate(manga_paths[:20], 1):
                print(f"   {i}. {path}")
        else:
            print("❌ 未找到任何漫画相关路径")
        
        # 检查特定漫画端点
        manga_endpoints_to_check = [
            "/api/manga/local/sync/series/{series_id}",
            "/api/manga/local/sync/favorites",
            "/api/manga/local/series",
            "/api/manga/remote/sources",
            "/api/reading/ongoing"
        ]
        
        print(f"\n🔍 检查特定漫画端点:")
        found_endpoints = []
        missing_endpoints = []
        
        for endpoint in manga_endpoints_to_check:
            if endpoint in openapi_schema.get("paths", {}):
                found_endpoints.append(endpoint)
                print(f"   ✅ {endpoint}")
            else:
                missing_endpoints.append(endpoint)
                print(f"   ❌ {endpoint}")
        
        print(f"\n📊 端点检查结果:")
        print(f"   找到: {len(found_endpoints)}/{len(manga_endpoints_to_check)}")
        print(f"   缺失: {len(missing_endpoints)}/{len(manga_endpoints_to_check)}")
        
        if missing_endpoints:
            print(f"\n❌ 缺失的端点:")
            for endpoint in missing_endpoints:
                print(f"   - {endpoint}")
            return False
        else:
            print("\n🎉 所有漫画端点都正确注册!")
            return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务，请确保服务正在运行")
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

def main():
    """主函数"""
    
    print("🚀 开始漫画API注册测试...")
    
    success = test_api_registration()
    
    if success:
        print("\n🎉 漫画API注册测试通过!")
        sys.exit(0)
    else:
        print("\n❌ 漫画API注册测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main()