"""
测试订阅状态管理功能
"""

import asyncio
import httpx


async def test_subscription_status():
    """测试订阅状态管理功能"""
    base_url = "http://localhost:8092/api"
    
    print("=" * 60)
    print("订阅状态管理功能测试")
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
            
            # 测试2: 创建订阅（默认状态应该是active）
            print("[测试2] 创建订阅并验证默认状态...")
            subscription_data = {
                "title": "测试状态管理",
                "media_type": "movie",
                "year": 2023,
                "quality": "1080p"
            }
            
            try:
                response = await client.post(
                    f"{base_url}/subscriptions",
                    json=subscription_data,
                    follow_redirects=True
                )
                if response.status_code == 201:
                    data = response.json()
                    subscription = data.get("data", {})
                    subscription_id = subscription.get("id")
                    status = subscription.get("status")
                    
                    if status == "active":
                        print(f"  [OK] 订阅创建成功，默认状态为 active (ID: {subscription_id})")
                    else:
                        print(f"  [WARN] 订阅创建成功，但状态为 {status} (期望: active)")
                else:
                    print(f"  [FAIL] 订阅创建失败: {response.status_code}")
                    return False
            except Exception as e:
                print(f"  [FAIL] 创建订阅异常: {e}")
                return False
            
            print()
            
            # 测试3: 禁用订阅（状态应该变为paused）
            print("[测试3] 禁用订阅并验证状态变更...")
            try:
                response = await client.post(
                    f"{base_url}/subscriptions/{subscription_id}/disable"
                )
                if response.status_code == 200:
                    data = response.json()
                    subscription = data.get("data", {})
                    status = subscription.get("status")
                    
                    if status == "paused":
                        print("  [OK] 订阅禁用成功，状态已变更为 paused")
                    else:
                        print(f"  [FAIL] 订阅禁用后状态为 {status} (期望: paused)")
                else:
                    print(f"  [FAIL] 禁用订阅失败: {response.status_code}")
            except Exception as e:
                print(f"  [FAIL] 禁用订阅异常: {e}")
            
            print()
            
            # 测试4: 启用订阅（状态应该变为active）
            print("[测试4] 启用订阅并验证状态变更...")
            try:
                response = await client.post(
                    f"{base_url}/subscriptions/{subscription_id}/enable"
                )
                if response.status_code == 200:
                    data = response.json()
                    subscription = data.get("data", {})
                    status = subscription.get("status")
                    
                    if status == "active":
                        print("  [OK] 订阅启用成功，状态已变更为 active")
                    else:
                        print(f"  [FAIL] 订阅启用后状态为 {status} (期望: active)")
                else:
                    print(f"  [FAIL] 启用订阅失败: {response.status_code}")
            except Exception as e:
                print(f"  [FAIL] 启用订阅异常: {e}")
            
            print()
            
            # 测试5: 验证状态变更历史记录
            print("[测试5] 验证状态变更历史记录...")
            try:
                await asyncio.sleep(0.5)  # 等待历史记录保存
                
                response = await client.get(
                    f"{base_url}/subscriptions/{subscription_id}/history",
                    params={"action_type": "operation", "limit": 10}
                )
                if response.status_code == 200:
                    history_data = response.json()
                    history_list = history_data.get("data", [])
                    
                    # 查找启用和禁用历史
                    enable_history = [h for h in history_list if h.get("action") == "enable"]
                    disable_history = [h for h in history_list if h.get("action") == "disable"]
                    
                    if enable_history and disable_history:
                        print("  [OK] 状态变更历史记录已保存")
                        print(f"    启用记录: {len(enable_history)} 条")
                        print(f"    禁用记录: {len(disable_history)} 条")
                        
                        # 显示最新的状态变更
                        if enable_history:
                            latest = enable_history[0]
                            print(f"    最新启用: {latest.get('old_value')} -> {latest.get('new_value')}")
                    else:
                        print("  [WARN] 未找到完整的状态变更历史记录")
                else:
                    print(f"  [FAIL] 获取历史记录失败: {response.status_code}")
            except Exception as e:
                print(f"  [FAIL] 验证历史记录异常: {e}")
            
            print()
            
            # 测试6: 验证暂停状态下的搜索行为
            print("[测试6] 验证暂停状态下的搜索行为...")
            try:
                # 先禁用订阅
                await client.post(f"{base_url}/subscriptions/{subscription_id}/disable")
                
                # 尝试执行搜索
                response = await client.post(
                    f"{base_url}/subscriptions/{subscription_id}/search"
                )
                if response.status_code == 200:
                    data = response.json()
                    result = data.get("data", {})
                    success = result.get("success", True)
                    message = result.get("message", "")
                    
                    if not success and "无法执行搜索" in message:
                        print("  [OK] 暂停状态下的搜索被正确阻止")
                        print(f"    消息: {message}")
                    else:
                        print("  [WARN] 暂停状态下的搜索未被阻止")
                else:
                    print(f"  [INFO] 搜索请求返回: {response.status_code}")
            except Exception as e:
                print(f"  [FAIL] 验证搜索行为异常: {e}")
            
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
            print("订阅状态管理功能测试完成")
            print("=" * 60)
            
    except Exception as e:
        print(f"  [FAIL] 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_subscription_status())

