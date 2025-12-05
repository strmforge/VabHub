"""
集成ChartRow到图表服务
将新创建的ChartRow模型集成到现有的ChartsService中
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.modules.charts.providers.chart_row import ChartRow
from loguru import logger


def test_chart_row():
    """测试ChartRow模型"""
    print("\n" + "="*60)
    print("ChartRow模型测试")
    print("="*60)
    
    # 1. 测试ChartRow创建
    print("\n[1] 测试ChartRow创建...")
    chart_row = ChartRow(
        source="spotify",
        region="US",
        chart_type="hot",
        date_or_week="2025-01-13",
        rank=1,
        title="Test Song",
        artist_or_show="Test Artist",
        id_or_url="https://open.spotify.com/track/test",
        metrics={"streams": 1000000},
        search_query="Test Artist - Test Song"
    )
    print(f"ChartRow创建成功: {chart_row.title}")
    
    # 2. 测试to_dict方法
    print("\n[2] 测试to_dict方法...")
    chart_dict = chart_row.to_dict()
    print(f"字典格式: {chart_dict}")
    print("[OK] to_dict方法正常")
    
    # 3. 测试to_jsonl方法
    print("\n[3] 测试to_jsonl方法...")
    jsonl_str = chart_row.to_jsonl()
    print(f"JSONL格式: {jsonl_str}")
    print("[OK] to_jsonl方法正常")
    
    # 4. 测试多个ChartRow
    print("\n[4] 测试多个ChartRow...")
    chart_rows = [
        ChartRow(
            source="spotify",
            region="US",
            chart_type="hot",
            date_or_week="2025-01-13",
            rank=i+1,
            title=f"Song {i+1}",
            artist_or_show=f"Artist {i+1}",
            id_or_url=f"https://open.spotify.com/track/{i+1}",
            metrics={"streams": 1000000 - i*10000},
            search_query=f"Artist {i+1} - Song {i+1}"
        )
        for i in range(5)
    ]
    
    # 转换为JSONL格式（参考charts-suite-v2）
    jsonl_lines = [row.to_jsonl() for row in chart_rows]
    print(f"生成了 {len(jsonl_lines)} 行JSONL数据")
    print("[OK] 多个ChartRow处理正常")
    
    print("\n" + "="*60)
    print("[OK] ChartRow模型测试通过！")
    print("="*60)
    print("\n下一步: 将ChartRow集成到ChartsService中")
    return True


if __name__ == "__main__":
    try:
        result = test_chart_row()
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

