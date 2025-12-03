"""
系统设置服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Dict, Optional, List, Any
from datetime import datetime
from loguru import logger
import json

from app.models.settings import SystemSetting


class SettingsService:
    """系统设置服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_setting(self, key: str, default: Optional[Any] = None, category: Optional[str] = None) -> Optional[Any]:
        """
        获取单个设置
        
        Args:
            key: 设置键
            default: 默认值（如果设置不存在）
            category: 设置分类（可选，用于过滤）
            
        Returns:
            设置值或默认值
        """
        query = select(SystemSetting).where(SystemSetting.key == key)
        if category:
            query = query.where(SystemSetting.category == category)
        
        result = await self.db.execute(query)
        setting = result.scalar_one_or_none()
        if not setting:
            return default
        
        # 解析JSON值
        try:
            if setting.value:
                return json.loads(setting.value)
            return default
        except json.JSONDecodeError:
            # 如果不是JSON，直接返回字符串
            return setting.value if setting.value else default
    
    async def get_settings_by_category(self, category: str) -> Dict[str, Any]:
        """获取指定分类的所有设置"""
        result = await self.db.execute(
            select(SystemSetting).where(SystemSetting.category == category)
        )
        settings = result.scalars().all()
        
        result_dict = {}
        for setting in settings:
            try:
                if setting.value:
                    result_dict[setting.key] = json.loads(setting.value)
                else:
                    result_dict[setting.key] = None
            except json.JSONDecodeError:
                result_dict[setting.key] = setting.value
        
        return result_dict
    
    async def get_all_settings(self) -> Dict[str, Any]:
        """获取所有设置"""
        result = await self.db.execute(select(SystemSetting))
        settings = result.scalars().all()
        
        result_dict = {}
        for setting in settings:
            try:
                if setting.value:
                    result_dict[setting.key] = json.loads(setting.value)
                else:
                    result_dict[setting.key] = None
            except json.JSONDecodeError:
                result_dict[setting.key] = setting.value
        
        return result_dict
    
    async def set_setting(
        self,
        key: str,
        value: Any,
        category: str = "basic",
        description: Optional[str] = None,
        is_encrypted: bool = False
    ) -> SystemSetting:
        """设置单个配置项"""
        # 检查设置是否存在
        result = await self.db.execute(
            select(SystemSetting).where(SystemSetting.key == key)
        )
        existing = result.scalar_one_or_none()
        
        # 序列化值
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, ensure_ascii=False)
        else:
            value_str = str(value) if value is not None else None
        
        if existing:
            # 更新现有设置
            existing.value = value_str
            existing.category = category
            if description:
                existing.description = description
            existing.is_encrypted = is_encrypted
            existing.updated_at = datetime.utcnow()
            self.db.add(existing)
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            # 创建新设置
            new_setting = SystemSetting(
                key=key,
                value=value_str,
                category=category,
                description=description,
                is_encrypted=is_encrypted
            )
            self.db.add(new_setting)
            await self.db.commit()
            await self.db.refresh(new_setting)
            return new_setting
    
    async def set_settings(self, settings: Dict[str, Any], category: str = "basic") -> int:
        """批量设置配置项"""
        count = 0
        for key, value in settings.items():
            await self.set_setting(key, value, category)
            count += 1
        return count
    
    async def delete_setting(self, key: str) -> bool:
        """删除设置"""
        result = await self.db.execute(
            select(SystemSetting).where(SystemSetting.key == key)
        )
        setting = result.scalar_one_or_none()
        if not setting:
            return False
        
        await self.db.delete(setting)
        await self.db.commit()
        return True
    
    async def get_default_settings(self) -> Dict[str, Any]:
        """获取默认设置"""
        return {
            # 基础设置
            "system_name": "VabHub",
            "language": "zh-CN",
            "theme": "auto",
            "timezone": "Asia/Shanghai",
            
            # 下载器设置
            "default_downloader": "qBittorrent",
            "qbittorrent_host": "localhost",
            "qbittorrent_port": 8080,
            "qbittorrent_username": "",
            "qbittorrent_password": "",
            "transmission_host": "localhost",
            "transmission_port": 9091,
            "transmission_username": "",
            "transmission_password": "",
            "default_save_path": "",
            
            # 通知设置
            "notification_enabled": True,
            "notification_channels": ["system"],
            "email_smtp_host": "",
            "email_smtp_port": 587,
            "email_smtp_user": "",
            "email_smtp_password": "",
            "email_to": "",
            "telegram_bot_token": "",
            "telegram_chat_id": "",
            "wechat_webhook_url": "",
            
            # TMDB设置
            "tmdb_api_key": "",
            "tmdb_language": "zh-CN",
            
            # 高级设置
            "auto_download": True,
            "auto_search_interval": 3600,  # 秒
            "max_concurrent_downloads": 3,
            "enable_hdr": False,
            "enable_hnr_detection": False,
        }
    
    async def initialize_default_settings(self) -> int:
        """初始化默认设置"""
        default_settings = await self.get_default_settings()
        count = 0
        
        for key, value in default_settings.items():
            # 检查设置是否已存在
            existing = await self.get_setting(key)
            if existing is None:
                # 确定分类
                if key.startswith("qbittorrent") or key.startswith("transmission") or key in ["default_downloader", "default_save_path"]:
                    category = "downloader"
                elif key.startswith("notification") or key.startswith("email") or key.startswith("telegram") or key.startswith("wechat"):
                    category = "notification"
                elif key.startswith("tmdb"):
                    category = "tmdb"
                elif key in ["auto_download", "auto_search_interval", "max_concurrent_downloads", "enable_hdr", "enable_hnr_detection"]:
                    category = "advanced"
                elif key.startswith("subtitle_"):
                    category = "subtitle"
                else:
                    category = "basic"
                
                # 确定是否为加密字段
                is_encrypted = key.endswith("_password") or key.endswith("_token") or key.endswith("_key")
                
                await self.set_setting(key, value, category, is_encrypted=is_encrypted)
                count += 1
        
        return count

