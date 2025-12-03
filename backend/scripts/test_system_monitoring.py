"""
测试系统监控功能
"""

import asyncio
import httpx
import json


async def test_system_monitoring():
    """测试系统监控功能"""
    base_url = "http://localhost:8092/api"
    
    print("=" * 60)
    print("系统监控功能测试")
    print("=" * 60)
    print()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 测试1: 健康检查
            print("[测试1] 健康检查...")
            try:
                response = await client.get("http://localhost:8092/health")
                if response.status_code == 200:
                    print(f"  [OK] 后端服务运行正常")
                else:
                    print(f"  [FAIL] 后端服务响应异常: {response.status_code}")
                    return False
            except httpx.ConnectError:
                print("  [FAIL] 无法连接到后端服务")
                print("  请先启动后端服务: python main.py")
                return False
            
            print()
            
            # 测试2: 获取系统资源
            print("[测试2] 获取系统资源使用情况...")
            try:
                response = await client.get(f"{base_url}/monitoring/system/resources")
                if response.status_code == 200:
                    data = response.json()
                    resources = data.get("data", {})
                    
                    print(f"  [OK] 系统资源获取成功")
                    print(f"    CPU使用率: {resources.get('cpu', {}).get('usage_percent', 0)}%")
                    print(f"    内存使用率: {resources.get('memory', {}).get('usage_percent', 0)}%")
                    print(f"    磁盘使用率: {resources.get('disk', {}).get('usage_percent', 0)}%")
                    print(f"    内存总量: {resources.get('memory', {}).get('total_gb', 0)} GB")
                    print(f"    磁盘总量: {resources.get('disk', {}).get('total_gb', 0)} GB")
                else:
                    print(f"  [FAIL] 获取系统资源失败: {response.status_code}")
                    print(f"    响应: {response.text}")
            except Exception as e:
                print(f"  [FAIL] 获取系统资源异常: {e}")
            
            print()
            
            # 测试3: 获取系统资源历史记录
            print("[测试3] 获取系统资源历史记录...")
            try:
                response = await client.get(
                    f"{base_url}/monitoring/system/history",
                    params={"resource_type": "cpu", "limit": 10}
                )
                if response.status_code == 200:
                    data = response.json()
                    history = data.get("data", {})
                    cpu_history = history.get("cpu", [])
                    
                    print(f"  [OK] CPU历史记录获取成功，共 {len(cpu_history)} 条")
                    if cpu_history:
                        latest = cpu_history[-1]
                        print(f"    最新记录: {latest.get('usage_percent', 0)}% (时间: {latest.get('timestamp', 'N/A')})")
                else:
                    print(f"  [FAIL] 获取历史记录失败: {response.status_code}")
            except Exception as e:
                print(f"  [FAIL] 获取历史记录异常: {e}")
            
            print()
            
            # 测试4: 获取系统资源统计信息
            print("[测试4] 获取系统资源统计信息...")
            try:
                response = await client.get(f"{base_url}/monitoring/system/statistics")
                if response.status_code == 200:
                    data = response.json()
                    statistics = data.get("data", {})
                    
                    print(f"  [OK] 统计信息获取成功")
                    cpu_stats = statistics.get("cpu", {})
                    memory_stats = statistics.get("memory", {})
                    disk_stats = statistics.get("disk", {})
                    
                    print(f"    CPU统计: 平均={cpu_stats.get('avg', 0)}%, 最小={cpu_stats.get('min', 0)}%, 最大={cpu_stats.get('max', 0)}%")
                    print(f"    内存统计: 平均={memory_stats.get('avg', 0)}%, 最小={memory_stats.get('min', 0)}%, 最大={memory_stats.get('max', 0)}%")
                    print(f"    磁盘统计: 平均={disk_stats.get('avg', 0)}%, 最小={disk_stats.get('min', 0)}%, 最大={disk_stats.get('max', 0)}%")
                else:
                    print(f"  [FAIL] 获取统计信息失败: {response.status_code}")
            except Exception as e:
                print(f"  [FAIL] 获取统计信息异常: {e}")
            
            print()
            
            # 测试5: 获取API性能指标
            print("[测试5] 获取API性能指标...")
            try:
                response = await client.get(f"{base_url}/monitoring/api/performance")
                if response.status_code == 200:
                    data = response.json()
                    metrics = data.get("data", {})
                    summary = metrics.get("summary", {})
                    
                    print(f"  [OK] API性能指标获取成功")
                    print(f"    总请求数: {summary.get('total_requests', 0)}")
                    print(f"    总错误数: {summary.get('total_errors', 0)}")
                    print(f"    错误率: {summary.get('error_rate', 0) * 100:.2f}%")
                    print(f"    平均响应时间: {summary.get('avg_response_time', 0):.3f}s")
                    
                    endpoints = metrics.get("endpoints", {})
                    if endpoints:
                        print(f"    端点数量: {len(endpoints)}")
                        # 显示前3个端点的指标
                        for i, (endpoint, endpoint_metrics) in enumerate(list(endpoints.items())[:3]):
                            print(f"      - {endpoint}: {endpoint_metrics.get('request_count', 0)} 请求")
                else:
                    print(f"  [FAIL] 获取API性能指标失败: {response.status_code}")
            except Exception as e:
                print(f"  [FAIL] 获取API性能指标异常: {e}")
            
            print()
            
            # 测试6: 获取慢端点列表
            print("[测试6] 获取慢端点列表...")
            try:
                response = await client.get(
                    f"{base_url}/monitoring/api/slow-endpoints",
                    params={"threshold": 0.5, "limit": 10}
                )
                if response.status_code == 200:
                    data = response.json()
                    slow_endpoints = data.get("data", [])
                    
                    print(f"  [OK] 慢端点列表获取成功，共 {len(slow_endpoints)} 个")
                    for endpoint in slow_endpoints[:5]:
                        print(f"    - {endpoint.get('endpoint', 'N/A')}: {endpoint.get('avg_response_time', 0):.3f}s ({endpoint.get('count', 0)} 请求)")
                else:
                    print(f"  [FAIL] 获取慢端点列表失败: {response.status_code}")
            except Exception as e:
                print(f"  [FAIL] 获取慢端点列表异常: {e}")
            
            print()
            
            # 测试7: 获取错误端点列表
            print("[测试7] 获取错误端点列表...")
            try:
                response = await client.get(
                    f"{base_url}/monitoring/api/error-endpoints",
                    params={"limit": 10}
                )
                if response.status_code == 200:
                    data = response.json()
                    error_endpoints = data.get("data", [])
                    
                    print(f"  [OK] 错误端点列表获取成功，共 {len(error_endpoints)} 个")
                    for endpoint in error_endpoints[:5]:
                        print(f"    - 时间: {endpoint.get('timestamp', 'N/A')}, 错误数: {endpoint.get('error_count', 0)}, 错误率: {endpoint.get('error_rate', 0) * 100:.2f}%")
                else:
                    print(f"  [FAIL] 获取错误端点列表失败: {response.status_code}")
            except Exception as e:
                print(f"  [FAIL] 获取错误端点列表异常: {e}")
            
            print()
            
            # 测试8: 获取API性能历史记录
            print("[测试8] 获取API性能历史记录...")
            try:
                response = await client.get(
                    f"{base_url}/monitoring/api/history",
                    params={"limit": 10}
                )
                if response.status_code == 200:
                    data = response.json()
                    history = data.get("data", {})
                    
                    response_times = history.get("response_times", {})
                    errors = history.get("errors", [])
                    request_counts = history.get("request_counts", {})
                    
                    print(f"  [OK] API性能历史记录获取成功")
                    print(f"    响应时间历史: {len(response_times)} 个端点")
                    print(f"    错误历史: {len(errors)} 条")
                    print(f"    请求数量历史: {len(request_counts)} 个端点")
                else:
                    print(f"  [FAIL] 获取API性能历史失败: {response.status_code}")
            except Exception as e:
                print(f"  [FAIL] 获取API性能历史异常: {e}")
            
            print()
            print("=" * 60)
            print("系统监控功能测试完成")
            print("=" * 60)
            print()
            print("提示: WebSocket实时推送功能需要在浏览器中测试")
            print("  连接地址: ws://localhost:8092/api/ws/ws")
            print("  订阅主题: ['system', 'api_performance']")
            
    except Exception as e:
        print(f"  [FAIL] 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_system_monitoring())

