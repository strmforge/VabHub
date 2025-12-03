"""
插件令牌服务
PLUGIN-REMOTE-1 实现

为远程插件生成和管理访问令牌
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from loguru import logger

from app.models.plugin import Plugin, PluginType
from app.plugin_sdk.types import PluginCapability


class PluginTokenService:
    """
    插件令牌服务
    
    负责为远程插件生成、验证和管理访问令牌
    """
    
    TOKEN_PREFIX = "vab_plugin_"
    TOKEN_LENGTH = 32  # 不包括前缀的总长度
    
    @staticmethod
    def generate_token() -> str:
        """
        生成新的插件令牌
        
        Returns:
            格式：vab_plugin_<32位随机字符串>
        """
        random_part = secrets.token_urlsafe(PluginTokenService.TOKEN_LENGTH)
        return f"{PluginTokenService.TOKEN_PREFIX}{random_part}"
    
    @staticmethod
    def is_valid_token_format(token: str) -> bool:
        """
        验证令牌格式
        
        Args:
            token: 待验证的令牌
            
        Returns:
            是否为有效格式
        """
        if not token:
            return False
        
        return token.startswith(PluginTokenService.TOKEN_PREFIX) and len(token) == len(PluginTokenService.TOKEN_PREFIX) + PluginTokenService.TOKEN_LENGTH
    
    @staticmethod
    async def generate_token_for_plugin(
        session: AsyncSession,
        plugin_id: str
    ) -> Optional[str]:
        """
        为指定插件生成新的访问令牌
        
        Args:
            session: 数据库会话
            plugin_id: 插件 ID
            
        Returns:
            生成的令牌，失败返回 None
        """
        try:
            # 查找插件
            stmt = select(Plugin).where(Plugin.name == plugin_id)
            result = await session.execute(stmt)
            plugin = result.scalar_one_or_none()
            
            if not plugin:
                logger.error(f"[plugin-token] Plugin not found: {plugin_id}")
                return None
            
            if plugin.plugin_type != PluginType.REMOTE:
                logger.warning(f"[plugin-token] Plugin {plugin_id} is not a remote plugin")
                return None
            
            # 生成新令牌
            new_token = PluginTokenService.generate_token()
            
            # 更新插件记录
            plugin.plugin_token = new_token
            await session.commit()
            
            logger.info(f"[plugin-token] Generated token for remote plugin: {plugin_id}")
            return new_token
            
        except Exception as e:
            await session.rollback()
            logger.error(f"[plugin-token] Error generating token for {plugin_id}: {e}")
            return None
    
    @staticmethod
    async def find_plugin_by_token(
        session: AsyncSession,
        token: str
    ) -> Optional[Plugin]:
        """
        通过令牌查找插件
        
        Args:
            session: 数据库会话
            token: 插件令牌
            
        Returns:
            插件对象，未找到返回 None
        """
        if not PluginTokenService.is_valid_token_format(token):
            return None
        
        try:
            stmt = select(Plugin).where(
                Plugin.plugin_token == token,
                Plugin.plugin_type == PluginType.REMOTE
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"[plugin-token] Error finding plugin by token: {e}")
            return None
    
    @staticmethod
    async def revoke_token(
        session: AsyncSession,
        plugin_id: str
    ) -> bool:
        """
        撤销插件的访问令牌
        
        Args:
            session: 数据库会话
            plugin_id: 插件 ID
            
        Returns:
            是否成功撤销
        """
        try:
            stmt = (
                update(Plugin)
                .where(Plugin.name == plugin_id)
                .values(plugin_token=None)
            )
            result = await session.execute(stmt)
            await session.commit()
            
            success = result.rowcount > 0
            if success:
                logger.info(f"[plugin-token] Token revoked for plugin: {plugin_id}")
            else:
                logger.warning(f"[plugin-token] Plugin not found for token revocation: {plugin_id}")
            
            return success
            
        except Exception as e:
            await session.rollback()
            logger.error(f"[plugin-token] Error revoking token for {plugin_id}: {e}")
            return False
    
    @staticmethod
    async def rotate_token(
        session: AsyncSession,
        plugin_id: str
    ) -> Optional[str]:
        """
        轮换插件令牌（生成新令牌替换旧令牌）
        
        Args:
            session: 数据库会话
            plugin_id: 插件 ID
            
        Returns:
            新令牌，失败返回 None
        """
        logger.info(f"[plugin-token] Rotating token for plugin: {plugin_id}")
        return await PluginTokenService.generate_token_for_plugin(session, plugin_id)


class PluginPermissionMapper:
    """
    插件权限映射器
    
    将插件的 sdk_permissions 映射为具体的 API 权限
    """
    
    # 权限映射表：sdk_permissions -> API 权限
    PERMISSION_MAPPING = {
        PluginCapability.DOWNLOAD_READ: ["api:download:read"],
        PluginCapability.DOWNLOAD_ADD: ["api:download:create"],
        PluginCapability.CLOUD115_READ: ["api:cloud115:read"],
        PluginCapability.CLOUD115_ADD_OFFLINE: ["api:cloud115:create"],
        PluginCapability.MEDIA_READ: ["api:media:read"],
        PluginCapability.TTS_CONTROL: ["api:tts:control"],
    }
    
    @staticmethod
    def map_permissions(sdk_permissions: List[str]) -> List[str]:
        """
        将 SDK 权限映射为 API 权限
        
        Args:
            sdk_permissions: 插件声明的 SDK 权限列表
            
        Returns:
            API 权限列表
        """
        api_permissions = []
        
        for permission in sdk_permissions:
            try:
                capability = PluginCapability(permission)
                mapped = PluginPermissionMapper.PERMISSION_MAPPING.get(capability, [])
                api_permissions.extend(mapped)
            except ValueError:
                logger.warning(f"[plugin-permission] Unknown SDK permission: {permission}")
        
        # 去重
        return list(set(api_permissions))
    
    @staticmethod
    async def check_plugin_permission(
        session: AsyncSession,
        token: str,
        required_permission: str
    ) -> bool:
        """
        检查插件是否具有指定权限
        
        Args:
            session: 数据库会话
            token: 插件令牌
            required_permission: 需要的 API 权限
            
        Returns:
            是否具有权限
        """
        # 通过令牌查找插件
        plugin = await PluginTokenService.find_plugin_by_token(session, token)
        if not plugin:
            return False
        
        # 映射 SDK 权限到 API 权限
        api_permissions = PluginPermissionMapper.map_permissions(plugin.sdk_permissions)
        
        # 检查权限
        has_permission = required_permission in api_permissions
        
        logger.debug(f"[plugin-permission] Plugin {plugin.name} permission check: {required_permission} -> {has_permission}")
        
        return has_permission


# 便捷函数
async def create_remote_plugin_token(session: AsyncSession, plugin_id: str) -> Optional[str]:
    """为远程插件创建访问令牌"""
    return await PluginTokenService.generate_token_for_plugin(session, plugin_id)


async def validate_plugin_token(session: AsyncSession, token: str) -> Optional[Plugin]:
    """验证插件令牌并返回插件对象"""
    return await PluginTokenService.find_plugin_by_token(session, token)


async def check_plugin_api_permission(
    session: AsyncSession,
    token: str,
    permission: str
) -> bool:
    """检查插件 API 权限"""
    return await PluginPermissionMapper.check_plugin_permission(session, token, permission)
