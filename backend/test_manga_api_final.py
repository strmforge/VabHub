"""
最终测试漫画API端点
"""
import requests

BASE_URL = "http://localhost:8000"

def test_endpoint(method, path, data=None):
    """测试单个端点"""
    url = f"{BASE_URL}{path}"
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            print(f"❌ 不支持的HTTP方法: {method}")
            return False
            
        print(f"{method} {path} -> 状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ 成功")
            return True
        elif response.status_code == 404:
            print("   ❌ 端点不存在")
            return False
        else:
            print(f"   ⚠️  其他状态码: {response.status_code}")
            try:
                error_data = response.json()
                print(f"     错误信息: {error_data}")
            except:
                print(f"     响应内容: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到后端服务: {url}")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时: {url}")
        return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def main():
    print("=== 测试漫画API端点 ===")
    
    # 测试健康检查
    print("\n1. 测试健康检查:")
    test_endpoint("GET", "/health")
    
    # 测试OpenAPI文档
    print("\n2. 测试OpenAPI文档:")
    test_endpoint("GET", "/docs")
    
    # 测试漫画相关端点
    print("\n3. 测试漫画同步端点:")
    test_endpoint("GET", "/api/manga/local/sync/series/1")
    test_endpoint("POST", "/api/manga/local/sync/favorites")
    
    print("\n4. 测试本地漫画库端点:")
    test_endpoint("GET", "/api/manga/local/series")
    test_endpoint("GET", "/api/manga/local/series/1")
    
    print("\n5. 测试远程漫画端点:")
    test_endpoint("GET", "/api/manga/remote/sources")
    test_endpoint("GET", "/api/manga/remote/search")
    
    print("\n6. 测试漫画阅读进度端点:")
    test_endpoint("GET", "/api/manga/local/progress/series/1")
    test_endpoint("GET", "/api/manga/local/progress/history")
    
    print("\n7. 测试阅读中心端点:")
    test_endpoint("GET", "/api/reading/hub")
    
    # 检查OpenAPI规范中的漫画路径
    print("\n8. 检查OpenAPI规范中的漫画路径:")
    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
        if response.status_code == 200:
            openapi_spec = response.json()
            paths = list(openapi_spec["paths"].keys())
            
            manga_paths = [p for p in paths if 'manga' in p or 'reading' in p]
            print(f"OpenAPI中漫画相关路径数量: {len(manga_paths)}")
            
            if manga_paths:
                print("漫画相关路径:")
                for path in manga_paths[:10]:  # 只显示前10个
                    print(f"  - {path}")
                if len(manga_paths) > 10:
                    print(f"  ... 还有 {len(manga_paths) - 10} 个路径")
            else:
                print("❌ OpenAPI中没有找到漫画相关路径")
        else:
            print(f"❌ 无法获取OpenAPI规范: {response.status_code}")
    except Exception as e:
        print(f"❌ 检查OpenAPI规范失败: {e}")

if __name__ == "__main__":
    main()