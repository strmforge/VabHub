"""
文本处理工具 - 整合自acq-guardian项目
用于HNR检测的文本标准化和匹配
"""

import re
import unicodedata
from typing import Set, Optional


# 空白字符正则
_WS = re.compile(r"\s+")


def normalize(text: str) -> str:
    """
    标准化文本以便于匹配：
    - NFKC规范化（全角/兼容字符折叠）
    - 转换为小写
    - 压缩空白字符
    
    Args:
        text: 原始文本
    
    Returns:
        标准化后的文本
    """
    if text is None:
        return ""
    
    # NFKC规范化
    t = unicodedata.normalize("NFKC", text)
    # 转换为小写
    t = t.lower()
    # 压缩空白字符
    t = _WS.sub(" ", t).strip()
    
    return t


def cooccur(text: str, left: Set[str], right: Set[str]) -> bool:
    """
    检查文本中是否同时出现左侧和右侧的关键词
    
    用于启发式检测，例如：
    - 左侧：{"考核", "命中", "保种"}
    - 右侧：{"小时", "天", "做种", "时长"}
    
    Args:
        text: 要检查的文本
        left: 左侧关键词集合
        right: 右侧关键词集合
    
    Returns:
        是否同时出现
    """
    t = normalize(text)
    return any(l in t for l in left) and any(r in t for r in right)


def extract_level(text: str) -> Optional[int]:
    """
    从文本中提取HNR级别（H3, H5, H7等）
    
    Args:
        text: 要检查的文本
    
    Returns:
        HNR级别，如果未找到则返回None
    """
    # 避免H.264/H.265/HDR10误报的正则表达式
    RE_HNR_LEVEL = re.compile(r"""(?ix)
        (?<!H\.?26[45])  # avoid H.264/H.265
        (?<!HDR)         # avoid HDR / HDR10
        \bH\s*[-/:：]?\s*(?P<level>[1-9]|10)\b
    """)
    
    match = RE_HNR_LEVEL.search(text)
    if match:
        try:
            return int(match.group("level"))
        except (ValueError, IndexError):
            return None
    return None

