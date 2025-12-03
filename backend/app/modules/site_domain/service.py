"""
站点域名配置服务
实现域名管理、自动检测和切换逻辑
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
import httpx
from loguru import logger
from datetime import datetime

from app.models.site import Site
from app.models.site_domain import SiteDomainConfig


class SiteDomainService:
    """站点域名配置服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_domain_config(self, site_id: int) -> Optional[SiteDomainConfig]:
        """获取站点域名配置"""
        result = await self.db.execute(
            select(SiteDomainConfig).where(SiteDomainConfig.site_id == site_id)
        )
        return result.scalar_one_or_none()
    
    async def get_or_create_domain_config(self, site_id: int) -> SiteDomainConfig:
        """获取或创建站点域名配置"""
        config = await self.get_domain_config(site_id)
        if not config:
            # 获取站点信息
            site = await self.db.execute(
                select(Site).where(Site.id == site_id)
            )
            site = site.scalar_one_or_none()
            if not site:
                raise ValueError(f"站点 {site_id} 不存在")
            
            # 从站点URL提取域名
            parsed = urlparse(site.url)
            initial_domain = f"{parsed.scheme}://{parsed.netloc}"
            
            # 创建配置
            config = SiteDomainConfig(
                site_id=site_id,
                active_domains=[initial_domain],
                current_domain=initial_domain
            )
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)
        
        return config
    
    async def update_domain_config(
        self,
        site_id: int,
        active_domains: Optional[List[str]] = None,
        deprecated_domains: Optional[List[str]] = None,
        current_domain: Optional[str] = None,
        auto_detect: Optional[bool] = None
    ) -> SiteDomainConfig:
        """更新站点域名配置"""
        config = await self.get_or_create_domain_config(site_id)
        
        if active_domains is not None:
            config.active_domains = active_domains
        if deprecated_domains is not None:
            config.deprecated_domains = deprecated_domains
        if current_domain is not None:
            if current_domain not in config.get_active_domains():
                raise ValueError(f"域名 {current_domain} 不在活跃域名列表中")
            config.current_domain = current_domain
        if auto_detect is not None:
            config.auto_detect = 1 if auto_detect else 0
        
        config.updated_at = datetime.utcnow()
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        
        return config
    
    async def add_domain(self, site_id: int, domain: str, is_active: bool = True) -> SiteDomainConfig:
        """添加域名"""
        config = await self.get_or_create_domain_config(site_id)
        
        # 规范化域名
        domain = self._normalize_domain(domain)
        
        if is_active:
            # 添加到活跃列表
            if config.add_active_domain(domain):
                # 如果当前没有域名，设置为当前域名
                if not config.current_domain:
                    config.current_domain = domain
        else:
            # 添加到废弃列表
            deprecated = config.get_deprecated_domains()
            if domain not in deprecated:
                deprecated.append(domain)
                config.deprecated_domains = deprecated
        
        config.updated_at = datetime.utcnow()
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        
        return config
    
    async def remove_domain(self, site_id: int, domain: str) -> SiteDomainConfig:
        """移除域名（从活跃移到废弃）"""
        config = await self.get_or_create_domain_config(site_id)
        
        if config.remove_active_domain(domain):
            config.updated_at = datetime.utcnow()
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)
        
        return config
    
    async def switch_domain(self, site_id: int, domain: str, reason: str = "手动切换") -> SiteDomainConfig:
        """切换到指定域名"""
        config = await self.get_or_create_domain_config(site_id)
        
        # 规范化域名
        domain = self._normalize_domain(domain)
        
        if config.switch_to_domain(domain, reason):
            config.updated_at = datetime.utcnow()
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)
        else:
            raise ValueError(f"域名 {domain} 不在活跃域名列表中")
        
        return config
    
    async def detect_and_switch_domain(self, site_id: int) -> Dict[str, Any]:
        """
        自动检测并切换域名
        尝试访问所有活跃域名，选择第一个可访问的域名
        """
        config = await self.get_or_create_domain_config(site_id)
        
        if not config.auto_detect:
            return {
                "switched": False,
                "reason": "自动检测已禁用",
                "current_domain": config.get_current_domain()
            }
        
        active_domains = config.get_active_domains()
        if not active_domains:
            return {
                "switched": False,
                "reason": "没有活跃域名",
                "current_domain": None
            }
        
        # 测试所有活跃域名
        accessible_domains = []
        for domain in active_domains:
            if await self._test_domain_accessibility(domain):
                accessible_domains.append(domain)
        
        if not accessible_domains:
            logger.warning(f"站点 {site_id} 的所有活跃域名都不可访问")
            config.last_detect_time = datetime.utcnow()
            self.db.add(config)
            await self.db.commit()
            return {
                "switched": False,
                "reason": "所有活跃域名都不可访问",
                "current_domain": config.get_current_domain()
            }
        
        # 选择第一个可访问的域名
        new_domain = accessible_domains[0]
        current_domain = config.get_current_domain()
        
        if new_domain != current_domain:
            # 切换到新域名
            config.switch_to_domain(new_domain, reason="自动检测切换")
            config.last_detect_time = datetime.utcnow()
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)
            
            logger.info(f"站点 {site_id} 自动切换到域名: {new_domain} (原域名: {current_domain})")
            
            return {
                "switched": True,
                "from": current_domain,
                "to": new_domain,
                "reason": "自动检测切换",
                "current_domain": new_domain
            }
        else:
            config.last_detect_time = datetime.utcnow()
            self.db.add(config)
            await self.db.commit()
            
            return {
                "switched": False,
                "reason": "当前域名可访问，无需切换",
                "current_domain": current_domain
            }
    
    async def get_best_domain(self, site_id: int) -> Optional[str]:
        """
        获取最佳域名（当前域名或自动检测）
        用于站点服务中自动选择域名
        """
        config = await self.get_or_create_domain_config(site_id)
        
        current = config.get_current_domain()
        if not current:
            return None
        
        # 如果启用了自动检测，先检测当前域名是否可访问
        if config.auto_detect:
            if not await self._test_domain_accessibility(current):
                # 当前域名不可访问，尝试自动切换
                result = await self.detect_and_switch_domain(site_id)
                if result.get("switched"):
                    return result.get("current_domain")
        
        return current
    
    async def _test_domain_accessibility(self, domain: str, timeout: int = 5) -> bool:
        """测试域名是否可访问"""
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(domain, allow_redirects=True)
                return response.status_code < 500
        except Exception as e:
            logger.debug(f"域名 {domain} 不可访问: {e}")
            return False
    
    def _normalize_domain(self, domain: str) -> str:
        """规范化域名（确保包含协议）"""
        domain = domain.strip()
        if not domain.startswith(("http://", "https://")):
            domain = f"https://{domain}"
        # 移除末尾的斜杠
        domain = domain.rstrip("/")
        return domain
    
    async def get_domain_info(self, site_id: int) -> Dict[str, Any]:
        """获取域名配置信息"""
        config = await self.get_or_create_domain_config(site_id)
        
        return {
            "site_id": site_id,
            "active_domains": config.get_active_domains(),
            "deprecated_domains": config.get_deprecated_domains(),
            "current_domain": config.get_current_domain(),
            "auto_detect": bool(config.auto_detect),
            "last_detect_time": config.last_detect_time.isoformat() if config.last_detect_time else None,
            "switch_history": config.switch_history[-10:] if config.switch_history else [],  # 最近10条
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat()
        }

