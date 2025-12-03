"""
上传任务管理器
实现任务队列、状态跟踪、重试机制、并发控制等功能
"""

import asyncio
import time
from typing import Dict, Optional, Any, List, Callable
from datetime import datetime
from uuid import UUID
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.upload import UploadTask, UploadProgress, UploadTaskStatus
from app.core.cloud_storage.providers.cloud_115_api import Cloud115API
from app.core.cloud_storage.providers.cloud_115_upload import Cloud115UploadManager
from app.core.cloud_storage.providers.cloud_115_oss_resume import Cloud115OSSResume
from app.modules.upload.verification import verify_upload_complete


class UploadTaskManager:
    """上传任务管理器"""
    
    def __init__(
        self,
        api_client: Cloud115API,
        max_concurrent: int = 3,
        max_retries: int = 3,
        retry_delay: float = 5.0
    ):
        """
        初始化上传任务管理器
        
        Args:
            api_client: 115网盘API客户端
            max_concurrent: 最大并发上传数
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.api = api_client
        self.upload_manager = Cloud115UploadManager(api_client)
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 任务队列
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.running_tasks: Dict[UUID, asyncio.Task] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # 工作协程
        self.worker_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def start(self):
        """启动任务管理器"""
        if self.is_running:
            logger.warning("上传任务管理器已在运行")
            return
        
        self.is_running = True
        self.worker_task = asyncio.create_task(self._worker())
        logger.info(f"上传任务管理器已启动，最大并发数: {self.max_concurrent}")
    
    async def stop(self):
        """停止任务管理器"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 等待所有任务完成
        if self.running_tasks:
            logger.info(f"等待 {len(self.running_tasks)} 个上传任务完成...")
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        
        # 取消工作协程
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("上传任务管理器已停止")
    
    async def add_task(
        self,
        file_path: str,
        target_parent_id: str = "0",
        file_name: Optional[str] = None,
        speed_limit: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> UUID:
        """
        添加上传任务
        
        Args:
            file_path: 本地文件路径
            target_parent_id: 目标目录ID
            file_name: 文件名（可选）
            speed_limit: 速度限制（字节/秒，可选）
            user_id: 用户ID（可选）
        
        Returns:
            任务ID
        """
        import os
        from pathlib import Path
        
        # 验证文件
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        file_size = file_path_obj.stat().st_size
        file_name = file_name or file_path_obj.name
        
        # 创建任务记录
        async for db in get_db():
            task = UploadTask(
                user_id=user_id,
                file_path=str(file_path),
                file_name=file_name,
                file_size=file_size,
                target_parent_id=target_parent_id,
                status=UploadTaskStatus.PENDING.value,
                total_bytes=file_size,
                max_retries=self.max_retries,
                speed_limit=speed_limit
            )
            db.add(task)
            await db.commit()
            await db.refresh(task)
            task_id = task.id
            
            logger.info(f"添加上传任务: {task_id}, 文件: {file_name}, 大小: {file_size} 字节")
            
            # 添加到队列
            await self.task_queue.put(task_id)
            
            return task_id
    
    async def get_task(self, task_id: UUID) -> Optional[Dict[str, Any]]:
        """
        获取任务信息
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务信息字典
        """
        async for db in get_db():
            result = await db.execute(
                select(UploadTask).where(UploadTask.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if task:
                return task.to_dict()
            return None
    
    async def list_tasks(
        self,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        列出任务
        
        Args:
            status: 状态过滤（可选）
            user_id: 用户ID过滤（可选）
            limit: 限制数量
            offset: 偏移量
        
        Returns:
            任务列表
        """
        async for db in get_db():
            query = select(UploadTask)
            
            conditions = []
            if status:
                conditions.append(UploadTask.status == status)
            if user_id:
                conditions.append(UploadTask.user_id == user_id)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.order_by(UploadTask.created_at.desc()).limit(limit).offset(offset)
            
            result = await db.execute(query)
            tasks = result.scalars().all()
            
            return [task.to_dict() for task in tasks]
    
    async def cancel_task(self, task_id: UUID) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否成功
        """
        async for db in get_db():
            # 更新任务状态
            await db.execute(
                update(UploadTask)
                .where(UploadTask.id == task_id)
                .values(
                    status=UploadTaskStatus.CANCELLED.value,
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
            
            # 取消运行中的任务
            if task_id in self.running_tasks:
                task = self.running_tasks[task_id]
                task.cancel()
                del self.running_tasks[task_id]
            
            logger.info(f"任务已取消: {task_id}")
            return True
    
    async def pause_task(self, task_id: UUID) -> bool:
        """
        暂停任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否成功
        """
        async for db in get_db():
            await db.execute(
                update(UploadTask)
                .where(UploadTask.id == task_id)
                .values(
                    status=UploadTaskStatus.PAUSED.value,
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
            
            logger.info(f"任务已暂停: {task_id}")
            return True
    
    async def resume_task(self, task_id: UUID) -> bool:
        """
        恢复任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否成功
        """
        async for db in get_db():
            # 检查任务状态
            result = await db.execute(
                select(UploadTask).where(UploadTask.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task:
                return False
            
            if task.status not in [UploadTaskStatus.PAUSED.value, UploadTaskStatus.FAILED.value]:
                logger.warning(f"任务状态不允许恢复: {task_id}, 状态: {task.status}")
                return False
            
            # 更新状态并重新加入队列
            await db.execute(
                update(UploadTask)
                .where(UploadTask.id == task_id)
                .values(
                    status=UploadTaskStatus.QUEUED.value,
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
            
            # 重新加入队列
            await self.task_queue.put(task_id)
            
            logger.info(f"任务已恢复: {task_id}")
            return True
    
    async def _worker(self):
        """工作协程，处理任务队列"""
        while self.is_running:
            try:
                # 从队列获取任务
                task_id = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # 使用信号量控制并发
                async with self.semaphore:
                    # 创建任务协程
                    task = asyncio.create_task(self._process_task(task_id))
                    self.running_tasks[task_id] = task
                    
                    try:
                        await task
                    except asyncio.CancelledError:
                        logger.info(f"任务被取消: {task_id}")
                    except Exception as e:
                        logger.error(f"任务处理异常: {task_id}, 错误: {e}")
                    finally:
                        if task_id in self.running_tasks:
                            del self.running_tasks[task_id]
                
                self.task_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"工作协程异常: {e}")
                await asyncio.sleep(1.0)
    
    async def _process_task(self, task_id: UUID):
        """处理单个任务"""
        async for db in get_db():
            # 获取任务
            result = await db.execute(
                select(UploadTask).where(UploadTask.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task:
                logger.error(f"任务不存在: {task_id}")
                return
            
            # 检查任务状态
            if task.status == UploadTaskStatus.CANCELLED.value:
                logger.info(f"任务已取消，跳过: {task_id}")
                return
            
            if task.status == UploadTaskStatus.PAUSED.value:
                logger.info(f"任务已暂停，跳过: {task_id}")
                return
            
            # 更新状态为排队中
            if task.status == UploadTaskStatus.PENDING.value:
                await db.execute(
                    update(UploadTask)
                    .where(UploadTask.id == task_id)
                    .values(
                        status=UploadTaskStatus.QUEUED.value,
                        updated_at=datetime.utcnow()
                    )
                )
                await db.commit()
        
        # 执行上传
        await self._execute_upload(task_id)
    
    async def _execute_upload(self, task_id: UUID):
        """执行上传任务"""
        retry_count = 0
        
        while retry_count <= self.max_retries:
            try:
                # 更新状态为初始化中
                async for db in get_db():
                    await db.execute(
                        update(UploadTask)
                        .where(UploadTask.id == task_id)
                        .values(
                            status=UploadTaskStatus.INITIALIZING.value,
                            started_at=datetime.utcnow() if retry_count == 0 else None,
                            updated_at=datetime.utcnow()
                        )
                    )
                    await db.commit()
                
                # 执行上传
                await self._do_upload(task_id)
                
                # 上传成功
                return
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                logger.error(f"上传任务失败 (重试 {retry_count}/{self.max_retries}): {task_id}, 错误: {error_msg}")
                
                # 记录错误
                async for db in get_db():
                    result = await db.execute(
                        select(UploadTask).where(UploadTask.id == task_id)
                    )
                    task = result.scalar_one_or_none()
                    
                    if task:
                        error_history = task.error_history or []
                        error_history.append({
                            "retry_count": retry_count,
                            "error": error_msg,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        
                        await db.execute(
                            update(UploadTask)
                            .where(UploadTask.id == task_id)
                            .values(
                                retry_count=retry_count,
                                last_error=error_msg,
                                error_history=error_history,
                                updated_at=datetime.utcnow()
                            )
                        )
                        await db.commit()
                
                # 如果还有重试机会，等待后重试
                if retry_count <= self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                else:
                    # 重试次数用完，标记为失败
                    async for db in get_db():
                        await db.execute(
                            update(UploadTask)
                            .where(UploadTask.id == task_id)
                            .values(
                                status=UploadTaskStatus.FAILED.value,
                                updated_at=datetime.utcnow()
                            )
                        )
                        await db.commit()
    
    async def _do_upload(self, task_id: UUID):
        """执行实际上传"""
        # 获取任务信息
        async for db in get_db():
            result = await db.execute(
                select(UploadTask).where(UploadTask.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task:
                raise ValueError(f"任务不存在: {task_id}")
        
        # 检查是否需要恢复断点续传
        if task.pick_code and task.status == UploadTaskStatus.PAUSED.value:
            # 恢复断点续传
            await self._resume_upload(task)
        else:
            # 新上传
            await self._new_upload(task)
    
    async def _new_upload(self, task: UploadTask):
        """新上传任务"""
        # 定义进度回调
        def progress_callback(uploaded: int, total: int, status: str):
            asyncio.create_task(self._update_progress(
                task.id,
                uploaded,
                total,
                status
            ))
        
        # 执行上传
        result = await self.upload_manager.upload_file(
            file_path=task.file_path,
            target_parent_id=task.target_parent_id,
            file_name=task.file_name,
            progress_callback=progress_callback,
            speed_limit=task.speed_limit
        )
        
        # 更新任务状态
        async for db in get_db():
            if result.get("success"):
                # 保存pick_code用于断点续传
                pick_code = result.get("pick_code")
                if pick_code and not task.pick_code:
                    # 更新pick_code
                    await db.execute(
                        update(UploadTask)
                        .where(UploadTask.id == task.id)
                        .values(pick_code=pick_code)
                    )
                    await db.commit()
                
                await db.execute(
                    update(UploadTask)
                    .where(UploadTask.id == task.id)
                    .values(
                        status=UploadTaskStatus.COMPLETED.value,
                        upload_method=result.get("method"),
                        bucket=result.get("bucket"),
                        object_key=result.get("object_key"),
                        etag=result.get("etag"),
                        part_size=result.get("part_size"),
                        total_parts=result.get("parts_count"),
                        completed_parts=result.get("parts_count"),
                        current_speed=result.get("final_speed"),
                        completed_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                )
                await db.commit()
                
                # 验证上传
                await self._verify_upload(task.id)
            else:
                raise Exception(result.get("error", "上传失败"))
    
    async def _resume_upload(self, task: UploadTask):
        """恢复断点续传"""
        if not task.pick_code or not task.file_sha1:
            raise ValueError("缺少断点续传所需信息")
        
        # 定义进度回调
        def progress_callback(uploaded: int, total: int, status: str):
            asyncio.create_task(self._update_progress(
                task.id,
                uploaded,
                total,
                status
            ))
        
        # 执行断点续传
        result = await self.upload_manager.resume_upload(
            file_path=task.file_path,
            target_parent_id=task.target_parent_id,
            file_sha1=task.file_sha1,
            pick_code=task.pick_code,
            progress_callback=progress_callback,
            speed_limit=task.speed_limit
        )
        
        # 更新任务状态
        async for db in get_db():
            if result.get("success"):
                await db.execute(
                    update(UploadTask)
                    .where(UploadTask.id == task.id)
                    .values(
                        status=UploadTaskStatus.COMPLETED.value,
                        upload_method=result.get("method"),
                        bucket=result.get("bucket"),
                        object_key=result.get("object_key"),
                        etag=result.get("etag"),
                        completed_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                )
                await db.commit()
                
                # 验证上传
                await self._verify_upload(task.id)
            else:
                raise Exception(result.get("error", "断点续传失败"))
    
    async def _update_progress(
        self,
        task_id: UUID,
        uploaded: int,
        total: int,
        status: str
    ):
        """更新上传进度"""
        progress = (uploaded / total * 100.0) if total > 0 else 0.0
        
        async for db in get_db():
            # 更新任务进度
            await db.execute(
                update(UploadTask)
                .where(UploadTask.id == task_id)
                .values(
                    status=UploadTaskStatus.UPLOADING.value if "上传" in status else (
                        UploadTaskStatus.CALCULATING_HASH.value if "计算" in status else UploadTaskStatus.INITIALIZING.value
                    ),
                    progress=progress,
                    uploaded_bytes=uploaded,
                    total_bytes=total,
                    current_speed=current_speed,
                    updated_at=datetime.utcnow()
                )
            )
            
            # 记录进度历史（每5%记录一次，或每10秒记录一次）
            should_record = False
            if task.progress is None:
                should_record = True
            elif abs(progress - task.progress) >= 5.0:
                should_record = True
            else:
                # 检查距离上次记录是否超过10秒
                from sqlalchemy import select, desc
                last_progress_query = select(UploadProgress).where(
                    UploadProgress.task_id == task_id
                ).order_by(desc(UploadProgress.recorded_at)).limit(1)
                last_progress_result = await db.execute(last_progress_query)
                last_record = last_progress_result.scalar_one_or_none()
                if not last_record or (datetime.utcnow() - last_record.recorded_at).total_seconds() >= 10:
                    should_record = True
            
            if should_record:
                progress_record = UploadProgress(
                    task_id=task_id,
                    uploaded_bytes=uploaded,
                    total_bytes=total,
                    progress=progress,
                    current_speed=current_speed,
                    elapsed_time=elapsed_time,
                    estimated_remaining=estimated_remaining
                )
                db.add(progress_record)
            
            await db.commit()
    
    async def _verify_upload(self, task_id: UUID):
        """验证上传结果"""
        async for db in get_db():
            result = await db.execute(
                select(UploadTask).where(UploadTask.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task or not task.etag:
                return
            
            # 更新状态为验证中
            await db.execute(
                update(UploadTask)
                .where(UploadTask.id == task_id)
                .values(
                    status=UploadTaskStatus.VERIFYING.value,
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
        
        # 执行验证
        try:
            verification_result = verify_upload_complete(
                local_file_path=task.file_path,
                remote_etag=task.etag,
                remote_size=task.file_size,
                part_size=task.part_size
            )
            
            # 更新验证结果
            async for db in get_db():
                await db.execute(
                    update(UploadTask)
                    .where(UploadTask.id == task_id)
                    .values(
                        verification_status="verified" if verification_result.get("verified") else "failed",
                        verification_result=verification_result,
                        updated_at=datetime.utcnow()
                    )
                )
                await db.commit()
            
            if verification_result.get("verified"):
                logger.info(f"上传验证成功: {task_id}, ETag: {task.etag}")
            else:
                logger.error(f"上传验证失败: {task_id}, 结果: {verification_result}")
                
        except Exception as e:
            logger.error(f"上传验证异常: {task_id}, 错误: {e}")
            async for db in get_db():
                await db.execute(
                    update(UploadTask)
                    .where(UploadTask.id == task_id)
                    .values(
                        verification_status="failed",
                        verification_result={
                            "success": False,
                            "error": str(e)
                        },
                        updated_at=datetime.utcnow()
                    )
                )
                await db.commit()

