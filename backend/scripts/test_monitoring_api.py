"""
测试监控API
"""

import asyncio
import httpx


async def test_monitoring_api():
    """测试监控API"""
    base_url = "http://localhost:8092/api"
    
    print("=" * 60)
    print("监控API测试")
    print("=" * 60)
    print()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 测试1: 系统资源
            print("[测试1] 系统资源监控...")
            try:
                response = await client.get(f"{base_url}/monitoring/system/resources")
                if response.status_code == 200:
                    data = response.json()
                    resources = data.get("data", {})
                    print("  [OK] 系统资源获取成功")
                    print(f"    CPU使用率: {resources.get('cpu', {}).get('usage_percent', 0)}%")
                    print(f"    内存使用率: {resources.get('memory', {}).get('usage_percent', 0)}%")
                    print(f"    磁盘使用率: {resources.get('disk', {}).get('usage_percent', 0)}%")
                else:
                    print(f"  [FAIL] 状态码: {response.status_code}")
                    print(f"    响应: {response.text[:200]}")
            except Exception as e:
                print(f"  [FAIL] 异常: {e}")
            
            print()
            
            # 测试2: API性能
            print("[测试2] API性能监控...")
            try:
                response = await client.get(f"{base_url}/monitoring/api/performance")
                if response.status_code == 200:
                    data = response.json()
                    metrics = data.get("data", {})
                    summary = metrics.get("summary", {})
                    print("  [OK] API性能指标获取成功")
                    print(f"    总请求数: {summary.get('total_requests', 0)}")
                    print(f"    总错误数: {summary.get('total_errors', 0)}")
                    print(f"    错误率: {summary.get('error_rate', 0) * 100:.2f}%")
                else:
                    print(f"  [FAIL] 状态码: {response.status_code}")
            except Exception as e:
                print(f"  [FAIL] 异常: {e}")
            
            print()
            
            # 测试3: 系统统计
            print("[测试3] 系统资源统计...")
            try:
                response = await client.get(f"{base_url}/monitoring/system/statistics")
                if response.status_code == 200:
                    data = response.json()
                    statistics = data.get("data", {})
                    print("  [OK] 统计信息获取成功")
                    cpu_stats = statistics.get("cpu", {})
                    print(f"    CPU统计: 平均={cpu_stats.get('avg', 0)}%")
                else:
                    print(f"  [FAIL] 状态码: {response.status_code}")
            except Exception as e:
                print(f"  [FAIL] 异常: {e}")
            
            print()
            print("=" * 60)
            print("监控API测试完成")
            print("=" * 60)
            
    except httpx.ConnectError:
        print("  [FAIL] 无法连接到后端服务")
        print("  请先启动后端服务: python main.py")
    except Exception as e:
        print(f"  [FAIL] 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_monitoring_api())

