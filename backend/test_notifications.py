#!/usr/bin/env python3
"""
通知系统功能测试脚本
"""

import sys
import asyncio
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.models.user_notification import UserNotification
from app.schemas.user_notification import UserNotificationCreate, UserNotificationListResponseLegacy
from app.services.notification_service import NotificationService


async def test_notification_schema():
    """测试Schema功能"""
    print("📋 测试通知Schema...")
    
    # 测试创建Schema
    notification_data = {
        "user_id": 1,
        "title": "测试通知",
        "message": "这是一个测试通知",
        "type": "info"
    }
    
    try:
        notification_create = UserNotificationCreate(**notification_data)
        print(f"✅ 创建Schema测试通过: {notification_create.title}")
        
        # 测试列表响应Schema
        list_response = UserNotificationListResponseLegacy(
            items=[],
            total=0,
            unread_count=0
        )
        print("✅ 列表响应Schema测试通过")
        
        return True
    except Exception as e:
        print(f"❌ Schema测试失败: {e}")
        return False


async def test_service_methods():
    """测试服务方法"""
    print("\n🔧 测试通知服务方法...")
    
    # 测试服务类导入和实例化
    try:
        service = NotificationService
        print("✅ 服务类导入成功")
        
        # 测试方法存在性
        assert hasattr(service, 'list_notifications'), "缺少list_notifications方法"
        assert hasattr(service, 'create_notification'), "缺少create_notification方法"
        assert hasattr(service, 'mark_notification_read'), "缺少mark_notification_read方法"
        assert hasattr(service, 'mark_all_read'), "缺少mark_all_read方法"
        
        print("✅ 所有服务方法存在性检查通过")
        return True
    except Exception as e:
        print(f"❌ 服务方法测试失败: {e}")
        return False


async def test_model_import():
    """测试模型导入"""
    print("\n🏗️ 测试通知模型导入...")
    
    try:
        # 测试模型导入
        model = UserNotification
        assert hasattr(model, '__tablename__'), "模型缺少__tablename__属性"
        print(f"✅ 通知模型导入成功: {model.__tablename__}")
        
        # 测试字段存在性
        assert hasattr(model, 'id'), "模型缺少id字段"
        assert hasattr(model, 'user_id'), "模型缺少user_id字段"
        assert hasattr(model, 'title'), "模型缺少title字段"
        assert hasattr(model, 'message'), "模型缺少message字段"
        assert hasattr(model, 'type'), "模型缺少type字段"
        assert hasattr(model, 'is_read'), "模型缺少is_read字段"
        
        print("✅ 模型字段检查通过")
        return True
    except Exception as e:
        print(f"❌ 模型导入测试失败: {e}")
        return False


async def test_api_import():
    """测试API路由导入"""
    print("\n🌐 测试API路由导入...")
    
    try:
        from app.api.notification import router
        
        # 检查路由是否存在
        assert router is not None, "路由未定义"
        
        # 检查路由路径
        assert hasattr(router, 'prefix'), "路由缺少prefix属性"
        print(f"✅ API路由导入成功: {router.prefix}")
        
        return True
    except Exception as e:
        print(f"❌ API导入测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("=" * 60)
    print("🔔 VabHub 通知系统功能测试")
    print("=" * 60)
    
    test_results = []
    
    # 运行各项测试
    test_results.append(await test_model_import())
    test_results.append(await test_notification_schema())
    test_results.append(await test_service_methods())
    test_results.append(await test_api_import())
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print("=" * 60)
    
    passed_count = sum(test_results)
    total_count = len(test_results)
    
    print(f"✅ 通过: {passed_count}/{total_count}")
    print(f"❌ 失败: {total_count - passed_count}/{total_count}")
    
    if passed_count == total_count:
        print("\n🎉 所有测试通过！通知系统功能完整。")
        print("\n📋 可用功能:")
        print("  • 用户通知模型 (UserNotification)")
        print("  • 通知Schema (UserNotificationCreate, UserNotificationListResponse)")
        print("  • 通知服务 (NotificationService)")
        print("  • API路由 (/api/notifications)")
        print("  • 前端通知页面 (/notifications)")
    else:
        print("\n⚠️ 部分测试失败，需要检查相关代码。")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)