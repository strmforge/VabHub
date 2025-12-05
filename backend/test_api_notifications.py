#!/usr/bin/env python3
"""
测试通知API功能
"""

import requests
import json

BASE_URL = "http://localhost:8092/api"

def test_get_notifications():
    """测试获取通知列表"""
    print("📋 测试获取通知列表...")
    
    try:
        response = requests.get(f"{BASE_URL}/notifications")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 获取通知列表成功")
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ 获取通知列表失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_create_notification():
    """测试创建通知"""
    print("\n📝 测试创建通知...")
    
    notification_data = {
        "title": "测试通知",
        "message": "这是一个测试通知消息",
        "type": "info",
        "channels": ["system"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/notifications",
            json=notification_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print("✅ 创建通知成功")
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ 创建通知失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🔔 VabHub 通知API功能测试")
    print("=" * 60)
    
    test_results = []
    
    # 测试获取通知列表
    test_results.append(test_get_notifications())
    
    # 测试创建通知
    test_results.append(test_create_notification())
    
    print("\n" + "=" * 60)
    print("📊 API测试结果汇总:")
    print("=" * 60)
    
    passed_count = sum(test_results)
    total_count = len(test_results)
    
    print(f"✅ 通过: {passed_count}/{total_count}")
    print(f"❌ 失败: {total_count - passed_count}/{total_count}")
    
    if passed_count == total_count:
        print("\n🎉 所有API测试通过！通知系统功能正常。")
    else:
        print("\n⚠️ 部分API测试失败，需要检查API配置。")
    
    return passed_count == total_count

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)