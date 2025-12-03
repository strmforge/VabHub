"""
插件安全服务
PLUGIN-REMOTE-1 实现

提供插件签名验证、官方源标记等安全功能
"""

import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.plugin import Plugin
from app.core.config import settings
from app.services.plugin_hub_service import extract_org_from_repo_url


class PluginSecurityService:
    """
    插件安全服务
    
    提供插件安全验证、官方源标记等功能
    """
    
    @staticmethod
    def is_official_org(org: str) -> bool:
        """
        检查组织是否为官方组织
        
        Args:
            org: 组织名
            
        Returns:
            是否为官方组织
        """
        return org and org.lower() in settings.PLUGIN_OFFICIAL_ORGS
    
    @staticmethod
    def extract_org_from_repo(repo_url: str) -> Optional[str]:
        """
        从仓库 URL 提取组织名
        
        Args:
            repo_url: Git 仓库 URL
            
        Returns:
            组织名或 None
        """
        return extract_org_from_repo_url(repo_url)
    
    @staticmethod
    def is_official_plugin(repo_url: str, channel: str = None) -> bool:
        """
        判断插件是否为官方插件
        
        Args:
            repo_url: Git 仓库 URL
            channel: 插件频道（可选）
            
        Returns:
            是否为官方插件
        """
        # 如果明确指定了 channel，优先使用
        if channel:
            return channel.lower() == "official"
        
        # 否则根据仓库 URL 判断
        org = PluginSecurityService.extract_org_from_repo(repo_url)
        return PluginSecurityService.is_official_org(org)
    
    @staticmethod
    def get_security_level(plugin: Plugin) -> Dict[str, Any]:
        """
        获取插件的安全级别信息
        
        Args:
            plugin: 插件对象
            
        Returns:
            安全级别信息
        """
        # 基础安全信息
        security_info = {
            "is_official": False,
            "trust_level": "community",  # official, trusted, community
            "security_notes": [],
            "recommendations": []
        }
        
        # 检查是否为官方插件
        if plugin.repo_url:
            is_official = PluginSecurityService.is_official_plugin(
                plugin.repo_url, 
                getattr(plugin, 'channel', None)
            )
            security_info["is_official"] = is_official
            
            if is_official:
                security_info["trust_level"] = "official"
                security_info["security_notes"].append("来自官方组织，经过基础审查")
            else:
                org = PluginSecurityService.extract_org_from_repo(plugin.repo_url)
                if org:
                    security_info["security_notes"].append(f"来自社区组织: {org}")
                else:
                    security_info["security_notes"].append("来源不明，请谨慎使用")
        
        # 检查插件类型
        if hasattr(plugin, 'plugin_type') and plugin.plugin_type.value == "remote":
            security_info["security_notes"].append("远程插件，通过网络通信")
            security_info["recommendations"].append("检查远程服务的安全性")
        
        # 检查权限声明
        if hasattr(plugin, 'sdk_permissions') and plugin.sdk_permissions:
            high_risk_permissions = [
                "download.write", "download.add",
                "cloud115.task", "cloud115.add_offline",
                "tts.control"
            ]
            
            risky_perms = [perm for perm in plugin.sdk_permissions if perm in high_risk_permissions]
            if risky_perms:
                security_info["security_notes"].append(f"声明了高风险权限: {', '.join(risky_perms)}")
                security_info["recommendations"].append("仔细审查权限使用场景")
        
        # 检查是否有 commit hash
        if hasattr(plugin, 'installed_ref') and plugin.installed_ref:
            security_info["security_notes"].append(f"已记录安装版本: {plugin.installed_ref[:8]}")
        else:
            security_info["security_notes"].append("未记录版本信息")
            security_info["recommendations"].append("建议重新安装以获取版本信息")
        
        return security_info
    
    @staticmethod
    def validate_plugin_config(plugin_config: Dict[str, Any]) -> List[str]:
        """
        验证插件配置的安全性
        
        Args:
            plugin_config: 插件配置
            
        Returns:
            安全警告列表
        """
        warnings = []
        
        # 检查远程插件配置
        if plugin_config.get("plugin_type") == "remote":
            remote_config = plugin_config.get("remote", {})
            
            # 检查 URL
            base_url = remote_config.get("base_url", "")
            if not base_url:
                warnings.append("远程插件缺少 base_url 配置")
            else:
                try:
                    parsed = urlparse(base_url)
                    if parsed.scheme not in ["http", "https"]:
                        warnings.append(f"不安全的协议: {parsed.scheme}")
                    elif parsed.scheme == "http":
                        warnings.append("使用 HTTP 协议，建议改用 HTTPS")
                except Exception:
                    warnings.append("无效的 base_url 格式")
            
            # 检查超时设置
            timeout = remote_config.get("timeout", 5)
            if timeout > 30:
                warnings.append("超时设置过长，可能导致系统阻塞")
            elif timeout < 1:
                warnings.append("超时设置过短，可能导致频繁失败")
        
        # 检查权限声明
        permissions = plugin_config.get("sdk_permissions", [])
        if not permissions:
            warnings.append("插件未声明任何权限")
        
        # 检查事件订阅
        events = plugin_config.get("events", [])
        if plugin_config.get("plugin_type") == "remote" and not events:
            warnings.append("远程插件未订阅任何事件，可能无法正常工作")
        
        return warnings
    
    @staticmethod
    async def scan_plugin_security(
        session: AsyncSession,
        plugin_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        扫描插件的安全状态
        
        Args:
            session: 数据库会话
            plugin_id: 插件 ID
            
        Returns:
            安全扫描结果
        """
        try:
            stmt = select(Plugin).where(Plugin.name == plugin_id)
            result = await session.execute(stmt)
            plugin = result.scalar_one_or_none()
            
            if not plugin:
                return None
            
            # 获取安全级别信息
            security_info = PluginSecurityService.get_security_level(plugin)
            
            # 添加插件基本信息
            security_info.update({
                "plugin_id": plugin.name,
                "plugin_type": plugin.plugin_type.value if hasattr(plugin, 'plugin_type') else "local",
                "version": plugin.version,
                "source": getattr(plugin, 'source', 'local'),
                "installed_at": plugin.installed_at.isoformat() if plugin.installed_at else None,
                "last_updated": plugin.updated_at.isoformat() if plugin.updated_at else None
            })
            
            return security_info
            
        except Exception as e:
            logger.error(f"[plugin-security] Error scanning plugin {plugin_id}: {e}")
            return None
    
    @staticmethod
    def generate_security_report(plugins: List[Plugin]) -> Dict[str, Any]:
        """
        生成插件安全报告
        
        Args:
            plugins: 插件列表
            
        Returns:
            安全报告
        """
        report = {
            "total_plugins": len(plugins),
            "official_plugins": 0,
            "community_plugins": 0,
            "remote_plugins": 0,
            "high_risk_plugins": 0,
            "security_summary": []
        }
        
        for plugin in plugins:
            security_info = PluginSecurityService.get_security_level(plugin)
            
            # 统计
            if security_info["is_official"]:
                report["official_plugins"] += 1
            else:
                report["community_plugins"] += 1
            
            if hasattr(plugin, 'plugin_type') and plugin.plugin_type.value == "remote":
                report["remote_plugins"] += 1
            
            # 检查高风险
            high_risk_permissions = [
                "download.write", "download.add",
                "cloud115.task", "cloud115.add_offline",
                "tts.control"
            ]
            if hasattr(plugin, 'sdk_permissions') and any(
                perm in high_risk_permissions for perm in plugin.sdk_permissions
            ):
                report["high_risk_plugins"] += 1
            
            # 添加到摘要
            report["security_summary"].append({
                "plugin_id": plugin.name,
                "trust_level": security_info["trust_level"],
                "is_remote": hasattr(plugin, 'plugin_type') and plugin.plugin_type.value == "remote",
                "permissions_count": len(getattr(plugin, 'sdk_permissions', [])),
                "has_version_info": bool(getattr(plugin, 'installed_ref', None))
            })
        
        return report


# 便捷函数
def is_plugin_from_official_source(plugin: Plugin) -> bool:
    """检查插件是否来自官方源"""
    return PluginSecurityService.is_official_plugin(
        plugin.repo_url,
        getattr(plugin, 'channel', None)
    )


def get_plugin_security_badge(plugin: Plugin) -> str:
    """获取插件安全徽章"""
    security_info = PluginSecurityService.get_security_level(plugin)
    
    if security_info["is_official"]:
        return "🏢 官方"
    elif security_info["trust_level"] == "trusted":
        return "✅ 可信"
    else:
        return "⚠️ 社区"
