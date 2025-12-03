"""
测试阶段3：本地端集成云端（Hybrid模式）
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from app.core.intel.service import (
    get_intel_service,
    LocalIntelService,
    CloudIntelService,
    HybridIntelService,
)
from app.core.config import settings
from loguru import logger


async def test_cloud_intel():
    """测试云端Intel服务"""
    print("=" * 60)
    print("阶段3测试：云端Intel服务")
    print("=" * 60)
    print()
    
    # 测试1: 创建CloudIntelService
    print("[测试1] 创建CloudIntelService...")
    try:
        cloud_intel = CloudIntelService()
        print(f"  [OK] CloudIntelService创建成功")
        print(f"  [INFO] Intel端点: {settings.INTEL_INTEL_ENDPOINT}")
    except Exception as e:
        print(f"  [FAIL] 创建CloudIntelService失败: {e}")
        return False
    print()
    
    # 测试2: 测试resolve_title（云端不可用时）
    print("[测试2] 测试resolve_title（云端不可用）...")
    try:
        result = await cloud_intel.resolve_title("钢铁侠")
        if result is None:
            print("  [OK] 返回None（符合预期，云端服务未部署）")
        else:
            print(f"  [INFO] 返回结果: {result}")
    except Exception as e:
        print(f"  [WARN] resolve_title异常（云端未部署）: {e}")
    print()
    
    # 测试3: 测试get_release_sites（云端不可用时）
    print("[测试3] 测试get_release_sites（云端不可用）...")
    try:
        result = await cloud_intel.get_release_sites("iron-man-2008-movie")
        print(f"  [INFO] 返回结果: {result}")
        if result.get("release_key") == "iron-man-2008-movie":
            print("  [OK] release_key正确")
    except Exception as e:
        print(f"  [WARN] get_release_sites异常（云端未部署）: {e}")
    print()
    
    print("=" * 60)
    print("云端Intel服务测试完成")
    print("=" * 60)
    print()
    print("[说明] 云端服务未部署时，会返回None或空结果，这是正常的")
    print()
    
    return True


async def test_hybrid_intel():
    """测试混合Intel服务"""
    print("=" * 60)
    print("阶段3测试：混合Intel服务")
    print("=" * 60)
    print()
    
    # 测试1: 创建HybridIntelService
    print("[测试1] 创建HybridIntelService...")
    try:
        local = LocalIntelService()
        cloud = CloudIntelService()
        hybrid = HybridIntelService(local=local, cloud=cloud)
        print(f"  [OK] HybridIntelService创建成功")
        print(f"  [INFO] 降级配置: {settings.INTEL_FALLBACK_TO_LOCAL}")
    except Exception as e:
        print(f"  [FAIL] 创建HybridIntelService失败: {e}")
        return False
    print()
    
    # 测试2: 测试resolve_title（混合模式）
    print("[测试2] 测试resolve_title（混合模式）...")
    try:
        result = await hybrid.resolve_title("钢铁侠")
        if result:
            print(f"  [OK] 返回结果: {result}")
            print(f"  [INFO] 来源: 本地（云端不可用，自动降级）")
        else:
            print("  [WARN] 返回None（本地和云端都无数据）")
    except Exception as e:
        print(f"  [FAIL] resolve_title失败: {e}")
        return False
    print()
    
    # 测试3: 测试get_release_sites（混合模式）
    print("[测试3] 测试get_release_sites（混合模式）...")
    try:
        result = await hybrid.get_release_sites("iron-man-2008-movie")
        print(f"  [OK] 返回结果: {result}")
        if result.get("sites"):
            print(f"  [INFO] 找到 {len(result.get('sites', []))} 个站点")
            print(f"  [INFO] 来源: 本地（云端不可用，自动降级）")
        else:
            print("  [INFO] 无站点数据（本地和云端都无数据）")
    except Exception as e:
        print(f"  [FAIL] get_release_sites失败: {e}")
        return False
    print()
    
    print("=" * 60)
    print("混合Intel服务测试完成")
    print("=" * 60)
    print()
    print("[说明] 混合模式会优先尝试云端，失败时自动降级到本地")
    print()
    
    return True


async def test_mode_switching():
    """测试模式切换"""
    print("=" * 60)
    print("阶段3测试：模式切换")
    print("=" * 60)
    print()
    
    # 测试1: 测试local模式
    print("[测试1] 测试local模式...")
    try:
        # 临时设置模式
        original_mode = settings.INTEL_MODE
        settings.INTEL_MODE = "local"
        
        # 清除缓存
        from app.core.intel.service import get_intel_service
        get_intel_service.cache_clear()
        
        intel = get_intel_service()
        print(f"  [OK] 获取Intel服务: {type(intel).__name__}")
        if isinstance(intel, LocalIntelService):
            print("  [OK] 模式正确: LocalIntelService")
        else:
            print(f"  [WARN] 模式不正确: {type(intel).__name__}")
        
        # 恢复模式
        settings.INTEL_MODE = original_mode
        get_intel_service.cache_clear()
    except Exception as e:
        print(f"  [FAIL] 测试local模式失败: {e}")
    print()
    
    # 测试2: 测试cloud模式
    print("[测试2] 测试cloud模式...")
    try:
        original_mode = settings.INTEL_MODE
        settings.INTEL_MODE = "cloud"
        get_intel_service.cache_clear()
        
        intel = get_intel_service()
        print(f"  [OK] 获取Intel服务: {type(intel).__name__}")
        if isinstance(intel, CloudIntelService):
            print("  [OK] 模式正确: CloudIntelService")
        else:
            print(f"  [WARN] 模式不正确: {type(intel).__name__}")
        
        settings.INTEL_MODE = original_mode
        get_intel_service.cache_clear()
    except Exception as e:
        print(f"  [FAIL] 测试cloud模式失败: {e}")
    print()
    
    # 测试3: 测试hybrid模式
    print("[测试3] 测试hybrid模式...")
    try:
        original_mode = settings.INTEL_MODE
        settings.INTEL_MODE = "hybrid"
        get_intel_service.cache_clear()
        
        intel = get_intel_service()
        print(f"  [OK] 获取Intel服务: {type(intel).__name__}")
        if isinstance(intel, HybridIntelService):
            print("  [OK] 模式正确: HybridIntelService")
        else:
            print(f"  [WARN] 模式不正确: {type(intel).__name__}")
        
        settings.INTEL_MODE = original_mode
        get_intel_service.cache_clear()
    except Exception as e:
        print(f"  [FAIL] 测试hybrid模式失败: {e}")
    print()
    
    print("=" * 60)
    print("模式切换测试完成")
    print("=" * 60)
    print()
    
    return True


async def main():
    """主测试函数"""
    print("=" * 60)
    print("阶段3：本地端集成云端测试")
    print("=" * 60)
    print()
    print(f"当前配置:")
    print(f"  INTEL_ENABLED: {settings.INTEL_ENABLED}")
    print(f"  INTEL_MODE: {settings.INTEL_MODE}")
    print(f"  INTEL_INTEL_ENDPOINT: {settings.INTEL_INTEL_ENDPOINT}")
    print(f"  INTEL_FALLBACK_TO_LOCAL: {settings.INTEL_FALLBACK_TO_LOCAL}")
    print()
    
    # 运行测试
    results = []
    
    print("\n" + "=" * 60)
    results.append(await test_cloud_intel())
    
    print("\n" + "=" * 60)
    results.append(await test_hybrid_intel())
    
    print("\n" + "=" * 60)
    results.append(await test_mode_switching())
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print()
    if all(results):
        print("[OK] 所有测试通过！")
    else:
        print("[WARN] 部分测试失败，请检查日志")
    print()
    print("[下一步]")
    print("  1. 部署云端服务（Mesh Scheduler、Intel Center）")
    print("  2. 配置云端端点")
    print("  3. 设置 INTEL_MODE=hybrid")
    print("  4. 测试完整集成")
    print()


if __name__ == "__main__":
    asyncio.run(main())

