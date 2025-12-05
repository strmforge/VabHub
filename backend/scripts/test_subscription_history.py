"""
测试订阅历史记录功能
"""

import asyncio
import httpx


async def test_subscription_history():
    """测试订阅历史记录功能"""
    base_url = "http://localhost:8092/api"
    
    print("=" * 60)
    print("订阅历史记录功能测试")
    print("=" * 60)
    print()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 测试1: 健康检查
            print("[测试1] 健康检查...")
            try:
                response = await client.get("http://localhost:8092/health")
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
            
            # 测试2: 创建订阅（应该记录创建历史）
            print("[测试2] 创建订阅并验证历史记录...")
            subscription_data = {
                "title": "测试订阅历史",
                "media_type": "movie",
                "year": 2023,
                "quality": "1080p",
                "auto_download": True
            }
            
            try:
                response = await client.post(
                    f"{base_url}/subscriptions",
                    json=subscription_data,
                    follow_redirects=True
                )
                if response.status_code == 201:
                    data = response.json()
                    subscription_id = data.get("data", {}).get("id")
                    print(f"  [OK] 订阅创建成功 (ID: {subscription_id})")
                    
                    # 等待一下，确保历史记录已保存
                    await asyncio.sleep(0.5)
                    
                    # 获取历史记录
                    history_response = await client.get(
                        f"{base_url}/subscriptions/{subscription_id}/history",
                        params={"action_type": "operation", "limit": 10}
                    )
                    if history_response.status_code == 200:
                        history_data = history_response.json()
                        history_list = history_data.get("data", [])
                        
                        # 查找创建历史
                        create_history = [h for h in history_list if h.get("action") == "create"]
                        if create_history:
                            print("  [OK] 创建历史记录已保存")
                            print(f"    描述: {create_history[0].get('description')}")
                        else:
                            print("  [WARN] 未找到创建历史记录")
                    else:
                        print(f"  [WARN] 获取历史记录失败: {history_response.status_code}")
                else:
                    print(f"  [FAIL] 订阅创建失败: {response.status_code}")
                    print(f"    响应: {response.text}")
                    return False
            except Exception as e:
                print(f"  [FAIL] 创建订阅异常: {e}")
                import traceback
                traceback.print_exc()
                return False
            
            print()
            
            # 测试3: 更新订阅（应该记录更新历史）
            print("[测试3] 更新订阅并验证历史记录...")
            try:
                update_data = {
                    "quality": "4K",
                    "resolution": "2160p"
                }
                response = await client.put(
                    f"{base_url}/subscriptions/{subscription_id}",
                    json=update_data
                )
                if response.status_code == 200:
                    print("  [OK] 订阅更新成功")
                    
                    # 等待一下
                    await asyncio.sleep(0.5)
                    
                    # 获取更新历史
                    history_response = await client.get(
                        f"{base_url}/subscriptions/{subscription_id}/history",
                        params={"action_type": "operation", "limit": 10}
                    )
                    if history_response.status_code == 200:
                        history_data = history_response.json()
                        history_list = history_data.get("data", [])
                        
                        # 查找更新历史
                        update_history = [h for h in history_list if h.get("action") == "update"]
                        if update_history:
                            print("  [OK] 更新历史记录已保存")
                            print(f"    描述: {update_history[0].get('description')}")
                            print(f"    旧值: {update_history[0].get('old_value')}")
                            print(f"    新值: {update_history[0].get('new_value')}")
                        else:
                            print("  [WARN] 未找到更新历史记录")
            except Exception as e:
                print(f"  [FAIL] 更新订阅异常: {e}")
            
            print()
            
            # 测试4: 启用/禁用订阅（应该记录状态变更历史）
            print("[测试4] 禁用订阅并验证状态变更历史...")
            try:
                response = await client.post(
                    f"{base_url}/subscriptions/{subscription_id}/disable"
                )
                if response.status_code == 200:
                    print("  [OK] 订阅禁用成功")
                    
                    # 等待一下
                    await asyncio.sleep(0.5)
                    
                    # 获取状态变更历史
                    history_response = await client.get(
                        f"{base_url}/subscriptions/{subscription_id}/history",
                        params={"action_type": "operation", "limit": 10}
                    )
                    if history_response.status_code == 200:
                        history_data = history_response.json()
                        history_list = history_data.get("data", [])
                        
                        # 查找禁用历史
                        disable_history = [h for h in history_list if h.get("action") == "disable"]
                        if disable_history:
                            print("  [OK] 禁用历史记录已保存")
                            print(f"    描述: {disable_history[0].get('description')}")
                            print(f"    状态变更: {disable_history[0].get('old_value')} -> {disable_history[0].get('new_value')}")
                        else:
                            print("  [WARN] 未找到禁用历史记录")
            except Exception as e:
                print(f"  [FAIL] 禁用订阅异常: {e}")
            
            print()
            
            # 测试5: 执行搜索（应该记录搜索历史）
            print("[测试5] 执行搜索并验证搜索历史...")
            try:
                # 先启用订阅
                await client.post(f"{base_url}/subscriptions/{subscription_id}/enable")
                
                response = await client.post(
                    f"{base_url}/subscriptions/{subscription_id}/search"
                )
                if response.status_code == 200:
                    print("  [OK] 搜索执行成功")
                    
                    # 等待一下
                    await asyncio.sleep(0.5)
                    
                    # 获取搜索历史
                    history_response = await client.get(
                        f"{base_url}/subscriptions/{subscription_id}/history",
                        params={"action_type": "search", "limit": 10}
                    )
                    if history_response.status_code == 200:
                        history_data = history_response.json()
                        history_list = history_data.get("data", [])
                        
                        # 查找搜索历史
                        search_history = [h for h in history_list if h.get("action") == "search"]
                        if search_history:
                            print("  [OK] 搜索历史记录已保存")
                            print(f"    描述: {search_history[0].get('description')}")
                            print(f"    搜索关键词: {search_history[0].get('search_query')}")
                            print(f"    结果数量: {search_history[0].get('search_results_count')}")
                        else:
                            print("  [WARN] 未找到搜索历史记录")
            except Exception as e:
                print(f"  [FAIL] 执行搜索异常: {e}")
            
            print()
            
            # 测试6: 获取所有历史记录
            print("[测试6] 获取所有历史记录...")
            try:
                response = await client.get(
                    f"{base_url}/subscriptions/{subscription_id}/history",
                    params={"limit": 50}
                )
                if response.status_code == 200:
                    history_data = response.json()
                    history_list = history_data.get("data", [])
                    print(f"  [OK] 获取历史记录成功，共 {len(history_list)} 条")
                    
                    # 按操作类型分组统计
                    action_counts = {}
                    for h in history_list:
                        action = h.get("action", "unknown")
                        action_counts[action] = action_counts.get(action, 0) + 1
                    
                    print("  操作类型统计:")
                    for action, count in action_counts.items():
                        print(f"    - {action}: {count} 条")
                else:
                    print(f"  [FAIL] 获取历史记录失败: {response.status_code}")
            except Exception as e:
                print(f"  [FAIL] 获取历史记录异常: {e}")
            
            print()
            
            # 测试7: 获取所有订阅的历史记录
            print("[测试7] 获取所有订阅的历史记录...")
            try:
                response = await client.get(
                    f"{base_url}/subscriptions/history",
                    params={"limit": 20}
                )
                if response.status_code == 200:
                    history_data = response.json()
                    history_list = history_data.get("data", [])
                    print(f"  [OK] 获取所有历史记录成功，共 {len(history_list)} 条")
                else:
                    print(f"  [FAIL] 获取所有历史记录失败: {response.status_code}")
            except Exception as e:
                print(f"  [FAIL] 获取所有历史记录异常: {e}")
            
            print()
            
            # 清理：删除测试订阅
            print("[清理] 删除测试订阅...")
            try:
                response = await client.delete(
                    f"{base_url}/subscriptions/{subscription_id}"
                )
                if response.status_code == 200:
                    print("  [OK] 订阅删除成功")
                else:
                    print(f"  [WARN] 订阅删除失败: {response.status_code}")
            except Exception as e:
                print(f"  [WARN] 订阅删除异常: {e}")
            
            print()
            print("=" * 60)
            print("订阅历史记录功能测试完成")
            print("=" * 60)
            
    except Exception as e:
        print(f"  [FAIL] 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_subscription_history())

