"""
文件处理模块
实现复制、移动、软连接、硬链接等文件操作
参考MoviePilot的文件处理模式
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger

from .file_operation_mode import FileOperationMode, MediaLibraryDestination, FileOperationConfig


class FileHandler:
    """文件处理器"""
    
    @staticmethod
    async def handle_file_operation(config: FileOperationConfig) -> Dict[str, Any]:
        """
        处理文件操作
        
        Args:
            config: 文件操作配置
        
        Returns:
            操作结果
        """
        source_path = Path(config.source_path)
        target_path = Path(config.target_path)
        
        # 确保目标目录存在
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 根据操作模式处理文件
        if config.operation_mode == FileOperationMode.COPY:
            return await FileHandler._copy_file(source_path, target_path, config)
        elif config.operation_mode == FileOperationMode.MOVE:
            return await FileHandler._move_file(source_path, target_path, config)
        elif config.operation_mode == FileOperationMode.SYMLINK:
            return await FileHandler._create_symlink(source_path, target_path, config)
        elif config.operation_mode == FileOperationMode.HARDLINK:
            return await FileHandler._create_hardlink(source_path, target_path, config)
        elif config.operation_mode == FileOperationMode.CLOUD_COPY:
            return await FileHandler._cloud_copy_file(source_path, target_path, config)
        elif config.operation_mode == FileOperationMode.CLOUD_MOVE:
            return await FileHandler._cloud_move_file(source_path, target_path, config)
        elif config.operation_mode == FileOperationMode.CLOUD_STRM:
            return await FileHandler._cloud_strm_file(source_path, target_path, config)
        else:
            raise ValueError(f"不支持的文件操作模式: {config.operation_mode}")
    
    @staticmethod
    async def _copy_file(
        source_path: Path,
        target_path: Path,
        config: FileOperationConfig
    ) -> Dict[str, Any]:
        """复制文件"""
        try:
            shutil.copy2(source_path, target_path)
            logger.info(f"文件复制成功: {source_path} -> {target_path}")
            return {
                'success': True,
                'operation': 'copy',
                'source_path': str(source_path),
                'target_path': str(target_path),
                'source_exists': source_path.exists(),
                'target_exists': target_path.exists()
            }
        except Exception as e:
            logger.error(f"文件复制失败: {e}")
            return {
                'success': False,
                'operation': 'copy',
                'error': str(e)
            }
    
    @staticmethod
    async def _move_file(
        source_path: Path,
        target_path: Path,
        config: FileOperationConfig
    ) -> Dict[str, Any]:
        """移动文件"""
        try:
            if config.delete_source:
                shutil.move(str(source_path), str(target_path))
                logger.info(f"文件移动成功: {source_path} -> {target_path}")
            else:
                # 如果不删除源文件，实际执行复制
                shutil.copy2(source_path, target_path)
                logger.info(f"文件复制成功（移动模式但保留源文件）: {source_path} -> {target_path}")
            
            # 清理空文件夹
            if config.delete_source:
                await FileHandler._cleanup_empty_folders(source_path.parent)
            
            return {
                'success': True,
                'operation': 'move',
                'source_path': str(source_path),
                'target_path': str(target_path),
                'source_exists': source_path.exists() if not config.delete_source else False,
                'target_exists': target_path.exists()
            }
        except Exception as e:
            logger.error(f"文件移动失败: {e}")
            return {
                'success': False,
                'operation': 'move',
                'error': str(e)
            }
    
    @staticmethod
    async def _create_symlink(
        source_path: Path,
        target_path: Path,
        config: FileOperationConfig
    ) -> Dict[str, Any]:
        """创建软连接"""
        try:
            # 删除已存在的目标文件
            if target_path.exists() or target_path.is_symlink():
                target_path.unlink()
            
            # 创建软连接
            target_path.symlink_to(source_path)
            logger.info(f"软连接创建成功: {source_path} -> {target_path}")
            
            return {
                'success': True,
                'operation': 'symlink',
                'source_path': str(source_path),
                'target_path': str(target_path),
                'source_exists': source_path.exists(),
                'target_exists': target_path.exists(),
                'is_symlink': target_path.is_symlink()
            }
        except Exception as e:
            logger.error(f"软连接创建失败: {e}")
            return {
                'success': False,
                'operation': 'symlink',
                'error': str(e)
            }
    
    @staticmethod
    async def _create_hardlink(
        source_path: Path,
        target_path: Path,
        config: FileOperationConfig
    ) -> Dict[str, Any]:
        """创建硬链接"""
        try:
            # 删除已存在的目标文件
            if target_path.exists():
                target_path.unlink()
            
            # 创建硬链接
            os.link(source_path, target_path)
            logger.info(f"硬链接创建成功: {source_path} -> {target_path}")
            
            return {
                'success': True,
                'operation': 'hardlink',
                'source_path': str(source_path),
                'target_path': str(target_path),
                'source_exists': source_path.exists(),
                'target_exists': target_path.exists(),
                'is_hardlink': os.stat(source_path).st_ino == os.stat(target_path).st_ino
            }
        except Exception as e:
            logger.error(f"硬链接创建失败: {e}")
            return {
                'success': False,
                'operation': 'hardlink',
                'error': str(e)
            }
    
    @staticmethod
    async def _cloud_copy_file(
        source_path: Path,
        target_path: Path,
        config: FileOperationConfig
    ) -> Dict[str, Any]:
        """网盘复制文件（实际上传到网盘）"""
        # 这里需要调用云存储服务的上传功能
        # 暂时返回占位符
        logger.info(f"网盘复制文件: {source_path} -> {target_path}")
        return {
            'success': True,
            'operation': 'cloud_copy',
            'source_path': str(source_path),
            'target_path': str(target_path),
            'message': '网盘复制功能需要集成云存储服务'
        }
    
    @staticmethod
    async def _cloud_move_file(
        source_path: Path,
        target_path: Path,
        config: FileOperationConfig
    ) -> Dict[str, Any]:
        """网盘移动文件（上传到网盘后删除本地文件）"""
        # 这里需要调用云存储服务的上传功能，然后删除本地文件
        # 暂时返回占位符
        logger.info(f"网盘移动文件: {source_path} -> {target_path}")
        return {
            'success': True,
            'operation': 'cloud_move',
            'source_path': str(source_path),
            'target_path': str(target_path),
            'message': '网盘移动功能需要集成云存储服务'
        }
    
    @staticmethod
    async def _cloud_strm_file(
        source_path: Path,
        target_path: Path,
        config: FileOperationConfig
    ) -> Dict[str, Any]:
        """网盘STRM文件（上传到网盘并生成STRM文件）"""
        # 这里需要调用云存储服务的上传功能，然后生成STRM文件
        # 暂时返回占位符
        logger.info(f"网盘STRM文件: {source_path} -> {target_path}")
        return {
            'success': True,
            'operation': 'cloud_strm',
            'source_path': str(source_path),
            'target_path': str(target_path),
            'message': '网盘STRM功能需要集成云存储服务和STRM生成器'
        }
    
    @staticmethod
    async def _cleanup_empty_folders(directory: Path):
        """清理空文件夹"""
        try:
            # 递归向上清理空文件夹
            current_dir = directory
            while current_dir.exists() and current_dir != current_dir.parent:
                # 检查目录是否为空
                try:
                    if not any(current_dir.iterdir()):
                        current_dir.rmdir()
                        logger.info(f"删除空文件夹: {current_dir}")
                        current_dir = current_dir.parent
                    else:
                        break
                except OSError:
                    break
        except Exception as e:
            logger.error(f"清理空文件夹失败: {e}")

