"""
备份系统服务
提供数据库备份和恢复功能
"""

import asyncio
import gzip
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, inspect, text, delete
from sqlalchemy.orm import class_mapper
from loguru import logger

from app.core.config import settings
from app.models.backup import BackupRecord
from app.models import (
    User, Media, MediaFile, Subscription, DownloadTask, UploadTask, UploadProgress,
    Workflow, WorkflowExecution, Site, Notification, MusicSubscription, MusicTrack,
    MusicPlaylist, MusicLibrary, SearchHistory, SystemSetting, HNRDetection, HNRTask,
    HNRSignature, CacheEntry, IdentificationHistory, CloudStorage, CloudStorageAuth,
    RSSSubscription, RSSItem, Subtitle, SubtitleDownloadHistory,
    MultimodalPerformanceMetric, MultimodalPerformanceAlert, MultimodalOptimizationHistory,
    MediaServer, MediaServerSyncHistory, MediaServerItem, MediaServerPlaybackSession,
    SchedulerTask, SchedulerTaskExecution, StorageDirectory, StorageUsageHistory,
    StorageAlert, STRMWorkflowTask, STRMFile, STRMFileTree, STRMLifeEvent, STRMConfig,
    Directory, DashboardLayout, DashboardWidget
)


@dataclass
class BackupConfig:
    """备份配置"""
    backup_dir: str = "./backups"
    max_backups: int = 10
    compression_enabled: bool = True
    encryption_enabled: bool = False
    encryption_key: Optional[str] = None
    auto_backup_enabled: bool = True
    auto_backup_interval_hours: int = 24
    verify_backup: bool = True
    # 要备份的表列表（如果为空，则备份所有表）
    tables_to_backup: Optional[List[str]] = None


class BackupService:
    """备份服务"""
    
    # 定义要备份的表和模型映射
    TABLE_MODEL_MAP = {
        "users": User,
        "media": Media,
        "media_files": MediaFile,
        "subscriptions": Subscription,
        "download_tasks": DownloadTask,
        "upload_tasks": UploadTask,
        "upload_progress": UploadProgress,
        "workflows": Workflow,
        "workflow_executions": WorkflowExecution,
        "sites": Site,
        "notifications": Notification,
        "music_subscriptions": MusicSubscription,
        "music_tracks": MusicTrack,
        "music_playlists": MusicPlaylist,
        "music_libraries": MusicLibrary,
        "search_history": SearchHistory,
        "system_settings": SystemSetting,
        "hnr_detections": HNRDetection,
        "hnr_tasks": HNRTask,
        "hnr_signatures": HNRSignature,
        "cache_entries": CacheEntry,
        "identification_history": IdentificationHistory,
        "cloud_storage": CloudStorage,
        "cloud_storage_auth": CloudStorageAuth,
        "rss_subscriptions": RSSSubscription,
        "rss_items": RSSItem,
        "subtitles": Subtitle,
        "subtitle_download_history": SubtitleDownloadHistory,
        "multimodal_performance_metrics": MultimodalPerformanceMetric,
        "multimodal_performance_alerts": MultimodalPerformanceAlert,
        "multimodal_optimization_history": MultimodalOptimizationHistory,
        "media_servers": MediaServer,
        "media_server_sync_history": MediaServerSyncHistory,
        "media_server_items": MediaServerItem,
        "media_server_playback_sessions": MediaServerPlaybackSession,
        "scheduler_tasks": SchedulerTask,
        "scheduler_task_executions": SchedulerTaskExecution,
        "storage_directories": StorageDirectory,
        "storage_usage_history": StorageUsageHistory,
        "storage_alerts": StorageAlert,
        "strm_workflow_tasks": STRMWorkflowTask,
        "strm_files": STRMFile,
        "strm_file_trees": STRMFileTree,
        "strm_life_events": STRMLifeEvent,
        "strm_configs": STRMConfig,
        "directories": Directory,
        "dashboard_layouts": DashboardLayout,
        "dashboard_widgets": DashboardWidget,
        "backup_records": BackupRecord,
    }
    
    def __init__(self, db: AsyncSession, config: Optional[BackupConfig] = None):
        self.db = db
        self.config = config or BackupConfig()
        self.backup_dir = Path(self.config.backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._is_running = False
    
    async def create_backup(self, backup_name: Optional[str] = None) -> Optional[BackupRecord]:
        """创建数据库备份"""
        if self._is_running:
            logger.warning("备份任务正在运行中")
            return None
        
        self._is_running = True
        backup_record = None
        
        try:
            # 生成备份ID和路径
            backup_id = backup_name or f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_filename = f"{backup_id}.json"
            if self.config.compression_enabled:
                backup_filename += ".gz"
            
            backup_path = self.backup_dir / backup_filename
            
            logger.info(f"开始创建备份: {backup_path}")
            
            # 收集备份数据
            backup_data = await self._collect_backup_data()
            
            # 写入备份文件
            await self._write_backup_file(backup_path, backup_data)
            
            # 计算文件大小和校验和
            file_size = backup_path.stat().st_size
            checksum = await self._calculate_checksum(backup_path)
            
            # 创建备份记录
            backup_record = BackupRecord(
                backup_id=backup_id,
                backup_path=str(backup_path),
                created_at=datetime.utcnow(),
                database_version=backup_data['metadata']['database_version'],
                file_size=file_size,
                checksum=checksum,
                compressed=self.config.compression_enabled,
                encrypted=self.config.encryption_enabled,
                tables_count=backup_data['metadata']['tables_count'],
                status="completed",
                metadata=backup_data['metadata']
            )
            
            # 保存备份记录到数据库
            self.db.add(backup_record)
            await self.db.commit()
            await self.db.refresh(backup_record)
            
            # 验证备份
            if self.config.verify_backup:
                if await self._verify_backup(backup_path, backup_data):
                    logger.info("备份验证成功")
                else:
                    logger.error("备份验证失败")
                    backup_record.status = "corrupted"
                    await self.db.commit()
            
            # 清理旧备份
            await self._cleanup_old_backups()
            
            logger.info(f"备份创建成功: {backup_path} ({file_size} 字节)")
            return backup_record
            
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            if backup_record:
                backup_record.status = "failed"
                backup_record.error_message = str(e)
                await self.db.commit()
            return None
        finally:
            self._is_running = False
    
    async def _collect_backup_data(self) -> Dict[str, Any]:
        """收集备份数据"""
        backup_data = {
            'metadata': {
                'backup_version': '1.0',
                'created_at': datetime.utcnow().isoformat(),
                'database_version': getattr(settings, 'APP_VERSION', '1.0.0'),
                'tables_count': {}
            },
            'tables': {}
        }
        
        # 确定要备份的表
        tables_to_backup = self.config.tables_to_backup or list(self.TABLE_MODEL_MAP.keys())
        
        # 备份每个表
        for table_name in tables_to_backup:
            if table_name not in self.TABLE_MODEL_MAP:
                logger.warning(f"表 {table_name} 不在备份列表中，跳过")
                continue
            
            model = self.TABLE_MODEL_MAP[table_name]
            
            try:
                logger.info(f"备份表: {table_name}")
                
                # 查询所有记录
                result = await self.db.execute(select(model))
                items = result.scalars().all()
                
                # 转换为字典格式
                table_data = []
                for item in items:
                    item_dict = self._model_to_dict(item)
                    table_data.append(item_dict)
                
                backup_data['tables'][table_name] = table_data
                backup_data['metadata']['tables_count'][table_name] = len(table_data)
                
                logger.info(f"已备份 {len(table_data)} 条记录 from {table_name}")
                
            except Exception as e:
                logger.error(f"备份表 {table_name} 失败: {e}")
                backup_data['tables'][table_name] = []
                backup_data['metadata']['tables_count'][table_name] = 0
        
        return backup_data
    
    def _model_to_dict(self, model_instance) -> Dict[str, Any]:
        """将模型实例转换为字典"""
        mapper = class_mapper(model_instance.__class__)
        result = {}
        
        for column in mapper.columns:
            value = getattr(model_instance, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif hasattr(value, '__dict__'):
                # 处理关系对象（简化处理，只保存ID）
                if hasattr(value, 'id'):
                    value = value.id
                else:
                    value = str(value)
            result[column.name] = value
        
        return result
    
    async def _write_backup_file(self, backup_path: Path, backup_data: Dict[str, Any]):
        """写入备份文件"""
        # 序列化数据
        json_data = json.dumps(backup_data, ensure_ascii=False, indent=2, default=str)
        
        if self.config.compression_enabled:
            # 压缩写入
            with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                f.write(json_data)
        else:
            # 直接写入
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(json_data)
        
        # 如果启用加密（这里只是占位，实际应该使用更安全的加密方法）
        if self.config.encryption_enabled and self.config.encryption_key:
            logger.warning("加密功能尚未实现")
    
    async def _calculate_checksum(self, file_path: Path) -> str:
        """计算文件校验和"""
        hash_md5 = hashlib.md5()
        
        # 始终使用二进制模式读取
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        
        return hash_md5.hexdigest()
    
    async def _verify_backup(self, backup_path: Path, original_data: Dict[str, Any]) -> bool:
        """验证备份文件"""
        try:
            # 读取备份文件
            restored_data = await self._read_backup_file(backup_path)
            
            # 比较关键字段
            if restored_data['metadata']['database_version'] != original_data['metadata']['database_version']:
                return False
            
            if restored_data['metadata']['tables_count'] != original_data['metadata']['tables_count']:
                return False
            
            # 抽样验证表数据
            for table_name in original_data['tables']:
                if table_name not in restored_data['tables']:
                    return False
                
                original_count = len(original_data['tables'][table_name])
                restored_count = len(restored_data['tables'][table_name])
                
                if original_count != restored_count:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"备份验证错误: {e}")
            return False
    
    async def _read_backup_file(self, backup_path: Path) -> Dict[str, Any]:
        """读取备份文件"""
        if backup_path.suffix == '.gz':
            # 解压缩读取
            with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 直接读取
            with open(backup_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    async def list_backups(self, limit: Optional[int] = None) -> List[BackupRecord]:
        """列出所有备份"""
        query = select(BackupRecord).order_by(BackupRecord.created_at.desc())
        if limit:
            query = query.limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_backup(self, backup_id: str) -> Optional[BackupRecord]:
        """获取指定备份"""
        result = await self.db.execute(
            select(BackupRecord).where(BackupRecord.backup_id == backup_id)
        )
        return result.scalar_one_or_none()
    
    async def delete_backup(self, backup_id: str) -> bool:
        """删除备份"""
        try:
            backup_record = await self.get_backup(backup_id)
            if not backup_record:
                logger.error(f"备份不存在: {backup_id}")
                return False
            
            # 删除备份文件
            backup_path = Path(backup_record.backup_path)
            if backup_path.exists():
                backup_path.unlink()
                logger.info(f"已删除备份文件: {backup_path}")
            
            # 删除数据库记录
            await self.db.execute(delete(BackupRecord).where(BackupRecord.id == backup_record.id))
            await self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"删除备份失败: {e}")
            await self.db.rollback()
            return False
    
    async def restore_backup(self, backup_id: str, confirm: bool = False) -> bool:
        """恢复备份"""
        if not confirm:
            logger.error("恢复操作需要明确确认")
            return False
        
        try:
            # 查找备份
            backup_record = await self.get_backup(backup_id)
            if not backup_record:
                logger.error(f"备份不存在: {backup_id}")
                return False
            
            backup_path = Path(backup_record.backup_path)
            if not backup_path.exists():
                logger.error(f"备份文件不存在: {backup_path}")
                return False
            
            logger.info(f"开始恢复备份: {backup_path}")
            
            # 验证备份文件
            current_checksum = await self._calculate_checksum(backup_path)
            if current_checksum != backup_record.checksum:
                logger.error("备份文件校验和不匹配 - 文件可能已损坏")
                return False
            
            # 读取备份数据
            backup_data = await self._read_backup_file(backup_path)
            
            # 执行恢复
            await self._restore_data(backup_data)
            
            logger.info("备份恢复成功")
            return True
            
        except Exception as e:
            logger.error(f"恢复备份失败: {e}")
            return False
    
    async def _restore_data(self, backup_data: Dict[str, Any]):
        """恢复数据到数据库"""
        logger.warning("开始数据库恢复 - 这将删除所有现有数据")
        
        # 按照依赖关系顺序清空表（从依赖表开始）
        reverse_order = list(reversed(self.TABLE_MODEL_MAP.keys()))
        
        for table_name in reverse_order:
            if table_name not in self.TABLE_MODEL_MAP:
                continue
            
            model = self.TABLE_MODEL_MAP[table_name]
            
            try:
                # 删除所有记录（使用delete语句）
                await self.db.execute(delete(model))
                logger.info(f"已清空表: {table_name}")
            except Exception as e:
                logger.warning(f"清空表 {table_name} 失败: {e}")
        
        await self.db.commit()
        logger.info("现有数据已清空")
        
        # 恢复数据（按照正常顺序）
        tables_data = backup_data.get('tables', {})
        
        for table_name in self.TABLE_MODEL_MAP.keys():
            if table_name not in tables_data:
                continue
            
            model = self.TABLE_MODEL_MAP[table_name]
            table_data = tables_data[table_name]
            
            try:
                logger.info(f"恢复表: {table_name} ({len(table_data)} 条记录)")
                
                for item_data in table_data:
                    # 转换日期字段
                    for key, value in item_data.items():
                        if isinstance(value, str) and 'T' in value and ('+' in value or value.endswith('Z')):
                            try:
                                item_data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            except:
                                pass
                    
                    # 创建模型实例
                    instance = model(**item_data)
                    self.db.add(instance)
                
                await self.db.commit()
                logger.info(f"已恢复 {len(table_data)} 条记录到 {table_name}")
                
            except Exception as e:
                logger.error(f"恢复表 {table_name} 失败: {e}")
                await self.db.rollback()
        
        logger.info("数据恢复完成")
    
    async def _cleanup_old_backups(self):
        """清理旧备份"""
        try:
            backups = await self.list_backups()
            
            if len(backups) <= self.config.max_backups:
                return
            
            # 按创建时间排序，保留最新的
            backups.sort(key=lambda x: x.created_at, reverse=True)
            old_backups = backups[self.config.max_backups:]
            
            for backup in old_backups:
                await self.delete_backup(backup.backup_id)
            
        except Exception as e:
            logger.error(f"清理旧备份失败: {e}")
    
    async def get_backup_status(self) -> Dict[str, Any]:
        """获取备份系统状态"""
        backups = await self.list_backups()
        
        total_size = sum(backup.file_size for backup in backups)
        successful_backups = len([b for b in backups if b.status == 'completed'])
        failed_backups = len([b for b in backups if b.status == 'failed'])
        
        latest_backup = backups[0] if backups else None
        
        return {
            'auto_backup_enabled': self.config.auto_backup_enabled,
            'backup_running': self._is_running,
            'total_backups': len(backups),
            'successful_backups': successful_backups,
            'failed_backups': failed_backups,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'latest_backup': {
                'backup_id': latest_backup.backup_id,
                'created_at': latest_backup.created_at.isoformat() if latest_backup else None,
                'status': latest_backup.status if latest_backup else None
            } if latest_backup else None,
            'backup_directory': str(self.backup_dir),
            'max_backups': self.config.max_backups
        }

