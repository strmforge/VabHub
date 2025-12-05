"""
测试统一响应模型API
验证所有API端点是否使用统一响应格式
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_response_format(endpoint: str, method: str = "GET", data: dict = None):
    """
    测试API端点是否返回统一响应格式
    
    Args:
        endpoint: API端点路径
        method: HTTP方法
        data: 请求数据（可选）
    """
    try:
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint, json=data if data else {})
        elif method == "PUT":
            response = client.put(endpoint, json=data if data else {})
        elif method == "DELETE":
            response = client.delete(endpoint)
        else:
            print(f"❌ 不支持的方法: {method}")
            return False
        
        # 检查响应状态码
        if response.status_code >= 500:
            print(f"⚠️  {method} {endpoint}: 服务器错误 ({response.status_code})")
            return False
        
        # 尝试解析JSON
        try:
            json_data = response.json()
        except:
            print(f"⚠️  {method} {endpoint}: 响应不是JSON格式")
            return False
        
        # 检查统一响应格式
        if "success" not in json_data:
            print(f"❌ {method} {endpoint}: 缺少'success'字段")
            print(f"   响应: {json_data}")
            return False
        
        if "message" not in json_data:
            print(f"❌ {method} {endpoint}: 缺少'message'字段")
            return False
        
        if "timestamp" not in json_data:
            print(f"❌ {method} {endpoint}: 缺少'timestamp'字段")
            return False
        
        # 检查分页格式（如果是列表端点）
        if "data" in json_data and isinstance(json_data["data"], dict):
            if "items" in json_data["data"] and "total" in json_data["data"]:
                # 这是分页响应
                if "page" not in json_data["data"]:
                    print(f"⚠️  {method} {endpoint}: 分页响应缺少'page'字段")
                    return False
                if "page_size" not in json_data["data"]:
                    print(f"⚠️  {method} {endpoint}: 分页响应缺少'page_size'字段")
                    return False
        
        print(f"✅ {method} {endpoint}: 响应格式正确")
        return True
        
    except Exception as e:
        print(f"❌ {method} {endpoint}: 测试失败 - {str(e)}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("API统一响应模型测试")
    print("=" * 60)
    print()
    
    # 测试端点列表
    test_endpoints = [
        # 订阅管理
        ("GET", "/api/subscriptions/"),
        ("GET", "/api/subscriptions/1"),  # 可能返回404，但格式应该正确
        
        # 下载管理
        ("GET", "/api/downloads/"),
        
        # 搜索系统
        ("POST", "/api/search/", {"query": "test", "media_type": "movie"}),
        
        # 站点管理
        ("GET", "/api/sites/"),
        
        # 工作流
        ("GET", "/api/workflows/"),
        
        # 通知
        ("GET", "/api/notifications/"),
        
        # 仪表盘
        ("GET", "/api/dashboard/"),
        
        # 设置
        ("GET", "/api/settings/"),
        
        # 云存储
        ("GET", "/api/cloud-storage/"),
        
        # 音乐
        ("GET", "/api/music/charts/platforms"),
        ("GET", "/api/music/subscriptions/"),
        
        # 日历
        # ("GET", "/api/calendar/?start_date=2025-01-01T00:00:00&end_date=2025-01-31T23:59:59"),  # 需要日期参数
        
        # HNR检测
        ("GET", "/api/hnr/signatures"),
        ("GET", "/api/hnr/tasks/"),
        ("GET", "/api/hnr/stats"),
        
        # 推荐
        ("GET", "/api/recommendations/popular/recommendations"),
        
        # 媒体识别
        ("GET", "/api/media-identification/history/"),
        ("GET", "/api/media-identification/history/statistics"),
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for item in test_endpoints:
        if len(item) == 2:
            method, endpoint = item
            data = None
        else:
            method, endpoint, data = item
        
        # 跳过需要认证或特殊参数的端点
        if "calendar" in endpoint and "start_date" not in endpoint:
            print(f"⏭️  跳过 {method} {endpoint}: 需要日期参数")
            skipped += 1
            continue
        
        success = test_response_format(endpoint, method, data)
        if success:
            passed += 1
        else:
            failed += 1
    
    print()
    print("=" * 60)
    print("测试结果")
    print("=" * 60)
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"⏭️  跳过: {skipped}")
    print(f"总计: {passed + failed + skipped}")
    print()
    
    if failed == 0:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("⚠️  部分测试失败，请检查上述错误")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

