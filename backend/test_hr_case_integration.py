#!/usr/bin/env python3
"""
HR案件系统集成测试
验证SqlAlchemyHrCasesRepository的双写功能
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.intel_local.models import HRTorrentState, HRStatus, TorrentLife
from app.core.intel_local.hr_state import _HR_STATE_CACHE
from app.modules.hr_case.repository import SqlAlchemyHrCasesRepository, from_hr_torrent_state, to_hr_torrent_state


async def test_dual_write_functionality():
    """测试双写功能：DB和内存缓存同步"""
    print("🧪 测试HR案件系统双写功能...")
    
    # 创建仓库实例
    repo = SqlAlchemyHrCasesRepository()
    
    # 创建测试数据
    site_key = "test_site_hdhome"
    torrent_id = "test_torrent_456"
    
    # 创建HRTorrentState
    hr_state = HRTorrentState(
        site=site_key,
        torrent_id=torrent_id,
        hr_status=HRStatus.ACTIVE,
        life_status=TorrentLife.ALIVE,
        required_seed_hours=72.0,
        seeded_hours=24.5,
        deadline=datetime.utcnow() + timedelta(hours=48),
        first_seen_at=datetime.utcnow() - timedelta(hours=24),
        last_seen_at=datetime.utcnow(),
    )
    
    print(f"📝 测试数据: {site_key}/{torrent_id}")
    print(f"   HR状态: {hr_state.hr_status.value}, 已做种: {hr_state.seeded_hours}h")
    
    try:
        # 1. 测试upsert操作
        print("\n1️⃣ 测试upsert操作...")
        hr_case = await repo.upsert(hr_state)
        
        print(f"   ✅ DB写入成功，HR Case ID: {hr_case.id}")
        print(f"   ✅ 状态: {hr_case.status}, 进度: {hr_case.progress_percentage:.1f}%")
        
        # 2. 验证内存缓存更新
        print("\n2️⃣ 验证内存缓存同步...")
        cache_key = (site_key, torrent_id)
        if cache_key in _HR_STATE_CACHE:
            cache_state = _HR_STATE_CACHE[cache_key]
            print("   ✅ 内存缓存已更新")
            print(f"   ✅ 缓存状态: {cache_state.hr_status.value}, 做种时间: {cache_state.seeded_hours}h")
            
            # 验证数据一致性
            if (cache_state.hr_status == hr_state.hr_status and 
                cache_state.seeded_hours == hr_state.seeded_hours):
                print("   ✅ DB与缓存数据一致")
            else:
                print("   ❌ DB与缓存数据不一致!")
                return False
        else:
            print("   ❌ 内存缓存未更新!")
            return False
        
        # 3. 测试查询功能
        print("\n3️⃣ 测试查询功能...")
        retrieved_case = await repo.get(site_key, torrent_id)
        if retrieved_case:
            print(f"   ✅ 查询成功，状态: {retrieved_case.status}")
            print(f"   ✅ 剩余时间: {retrieved_case.hours_remaining:.1f}h")
        else:
            print("   ❌ 查询失败!")
            return False
        
        # 4. 测试状态更新
        print("\n4️⃣ 测试状态更新...")
        hr_state.hr_status = HRStatus.FINISHED
        hr_state.seeded_hours = 72.0
        updated_case = await repo.upsert(hr_state)
        
        if updated_case.status == "safe":
            print("   ✅ 状态更新成功: ACTIVE -> SAFE")
        else:
            print(f"   ❌ 状态更新失败: 期望safe，实际{updated_case.status}")
            return False
        
        # 5. 测试mark_penalized
        print("\n5️⃣ 测试违规标记...")
        penalized_case = await repo.mark_penalized(site_key, "test_torrent_violated")
        if penalized_case.status == "violated":
            print("   ✅ 违规标记成功")
        else:
            print(f"   ❌ 违规标记失败: 期望violated，实际{penalized_case.status}")
            return False
        
        # 6. 测试一致性检查
        print("\n6️⃣ 测试一致性检查...")
        consistency_result = await repo.check_consistency()
        print(f"   ✅ 检查完成: 检查了{consistency_result.total_checked}项")
        print(f"   ✅ 发现{consistency_result.mismatches}项不一致")
        
        # 7. 清理测试数据
        print("\n7️⃣ 清理测试数据...")
        if cache_key in _HR_STATE_CACHE:
            del _HR_STATE_CACHE[cache_key]
            print("   ✅ 内存缓存已清理")
        
        print("\n🎉 双写功能测试全部通过!")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_conversion_functions():
    """测试转换函数"""
    print("\n🔄 测试转换函数...")
    
    # 创建测试HRTorrentState
    hr_state = HRTorrentState(
        site="test_site",
        torrent_id="test_torrent_789",
        hr_status=HRStatus.ACTIVE,
        life_status=TorrentLife.ALIVE,
        required_seed_hours=48.0,
        seeded_hours=12.0,
    )
    
    # 测试HRTorrentState -> HrCase
    hr_case = from_hr_torrent_state(hr_state, site_id=1, site_key="test_site")
    print(f"   ✅ HRTorrentState -> HrCase: {hr_case.status.value}")
    
    # 测试HrCase -> HRTorrentState
    converted_back = to_hr_torrent_state(hr_case)
    print(f"   ✅ HrCase -> HRTorrentState: {converted_back.hr_status.value}")
    
    # 验证转换一致性
    if (converted_back.hr_status == hr_state.hr_status and 
        converted_back.seeded_hours == hr_state.seeded_hours):
        print("   ✅ 转换函数数据一致")
        return True
    else:
        print("   ❌ 转换函数数据不一致")
        return False


async def main():
    """主测试函数"""
    print("🚀 开始HR案件系统集成测试")
    print("=" * 50)
    
    success = True
    
    # 测试转换函数
    if not await test_conversion_functions():
        success = False
    
    # 测试双写功能
    if not await test_dual_write_functionality():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 所有集成测试通过!")
        print("✅ HR案件系统P1阶段基础设施验证完成")
        print("📋 下一步: 可以开始修改hr_state.py集成新仓库")
    else:
        print("❌ 部分测试失败，请检查实现")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
