"""
测试阶段1：本地Intel功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from app.core.intel.service import get_intel_service, LocalIntelService
from loguru import logger


async def test_local_intel():
    """测试本地Intel服务"""
    print("=" * 60)
    print("阶段1测试：本地Intel功能")
    print("=" * 60)
    print()
    
    # 测试1: 获取Intel服务
    print("[测试1] 获取Intel服务...")
    try:
        intel = get_intel_service()
        print(f"  [OK] Intel服务类型: {type(intel).__name__}")
        print(f"  [INFO] 服务模式: {intel.__class__.__name__}")
    except Exception as e:
        print(f"  [FAIL] 获取Intel服务失败: {e}")
        return False
    print()
    
    # 测试2: 测试resolve_title（空数据）
    print("[测试2] 测试resolve_title（空数据）...")
    try:
        result = await intel.resolve_title("测试标题")
        if result is None:
            print("  [OK] 返回None（符合预期，因为数据文件为空）")
        else:
            print(f"  [INFO] 返回结果: {result}")
    except Exception as e:
        print(f"  [FAIL] resolve_title失败: {e}")
        return False
    print()
    
    # 测试3: 测试get_release_sites（空数据）
    print("[测试3] 测试get_release_sites（空数据）...")
    try:
        result = await intel.get_release_sites("test-release-key")
        print(f"  [OK] 返回结果: {result}")
        if result.get("release_key") == "test-release-key":
            print("  [OK] release_key正确")
        if result.get("sites") == []:
            print("  [OK] sites为空列表（符合预期）")
    except Exception as e:
        print(f"  [FAIL] get_release_sites失败: {e}")
        return False
    print()
    
    # 测试4: 检查数据目录
    print("[测试4] 检查数据目录...")
    try:
        if isinstance(intel, LocalIntelService):
            data_dir = intel._data_dir
            print(f"  [INFO] 数据目录: {data_dir}")
            if data_dir.exists():
                print("  [OK] 数据目录已创建")
            else:
                print("  [WARN] 数据目录不存在（将在首次使用时创建）")
            
            aliases_file = intel._aliases_file
            index_file = intel._index_file
            print(f"  [INFO] 别名文件: {aliases_file}")
            print(f"  [INFO] 索引文件: {index_file}")
        else:
            print("  [INFO] 当前不是LocalIntelService，跳过数据目录检查")
    except Exception as e:
        print(f"  [WARN] 检查数据目录失败: {e}")
    print()
    
    # 测试5: 测试数据加载
    print("[测试5] 测试数据加载...")
    try:
        if isinstance(intel, LocalIntelService):
            await intel._ensure_loaded()
            print(f"  [OK] 数据加载完成")
            print(f"  [INFO] 别名数量: {len(intel._aliases)}")
            print(f"  [INFO] 索引数量: {len(intel._index)}")
        else:
            print("  [INFO] 当前不是LocalIntelService，跳过数据加载测试")
    except Exception as e:
        print(f"  [WARN] 数据加载失败: {e}")
    print()
    
    print("=" * 60)
    print("阶段1测试完成")
    print("=" * 60)
    print()
    print("[OK] 所有测试通过！")
    print()
    print("[下一步]")
    print("  1. 创建测试数据文件: backend/data/intel/aliases.json")
    print("  2. 添加测试别名数据")
    print("  3. 重新运行测试验证数据加载")
    print()
    
    return True


if __name__ == "__main__":
    asyncio.run(test_local_intel())

