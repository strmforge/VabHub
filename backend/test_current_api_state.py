"""
测试当前后端服务的API状态
"""
import requests

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"健康检查状态码: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"健康状态: {health_data.get('status', 'unknown')}")
            return True
        else:
            print(f"健康检查失败: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"健康检查异常: {e}")
        return False

def test_openapi():
    """测试OpenAPI文档"""
    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        print(f"OpenAPI状态码: {response.status_code}")
        if response.status_code == 200:
            openapi_data = response.json()
            paths = list(openapi_data["paths"].keys())
            print(f"OpenAPI路径总数: {len(paths)}")
            
            # 显示所有路径
            print("\n所有API路径:")
            for path in paths[:20]:  # 只显示前20个
                print(f"  - {path}")
            if len(paths) > 20:
                print(f"  ... 还有 {len(paths) - 20} 个路径")
            
            # 检查漫画相关路径
            manga_paths = [p for p in paths if 'manga' in p or 'reading' in p]
            print(f"\n漫画相关路径数量: {len(manga_paths)}")
            if manga_paths:
                print("漫画相关路径:")
                for path in manga_paths:
                    print(f"  - {path}")
            else:
                print("❌ 没有找到漫画相关路径")
            
            return True
        else:
            print(f"OpenAPI获取失败: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"OpenAPI测试异常: {e}")
        return False

def test_specific_endpoints():
    """测试特定端点"""
    endpoints = [
        ("/", "根路径"),
        ("/docs", "API文档"),
        ("/api/manga/local/series", "本地漫画列表"),
        ("/api/manga/remote/sources", "远程漫画源"),
        ("/api/reading/hub", "阅读中心"),
        ("/api/health", "健康检查（API版本）"),
    ]
    
    print("\n测试特定端点:")
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            print(f"{description} ({endpoint}) -> 状态码: {response.status_code}")
        except Exception as e:
            print(f"{description} ({endpoint}) -> 异常: {e}")

def main():
    print("=== 测试当前后端服务API状态 ===")
    
    # 测试健康检查
    if not test_health():
        print("❌ 后端服务可能未正常运行")
        return
    
    # 测试OpenAPI
    if not test_openapi():
        print("❌ OpenAPI文档获取失败")
        return
    
    # 测试特定端点
    test_specific_endpoints()
    
    print("\n=== 分析结果 ===")
    print("如果漫画相关路径数量为0，说明漫画模块的路由器没有正确注册到主应用中")
    print("如果漫画相关路径存在但返回404，可能是数据库或服务初始化问题")

if __name__ == "__main__":
    main()