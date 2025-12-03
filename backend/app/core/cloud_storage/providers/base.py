"""
云存储提供商基类
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple, Callable
from dataclasses import dataclass
from app.core.cloud_storage.schemas import CloudStorageUsage
from datetime import datetime


@dataclass
class CloudFileInfo:
    """云存储文件信息"""
    id: str
    name: str
    path: str
    size: int
    type: str  # "file" or "dir"
    parent_id: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    thumbnail: Optional[str] = None
    download_url: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CloudStorageUsage:
    """云存储使用情况"""
    total: int  # 总容量（字节）
    used: int   # 已使用（字节）
    available: int  # 可用容量（字节）
    percentage: float = 0.0  # 使用率（0-100）


class CloudStorageProvider(ABC):
    """云存储提供商基类"""
    
    # 支持的传输类型（子类可以覆盖）
    transtype: Dict[str, str] = {}
    # 是否支持快照检查文件夹修改时间
    snapshot_check_folder_modtime: bool = True
    
    @abstractmethod
    async def initialize(self, credentials: Dict[str, Any]) -> bool:
        """初始化提供商"""
        pass
    
    @abstractmethod
    async def is_authenticated(self) -> bool:
        """检查是否已认证"""
        pass
    
    @abstractmethod
    async def list_files(self, path: str = "/", recursive: bool = False) -> List[CloudFileInfo]:
        """列出文件"""
        pass
    
    @abstractmethod
    async def get_file_info(self, file_id: str) -> Optional[CloudFileInfo]:
        """获取文件信息"""
        pass
    
    @abstractmethod
    async def create_folder(self, parent_path: str, name: str) -> Optional[CloudFileInfo]:
        """创建文件夹"""
        pass
    
    @abstractmethod
    async def delete_file(self, file_id: str) -> bool:
        """删除文件"""
        pass
    
    @abstractmethod
    async def upload_file(self, local_path: str, remote_path: str, progress_callback: Optional[Callable] = None) -> bool:
        """上传文件"""
        pass
    
    @abstractmethod
    async def download_file(self, file_id: str, save_path: str, progress_callback: Optional[Callable] = None) -> bool:
        """下载文件"""
        pass
    
    @abstractmethod
    async def get_storage_usage(self) -> Optional[CloudStorageUsage]:
        """获取存储使用情况"""
        pass
    
    # ========== 扩展方法（可选实现） ==========
    
    async def check(self) -> bool:
        """
        检查存储是否可用
        默认实现：检查是否已认证
        """
        return await self.is_authenticated()
    
    def get_config(self) -> Optional[Dict[str, Any]]:
        """
        获取配置
        子类可以覆盖此方法以提供配置管理
        """
        return None
    
    def set_config(self, conf: Dict[str, Any]):
        """
        设置配置
        子类可以覆盖此方法以提供配置管理
        """
        pass
    
    def generate_qrcode(self, *args, **kwargs) -> Optional[Tuple[Dict[str, Any], str]]:
        """
        生成二维码（用于网盘登录）
        返回: (二维码数据, 二维码URL) 或 None
        """
        return None
    
    def check_login(self, *args, **kwargs) -> Optional[Dict[str, str]]:
        """
        检查登录状态
        返回: 登录信息字典 或 None
        """
        return None
    
    def support_transtype(self) -> Dict[str, str]:
        """
        支持的传输类型
        返回: {类型名: 描述} 字典
        """
        return self.transtype
    
    def is_support_transtype(self, transtype: str) -> bool:
        """
        是否支持特定传输类型
        """
        return transtype in self.transtype
    
    def reset_config(self):
        """
        重置配置
        子类可以覆盖此方法
        """
        pass
    
    async def move_file(self, file_id: str, target_path: str) -> bool:
        """
        移动文件（可选实现）
        """
        raise NotImplementedError("此存储提供商不支持移动文件")
    
    async def copy_file(self, file_id: str, target_path: str) -> bool:
        """
        复制文件（可选实现）
        """
        raise NotImplementedError("此存储提供商不支持复制文件")
    
    async def rename_file(self, file_id: str, new_name: str) -> bool:
        """
        重命名文件（可选实现）
        """
        raise NotImplementedError("此存储提供商不支持重命名文件")

