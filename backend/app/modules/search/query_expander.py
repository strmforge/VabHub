"""
查询扩展器
用于老电视剧搜索优化，支持去除年份、添加后缀、繁简转换、拼音转换
"""

import re
from typing import List, Optional
from loguru import logger

try:
    import zhconv
    ZHCONV_AVAILABLE = True
except ImportError:
    ZHCONV_AVAILABLE = False
    logger.warning("zhconv not available, traditional Chinese conversion will be limited")

try:
    from pypinyin import lazy_pinyin, Style
    PYPINYIN_AVAILABLE = True
except ImportError:
    PYPINYIN_AVAILABLE = False
    logger.warning("pypinyin not available, pinyin conversion will be limited")


class QueryExpander:
    """查询扩展器"""
    
    # 老电视剧关键词库
    OLD_TV_KEYWORDS = [
        '天下第一', '武林外传', '还珠格格', '神雕侠侣', '射雕英雄传',
        '天龙八部', '笑傲江湖', '倚天屠龙记', '鹿鼎记', '碧血剑',
        '连城诀', '侠客行', '飞狐外传', '雪山飞狐', '书剑恩仇录',
        '白发魔女传', '绝代双骄', '楚留香', '陆小凤', '小李飞刀',
        '大宅门', '康熙王朝', '雍正王朝', '汉武大帝', '大明王朝',
        '走向共和', '亮剑', '士兵突击', '我的团长我的团', '潜伏',
        '暗算', '黎明之前', '悬崖', '风筝', '伪装者'
    ]
    
    # 常见后缀
    TV_SUFFIXES = ['电视剧', '剧集', 'TV版', 'TV剧', '连续剧']
    
    # 年份范围（老电视剧）
    OLD_TV_YEAR_RANGE = (1990, 2010)
    
    @classmethod
    def expand_query(
        cls,
        query: str,
        year: Optional[int] = None,
        media_type: Optional[str] = None
    ) -> List[str]:
        """
        扩展查询
        
        Args:
            query: 原始查询
            year: 年份（可选）
            media_type: 媒体类型（可选）
        
        Returns:
            扩展后的查询列表
        """
        expanded_queries = [query]
        
        # 检测是否为老电视剧
        is_old_tv = cls._is_old_tv(query, year, media_type)
        
        if is_old_tv:
            # 老电视剧特殊处理
            expanded_queries.extend(cls._expand_old_tv_query(query, year))
        else:
            # 通用扩展
            expanded_queries.extend(cls._general_expansion(query))
        
        # 去重
        return list(dict.fromkeys(expanded_queries))
    
    @classmethod
    def _is_old_tv(
        cls,
        query: str,
        year: Optional[int] = None,
        media_type: Optional[str] = None
    ) -> bool:
        """检测是否为老电视剧"""
        # 检查媒体类型
        if media_type and media_type not in ['tv', 'tv_show']:
            return False
        
        # 检查年份
        if year:
            if cls.OLD_TV_YEAR_RANGE[0] <= year <= cls.OLD_TV_YEAR_RANGE[1]:
                return True
        
        # 检查关键词
        for keyword in cls.OLD_TV_KEYWORDS:
            if keyword in query:
                return True
        
        # 检查是否包含年份（在查询中）
        year_match = re.search(r'\d{4}', query)
        if year_match:
            year_in_query = int(year_match.group())
            if cls.OLD_TV_YEAR_RANGE[0] <= year_in_query <= cls.OLD_TV_YEAR_RANGE[1]:
                return True
        
        return False
    
    @classmethod
    def _expand_old_tv_query(
        cls,
        query: str,
        year: Optional[int] = None
    ) -> List[str]:
        """扩展老电视剧查询"""
        expansions = []
        
        # 1. 去除年份的版本
        if year:
            clean_query = re.sub(r'\s*\d{4}\s*', ' ', query).strip()
            if clean_query and clean_query != query:
                expansions.append(clean_query)
        
        # 去除查询中的年份
        clean_query = re.sub(r'\s*\d{4}\s*', ' ', query).strip()
        if clean_query and clean_query != query:
            expansions.append(clean_query)
        
        # 2. 添加常见后缀
        base_query = clean_query if clean_query else query
        for suffix in cls.TV_SUFFIXES:
            if suffix not in base_query:
                expansions.append(f"{base_query} {suffix}")
                expansions.append(f"{base_query}{suffix}")
        
        # 3. 繁体字版本
        traditional_queries = cls._to_traditional(base_query)
        expansions.extend(traditional_queries)
        
        # 4. 拼音版本
        pinyin_queries = cls._to_pinyin(base_query)
        expansions.extend(pinyin_queries)
        
        return expansions
    
    @classmethod
    def _general_expansion(cls, query: str) -> List[str]:
        """通用扩展"""
        expansions = []
        
        # 1. 去除标点符号的版本
        clean_query = re.sub(r'[，。！？；：""''《》【】]', ' ', query).strip()
        if clean_query != query:
            expansions.append(clean_query)
        
        # 2. 空格处理的不同版本
        space_variants = [
            query.replace(' ', ''),      # 无空格
            query.replace(' ', '-'),     # 连字符
            query.replace(' ', '_'),     # 下划线
        ]
        expansions.extend(space_variants)
        
        # 3. 大小写变体（如果是英文）
        if query.isascii():
            expansions.append(query.lower())
            expansions.append(query.upper())
            expansions.append(query.title())
        
        return expansions
    
    @classmethod
    def _to_traditional(cls, query: str) -> List[str]:
        """转换为繁体中文"""
        if not ZHCONV_AVAILABLE:
            # 简化实现：只处理常见转换
            traditional_map = {
                '传': '傳', '还': '還', '侠': '俠', '侣': '侶',
                '龙': '龍', '凤': '鳳', '门': '門', '国': '國',
                '学': '學', '书': '書', '剑': '劍', '飞': '飛'
            }
            traditional_query = ''.join(traditional_map.get(char, char) for char in query)
            if traditional_query != query:
                return [traditional_query]
            return []
        
        try:
            # 使用zhconv库转换
            traditional_query = zhconv.convert(query, 'zh-tw')
            if traditional_query != query:
                return [traditional_query]
            return []
        except Exception as e:
            logger.warning(f"繁简转换失败: {e}")
            return []
    
    @classmethod
    def _to_pinyin(cls, query: str) -> List[str]:
        """转换为拼音"""
        if not PYPINYIN_AVAILABLE:
            # 简化实现：只处理常见转换
            pinyin_map = {
                '天下第一': 'tian xia di yi',
                '武林外传': 'wu lin wai zhuan',
                '还珠格格': 'huan zhu ge ge',
                '神雕侠侣': 'shen diao xia lv'
            }
            if query in pinyin_map:
                return [pinyin_map[query]]
            return []
        
        try:
            # 使用pypinyin库转换
            # 带声调
            pinyin_with_tone = ' '.join(lazy_pinyin(query, style=Style.TONE))
            # 不带声调
            pinyin_without_tone = ' '.join(lazy_pinyin(query, style=Style.NORMAL))
            # 首字母
            pinyin_initials = ' '.join(lazy_pinyin(query, style=Style.FIRST_LETTER))
            
            results = []
            if pinyin_with_tone != query:
                results.append(pinyin_with_tone)
            if pinyin_without_tone != query and pinyin_without_tone != pinyin_with_tone:
                results.append(pinyin_without_tone)
            if pinyin_initials != query and pinyin_initials not in results:
                results.append(pinyin_initials)
            
            return results
        except Exception as e:
            logger.warning(f"拼音转换失败: {e}")
            return []
    
    @classmethod
    def remove_year(cls, query: str) -> str:
        """去除查询中的年份"""
        return re.sub(r'\s*\d{4}\s*', ' ', query).strip()
    
    @classmethod
    def extract_year(cls, query: str) -> Optional[int]:
        """从查询中提取年份"""
        year_match = re.search(r'\d{4}', query)
        if year_match:
            try:
                return int(year_match.group())
            except ValueError:
                pass
        return None

