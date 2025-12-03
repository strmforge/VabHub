"""
默认订阅配置服务
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.settings import SystemSetting


class DefaultSubscriptionConfig(BaseModel):
    """默认订阅配置模型"""
    quality: str = Field(default="", description="质量要求")
    resolution: str = Field(default="", description="分辨率要求")
    effect: str = Field(default="", description="特效要求")
    min_seeders: int = Field(default=5, description="最小做种数")
    auto_download: bool = Field(default=True, description="自动下载")
    best_version: bool = Field(default=False, description="洗版")
    include: str = Field(default="", description="包含规则")
    exclude: str = Field(default="", description="排除规则")
    filter_group_ids: List[int] = Field(default_factory=list, description="过滤规则组ID列表")
    allow_hr: bool = Field(default=False, description="允许HR")
    allow_h3h5: bool = Field(default=False, description="允许H3/H5")
    strict_free_only: bool = Field(default=False, description="仅免费种")
    sites: List[int] = Field(default_factory=list, description="订阅站点")
    downloader: str = Field(default="", description="下载器")
    save_path: str = Field(default="", description="保存路径")


class DefaultSubscriptionConfigService:
    """默认订阅配置服务"""
    
    # 配置键常量
    CONFIG_KEYS = {
        "movie": "subscription.default.movie",
        "tv": "subscription.default.tv",
        "short_drama": "subscription.default.short_drama",
        "anime": "subscription.default.anime",
        "music": "subscription.default.music",
    }
    
    # 内置默认配置
    BUILTIN_DEFAULTS = {
        "movie": DefaultSubscriptionConfig(
            quality="1080p",
            resolution="",
            effect="",
            min_seeders=5,
            auto_download=True,
            best_version=False,
            include="",
            exclude="",
            filter_group_ids=[],
            allow_hr=False,
            allow_h3h5=False,
            strict_free_only=False,
            sites=[],
            downloader="",
            save_path=""
        ),
        "tv": DefaultSubscriptionConfig(
            quality="1080p",
            resolution="",
            effect="",
            min_seeders=5,
            auto_download=True,
            best_version=False,
            include="",
            exclude="",
            filter_group_ids=[],
            allow_hr=False,
            allow_h3h5=False,
            strict_free_only=False,
            sites=[],
            downloader="",
            save_path=""
        ),
        "short_drama": DefaultSubscriptionConfig(),
        "anime": DefaultSubscriptionConfig(),
        "music": DefaultSubscriptionConfig(),
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_default_config(self, media_type: str) -> DefaultSubscriptionConfig:
        """
        获取默认订阅配置
        
        Args:
            media_type: 媒体类型
            
        Returns:
            默认订阅配置对象
        """
        try:
            if media_type not in self.CONFIG_KEYS:
                raise ValueError(f"不支持的媒体类型: {media_type}")
            
            config_key = self.CONFIG_KEYS[media_type]
            
            # 从数据库获取配置
            query = select(SystemSetting).where(SystemSetting.key == config_key)
            result = await self.db.execute(query)
            setting = result.scalar_one_or_none()
            
            if setting and setting.value:
                try:
                    config_data = setting.value
                    if isinstance(config_data, str):
                        import json
                        config_data = json.loads(config_data)
                    
                    config = DefaultSubscriptionConfig(**config_data)
                    logger.info(f"从数据库加载默认配置: {media_type}")
                    return config
                    
                except Exception as e:
                    logger.warning(f"解析默认配置失败: {media_type}, {e}")
            
            # 返回内置默认配置
            config = self.BUILTIN_DEFAULTS[media_type]
            logger.info(f"使用内置默认配置: {media_type}")
            return config
            
        except Exception as e:
            logger.error(f"获取默认配置失败: {media_type}, {e}")
            # 发生错误时返回基础配置
            return DefaultSubscriptionConfig()
    
    async def save_default_config(
        self, 
        media_type: str, 
        config_data: dict
    ) -> DefaultSubscriptionConfig:
        """
        保存默认订阅配置
        
        Args:
            media_type: 媒体类型
            config_data: 配置数据
            
        Returns:
            保存后的配置对象
        """
        try:
            if media_type not in self.CONFIG_KEYS:
                raise ValueError(f"不支持的媒体类型: {media_type}")
            
            config_key = self.CONFIG_KEYS[media_type]
            
            # 验证配置数据
            config = DefaultSubscriptionConfig(**config_data)
            
            # 检查设置是否存在
            query = select(SystemSetting).where(SystemSetting.key == config_key)
            result = await self.db.execute(query)
            existing = result.scalar_one_or_none()
            
            # 序列化值
            import json
            value_str = json.dumps(config_data, ensure_ascii=False)
            
            if existing:
                # 更新现有设置
                existing.value = value_str
                existing.category = "subscription"
                existing.updated_at = datetime.utcnow()
                self.db.add(existing)
                await self.db.commit()
                await self.db.refresh(existing)
            else:
                # 创建新设置
                setting = SystemSetting(
                    key=config_key,
                    value=value_str,
                    category="subscription",
                    description=f"默认{media_type}订阅配置"
                )
                self.db.add(setting)
                await self.db.commit()
                await self.db.refresh(setting)
            
            logger.info(f"保存默认配置成功: {media_type}")
            return config
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"保存默认配置失败: {media_type}, {e}")
            raise
    
    async def reset_default_config(self, media_type: str) -> DefaultSubscriptionConfig:
        """
        重置默认订阅配置为内置值
        
        Args:
            media_type: 媒体类型
            
        Returns:
            重置后的配置对象
        """
        try:
            if media_type not in self.CONFIG_KEYS:
                raise ValueError(f"不支持的媒体类型: {media_type}")
            
            config_key = self.CONFIG_KEYS[media_type]
            
            # 删除数据库中的配置
            query = delete(SystemSetting).where(SystemSetting.key == config_key)
            await self.db.execute(query)
            await self.db.commit()
            
            # 返回内置默认配置
            config = self.BUILTIN_DEFAULTS[media_type]
            
            logger.info(f"重置默认配置成功: {media_type}")
            return config
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"重置默认配置失败: {media_type}, {e}")
            raise
    
    async def get_all_configs(self) -> Dict[str, DefaultSubscriptionConfig]:
        """
        获取所有媒体类型的默认配置
        
        Returns:
            所有配置的字典
        """
        try:
            configs = {}
            for media_type in self.CONFIG_KEYS.keys():
                configs[media_type] = await self.get_default_config(media_type)
            
            return configs
            
        except Exception as e:
            logger.error(f"获取所有默认配置失败: {e}")
            # 返回基础配置
            return {mt: DefaultSubscriptionConfig() for mt in self.CONFIG_KEYS.keys()}
    
    async def apply_default_to_subscription_data(
        self, 
        media_type: str, 
        subscription_data: dict
    ) -> dict:
        """
        将默认配置应用到订阅数据
        
        Args:
            media_type: 媒体类型
            subscription_data: 订阅数据
            
        Returns:
            应用默认配置后的订阅数据
        """
        try:
            default_config = await self.get_default_config(media_type)
            default_dict = default_config.model_dump(exclude_none=True)
            
            # 只应用空的字段
            for key, value in default_dict.items():
                if key not in subscription_data or subscription_data[key] is None or subscription_data[key] == "":
                    subscription_data[key] = value
            
            logger.debug(f"应用默认配置到订阅: {media_type}")
            return subscription_data
            
        except Exception as e:
            logger.error(f"应用默认配置失败: {media_type}, {e}")
            return subscription_data
    
    def get_supported_media_types(self) -> List[str]:
        """
        获取支持的媒体类型列表
        
        Returns:
            媒体类型列表
        """
        return list(self.CONFIG_KEYS.keys())
    
    def validate_media_type(self, media_type: str) -> bool:
        """
        验证媒体类型是否支持
        
        Args:
            media_type: 媒体类型
            
        Returns:
            是否支持
        """
        return media_type in self.CONFIG_KEYS
