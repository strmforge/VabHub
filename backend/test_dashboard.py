"""
仪表盘API测试脚本
"""

import asyncio
import httpx
import sys

from scripts.api_test_config import API_BASE_URL, api_url


async def test_dashboard_api():
    """测试仪表盘API"""
    base_url = API_BASE_URL
    
    print("=" * 60)
    print("VabHub 仪表盘API测试")
    print("=" * 60)
    print()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 测试1: 健康检查
            print("[测试1] 健康检查...")
            try:
                response = await client.get(f"{API_BASE_URL}/health")
                if response.status_code == 200:
                    print("  [OK] 后端服务运行正常")
                else:
                    print(f"  [FAIL] 后端服务响应异常: {response.status_code}")
                    return False
            except httpx.ConnectError:
                print("  [FAIL] 无法连接到后端服务")
                print("  请先启动后端服务: python main.py")
                return False
            
            print()
            
            # 测试2: 系统统计
            print("[测试2] 系统统计API...")
            response = await client.get(api_url("/dashboard/system-stats"))
            if response.status_code == 200:
                data = response.json()
                print("  [OK] 系统统计获取成功")
                print(f"    CPU使用率: {data.get('cpu_usage')}%")
                print(f"    内存使用率: {data.get('memory_usage')}%")
                print(f"    磁盘使用率: {data.get('disk_usage')}%")
            else:
                print(f"  [FAIL] 系统统计获取失败: {response.status_code}")
                print(f"    响应: {response.text}")
                return False
            
            print()
            
            # 测试3: 媒体统计
            print("[测试3] 媒体统计API...")
            response = await client.get(api_url("/dashboard/media-stats"))
            if response.status_code == 200:
                data = response.json()
                print("  [OK] 媒体统计获取成功")
                print(f"    电影数: {data.get('total_movies')}")
                print(f"    电视剧数: {data.get('total_tv_shows')}")
                print(f"    动漫数: {data.get('total_anime')}")
                print(f"    总大小: {data.get('total_size_gb')} GB")
            else:
                print(f"  [FAIL] 媒体统计获取失败: {response.status_code}")
                print(f"    响应: {response.text}")
                return False
            
            print()
            
            # 测试4: 下载统计
            print("[测试4] 下载统计API...")
            response = await client.get(api_url("/dashboard/download-stats"))
            if response.status_code == 200:
                data = response.json()
                print("  [OK] 下载统计获取成功")
                print(f"    活跃下载: {data.get('active')}")
                print(f"    暂停: {data.get('paused')}")
                print(f"    完成: {data.get('completed')}")
                print(f"    总速度: {data.get('total_speed_mbps')} Mbps")
            else:
                print(f"  [FAIL] 下载统计获取失败: {response.status_code}")
                print(f"    响应: {response.text}")
                return False
            
            print()
            
            # 测试5: 综合仪表盘API
            print("[测试5] 综合仪表盘API...")
            response = await client.get(api_url("/dashboard/"))
            if response.status_code == 200:
                data = response.json()
                print("  [OK] 综合仪表盘数据获取成功")
                print(f"    系统统计: CPU {data.get('system_stats', {}).get('cpu_usage')}%")
                print(f"    媒体统计: {data.get('media_stats', {}).get('total_movies')} 部电影")
                print(f"    下载统计: {data.get('download_stats', {}).get('active')} 个活跃下载")
                print(f"    活跃订阅: {data.get('active_subscriptions')}")
            else:
                print(f"  [FAIL] 综合仪表盘数据获取失败: {response.status_code}")
                print(f"    响应: {response.text}")
                return False
            
            print()
            print("=" * 60)
            print("[SUCCESS] 所有仪表盘API测试通过！")
            print("=" * 60)
            return True
            
    except Exception as e:
        print(f"[ERROR] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_dashboard_api())
    sys.exit(0 if success else 1)

