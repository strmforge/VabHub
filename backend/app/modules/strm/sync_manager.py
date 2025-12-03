"""
STRM同步管理器
实现网盘和本地STRM文件的自动同步
利用115网盘开发者权限实现实时对比
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .file_operation_mode import STRMSyncConfig
from .file_tree_manager import FileTreeManager
from .generator import STRMGenerator
from .config import STRMConfig
from .lifecycle_tracker import LifecycleTracker
from app.models.strm import STRMFileTree, STRMLifeEvent, STRMFile


class STRMSyncManager:
    """STRM同步管理器"""
    
    def __init__(
        self,
        db: AsyncSession,
        sync_config: STRMSyncConfig,
        strm_config: STRMConfig,
        cloud_storage: str = '115',
        cloud_115_api: Optional[Any] = None
    ):
        self.db = db
        self.sync_config = sync_config
        self.strm_config = strm_config
        self.cloud_storage = cloud_storage
        self.cloud_115_api = cloud_115_api
        self.file_tree_manager = FileTreeManager(db, cloud_115_api=cloud_115_api)
        self.strm_generator = STRMGenerator(strm_config, db=db)
        self.lifecycle_tracker = LifecycleTracker(db)
        self._running = False
    
    async def start_sync(self):
        """
        启动同步任务（手动触发，用于首次全量同步）
        
        注意：此方法仅用于手动触发同步（通过API端点），不用于自动增量同步。
        自动增量同步功能已移除，因为系统已有完整工作流（下载→上传→STRM生成）。
        
        工作流程：
        1. 第一次开启STRM功能时，自动全量同步一次
        2. 之后不再自动增量同步（由工作流模式处理新文件）
        3. 网盘删除文件时自动删除本地STRM文件（如果启用）
        """
        if self._running:
            logger.warning("同步任务已在运行")
            return
        
        self._running = True
        logger.info("STRM同步管理器启动")
        
        # 检测是否是第一次同步（通过检查是否有STRM文件记录或同步历史）
        is_first_sync = await self._is_first_sync()
        
        if is_first_sync:
            # 第一次开启STRM功能，执行全量同步
            logger.info("检测到第一次开启STRM功能，执行全量同步")
            await self.full_sync()
            # 标记已完成首次同步
            await self._mark_first_sync_completed()
        else:
            # 之后使用增量同步
            logger.info("执行增量同步")
            await self.incremental_sync()
        
        # 注意：自动增量同步功能已移除，因为系统已有完整工作流（下载→上传→STRM生成）
        # 新文件的STRM生成由工作流模式处理，无需额外的自动增量同步
    
    async def stop_sync(self):
        """停止同步任务"""
        self._running = False
        logger.info("STRM同步管理器停止")
    
    async def full_sync(self, cloud_media_library_path: Optional[str] = None, check_local_missing_only: bool = False):
        """
        全量同步
        
        工作流程：
        1. 扫描网盘文件树（如果指定了路径，只扫描指定路径，降低风控风险）
        2. 扫描本地STRM文件树
        3. 对比文件树，找出差异
        4. 生成STRM文件（新增和更新的文件）
        5. 删除本地STRM文件（如果网盘文件已删除）
        6. 更新同步时间
        
        Args:
            cloud_media_library_path: 网盘媒体库路径（可选，如果指定则只扫描此路径，降低风控风险）
            check_local_missing_only: 是否只检查本地缺失的文件（不调用115 API获取文件列表，进一步降低风控风险）
        """
        logger.info("开始全量同步STRM文件")
        
        try:
            # 确定扫描路径（优先使用传入的路径，否则使用配置中的路径）
            scan_path = cloud_media_library_path or self.sync_config.cloud_media_library_path or '/'
            
            if check_local_missing_only:
                # 只检查本地缺失的文件（不调用115 API，降低风控风险）
                logger.info("使用本地缺失检查模式（不调用115 API）...")
                # 1. 扫描本地STRM文件树
                logger.info("扫描本地STRM文件树...")
                local_tree = await self._scan_local_strm_files()
                logger.info(f"本地STRM文件树扫描完成，共{len(local_tree)}个文件")
                
                # 2. 从数据库获取网盘文件列表（基于已有的文件树快照）
                logger.info("从数据库获取网盘文件列表...")
                cloud_tree = await self._get_cloud_tree_from_db()
                logger.info(f"从数据库获取到{len(cloud_tree)}个文件/文件夹")
                
                # 3. 对比文件树，找出本地缺失的文件
                logger.info("对比文件树，找出本地缺失的文件...")
                missing_files = await self._find_missing_local_files(local_tree, cloud_tree)
                logger.info(f"发现{len(missing_files)}个本地缺失的文件")
                
                # 4. 为缺失的文件生成STRM文件
                if missing_files:
                    logger.info(f"开始为缺失的文件生成STRM文件，共{len(missing_files)}个文件")
                    results = await self._generate_strm_files(missing_files)
                    logger.info(f"STRM文件生成完成: 新增{len(results.get('generated', []))}, 跳过{len(results.get('skipped', []))}, 失败{len(results.get('failed', []))}")
                else:
                    results = {'generated': [], 'skipped': [], 'failed': []}
                
                # 5. 更新同步时间
                await self._update_last_sync_time()
                
                logger.info(f"全量同步完成（本地缺失检查模式）: 新增{len(results.get('generated', []))}, 跳过{len(results.get('skipped', []))}, 失败{len(results.get('failed', []))}")
                
                results['deleted'] = []
                return results
            else:
                # 传统模式：扫描网盘文件树（如果指定了路径，只扫描指定路径）
                logger.info(f"扫描网盘文件树（路径: {scan_path}）...")
                cloud_tree = await self.file_tree_manager.scan_cloud_storage(
                    self.cloud_storage,
                    root_path=scan_path
                )
                logger.info(f"网盘文件树扫描完成，共{len(cloud_tree)}个文件/文件夹")
            
            # 2. 扫描本地STRM文件树
            logger.info("扫描本地STRM文件树...")
            local_tree = await self._scan_local_strm_files()
            logger.info(f"本地STRM文件树扫描完成，共{len(local_tree)}个文件")
            
            # 3. 对比文件树，找出差异
            logger.info("对比文件树，找出差异...")
            differences = await self.file_tree_manager.compare_file_trees(
                cloud_storage=self.cloud_storage,
                local_tree=local_tree,
                cloud_tree=cloud_tree
            )
            logger.info(f"文件树对比完成: 新增{len(differences.get('added', []))}, 更新{len(differences.get('updated', []))}, 删除{len(differences.get('deleted', []))}")
            
            # 4. 生成STRM文件（新增和更新的文件）
            added_files = differences.get('added', [])
            updated_files = differences.get('updated', [])
            files_to_process = added_files + updated_files
            if files_to_process:
                logger.info(f"开始生成STRM文件，共{len(files_to_process)}个文件")
                results = await self._generate_strm_files(files_to_process)
                logger.info(f"STRM文件生成完成: 新增{len(results.get('generated', []))}, 跳过{len(results.get('skipped', []))}, 失败{len(results.get('failed', []))}")
            else:
                results = {'generated': [], 'skipped': [], 'failed': []}
            
            # 5. 删除本地STRM文件（如果网盘文件已删除）
            deleted_files = differences.get('deleted', [])
            if deleted_files and self.sync_config.auto_delete_on_cloud_delete:
                logger.info(f"开始删除本地STRM文件，共{len(deleted_files)}个文件")
                # 注意：differences['deleted'] 可能是文件路径列表，需要转换为文件信息字典
                # 这里需要根据实际情况处理
                await self._delete_local_strm_files(deleted_files)
                logger.info("本地STRM文件删除完成")
            
                # 6. 更新同步时间
                await self._update_last_sync_time()
                
                logger.info(f"全量同步完成: 新增{len(results.get('generated', []))}, 跳过{len(results.get('skipped', []))}, 失败{len(results.get('failed', []))}, 删除{len(deleted_files)}")
                
                # 返回结果，包含deleted字段
                results['deleted'] = deleted_files
                return results
                
        except Exception as e:
            logger.error(f"全量同步失败: {e}")
            raise
    
    async def _get_cloud_tree_from_db(self) -> Dict[str, Any]:
        """
        从数据库获取网盘文件树（基于已有的文件树快照）
        
        降低风控风险：不调用115 API，只从数据库读取已有的文件树记录
        
        Returns:
            网盘文件树字典
        """
        try:
            # 从STRMFileTree表获取文件树
            result = await self.db.execute(
                select(STRMFileTree)
                .where(STRMFileTree.cloud_storage == self.cloud_storage)
                .where(STRMFileTree.is_dir == False)  # 只获取文件，不获取文件夹
            )
            file_trees = result.scalars().all()
            
            cloud_tree = {}
            for file_tree in file_trees:
                # 构建文件路径
                file_path = file_tree.path
                cloud_tree[file_path] = {
                    'file_id': file_tree.file_id,
                    'file_name': file_tree.name,
                    'file_size': file_tree.size,
                    'sha1': file_tree.sha1,
                    'pick_code': file_tree.pick_code,
                    'update_time': file_tree.update_time,
                    'path': file_path
                }
            
            return cloud_tree
        except Exception as e:
            logger.error(f"从数据库获取网盘文件树失败: {e}")
            return {}
    
    async def _find_missing_local_files(
        self,
        local_tree: Dict[str, Any],
        cloud_tree: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        找出本地缺失的文件（对比本地STRM文件和网盘文件）
        
        Args:
            local_tree: 本地STRM文件树
            cloud_tree: 网盘文件树（从数据库获取）
        
        Returns:
            缺失的文件列表
        """
        missing_files = []
        
        try:
            # 构建本地STRM文件路径集合（用于快速查找）
            local_paths = set(local_tree.keys())
            
            # 遍历网盘文件，找出本地缺失的文件
            for cloud_path, cloud_file_info in cloud_tree.items():
                # 检查本地是否有对应的STRM文件
                # 注意：需要将网盘路径映射到本地STRM路径
                local_strm_path = self._map_cloud_path_to_local_strm_path(cloud_path)
                
                # 检查本地是否存在STRM文件
                if local_strm_path not in local_paths:
                    # 本地缺失此文件，需要生成STRM文件
                    missing_files.append(cloud_file_info)
            
            return missing_files
        except Exception as e:
            logger.error(f"查找本地缺失文件失败: {e}")
            return []
    
    def _map_cloud_path_to_local_strm_path(self, cloud_path: str) -> str:
        """
        将网盘路径映射到本地STRM路径
        
        Args:
            cloud_path: 网盘文件路径（例如：/115/电影/xxx.mkv）
        
        Returns:
            本地STRM文件路径（例如：/media_library/Movies/xxx.strm）
        """
        try:
            # 移除云存储前缀（例如：/115）
            for cloud_storage, cloud_prefix in self.strm_config.cloud_storage_mapping.items():
                if cloud_path.startswith(cloud_prefix):
                    relative_path = cloud_path[len(cloud_prefix):].lstrip('/')
                    # 构建本地STRM路径
                    # 这里需要根据媒体类型（电影/电视剧/动漫）映射到不同的本地路径
                    # 简化处理：直接使用media_library_path + 相对路径
                    local_path = f"{self.strm_config.media_library_path}/{relative_path}"
                    # 将文件扩展名改为.strm
                    if '.' in local_path:
                        local_path = local_path.rsplit('.', 1)[0] + '.strm'
                    return local_path
            return cloud_path
        except Exception as e:
            logger.error(f"映射网盘路径到本地STRM路径失败: {e}")
            return cloud_path
    
    async def incremental_sync(self):
        """
        增量同步
        
        工作流程：
        1. 获取上次同步时间
        2. 扫描网盘变更文件（利用115网盘开发者权限API，基于时间范围）
        3. 生成或更新STRM文件（新增和更新的文件）
        4. 检测并删除本地STRM文件（如果网盘文件已删除）
        5. 更新同步时间
        """
        logger.info("开始增量同步STRM文件")
        
        try:
            # 1. 获取上次同步时间
            last_sync_time = await self._get_last_sync_time()
            logger.info(f"上次同步时间: {last_sync_time}")
            
            # 2. 扫描网盘变更文件（利用115网盘开发者权限API，基于时间范围）
            logger.info("扫描网盘变更文件...")
            changed_files = await self._scan_cloud_changes(last_sync_time)
            logger.info(f"网盘变更文件扫描完成: 共{len(changed_files)}个文件")
            
            # 3. 生成或更新STRM文件（新增和更新的文件）
            if changed_files:
                logger.info(f"开始生成/更新STRM文件，共{len(changed_files)}个文件")
                results = await self._generate_strm_files(changed_files)
                logger.info(f"STRM文件生成/更新完成: 新增{len(results.get('generated', []))}, 跳过{len(results.get('skipped', []))}, 失败{len(results.get('failed', []))}")
            else:
                results = {'generated': [], 'skipped': [], 'failed': []}
            
            # 4. 检测并删除本地STRM文件（如果网盘文件已删除）
            # 通过对比数据库中的STRM文件和网盘文件列表检测删除的文件
            deleted_files = []
            if self.sync_config.auto_delete_on_cloud_delete:
                logger.info("检测网盘删除的文件...")
                deleted_files = await self._detect_deleted_files()
                if deleted_files:
                    logger.info(f"检测到{len(deleted_files)}个删除的文件，开始删除本地STRM文件")
                    await self._delete_local_strm_files_from_cloud_deletes(deleted_files)
                    logger.info("本地STRM文件删除完成")
                else:
                    logger.info("未检测到删除的文件")
            
            # 5. 更新同步时间
            await self._update_last_sync_time()
            
            logger.info(f"增量同步完成: 处理{len(changed_files)}个文件，删除{len(deleted_files)}个文件")
            
            # 返回结果，包含deleted字段
            results['deleted'] = deleted_files
            return results
            
        except Exception as e:
            logger.error(f"增量同步失败: {e}")
            raise
    
    async def _auto_sync_loop(self):
        """自动同步循环"""
        while self._running:
            try:
                await asyncio.sleep(self.sync_config.sync_interval)
                await self.incremental_sync()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"自动同步失败: {e}")
    
    async def _realtime_compare_loop(self):
        """实时对比循环"""
        while self._running:
            try:
                await asyncio.sleep(self.sync_config.compare_interval)
                await self._realtime_compare()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"实时对比失败: {e}")
    
    async def _realtime_compare(self):
        """
        实时对比网盘和本地STRM文件
        
        工作流程：
        1. 获取网盘文件变更（使用115网盘API，检测文件变更）
        2. 处理新增和更新的文件（生成/更新STRM文件）
        3. 处理删除的文件（自动删除本地STRM文件）
        
        注意：实时对比和增量同步的区别：
        - 增量同步：基于时间范围扫描变更文件（定时执行，如每1小时）
        - 实时对比：实时检测文件变更（更频繁，如每5分钟），主要用于快速响应变更
        """
        try:
            logger.debug("开始实时对比网盘和本地STRM文件")
            
            # 1. 获取网盘文件变更（使用115网盘API）
            # 通过对比数据库中的STRM文件和网盘文件列表检测变更
            changes = await self._get_cloud_realtime_changes()
            
            # 2. 处理新增和更新的文件
            added_files = changes.get('added', [])
            updated_files = changes.get('updated', [])
            if added_files or updated_files:
                files_to_process = added_files + updated_files
                logger.info(f"实时对比检测到{len(files_to_process)}个新增/更新文件")
                await self._generate_strm_files(files_to_process)
            
            # 3. 处理删除的文件（自动删除本地STRM文件）
            deleted_files = changes.get('deleted', [])
            if deleted_files and self.sync_config.auto_delete_on_cloud_delete:
                logger.info(f"实时对比检测到{len(deleted_files)}个删除文件")
                await self._delete_local_strm_files_from_cloud_deletes(deleted_files)
            
            # 如果没有变更，记录日志
            if not added_files and not updated_files and not deleted_files:
                logger.debug("实时对比未检测到文件变更")
            
        except Exception as e:
            logger.error(f"实时对比失败: {e}")
    
    async def _get_cloud_realtime_changes(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取网盘实时文件变更
        利用115网盘开发者权限API
        
        使用115网盘API：
        - 文件搜索API: /open/ufile/search - 根据时间范围搜索文件
        - 文件详情API: /open/folder/get_info - 获取文件详情
        
        返回格式：
        {
            'added': [文件信息字典],
            'updated': [文件信息字典],
            'deleted': [文件信息字典]
        }
        """
        try:
            if self.cloud_storage == '115' and self.cloud_115_api:
                # 获取上次同步时间
                last_sync_time = await self._get_last_sync_time()
                
                # 获取文件变更
                changes = await self.cloud_115_api.get_file_changes(
                    last_sync_time=last_sync_time,
                    file_type=4  # 4:视频
                )
                
                # 确保返回格式正确
                if not isinstance(changes, dict):
                    changes = {
                        'added': [],
                        'updated': [],
                        'deleted': []
                    }
                
                # 检测删除的文件：对比数据库中的STRM文件和网盘文件
                deleted_files = await self._detect_deleted_files()
                if deleted_files:
                    changes['deleted'] = changes.get('deleted', []) + deleted_files
                
                return changes
            else:
                logger.warning(f"未配置{self.cloud_storage}的API客户端")
                # 即使没有API客户端，也可以检测删除的文件
                deleted_files = await self._detect_deleted_files()
                return {
                    'added': [],
                    'updated': [],
                    'deleted': deleted_files
                }
                
        except Exception as e:
            logger.error(f"获取网盘实时文件变更失败: {e}")
            return {
                'added': [],
                'updated': [],
                'deleted': []
            }
    
    async def _detect_deleted_files(self) -> List[Dict[str, Any]]:
        """
        检测网盘中已删除的文件（通过对比数据库和网盘文件列表）
        
        Returns:
            删除的文件列表
        """
        try:
            deleted_files = []
            
            # 获取数据库中的所有STRM文件记录
            result = await self.db.execute(
                select(STRMFile).where(STRMFile.cloud_storage == self.cloud_storage)
            )
            strm_files = result.scalars().all()
            
            # 检查每个STRM文件对应的网盘文件是否还存在
            for strm_file in strm_files:
                try:
                    # 使用115网盘API检查文件是否存在
                    if self.cloud_115_api:
                        file_info_result = await self.cloud_115_api.get_file_info(
                            file_id=strm_file.cloud_file_id
                        )
                        
                        # 如果文件不存在或已删除，添加到删除列表
                        if not file_info_result or not file_info_result.get("success"):
                            # 文件不存在或已删除
                            deleted_files.append({
                                "file_id": strm_file.cloud_file_id,
                                "pick_code": strm_file.cloud_file_id,
                                "file_name": strm_file.title,
                                "cloud_storage": self.cloud_storage,
                                "parent_id": None,
                                "file_category": 1,
                                "file_type": 4,
                                "file_size": None,
                                "sha1": None,
                                "update_time": None
                            })
                except Exception as e:
                    logger.warning(f"检查文件是否存在失败: cloud_file_id={strm_file.cloud_file_id}, {e}")
                    # 如果检查失败，暂时不处理，避免误删
            
            return deleted_files
            
        except Exception as e:
            logger.error(f"检测删除的文件失败: {e}")
            return []
    
    async def _scan_local_strm_files(self) -> Dict[str, Any]:
        """扫描本地STRM文件"""
        strm_library_path = Path(self.sync_config.strm_library_path)
        local_files = {}
        
        # 递归扫描STRM文件
        for strm_file in strm_library_path.rglob('*.strm'):
            relative_path = strm_file.relative_to(strm_library_path)
            local_files[str(relative_path)] = {
                'path': str(strm_file),
                'size': strm_file.stat().st_size,
                'mtime': strm_file.stat().st_mtime
            }
        
        return local_files
    
    async def _generate_strm_files(self, file_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成STRM文件
        
        Args:
            file_list: 文件列表（可以是文件路径字符串或文件信息字典）
        """
        results = {
            'generated': [],
            'skipped': [],
            'failed': []
        }
        
        for file_item in file_list:
            try:
                # 处理文件路径字符串或文件信息字典
                if isinstance(file_item, str):
                    file_path = file_item
                    file_info = await self._get_cloud_file_info(file_path)
                else:
                    # 文件信息字典（来自115网盘API）
                    file_path = file_item.get('file_name', '')
                    file_id = file_item.get('file_id', '') or file_item.get('pick_code', '')
                    file_info = {
                        'file_id': file_id,
                        'file_name': file_item.get('file_name', ''),
                        'file_size': file_item.get('file_size', ''),
                        'sha1': file_item.get('sha1', ''),
                        'parent_id': file_item.get('parent_id', ''),
                        'file_category': file_item.get('file_category', 1),
                        'file_type': file_item.get('file_type', 4),
                        'update_time': file_item.get('update_time'),
                        'media_info': {}  # 需要进一步识别媒体信息
                    }
                
                # 检查是否应该处理此文件
                if not self._should_process_file(file_path):
                    results['skipped'].append(file_path)
                    continue
                
                cloud_file_id = file_info.get('file_id')
                if not cloud_file_id:
                    logger.warning(f"无法获取文件ID，跳过: {file_path}")
                    results['skipped'].append(file_path)
                    continue
                
                # 检查是否已存在STRM文件
                result = await self.db.execute(
                    select(STRMFile).where(
                        STRMFile.cloud_file_id == cloud_file_id,
                        STRMFile.cloud_storage == self.cloud_storage
                    )
                )
                existing_strm_file = result.scalar_one_or_none()
                
                # 生成STRM文件
                strm_result = await self.strm_generator.generate_strm_file(
                    media_info=file_info.get('media_info', {}),
                    cloud_file_id=cloud_file_id,
                    cloud_storage=self.cloud_storage,
                    cloud_path=file_path,
                    subtitle_files=file_info.get('subtitle_files', [])
                )
                
                # 保存或更新STRM文件记录
                if existing_strm_file:
                    # 更新现有记录
                    existing_strm_file.strm_path = strm_result['strm_path']
                    existing_strm_file.updated_at = int(datetime.now().timestamp())
                    await self.db.commit()
                    
                    # 记录更新事件
                    await self.lifecycle_tracker.record_update_event(
                        strm_file_id=existing_strm_file.id,
                        cloud_file_id=cloud_file_id,
                        cloud_storage=self.cloud_storage,
                        file_info=file_info
                    )
                    logger.info(f"STRM文件更新成功: {strm_result['strm_path']}")
                else:
                    # 创建新记录
                    new_strm_file = STRMFile(
                        cloud_file_id=cloud_file_id,
                        cloud_storage=self.cloud_storage,
                        cloud_path=file_path,
                        strm_path=strm_result['strm_path'],
                        media_type=file_info.get('media_info', {}).get('type', 'movie'),
                        title=file_info.get('media_info', {}).get('title', file_info.get('file_name', '')),
                        year=file_info.get('media_info', {}).get('year'),
                        season=file_info.get('media_info', {}).get('season'),
                        episode=file_info.get('media_info', {}).get('episode'),
                        subtitle_files=file_info.get('subtitle_files', []),
                        nfo_path=strm_result.get('nfo_path')
                    )
                    self.db.add(new_strm_file)
                    await self.db.commit()
                    await self.db.refresh(new_strm_file)
                    
                    # 记录创建事件
                    await self.lifecycle_tracker.record_create_event(
                        strm_file_id=new_strm_file.id,
                        cloud_file_id=cloud_file_id,
                        cloud_storage=self.cloud_storage,
                        file_info=file_info
                    )
                    logger.info(f"STRM文件生成成功: {strm_result['strm_path']}")
                
                results['generated'].append(file_path)
                
            except Exception as e:
                results['failed'].append({'path': file_path if isinstance(file_item, str) else file_item.get('file_name', ''), 'error': str(e)})
                logger.error(f"STRM文件生成失败: {file_item} - {e}")
        
        return results
    
    async def _delete_local_strm_files(self, file_list: List[str]):
        """删除本地STRM文件（基于文件路径）"""
        for file_path in file_list:
            try:
                # 查找对应的本地STRM文件
                local_strm_path = await self._find_local_strm_file(file_path)
                
                if local_strm_path and Path(local_strm_path).exists():
                    await self._delete_strm_file_by_path(local_strm_path, file_path)
                    
            except Exception as e:
                logger.error(f"删除本地STRM文件失败: {file_path} - {e}")
    
    async def _delete_local_strm_files_from_cloud_deletes(self, deleted_files: List[Dict[str, Any]]):
        """
        从网盘删除的文件中删除本地对应的STRM文件
        
        Args:
            deleted_files: 删除的文件列表（包含文件信息字典）
        """
        for file_info in deleted_files:
            try:
                cloud_file_id = file_info.get("file_id") or file_info.get("pick_code")
                cloud_storage = file_info.get("cloud_storage", self.cloud_storage)
                
                if not cloud_file_id:
                    logger.warning(f"无法获取文件ID，跳过删除: {file_info}")
                    continue
                
                # 查询STRM文件记录
                result = await self.db.execute(
                    select(STRMFile).where(
                        STRMFile.cloud_file_id == cloud_file_id,
                        STRMFile.cloud_storage == cloud_storage
                    )
                )
                strm_file = result.scalar_one_or_none()
                
                if strm_file:
                    strm_path = strm_file.strm_path
                    
                    # 删除本地STRM文件
                    await self._delete_strm_file_by_record(strm_file, file_info)
                else:
                    logger.warning(f"未找到对应的STRM文件记录: cloud_file_id={cloud_file_id}")
                    
            except Exception as e:
                logger.error(f"删除本地STRM文件失败: {file_info} - {e}")
    
    async def _delete_strm_file_by_path(self, strm_path: str, cloud_path: str):
        """
        删除本地STRM文件（基于文件路径）
        
        Args:
            strm_path: 本地STRM文件路径
            cloud_path: 云存储路径
        """
        try:
            strm_file_path = Path(strm_path)
            
            if strm_file_path.exists():
                # 查询STRM文件记录
                result = await self.db.execute(
                    select(STRMFile).where(STRMFile.strm_path == str(strm_path))
                )
                strm_file = result.scalar_one_or_none()
                
                # 删除文件
                strm_file_path.unlink()
                
                # 删除关联的NFO文件
                nfo_path = strm_file_path.with_suffix('.nfo')
                if nfo_path.exists():
                    nfo_path.unlink()
                
                # 删除关联的字幕文件
                subtitle_files = await self._find_local_subtitle_files(str(strm_path))
                for subtitle_file in subtitle_files:
                    if Path(subtitle_file).exists():
                        Path(subtitle_file).unlink()
                
                # 清理空文件夹
                await self._cleanup_empty_folders(strm_file_path.parent)
                
                # 记录生命周期事件
                if strm_file:
                    file_info = {
                        "parent_id": None,
                        "file_name": strm_file_path.name,
                        "file_category": 1,
                        "file_type": 4,
                        "file_size": None,
                        "sha1": None,
                        "update_time": None
                    }
                    await self.lifecycle_tracker.record_delete_event(
                        strm_file_id=strm_file.id,
                        cloud_file_id=strm_file.cloud_file_id,
                        cloud_storage=strm_file.cloud_storage,
                        file_info=file_info
                    )
                    
                    # 删除数据库记录
                    if strm_file:
                        await self.db.delete(strm_file)
                        await self.db.commit()
                        await self.db.flush()
                
                logger.info(f"本地STRM文件已删除: {strm_path}")
            else:
                logger.warning(f"本地STRM文件不存在: {strm_path}")
                
        except Exception as e:
            logger.error(f"删除本地STRM文件失败: {strm_path} - {e}")
            await self.db.rollback()
    
    async def _delete_strm_file_by_record(self, strm_file: STRMFile, file_info: Dict[str, Any]):
        """
        删除本地STRM文件（基于数据库记录）
        
        Args:
            strm_file: STRM文件记录
            file_info: 文件信息
        """
        try:
            strm_path = Path(strm_file.strm_path)
            
            if strm_path.exists():
                # 删除STRM文件
                strm_path.unlink()
                
                # 删除关联的NFO文件
                nfo_path = strm_path.with_suffix('.nfo')
                if nfo_path.exists():
                    nfo_path.unlink()
                
                # 删除关联的字幕文件
                if strm_file.subtitle_files:
                    for subtitle_file in strm_file.subtitle_files:
                        subtitle_path = strm_path.parent / subtitle_file
                        if subtitle_path.exists():
                            subtitle_path.unlink()
                
                # 清理空文件夹
                await self._cleanup_empty_folders(strm_path.parent)
                
                # 记录生命周期事件
                event_file_info = {
                    "parent_id": file_info.get("parent_id"),
                    "file_name": file_info.get("file_name", strm_path.name),
                    "file_category": file_info.get("file_category", 1),
                    "file_type": file_info.get("file_type", 4),
                    "file_size": file_info.get("file_size"),
                    "sha1": file_info.get("sha1"),
                    "update_time": file_info.get("update_time")
                }
                await self.lifecycle_tracker.record_delete_event(
                    strm_file_id=strm_file.id,
                    cloud_file_id=strm_file.cloud_file_id,
                    cloud_storage=strm_file.cloud_storage,
                    file_info=event_file_info
                )
                
                # 删除数据库记录
                await self.db.delete(strm_file)
                await self.db.commit()
                
                logger.info(f"本地STRM文件已删除: {strm_file.strm_path} (cloud_file_id={strm_file.cloud_file_id})")
            else:
                logger.warning(f"本地STRM文件不存在: {strm_file.strm_path}")
                # 即使文件不存在，也删除数据库记录并记录删除事件
                event_file_info = {
                    "parent_id": file_info.get("parent_id"),
                    "file_name": file_info.get("file_name", Path(strm_file.strm_path).name),
                    "file_category": file_info.get("file_category", 1),
                    "file_type": file_info.get("file_type", 4),
                    "file_size": file_info.get("file_size"),
                    "sha1": file_info.get("sha1"),
                    "update_time": file_info.get("update_time")
                }
                await self.lifecycle_tracker.record_delete_event(
                    strm_file_id=strm_file.id,
                    cloud_file_id=strm_file.cloud_file_id,
                    cloud_storage=strm_file.cloud_storage,
                    file_info=event_file_info
                )
                await self.db.delete(strm_file)
                await self.db.commit()
                
        except Exception as e:
            logger.error(f"删除本地STRM文件失败: {strm_file.strm_path} - {e}")
            await self.db.rollback()
    
    async def _should_process_file(self, file_path: str) -> bool:
        """判断是否应该处理此文件"""
        # 检查文件类型
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.sync_config.sync_file_types:
            return False
        
        # 检查排除路径
        for exclude_path in self.sync_config.exclude_paths:
            if file_path.startswith(exclude_path):
                return False
        
        # 检查包含路径
        if self.sync_config.include_paths:
            matched = False
            for include_path in self.sync_config.include_paths:
                if file_path.startswith(include_path):
                    matched = True
                    break
            if not matched:
                return False
        
        return True
    
    async def _get_cloud_file_info(self, file_path: str) -> Dict[str, Any]:
        """获取网盘文件信息"""
        try:
            if self.cloud_storage == '115' and self.cloud_115_api:
                # 使用115网盘API获取文件信息
                file_info = await self.cloud_115_api.get_file_info(path=file_path)
                
                if file_info:
                    return {
                        'file_id': file_info.get('file_id', ''),
                        'file_name': file_info.get('file_name', ''),
                        'file_size': file_info.get('size_byte', 0),
                        'sha1': file_info.get('sha1', ''),
                        'pick_code': file_info.get('pick_code', ''),
                        'media_info': {},  # 需要进一步识别媒体信息
                        'subtitle_files': []  # 需要查找关联的字幕文件
                    }
                else:
                    return {
                        'file_id': '',
                        'media_info': {},
                        'subtitle_files': []
                    }
            else:
                # 其他云存储或未配置API
                return {
                    'file_id': '',
                    'media_info': {},
                    'subtitle_files': []
                }
                
        except Exception as e:
            logger.error(f"获取网盘文件信息失败: {file_path} - {e}")
            return {
                'file_id': '',
                'media_info': {},
                'subtitle_files': []
            }
    
    async def _find_local_strm_file(
        self,
        cloud_path: str,
        cloud_file_id: Optional[str] = None
    ) -> Optional[str]:
        """
        查找对应的本地STRM文件
        
        Args:
            cloud_path: 云存储路径
            cloud_file_id: 云存储文件ID（可选）
        
        Returns:
            本地STRM文件路径
        """
        try:
            # 方法1：通过cloud_file_id查询数据库
            if cloud_file_id:
                from sqlalchemy import select
                from app.models.strm import STRMFile
                
                result = await self.db.execute(
                    select(STRMFile).where(STRMFile.cloud_file_id == cloud_file_id)
                )
                strm_file = result.scalar_one_or_none()
                
                if strm_file and Path(strm_file.strm_path).exists():
                    return strm_file.strm_path
            
            # 方法2：根据云存储路径映射到本地路径
            # 从云存储路径提取相对路径，然后映射到本地媒体库路径
            # 这里需要根据STRMGenerator的路径映射逻辑来实现
            # 暂时返回None，等待完善
            
            return None
            
        except Exception as e:
            logger.error(f"查找本地STRM文件失败: {cloud_path} - {e}")
            return None
    
    async def _find_local_subtitle_files(self, strm_path: str) -> List[str]:
        """查找关联的字幕文件"""
        strm_file = Path(strm_path)
        strm_dir = strm_file.parent
        subtitle_files = []
        
        # 查找同名的字幕文件
        for ext in ['.srt', '.ass', '.ssa', '.vtt']:
            subtitle_file = strm_dir / f"{strm_file.stem}{ext}"
            if subtitle_file.exists():
                subtitle_files.append(str(subtitle_file))
        
        return subtitle_files
    
    async def _cleanup_empty_folders(self, directory: Path):
        """清理空文件夹"""
        try:
            current_dir = directory
            while current_dir.exists() and current_dir != current_dir.parent:
                try:
                    if not any(current_dir.iterdir()):
                        current_dir.rmdir()
                        current_dir = current_dir.parent
                    else:
                        break
                except OSError:
                    break
        except Exception as e:
            logger.error(f"清理空文件夹失败: {e}")
    
    async def _scan_cloud_changes(self, last_sync_time: datetime) -> List[Dict[str, Any]]:
        """
        扫描网盘变更文件
        利用115网盘开发者权限API获取变更文件
        """
        try:
            if self.cloud_storage == '115' and self.cloud_115_api:
                # 使用115网盘API根据时间范围搜索文件
                files = await self.cloud_115_api.search_files_by_time_range(
                    start_time=last_sync_time,
                    end_time=datetime.now(),
                    file_type=4  # 4:视频
                )
                return files
            else:
                logger.warning(f"未配置{self.cloud_storage}的API客户端")
                return []
                
        except Exception as e:
            logger.error(f"扫描网盘变更文件失败: {e}")
            return []
    
    async def _scan_cloud_deletes(self, last_sync_time: datetime) -> List[Dict[str, Any]]:
        """
        扫描网盘删除文件
        通过对比数据库中的STRM文件和网盘文件列表检测删除的文件
        
        Args:
            last_sync_time: 上次同步时间
        
        Returns:
            删除的文件列表
        """
        try:
            # 使用检测删除文件的方法
            deleted_files = await self._detect_deleted_files()
            return deleted_files
                
        except Exception as e:
            logger.error(f"扫描网盘删除文件失败: {e}")
            return []
    
    async def _get_last_sync_time(self) -> datetime:
        """获取上次同步时间"""
        # 从数据库查询上次同步时间
        # 暂时返回当前时间
        return datetime.now() - timedelta(days=1)
    
    async def _update_last_sync_time(self):
        """更新同步时间"""
        # 更新数据库中的同步时间
        pass
    
    async def _record_life_events(self, changes: Dict[str, List[Dict[str, Any]]]):
        """
        记录生命周期事件（已集成到各个方法中，此方法保留用于批量记录）
        
        Args:
            changes: 文件变更字典
        """
        # 生命周期事件已在各个方法中记录（create/update/delete）
        # 此方法保留用于批量记录或特殊场景
        pass

