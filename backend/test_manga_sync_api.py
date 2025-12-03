#!/usr/bin/env python3
"""
测试漫画同步API是否已正确注册到OpenAPI
"""

import requests
import time
import sys

def test_openapi_registration():
    """测试漫画同步API在OpenAPI中的注册情况"""
    
    # 等待服务启动
    print("等待后端服务启动...")
    time.sleep(5)
    
    try:
        # 获取OpenAPI规范
        response = requests.get("http://localhost:8000/openapi.json")
        if response.status_code != 200:
            print(f"❌ 无法获取OpenAPI规范，状态码: {response.status_code}")
            return False
        
        openapi_spec = response.json()
        
        # 检查漫画同步相关端点和标签
        manga_sync_endpoints = []
        all_manga_endpoints = []
        manga_tags = []
        
        # 遍历所有路径
        for path, path_item in openapi_spec.get("paths", {}).items():
            # 检查是否是漫画同步相关路径
            if "/api/manga/local/sync" in path:
                manga_sync_endpoints.append(path)
            
            # 检查所有漫画相关路径
            if "/manga" in path:
                all_manga_endpoints.append(path)
        
        # 检查标签
        for tag in openapi_spec.get("tags", []):
            if "漫画" in tag.get("name", ""):
                manga_tags.append(tag.get("name"))
        
        print(f"📊 OpenAPI规范检查结果:")
        print(f"   漫画同步端点数量: {len(manga_sync_endpoints)}")
        print(f"   漫画同步标签: {manga_tags}")
        print(f"   所有漫画相关端点数量: {len(all_manga_endpoints)}")
        
        # 打印具体的漫画同步端点
        if manga_sync_endpoints:
            print(f"\n🔍 漫画同步端点详情:")
            for endpoint in manga_sync_endpoints:
                print(f"   - {endpoint}")
                # 打印该端点的HTTP方法
                for method in ["get", "post", "put", "delete", "patch"]:
                    if method in openapi_spec["paths"][endpoint]:
                        print(f"     {method.upper()}: {openapi_spec['paths'][endpoint][method].get('summary', 'No summary')}")
        
        # 检查是否包含预期的端点
        expected_endpoints = [
            "/api/manga/local/sync/series/{series_id}",
            "/api/manga/local/sync/favorites"
        ]
        
        missing_endpoints = []
        for expected in expected_endpoints:
            if expected not in manga_sync_endpoints:
                missing_endpoints.append(expected)
        
        if missing_endpoints:
            print(f"\n❌ 缺少预期端点: {missing_endpoints}")
            return False
        else:
            print(f"\n✅ 所有预期端点都已注册!")
            return True
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务，请确保服务正在运行")
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = test_openapi_registration()
    sys.exit(0 if success else 1)