"""
搜索结果聚合器（增强版）
优化多源搜索结果聚合、去重、排序和评分
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
import re


class ResultAggregator:
    """搜索结果聚合器（增强版）"""
    
    def __init__(self, similarity_threshold: float = 0.8):
        """
        初始化聚合器
        
        Args:
            similarity_threshold: 标题相似度阈值（0-1）
        """
        self.similarity_threshold = similarity_threshold
    
    def aggregate(
        self,
        results: List[Dict[str, Any]],
        sort_by: str = "score",
        sort_order: str = "desc",
        group_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        聚合搜索结果
        
        Args:
            results: 搜索结果列表
            sort_by: 排序字段（score, seeders, size, date）
            sort_order: 排序方向（asc, desc）
            group_by: 分组字段（site, quality, resolution, category）
        
        Returns:
            聚合后的结果列表
        """
        # 1. 去重
        deduplicated = self._deduplicate(results)
        
        # 2. 评分
        scored = self._score_results(deduplicated)
        
        # 3. 排序
        sorted_results = self._sort_results(scored, sort_by, sort_order)
        
        # 4. 分组（如果需要）
        if group_by:
            return self._group_results(sorted_results, group_by)
        
        return sorted_results
    
    def _deduplicate(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去重搜索结果（增强版）
        
        策略：
        1. 基于info_hash去重（最准确）
        2. 基于magnet链接去重
        3. 基于标题相似度去重（保留质量最好的）
        """
        seen_hashes: set = set()
        seen_magnets: set = set()
        deduplicated: List[Dict[str, Any]] = []
        
        for result in results:
            # 基于info_hash去重（最准确）
            info_hash = result.get('info_hash')
            if info_hash:
                info_hash_lower = info_hash.lower()
                if info_hash_lower in seen_hashes:
                    # 如果已存在，比较质量，保留更好的
                    existing = next(
                        (r for r in deduplicated if r.get('info_hash', '').lower() == info_hash_lower),
                        None
                    )
                    if existing and self._is_better_result(result, existing):
                        deduplicated.remove(existing)
                        deduplicated.append(result)
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
                        # 如果已存在，比较质量，保留更好的
                        existing = next(
                            (r for r in deduplicated if r.get('info_hash', '').lower() == extracted_hash),
                            None
                        )
                        if existing and self._is_better_result(result, existing):
                            deduplicated.remove(existing)
                            result['info_hash'] = extracted_hash
                            deduplicated.append(result)
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
                    # 保留质量更好的结果
                    if self._is_better_result(result, existing):
                        deduplicated.remove(existing)
                        break
                    else:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                deduplicated.append(result)
        
        logger.debug(f"去重完成: {len(results)} -> {len(deduplicated)}")
        return deduplicated
    
    def _score_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        为搜索结果评分
        
        评分因素：
        1. 做种数（权重：0.4）
        2. 文件大小合理性（权重：0.2）
        3. 上传时间（权重：0.2）
        4. 站点质量（权重：0.1）
        5. 标题匹配度（权重：0.1）
        
        总分：0-100
        """
        scored_results = []
        
        for result in results:
            score = 0.0
            
            # 1. 做种数评分（0-40分）
            seeders = result.get('seeders', 0)
            if seeders > 100:
                score += 40
            elif seeders > 50:
                score += 30
            elif seeders > 20:
                score += 20
            elif seeders > 10:
                score += 10
            elif seeders > 5:
                score += 5
            
            # 2. 文件大小合理性评分（0-20分）
            size_gb = result.get('size_gb', 0)
            if 0.5 <= size_gb <= 50:  # 合理范围
                score += 20
            elif 0.1 <= size_gb <= 100:
                score += 15
            elif size_gb > 0:
                score += 10
            
            # 3. 上传时间评分（0-20分）
            upload_date = result.get('upload_date')
            if upload_date:
                if isinstance(upload_date, str):
                    # 尝试解析日期字符串
                    try:
                        upload_date = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                    except:
                        upload_date = None
                
                if upload_date:
                    days_ago = (datetime.utcnow() - upload_date.replace(tzinfo=None)).days
                    if days_ago <= 7:
                        score += 20
                    elif days_ago <= 30:
                        score += 15
                    elif days_ago <= 90:
                        score += 10
                    elif days_ago <= 180:
                        score += 5
            
            # 4. 站点质量评分（0-10分）
            site = result.get('site', '').lower()
            # 私有PT站点通常质量更高
            if any(pt in site for pt in ['pt', 'private', 'tracker']):
                score += 10
            elif any(public in site for public in ['1337x', 'nyaa', 'yts']):
                score += 5
            
            # 5. 标题匹配度评分（0-10分）
            # 这里简化处理，实际可以根据搜索关键词匹配度计算
            score += 10
            
            result['score'] = round(score, 2)
            scored_results.append(result)
        
        return scored_results
    
    def _sort_results(
        self,
        results: List[Dict[str, Any]],
        sort_by: str = "score",
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        排序搜索结果
        
        Args:
            results: 结果列表
            sort_by: 排序字段（score, seeders, size, date）
            sort_order: 排序方向（asc, desc）
        
        Returns:
            排序后的结果列表
        """
        reverse = sort_order == "desc"
        
        if sort_by == "score":
            results.sort(key=lambda x: x.get('score', 0), reverse=reverse)
        elif sort_by == "seeders":
            results.sort(key=lambda x: x.get('seeders', 0), reverse=reverse)
        elif sort_by == "size":
            results.sort(key=lambda x: x.get('size_gb', 0), reverse=reverse)
        elif sort_by == "date":
            results.sort(
                key=lambda x: x.get('upload_date') or datetime.min,
                reverse=reverse
            )
        else:
            # 默认按评分排序
            results.sort(key=lambda x: x.get('score', 0), reverse=reverse)
        
        return results
    
    def _group_results(
        self,
        results: List[Dict[str, Any]],
        group_by: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        分组搜索结果
        
        Args:
            results: 结果列表
            group_by: 分组字段（site, quality, resolution, category）
        
        Returns:
            分组后的结果字典
        """
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        
        for result in results:
            if group_by == "site":
                key = result.get('site', 'Unknown')
            elif group_by == "quality":
                key = result.get('quality', 'Unknown')
            elif group_by == "resolution":
                key = result.get('resolution', 'Unknown')
            elif group_by == "category":
                key = result.get('category', 'Unknown')
            else:
                key = 'Other'
            
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(result)
        
        return grouped
    
    def _is_better_result(self, result1: Dict[str, Any], result2: Dict[str, Any]) -> bool:
        """
        判断result1是否比result2更好
        
        比较因素：
        1. 做种数
        2. 文件大小合理性
        3. 上传时间
        """
        # 比较做种数
        seeders1 = result1.get('seeders', 0)
        seeders2 = result2.get('seeders', 0)
        if seeders1 > seeders2:
            return True
        elif seeders1 < seeders2:
            return False
        
        # 比较文件大小合理性
        size1 = result1.get('size_gb', 0)
        size2 = result2.get('size_gb', 0)
        if 0.5 <= size1 <= 50 and not (0.5 <= size2 <= 50):
            return True
        elif not (0.5 <= size1 <= 50) and 0.5 <= size2 <= 50:
            return False
        
        # 比较上传时间（越新越好）
        date1 = result1.get('upload_date')
        date2 = result2.get('upload_date')
        if date1 and date2:
            if isinstance(date1, str):
                try:
                    date1 = datetime.fromisoformat(date1.replace('Z', '+00:00'))
                except:
                    date1 = None
            if isinstance(date2, str):
                try:
                    date2 = datetime.fromisoformat(date2.replace('Z', '+00:00'))
                except:
                    date2 = None
            
            if date1 and date2:
                if date1 > date2:
                    return True
                elif date1 < date2:
                    return False
        
        # 默认保留第一个
        return False
    
    def _extract_info_hash(self, magnet_link: str) -> Optional[str]:
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

