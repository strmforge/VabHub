"""
检查后端服务健康状态
"""

import asyncio
import httpx
import sys


async def check_backend_health():
    """检查后端服务健康状态"""
    print("=" * 60)
    print("后端服务健康检查")
    print("=" * 60)
    print()
    
    base_url = "http://localhost:8092"
    
    # 测试多个端点
    endpoints = [
        ("/health", "健康检查"),
        ("/", "根路径"),
        ("/api/monitoring/system/resources", "系统资源监控"),
        ("/api/subscriptions", "订阅列表"),
    ]
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            for endpoint, name in endpoints:
                try:
                    print(f"[检查] {name} ({endpoint})...")
                    response = await client.get(f"{base_url}{endpoint}")
                    print(f"  状态码: {response.status_code}")
                    
                    if response.status_code == 200:
                        print(f"  [OK] {name} 正常")
                        if endpoint == "/health":
                            data = response.json()
                            print(f"    状态: {data.get('status', 'N/A')}")
                    elif response.status_code == 503:
                        print(f"  [WARN] {name} 返回503（服务可能正在启动中）")
                    else:
                        print(f"  [WARN] {name} 返回 {response.status_code}")
                        print(f"    响应: {response.text[:200]}")
                    
                    print()
                except httpx.ConnectError:
                    print("  [FAIL] 无法连接到后端服务")
                    print("  请确保后端服务正在运行: python main.py")
                    return False
                except httpx.TimeoutException:
                    print("  [FAIL] 请求超时")
                    return False
                except Exception as e:
                    print(f"  [FAIL] 请求异常: {e}")
                    return False
            
            print("=" * 60)
            print("健康检查完成")
            print("=" * 60)
            return True
            
    except Exception as e:
        print(f"  [FAIL] 检查异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(check_backend_health())
    sys.exit(0 if success else 1)

