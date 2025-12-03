"""
STRM定时任务服务
实现定期全量同步（补全历史文件，修复缺失文件）
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.scheduler import TaskScheduler
from app.modules.strm.config import STRMConfig
from app.modules.strm.file_operation_mode import STRMSyncConfig
from app.modules.strm.sync_manager import STRMSyncManager
from app.modules.strm.service import STRMService
from app.modules.settings.service import SettingsService


class STRMSchedulerService:
    """STRM定时任务服务"""
    
    def __init__(self):
        self.scheduler = TaskScheduler()
        self._initialized = False
    
    async def initialize(self):
        """初始化定时任务"""
        if self._initialized:
            return
        
        try:
            # 添加定期全量同步任务（每天检查一次，实际执行间隔由配置决定）
            from apscheduler.triggers.cron import CronTrigger
            self.scheduler.add_job(
                func=self._periodic_full_sync_task,
                trigger=CronTrigger(hour=2, minute=0),  # 每天凌晨2点检查
                id="strm_periodic_full_sync",
                name="STRM定期全量同步"
            )
            
            logger.info("STRM定时任务服务初始化完成")
            self._initialized = True
        except Exception as e:
            logger.error(f"STRM定时任务服务初始化失败: {e}")
    
    async def _periodic_full_sync_task(self):
        """
        定期全量同步任务
        
        工作流程：
        1. 检查是否启用定期全量同步
        2. 获取STRM配置
        3. 执行全量同步（使用本地缺失检查模式，降低风控风险）
        """
        try:
            # 创建数据库会话
            async with AsyncSessionLocal() as db:
                # 获取STRM配置
                settings_service = SettingsService(db)
                strm_settings = await settings_service.get_settings_by_category("strm")
                
                if not strm_settings:
                    logger.debug("STRM配置不存在，跳过定期全量同步")
                    return
                
                # 检查是否启用定期全量同步
                periodic_full_sync = strm_settings.get("strm_periodic_full_sync", True)
                if not periodic_full_sync:
                    logger.debug("定期全量同步未启用，跳过")
                    return
                
                # 获取配置
                periodic_full_sync_interval_days = strm_settings.get("strm_periodic_full_sync_interval_days", 7)
                cloud_media_library_path = strm_settings.get("strm_cloud_media_library_path", "/115/电影")
                strm_library_path = strm_settings.get("strm_media_library_path", "/media_library")
                
                # 检查是否到了执行时间（通过上次执行时间判断）
                last_sync_time = await self._get_last_periodic_full_sync_time(db)
                if last_sync_time:
                    days_since_last_sync = (datetime.now() - last_sync_time).days
                    if days_since_last_sync < periodic_full_sync_interval_days:
                        logger.debug(f"距离上次定期全量同步仅{days_since_last_sync}天，未达到间隔{periodic_full_sync_interval_days}天，跳过")
                        return
                
                logger.info(f"开始执行定期全量同步（间隔: {periodic_full_sync_interval_days}天，路径: {cloud_media_library_path}）")
                
                # 获取STRM配置对象
                config_dict = {}
                for key, value in strm_settings.items():
                    if key.startswith("strm_"):
                        config_key = key[5:]  # 移除 "strm_" 前缀
                        config_dict[config_key] = value
                    else:
                        config_dict[key] = value
                
                strm_config = STRMConfig(**config_dict)
                
                # 创建同步配置
                sync_config = STRMSyncConfig(
                    strm_library_path=strm_library_path,
                    auto_sync=False,  # 定期全量同步是独立任务
                    cloud_media_library_path=cloud_media_library_path,
                    periodic_full_sync_interval_days=periodic_full_sync_interval_days
                )
                
                # 获取115 API客户端
                strm_service = STRMService(db)
                api_client = await strm_service.get_115_api_client()
                
                if not api_client:
                    logger.warning("无法获取115网盘API客户端，跳过定期全量同步")
                    return
                
                # 创建同步管理器
                sync_manager = STRMSyncManager(
                    db=db,
                    sync_config=sync_config,
                    strm_config=strm_config,
                    cloud_storage='115',
                    cloud_115_api=api_client
                )
                
                # 执行全量同步（使用本地缺失检查模式，降低风控风险）
                result = await sync_manager.full_sync(
                    cloud_media_library_path=cloud_media_library_path,
                    check_local_missing_only=True  # 只检查本地缺失，不调用115 API
                )
                
                # 记录执行时间
                await self._save_last_periodic_full_sync_time(db)
                
                logger.info(f"定期全量同步完成: 新增{len(result.get('generated', []))}个文件，跳过{len(result.get('skipped', []))}个文件，失败{len(result.get('failed', []))}个文件")
                
        except Exception as e:
            logger.error(f"定期全量同步任务执行失败: {e}", exc_info=True)
    
    async def _get_last_periodic_full_sync_time(self, db: AsyncSession) -> Optional[datetime]:
        """获取上次定期全量同步时间"""
        try:
            settings_service = SettingsService(db)
            last_sync_time_str = await settings_service.get_setting("strm_last_periodic_full_sync_time", category="strm")
            if last_sync_time_str:
                return datetime.fromisoformat(last_sync_time_str)
            return None
        except Exception as e:
            logger.debug(f"获取上次定期全量同步时间失败: {e}")
            return None
    
    async def _save_last_periodic_full_sync_time(self, db: AsyncSession):
        """保存上次定期全量同步时间"""
        try:
            settings_service = SettingsService(db)
            await settings_service.set_setting(
                "strm_last_periodic_full_sync_time",
                datetime.now().isoformat(),
                category="strm"
            )
        except Exception as e:
            logger.error(f"保存上次定期全量同步时间失败: {e}")
    


# 全局单例
_strm_scheduler_service: Optional[STRMSchedulerService] = None


def get_strm_scheduler_service() -> STRMSchedulerService:
    """获取STRM定时任务服务单例"""
    global _strm_scheduler_service
    if _strm_scheduler_service is None:
        _strm_scheduler_service = STRMSchedulerService()
    return _strm_scheduler_service

