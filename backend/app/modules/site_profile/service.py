"""
站点配置文件服务
整合配置文件加载、验证和解析功能
"""

from typing import Optional, Dict, Any
from urllib.parse import urlparse
from loguru import logger

from app.modules.site_profile.loader import SiteProfileLoader
from app.modules.site_profile.verifier import SiteVerifier
from app.modules.site_profile.parser import SiteParser
from app.models.site import Site


class SiteProfileService:
    """站点配置文件服务"""
    
    def __init__(self):
        self.loader = SiteProfileLoader()
    
    async def identify_site(self, site: Site) -> Optional[Dict[str, Any]]:
        """
        识别站点类型（根据配置文件）
        
        Args:
            site: 站点对象
            
        Returns:
            匹配的配置文件，如果未匹配返回None
        """
        # 1. 从域名查找配置文件
        domain = self._extract_domain(site.url)
        if domain:
            profile = self.loader.find_profile_by_domain(domain)
            if profile:
                # 验证站点是否符合配置
                verifier = SiteVerifier(site.url, site.cookie)
                verify_rules = profile.get("verify", {})
                
                if verify_rules:
                    is_valid = await verifier.verify(verify_rules)
                    if is_valid:
                        logger.info(f"站点 {site.name} 匹配配置文件: {profile.get('meta', {}).get('id')}")
                        return profile
                    else:
                        logger.debug(f"站点 {site.name} 域名匹配但验证失败")
                else:
                    # 没有验证规则，直接返回
                    return profile
        
        # 2. 尝试所有配置文件进行验证
        profiles = self.loader.list_profiles()
        for profile_id in profiles:
            profile = self.loader.load_profile(profile_id)
            if not profile:
                continue
            
            verify_rules = profile.get("verify", {})
            if not verify_rules:
                continue
            
            verifier = SiteVerifier(site.url, site.cookie)
            is_valid = await verifier.verify(verify_rules)
            if is_valid:
                logger.info(f"站点 {site.name} 通过验证匹配配置文件: {profile_id}")
                return profile
        
        logger.debug(f"站点 {site.name} 未找到匹配的配置文件")
        return None
    
    async def parse_site_content(
        self,
        site: Site,
        parse_type: str = "list",
        page_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        解析站点内容
        
        Args:
            site: 站点对象
            parse_type: 解析类型（list/detail/user）
            page_url: 要解析的页面URL
            
        Returns:
            解析结果
        """
        # 1. 获取站点配置文件
        profile = await self.identify_site(site)
        if not profile:
            return {}
        
        # 2. 获取解析规则
        parse_rules = profile.get("parse", {})
        if not parse_rules:
            return {}
        
        # 3. 执行解析
        parser = SiteParser(site.url, site.cookie)
        
        if parse_type == "list" and "list" in parse_rules:
            result = await parser._parse_list(parse_rules["list"], page_url)
            return {"list": result}
        elif parse_type == "detail" and "detail" in parse_rules:
            result = await parser._parse_detail(parse_rules["detail"], page_url)
            return {"detail": result}
        elif parse_type == "user" and "user" in parse_rules:
            result = await parser._parse_user(parse_rules["user"], page_url)
            return {"user": result}
        else:
            # 解析所有类型
            return await parser.parse(parse_rules, page_url)
    
    def get_site_family(self, site: Site) -> Optional[str]:
        """
        获取站点类型（family）
        
        Args:
            site: 站点对象
            
        Returns:
            站点类型（如 nexusphp, gazelle等），如果未识别返回None
        """
        # 从域名查找配置文件
        domain = self._extract_domain(site.url)
        if domain:
            profile = self.loader.find_profile_by_domain(domain)
            if profile:
                meta = profile.get("meta", {})
                return meta.get("family")
        
        return None
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """从URL提取域名"""
        try:
            if not url:
                return None
            if not url.startswith(('http://', 'https://')):
                url = f"https://{url}"
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path.split('/')[0]
            domain = domain.split(':')[0]
            return domain.lower()
        except Exception as e:
            logger.debug(f"提取域名失败: {e}")
            return None

