"""
图表数据行模型
参考charts-suite-v2的ChartRow实现
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class ChartRow:
    """图表数据行"""
    source: str  # 数据源（apple_music, spotify等）
    region: Optional[str] = None  # 地区（US, CN等）
    chart_type: str = ""  # 榜单类型（hot, new等）
    date_or_week: Optional[str] = None  # 日期或周
    rank: Optional[int] = None  # 排名
    title: Optional[str] = None  # 标题（歌曲名/电影名）
    artist_or_show: Optional[str] = None  # 艺术家或节目名
    id_or_url: Optional[str] = None  # ID或URL
    metrics: Optional[Dict[str, Any]] = None  # 指标（播放量、下载量等）
    search_query: Optional[str] = None  # 搜索查询字符串
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_jsonl(self) -> str:
        """转换为JSONL格式（参考charts-suite-v2）"""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False)

