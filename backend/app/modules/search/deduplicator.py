"""
搜索结果去重器
基于info_hash、磁力链接和标题相似度进行去重
"""

import re
from typing import List, Dict, Any, Set
from loguru import logger


class ResultDeduplicator:
    """搜索结果去重器"""
    
    def __init__(self, similarity_threshold: float = 0.8):
        """
        初始化去重器
        
        Args:
            similarity_threshold: 标题相似度阈值（0-1）
        """
        self.similarity_threshold = similarity_threshold
    
    def deduplicate(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去重搜索结果
        
        Args:
            results: 搜索结果列表
        
        Returns:
            去重后的结果列表
        """
        seen_hashes: Set[str] = set()
        seen_magnets: Set[str] = set()
        deduplicated: List[Dict[str, Any]] = []
        
        for result in results:
            # 基于info_hash去重（最准确）
            info_hash = result.get('info_hash')
            if info_hash:
                info_hash_lower = info_hash.lower()
                if info_hash_lower in seen_hashes:
                    continue
                seen_hashes.add(info_hash_lower)
                deduplicated.append(result)
                continue
            
            # 基于magnet链接去重
            magnet_link = result.get('magnet_link')
            if magnet_link:
                # 提取info_hash
                extracted_hash = self._extract_info_hash(magnet_link)
                if extracted_hash:
                    if extracted_hash in seen_hashes:
                        continue
                    seen_hashes.add(extracted_hash)
                    result['info_hash'] = extracted_hash
                    deduplicated.append(result)
                    continue
                
                # 如果没有info_hash，使用完整magnet链接
                if magnet_link in seen_magnets:
                    continue
                seen_magnets.add(magnet_link)
                deduplicated.append(result)
                continue
            
            # 基于标题相似度去重
            is_duplicate = False
            title = result.get('title', '')
            
            for existing in deduplicated:
                existing_title = existing.get('title', '')
                similarity = self._calculate_similarity(title, existing_title)
                
                if similarity > self.similarity_threshold:
                    # 保留质量更好的结果（做种数更多）
                    if result.get('seeders', 0) > existing.get('seeders', 0):
                        deduplicated.remove(existing)
                        break
                    else:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                deduplicated.append(result)
        
        logger.debug(f"去重完成: {len(results)} -> {len(deduplicated)}")
        return deduplicated
    
    def _extract_info_hash(self, magnet_link: str) -> str:
        """从磁力链接提取info_hash"""
        if not magnet_link:
            return None
        
        match = re.search(r'btih:([a-fA-F0-9]{40})', magnet_link)
        if match:
            return match.group(1).lower()
        
        return None
    
    def _calculate_similarity(self, title1: str, title2: str) -> float:
        """
        计算标题相似度
        
        使用Jaccard相似度（基于词汇集合的交集和并集）
        
        Args:
            title1: 标题1
            title2: 标题2
        
        Returns:
            相似度（0-1）
        """
        if not title1 or not title2:
            return 0.0
        
        # 清理标题：移除标点符号，转为小写
        title1_clean = re.sub(r'[^\w\s]', '', title1.lower())
        title2_clean = re.sub(r'[^\w\s]', '', title2.lower())
        
        # 分词
        words1 = set(title1_clean.split())
        words2 = set(title2_clean.split())
        
        if not words1 or not words2:
            return 0.0
        
        # 计算Jaccard相似度
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        similarity = len(intersection) / len(union)
        
        # 如果标题长度差异很大，降低相似度
        length_ratio = min(len(title1), len(title2)) / max(len(title1), len(title2))
        similarity *= length_ratio
        
        return similarity

