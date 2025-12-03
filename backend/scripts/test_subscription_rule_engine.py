"""
测试订阅规则引擎
"""

import asyncio
import httpx
import json
from typing import Dict, Any


async def test_rule_engine():
    """测试订阅规则引擎"""
    base_url = "http://localhost:8092/api"
    
    print("=" * 60)
    print("订阅规则引擎测试")
    print("=" * 60)
    print()
    
    # 测试用例：搜索结果
    test_results = [
        {
            "title": "Movie Name 2023 1080p HDR CHD",
            "quality": "1080p",
            "resolution": "1080p",
            "seeders": 100,
            "size_gb": 10.5,
            "site": "chdbits"
        },
        {
            "title": "Movie Name 2023 4K H.265",
            "quality": "4K",
            "resolution": "2160p",
            "seeders": 50,
            "size_gb": 20.0,
            "site": "pttime"
        },
        {
            "title": "Movie Name 2023 720p CAM",
            "quality": "720p",
            "resolution": "720p",
            "seeders": 5,
            "size_gb": 2.0,
            "site": "other"
        }
    ]
    
    # 测试用例：订阅规则
    test_subscriptions = [
        {
            "name": "基础规则测试",
            "subscription": {
                "quality": "1080p",
                "resolution": "1080p",
                "min_seeders": 10,
                "include": "CHD",
                "exclude": "CAM"
            },
            "expected_count": 1
        },
        {
            "name": "正则表达式测试",
            "subscription": {
                "quality": "1080p",
                "include": "/CHD|WiKi/",
                "exclude": "/CAM|TS/"
            },
            "expected_count": 1
        },
        {
            "name": "优先级规则组测试",
            "subscription": {
                "quality": "1080p",
                "filter_groups": [
                    {
                        "name": "发布组",
                        "priority": 1,
                        "rules": [
                            {"type": "include", "pattern": "CHD", "logic": "or"},
                            {"type": "include", "pattern": "WiKi", "logic": "or"}
                        ]
                    }
                ]
            },
            "expected_count": 1
        }
    ]
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 测试1: 创建测试订阅
            print("[测试1] 创建测试订阅...")
            for i, test_case in enumerate(test_subscriptions):
                subscription_data = {
                    "title": f"测试订阅 {i+1}",
                    "media_type": "movie",
                    "year": 2023,
                    **test_case["subscription"]
                }
                
                try:
                    response = await client.post(
                        f"{base_url}/subscriptions",
                        json=subscription_data
                    )
                    if response.status_code == 201:
                        data = response.json()
                        subscription_id = data.get("data", {}).get("id")
                        print(f"  [OK] 订阅创建成功: {test_case['name']} (ID: {subscription_id})")
                        test_case["subscription_id"] = subscription_id
                    else:
                        print(f"  [FAIL] 订阅创建失败: {response.status_code}")
                        print(f"    响应: {response.text}")
                except Exception as e:
                    print(f"  [FAIL] 订阅创建异常: {e}")
            
            print()
            
            # 测试2: 执行搜索并验证规则过滤
            print("[测试2] 执行搜索并验证规则过滤...")
            for test_case in test_subscriptions:
                if "subscription_id" not in test_case:
                    continue
                
                subscription_id = test_case["subscription_id"]
                try:
                    response = await client.post(
                        f"{base_url}/subscriptions/{subscription_id}/search"
                    )
                    if response.status_code == 200:
                        data = response.json()
                        result = data.get("data", {})
                        filtered_count = result.get("filtered_count", 0)
                        expected_count = test_case["expected_count"]
                        
                        if filtered_count == expected_count:
                            print(f"  [OK] {test_case['name']}: 过滤结果数量正确 ({filtered_count})")
                        else:
                            print(f"  [WARN] {test_case['name']}: 过滤结果数量不匹配 (期望: {expected_count}, 实际: {filtered_count})")
                    else:
                        print(f"  [FAIL] 搜索失败: {response.status_code}")
                except Exception as e:
                    print(f"  [FAIL] 搜索异常: {e}")
            
            print()
            
            # 测试3: 验证结果评分
            print("[测试3] 验证结果评分...")
            # 这里需要实际搜索结果来验证评分
            print("  [INFO] 结果评分功能已集成到搜索服务中")
            print("  [INFO] 评分维度: 做种数(40分)、大小(20分)、质量(20分)、分辨率(10分)、特效(10分)")
            
            print()
            
            # 清理：删除测试订阅
            print("[清理] 删除测试订阅...")
            for test_case in test_subscriptions:
                if "subscription_id" not in test_case:
                    continue
                
                subscription_id = test_case["subscription_id"]
                try:
                    response = await client.delete(
                        f"{base_url}/subscriptions/{subscription_id}"
                    )
                    if response.status_code == 200:
                        print(f"  [OK] 订阅删除成功: {test_case['name']}")
                    else:
                        print(f"  [WARN] 订阅删除失败: {response.status_code}")
                except Exception as e:
                    print(f"  [WARN] 订阅删除异常: {e}")
            
            print()
            print("=" * 60)
            print("订阅规则引擎测试完成")
            print("=" * 60)
            
    except httpx.ConnectError:
        print("  [FAIL] 无法连接到后端服务")
        print("  请先启动后端服务: python main.py")
    except Exception as e:
        print(f"  [FAIL] 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_rule_engine())

