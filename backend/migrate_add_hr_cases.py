#!/usr/bin/env python3
"""
HR案件系统数据库迁移脚本
添加 hr_cases 表用于 HR-POLICY-2 项目

运行方式:
python migrate_add_hr_cases.py

作者: Cascade
创建时间: 2025-11-29
项目: HR-POLICY-2 P1阶段
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.core.database import engine, AsyncSessionLocal
from app.modules.hr_case.models import HrCase


async def check_table_exists(session, table_name: str) -> bool:
    """检查表是否存在"""
    result = await session.execute(text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"
    ), {"table_name": table_name})
    return result.fetchone() is not None


async def create_hr_cases_table():
    """创建 hr_cases 表"""
    
    print("🚀 开始HR案件系统数据库迁移...")
    
    try:
        # 检查表是否已存在并获取数据量
        async with AsyncSessionLocal() as session:
            exists = await check_table_exists(session, "hr_cases")
            if exists:
                # 检查数据量
                result = await session.execute(text("SELECT COUNT(*) FROM hr_cases"))
                count = result.scalar()
                print(f"⚠️  发现现有hr_cases表，包含 {count} 条数据")
                
                if count > 0:
                    print("⚠️  表中有数据，为安全起见，迁移将被中止")
                    print("   如需强制重建，请手动清空表或备份数据")
                    return
                else:
                    print("🗑️  表为空，将删除旧表并重建")
                    await session.execute(text("DROP TABLE hr_cases"))
                    await session.commit()
                    print("✅ 旧表已删除")
        
        # 创建表（使用SQLAlchemy的create_all方法，跨数据库兼容）
        print("📝 创建 hr_cases 表...")
        async with engine.begin() as conn:
            await conn.run_sync(HrCase.metadata.create_all)
        
        # 验证表创建成功
        async with AsyncSessionLocal() as session:
            exists = await check_table_exists(session, "hr_cases")
            if not exists:
                raise Exception("表创建失败")
        
        print("✅ hr_cases 表创建成功")
        
        # 创建索引（如果需要额外的索引）
        print("📝 创建额外索引...")
        async with AsyncSessionLocal() as session:
            # 创建复合索引优化查询性能
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_hr_cases_site_torrent ON hr_cases(site_key, torrent_id)",
                "CREATE INDEX IF NOT EXISTS idx_hr_cases_status_deadline ON hr_cases(status, deadline)",
                "CREATE INDEX IF NOT EXISTS idx_hr_cases_site_status ON hr_cases(site_key, status)",
                "CREATE INDEX IF NOT EXISTS idx_hr_cases_active_hr ON hr_cases(site_key, status, life_status)",
                "CREATE INDEX IF NOT EXISTS idx_hr_cases_updated_at ON hr_cases(updated_at)",
                "CREATE INDEX IF NOT EXISTS idx_hr_cases_deadline ON hr_cases(deadline)",
            ]
            
            for index_sql in indexes:
                try:
                    await session.execute(text(index_sql))
                    print(f"  ✅ 创建索引: {index_sql.split('idx_')[1].split(' ')[0]}")
                except Exception as e:
                    print(f"  ⚠️  索引创建失败（可能已存在）: {e}")
            
            await session.commit()
        
        print("✅ 索引创建完成")
        
        # 显示表结构
        print("\n📋 hr_cases 表结构:")
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("PRAGMA table_info(hr_cases)"))
            columns = result.fetchall()
            
            print("  列名                    | 类型           | 允许空 | 默认值")
            print("  -----------------------|---------------|--------|----------")
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = "NO" if col[3] else "YES"
                default_val = col[4] if col[4] else ""
                print(f"  {col_name:<23} | {col_type:<13} | {not_null:<6} | {default_val}")
        
        print("\n🎉 HR案件系统数据库迁移完成！")
        print(f"   迁移时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("   下一步: 可以开始使用 HrCasesRepository")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        raise


async def verify_migration():
    """验证迁移结果"""
    print("\n🔍 验证迁移结果...")
    
    async with AsyncSessionLocal() as session:
        # 检查表
        exists = await check_table_exists(session, "hr_cases")
        if not exists:
            raise Exception("hr_cases 表不存在")
        
        # 检查索引
        result = await session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_hr_cases_%'"
        ))
        indexes = result.fetchall()
        
        print("  ✅ hr_cases 表存在")
        print(f"  ✅ 创建了 {len(indexes)} 个索引")
        
        # 测试插入一条记录
        try:
            test_case = HrCase(
                site_id=1,
                site_key="test_site",
                torrent_id="test_torrent_123",
                status="none",
                life_status="alive",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(test_case)
            await session.commit()
            
            # 查询测试
            result = await session.execute(text(
                "SELECT COUNT(*) FROM hr_cases WHERE site_key = 'test_site'"
            ))
            count = result.scalar()
            
            if count == 1:
                print("  ✅ 数据插入和查询测试通过")
                
                # 清理测试数据
                await session.execute(text(
                    "DELETE FROM hr_cases WHERE site_key = 'test_site'"
                ))
                await session.commit()
                print("  ✅ 测试数据清理完成")
            else:
                raise Exception("数据插入测试失败")
                
        except Exception as e:
            print(f"  ❌ 数据操作测试失败: {e}")
            raise
    
    print("✅ 迁移验证完成")


async def show_next_steps():
    """显示后续步骤"""
    print("\n📋 后续实施步骤:")
    print("  P1 ✅ 创建HrCase模型和数据库表")
    print("  P1 ✅ 实现SqlAlchemyHrCasesRepository")
    print("  P1 🔄 修改hr_state.py通过新仓库操作")
    print("  P1 ⏳ 验证现有HR功能不退化")
    print("")
    print("  P2 ⏳ 实现SafetyPolicyEngine核心逻辑")
    print("  P3 ⏳ 后端接入关键操作")
    print("  P4 ⏳ 前端安全模式中心")
    print("  P5 ⏳ 通知中心&Telegram联动")
    print("  P6 ⏳ 测试回归与文档")
    print("")
    print("🔧 使用示例:")
    print("  from app.modules.hr_case.repository import get_hr_repository")
    print("  repo = get_hr_repository()")
    print("  hr_case = await repo.get('hdhome', 'torrent_123')")


async def main():
    """主函数"""
    try:
        await create_hr_cases_table()
        await verify_migration()
        await show_next_steps()
    except KeyboardInterrupt:
        print("\n⚠️  迁移被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 运行迁移
    asyncio.run(main())
