"""
简单测试漫画API
"""
import requests

# 测试OpenAPI规范中是否包含漫画端点
print("=== 检查OpenAPI规范中的漫画端点 ===")

try:
    response = requests.get("http://localhost:8000/openapi.json")
    if response.status_code == 200:
        openapi_spec = response.json()
        paths = list(openapi_spec["paths"].keys())
        
        print("✅ OpenAPI规范获取成功")
        print(f"路径总数: {len(paths)}")
        
        # 查找漫画相关路径
        manga_paths = [p for p in paths if 'manga' in p]
        print(f"漫画相关路径数量: {len(manga_paths)}")
        
        if manga_paths:
            print("漫画相关路径:")
            for path in manga_paths:
                print(f"  - {path}")
                
            # 检查漫画同步端点
            sync_paths = [p for p in manga_paths if 'sync' in p]
            print(f"\n漫画同步相关路径数量: {len(sync_paths)}")
            for path in sync_paths:
                print(f"  - {path}")
                
        else:
            print("❌ 没有找到漫画相关路径")
            
        # 检查标签
        tags = openapi_spec.get("tags", [])
        manga_tags = [t for t in tags if '漫画' in t.get('name', '')]
        print(f"\n漫画相关标签数量: {len(manga_tags)}")
        for tag in manga_tags:
            print(f"  - {tag['name']}")
            
except Exception as e:
    print(f"❌ 测试失败: {e}")

print("\n=== 测试漫画同步端点 ===")

# 测试漫画同步端点
try:
    # 测试GET方法（应该返回405或401）
    response = requests.get("http://localhost:8000/api/manga/local/sync/series/1")
    print(f"GET /api/manga/local/sync/series/1: {response.status_code}")
    
    # 测试POST方法（应该返回401，需要认证）
    response = requests.post("http://localhost:8000/api/manga/local/sync/series/1")
    print(f"POST /api/manga/local/sync/series/1: {response.status_code}")
    
    if response.status_code == 401:
        print("✅ 端点存在，需要认证（正常行为）")
    elif response.status_code == 404:
        print("❌ 端点不存在")
    else:
        print(f"❓ 未知状态码: {response.status_code}")
        
except Exception as e:
    print(f"❌ 测试失败: {e}")