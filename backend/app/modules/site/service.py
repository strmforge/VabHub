"""
站点服务
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from app.models.site import Site


class SiteService:
    """站点服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _get_site_url(self, site: Site) -> str:
        """
        获取站点URL（优先使用域名配置中的最佳域名）
        """
        try:
            from app.modules.site_domain.service import SiteDomainService
            domain_service = SiteDomainService(self.db)
            best_domain = await domain_service.get_best_domain(site.id)
            if best_domain:
                return best_domain
        except Exception as e:
            logger.debug(f"获取站点最佳域名失败，使用原始URL: {e}")
        
        return site.url
    
    async def create_site(self, site: dict) -> Site:
        """创建站点"""
        new_site = Site(
            name=site.get("name"),
            url=site.get("url"),
            cookie=site.get("cookie"),
            cookiecloud_uuid=site.get("cookiecloud_uuid"),
            cookiecloud_password=site.get("cookiecloud_password"),
            cookiecloud_server=site.get("cookiecloud_server"),
            is_active=site.get("is_active", True)
        )
        
        self.db.add(new_site)
        await self.db.commit()
        await self.db.refresh(new_site)
        
        return new_site
    
    async def list_sites(self, active_only: bool = False, active: bool = False) -> List[Site]:
        """获取站点列表"""
        query = select(Site)
        
        # 支持两种参数名
        if active_only or active:
            query = query.where(Site.is_active == True)
        
        query = query.order_by(Site.name)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_site(self, site_id: int) -> Optional[Site]:
        """获取站点详情"""
        result = await self.db.execute(
            select(Site).where(Site.id == site_id)
        )
        return result.scalar_one_or_none()
    
    async def update_site(self, site_id: int, site: dict) -> Optional[Site]:
        """更新站点"""
        existing = await self.get_site(site_id)
        if not existing:
            return None
        
        if "name" in site:
            existing.name = site["name"]
        if "url" in site:
            existing.url = site["url"]
        if "cookie" in site:
            existing.cookie = site.get("cookie")
        if "cookiecloud_uuid" in site:
            existing.cookiecloud_uuid = site.get("cookiecloud_uuid")
        if "cookiecloud_password" in site:
            existing.cookiecloud_password = site.get("cookiecloud_password")
        if "cookiecloud_server" in site:
            existing.cookiecloud_server = site.get("cookiecloud_server")
        if "is_active" in site:
            existing.is_active = site.get("is_active", True)
        if "user_data" in site:
            existing.user_data = site.get("user_data")
        
        self.db.add(existing)
        await self.db.commit()
        await self.db.refresh(existing)
        
        return existing
    
    async def delete_site(self, site_id: int) -> bool:
        """删除站点"""
        from sqlalchemy import delete
        
        result = await self.db.execute(
            delete(Site).where(Site.id == site_id)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    
    async def checkin(self, site_id: int) -> Dict[str, Any]:
        """
        执行站点签到
        
        Args:
            site_id: 站点ID
            
        Returns:
            签到结果字典
        """
        from app.modules.site.checkin import SiteCheckin
        from app.core.cookiecloud import CookieCloudClient
        from datetime import datetime
        from loguru import logger
        
        site = await self.get_site(site_id)
        if not site:
            return {
                "success": False,
                "message": "站点不存在"
            }
        
        if not site.is_active:
            return {
                "success": False,
                "message": "站点未启用"
            }
        
        try:
            # 获取Cookie
            cookies = site.cookie
            
            # 如果配置了CookieCloud，尝试从CookieCloud同步
            if site.cookiecloud_uuid and site.cookiecloud_server:
                try:
                    cookiecloud_client = CookieCloudClient(
                        server_url=site.cookiecloud_server,
                        uuid=site.cookiecloud_uuid,
                        password=site.cookiecloud_password or ""
                    )
                    cookie_data = await cookiecloud_client.get_cookies()
                    
                    # 从CookieCloud数据中提取对应站点的Cookie
                    if cookie_data:
                        site_url = site.url
                        # 提取站点域名
                        from urllib.parse import urlparse
                        parsed_url = urlparse(site_url)
                        site_domain = parsed_url.netloc
                        
                        # 尝试匹配域名
                        for domain, cookie_string in cookie_data.items():
                            # 清理域名进行匹配
                            domain_clean = domain.replace("http://", "").replace("https://", "").split("/")[0]
                            if domain_clean in site_domain or site_domain in domain_clean:
                                cookies = cookie_string
                                break
                
                except Exception as e:
                    logger.warning(f"从CookieCloud获取Cookie失败: {e}，使用本地Cookie")
            
            if not cookies:
                return {
                    "success": False,
                    "message": "站点Cookie未配置"
                }
            
            # 获取最佳域名（如果配置了域名管理）
            site_url = await self._get_site_url(site)
            
            # 执行签到
            checkin_handler = SiteCheckin(site_url=site_url, cookies=cookies)
            result = await checkin_handler.checkin()
            
            # 更新最后签到时间
            if result.get("success"):
                site.last_checkin = datetime.utcnow()
                self.db.add(site)
                await self.db.commit()
                logger.info(f"站点签到成功: {site.name}")
            else:
                logger.warning(f"站点签到失败: {site.name} - {result.get('message')}")
            
            return result
        
        except Exception as e:
            logger.error(f"站点签到异常: {site.name} - {e}")
            return {
                "success": False,
                "message": f"签到失败: {str(e)}"
            }
    
    async def batch_checkin(self, site_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        批量签到
        
        Args:
            site_ids: 站点ID列表，如果为None则签到所有启用的站点
            
        Returns:
            批量签到结果
        """
        if site_ids:
            sites = [await self.get_site(site_id) for site_id in site_ids]
            sites = [s for s in sites if s and s.is_active]
        else:
            sites = await self.list_sites(active_only=True)
        
        success_count = 0
        failed_count = 0
        results = []
        
        for site in sites:
            result = await self.checkin(site.id)
            if result.get("success"):
                success_count += 1
            else:
                failed_count += 1
            
            results.append({
                "site_id": site.id,
                "site_name": site.name,
                **result
            })
        
        return {
            "success": True,
            "total": len(sites),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results
        }
    
    async def test_connection(self, site_id: int) -> Dict[str, Any]:
        """
        测试站点连接
        
        Args:
            site_id: 站点ID
            
        Returns:
            连接测试结果字典
        """
        import httpx
        from urllib.parse import urlparse
        from loguru import logger
        
        site = await self.get_site(site_id)
        if not site:
            return {
                "success": False,
                "message": "站点不存在"
            }
        
        try:
            # 获取Cookie
            cookies = site.cookie
            
            # 如果配置了CookieCloud，尝试从CookieCloud同步
            if site.cookiecloud_uuid and site.cookiecloud_server:
                try:
                    from app.core.cookiecloud import CookieCloudClient
                    cookiecloud_client = CookieCloudClient(
                        server_url=site.cookiecloud_server,
                        uuid=site.cookiecloud_uuid,
                        password=site.cookiecloud_password or ""
                    )
                    cookie_data = await cookiecloud_client.get_cookies()
                    
                    # 从CookieCloud数据中提取对应站点的Cookie
                    if cookie_data:
                        # 使用最佳域名（如果配置了域名管理）
                        site_url = await self._get_site_url(site)
                        from urllib.parse import urlparse
                        parsed_url = urlparse(site_url)
                        site_domain = parsed_url.netloc
                        
                        # 尝试匹配域名
                        for domain, cookie_string in cookie_data.items():
                            domain_clean = domain.replace("http://", "").replace("https://", "").split("/")[0]
                            if domain_clean in site_domain or site_domain in domain_clean:
                                cookies = cookie_string
                                break
                
                except Exception as e:
                    logger.warning(f"从CookieCloud获取Cookie失败: {e}，使用本地Cookie")
            
            # 解析Cookie
            cookie_dict = {}
            if cookies:
                for item in cookies.split(';'):
                    item = item.strip()
                    if '=' in item:
                        key, value = item.split('=', 1)
                        cookie_dict[key.strip()] = value.strip()
            
            # 测试连接
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                # 1. 测试基本连接
                try:
                    response = await client.get(
                        site.url,
                        cookies=cookie_dict,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                        }
                    )
                    
                    status_code = response.status_code
                    response_time = response.elapsed.total_seconds()
                    
                    # 检查响应内容
                    html_content = response.text.lower()
                    is_accessible = status_code == 200
                    
                    # 检查是否需要登录（常见的登录页面标识）
                    needs_login = any(keyword in html_content for keyword in [
                        "login", "sign in", "登录", "请登录", "username", "password"
                    ])
                    
                    # 检查Cookie是否有效（如果响应中包含用户信息，说明Cookie有效）
                    cookie_valid = not needs_login or any(keyword in html_content for keyword in [
                        "user", "profile", "dashboard", "用户", "个人中心", "控制面板"
                    ])
                    
                    # 尝试获取用户数据（如果可能）
                    user_info = None
                    if cookie_valid and not needs_login:
                        # 尝试提取用户数据（简化版）
                        # 实际实现可能需要解析HTML或调用API
                        try:
                            # 这里可以尝试提取上传量、下载量等信息
                            # 简化处理，实际需要根据站点HTML结构解析
                            user_info = {
                                "logged_in": True,
                                "username": None,  # 需要从HTML中提取
                                "upload": None,  # 需要从HTML中提取
                                "download": None  # 需要从HTML中提取
                            }
                        except:
                            pass
                    
                    return {
                        "success": True,
                        "message": "连接测试完成",
                        "site_id": site_id,
                        "site_name": site.name,
                        "site_url": site.url,
                        "status_code": status_code,
                        "response_time": response_time,
                        "is_accessible": is_accessible,
                        "needs_login": needs_login,
                        "cookie_valid": cookie_valid,
                        "has_cookie": bool(cookies),
                        "user_info": user_info,
                        "details": {
                            "status": "connected" if is_accessible and cookie_valid else "disconnected",
                            "message": "站点连接正常，Cookie有效" if (is_accessible and cookie_valid) else 
                                      ("站点可访问但需要登录" if is_accessible else "站点无法访问")
                        }
                    }
                
                except httpx.TimeoutException:
                    return {
                        "success": False,
                        "message": "连接超时",
                        "site_id": site_id,
                        "site_name": site.name,
                        "site_url": site.url,
                        "details": {
                            "status": "timeout",
                            "message": "站点连接超时，请检查网络或站点地址"
                        }
                    }
                
                except httpx.ConnectError:
                    return {
                        "success": False,
                        "message": "无法连接到站点",
                        "site_id": site_id,
                        "site_name": site.name,
                        "site_url": site.url,
                        "details": {
                            "status": "connection_error",
                            "message": "无法连接到站点，请检查站点地址"
                        }
                    }
                
                except Exception as e:
                    logger.error(f"测试站点连接异常: {e}")
                    return {
                        "success": False,
                        "message": f"连接测试失败: {str(e)}",
                        "site_id": site_id,
                        "site_name": site.name,
                        "site_url": site.url,
                        "details": {
                            "status": "error",
                            "message": str(e)
                        }
                    }
        
        except Exception as e:
            logger.error(f"测试站点连接异常: {site.name} - {e}")
            return {
                "success": False,
                "message": f"连接测试失败: {str(e)}",
                "site_id": site_id,
                "site_name": site.name
            }

