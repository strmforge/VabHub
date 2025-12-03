"""
测试漫画API是否真的可用
"""
import requests
import json
import sys

# 后端服务地址
BASE_URL = "http://localhost:8000"

# 要测试的漫画API端点
MANGA_ENDPOINTS = [
    "/api/manga/local/sync/series/{series_id}",  # 漫画同步端点
    "/api/manga/local/sync/favorites",           # 漫画同步收藏端点
    "/api/manga/local/series",                   # 本地漫画系列列表
    "/api/manga/remote/sources",                 # 远程漫画源列表
    "/api/manga/local/progress/history"          # 漫画阅读历史
]

print("=== 测试漫画API端点可用性 ===")

# 首先检查后端服务是否正常运行
try:
    health_response = requests.get(f"{BASE_URL}/health")
    if health_response.status_code == 200:
        print("✅ 后端服务正常运行")
    else:
        print(f"❌ 后端服务异常，状态码: {health_response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"❌ 无法连接到后端服务: {e}")
    sys.exit(1)

# 获取OpenAPI规范
try:
    openapi_response = requests.get(f"{BASE_URL}/openapi.json")
    if openapi_response.status_code == 200:
        openapi_spec = openapi_response.json()
        paths = list(openapi_spec["paths"].keys())
        print(f"✅ OpenAPI规范获取成功，路径总数: {len(paths)}")
        
        # 检查漫画相关路径
        manga_paths = [p for p in paths if 'manga' in p]
        print(f"漫画相关路径数量: {len(manga_paths)}")
        
        if manga_paths:
            print("漫画相关路径:")
            for path in manga_paths[:10]:  # 只显示前10个
                print(f"  - {path}")
            if len(manga_paths) > 10:
                print(f"  ... 还有 {len(manga_paths) - 10} 个路径")
        else:
            print("❌ 没有找到漫画相关路径")
            
    else:
        print(f"❌ 获取OpenAPI规范失败，状态码: {openapi_response.status_code}")
except Exception as e:
    print(f"❌ 获取OpenAPI规范时出错: {e}")

print("\n=== 测试具体端点 ===")

# 测试每个端点
for endpoint in MANGA_ENDPOINTS:
    # 对于需要参数的端点，使用测试值
    test_endpoint = endpoint
    if "{series_id}" in endpoint:
        test_endpoint = endpoint.replace("{series_id}", "1")  # 使用测试ID 1
    
    try:
        # 使用GET方法测试端点是否存在
        response = requests.get(f"{BASE_URL}{test_endpoint}")
        
        # 检查响应状态
        if response.status_code == 200:
            print(f"✅ {endpoint}: 端点存在且可访问")
        elif response.status_code == 404:
            print(f"❌ {endpoint}: 端点不存在 (404)")
        elif response.status_code == 401:
            print(f"⚠️ {endpoint}: 需要认证 (401)")
        elif response.status_code == 405:
            # 可能是方法不支持，尝试POST
            try:
                post_response = requests.post(f"{BASE_URL}{test_endpoint}")
                if post_response.status_code == 200 or post_response.status_code == 401:
                    print(f"✅ {endpoint}: 端点存在 (需要POST方法)")
                else:
                    print(f"❌ {endpoint}: 端点可能不存在 (POST返回 {post_response.status_code})")
            except:
                print(f"❌ {endpoint}: 端点可能不存在")
        else:
            print(f"❓ {endpoint}: 未知状态码 {response.status_code}")
            
    except Exception as e:
        print(f"❌ {endpoint}: 请求失败 - {e}")

print("\n=== 测试漫画同步端点（POST方法） ===")

# 特别测试漫画同步端点（需要POST方法）
sync_endpoints = [
    "/api/manga/local/sync/series/1",
    "/api/manga/local/sync/favorites"
]

for endpoint in sync_endpoints:
    try:
        response = requests.post(f"{BASE_URL}{endpoint}")
        if response.status_code == 200:
            print(f"✅ {endpoint}: POST方法成功")
        elif response.status_code == 401:
            print(f"⚠️ {endpoint}: 需要认证 (401)")
        elif response.status_code == 404:
            print(f"❌ {endpoint}: 端点不存在 (404)")
        else:
            print(f"❓ {endpoint}: 状态码 {response.status_code}")
    except Exception as e:
        print(f"❌ {endpoint}: 请求失败 - {e}")