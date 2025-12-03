"""
重复文件检测器
"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from loguru import logger
import asyncio
from concurrent.futures import ThreadPoolExecutor


@dataclass
class DuplicateFile:
    """重复文件信息"""
    file_path: str
    file_size: int
    file_hash: str
    group_id: int  # 同一组的重复文件具有相同的group_id


class DuplicateDetector:
    """重复文件检测器"""
    
    def __init__(self, chunk_size: int = 8192, max_workers: int = 4):
        """
        初始化重复文件检测器
        
        Args:
            chunk_size: 读取文件时的块大小（字节）
            max_workers: 最大并发工作线程数
        """
        self.chunk_size = chunk_size
        self.max_workers = max_workers
    
    def calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件哈希值（MD5）
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件的MD5哈希值
        """
        md5_hash = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                # 读取文件并更新哈希（流式处理，减少内存占用）
                while chunk := f.read(self.chunk_size):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败: {file_path}, 错误: {e}")
            return ""
    
    def calculate_file_hash_parallel(self, file_paths: List[str]) -> Dict[str, str]:
        """
        并行计算多个文件的哈希值
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            文件路径到哈希值的字典
        """
        hash_map = {}
        
        def calculate_single(file_path: str) -> Tuple[str, str]:
            return file_path, self.calculate_file_hash(file_path)
        
        # 使用线程池并行计算
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = executor.map(calculate_single, file_paths)
            for file_path, file_hash in results:
                if file_hash:
                    hash_map[file_path] = file_hash
        
        return hash_map
    
    def detect_duplicates_by_size(self, directory: str, extensions: Optional[List[str]] = None) -> Dict[int, List[str]]:
        """
        按文件大小检测重复文件（快速检测）
        
        Args:
            directory: 目录路径
            extensions: 文件扩展名列表（如 ['.mp4', '.mkv']），如果为None则检测所有文件
            
        Returns:
            字典，键为文件大小，值为具有该大小的文件路径列表
        """
        size_map: Dict[int, List[str]] = {}
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # 检查扩展名
                    if extensions:
                        file_ext = Path(file_path).suffix.lower()
                        if file_ext not in extensions:
                            continue
                    
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size not in size_map:
                            size_map[file_size] = []
                        size_map[file_size].append(file_path)
                    except OSError:
                        continue
        except Exception as e:
            logger.error(f"扫描目录失败: {directory}, 错误: {e}")
        
        # 只返回大小重复的文件
        return {size: paths for size, paths in size_map.items() if len(paths) > 1}
    
    def detect_duplicates_by_hash(
        self,
        directory: str,
        extensions: Optional[List[str]] = None
    ) -> List[List[DuplicateFile]]:
        """
        按文件哈希值检测重复文件（精确检测）
        
        Args:
            directory: 目录路径
            extensions: 文件扩展名列表
            
        Returns:
            重复文件组列表，每个组包含具有相同哈希值的文件
        """
        # 先按大小快速检测
        size_duplicates = self.detect_duplicates_by_size(directory, extensions)
        
        # 对大小相同的文件计算哈希值
        hash_map: Dict[str, List[DuplicateFile]] = {}
        group_id = 0
        
        # 收集所有需要计算哈希的文件
        files_to_hash = []
        for size, file_paths in size_duplicates.items():
            if len(file_paths) >= 2:
                files_to_hash.extend(file_paths)
        
        # 并行计算哈希值
        if files_to_hash:
            hash_map_parallel = self.calculate_file_hash_parallel(files_to_hash)
            
            # 按大小分组处理
            for size, file_paths in size_duplicates.items():
                if len(file_paths) < 2:
                    continue
                
                # 使用已计算的哈希值
                for file_path in file_paths:
                    file_hash = hash_map_parallel.get(file_path)
                    if not file_hash:
                        continue
                    
                    if file_hash not in hash_map:
                        hash_map[file_hash] = []
                        group_id += 1
                    
                    hash_map[file_hash].append(
                        DuplicateFile(
                            file_path=file_path,
                            file_size=size,
                            file_hash=file_hash,
                            group_id=group_id
                        )
                    )
        
        # 只返回哈希值重复的文件组
        return [files for files in hash_map.values() if len(files) > 1]
    
    def detect_duplicates(
        self,
        directory: str,
        extensions: Optional[List[str]] = None,
        use_hash: bool = True
    ) -> List[List[DuplicateFile]]:
        """
        检测重复文件
        
        Args:
            directory: 目录路径
            extensions: 文件扩展名列表
            use_hash: 是否使用哈希值检测（更精确但更慢）
            
        Returns:
            重复文件组列表
        """
        if use_hash:
            return self.detect_duplicates_by_hash(directory, extensions)
        else:
            # 只按大小检测
            size_duplicates = self.detect_duplicates_by_size(directory, extensions)
            duplicate_groups = []
            group_id = 0
            
            for size, file_paths in size_duplicates.items():
                group_id += 1
                group = [
                    DuplicateFile(
                        file_path=path,
                        file_size=size,
                        file_hash="",
                        group_id=group_id
                    )
                    for path in file_paths
                ]
                duplicate_groups.append(group)
            
            return duplicate_groups

