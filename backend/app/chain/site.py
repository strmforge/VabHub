"""
站点处理链
统一处理站点相关操作
"""

from typing import List, Optional, Dict, Any
from app.chain.base import ChainBase
from app.core.database import AsyncSessionLocal
from loguru import logger


class SiteChain(ChainBase):
    """站点处理链"""
    
    def __init__(self):
        super().__init__()
    
    def _get_service(self, session):
        """
        获取站点服务实例
        
        Args:
            session: 数据库会话
        
        Returns:
            SiteService 实例
        """
        from app.modules.site.service import SiteService
        return SiteService(session)
    
    # ========== 站点管理 ==========
    
    async def list_sites(
        self,
        active_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        列出站点
        
        Args:
            active_only: 是否只返回激活的站点
        
        Returns:
            站点列表
        """
        # 检查缓存
        cache_key = self._get_cache_key("list_sites", active_only)
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"从缓存获取站点列表: active_only={active_only}")
            return cached_result
        
        # 执行操作
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            sites = await service.list_sites(active_only=active_only)
            
            # 转换为字典
            result = [self._site_to_dict(site) for site in sites]
            
            # 缓存结果（2分钟）
            await self._set_to_cache(cache_key, result, ttl=120)
            
            return result
    
    async def get_site(self, site_id: int) -> Optional[Dict[str, Any]]:
        """
        获取站点详情
        
        Args:
            site_id: 站点ID
        
        Returns:
            站点详情
        """
        # 检查缓存
        cache_key = self._get_cache_key("get_site", site_id)
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"从缓存获取站点详情: site_id={site_id}")
            return cached_result
        
        # 执行操作
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            site = await service.get_site(site_id)
            
            if site:
                result = self._site_to_dict(site)
                # 缓存结果（2分钟）
                await self._set_to_cache(cache_key, result, ttl=120)
                return result
            
            return None
    
    async def create_site(self, site_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建站点
        
        Args:
            site_data: 站点数据
        
        Returns:
            创建的站点
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            site = await service.create_site(site_data)
            
            # 清除站点列表缓存
            await self._clear_site_cache()
            
            return self._site_to_dict(site)
    
    async def update_site(
        self,
        site_id: int,
        site_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        更新站点
        
        Args:
            site_id: 站点ID
            site_data: 站点数据
        
        Returns:
            更新后的站点
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            site = await service.update_site(site_id, site_data)
            
            if site:
                # 清除相关缓存
                await self._clear_site_cache(site_id)
                return self._site_to_dict(site)
            
            return None
    
    async def delete_site(self, site_id: int) -> bool:
        """
        删除站点
        
        Args:
            site_id: 站点ID
        
        Returns:
            是否成功
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            success = await service.delete_site(site_id)
            
            if success:
                # 清除相关缓存
                await self._clear_site_cache(site_id)
            
            return success
    
    # ========== 站点操作 ==========
    
    async def checkin(self, site_id: int) -> Dict[str, Any]:
        """
        执行站点签到
        
        Args:
            site_id: 站点ID
        
        Returns:
            签到结果
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            result = await service.checkin(site_id)
            
            # 清除站点详情缓存（因为签到后状态可能改变）
            await self._clear_site_cache(site_id)
            
            return result
    
    async def batch_checkin(self, site_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        批量签到
        
        Args:
            site_ids: 站点ID列表（如果为None，签到所有激活的站点）
        
        Returns:
            批量签到结果
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            result = await service.batch_checkin(site_ids)
            
            # 清除所有站点缓存
            await self._clear_site_cache()
            
            return result
    
    async def test_connection(self, site_id: int) -> Dict[str, Any]:
        """
        测试站点连接
        
        Args:
            site_id: 站点ID
        
        Returns:
            连接测试结果
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            result = await service.test_connection(site_id)
            
            return result
    
    async def sync_cookiecloud(
        self,
        site_id: int,
        server_url: str,
        uuid: str,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        同步CookieCloud
        
        Args:
            site_id: 站点ID
            server_url: CookieCloud服务器地址
            uuid: CookieCloud UUID
            password: CookieCloud密码
        
        Returns:
            同步结果
        """
        # 注意：这个方法可能需要在SiteService中实现
        # 暂时返回一个占位符响应
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            # 如果SiteService有sync_cookiecloud方法，则调用它
            if hasattr(service, 'sync_cookiecloud'):
                result = await service.sync_cookiecloud(site_id, server_url, uuid, password)
            else:
                # 如果没有该方法，返回错误
                result = {
                    "success": False,
                    "message": "CookieCloud同步功能尚未实现"
                }
            
            # 清除站点详情缓存
            await self._clear_site_cache(site_id)
            
            return result
    
    # ========== 辅助方法 ==========
    
    def _site_to_dict(self, site) -> Dict[str, Any]:
        """将站点对象转换为字典"""
        return {
            "id": site.id,
            "name": site.name,
            "url": site.url,
            "cookie": site.cookie,  # 注意：实际使用时可能需要隐藏敏感信息
            "cookiecloud_uuid": site.cookiecloud_uuid,
            "cookiecloud_server": site.cookiecloud_server,
            "is_active": site.is_active,
            "user_data": site.user_data,
            "last_checkin": site.last_checkin.isoformat() if site.last_checkin else None,
            "created_at": site.created_at.isoformat() if site.created_at else None,
            "updated_at": site.updated_at.isoformat() if site.updated_at else None,
        }
    
    async def _clear_site_cache(self, site_id: Optional[int] = None):
        """
        清除站点缓存
        
        Args:
            site_id: 站点ID（如果指定，只清除该站点的缓存；否则清除所有缓存）
        """
        if site_id:
            # 清除特定站点的缓存
            cache_key = self._get_cache_key("get_site", site_id)
            if cache_key in self._cache:
                del self._cache[cache_key]
        else:
            # 清除所有站点相关缓存
            keys_to_remove = [
                key for key in self._cache.keys()
                if "list_sites" in key or "get_site" in key
            ]
            for key in keys_to_remove:
                del self._cache[key]
        
        logger.debug(f"已清除站点缓存: site_id={site_id}")

