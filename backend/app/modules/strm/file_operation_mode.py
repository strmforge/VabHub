"""
文件操作模式定义
文件处理模式
"""

from enum import Enum
from typing import Optional, Dict, Any, TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from typing import ForwardRef


class FileOperationMode(str, Enum):
    """文件操作模式"""
    COPY = "copy"  # 复制
    MOVE = "move"  # 移动
    LINK = "link"  # 硬链接（仅本地存储到本地存储）
    SOFTLINK = "softlink"  # 软链接（仅本地存储到本地存储）


class MediaLibraryDestination(str, Enum):
    """媒体库目的地类型"""
    LOCAL = "local"  # 本地
    CLOUD = "cloud"  # 网盘


class FileOperationConfig(BaseModel):
    """文件操作配置"""
    # 操作名称（可选，用于显示）
    name: Optional[str] = None
    
    # 源存储类型
    source_storage: str = "local"  # local/115/123等
    
    # 目标存储类型
    target_storage: str = "local"  # local/115/123等
    
    # 文件操作模式
    operation_mode: FileOperationMode = FileOperationMode.COPY
    
    # 源文件路径
    source_path: str
    
    # 目标路径
    target_path: str
    
    # 覆盖模式（never/always/size/latest）
    overwrite_mode: str = "never"
    
    # 是否删除源文件（仅当operation_mode为MOVE时有效）
    delete_source: bool = True
    
    # 是否保留做种（仅当operation_mode为COPY或LINK或SOFTLINK时有效）
    keep_seeding: bool = True
    
    # STRM配置（仅当目标存储为网盘时有效）
    strm_config: Optional["STRMConfigForOperation"] = None


class STRMConfigForOperation(BaseModel):
    """文件操作中的STRM配置（简化版，用于文件操作模式选择）"""
    # 是否启用STRM功能
    enabled: bool = Field(
        default=False,
        description="是否启用STRM功能"
    )
    
    # STRM本地媒体库地址（本地STRM文件存放地址）
    media_library_path: str = Field(
        default='/media_library',
        description="本地STRM文件存放的媒体库地址（可通过前端地址栏输入或点击选择）"
    )
    
    # STRM文件生成设置
    generate_nfo: bool = Field(
        default=True,
        description="是否生成NFO文件"
    )
    
    generate_subtitle_files: bool = Field(
        default=True,
        description="是否生成字幕文件"
    )
    
    # 刮削设置
    scrape_cloud_files: bool = Field(
        default=False,
        description="是否对网盘文件进行刮削（获取元数据、海报等）"
    )
    
    scrape_local_strm: bool = Field(
        default=True,
        description="是否对本地STRM文件进行刮削（获取元数据、海报等）"
    )


class STRMSyncConfig(BaseModel):
    """STRM同步配置"""
    # STRM本地媒体库地址（本地STRM文件存放地址）
    strm_library_path: str = Field(
        ...,
        description="本地STRM文件存放的媒体库地址（可通过前端地址栏输入或点击选择）"
    )
    
    # 是否启用自动同步
    auto_sync: bool = True
    
    # 首次同步模式（全量/增量）
    first_sync_mode: str = "full"  # full/incremental
    
    # 同步间隔（秒）
    sync_interval: int = 300  # 5分钟
    
    # 实时对比（利用115网盘开发者权限）
    realtime_compare: bool = True
    
    # 对比间隔（秒）
    compare_interval: int = 60  # 1分钟
    
    # 网盘删除自动删除本地STRM文件
    auto_delete_on_cloud_delete: bool = True
    
    # 同步文件类型
    sync_file_types: list = [".mkv", ".mp4", ".avi", ".mov", ".flv", ".wmv"]
    
    # 排除路径
    exclude_paths: list = []
    
    # 包含路径
    include_paths: list = []
    
    # 网盘媒体库路径（用于定期全量同步，只扫描指定路径，降低风控风险）
    cloud_media_library_path: str = Field(
        default='/115/电影',
        description="网盘媒体库路径（只扫描此路径下的文件，不进行全盘扫描，降低风控风险）"
    )
    
    # 定期全量同步间隔（天数）
    periodic_full_sync_interval_days: int = Field(
        default=7,  # 默认7天（1周）
        description="定期全量同步间隔（天数），建议3-7天"
    )


def get_available_modes(source_storage: str, target_storage: str) -> list[FileOperationMode]:
    """
    获取可用的文件操作模式
    
    Args:
        source_storage: 源存储类型（local/115/123等）
        target_storage: 目标存储类型（local/115/123等）
    
    Returns:
        可用的文件操作模式列表
    """
    # 本地存储到本地存储：支持所有模式
    if source_storage == "local" and target_storage == "local":
        return [
            FileOperationMode.COPY,
            FileOperationMode.MOVE,
            FileOperationMode.LINK,
            FileOperationMode.SOFTLINK
        ]
    # 其他情况（本地到云存储、云存储到本地、云存储到云存储）：只支持复制和移动
    else:
        return [
            FileOperationMode.COPY,
            FileOperationMode.MOVE
        ]


def validate_operation_mode(
    source_storage: str,
    target_storage: str,
    operation_mode: FileOperationMode
) -> bool:
    """
    验证文件操作模式是否适用于指定的存储类型
    
    Args:
        source_storage: 源存储类型（local/115/123等）
        target_storage: 目标存储类型（local/115/123等）
        operation_mode: 文件操作模式
    
    Returns:
        是否有效
    """
    available_modes = get_available_modes(source_storage, target_storage)
    return operation_mode in available_modes

