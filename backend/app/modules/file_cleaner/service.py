"""
文件清理服务
清理临时文件、空目录等
"""

import os
import fnmatch
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class CleanupResult:
    """清理结果"""
    cleaned_files: int = 0
    cleaned_dirs: int = 0
    total_size: int = 0
    files_removed: List[str] = None
    dirs_removed: List[str] = None
    
    def __post_init__(self):
        if self.files_removed is None:
            self.files_removed = []
        if self.dirs_removed is None:
            self.dirs_removed = []


class FileCleanerService:
    """文件清理服务"""
    
    # 临时文件模式
    TEMP_PATTERNS = [
        "*.tmp", "*.temp", "*.bak", "*.log", "~*", "._*",
        "Thumbs.db", ".DS_Store", "desktop.ini",
        "*.swp", "*.swo", "*.cache", "*.lock"
    ]
    
    # 临时目录模式
    TEMP_DIR_PATTERNS = [
        "__pycache__", ".pytest_cache", ".mypy_cache",
        ".cache", ".tmp", "node_modules"
    ]
    
    def __init__(self):
        pass
    
    def _is_temp_file(self, filename: str) -> bool:
        """检查是否为临时文件"""
        for pattern in self.TEMP_PATTERNS:
            if fnmatch.fnmatch(filename, pattern):
                return True
        return False
    
    def _is_temp_dir(self, dirname: str) -> bool:
        """检查是否为临时目录"""
        return dirname in self.TEMP_DIR_PATTERNS
    
    async def clean_directory(
        self,
        directory: str,
        dry_run: bool = True,
        include_subdirs: bool = True,
        max_file_size_mb: Optional[int] = None
    ) -> CleanupResult:
        """清理目录"""
        result = CleanupResult()
        dir_path = Path(directory)
        
        if not dir_path.exists():
            logger.error(f"目录不存在: {directory}")
            return result
        
        if not dir_path.is_dir():
            logger.error(f"路径不是目录: {directory}")
            return result
        
        try:
            # P3-4: SafetyPolicyEngine 清理前检查
            try:
                from app.modules.safety.engine import get_safety_policy_engine
                from app.modules.safety.models import SafetyContext
                from app.modules.hr_case.repository import get_hr_repository
                
                safety_engine = get_safety_policy_engine()
                hr_repo = get_hr_repository()
                
                # 创建安全上下文
                safety_ctx = SafetyContext(
                    action="upload_cleanup",
                    site_key=None,  # 清理操作通常不针对特定站点
                    torrent_id=None,
                    trigger="system_runner",
                    metadata={
                        "cleanup_directory": directory,
                        "dry_run": dry_run
                    }
                )
                
                # 执行安全策略评估
                safety_decision = await safety_engine.evaluate(safety_ctx)
                
                if safety_decision.decision == "DENY":
                    logger.warning(f"安全策略阻止清理: {safety_decision.message}")
                    return result
                elif safety_decision.decision == "REQUIRE_CONFIRM":
                    logger.warning(f"清理需要用户确认: {safety_decision.message}")
                    # 对于自动清理，需要确认时直接跳过
                    return result
                    
            except Exception as e:
                logger.warning(f"安全策略检查失败，允许清理: {e}")
            
            # 清理临时文件
            if include_subdirs:
                files = list(dir_path.rglob('*'))
            else:
                files = list(dir_path.iterdir())
            
            for file_path in files:
                if not file_path.is_file():
                    continue
                
                # 检查文件大小
                if max_file_size_mb:
                    file_size_mb = file_path.stat().st_size / (1024 * 1024)
                    if file_size_mb > max_file_size_mb:
                        continue
                
                # 检查是否为临时文件
                if self._is_temp_file(file_path.name):
                    file_size = file_path.stat().st_size
                    
                    if not dry_run:
                        try:
                            file_path.unlink()
                            result.cleaned_files += 1
                            result.total_size += file_size
                            result.files_removed.append(str(file_path))
                            logger.debug(f"已删除临时文件: {file_path}")
                        except Exception as e:
                            logger.warning(f"删除文件失败: {file_path} - {e}")
                    else:
                        result.cleaned_files += 1
                        result.total_size += file_size
                        result.files_removed.append(str(file_path))
            
            # 清理空目录（从底层开始）
            if not dry_run:
                # 收集所有目录
                dirs = []
                if include_subdirs:
                    for item in dir_path.rglob('*'):
                        if item.is_dir():
                            dirs.append(item)
                else:
                    for item in dir_path.iterdir():
                        if item.is_dir():
                            dirs.append(item)
                
                # 按深度排序（从深到浅）
                dirs.sort(key=lambda p: len(p.parts), reverse=True)
                
                for dir_item in dirs:
                    try:
                        # 跳过临时目录
                        if self._is_temp_dir(dir_item.name):
                            # 删除整个临时目录
                            try:
                                import shutil
                                shutil.rmtree(dir_item)
                                result.cleaned_dirs += 1
                                result.dirs_removed.append(str(dir_item))
                                logger.debug(f"已删除临时目录: {dir_item}")
                            except Exception as e:
                                logger.warning(f"删除临时目录失败: {dir_item} - {e}")
                        else:
                            # 只删除空目录
                            if not any(dir_item.iterdir()):
                                dir_item.rmdir()
                                result.cleaned_dirs += 1
                                result.dirs_removed.append(str(dir_item))
                                logger.debug(f"已删除空目录: {dir_item}")
                    except Exception as e:
                        logger.debug(f"删除目录失败或目录非空: {dir_item} - {e}")
            
            logger.info(
                f"清理完成: {result.cleaned_files} 个文件, {result.cleaned_dirs} 个目录, "
                f"释放空间: {result.total_size / 1024 / 1024:.2f} MB"
            )
            
        except Exception as e:
            logger.error(f"清理目录失败: {directory} - {e}")
        
        return result
    
    async def clean_by_size(
        self,
        directory: str,
        max_size_mb: int = 10,
        dry_run: bool = True,
        include_subdirs: bool = True
    ) -> CleanupResult:
        """按大小清理文件"""
        return await self.clean_directory(
            directory=directory,
            dry_run=dry_run,
            include_subdirs=include_subdirs,
            max_file_size_mb=max_size_mb
        )
    
    async def clean_by_age(
        self,
        directory: str,
        days: int = 7,
        dry_run: bool = True,
        include_subdirs: bool = True
    ) -> CleanupResult:
        """按年龄清理文件（删除指定天数前的文件）"""
        result = CleanupResult()
        dir_path = Path(directory)
        
        if not dir_path.exists() or not dir_path.is_dir():
            return result
        
        from datetime import datetime, timedelta
        cutoff_time = datetime.now() - timedelta(days=days)
        
        try:
            if include_subdirs:
                files = list(dir_path.rglob('*'))
            else:
                files = list(dir_path.iterdir())
            
            for file_path in files:
                if not file_path.is_file():
                    continue
                
                # 检查文件修改时间
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_time:
                    # 只清理临时文件
                    if self._is_temp_file(file_path.name):
                        file_size = file_path.stat().st_size
                        
                        if not dry_run:
                            try:
                                file_path.unlink()
                                result.cleaned_files += 1
                                result.total_size += file_size
                                result.files_removed.append(str(file_path))
                            except Exception as e:
                                logger.warning(f"删除文件失败: {file_path} - {e}")
                        else:
                            result.cleaned_files += 1
                            result.total_size += file_size
                            result.files_removed.append(str(file_path))
            
        except Exception as e:
            logger.error(f"按年龄清理文件失败: {directory} - {e}")
        
        return result
    
    async def get_directory_stats(self, directory: str) -> Dict[str, Any]:
        """获取目录统计信息"""
        dir_path = Path(directory)
        
        if not dir_path.exists() or not dir_path.is_dir():
            return {
                "total_files": 0,
                "total_dirs": 0,
                "total_size": 0,
                "temp_files": 0,
                "temp_dirs": 0,
                "temp_size": 0
            }
        
        total_files = 0
        total_dirs = 0
        total_size = 0
        temp_files = 0
        temp_dirs = 0
        temp_size = 0
        
        try:
            for item in dir_path.rglob('*'):
                if item.is_file():
                    total_files += 1
                    file_size = item.stat().st_size
                    total_size += file_size
                    
                    if self._is_temp_file(item.name):
                        temp_files += 1
                        temp_size += file_size
                elif item.is_dir():
                    total_dirs += 1
                    if self._is_temp_dir(item.name):
                        temp_dirs += 1
        except Exception as e:
            logger.error(f"获取目录统计失败: {directory} - {e}")
        
        return {
            "total_files": total_files,
            "total_dirs": total_dirs,
            "total_size": total_size,
            "temp_files": temp_files,
            "temp_dirs": temp_dirs,
            "temp_size": temp_size
        }

