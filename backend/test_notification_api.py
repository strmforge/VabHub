"""
测试通知API功能
"""

import asyncio
import httpx

# 测试配置 - 使用正确的端口和API前缀
BASE_URL = "http://localhost:8092"
API_PREFIX = "/api"

async def test_notifications():
    """测试通知API功能"""
    async with httpx.AsyncClient() as client:
        # 测试1: 获取通知列表
        print("测试1: 获取通知列表")
        response = await client.get(f"{BASE_URL}{API_PREFIX}/notifications/")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"响应: {response.json()}")
        else:
            print(f"响应: {response.text}")
        
        # 测试2: 创建通知
        print("\n测试2: 创建通知")
        notification_data = {
            "title": "测试通知",
            "message": "这是一个测试通知",
            "level": "info",
            "extra_metadata": {"test": "data"}
        }
        response = await client.post(f"{BASE_URL}{API_PREFIX}/notifications/", json=notification_data)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"响应: {response.json()}")
        else:
            print(f"响应: {response.text}")
        
        # 测试3: 再次获取通知列表验证创建成功
        print("\n测试3: 验证通知列表更新")
        response = await client.get(f"{BASE_URL}{API_PREFIX}/notifications/")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"响应: {response.json()}")
        else:
            print(f"响应: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_notifications())