"""
站点图标服务
实现三级回退机制：资源库logo → favicon抓取 → SVG字母生成
"""

import re
import base64
import httpx
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlparse
from datetime import datetime
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.site_icon import SiteIcon
from app.models.site import Site
from app.modules.site_icon.resource_loader import SiteLogoResourceLoader


class SiteIconService:
    """站点图标服务"""
    
    # 预设的站点图标资源库（常见PT站点）
    PRESET_ICONS: Dict[str, str] = {
        # 可以在这里添加预设的站点图标URL或base64
        # 例如：
        # "pt.example.com": "https://example.com/icon.png",
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.resource_loader = SiteLogoResourceLoader()
    
    async def get_site_icon(
        self,
        site: Site,
        size: int = 40
    ) -> Dict[str, Any]:
        """
        获取站点图标（三级回退）
        
        Args:
            site: 站点对象
            size: 图标尺寸
            
        Returns:
            包含图标信息的字典：
            {
                "type": "preset" | "favicon" | "svg",
                "url": str | None,
                "base64": str | None,
                "svg": str | None
            }
        """
        domain = self._extract_domain(site.url)
        if not domain:
            return self._generate_svg_icon(site.name, size)
        
        # 1. 检查数据库缓存
        cached_icon = await self._get_cached_icon(domain)
        if cached_icon and cached_icon.base64:
            return {
                "type": "cached",
                "url": cached_icon.url,
                "base64": cached_icon.base64,
                "svg": None
            }
        
        # 2. 尝试从资源文件系统加载Logo
        logo_svg = self.resource_loader.get_logo(str(site.id))
        if logo_svg:
            # 保存到数据库（作为SVG）
            await self._save_icon(domain, site.name, None, None, svg=logo_svg)
            return {
                "type": "preset",
                "url": self.resource_loader.get_logo_path(str(site.id)),
                "base64": None,
                "svg": logo_svg
            }
        
        # 3. 尝试预设资源库（兼容旧代码）
        preset_icon = self._get_preset_icon(domain)
        if preset_icon:
            # 保存到数据库
            await self._save_icon(domain, site.name, preset_icon, None)
            return {
                "type": "preset",
                "url": preset_icon,
                "base64": None,
                "svg": None
            }
        
        # 4. 尝试抓取favicon（支持多域名尝试）
        favicon_result = await self._fetch_favicon_with_domains(site, site.cookie)
        if favicon_result:
            icon_url, icon_base64 = favicon_result
            # 保存到数据库
            await self._save_icon(domain, site.name, icon_url, icon_base64)
            return {
                "type": "favicon",
                "url": icon_url,
                "base64": icon_base64,
                "svg": None
            }
        
        # 5. 生成SVG字母图标（使用渐变效果）
        svg_icon = self._generate_svg_icon(site.name, size, site_id=str(site.id))
        return svg_icon
    
    async def _get_cached_icon(self, domain: str) -> Optional[SiteIcon]:
        """从数据库获取缓存的图标"""
        try:
            result = await self.db.execute(
                select(SiteIcon).where(SiteIcon.domain == domain)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取缓存图标失败: {e}")
            return None
    
    def _get_preset_icon(self, domain: str) -> Optional[str]:
        """从预设资源库获取图标"""
        return self.PRESET_ICONS.get(domain)
    
    async def _fetch_favicon(
        self,
        site_url: str,
        cookie: Optional[str] = None
    ) -> Optional[Tuple[str, str]]:
        """
        抓取站点favicon
        
        Returns:
            (icon_url, icon_base64) 或 None
        """
        try:
            domain = self._extract_domain(site_url)
            if not domain:
                return None
            
            # 尝试多个常见的favicon路径
            favicon_paths = [
                f"https://{domain}/favicon.ico",
                f"https://{domain}/favicon.png",
                f"https://{domain}/apple-touch-icon.png",
                f"https://{domain}/logo.png",
            ]
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            if cookie:
                headers["Cookie"] = cookie
            
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
                for favicon_url in favicon_paths:
                    try:
                        response = await client.get(favicon_url, headers=headers)
                        if response.status_code == 200 and response.content:
                            # 转换为base64
                            icon_base64 = base64.b64encode(response.content).decode('utf-8')
                            # 添加data URI前缀
                            content_type = response.headers.get('content-type', 'image/png')
                            icon_base64 = f"data:{content_type};base64,{icon_base64}"
                            return (favicon_url, icon_base64)
                    except Exception as e:
                        logger.debug(f"抓取favicon失败 {favicon_url}: {e}")
                        continue
                
                # 如果直接抓取失败，尝试从HTML中解析
                try:
                    response = await client.get(f"https://{domain}", headers=headers)
                    if response.status_code == 200:
                        html = response.text
                        # 查找favicon链接
                        favicon_match = re.search(
                            r'<link[^>]*rel=["\'](?:shortcut )?icon["\'][^>]*href=["\']([^"\']+)["\']',
                            html,
                            re.IGNORECASE
                        )
                        if favicon_match:
                            favicon_href = favicon_match.group(1)
                            # 处理相对路径
                            if favicon_href.startswith('//'):
                                favicon_url = f"https:{favicon_href}"
                            elif favicon_href.startswith('/'):
                                favicon_url = f"https://{domain}{favicon_href}"
                            elif not favicon_href.startswith('http'):
                                favicon_url = f"https://{domain}/{favicon_href}"
                            else:
                                favicon_url = favicon_href
                            
                            # 抓取favicon
                            icon_response = await client.get(favicon_url, headers=headers)
                            if icon_response.status_code == 200 and icon_response.content:
                                icon_base64 = base64.b64encode(icon_response.content).decode('utf-8')
                                content_type = icon_response.headers.get('content-type', 'image/png')
                                icon_base64 = f"data:{content_type};base64,{icon_base64}"
                                return (favicon_url, icon_base64)
                except Exception as e:
                    logger.debug(f"从HTML解析favicon失败: {e}")
            
            return None
        except Exception as e:
            logger.error(f"抓取favicon异常: {e}")
            return None
    
    def _generate_svg_icon(self, site_name: str, size: int = 40, site_id: Optional[str] = None) -> Dict[str, Any]:
        """
        生成SVG字母图标（使用HSL渐变效果，与参考包一致）
        
        Args:
            site_name: 站点名称
            size: 图标尺寸
            site_id: 站点ID（用于生成稳定的hash）
            
        Returns:
            包含SVG图标的字典
        """
        import hashlib
        
        # 获取首字母
        if not site_name:
            letter = "?"
        else:
            # 提取中文字符或英文字母
            chinese_match = re.search(r'[\u4e00-\u9fff]', site_name)
            if chinese_match:
                letter = chinese_match.group(0)
            else:
                letter = site_name[0].upper() if site_name else "?"
        
        # 使用站点ID或站点名称生成hash（与参考包一致）
        hash_input = str(site_id) if site_id else site_name
        h = int(hashlib.sha1(hash_input.encode()).hexdigest(), 16)
        hue1 = h % 360
        hue2 = (h + 137) % 360
        
        # 生成SVG（与参考包一致）
        svg = f'''<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}' viewBox='0 0 256 256'>
<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>
<stop offset='0%' stop-color='hsl({hue1} 65% 54%)'/>
<stop offset='100%' stop-color='hsl({hue2} 70% 46%)'/>
</linearGradient></defs>
<rect x='8' y='8' width='240' height='240' rx='56' fill='url(#g)'/>
<text x='50%' y='54%' text-anchor='middle' dominant-baseline='middle'
font-family='Inter, Arial' font-size='136' fill='white' font-weight='700'>{letter}</text>
</svg>'''
        
        return {
            "type": "svg",
            "url": None,
            "base64": None,
            "svg": svg
        }
    
    async def _save_icon(
        self,
        domain: str,
        name: str,
        url: Optional[str],
        base64: Optional[str],
        svg: Optional[str] = None
    ):
        """
        保存图标到数据库
        
        Args:
            domain: 域名
            name: 站点名称
            url: 图标URL
            base64: 图标Base64编码
            svg: SVG内容（如果提供，会转换为base64存储）
        """
        try:
            # 如果有SVG，转换为base64存储
            if svg and not base64:
                import base64 as b64
                svg_bytes = svg.encode('utf-8')
                base64 = f"data:image/svg+xml;base64,{b64.b64encode(svg_bytes).decode('utf-8')}"
            
            result = await self.db.execute(
                select(SiteIcon).where(SiteIcon.domain == domain)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.url = url
                existing.base64 = base64
                existing.name = name
                existing.updated_at = datetime.utcnow()
            else:
                new_icon = SiteIcon(
                    domain=domain,
                    name=name,
                    url=url,
                    base64=base64
                )
                self.db.add(new_icon)
            
            await self.db.commit()
        except Exception as e:
            logger.error(f"保存图标失败: {e}")
            await self.db.rollback()
    
    async def _fetch_favicon_with_domains(
        self,
        site: Site,
        cookie: Optional[str] = None
    ) -> Optional[Tuple[str, str]]:
        """
        从多个域名尝试抓取favicon（支持域名配置）
        
        Args:
            site: 站点对象
            cookie: Cookie
            
        Returns:
            (icon_url, icon_base64) 或 None
        """
        # 获取站点域名配置（如果存在）
        domains_to_try = [site.url]
        try:
            from app.modules.site_domain.service import SiteDomainService
            domain_service = SiteDomainService(self.db)
            domain_config = await domain_service.get_domain_config(site.id)
            if domain_config:
                active_domains = domain_config.get_active_domains()
                if active_domains:
                    domains_to_try = active_domains
        except Exception as e:
            logger.debug(f"获取站点域名配置失败，使用原始URL: {e}")
        
        # 尝试每个域名
        for domain_url in domains_to_try:
            result = await self._fetch_favicon(domain_url, cookie)
            if result:
                return result
        
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
            # 移除端口号
            domain = domain.split(':')[0]
            return domain.lower()
        except Exception as e:
            logger.debug(f"提取域名失败: {e}")
            return None
    
    async def refresh_icon(self, site: Site) -> Dict[str, Any]:
        """
        刷新站点图标（强制重新抓取）
        
        Args:
            site: 站点对象
            
        Returns:
            图标信息字典
        """
        domain = self._extract_domain(site.url)
        if domain:
            # 删除旧缓存
            result = await self.db.execute(
                select(SiteIcon).where(SiteIcon.domain == domain)
            )
            existing = result.scalar_one_or_none()
            if existing:
                await self.db.delete(existing)
                await self.db.commit()
        
        # 重新获取
        return await self.get_site_icon(site)

