"""
订阅规则引擎
实现高级规则匹配和过滤
"""

import re
from typing import Any, Dict, List, Optional

from loguru import logger

from app.constants.media_types import is_tv_like


class RuleEngine:
    """订阅规则引擎"""
    
    def __init__(self):
        self.compiled_patterns = {}  # 缓存编译后的正则表达式
    
    def match_result(self, result: Dict[str, Any], subscription: Dict[str, Any]) -> bool:
        """
        检查搜索结果是否匹配订阅规则
        
        Args:
            result: 搜索结果字典
            subscription: 订阅配置字典
        
        Returns:
            bool: 是否匹配
        """
        title = result.get("title", "").lower()
        
        # 1. 基础规则检查
        if not self._check_basic_rules(result, subscription):
            return False
        
        # 2. 包含规则检查（支持正则表达式）
        if not self._check_include_rules(title, subscription.get("include")):
            return False
        
        # 3. 排除规则检查（支持正则表达式）
        if not self._check_exclude_rules(title, subscription.get("exclude")):
            return False
        
        # 4. 优先级规则组检查
        if not self._check_filter_groups(result, subscription.get("filter_groups")):
            return False
        
        # 5. 媒体类型特殊规则检查
        if is_tv_like(subscription.get("media_type")):
            if not self._check_tv_rules(result, subscription):
                return False
        
        return True
    
    def _check_basic_rules(self, result: Dict[str, Any], subscription: Dict[str, Any]) -> bool:
        """检查基础规则（质量、分辨率、特效、做种数等）"""
        title = result.get("title", "").lower()
        
        # 质量检查
        if subscription.get("quality"):
            quality = subscription.get("quality").lower()
            result_quality = result.get("quality", "").lower()
            if quality not in title and quality not in result_quality:
                return False
        
        # 分辨率检查
        if subscription.get("resolution"):
            resolution = subscription.get("resolution").lower()
            result_resolution = result.get("resolution", "").lower()
            if resolution not in title and resolution not in result_resolution:
                return False
        
        # 特效检查（HDR、Dolby Vision等）
        if subscription.get("effect"):
            effect = subscription.get("effect").lower()
            if effect not in title:
                return False
        
        # 做种数检查
        min_seeders = subscription.get("min_seeders", 0)
        if result.get("seeders", 0) < min_seeders:
            return False
        
        # 文件大小检查（可选）
        if subscription.get("min_size"):
            min_size = subscription.get("min_size")
            if result.get("size_gb", 0) < min_size:
                return False
        
        if subscription.get("max_size"):
            max_size = subscription.get("max_size")
            if result.get("size_gb", 0) > max_size:
                return False
        
        return True
    
    def _check_include_rules(self, title: str, include_rules: Optional[str]) -> bool:
        """
        检查包含规则（支持正则表达式）
        
        规则格式：
        - 简单字符串：多个关键词用逗号分隔，OR逻辑
        - 正则表达式：以 / 开头和结尾，如 /pattern/
        - 混合模式：可以同时使用字符串和正则
        """
        if not include_rules:
            return True
        
        # 检查是否包含正则表达式（以 / 开头和结尾）
        if include_rules.strip().startswith("/") and include_rules.strip().endswith("/"):
            # 正则表达式模式
            pattern = include_rules.strip()[1:-1]  # 去掉首尾的 /
            try:
                if pattern not in self.compiled_patterns:
                    self.compiled_patterns[pattern] = re.compile(pattern, re.IGNORECASE)
                return bool(self.compiled_patterns[pattern].search(title))
            except re.error as e:
                logger.warning(f"包含规则正则表达式错误: {pattern}, {e}")
                return False
        else:
            # 简单字符串匹配（OR逻辑）
            keywords = [k.strip().lower() for k in include_rules.split(",")]
            return any(keyword in title for keyword in keywords)
    
    def _check_exclude_rules(self, title: str, exclude_rules: Optional[str]) -> bool:
        """
        检查排除规则（支持正则表达式）
        
        规则格式同包含规则
        """
        if not exclude_rules:
            return True
        
        # 检查是否包含正则表达式
        if exclude_rules.strip().startswith("/") and exclude_rules.strip().endswith("/"):
            # 正则表达式模式
            pattern = exclude_rules.strip()[1:-1]
            try:
                if pattern not in self.compiled_patterns:
                    self.compiled_patterns[pattern] = re.compile(pattern, re.IGNORECASE)
                # 排除规则：如果匹配则返回False
                return not bool(self.compiled_patterns[pattern].search(title))
            except re.error as e:
                logger.warning(f"排除规则正则表达式错误: {pattern}, {e}")
                return True  # 正则错误时，不排除
        else:
            # 简单字符串匹配（OR逻辑）
            keywords = [k.strip().lower() for k in exclude_rules.split(",")]
            # 排除规则：如果匹配任何关键词则返回False
            return not any(keyword in title for keyword in keywords)
    
    def _check_filter_groups(self, result: Dict[str, Any], filter_groups: Optional[List[Dict]]) -> bool:
        """
        检查优先级规则组
        
        规则组格式：
        [
            {
                "name": "发布组优先级",
                "priority": 1,
                "rules": [
                    {"type": "include", "pattern": "CHD", "logic": "or"},
                    {"type": "include", "pattern": "WiKi", "logic": "or"}
                ]
            },
            {
                "name": "编码格式",
                "priority": 2,
                "rules": [
                    {"type": "include", "pattern": "H.265", "logic": "and"}
                ]
            }
        ]
        """
        if not filter_groups:
            return True
        
        title = result.get("title", "").lower()
        
        # 按优先级排序
        sorted_groups = sorted(filter_groups, key=lambda x: x.get("priority", 999))
        
        for group in sorted_groups:
            rules = group.get("rules", [])
            if not rules:
                continue
            
            # 检查规则组内的规则
            group_match = self._check_rule_group(title, rules)
            if not group_match:
                return False
        
        return True
    
    def _check_rule_group(self, title: str, rules: List[Dict]) -> bool:
        """
        检查规则组内的规则
        
        支持 AND/OR 逻辑
        """
        if not rules:
            return True
        
        # 按逻辑分组
        or_rules = [r for r in rules if r.get("logic", "and").lower() == "or"]
        and_rules = [r for r in rules if r.get("logic", "and").lower() == "and"]
        
        # OR规则：至少匹配一个
        if or_rules:
            or_match = any(self._check_single_rule(title, rule) for rule in or_rules)
            if not or_match:
                return False
        
        # AND规则：必须全部匹配
        if and_rules:
            and_match = all(self._check_single_rule(title, rule) for rule in and_rules)
            if not and_match:
                return False
        
        return True
    
    def _check_single_rule(self, title: str, rule: Dict) -> bool:
        """检查单个规则"""
        rule_type = rule.get("type", "include")
        pattern = rule.get("pattern", "")
        
        if not pattern:
            return True
        
        # 检查是否为正则表达式
        if pattern.strip().startswith("/") and pattern.strip().endswith("/"):
            pattern_str = pattern.strip()[1:-1]
            try:
                if pattern_str not in self.compiled_patterns:
                    self.compiled_patterns[pattern_str] = re.compile(pattern_str, re.IGNORECASE)
                match = bool(self.compiled_patterns[pattern_str].search(title))
            except re.error:
                match = False
        else:
            # 简单字符串匹配
            match = pattern.lower() in title
        
        return match if rule_type == "include" else not match
    
    def _check_tv_rules(self, result: Dict[str, Any], subscription: Dict[str, Any]) -> bool:
        """检查电视剧特殊规则"""
        title = result.get("title", "").lower()
        season = subscription.get("season")
        
        if season:
            # 检查季数
            season_patterns = [
                f"s{season:02d}",
                f"season {season}",
                f"season{season}",
                f"s{season}"
            ]
            if not any(pattern in title for pattern in season_patterns):
                return False
        
        # 检查集数范围（如果指定）
        start_episode = subscription.get("start_episode")
        total_episode = subscription.get("total_episode")
        
        if start_episode or total_episode:
            # 尝试从标题中提取集数信息
            # 这里简化处理，实际应该更智能地解析
            pass
        
        return True
    
    def score_result(self, result: Dict[str, Any], subscription: Dict[str, Any]) -> float:
        """
        为搜索结果评分（用于选择最佳结果）
        
        Returns:
            float: 评分（0-100）
        """
        score = 0.0
        title = result.get("title", "").lower()
        
        # 做种数评分（最高40分）
        seeders = result.get("seeders", 0)
        score += min(seeders / 100 * 40, 40)
        
        # 文件大小评分（最高20分，偏好适中大小）
        size_gb = result.get("size_gb", 0)
        if 5 <= size_gb <= 20:  # 电影常见大小
            score += 20
        elif 1 <= size_gb <= 5:  # 剧集常见大小
            score += 15
        elif size_gb > 0:
            score += 10
        
        # 质量匹配评分（最高20分）
        if subscription.get("quality"):
            quality = subscription.get("quality").lower()
            if quality in title or quality in result.get("quality", "").lower():
                score += 20
        
        # 分辨率匹配评分（最高10分）
        if subscription.get("resolution"):
            resolution = subscription.get("resolution").lower()
            if resolution in title or resolution in result.get("resolution", "").lower():
                score += 10
        
        # 特效匹配评分（最高10分）
        if subscription.get("effect"):
            effect = subscription.get("effect").lower()
            if effect in title:
                score += 10
        
        return min(score, 100.0)
    
    def filter_and_sort_results(
        self,
        results: List[Dict[str, Any]],
        subscription: Dict[str, Any],
        sort_by: str = "score"
    ) -> List[Dict[str, Any]]:
        """
        过滤并排序搜索结果
        
        Args:
            results: 搜索结果列表
            subscription: 订阅配置
            sort_by: 排序方式（score, seeders, size）
        
        Returns:
            过滤并排序后的结果列表
        """
        # 1. 过滤
        filtered = [r for r in results if self.match_result(r, subscription)]
        
        # 2. 评分
        for result in filtered:
            result["_rule_score"] = self.score_result(result, subscription)
        
        # 3. 排序
        if sort_by == "score":
            filtered.sort(key=lambda x: x.get("_rule_score", 0), reverse=True)
        elif sort_by == "seeders":
            filtered.sort(key=lambda x: x.get("seeders", 0), reverse=True)
        elif sort_by == "size":
            filtered.sort(key=lambda x: x.get("size_gb", 0), reverse=True)
        
        return filtered

