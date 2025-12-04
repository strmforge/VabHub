"""
CookieCloud同步服务
"""

import json
from typing import List, Dict, Optional, Set
from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import Session
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
        self._cached_settings: Optional[CookieCloudSettings] = self._prefetch_settings_from_session()

    def _prefetch_settings_from_session(self) -> Optional[CookieCloudSettings]:
        """尝试同步方式获取已存在的配置"""
        # 优先使用identity_map
        try:
            cached = next(
                (
                    obj for obj in self.db.identity_map.values()
                    if isinstance(obj, CookieCloudSettings)
                ),
                None
            )
            if cached:
                return cached
        except Exception:
            pass
        # 回退到同步会话查询最新记录（测试环境）
        try:
            sync_session: Optional[Session] = getattr(self.db, "sync_session", None)
            if sync_session is not None:
                stmt = select(CookieCloudSettings).order_by(CookieCloudSettings.id.desc()).limit(1)
                result = sync_session.execute(stmt)
                return result.scalar_one_or_none()
        except Exception:
            logger.debug("同步加载CookieCloud设置失败", exc_info=True)
        return None

    def _ensure_cached_settings(self) -> Optional[CookieCloudSettings]:
        if self._cached_settings is None:
            self._cached_settings = self._prefetch_settings_from_session()
        return self._cached_settings
    
    async def _get_settings(self) -> Optional[CookieCloudSettings]:
        """获取CookieCloud全局配置"""
        try:
            result = await self.db.execute(
                select(CookieCloudSettings).order_by(CookieCloudSettings.id.desc()).limit(1)
            )
            settings = result.scalar_one_or_none()
            self._cached_settings = settings
            return settings
        except Exception as e:
            logger.error(f"获取CookieCloud配置失败: {e}")
            return None
    
    async def _update_settings_status(self, status: str, error: Optional[str] = None):
        """更新配置状态"""
        await self._update_sync_status(status=status, error=error)
    
    async def _update_sync_status(self, status: str, error: Optional[str] = None, sync_at: Optional[datetime] = None):
        """更新同步状态（测试期望的接口）"""
        try:
            update_data = {
                "last_sync_at": sync_at or datetime.utcnow(),
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
            logger.error(f"更新CookieCloud同步状态失败: {e}")
    
    def _extract_domain_cookies(self, cookie_data: Dict, domain: str) -> str:
        """从CookieCloud数据中提取指定域名的Cookie字符串"""
        try:
            if not isinstance(cookie_data, dict):
                return ""

            cookies_source = cookie_data.get("cookie_data") if "cookie_data" in cookie_data else cookie_data
            if not isinstance(cookies_source, dict):
                return ""

            matched_cookies: List[str] = []

            def append_from_entry(entry):
                if not entry:
                    return
                if isinstance(entry, dict):
                    if "cookie_data" in entry:
                        append_from_entry(entry["cookie_data"])
                    else:
                        name = entry.get("name")
                        value = entry.get("value")
                        if name and value:
                            matched_cookies.append(f"{name}={value}")
                elif isinstance(entry, list):
                    formatted = self._format_cookie_string(entry)
                    if formatted:
                        matched_cookies.append(formatted)
                elif isinstance(entry, str):
                    matched_cookies.append(entry)

            if domain in cookies_source:
                append_from_entry(cookies_source[domain])
            else:
                for cookie_domain, entry in cookies_source.items():
                    if self._is_domain_match(cookie_domain, domain):
                        append_from_entry(entry)

            return "; ".join(filter(None, matched_cookies))

        except Exception as e:
            logger.error(f"提取域名Cookie失败 {domain}: {e}")
            return ""
    
    def _format_cookie_string(self, cookies: List[Dict[str, str]]) -> str:
        """将Cookie列表格式化为标准字符串"""
        if not cookies:
            return ""
        parts: List[str] = []
        for cookie in cookies:
            if not isinstance(cookie, dict):
                continue
            name = cookie.get("name")
            value = cookie.get("value")
            if name and value:
                parts.append(f"{name}={value}")
        return "; ".join(parts)

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

    def _extract_domain_from_url(self, url: str) -> str:
        """从URL中提取域名"""
        if url is None:
            raise AttributeError("URL is None")
        if not url:
            return ""
        try:
            url = url.strip()
            parsed = urlparse(url if "://" in url else f"http://{url}")
            if parsed.scheme not in ("http", "https"):
                return ""
            domain = parsed.netloc
            if not domain:
                return ""
            if ":" in domain:
                domain = domain.split(":", 1)[0]
            if "." not in domain:
                return ""
            return domain.lower()
        except Exception:
            return ""

    def _is_domain_in_whitelist(self, domain: str) -> bool:
        """检查域名是否在安全白名单中"""
        if not domain:
            return False
        settings = self._ensure_cached_settings()
        if settings is None:
            return False
        whitelist_raw = settings.safe_host_whitelist or "[]"
        try:
            whitelist = json.loads(whitelist_raw)
        except Exception:
            whitelist = []
        if not whitelist:
            return False
        domain = domain.lower()
        for pattern in whitelist:
            pattern = pattern.lower()
            if pattern.startswith("*."):
                suffix = pattern[1:]
                if domain.endswith(suffix) and domain != suffix.lstrip('.'): 
                    return True
            elif pattern == domain:
                return True
        return False

    def _resolve_site_domain(self, site: Site) -> str:
        domain = site.domain or self._extract_domain_from_url(site.url or "")
        if domain and domain != site.domain:
            try:
                site.domain = domain
            except Exception:
                pass
        return domain
    
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
            domain = self._resolve_site_domain(site)
            if not domain:
                return {
                    'success': False,
                    'cookie_updated': False,
                    'error': "无法解析站点域名"
                }
            if not self._is_domain_in_whitelist(domain):
                return {
                    'success': False,
                    'cookie_updated': False,
                    'error': f"域名 {domain} 不在安全白名单中"
                }
            # 提取Cookie
            cookie_string = self._extract_domain_cookies(cookie_data, domain)
            
            if cookie_string:
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
            return {
                'success': False,
                'cookie_updated': False,
                'error': "未找到Cookie数据"
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
                    errors=["未配置CookieCloud设置"]
                )
            
            if not settings.enabled:
                return CookieCloudSyncResult(
                    success=False,
                    total_sites=0,
                    synced_sites=0,
                    unmatched_sites=0,
                    error_sites=0,
                    errors=["CookieCloud已禁用"]
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
            
            # 2. 获取所有启用的站点
            result = await self.db.execute(
                select(Site).where(Site.is_active == True)
            )
            sites = result.scalars().all()
            
            # 3. 构建需要同步的站点列表（仅限CookieCloud源且已启用）
            filtered_sites: List[Site] = [
                site for site in sites
                if site.cookie_source == CookieSource.COOKIECLOUD
            ]
            logger.info(f"过滤后需要同步的CookieCloud站点数量: {len(filtered_sites)}")
            
            if not filtered_sites:
                return CookieCloudSyncResult(
                    success=True,
                    total_sites=0,
                    synced_sites=0,
                    unmatched_sites=0,
                    error_sites=0,
                    errors=[],
                    sync_time=start_time
                )
            
            # 4. 遍历站点逐个同步
            synced_count = 0
            unmatched_count = 0
            error_count = 0
            errors = []
            
            logger.info(f"开始同步 {len(filtered_sites)} 个CookieCloud站点")
            
            for site in filtered_sites:
                client = CookieCloudClient(settings.host, settings.uuid, settings.password)
                try:
                    cookie_data = await self._get_cookies_with_retry(client, max_retries=3)
                    if cookie_data is None:
                        error_count += 1
                        errors.append(f"站点 {site.name} 无法从CookieCloud获取数据")
                        continue
                    single_result = await self._sync_single_site(site, cookie_data)
                    if single_result['success'] and single_result['cookie_updated']:
                        synced_count += 1
                    elif single_result['success'] and not single_result['cookie_updated']:
                        unmatched_count += 1
                    else:
                        error_count += 1
                        errors.append(
                            f"站点 {site.name} 同步失败: {single_result['error'] or '未知错误'}"
                        )
                except Exception as e:
                    error_count += 1
                    errors.append(f"站点 {site.name} 同步异常: {e}")
                finally:
                    try:
                        await client.close()
                    except Exception:
                        pass
            
            # 5. 提交更改
            await self.db.commit()
            
            # 6. 更新配置状态
            status = "SUCCESS" if error_count == 0 else "PARTIAL"
            await self._update_settings_status(status)
            
            total_sites = len(filtered_sites)

            return CookieCloudSyncResult(
                success=error_count == 0,
                total_sites=total_sites,
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
            if not settings:
                return CookieCloudSiteSyncResult(
                    site_id=site_id,
                    site_name="Unknown",
                    success=False,
                    cookie_updated=False,
                    error_message="未配置CookieCloud设置"
                )
            if not settings.enabled:
                return CookieCloudSiteSyncResult(
                    site_id=site_id,
                    site_name="Unknown",
                    success=False,
                    cookie_updated=False,
                    error_message="CookieCloud已禁用"
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
            if site.cookie_source != CookieSource.COOKIECLOUD:
                return CookieCloudSiteSyncResult(
                    site_id=site_id,
                    site_name=site.name,
                    success=False,
                    cookie_updated=False,
                    error_message=f"站点 {site.name} 不是CookieCloud源"
                )
            
            # 3. 检查域名白名单
            safe_domains: Set[str] = set()
            domain = self._resolve_site_domain(site)
            if settings.safe_host_whitelist:
                try:
                    safe_domains = set(json.loads(settings.safe_host_whitelist or "[]"))
                    if safe_domains and (not domain or domain not in safe_domains):
                        return CookieCloudSiteSyncResult(
                            site_id=site_id,
                            site_name=site.name,
                            success=False,
                            cookie_updated=False,
                            error_message=f"域名 {domain or '未知'} 不在安全域名白名单中"
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
            cookie_string = self._extract_domain_cookies(cookie_data, domain)
            
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

            await client.close()
            duration = (datetime.utcnow() - start_time).total_seconds()
            return CookieCloudSiteSyncResult(
                site_id=site_id,
                site_name=site.name,
                success=False,
                cookie_updated=False,
                error_message="未找到Cookie数据",
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
