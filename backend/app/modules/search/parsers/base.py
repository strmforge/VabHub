"""
解析器基类
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from loguru import logger


class ParserBase(ABC):
    """解析器基类"""
    
    def __init__(self, site_name: str = ""):
        """
        初始化解析器
        
        Args:
            site_name: 站点名称
        """
        self.site_name = site_name
    
    @abstractmethod
    def parse_search_results(self, html: str) -> List[Dict[str, Any]]:
        """
        解析搜索结果页面
        
        Args:
            html: HTML内容
        
        Returns:
            解析后的结果列表，每个结果包含：
            - title: 标题
            - magnet_link: 磁力链接
            - torrent_url: 种子页面URL
            - size_gb: 大小（GB）
            - seeders: 做种数
            - leechers: 下载数
            - upload_date: 上传日期
            - info_hash: Info Hash
        """
        pass
    
    @abstractmethod
    def parse_torrent_detail(self, html: str) -> Dict[str, Any]:
        """
        解析种子详情页面
        
        Args:
            html: HTML内容
        
        Returns:
            解析后的详情字典，包含：
            - title: 标题
            - description: 描述
            - magnet_link: 磁力链接
            - torrent_url: 种子下载URL
            - size_gb: 大小（GB）
            - seeders: 做种数
            - leechers: 下载数
            - upload_date: 上传日期
            - uploader: 上传者
            - category: 分类
        """
        pass
    
    def extract_info_hash(self, magnet_link: str) -> Optional[str]:
        """
        从磁力链接提取info_hash
        
        Args:
            magnet_link: 磁力链接
        
        Returns:
            Info Hash或None
        """
        import re
        if not magnet_link:
            return None
        
        match = re.search(r'btih:([a-fA-F0-9]{40})', magnet_link)
        if match:
            return match.group(1).lower()
        
        return None
    
    def parse_size(self, size_str: str) -> float:
        """
        解析大小字符串为GB
        
        Args:
            size_str: 大小字符串（如 "10.5 GB", "1.2 TB"）
        
        Returns:
            大小（GB）
        """
        import re
        if not size_str:
            return 0.0
        
        # 提取数字和单位
        match = re.search(r'([\d.]+)\s*([KMGT]?B)', size_str.upper())
        if not match:
            return 0.0
        
        size_value = float(match.group(1))
        unit = match.group(2)
        
        # 转换为GB
        unit_map = {
            "B": 1 / (1024 ** 3),
            "KB": 1 / (1024 ** 2),
            "MB": 1 / 1024,
            "GB": 1,
            "TB": 1024
        }
        
        multiplier = unit_map.get(unit, 1)
        return size_value * multiplier
    
    def parse_date(self, date_str: str) -> Optional[str]:
        """
        解析日期字符串
        
        Args:
            date_str: 日期字符串
        
        Returns:
            ISO格式日期字符串或None
        """
        from datetime import datetime
        import re
        
        if not date_str:
            return None
        
        # 尝试解析常见日期格式
        date_formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y年%m月%d日"
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        # 如果都失败，返回原始字符串
        return date_str

