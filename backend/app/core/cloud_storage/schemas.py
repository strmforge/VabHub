"""
云存储数据模型
统一的数据模型定义，参考MoviePilot的设计
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from pathlib import Path


class FileItem(BaseModel):
    """文件项（统一模型，参考MoviePilot）"""
    # 存储类型
    storage: Optional[str] = Field(default="local", description="存储类型")
    # 类型 dir/file
    type: Optional[str] = Field(default=None, description="文件类型: file/dir")
    # 文件路径
    path: Optional[str] = Field(default="/", description="文件路径")
    # 文件名
    name: Optional[str] = Field(default=None, description="文件名")
    # 文件基本名（不含扩展名）
    basename: Optional[str] = Field(default=None, description="文件基本名")
    # 文件扩展名
    extension: Optional[str] = Field(default=None, description="文件扩展名")
    # 文件大小
    size: Optional[int] = Field(default=None, description="文件大小（字节）")
    # 修改时间（时间戳）
    modify_time: Optional[float] = Field(default=None, description="修改时间（时间戳）")
    # 创建时间（时间戳）
    create_time: Optional[float] = Field(default=None, description="创建时间（时间戳）")
    # 子节点
    children: Optional[List['FileItem']] = Field(default_factory=list, description="子节点（目录时）")
    # 文件ID
    fileid: Optional[str] = Field(default=None, description="文件ID")
    # 父文件ID
    parent_fileid: Optional[str] = Field(default=None, description="父文件ID")
    # 缩略图URL
    thumbnail: Optional[str] = Field(default=None, description="缩略图URL")
    # 115 pickcode（115网盘专用）
    pickcode: Optional[str] = Field(default=None, description="115 pickcode")
    # drive_id（网盘驱动ID）
    drive_id: Optional[str] = Field(default=None, description="drive_id")
    # 下载URL
    url: Optional[str] = Field(default=None, description="下载URL")
    # 元数据
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")
    
    class Config:
        json_encoders = {
            Path: str,
            datetime: lambda v: v.isoformat() if v else None
        }


class CloudStorageUsage(BaseModel):
    """云存储使用情况"""
    # 总空间（字节）
    total: float = Field(default=0.0, description="总空间（字节）")
    # 已使用空间（字节）
    used: float = Field(default=0.0, description="已使用空间（字节）")
    # 剩余空间（字节）
    available: float = Field(default=0.0, description="剩余空间（字节）")
    # 使用率（0-100）
    percentage: float = Field(default=0.0, description="使用率（0-100）")


class StorageUsage(BaseModel):
    """存储使用情况"""
    # 总空间（字节）
    total: float = Field(default=0.0, description="总空间（字节）")
    # 已使用空间（字节）
    used: float = Field(default=0.0, description="已使用空间（字节）")
    # 剩余空间（字节）
    available: float = Field(default=0.0, description="剩余空间（字节）")
    # 使用率（0-100）
    percentage: float = Field(default=0.0, description="使用率（0-100）")
    
    @property
    def used_gb(self) -> float:
        """已使用空间（GB）"""
        return self.used / (1024 ** 3)
    
    @property
    def available_gb(self) -> float:
        """剩余空间（GB）"""
        return self.available / (1024 ** 3)
    
    @property
    def total_gb(self) -> float:
        """总空间（GB）"""
        return self.total / (1024 ** 3)


class StorageConfig(BaseModel):
    """存储配置"""
    # 提供商类型
    provider: str = Field(..., description="提供商类型（115、rclone、openlist等）")
    # 配置名称
    name: str = Field(..., description="配置名称")
    # 是否启用
    enabled: bool = Field(default=True, description="是否启用")
    # 具体配置
    config: Dict[str, Any] = Field(default_factory=dict, description="具体配置")
    # 创建时间
    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    # 更新时间
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TransferInfo(BaseModel):
    """传输信息"""
    # 源路径
    source: str = Field(..., description="源路径")
    # 目标路径
    target: str = Field(..., description="目标路径")
    # 传输类型（copy、move、link等）
    transtype: str = Field(default="copy", description="传输类型")
    # 传输状态（pending、running、completed、failed）
    status: str = Field(default="pending", description="传输状态")
    # 进度（0-100）
    progress: float = Field(default=0.0, description="进度（0-100）")
    # 传输速度（字节/秒）
    speed: Optional[float] = Field(default=None, description="传输速度（字节/秒）")
    # 已传输大小（字节）
    transferred: Optional[int] = Field(default=None, description="已传输大小（字节）")
    # 总大小（字节）
    total_size: Optional[int] = Field(default=None, description="总大小（字节）")
    # 错误信息
    error: Optional[str] = Field(default=None, description="错误信息")
    # 开始时间
    start_time: Optional[datetime] = Field(default=None, description="开始时间")
    # 完成时间
    end_time: Optional[datetime] = Field(default=None, description="完成时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


# 模型转换工具函数

def cloud_file_info_to_file_item(cloud_file: 'CloudFileInfo', storage: str = "cloud") -> FileItem:
    """
    将CloudFileInfo转换为FileItem
    
    Args:
        cloud_file: CloudFileInfo对象
        storage: 存储类型
    
    Returns:
        FileItem对象
    """
    from pathlib import Path
    
    path_obj = Path(cloud_file.path)
    name = cloud_file.name or path_obj.name
    basename = path_obj.stem
    extension = path_obj.suffix.lstrip('.') if path_obj.suffix else None
    
    modify_time = cloud_file.modified_at.timestamp() if cloud_file.modified_at else None
    create_time = cloud_file.created_at.timestamp() if cloud_file.created_at else None
    
    return FileItem(
        storage=storage,
        type=cloud_file.type,
        path=cloud_file.path,
        name=name,
        basename=basename,
        extension=extension,
        size=cloud_file.size,
        modify_time=modify_time,
        create_time=create_time,
        fileid=cloud_file.id,
        parent_fileid=cloud_file.parent_id,
        thumbnail=cloud_file.thumbnail,
        url=cloud_file.download_url,
        metadata=cloud_file.metadata or {}
    )


def file_item_to_cloud_file_info(file_item: FileItem) -> 'CloudFileInfo':
    """
    将FileItem转换为CloudFileInfo
    
    Args:
        file_item: FileItem对象
    
    Returns:
        CloudFileInfo对象
    """
    from app.core.cloud_storage.providers.base import CloudFileInfo
    from datetime import datetime
    
    modify_time = datetime.fromtimestamp(file_item.modify_time) if file_item.modify_time else None
    create_time = datetime.fromtimestamp(file_item.create_time) if file_item.create_time else None
    
    return CloudFileInfo(
        id=file_item.fileid or file_item.path,
        name=file_item.name or "",
        path=file_item.path or "/",
        size=file_item.size or 0,
        type=file_item.type or "file",
        parent_id=file_item.parent_fileid,
        created_at=create_time,
        modified_at=modify_time,
        thumbnail=file_item.thumbnail,
        download_url=file_item.url,
        metadata=file_item.metadata or {}
    )


def cloud_storage_usage_to_storage_usage(cloud_usage: 'CloudStorageUsage') -> StorageUsage:
    """
    将CloudStorageUsage转换为StorageUsage
    
    Args:
        cloud_usage: CloudStorageUsage对象
    
    Returns:
        StorageUsage对象
    """
    return StorageUsage(
        total=float(cloud_usage.total),
        used=float(cloud_usage.used),
        available=float(cloud_usage.available),
        percentage=cloud_usage.percentage
    )

