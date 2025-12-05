#!/usr/bin/env python3
"""
调试漫画同步API注册问题
"""

import requests
import sys

def check_service_status():
    """检查后端服务状态"""
    
    print("🔍 检查后端服务状态...")
    
    # 检查多个可能的端口
    ports = [8000, 8001, 8080, 8081]
    
    for port in ports:
        try:
            response = requests.get(f"http://localhost:{port}/docs", timeout=5)
            if response.status_code == 200:
                print(f"✅ 后端服务正在端口 {port} 运行")
                return port
        except requests.exceptions.ConnectionError:
            print(f"❌ 端口 {port} 无响应")
        except requests.exceptions.Timeout:
            print(f"⏰ 端口 {port} 连接超时")
        except Exception as e:
            print(f"⚠️ 检查端口 {port} 时出错: {e}")
    
    return None

def check_openapi_spec(port):
    """检查OpenAPI规范"""
    
    print(f"\n🔍 检查端口 {port} 的OpenAPI规范...")
    
    try:
        # 获取OpenAPI规范
        response = requests.get(f"http://localhost:{port}/openapi.json", timeout=10)
        if response.status_code != 200:
            print(f"❌ 无法获取OpenAPI规范，状态码: {response.status_code}")
            return None
        
        openapi_spec = response.json()
        
        print("✅ OpenAPI规范获取成功")
        print(f"   版本: {openapi_spec.get('openapi', 'Unknown')}")
        print(f"   标题: {openapi_spec.get('info', {}).get('title', 'Unknown')}")
        print(f"   路径数量: {len(openapi_spec.get('paths', {}))}")
        print(f"   标签数量: {len(openapi_spec.get('tags', []))}")
        
        return openapi_spec
        
    except Exception as e:
        print(f"❌ 获取OpenAPI规范时出错: {e}")
        return None

def check_manga_sync_in_openapi(openapi_spec):
    """检查漫画同步相关端点在OpenAPI中的存在"""
    
    print("\n🔍 检查漫画同步相关端点...")
    
    if not openapi_spec:
        return
    
    # 检查所有路径
    paths = openapi_spec.get("paths", {})
    
    # 查找漫画同步相关路径
    manga_sync_paths = []
    all_manga_paths = []
    
    for path in paths:
        if "/api/manga/local/sync" in path:
            manga_sync_paths.append(path)
        if "/manga" in path:
            all_manga_paths.append(path)
    
    print(f"   漫画同步端点数量: {len(manga_sync_paths)}")
    print(f"   所有漫画相关端点数量: {len(all_manga_paths)}")
    
    # 打印漫画同步端点详情
    if manga_sync_paths:
        print("\n🔍 漫画同步端点详情:")
        for path in manga_sync_paths:
            print(f"   - {path}")
            for method in ["get", "post", "put", "delete", "patch"]:
                if method in paths[path]:
                    endpoint_info = paths[path][method]
                    print(f"     {method.upper()}: {endpoint_info.get('summary', 'No summary')}")
                    print(f"       标签: {endpoint_info.get('tags', [])}")
    else:
        print("\n❌ 未找到漫画同步端点")
    
    # 检查标签
    tags = openapi_spec.get("tags", [])
    manga_tags = [tag["name"] for tag in tags if "漫画" in tag.get("name", "")]
    print(f"\n🔍 漫画相关标签: {manga_tags}")
    
    # 检查是否包含预期的端点
    expected_endpoints = [
        "/api/manga/local/sync/series/{series_id}",
        "/api/manga/local/sync/favorites"
    ]
    
    missing_endpoints = []
    for expected in expected_endpoints:
        if expected not in manga_sync_paths:
            missing_endpoints.append(expected)
    
    if missing_endpoints:
        print(f"\n❌ 缺少预期端点: {missing_endpoints}")
        return False
    else:
        print("\n✅ 所有预期端点都已注册!")
        return True

def check_other_manga_modules(openapi_spec):
    """检查其他漫画模块的注册情况"""
    
    print("\n🔍 检查其他漫画模块的注册情况...")
    
    if not openapi_spec:
        return
    
    paths = openapi_spec.get("paths", {})
    
    # 检查其他漫画模块
    manga_modules = [
        "manga_source_admin",
        "manga_remote", 
        "manga_local",
        "manga_progress",
        "reading_hub"
    ]
    
    for module in manga_modules:
        module_paths = [path for path in paths if f"/api/manga/{module.replace('_', '/')}" in path or module in path]
        print(f"   {module}: {len(module_paths)} 个端点")
        if module_paths:
            for path in module_paths[:3]:  # 只显示前3个
                print(f"      - {path}")

def main():
    """主函数"""
    
    print("🚀 开始调试漫画同步API注册问题...")
    
    # 检查服务状态
    port = check_service_status()
    if not port:
        print("❌ 未找到运行中的后端服务")
        sys.exit(1)
    
    # 检查OpenAPI规范
    openapi_spec = check_openapi_spec(port)
    if not openapi_spec:
        print("❌ 无法获取OpenAPI规范")
        sys.exit(1)
    
    # 检查漫画同步端点
    manga_sync_success = check_manga_sync_in_openapi(openapi_spec)
    
    # 检查其他漫画模块
    check_other_manga_modules(openapi_spec)
    
    if manga_sync_success:
        print("\n🎉 漫画同步API注册成功!")
        sys.exit(0)
    else:
        print("\n❌ 漫画同步API注册失败")
        sys.exit(1)

if __name__ == "__main__":
    main()