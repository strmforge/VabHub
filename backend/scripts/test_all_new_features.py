"""
测试所有新功能
综合测试脚本
"""

import asyncio
import httpx
import sys
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_subscription_rule_engine import test_rule_engine
from test_subscription_history import test_subscription_history
from test_subscription_status import test_subscription_status
from test_system_monitoring import test_system_monitoring


async def test_all_features():
    """测试所有新功能"""
    print("=" * 80)
    print("VabHub 新功能综合测试")
    print("=" * 80)
    print()
    
    # 检查后端服务
    print("[检查] 后端服务状态...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
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
    print("=" * 80)
    print()
    
    # 测试1: 订阅规则引擎
    print("\n" + "=" * 80)
    print("测试1: 订阅规则引擎")
    print("=" * 80)
    await test_rule_engine()
    
    print()
    print("=" * 80)
    print()
    
    # 测试2: 订阅历史记录
    print("\n" + "=" * 80)
    print("测试2: 订阅历史记录功能")
    print("=" * 80)
    await test_subscription_history()
    
    print()
    print("=" * 80)
    print()
    
    # 测试3: 订阅状态管理
    print("\n" + "=" * 80)
    print("测试3: 订阅状态管理功能")
    print("=" * 80)
    await test_subscription_status()
    
    print()
    print("=" * 80)
    print()
    
    # 测试4: 系统监控
    print("\n" + "=" * 80)
    print("测试4: 系统监控功能")
    print("=" * 80)
    await test_system_monitoring()
    
    print()
    print("=" * 80)
    print()
    print("=" * 80)
    print("所有功能测试完成")
    print("=" * 80)
    print()
    print("前端功能测试:")
    print("  - 图片懒加载: 请参考 前端功能测试指南.md")
    print("  - 搜索防抖: 请参考 前端功能测试指南.md")
    print("  - WebSocket实时推送: 请参考 前端功能测试指南.md")
    print()


if __name__ == "__main__":
    asyncio.run(test_all_features())

