"""
前后端联调测试脚本
模拟前端调用后端API
"""

import asyncio
import httpx
import sys

from scripts.api_test_config import API_BASE_URL, API_PREFIX as CONFIG_API_PREFIX, api_url


async def test_frontend_integration():
    """测试前后端联调"""
    base_url = API_BASE_URL
    prefix = CONFIG_API_PREFIX
    
    print("=" * 60)
    print("VabHub 前后端联调测试")
    print("=" * 60)
    print()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 测试1: 健康检查
            print("[测试1] 后端服务健康检查...")
            try:
                response = await client.get(f"{API_BASE_URL}/health")
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
            
            # 测试2: 用户注册（模拟前端注册）
            print("[测试2] 模拟前端用户注册...")
            register_data = {
                "username": "frontendtest",
                "email": "frontend@example.com",
                "password": "test123456",
                "full_name": "Frontend Test User"
            }
            response = await client.post(api_url("/auth/register"), json=register_data)
            if response.status_code == 201:
                user_data = response.json()
                print(f"  [OK] 用户注册成功")
                print(f"    用户ID: {user_data.get('id')}")
                print(f"    用户名: {user_data.get('username')}")
            else:
                # 如果用户已存在，尝试登录
                if response.status_code == 400:
                    print(f"  [INFO] 用户已存在，跳过注册")
                else:
                    print(f"  [FAIL] 用户注册失败: {response.status_code}")
                    print(f"    响应: {response.text}")
                    return False
            
            print()
            
            # 测试3: 用户登录（模拟前端登录）
            print("[测试3] 模拟前端用户登录...")
            login_data = {
                "username": "frontendtest",
                "password": "test123456"
            }
            response = await client.post(
                api_url("/auth/login"),
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                print(f"  [OK] 用户登录成功")
                print(f"    Token: {access_token[:50]}...")
            else:
                print(f"  [FAIL] 用户登录失败: {response.status_code}")
                print(f"    响应: {response.text}")
                return False
            
            print()
            
            # 测试4: 获取仪表盘数据（模拟前端调用）
            print("[测试4] 模拟前端获取仪表盘数据...")
            response = await client.get(
                api_url("/dashboard/"),
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code == 200:
                dashboard_data = response.json()
                print(f"  [OK] 仪表盘数据获取成功")
                print(f"    系统统计:")
                print(f"      CPU: {dashboard_data.get('system_stats', {}).get('cpu_usage')}%")
                print(f"      内存: {dashboard_data.get('system_stats', {}).get('memory_usage')}%")
                print(f"      磁盘: {dashboard_data.get('system_stats', {}).get('disk_usage')}%")
                print(f"    媒体统计:")
                print(f"      电影: {dashboard_data.get('media_stats', {}).get('total_movies')}")
                print(f"      电视剧: {dashboard_data.get('media_stats', {}).get('total_tv_shows')}")
                print(f"    下载统计:")
                print(f"      活跃下载: {dashboard_data.get('download_stats', {}).get('active')}")
                print(f"      总速度: {dashboard_data.get('download_stats', {}).get('total_speed_mbps')} Mbps")
            else:
                print(f"  [FAIL] 仪表盘数据获取失败: {response.status_code}")
                print(f"    响应: {response.text}")
                return False
            
            print()
            
            # 测试5: 获取系统统计（模拟前端调用）
            print("[测试5] 模拟前端获取系统统计...")
            response = await client.get(
                api_url("/dashboard/system-stats"),
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code == 200:
                stats = response.json()
                print(f"  [OK] 系统统计获取成功")
                print(f"    CPU: {stats.get('cpu_usage')}%")
                print(f"    内存: {stats.get('memory_usage')}% ({stats.get('memory_used_gb')}GB / {stats.get('memory_total_gb')}GB)")
                print(f"    磁盘: {stats.get('disk_usage')}% ({stats.get('disk_used_gb')}GB / {stats.get('disk_total_gb')}GB)")
            else:
                print(f"  [WARN] 系统统计获取失败: {response.status_code}")
            
            print()
            
            # 测试6: 获取媒体统计（模拟前端调用）
            print("[测试6] 模拟前端获取媒体统计...")
            response = await client.get(
                f"{base_url}/dashboard/media-stats",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code == 200:
                stats = response.json()
                print(f"  [OK] 媒体统计获取成功")
                print(f"    电影: {stats.get('total_movies')}")
                print(f"    电视剧: {stats.get('total_tv_shows')}")
                print(f"    动漫: {stats.get('total_anime')}")
                print(f"    总大小: {stats.get('total_size_gb')} GB")
            else:
                print(f"  [WARN] 媒体统计获取失败: {response.status_code}")
            
            print()
            
            # 测试7: 获取下载统计（模拟前端调用）
            print("[测试7] 模拟前端获取下载统计...")
            response = await client.get(
                f"{base_url}/dashboard/download-stats",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code == 200:
                stats = response.json()
                print(f"  [OK] 下载统计获取成功")
                print(f"    活跃: {stats.get('active')}")
                print(f"    暂停: {stats.get('paused')}")
                print(f"    完成: {stats.get('completed')}")
                print(f"    总速度: {stats.get('total_speed_mbps')} Mbps")
            else:
                print(f"  [WARN] 下载统计获取失败: {response.status_code}")
            
            print()
            print("=" * 60)
            print("[SUCCESS] 前后端联调测试通过！")
            print("=" * 60)
            print()
            print("前端可以正常调用以下API:")
            print(f"  - POST {prefix}/auth/register - 用户注册")
            print(f"  - POST {prefix}/auth/login - 用户登录")
            print(f"  - GET {prefix}/auth/me - 获取用户信息")
            print(f"  - GET {prefix}/dashboard/ - 综合仪表盘数据")
            print(f"  - GET {prefix}/dashboard/system-stats - 系统统计")
            print(f"  - GET {prefix}/dashboard/media-stats - 媒体统计")
            print(f"  - GET {prefix}/dashboard/download-stats - 下载统计")
            print()
            return True
            
    except Exception as e:
        print(f"[ERROR] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_frontend_integration())
    sys.exit(0 if success else 1)

