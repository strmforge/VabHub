#!/usr/bin/env python3
"""
HR-POLICY-2 P1阶段最终验证测试
验证hr_state.py集成新仓库的完整功能
"""

import asyncio
from datetime import datetime, timedelta
from app.core.intel_local.hr_state import (
    get_hr_state_for_torrent,
    update_from_hr_page,
    mark_penalized,
    mark_torrent_deleted,
    iter_site_states
)
from app.core.intel_local.models import HRStatus
from app.modules.hr_case.repository import get_hr_repository

def test_p1_integration():
    """测试P1阶段集成的完整功能"""
    print("🚀 开始HR-POLICY-2 P1阶段最终验证测试")
    print("=" * 50)
    
    # 获取正确的仓库实例
    hr_repository = get_hr_repository()
    
    test_site = "test_site_verification"
    test_torrent = "test_torrent_final"
    
    try:
        # 1. 测试get_hr_state_for_torrent的数据库加载
        print("\n1️⃣ 测试HR状态获取...")
        
        # 先通过仓库插入测试数据
        from app.core.intel_local.models import HRTorrentState
        test_state = HRTorrentState(
            site=test_site,
            torrent_id=test_torrent,
            hr_status=HRStatus.ACTIVE,
            required_seed_hours=72.0,
            seeded_hours=24.0,
            deadline=datetime.utcnow() + timedelta(days=3),
            first_seen_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow()
        )
        
        # 使用asyncio.run来运行异步仓库操作
        asyncio.run(hr_repository.upsert(test_state))
        print("   ✅ 测试数据已插入数据库")
        
        # 通过hr_state获取，应该从数据库加载
        retrieved_state = get_hr_state_for_torrent(test_site, test_torrent)
        if retrieved_state.hr_status == HRStatus.ACTIVE:
            print("   ✅ 从数据库成功加载HR状态")
        else:
            print(f"   ❌ 状态加载失败: {retrieved_state.hr_status}")
            return False
        
        # 2. 测试update_from_hr_page的双写功能
        print("\n2️⃣ 测试HR页面更新双写...")
        updated_state = update_from_hr_page(
            test_site, test_torrent, 
            required_seed_hours=96.0,
            seeded_hours=48.0,
            deadline=datetime.utcnow() + timedelta(days=4)
        )
        
        if updated_state.required_seed_hours == 96.0 and updated_state.seeded_hours == 48.0:
            print("   ✅ HR页面更新成功")
        else:
            print(f"   ❌ HR页面更新失败")
            return False
        
        # 验证数据库已更新
        db_case = asyncio.run(hr_repository.get(test_site, test_torrent))
        if db_case and db_case.requirement_hours == 96.0:
            print("   ✅ 数据库同步更新成功")
        else:
            print("   ❌ 数据库同步更新失败")
            return False
        
        # 3. 测试mark_penalized
        print("\n3️⃣ 测试违规标记...")
        penalized_state = mark_penalized(retrieved_state)
        if penalized_state.hr_status == HRStatus.FAILED:
            print("   ✅ 违规标记成功")
        else:
            print(f"   ❌ 违规标记失败: {penalized_state.hr_status}")
            return False
        
        # 4. 测试mark_torrent_deleted
        print("\n4️⃣ 测试种子删除标记...")
        deleted_state = mark_torrent_deleted(penalized_state)
        if deleted_state.life_status.value == "deleted":
            print("   ✅ 种子删除标记成功")
        else:
            print(f"   ❌ 种子删除标记失败: {deleted_state.life_status}")
            return False
        
        # 5. 测试iter_site_states
        print("\n5️⃣ 测试站点状态遍历...")
        states = list(iter_site_states(test_site))
        if len(states) > 0:
            print(f"   ✅ 遍历成功，找到{len(states)}个状态")
        else:
            print("   ❌ 遍历失败，未找到状态")
            return False
        
        # 6. 清理测试数据
        print("\n6️⃣ 清理测试数据...")
        
        # 清理数据库的异步函数
        async def cleanup_database():
            async with hr_repository._session_factory() as session:
                from sqlalchemy import delete
                from app.modules.hr_case.models import HrCase
                await session.execute(
                    delete(HrCase).where(
                        HrCase.site_key == test_site
                    )
                )
                await session.commit()
        
        asyncio.run(cleanup_database())
        
        # 清理缓存
        from app.core.intel_local.hr_cache import remove_from_cache
        remove_from_cache(test_site, test_torrent)
        
        print("   ✅ 测试数据清理完成")
        
        print("\n" + "=" * 50)
        print("🎉 P1阶段最终验证测试全部通过!")
        print("✅ hr_state.py集成新仓库成功")
        print("✅ 双写功能正常工作")
        print("✅ 数据库持久化验证通过")
        print("✅ API兼容性保持完整")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_p1_integration()
    if success:
        print("\n🎯 P1阶段完成，可以开始P2 SafetyPolicyEngine实现")
    else:
        print("\n⚠️ P1阶段存在问题，需要修复后继续")
