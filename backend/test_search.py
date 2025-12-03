"""
搜索API测试脚本
"""

import asyncio
import httpx
import json

from scripts.api_test_config import API_BASE_URL, api_url

async def test_search():
    """测试搜索API"""
    async with httpx.AsyncClient() as client:
        print("=" * 60)
        print("搜索API测试")
        print("=" * 60)
        
        # 测试1: 基础搜索
        print("\n[测试1] 基础搜索")
        try:
            response = await client.post(
                api_url("/search"),
                json={
                    "query": "测试",
                    "media_type": None
                }
            )
            if response.status_code == 200:
                results = response.json()
                print(f"[OK] 搜索成功，返回 {len(results)} 条结果")
                if results:
                    print(f"  第一条结果: {results[0].get('title', 'N/A')}")
                    print(f"  站点: {results[0].get('site', 'N/A')}")
                    print(f"  大小: {results[0].get('size_gb', 0)} GB")
                    print(f"  做种数: {results[0].get('seeders', 0)}")
            else:
                print(f"[FAIL] 搜索失败: {response.status_code}")
                print(f"  响应: {response.text}")
        except Exception as e:
            print(f"[FAIL] 请求异常: {e}")
        
        # 测试2: 按类型搜索
        print("\n[测试2] 按类型搜索（电影）")
        try:
            response = await client.post(
                api_url("/search"),
                json={
                    "query": "电影",
                    "media_type": "movie"
                }
            )
            if response.status_code == 200:
                results = response.json()
                print(f"[OK] 搜索成功，返回 {len(results)} 条结果")
            else:
                print(f"[FAIL] 搜索失败: {response.status_code}")
        except Exception as e:
            print(f"[FAIL] 请求异常: {e}")
        
        # 测试3: 带过滤条件搜索
        print("\n[测试3] 带过滤条件搜索（最小做种数）")
        try:
            response = await client.post(
                api_url("/search"),
                json={
                    "query": "测试",
                    "min_seeders": 10,
                    "min_size": 1.0,
                    "max_size": 20.0
                }
            )
            if response.status_code == 200:
                results = response.json()
                print(f"[OK] 搜索成功，返回 {len(results)} 条结果")
                if results:
                    print(f"  所有结果的做种数都 >= 10: {all(r.get('seeders', 0) >= 10 for r in results)}")
                    print(f"  所有结果的大小都在 1-20GB: {all(1.0 <= r.get('size_gb', 0) <= 20.0 for r in results)}")
            else:
                print(f"[FAIL] 搜索失败: {response.status_code}")
        except Exception as e:
            print(f"[FAIL] 请求异常: {e}")
        
        # 测试4: 搜索历史
        print("\n[测试4] 获取搜索历史")
        try:
            response = await client.get(api_url("/search/history"))
            if response.status_code == 200:
                history = response.json()
                print(f"[OK] 获取搜索历史成功，返回 {len(history)} 条记录")
            else:
                print(f"[WARN] 搜索历史功能可能未实现: {response.status_code}")
        except Exception as e:
            print(f"[WARN] 请求异常: {e}")
        
        # 测试5: 搜索建议
        print("\n[测试5] 获取搜索建议")
        try:
            response = await client.get(
                api_url("/search/suggestions"),
                params={"query": "测试"}
            )
            if response.status_code == 200:
                suggestions = response.json()
                print(f"[OK] 获取搜索建议成功，返回 {len(suggestions)} 条建议")
            else:
                print(f"[WARN] 搜索建议功能可能未实现: {response.status_code}")
        except Exception as e:
            print(f"[WARN] 请求异常: {e}")
        
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)

if __name__ == "__main__":
    print(f"\n请确保后端服务已启动 ({API_BASE_URL})")
    print("按 Enter 开始测试...")
    input()
    asyncio.run(test_search())

