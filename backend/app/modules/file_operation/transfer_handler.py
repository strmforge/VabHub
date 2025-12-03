"""
文件传输处理器
参考MoviePilot的transhandler实现
支持本地存储到本地存储、本地存储到云存储、云存储到本地存储、云存储到云存储
"""

from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from loguru import logger

from app.modules.file_operation.overwrite_handler import OverwriteHandler, OverwriteMode
from app.modules.strm.file_operation_mode import FileOperationMode, FileOperationConfig, get_available_modes, validate_operation_mode


class TransferHandler:
    """文件传输处理器（参考MoviePilot）"""
    
    @staticmethod
    async def transfer_file(
        config: FileOperationConfig,
        source_oper: Optional[Any] = None,
        target_oper: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        传输文件（参考MoviePilot的__transfer_command方法）
        
        Args:
            config: 文件操作配置
            source_oper: 源存储操作对象（可选）
            target_oper: 目标存储操作对象（可选）
        
        Returns:
            传输结果
        """
        source_path = Path(config.source_path)
        target_path = Path(config.target_path)
        
        # 1. 检查传输类型是否支持
        if not validate_operation_mode(
            config.source_storage,
            config.target_storage,
            config.operation_mode
        ):
            return {
                "success": False,
                "error": f"不支持的传输类型: {config.operation_mode} (源: {config.source_storage}, 目标: {config.target_storage})"
            }
        
        # 2. 检查覆盖模式
        if config.source_storage == "local":
            new_file_size = source_path.stat().st_size if source_path.exists() else None
        else:
            # 云存储：需要从source_oper获取文件大小
            new_file_size = await TransferHandler._get_cloud_file_size(
                source_path, config.source_storage, source_oper
            )
        
        should_overwrite, reason = await OverwriteHandler.check_overwrite(
            target_path=target_path,
            overwrite_mode=config.overwrite_mode,
            new_file_size=new_file_size,
            storage_type=config.target_storage,
            storage_oper=target_oper
        )
        
        if not should_overwrite:
            return {
                "success": False,
                "error": reason
            }
        
        # 3. 如果是latest模式，删除版本文件
        if config.overwrite_mode == OverwriteMode.LATEST:
            await OverwriteHandler.delete_version_files(
                target_path=target_path,
                storage_type=config.target_storage,
                storage_oper=target_oper
            )
        
        # 4. 执行文件传输
        try:
            if config.source_storage == "local" and config.target_storage == "local":
                # 本地到本地
                return await TransferHandler._transfer_local_to_local(
                    source_path, target_path, config
                )
            elif config.source_storage == "local" and config.target_storage != "local":
                # 本地到云存储
                return await TransferHandler._transfer_local_to_cloud(
                    source_path, target_path, config, target_oper
                )
            elif config.source_storage != "local" and config.target_storage == "local":
                # 云存储到本地
                return await TransferHandler._transfer_cloud_to_local(
                    source_path, target_path, config, source_oper
                )
            elif config.source_storage == config.target_storage:
                # 云存储到云存储（同一网盘）
                return await TransferHandler._transfer_cloud_to_cloud(
                    source_path, target_path, config, source_oper, target_oper
                )
            else:
                return {
                    "success": False,
                    "error": f"不支持 {config.source_storage} 到 {config.target_storage} 的文件传输"
                }
        except Exception as e:
            logger.error(f"文件传输失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def _transfer_local_to_local(
        source_path: Path,
        target_path: Path,
        config: FileOperationConfig
    ) -> Dict[str, Any]:
        """本地到本地传输（参考MoviePilot）"""
        # 创建目录
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if config.operation_mode == FileOperationMode.COPY:
                import shutil
                shutil.copy2(source_path, target_path)
                logger.info(f"本地复制成功: {source_path} -> {target_path}")
                return {
                    "success": True,
                    "operation": "copy",
                    "source_path": str(source_path),
                    "target_path": str(target_path)
                }
            elif config.operation_mode == FileOperationMode.MOVE:
                import shutil
                shutil.move(str(source_path), str(target_path))
                logger.info(f"本地移动成功: {source_path} -> {target_path}")
                return {
                    "success": True,
                    "operation": "move",
                    "source_path": str(source_path),
                    "target_path": str(target_path)
                }
            elif config.operation_mode == FileOperationMode.LINK:
                import os
                # 删除已存在的目标文件
                if target_path.exists():
                    target_path.unlink()
                os.link(source_path, target_path)
                logger.info(f"硬链接创建成功: {source_path} -> {target_path}")
                return {
                    "success": True,
                    "operation": "link",
                    "source_path": str(source_path),
                    "target_path": str(target_path)
                }
            elif config.operation_mode == FileOperationMode.SOFTLINK:
                # 删除已存在的目标文件
                if target_path.exists() or target_path.is_symlink():
                    target_path.unlink()
                target_path.symlink_to(source_path)
                logger.info(f"软链接创建成功: {source_path} -> {target_path}")
                return {
                    "success": True,
                    "operation": "softlink",
                    "source_path": str(source_path),
                    "target_path": str(target_path)
                }
            else:
                return {
                    "success": False,
                    "error": f"不支持的传输方式: {config.operation_mode}"
                }
        except Exception as e:
            logger.error(f"本地传输失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def _transfer_local_to_cloud(
        source_path: Path,
        target_path: Path,
        config: FileOperationConfig,
        target_oper: Optional[Any]
    ) -> Dict[str, Any]:
        """本地到云存储传输（参考MoviePilot）"""
        if not source_path.exists():
            return {
                "success": False,
                "error": f"文件 {source_path} 不存在"
            }
        
        if not target_oper:
            return {
                "success": False,
                "error": "未提供目标存储操作对象"
            }
        
        try:
            # 获取目标文件夹
            if hasattr(target_oper, 'get_folder'):
                target_folder = target_oper.get_folder(target_path.parent)
                if not target_folder:
                    return {
                        "success": False,
                        "error": f"目标目录 {target_path.parent} 获取失败"
                    }
            else:
                # 如果没有get_folder方法，需要创建文件夹
                target_folder = await TransferHandler._ensure_cloud_folder(
                    target_path.parent, config.target_storage, target_oper
                )
            
            # 上传文件
            if hasattr(target_oper, 'upload'):
                new_item = target_oper.upload(target_folder, source_path, target_path.name)
                if not new_item:
                    return {
                        "success": False,
                        "error": f"上传 {config.target_storage} 失败"
                    }
                
                # 如果是移动模式，删除本地文件
                if config.operation_mode == FileOperationMode.MOVE:
                    source_path.unlink()
                    logger.info(f"删除本地文件: {source_path}")
                
                return {
                    "success": True,
                    "operation": config.operation_mode.value,
                    "source_path": str(source_path),
                    "target_path": str(target_path),
                    "cloud_file_id": getattr(new_item, 'fileid', None) if new_item else None
                }
            else:
                return {
                    "success": False,
                    "error": "目标存储操作对象不支持上传功能"
                }
        except Exception as e:
            logger.error(f"上传到云存储失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def _transfer_cloud_to_local(
        source_path: Path,
        target_path: Path,
        config: FileOperationConfig,
        source_oper: Optional[Any]
    ) -> Dict[str, Any]:
        """云存储到本地传输（参考MoviePilot）"""
        if target_path.exists():
            logger.warning(f"文件已存在: {target_path}")
            return {
                "success": True,
                "operation": "skip",
                "target_path": str(target_path),
                "message": "文件已存在，跳过下载"
            }
        
        if not source_oper:
            return {
                "success": False,
                "error": "未提供源存储操作对象"
            }
        
        try:
            # 创建目录
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 下载文件
            if hasattr(source_oper, 'download'):
                # 获取文件项
                if hasattr(source_oper, 'get_item'):
                    fileitem = source_oper.get_item(source_path)
                    if not fileitem:
                        return {
                            "success": False,
                            "error": f"获取文件 {source_path} 失败"
                        }
                else:
                    fileitem = source_path
                
                # 下载到临时文件
                tmp_file = source_oper.download(fileitem=fileitem, path=target_path.parent)
                if not tmp_file:
                    return {
                        "success": False,
                        "error": f"下载 {config.source_storage} 失败"
                    }
                
                # 移动到目标位置
                import shutil
                shutil.move(str(tmp_file), str(target_path))
                
                # 如果是移动模式，删除云存储文件
                if config.operation_mode == FileOperationMode.MOVE:
                    if hasattr(source_oper, 'delete'):
                        source_oper.delete(fileitem)
                        logger.info(f"删除云存储文件: {source_path}")
                
                return {
                    "success": True,
                    "operation": config.operation_mode.value,
                    "source_path": str(source_path),
                    "target_path": str(target_path)
                }
            else:
                return {
                    "success": False,
                    "error": "源存储操作对象不支持下载功能"
                }
        except Exception as e:
            logger.error(f"从云存储下载失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def _transfer_cloud_to_cloud(
        source_path: Path,
        target_path: Path,
        config: FileOperationConfig,
        source_oper: Optional[Any],
        target_oper: Optional[Any]
    ) -> Dict[str, Any]:
        """云存储到云存储传输（参考MoviePilot）"""
        if not source_oper or not target_oper:
            return {
                "success": False,
                "error": "未提供存储操作对象"
            }
        
        try:
            # 获取源文件项
            if hasattr(source_oper, 'get_item'):
                fileitem = source_oper.get_item(source_path)
                if not fileitem:
                    return {
                        "success": False,
                        "error": f"获取文件 {source_path} 失败"
                    }
            else:
                fileitem = source_path
            
            # 获取目标文件夹
            if hasattr(target_oper, 'get_folder'):
                target_folder = target_oper.get_folder(target_path.parent)
                if not target_folder:
                    return {
                        "success": False,
                        "error": f"目标目录 {target_path.parent} 获取失败"
                    }
            else:
                target_folder = target_path.parent
            
            if config.operation_mode == FileOperationMode.COPY:
                # 复制文件
                if hasattr(source_oper, 'copy'):
                    success = source_oper.copy(fileitem, Path(target_folder), target_path.name)
                    if success:
                        return {
                            "success": True,
                            "operation": "copy",
                            "source_path": str(source_path),
                            "target_path": str(target_path)
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"复制文件失败"
                        }
                else:
                    return {
                        "success": False,
                        "error": "源存储操作对象不支持复制功能"
                    }
            elif config.operation_mode == FileOperationMode.MOVE:
                # 移动文件
                if hasattr(source_oper, 'move'):
                    success = source_oper.move(fileitem, Path(target_folder), target_path.name)
                    if success:
                        return {
                            "success": True,
                            "operation": "move",
                            "source_path": str(source_path),
                            "target_path": str(target_path)
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"移动文件失败"
                        }
                else:
                    return {
                        "success": False,
                        "error": "源存储操作对象不支持移动功能"
                    }
            else:
                return {
                    "success": False,
                    "error": f"不支持的传输方式: {config.operation_mode}"
                }
        except Exception as e:
            logger.error(f"云存储到云存储传输失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def _get_cloud_file_size(
        source_path: Path,
        storage_type: str,
        storage_oper: Optional[Any]
    ) -> Optional[int]:
        """获取云存储文件大小"""
        if not storage_oper:
            return None
        
        try:
            if hasattr(storage_oper, 'get_item'):
                fileitem = storage_oper.get_item(source_path)
                if fileitem and hasattr(fileitem, 'size'):
                    return fileitem.size
        except Exception as e:
            logger.error(f"获取云存储文件大小失败: {e}")
        
        return None
    
    @staticmethod
    async def _ensure_cloud_folder(
        folder_path: Path,
        storage_type: str,
        storage_oper: Optional[Any]
    ) -> Any:
        """确保云存储文件夹存在"""
        # 这里需要根据实际的存储操作对象实现
        # 暂时返回folder_path
        return folder_path

