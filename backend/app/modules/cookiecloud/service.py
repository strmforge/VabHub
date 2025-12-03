"""
CookieCloud同步服务
"""

from typing import List, Dict, Optional, Set
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from loguru import logger

from app.core.cookiecloud import CookieCloudClient
from app.models.cookiecloud import CookieCloudSettings
from app.models.site import Site
from app.schemas.cookiecloud import (
    CookieCloudSyncResult, 
    SiteCookieSyncResult,
    CookieCloudSiteSyncResult,
    CookieSource
)


class CookieCloudSyncService:
    """CookieCloud同步服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _get_settings(self) -> Optional[CookieCloudSettings]:
        """获取CookieCloud全局配置"""
        try:
            result = await self.db.execute(
                select(CookieCloudSettings).where(CookieCloudSettings.id == 1)
            )
            settings = result.scalar_one_or_none()
            return settings
        except Exception as e:
            logger.error(f"获取CookieCloud配置失败: {e}")
            return None
    
    async def _update_settings_status(self, status: str, error: Optional[str] = None):
        """更新配置状态"""
        try:
            update_data = {
                "last_sync_at": datetime.utcnow(),
                "last_status": status
            }
            if error:
                update_data["last_error"] = error
            else:
                update_data["last_error"] = None
            
            await self.db.execute(
                update(CookieCloudSettings)
                .where(CookieCloudSettings.id == 1)
                .values(**update_data)
            )
            await self.db.commit()
        except Exception as e:
            logger.error(f"更新CookieCloud配置状态失败: {e}")
    
    def _extract_domain_cookies(self, cookie_data: Dict, domain: str) -> str:
        """从CookieCloud数据中提取指定域名的Cookie字符串"""
        try:
            if not cookie_data.get("cookie_data"):
                return ""
            
            cookies = cookie_data["cookie_data"]
            
            # 查找匹配的域名
            matched_cookies = []
            
            # 精确匹配
            if domain in cookies:
                domain_cookies = cookies[domain]
                if isinstance(domain_cookies, list):
                    for cookie in domain_cookies:
                        if isinstance(cookie, dict):
                            name = cookie.get("name", "")
                            value = cookie.get("value", "")
                            if name and value:
                                matched_cookies.append(f"{name}={value}")
                elif isinstance(domain_cookies, str):
                    matched_cookies.append(domain_cookies)
            
            # 模糊匹配（子域名）
            else:
                for cookie_domain, domain_cookies in cookies.items():
                    if isinstance(domain_cookies, list):
                        # 检查域名匹配
                        if self._is_domain_match(cookie_domain, domain):
                            for cookie in domain_cookies:
                                if isinstance(cookie, dict):
                                    name = cookie.get("name", "")
                                    value = cookie.get("value", "")
                                    if name and value:
                                        matched_cookies.append(f"{name}={value}")
            
            return "; ".join(matched_cookies)
            
        except Exception as e:
            logger.error(f"提取域名Cookie失败 {domain}: {e}")
            return ""
    
    def _is_domain_match(self, cookie_domain: str, site_domain: str) -> bool:
        """检查域名是否匹配，支持多级子域名匹配"""
        # 清理域名
        cookie_domain = cookie_domain.lower().replace("http://", "").replace("https://", "").split("/")[0]
        site_domain = site_domain.lower().replace("http://", "").replace("https://", "").split("/")[0]
        
        # 精确匹配
        if cookie_domain == site_domain:
            return True
        
        # 去掉前导点
        cookie_domain = cookie_domain.lstrip(".")
        site_domain = site_domain.lstrip(".")
        
        # 子域名匹配：检查是否互为子域名
        # 例如: tracker.hdhome.org 与 hdhome.org 应该匹配
        if cookie_domain.endswith(site_domain) and len(cookie_domain) > len(site_domain):
            # 确保是完整的子域名匹配（前面有点分隔）
            prefix = cookie_domain[:-len(site_domain)]
            if prefix.endswith('.'):
                return True
        
        if site_domain.endswith(cookie_domain) and len(site_domain) > len(cookie_domain):
            # 确保是完整的子域名匹配（前面有点分隔）
            prefix = site_domain[:-len(cookie_domain)]
            if prefix.endswith('.'):
                return True
        
        return False
    
    async def _get_cookies_with_retry(self, client: CookieCloudClient, max_retries: int = 3) -> Optional[Dict]:
        """带重试机制的Cookie获取"""
        import asyncio
        
        for attempt in range(max_retries):
            try:
                cookie_data = await client.get_cookies()
                if cookie_data is not None:
                    return cookie_data
                    
            except Exception as e:
                logger.warning(f"CookieCloud数据获取失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    # 指数退避策略
                    delay = min(2 ** attempt, 10)  # 最大延迟10秒
                    logger.info(f"等待 {delay} 秒后重试...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"CookieCloud数据获取失败，已达到最大重试次数 {max_retries}")
        
        return None
    
    async def _sync_site_batch(self, sites: List[Site], cookie_data: Dict, timeout: int) -> Dict:
        """批量同步站点，支持超时控制"""
        import asyncio
        
        results = {
            'synced': 0,
            'unmatched': 0,
            'errors': 0,
            'error_messages': []
        }
        
        # 创建并发任务列表
        tasks = []
        for site in sites:
            task = asyncio.create_task(
                self._sync_single_site_with_timeout(site, cookie_data, timeout)
            )
            tasks.append((site, task))
        
        # 等待所有任务完成
        for site, task in tasks:
            try:
                result = await task
                
                if result['success']:
                    if result['cookie_updated']:
                        results['synced'] += 1
                        logger.info(f"站点 {site.name} Cookie同步成功")
                    else:
                        results['unmatched'] += 1
                        logger.debug(f"站点 {site.name} 未找到匹配的Cookie")
                else:
                    results['errors'] += 1
                    error_msg = f"站点 {site.name} 同步失败: {result['error']}"
                    results['error_messages'].append(error_msg)
                    logger.error(error_msg)
                    
            except asyncio.TimeoutError:
                results['errors'] += 1
                error_msg = f"站点 {site.name} 同步超时 (>{timeout}s)"
                results['error_messages'].append(error_msg)
                logger.error(error_msg)
                
            except Exception as e:
                results['errors'] += 1
                error_msg = f"站点 {site.name} 同步异常: {e}"
                results['error_messages'].append(error_msg)
                logger.error(error_msg)
        
        return results
    
    async def _sync_single_site_with_timeout(self, site: Site, cookie_data: Dict, timeout: int) -> Dict:
        """同步单个站点，带超时控制"""
        import asyncio
        
        try:
            # 使用asyncio.wait_for实现超时控制
            result = await asyncio.wait_for(
                self._sync_single_site(site, cookie_data),
                timeout=timeout
            )
            return result
            
        except asyncio.TimeoutError:
            raise
        except Exception as e:
            return {
                'success': False,
                'cookie_updated': False,
                'error': str(e)
            }
    
    async def _sync_single_site(self, site: Site, cookie_data: Dict) -> Dict:
        """同步单个站点的核心逻辑"""
        try:
            # 提取Cookie
            cookie_string = self._extract_domain_cookies(cookie_data, site.domain)
            
            if cookie_string:
                # 更新站点Cookie
                await self.db.execute(
                    update(Site)
                    .where(Site.id == site.id)
                    .values(
                        cookie=cookie_string,
                        cookie_source=CookieSource.COOKIECLOUD,
                        last_cookiecloud_sync_at=datetime.utcnow()
                    )
                )
                
                return {
                    'success': True,
                    'cookie_updated': True,
                    'error': None
                }
            else:
                return {
                    'success': True,
                    'cookie_updated': False,
                    'error': None
                }
                
        except Exception as e:
            return {
                'success': False,
                'cookie_updated': False,
                'error': str(e)
            }
    
    async def sync_all_sites(self, batch_size: int = 10, site_timeout: int = 30) -> CookieCloudSyncResult:
        """同步所有站点的Cookie，支持批量处理和超时控制"""
        start_time = datetime.utcnow()
        
        try:
            # 1. 获取配置
            settings = await self._get_settings()
            if not settings:
                return CookieCloudSyncResult(
                    success=False,
                    total_sites=0,
                    synced_sites=0,
                    unmatched_sites=0,
                    error_sites=0,
                    errors=["未找到CookieCloud配置"]
                )
            
            if not settings.enabled:
                return CookieCloudSyncResult(
                    success=False,
                    total_sites=0,
                    synced_sites=0,
                    unmatched_sites=0,
                    error_sites=0,
                    errors=["CookieCloud未启用"]
                )
            
            if not settings.host or not settings.uuid or not settings.password:
                return CookieCloudSyncResult(
                    success=False,
                    total_sites=0,
                    synced_sites=0,
                    unmatched_sites=0,
                    error_sites=0,
                    errors=["CookieCloud配置不完整，请检查host/uuid/password"]
                )
            
            # 2. 创建客户端并获取数据（带重试机制）
            client = CookieCloudClient(settings.host, settings.uuid, settings.password)
            cookie_data = await self._get_cookies_with_retry(client, max_retries=3)
            
            if cookie_data is None:
                await self._update_settings_status("ERROR", "无法从CookieCloud获取数据")
                return CookieCloudSyncResult(
                    success=False,
                    total_sites=0,
                    synced_sites=0,
                    unmatched_sites=0,
                    error_sites=0,
                    errors=["无法从CookieCloud获取数据"]
                )
            
            # 3. 获取所有启用的站点
            result = await self.db.execute(
                select(Site).where(Site.enabled == True)
            )
            sites = result.scalars().all()
            
            # 4. 应用安全域名白名单
            safe_domains: Set[str] = set()
            if settings.safe_host_whitelist:
                try:
                    import json
                    safe_domains = set(json.loads(settings.safe_host_whitelist or "[]"))
                except Exception as e:
                    logger.warning(f"解析安全域名白名单失败: {e}")
            
            # 5. 批量同步站点，支持超时控制
            synced_count = 0
            unmatched_count = 0
            error_count = 0
            errors = []
            
            # 过滤白名单站点
            filtered_sites = []
            for site in sites:
                if safe_domains and site.domain not in safe_domains:
                    logger.debug(f"站点 {site.name} 域名 {site.domain} 不在白名单中，跳过")
                    continue
                filtered_sites.append(site)
            
            logger.info(f"开始批量同步 {len(filtered_sites)} 个站点，批次大小: {batch_size}")
            
            # 分批处理站点
            for i in range(0, len(filtered_sites), batch_size):
                batch_sites = filtered_sites[i:i + batch_size]
                batch_results = await self._sync_site_batch(batch_sites, cookie_data, site_timeout)
                
                synced_count += batch_results['synced']
                unmatched_count += batch_results['unmatched']
                error_count += batch_results['errors']
                errors.extend(batch_results['error_messages'])
                
                logger.info(f"批次 {i//batch_size + 1} 完成: 成功 {batch_results['synced']}, "
                           f"无匹配 {batch_results['unmatched']}, 错误 {batch_results['errors']}")
            
            # 6. 提交更改
            await self.db.commit()
            
            # 7. 更新配置状态
            status = "SUCCESS" if error_count == 0 else "PARTIAL"
            await self._update_settings_status(status)
            
            # 8. 关闭客户端
            await client.close()
            
            return CookieCloudSyncResult(
                success=error_count == 0,
                total_sites=len(sites),
                synced_sites=synced_count,
                unmatched_sites=unmatched_count,
                error_sites=error_count,
                errors=errors,
                sync_time=start_time
            )
            
        except Exception as e:
            await self.db.rollback()
            await self._update_settings_status("ERROR", str(e))
            logger.error(f"CookieCloud同步失败: {e}")
            
            return CookieCloudSyncResult(
                success=False,
                total_sites=0,
                synced_sites=0,
                unmatched_sites=0,
                error_sites=0,
                errors=[str(e)],
                sync_time=start_time
            )
    
    async def sync_site(self, site_id: int) -> CookieCloudSiteSyncResult:
        """同步单个站点的Cookie"""
        start_time = datetime.utcnow()
        
        try:
            # 1. 获取配置
            settings = await self._get_settings()
            if not settings or not settings.enabled:
                return CookieCloudSiteSyncResult(
                    site_id=site_id,
                    site_name="Unknown",
                    success=False,
                    cookie_updated=False,
                    error_message="CookieCloud未启用或配置不完整"
                )
            
            # 2. 获取站点
            result = await self.db.execute(
                select(Site).where(Site.id == site_id)
            )
            site = result.scalar_one_or_none()
            
            if not site:
                return CookieCloudSiteSyncResult(
                    site_id=site_id,
                    site_name="Unknown",
                    success=False,
                    cookie_updated=False,
                    error_message="站点不存在"
                )
            
            if not site.enabled:
                return CookieCloudSiteSyncResult(
                    site_id=site_id,
                    site_name=site.name,
                    success=False,
                    cookie_updated=False,
                    error_message=f"站点 {site.name} 已禁用"
                )
            
            # 3. 检查域名白名单
            safe_domains: Set[str] = set()
            if settings.safe_host_whitelist:
                try:
                    import json
                    safe_domains = set(json.loads(settings.safe_host_whitelist or "[]"))
                    if safe_domains and site.domain not in safe_domains:
                        return CookieCloudSiteSyncResult(
                            site_id=site_id,
                            site_name=site.name,
                            success=False,
                            cookie_updated=False,
                            error_message=f"域名 {site.domain} 不在安全白名单中"
                        )
                except Exception as e:
                    logger.warning(f"解析安全域名白名单失败: {e}")
            
            # 4. 获取CookieCloud数据
            client = CookieCloudClient(settings.host, settings.uuid, settings.password)
            cookie_data = await self._get_cookies_with_retry(client, max_retries=3)
            
            if cookie_data is None:
                await client.close()
                return CookieCloudSiteSyncResult(
                    site_id=site_id,
                    site_name=site.name,
                    success=False,
                    cookie_updated=False,
                    error_message="无法从CookieCloud获取数据"
                )
            
            # 5. 提取并更新Cookie
            cookie_string = self._extract_domain_cookies(cookie_data, site.domain)
            
            if cookie_string:
                await self.db.execute(
                    update(Site)
                    .where(Site.id == site_id)
                    .values(
                        cookie=cookie_string,
                        cookie_source=CookieSource.COOKIECLOUD,
                        last_cookiecloud_sync_at=datetime.utcnow()
                    )
                )
                await self.db.commit()
                
                await client.close()
                
                duration = (datetime.utcnow() - start_time).total_seconds()
                return CookieCloudSiteSyncResult(
                    site_id=site_id,
                    site_name=site.name,
                    success=True,
                    cookie_updated=True,
                    error_message=None,
                    duration_seconds=duration
                )
            else:
                await client.close()
                
                duration = (datetime.utcnow() - start_time).total_seconds()
                return CookieCloudSiteSyncResult(
                    site_id=site_id,
                    site_name=site.name,
                    success=True,
                    cookie_updated=False,
                    error_message=None,
                    duration_seconds=duration
                )
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"站点 {site_id} Cookie同步失败: {e}")
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            return CookieCloudSiteSyncResult(
                site_id=site_id,
                site_name="Unknown",
                success=False,
                cookie_updated=False,
                error_message=str(e),
                duration_seconds=duration
            )
    
    async def test_connection(self) -> bool:
        """测试CookieCloud连接"""
        try:
            settings = await self._get_settings()
            if not settings or not settings.host or not settings.uuid or not settings.password:
                return False
            
            client = CookieCloudClient(settings.host, settings.uuid, settings.password)
            result = await client.get_cookies()
            await client.close()
            
            return result is not None
            
        except Exception as e:
            logger.error(f"测试CookieCloud连接失败: {e}")
            return False
