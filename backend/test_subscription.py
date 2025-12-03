"""
订阅管理API测试脚本
"""

import asyncio
import httpx
import json

from scripts.api_test_config import API_BASE_URL, api_url

async def test_subscription():
    """测试订阅管理API"""
    async with httpx.AsyncClient() as client:
        print("=" * 60)
        print("订阅管理API测试")
        print("=" * 60)
        
        # 首先登录获取token
        print("\n[1/6] 登录获取Token...")
        try:
            login_response = await client.post(
                api_url("/auth/login"),
                data={
                    "username": "admin",
                    "password": "admin123"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if login_response.status_code == 200:
                token = login_response.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                print("[OK] 登录成功")
            else:
                print(f"[FAIL] 登录失败: {login_response.status_code}")
                return
        except Exception as e:
            print(f"[FAIL] 登录异常: {e}")
            return
        
        # 测试1: 创建订阅
        print("\n[2/6] 创建订阅...")
        try:
            subscription_data = {
                "title": "测试电影",
                "original_title": "Test Movie",
                "year": 2024,
                "media_type": "movie",
                "tmdb_id": 12345,
                "quality_profile": "1080p",
                "min_seeders": 10,
                "auto_download": True
            }
            response = await client.post(
                api_url("/subscriptions"),
                json=subscription_data,
                headers=headers
            )
            if response.status_code == 201:
                subscription = response.json()
                subscription_id = subscription["id"]
                print(f"[OK] 创建订阅成功，ID: {subscription_id}")
                print(f"  标题: {subscription['title']}")
                print(f"  类型: {subscription['media_type']}")
                print(f"  状态: {subscription['status']}")
            else:
                print(f"[FAIL] 创建订阅失败: {response.status_code}")
                print(f"  响应: {response.text}")
                return
        except Exception as e:
            print(f"[FAIL] 创建订阅异常: {e}")
            return
        
        # 测试2: 获取订阅列表
        print("\n[3/6] 获取订阅列表...")
        try:
            response = await client.get(
                api_url("/subscriptions"),
                headers=headers
            )
            if response.status_code == 200:
                subscriptions = response.json()
                print(f"[OK] 获取订阅列表成功，共 {len(subscriptions)} 条")
            else:
                print(f"[FAIL] 获取订阅列表失败: {response.status_code}")
        except Exception as e:
            print(f"[FAIL] 获取订阅列表异常: {e}")
        
        # 测试3: 获取订阅详情
        print("\n[4/6] 获取订阅详情...")
        try:
            response = await client.get(
                api_url(f"/subscriptions/{subscription_id}"),
                headers=headers
            )
            if response.status_code == 200:
                subscription = response.json()
                print(f"[OK] 获取订阅详情成功")
                print(f"  标题: {subscription['title']}")
            else:
                print(f"[FAIL] 获取订阅详情失败: {response.status_code}")
        except Exception as e:
            print(f"[FAIL] 获取订阅详情异常: {e}")
        
        # 测试4: 更新订阅
        print("\n[5/6] 更新订阅...")
        try:
            update_data = {
                "title": "测试电影（已更新）",
                "media_type": "movie",
                "year": 2024,
                "min_seeders": 15
            }
            response = await client.put(
                api_url(f"/subscriptions/{subscription_id}"),
                json=update_data,
                headers=headers
            )
            if response.status_code == 200:
                subscription = response.json()
                print(f"[OK] 更新订阅成功")
                print(f"  新标题: {subscription['title']}")
                print(f"  新最小做种数: {subscription['min_seeders']}")
            else:
                print(f"[FAIL] 更新订阅失败: {response.status_code}")
        except Exception as e:
            print(f"[FAIL] 更新订阅异常: {e}")
        
        # 测试5: 禁用订阅
        print("\n[6/6] 禁用订阅...")
        try:
            response = await client.post(
                api_url(f"/subscriptions/{subscription_id}/disable"),
                headers=headers
            )
            if response.status_code == 200:
                print(f"[OK] 禁用订阅成功")
            else:
                print(f"[WARN] 禁用订阅失败: {response.status_code}")
        except Exception as e:
            print(f"[WARN] 禁用订阅异常: {e}")
        
        # 测试6: 删除订阅
        print("\n[7/6] 删除订阅...")
        try:
            response = await client.delete(
                api_url(f"/subscriptions/{subscription_id}"),
                headers=headers
            )
            if response.status_code == 204:
                print(f"[OK] 删除订阅成功")
            else:
                print(f"[WARN] 删除订阅失败: {response.status_code}")
        except Exception as e:
            print(f"[WARN] 删除订阅异常: {e}")
        
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)

if __name__ == "__main__":
    print(f"\n请确保后端服务已启动 ({API_BASE_URL})")
    print("按 Enter 开始测试...")
    input()
    asyncio.run(test_subscription())

