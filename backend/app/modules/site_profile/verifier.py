"""
站点验证规则引擎
根据verify规则验证站点类型
"""

import re
from typing import Dict, Any, Optional, List
from lxml import html
from loguru import logger
import httpx


class SiteVerifier:
    """站点验证规则引擎"""
    
    def __init__(self, site_url: str, cookie: Optional[str] = None):
        """
        初始化验证器
        
        Args:
            site_url: 站点URL
            cookie: Cookie（可选）
        """
        self.site_url = site_url.rstrip('/')
        self.cookie = cookie
        self._html_cache: Optional[str] = None
    
    async def verify(self, verify_rules: Dict[str, Any]) -> bool:
        """
        根据验证规则验证站点
        
        Args:
            verify_rules: 验证规则字典
            
        Returns:
            是否验证通过
        """
        if not verify_rules:
            return True
        
        # 支持 any/all 逻辑
        if "any" in verify_rules:
            rules = verify_rules["any"]
            return await self._verify_any(rules)
        elif "all" in verify_rules:
            rules = verify_rules["all"]
            return await self._verify_all(rules)
        else:
            # 单个规则
            return await self._verify_rule(verify_rules)
    
    async def _verify_any(self, rules: List[Dict[str, Any]]) -> bool:
        """验证任意一个规则通过"""
        for rule in rules:
            if await self._verify_rule(rule):
                return True
        return False
    
    async def _verify_all(self, rules: List[Dict[str, Any]]) -> bool:
        """验证所有规则都通过"""
        for rule in rules:
            if not await self._verify_rule(rule):
                return False
        return True
    
    async def _verify_rule(self, rule: Dict[str, Any]) -> bool:
        """验证单个规则"""
        try:
            # meta_generator_equals: 检查meta generator标签
            if "meta_generator_equals" in rule:
                value = rule["meta_generator_equals"]
                return await self._check_meta_generator(value)
            
            # title_contains: 检查标题包含
            elif "title_contains" in rule:
                value = rule["title_contains"]
                return await self._check_title_contains(value)
            
            # url_contains: 检查URL包含
            elif "url_contains" in rule:
                value = rule["url_contains"]
                return value in self.site_url
            
            # selector_exists: 检查CSS选择器是否存在
            elif "selector_exists" in rule:
                selector = rule["selector_exists"]
                return await self._check_selector_exists(selector)
            
            # text_contains: 检查文本包含
            elif "text_contains" in rule:
                selector = rule.get("selector", "body")
                text = rule["text_contains"]
                return await self._check_text_contains(selector, text)
            
            # regex_match: 正则表达式匹配
            elif "regex_match" in rule:
                selector = rule.get("selector", "body")
                pattern = rule["regex_match"]
                return await self._check_regex_match(selector, pattern)
            
            else:
                logger.warning(f"未知的验证规则: {rule}")
                return False
                
        except Exception as e:
            logger.error(f"验证规则失败: {rule}, {e}")
            return False
    
    async def _get_html(self) -> str:
        """获取站点HTML（带缓存）"""
        if self._html_cache:
            return self._html_cache
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            if self.cookie:
                headers["Cookie"] = self.cookie
            
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(self.site_url, headers=headers)
                if response.status_code == 200:
                    self._html_cache = response.text
                    return self._html_cache
        except Exception as e:
            logger.error(f"获取站点HTML失败: {e}")
        
        return ""
    
    async def _check_meta_generator(self, value: str) -> bool:
        """检查meta generator标签"""
        html_content = await self._get_html()
        if not html_content:
            return False
        
        try:
            doc = html.fromstring(html_content)
            meta_generator = doc.xpath('//meta[@name="generator"]/@content')
            if meta_generator:
                return value.lower() in meta_generator[0].lower()
        except Exception as e:
            logger.debug(f"检查meta generator失败: {e}")
        
        return False
    
    async def _check_title_contains(self, value: str) -> bool:
        """检查标题包含"""
        html_content = await self._get_html()
        if not html_content:
            return False
        
        try:
            doc = html.fromstring(html_content)
            title = doc.xpath('//title/text()')
            if title:
                return value.lower() in title[0].lower()
        except Exception as e:
            logger.debug(f"检查标题失败: {e}")
        
        return False
    
    async def _check_selector_exists(self, selector: str) -> bool:
        """检查CSS选择器是否存在"""
        html_content = await self._get_html()
        if not html_content:
            return False
        
        try:
            doc = html.fromstring(html_content)
            elements = doc.cssselect(selector)
            return len(elements) > 0
        except Exception as e:
            logger.debug(f"检查选择器失败: {selector}, {e}")
        
        return False
    
    async def _check_text_contains(self, selector: str, text: str) -> bool:
        """检查文本包含"""
        html_content = await self._get_html()
        if not html_content:
            return False
        
        try:
            doc = html.fromstring(html_content)
            elements = doc.cssselect(selector)
            for element in elements:
                element_text = element.text_content()
                if text.lower() in element_text.lower():
                    return True
        except Exception as e:
            logger.debug(f"检查文本包含失败: {selector}, {e}")
        
        return False
    
    async def _check_regex_match(self, selector: str, pattern: str) -> bool:
        """检查正则表达式匹配"""
        html_content = await self._get_html()
        if not html_content:
            return False
        
        try:
            doc = html.fromstring(html_content)
            elements = doc.cssselect(selector)
            for element in elements:
                element_text = element.text_content()
                if re.search(pattern, element_text, re.IGNORECASE):
                    return True
        except Exception as e:
            logger.debug(f"检查正则匹配失败: {selector}, {e}")
        
        return False

