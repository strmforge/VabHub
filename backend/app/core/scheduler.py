"""
定时任务调度系统
支持自动执行订阅搜索、更新下载状态、清理过期缓存等
"""

import asyncio
from typing import Dict, Optional, Callable, Any, List
from datetime import datetime, timedelta
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_SUBMITTED

from app.core.database import AsyncSessionLocal
from app.core.cache import get_cache
from app.core.config import settings


class TaskScheduler:
    """定时任务调度器"""
    
    def __init__(self):
        """初始化调度器"""
        # 创建异步调度器
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        job_defaults = {
            'coalesce': True,  # 合并多个待执行的任务
            'max_instances': 3,  # 最大并发实例数
            'misfire_grace_time': 60  # 任务错过执行时间的宽限时间（秒）
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Asia/Shanghai'
        )
        
        # 添加事件监听器
        self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_SUBMITTED)
        
        # 执行开始时间记录
        self._job_start_times: Dict[str, datetime] = {}
        
        self._initialized = False
    
    def _job_listener(self, event):
        """任务执行监听器"""
        if event.code == EVENT_JOB_SUBMITTED:
            # 记录任务提交时间（任务开始执行）
            self._job_start_times[event.job_id] = datetime.utcnow()
            logger.debug(f"任务开始执行: {event.job_id}")
        elif event.code == EVENT_JOB_EXECUTED:
            # 任务执行成功
            started_at = self._job_start_times.pop(event.job_id, datetime.utcnow())
            self._record_execution(event.job_id, "completed", started_at, datetime.utcnow())
            logger.debug(f"任务执行成功: {event.job_id}")
        elif event.code == EVENT_JOB_ERROR:
            # 任务执行失败
            started_at = self._job_start_times.pop(event.job_id, datetime.utcnow())
            self._record_execution(
                event.job_id,
                "failed",
                started_at,
                datetime.utcnow(),
                error_message=str(event.exception),
                error_traceback=str(event.traceback) if hasattr(event, "traceback") else None
            )
            logger.error(f"任务执行失败: {event.job_id} - {event.exception}")
    
    def _record_execution(
        self,
        job_id: str,
        status: str,
        started_at: datetime,
        completed_at: datetime,
        error_message: Optional[str] = None,
        error_traceback: Optional[str] = None
    ):
        """记录任务执行（同步方式，实际记录在后台异步执行）"""
        # 使用后台任务记录，避免阻塞
        # 注意：APScheduler的事件监听器在同步上下文中运行，不能直接使用async
        # 我们使用后台线程来处理异步数据库操作
        import threading
        try:
            # 在后台线程中运行异步操作
            def run_async():
                try:
                    # 创建新的事件循环
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(self._record_execution_async(
                            job_id, status, started_at, completed_at, error_message, error_traceback
                        ))
                    finally:
                        loop.close()
                except Exception as e:
                    logger.error(f"后台记录任务执行失败: {e}")
            
            # 启动后台线程
            thread = threading.Thread(target=run_async, daemon=True)
            thread.start()
        except Exception as e:
            logger.error(f"创建记录任务失败: {e}")
    
    async def _record_execution_async(
        self,
        job_id: str,
        status: str,
        started_at: datetime,
        completed_at: datetime,
        error_message: Optional[str] = None,
        error_traceback: Optional[str] = None
    ):
        """异步记录任务执行"""
        try:
            from app.modules.scheduler.monitor import SchedulerMonitor
            from app.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as session:
                monitor = SchedulerMonitor(session)
                
                await monitor.record_execution(
                    job_id=job_id,
                    status=status,
                    started_at=started_at,
                    completed_at=completed_at,
                    result={"success": status == "completed"} if status == "completed" else None,
                    error_message=error_message,
                    error_traceback=error_traceback
                )
        except Exception as e:
            logger.error(f"记录任务执行历史失败: {e}")
    
    async def start(self):
        """启动调度器"""
        if not self._initialized:
            self._register_default_jobs()
            self._initialized = True
        
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("定时任务调度器已启动")
    
    async def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("定时任务调度器已停止")
    
    def _register_default_jobs(self):
        """注册默认任务"""
        # 1. 自动执行订阅搜索（每小时）
        self.add_job(
            func=self._auto_search_subscriptions,
            trigger=IntervalTrigger(hours=1),
            id="auto_search_subscriptions",
            name="自动执行订阅搜索",
            replace_existing=True
        )
        
        # 2. 更新下载状态（每30秒）
        self.add_job(
            func=self._update_download_status,
            trigger=IntervalTrigger(seconds=30),
            id="update_download_status",
            name="更新下载状态",
            replace_existing=True
        )
        
        # 3. 清理过期缓存（每天凌晨2点）
        self.add_job(
            func=self._cleanup_expired_cache,
            trigger=CronTrigger(hour=2, minute=0),
            id="cleanup_expired_cache",
            name="清理过期缓存",
            replace_existing=True
        )
        
        # 4. 站点自动签到（每天凌晨3点）
        self.add_job(
            func=self._auto_checkin_sites,
            trigger=CronTrigger(hour=3, minute=0),
            id="auto_checkin_sites",
            name="站点自动签到",
            replace_existing=True
        )
        
        # 5. 更新HNR监控任务（每5分钟）
        self.add_job(
            func=self._update_hnr_tasks,
            trigger=IntervalTrigger(minutes=5),
            id="update_hnr_tasks",
            name="更新HNR监控任务",
            replace_existing=True
        )
        
        # 6. RSS订阅自动检查（每30分钟）
        self.add_job(
            func=self._check_rss_subscriptions,
            trigger=IntervalTrigger(minutes=30),
            id="check_rss_subscriptions",
            name="RSS订阅自动检查",
            replace_existing=True
        )
        
        # 7. 存储使用历史记录（每小时）
        self.add_job(
            func=self._record_storage_usage,
            trigger=IntervalTrigger(hours=1),
            id="record_storage_usage",
            name="记录存储使用历史",
            replace_existing=True
        )
        
        # 8. 清理旧的存储使用历史（每天凌晨2点）
        self.add_job(
            func=self._cleanup_old_storage_history,
            trigger=CronTrigger(hour=2, minute=0),
            id="cleanup_old_storage_history",
            name="清理旧的存储使用历史",
            replace_existing=True
        )
        
        # 9. 清理旧的上传进度记录（每天凌晨3点）
        self.add_job(
            func=self._cleanup_old_upload_progress,
            trigger=CronTrigger(hour=3, minute=0),
            id="cleanup_old_upload_progress",
            name="清理旧的上传进度记录",
            replace_existing=True
        )
        
        # 10. 漫画收藏追更（每2小时）
        self.add_job(
            func=self._sync_favorite_manga,
            trigger=IntervalTrigger(hours=2),
            id="sync_favorite_manga",
            name="漫画收藏自动追更",
            replace_existing=True
        )
        
        # 11. Local Intel HR 页面监控（每6小时）
        from app.core.config import settings
        if settings.INTEL_ENABLED and settings.INTEL_HR_GUARD_ENABLED:
            self.add_job(
                func=self._watch_hr_pages,
                trigger=IntervalTrigger(hours=6),
                id="watch_hr_pages",
                name="LocalIntel HR 页面监控",
                replace_existing=True
            )
        
        # 12. Local Intel 站内信监控（每30分钟）
        if settings.INTEL_ENABLED:
            self.add_job(
                func=self._watch_inbox_messages,
                trigger=IntervalTrigger(minutes=30),
                id="watch_inbox_messages",
                name="LocalIntel 站内信监控",
                replace_existing=True
            )
        
        # 13. 清理孤立的上传进度记录（每天凌晨3点30分）
        self.add_job(
            func=self._cleanup_orphaned_upload_progress,
            trigger=CronTrigger(hour=3, minute=30),
            id="cleanup_orphaned_upload_progress",
            name="清理孤立的上传进度记录",
            replace_existing=True
        )
        
        # 14. 自动备份（可配置间隔，默认每天一次）
        if settings.AUTO_BACKUP_ENABLED:
            from app.modules.backup.tasks import auto_backup_task
            self.add_job(
                func=auto_backup_task,
                trigger=IntervalTrigger(hours=settings.AUTO_BACKUP_INTERVAL_HOURS),
                id="auto_backup",
                name="自动备份",
                replace_existing=True
            )
        
        # 15. RSSHub订阅处理（每30分钟）
        self.add_job(
            func=self._process_rsshub_subscriptions,
            trigger=IntervalTrigger(minutes=30),
            id="process_rsshub_subscriptions",
            name="RSSHub订阅处理",
            replace_existing=True
        )
        
        # 16. CookieCloud自动同步（如果已配置）
        self._register_cookiecloud_jobs()
        
        logger.info("默认定时任务已注册")
    
    def add_job(
        self,
        func: Callable,
        trigger,
        id: str,
        name: str,
        replace_existing: bool = True,
        **kwargs
    ):
        """添加定时任务"""
        try:
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=id,
                name=name,
                replace_existing=replace_existing,
                **kwargs
            )
            logger.info(f"定时任务已添加: {name} (ID: {id})")
        except Exception as e:
            logger.error(f"添加定时任务失败: {name} - {e}")
    
    def remove_job(self, job_id: str):
        """移除定时任务"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"定时任务已移除: {job_id}")
        except Exception as e:
            logger.error(f"移除定时任务失败: {job_id} - {e}")
    
    def get_jobs(self) -> List[Dict]:
        """获取所有任务"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        return jobs
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """获取任务详情"""
        job = self.scheduler.get_job(job_id)
        if not job:
            return None
        
        return {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        }
    
    async def _auto_search_subscriptions(self):
        """自动执行订阅搜索（使用增量刷新引擎）"""
        logger.info("开始自动执行订阅搜索（增量刷新）...")
        try:
            from app.modules.subscription.refresh_engine import SubscriptionRefreshEngine
            
            async with AsyncSessionLocal() as session:
                refresh_engine = SubscriptionRefreshEngine(session)
                
                # 使用刷新引擎批量刷新订阅（每次最多刷新50个）
                result = await refresh_engine.refresh_subscriptions_batch(max_count=50)
                
                if result.get("success"):
                    logger.info(
                        f"订阅刷新完成: 总计 {result.get('total_count', 0)} 个订阅, "
                        f"成功 {result.get('refreshed_count', 0)} 个, "
                        f"失败 {result.get('error_count', 0)} 个"
                    )
                else:
                    logger.error(f"订阅刷新失败: {result.get('error')}")
                
                logger.info("订阅搜索执行完成")
        except Exception as e:
            logger.error(f"自动执行订阅搜索失败: {e}")
    
    async def _update_download_status(self):
        """更新下载状态"""
        logger.debug("开始更新下载状态...")
        try:
            from app.modules.download.status_updater import DownloadStatusUpdater
            
            async with AsyncSessionLocal() as session:
                updater = DownloadStatusUpdater(session)
                await updater.update_all_downloads()
        except Exception as e:
            logger.error(f"更新下载状态失败: {e}")
    
    async def _cleanup_expired_cache(self):
        """清理过期缓存"""
        logger.info("开始清理过期缓存...")
        try:
            cache = get_cache()
            cleaned_count = await cache.cleanup_expired()
            logger.info(f"清理了 {cleaned_count} 个过期缓存")
        except Exception as e:
            logger.error(f"清理过期缓存失败: {e}")
    
    async def _auto_checkin_sites(self):
        """站点自动签到"""
        logger.info("开始站点自动签到...")
        try:
            from app.modules.site.service import SiteService
            
            async with AsyncSessionLocal() as session:
                site_service = SiteService(session)
                
                # 获取所有启用的站点
                sites = await site_service.list_sites(active=True)
                
                logger.info(f"找到 {len(sites)} 个启用的站点")
                
                for site in sites:
                    try:
                        # 执行签到
                        result = await site_service.checkin(site.id)
                        if result.get("success"):
                            if result.get("already_checked"):
                                logger.info(f"站点签到: {site.name} - 今日已签到")
                            else:
                                logger.info(f"站点签到成功: {site.name}")
                        else:
                            logger.warning(f"站点签到失败: {site.name} - {result.get('message')}")
                    except Exception as e:
                        logger.error(f"站点签到失败: {site.name} - {e}")
                
                logger.info("站点自动签到完成")
        except Exception as e:
            logger.error(f"站点自动签到失败: {e}")
    
    async def _update_hnr_tasks(self):
        """更新HNR监控任务"""
        logger.debug("开始更新HNR监控任务...")
        try:
            from app.modules.hnr.service import HNRService
            from app.models.download import DownloadTask
            from app.core.downloaders import DownloaderClient, DownloaderType
            from app.modules.settings.service import SettingsService
            from sqlalchemy import select
            from datetime import datetime, timedelta
            
            async with AsyncSessionLocal() as session:
                hnr_service = HNRService(session)
                settings_service = SettingsService(session)
                
                # 获取所有监控中的任务
                tasks = await hnr_service.list_tasks(status="monitoring")
                
                logger.debug(f"找到 {len(tasks)} 个HNR监控任务")
                
                for task in tasks:
                    try:
                        # 获取关联的下载任务
                        download_task_result = await session.execute(
                            select(DownloadTask).where(DownloadTask.id == task.download_task_id)
                        )
                        download_task = download_task_result.scalar_one_or_none()
                        
                        if not download_task:
                            logger.warning(f"HNR任务 {task.title} 的下载任务不存在")
                            continue
                        
                        if not download_task.downloader_hash:
                            logger.debug(f"HNR任务 {task.title} 的下载任务还没有hash，跳过")
                            continue
                        
                        # 从下载器获取实际指标
                        try:
                            # 获取下载器配置
                            config_prefix = f"{download_task.downloader.lower()}_"
                            host = await settings_service.get_setting(f"{config_prefix}host") or "localhost"
                            port = await settings_service.get_setting(f"{config_prefix}port") or (8080 if download_task.downloader == "qBittorrent" else 9091)
                            username = await settings_service.get_setting(f"{config_prefix}username") or ""
                            password = await settings_service.get_setting(f"{config_prefix}password") or ""
                            
                            downloader_config = {
                                "host": host,
                                "port": int(port) if isinstance(port, str) else port,
                                "username": username,
                                "password": password
                            }
                            
                            # 创建下载器客户端
                            downloader_type = DownloaderType.QBITTORRENT if download_task.downloader == "qBittorrent" else DownloaderType.TRANSMISSION
                            client = DownloaderClient(downloader_type, downloader_config)
                            
                            # 获取任务信息
                            torrent_info = await client.get_torrent_info(download_task.downloader_hash)
                            await client.close()
                            
                            if not torrent_info:
                                logger.warning(f"无法从下载器获取任务信息: {task.title}")
                                continue
                            
                            # 解析指标
                            if downloader_type == DownloaderType.QBITTORRENT:
                                # qBittorrent指标
                                uploaded = torrent_info.get("uploaded", 0) / (1024 ** 3)  # GB
                                downloaded = torrent_info.get("downloaded", 0) / (1024 ** 3)  # GB
                                ratio = torrent_info.get("ratio", 0.0)
                                
                                # 计算做种时间（从added_on到现在）
                                # qBittorrent的added_on是Unix时间戳（秒）
                                added_timestamp = torrent_info.get("added_on", 0)
                                if added_timestamp:
                                    try:
                                        added_datetime = datetime.fromtimestamp(added_timestamp)
                                        # 计算时间差（小时）
                                        time_diff = datetime.utcnow() - added_datetime
                                        seed_time_hours = time_diff.total_seconds() / 3600
                                    except (ValueError, TypeError, OSError):
                                        seed_time_hours = 0.0
                                else:
                                    seed_time_hours = 0.0
                            else:
                                # Transmission指标
                                uploaded = torrent_info.get("uploadedEver", 0) / (1024 ** 3)  # GB
                                downloaded = torrent_info.get("downloadedEver", 0) / (1024 ** 3)  # GB
                                ratio = torrent_info.get("uploadRatio", 0.0)
                                
                                # 计算做种时间（从addedDate到现在）
                                # Transmission的addedDate是Unix时间戳（秒）
                                added_timestamp = torrent_info.get("addedDate", 0)
                                if added_timestamp:
                                    try:
                                        added_datetime = datetime.fromtimestamp(added_timestamp)
                                        # 计算时间差（小时）
                                        time_diff = datetime.utcnow() - added_datetime
                                        seed_time_hours = time_diff.total_seconds() / 3600
                                    except (ValueError, TypeError, OSError):
                                        seed_time_hours = 0.0
                                else:
                                    seed_time_hours = 0.0
                            
                            # 更新HNR任务指标
                            await hnr_service.update_task_metrics(
                                task_id=task.id,
                                current_ratio=ratio,
                                seed_time_hours=seed_time_hours,
                                downloaded_gb=downloaded,
                                uploaded_gb=uploaded
                            )
                            
                            logger.debug(f"HNR任务指标已更新: {task.title} - 分享率: {ratio:.2f}, 做种时间: {seed_time_hours:.2f}小时")
                            
                            # 检查是否满足要求，如果满足则标记为完成
                            if ratio >= task.required_ratio and seed_time_hours >= task.required_seed_time_hours:
                                if task.status == "monitoring":
                                    task.status = "completed"
                                    task.completed_at = datetime.utcnow()
                                    session.add(task)
                                    await session.commit()
                                    logger.info(f"HNR任务已完成: {task.title}")
                        
                        except Exception as e:
                            logger.error(f"从下载器获取HNR任务指标失败: {task.title} - {e}")
                    
                    except Exception as e:
                        logger.error(f"更新HNR任务失败: {task.title} - {e}")
        except Exception as e:
            logger.error(f"更新HNR监控任务失败: {e}")
    
    async def _record_storage_usage(self):
        """记录存储使用历史"""
        logger.info("开始记录存储使用历史...")
        try:
            from app.modules.storage_monitor.tasks import record_storage_usage_task
            await record_storage_usage_task()
        except Exception as e:
            logger.error(f"记录存储使用历史失败: {e}")
    
    async def _cleanup_old_storage_history(self):
        """清理旧的存储使用历史"""
        logger.info("开始清理旧的存储使用历史...")
        try:
            from app.modules.storage_monitor.tasks import cleanup_old_usage_history_task
            await cleanup_old_usage_history_task(days=30)
        except Exception as e:
            logger.error(f"清理旧的存储使用历史失败: {e}")
    
    async def _check_rss_subscriptions(self):
        """RSS订阅自动检查"""
        logger.info("开始RSS订阅自动检查...")
        try:
            from app.modules.rss.service import RSSSubscriptionService
            from datetime import datetime
            
            async with AsyncSessionLocal() as session:
                rss_service = RSSSubscriptionService(session)
                
                # 获取所有启用的RSS订阅
                subscriptions = await rss_service.list_rss_subscriptions(enabled=True)
                
                logger.info(f"找到 {len(subscriptions)} 个启用的RSS订阅")
                
                for subscription in subscriptions:
                    try:
                        # 检查是否需要检查（基于next_check时间）
                        if subscription.next_check and subscription.next_check > datetime.utcnow():
                            logger.debug(f"RSS订阅 {subscription.name} 还未到检查时间，跳过")
                            continue
                        
                        # 检查RSS更新
                        result = await rss_service.check_rss_updates(subscription.id)
                        if result.get("success"):
                            logger.info(
                                f"RSS订阅检查成功: {subscription.name} - "
                                f"新项: {result.get('new_items', 0)}, "
                                f"处理: {result.get('processed_items', 0)}, "
                                f"下载: {result.get('downloaded_items', 0)}, "
                                f"跳过: {result.get('skipped_items', 0)}"
                            )
                        else:
                            logger.warning(f"RSS订阅检查失败: {subscription.name} - {result.get('error')}")
                    except Exception as e:
                        logger.error(f"检查RSS订阅失败: {subscription.name} - {e}")
                
                logger.info("RSS订阅自动检查完成")
        except Exception as e:
            logger.error(f"RSS订阅自动检查失败: {e}")
    
    async def _cleanup_old_upload_progress(self):
        """清理旧的上传进度记录"""
        logger.info("开始清理旧的上传进度记录...")
        try:
            from app.modules.upload.cleanup import cleanup_old_progress_records
            
            result = await cleanup_old_progress_records(
                days=30,
                keep_completed=True,
                keep_failed=False
            )
            
            if result.get("success"):
                logger.info(f"清理旧的上传进度记录完成: 删除了 {result.get('deleted_count', 0)} 条记录")
            else:
                logger.error(f"清理旧的上传进度记录失败: {result.get('error')}")
        except Exception as e:
            logger.error(f"清理旧的上传进度记录异常: {e}")
    
    async def _cleanup_orphaned_upload_progress(self):
        """清理孤立的上传进度记录"""
        logger.info("开始清理孤立的上传进度记录...")
        try:
            from app.modules.upload.cleanup import cleanup_orphaned_progress_records
            
            result = await cleanup_orphaned_progress_records()
            
            if result.get("success"):
                logger.info(f"清理孤立的上传进度记录完成: 删除了 {result.get('deleted_count', 0)} 条记录（{result.get('orphaned_task_count', 0)} 个孤立任务）")
            else:
                logger.error(f"清理孤立的上传进度记录失败: {result.get('error')}")
        except Exception as e:
            logger.error(f"清理孤立的上传进度记录异常: {e}")
    
    async def _process_rsshub_subscriptions(self):
        """处理RSSHub订阅"""
        logger.info("开始处理RSSHub订阅...")
        if not settings.RSSHUB_ENABLED:
            logger.info("RSSHub 功能已禁用，跳过订阅处理任务")
            return
        try:
            from app.modules.rsshub.scheduler import RSSHubScheduler
            from app.models.user import User
            from sqlalchemy import select
            
            async with AsyncSessionLocal() as session:
                scheduler = RSSHubScheduler(session)
                
                # 获取所有用户
                result = await session.execute(select(User))
                users = result.scalars().all()
                
                logger.info(f"找到 {len(users)} 个用户，开始处理RSSHub订阅")
                
                total_stats = {
                    "processed": 0,
                    "new_items": 0,
                    "errors": 0
                }
                
                for user in users:
                    try:
                        stats = await scheduler.process_user_subscriptions(user.id)
                        total_stats["processed"] += stats["processed"]
                        total_stats["new_items"] += stats["new_items"]
                        total_stats["errors"] += stats["errors"]
                    except Exception as e:
                        logger.error(f"处理用户 {user.id} 的RSSHub订阅失败: {e}")
                        total_stats["errors"] += 1
                
                logger.info(
                    f"RSSHub订阅处理完成: "
                    f"处理了 {total_stats['processed']} 个订阅, "
                    f"发现 {total_stats['new_items']} 个新项, "
                    f"错误 {total_stats['errors']} 个"
                )
        except Exception as e:
            logger.error(f"处理RSSHub订阅失败: {e}")
    
    async def _watch_hr_pages(self):
        """LocalIntel HR 页面监控任务"""
        if not settings.INTEL_ENABLED or not settings.INTEL_HR_GUARD_ENABLED:
            logger.debug("LocalIntel HR Guard 未启用，跳过 HR 页面监控")
            return
        
        try:
            from app.core.intel_local.hr_watcher import get_hr_watcher
            
            watcher = get_hr_watcher()
            result = await watcher.handle_all_sites()
            
            if result.get("success"):
                logger.info(
                    f"LocalIntel HR 页面监控完成: "
                    f"处理了 {result.get('processed', 0)} 个站点, "
                    f"成功 {result.get('success_count', 0)} 个"
                )
            else:
                logger.warning(f"LocalIntel HR 页面监控失败: {result.get('reason')}")
        except NotImplementedError:
            logger.warning("LocalIntel HR Watcher 尚未接入站点 HTTP 客户端，跳过本轮")
        except Exception as e:
            logger.error(f"LocalIntel HR 页面监控任务异常: {e}", exc_info=True)
    
    async def _watch_inbox_messages(self):
        """LocalIntel 站内信监控任务"""
        if not settings.INTEL_ENABLED:
            logger.debug("LocalIntel 未启用，跳过站内信监控")
            return
        
        try:
            from app.core.intel_local.inbox_watcher import get_inbox_watcher
            
            watcher = get_inbox_watcher()
            result = await watcher.handle_all_sites()
            
            if result.get("success"):
                logger.info(
                    f"LocalIntel 站内信监控完成: "
                    f"处理了 {result.get('processed', 0)} 个站点, "
                    f"成功 {result.get('success_count', 0)} 个"
                )
            else:
                logger.warning(f"LocalIntel 站内信监控失败: {result.get('reason')}")
        except NotImplementedError:
            logger.warning("LocalIntel Inbox Watcher 尚未接入站点 HTTP 客户端，跳过本轮")
        except Exception as e:
            logger.error(f"LocalIntel 站内信监控任务异常: {e}", exc_info=True)
    
    async def _sync_favorite_manga(self):
        """漫画收藏追更任务"""
        logger.info("开始漫画收藏自动追更...")
        try:
            from app.services.manga_sync_service import sync_all_favorite_series
            
            async with AsyncSessionLocal() as session:
                result = await sync_all_favorite_series(session=session)
                
                if result.get("success"):
                    logger.info(
                        f"漫画收藏追更完成: "
                        f"处理了 {result.get('processed_series', 0)} 个系列, "
                        f"发现 {result.get('total_new_chapters', 0)} 个新章节"
                    )
                else:
                    logger.error(f"漫画收藏追更失败: {result.get('error')}")
        except Exception as e:
            logger.error(f"漫画收藏追更任务异常: {e}", exc_info=True)
    
    def add_cookiecloud_sync_job(self, user_id: int, interval_minutes: int):
        """添加CookieCloud同步任务"""
        job_id = f"cookiecloud_sync_{user_id}"
        try:
            self.add_job(
                func=self._cookiecloud_sync_task,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id=job_id,
                name=f"CookieCloud自动同步 (用户{user_id})",
                replace_existing=True,
                kwargs={'user_id': user_id}
            )
            logger.info(f"CookieCloud同步任务已添加: 用户{user_id}, 间隔{interval_minutes}分钟")
        except Exception as e:
            logger.error(f"添加CookieCloud同步任务失败: 用户{user_id} - {e}")
    
    def remove_cookiecloud_sync_job(self, user_id: int):
        """移除CookieCloud同步任务"""
        job_id = f"cookiecloud_sync_{user_id}"
        try:
            self.remove_job(job_id)
            logger.info(f"CookieCloud同步任务已移除: 用户{user_id}")
        except Exception as e:
            logger.error(f"移除CookieCloud同步任务失败: 用户{user_id} - {e}")
    
    def update_cookiecloud_sync_job(self, user_id: int, interval_minutes: int):
        """更新CookieCloud同步任务"""
        if interval_minutes > 0:
            self.add_cookiecloud_sync_job(user_id, interval_minutes)
        else:
            self.remove_cookiecloud_sync_job(user_id)
    
    async def _cookiecloud_sync_task(self, user_id: int):
        """CookieCloud同步任务执行函数"""
        logger.info(f"开始执行CookieCloud同步任务: 用户{user_id}")
        try:
            async with AsyncSessionLocal() as session:
                from app.modules.cookiecloud.service import CookieCloudSyncService
                from app.models.cookiecloud import CookieCloudSettings
                from sqlalchemy import select
                
                # 获取CookieCloud设置
                result = await session.execute(select(CookieCloudSettings))
                settings = result.scalar_one_or_none()
                
                # 检查设置是否存在且已启用
                if not settings or not settings.enabled:
                    logger.info(f"CookieCloud未启用或配置不存在，跳过同步任务: 用户{user_id}")
                    return
                
                # 检查配置完整性
                if not settings.host or not settings.uuid or not settings.password:
                    logger.warning(f"CookieCloud配置不完整，跳过同步任务: 用户{user_id}")
                    return
                
                # 执行同步
                sync_service = CookieCloudSyncService(session)
                sync_result = await sync_service.sync_all_sites(
                    batch_size=10,
                    site_timeout=30
                )
                
                if sync_result.success:
                    logger.info(
                        f"CookieCloud同步任务完成: 用户{user_id} - "
                        f"总站点: {sync_result.total_sites}, "
                        f"成功: {sync_result.synced_sites}, "
                        f"无匹配: {sync_result.unmatched_sites}, "
                        f"错误: {sync_result.error_sites}"
                    )
                else:
                    logger.warning(f"CookieCloud同步任务部分失败: 用户{user_id} - 错误数: {sync_result.error_sites}")
                    if sync_result.errors:
                        for error in sync_result.errors[:3]:  # 只记录前3个错误
                            logger.warning(f"同步错误: {error}")
        
        except Exception as e:
            logger.error(f"CookieCloud同步任务执行失败: 用户{user_id} - {e}", exc_info=True)
    
    def _register_cookiecloud_jobs(self):
        """注册CookieCloud定时任务（启动时检查现有设置）"""
        try:
            import asyncio
            # 在同步上下文中运行异步操作
            asyncio.run(self._register_cookiecloud_jobs_async())
        except Exception as e:
            logger.error(f"自动注册CookieCloud定时任务失败: {e}")
    
    async def _register_cookiecloud_jobs_async(self):
        """异步注册CookieCloud定时任务"""
        try:
            async with AsyncSessionLocal() as session:
                from app.models.cookiecloud import CookieCloudSettings
                from sqlalchemy import select
                
                # 获取CookieCloud设置
                result = await session.execute(select(CookieCloudSettings))
                settings = result.scalar_one_or_none()
                
                # 如果设置存在且已启用且有同步间隔，则注册任务
                if settings and settings.enabled and settings.sync_interval_minutes:
                    if settings.host and settings.uuid and settings.password:
                        # 使用默认用户ID（简化实现，实际应该从用户表获取）
                        user_id = 1
                        self.add_cookiecloud_sync_job(user_id, settings.sync_interval_minutes)
                        logger.info(f"CookieCloud定时任务已自动注册: 用户{user_id}, 间隔{settings.sync_interval_minutes}分钟")
                    else:
                        logger.info("CookieCloud配置不完整，跳过自动注册定时任务")
                else:
                    logger.debug("CookieCloud未启用或配置不存在，跳过自动注册定时任务")
        
        except Exception as e:
            logger.error(f"异步注册CookieCloud定时任务失败: {e}")


# 全局调度器实例
_scheduler: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """获取调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler

