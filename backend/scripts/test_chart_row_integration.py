"""
测试ChartRow集成到图表服务
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.modules.charts.service import ChartsService
from app.core.database import AsyncSessionLocal
from loguru import logger


async def test_chart_row_integration():
    """测试ChartRow集成"""
    print("\n" + "="*60)
    print("ChartRow集成测试")
    print("="*60)
    
    async with AsyncSessionLocal() as session:
        service = ChartsService(session)
        
        # 测试1: 不使用ChartRow格式（向后兼容）
        print("\n[1] 测试不使用ChartRow格式（向后兼容）...")
        try:
            charts = await service.get_charts(
                platform="spotify",
                chart_type="hot",
                region="US",
                limit=5,
                use_chart_row=False
            )
            print(f"[OK] 获取到 {len(charts)} 条数据（传统格式）")
            if charts:
                print(f"示例数据: {charts[0]}")
        except Exception as e:
            print(f"[FAIL] 测试失败: {e}")
        
        # 测试2: 使用ChartRow格式
        print("\n[2] 测试使用ChartRow格式...")
        try:
            charts = await service.get_charts(
                platform="spotify",
                chart_type="hot",
                region="US",
                limit=5,
                use_chart_row=True
            )
            print(f"[OK] 获取到 {len(charts)} 条数据（ChartRow格式）")
            if charts:
                print(f"示例数据: {charts[0]}")
                # 验证ChartRow格式字段
                required_fields = ['source', 'region', 'chart_type', 'rank', 'title', 'artist_or_show']
                missing_fields = [f for f in required_fields if f not in charts[0]]
                if missing_fields:
                    print(f"[WARN] 缺少字段: {missing_fields}")
                else:
                    print("[OK] ChartRow格式字段完整")
        except Exception as e:
            print(f"[FAIL] 测试失败: {e}")
        
        # 测试3: JSONL格式输出
        print("\n[3] 测试JSONL格式输出...")
        try:
            jsonl_data = await service.get_charts_jsonl(
                platform="spotify",
                chart_type="hot",
                region="US",
                limit=5
            )
            lines = jsonl_data.split("\n") if jsonl_data else []
            print(f"[OK] 生成了 {len(lines)} 行JSONL数据")
            if lines:
                print(f"第一行示例: {lines[0][:100]}...")
        except Exception as e:
            print(f"[FAIL] 测试失败: {e}")
        
        print("\n" + "="*60)
        print("[OK] ChartRow集成测试完成")
        print("="*60)
        print("\n注意: 实际测试结果取决于API密钥配置和网络连接")


if __name__ == "__main__":
    try:
        asyncio.run(test_chart_row_integration())
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

