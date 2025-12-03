"""
STRM系统配置
"""

import os
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from .file_operation_mode import FileOperationMode, MediaLibraryDestination, STRMSyncConfig


class STRMConfig(BaseModel):
    """STRM系统配置"""
    # 媒体库路径（本地STRM文件存放地址）
    media_library_path: str = Field(
        default='/media_library',
        description="本地STRM文件存放的媒体库地址（可通过前端地址栏输入或点击选择）"
    )
    movie_path: str = Field(
        default='/media_library/Movies',
        description="电影STRM文件存放路径（相对于media_library_path）"
    )
    tv_path: str = Field(
        default='/media_library/TV Shows',
        description="电视剧STRM文件存放路径（相对于media_library_path）"
    )
    anime_path: str = Field(
        default='/media_library/Anime',
        description="动漫STRM文件存放路径（相对于media_library_path）"
    )
    music_path: str = Field(
        default='/media_library/Music',
        description="音乐STRM文件存放路径（相对于media_library_path）"
    )
    other_path: str = Field(
        default='/media_library/Other',
        description="其他类型STRM文件存放路径（相对于media_library_path）"
    )
    
    # 云存储映射
    cloud_storage_mapping: Dict[str, str] = {
        '115': '/115',
        '123': '/123'
    }
    
    # STRM URL生成模式
    # direct: 直接使用115网盘下载地址（简单，无需服务器，但链接可能过期）
    # local_redirect: 使用本地服务重定向（推荐，自动刷新链接，需要本地运行VabHub）
    strm_url_mode: str = Field(
        default='local_redirect',  # 默认使用本地重定向，自动链接刷新，傻瓜式操作
        description="STRM URL生成模式: direct(直接115下载地址) 或 local_redirect(本地重定向，推荐)"
    )
    
    # 本地重定向服务器（仅当strm_url_mode为local_redirect时使用）
    # 内网配置（用于内网访问）
    local_redirect_host: str = Field(
        default='',  # 空字符串表示自动检测内网IP
        description="内网访问主机（空字符串表示自动检测内网IP，例如：192.168.1.100）"
    )
    local_redirect_port: int = Field(
        default=0,  # 0表示使用系统配置的端口
        description="内网访问端口（0表示使用系统配置的端口。常见媒体库默认端口：Emby/Jellyfin: 8096, Plex: 32400）"
    )
    
    # 外网配置（用于外网访问，解决公网IP跳动问题）
    external_redirect_host: str = Field(
        default='',  # 空字符串表示未配置外网访问
        description="外网访问域名（必填，用于外网访问，支持带端口号，例如：vabhub.example.com:8096 或 frp.example.com:6000。注意：如果使用默认端口映射，建议配置为 domain.com:端口号，端口号应与媒体库默认端口一致：Emby/Jellyfin: 8096, Plex: 32400）"
    )
    external_redirect_port: int = Field(
        default=0,  # 0表示从域名中提取或使用默认端口（80/443）
        description="外网访问端口（0表示从域名中提取端口，如果域名中无端口则使用默认端口：HTTP:80, HTTPS:443，或自定义端口。注意：中国大陆家庭宽带默认关闭443和80端口，建议使用自定义端口）"
    )
    use_https: bool = Field(
        default=False,
        description="外网访问是否使用HTTPS（推荐，更安全）"
    )
    
    # 自动适配模式（推荐）
    auto_adapt_network: bool = Field(
        default=True,
        description="自动适配内外网环境（根据请求来源自动选择内网/外网地址，推荐开启）"
    )
    
    local_redirect_base_path: str = Field(
        default='/api/strm/stream',
        description="本地重定向API基础路径"
    )
    
    # JWT配置（仅当strm_url_mode为local_redirect时使用）
    # 默认使用系统配置的JWT密钥，无需重复配置
    jwt_secret: str = Field(
        default='',  # 空字符串表示使用系统配置
        description="JWT签名密钥（空字符串表示使用系统配置的JWT_SECRET_KEY）"
    )
    jwt_algorithm: str = Field(
        default='HS256',
        description="JWT签名算法"
    )
    token_expire_hours: int = Field(
        default=24 * 365,  # 1年
        description="JWT token过期时间（小时）"
    )
    
    # HMAC签名配置（可选，用于增强URL安全性）
    enable_hmac_signature: bool = Field(
        default=False,
        description="启用HMAC URL签名（增强安全性，防止URL滥用）"
    )
    hmac_secret: str = Field(
        default='',  # 空字符串表示使用系统配置
        description="HMAC签名密钥（空字符串表示使用系统配置的STRM_HMAC_SECRET或JWT_SECRET_KEY）"
    )
    hmac_ttl: int = Field(
        default=3600,  # 1小时
        description="HMAC签名URL有效期（秒，默认3600秒=1小时）"
    )
    
    # 115下载地址刷新配置（仅当strm_url_mode为direct时使用）
    refresh_download_url: bool = Field(
        default_factory=lambda: os.getenv('STRM_REFRESH_DOWNLOAD_URL', 'false').lower() == 'true',
        description="是否定期刷新115下载地址（下载地址可能会过期）"
    )
    download_url_refresh_interval_hours: int = Field(
        default=24 * 7,  # 7天
        description="115下载地址刷新间隔（小时）"
    )
    
    # 刮削配置
    scrape_cloud_files: bool = Field(
        default=False,
        description="是否对网盘文件进行刮削（获取元数据、海报等）"
    )
    scrape_local_strm: bool = Field(
        default=True,
        description="是否对本地STRM文件进行刮削（获取元数据、海报等）"
    )
    
    # NFO配置
    generate_nfo: bool = Field(
        default=True,
        description="是否生成NFO文件"
    )
    
    # 字幕配置
    generate_subtitle_files: bool = Field(
        default=True,
        description="是否生成字幕文件"
    )
    # 注意：detect_subtitles_from_cloud 已移除
    # 现在根据 external_redirect_host 是否配置来自动判断
    # 如果配置了外网域名和端口，自动启用从115网盘检测字幕功能
    
    # 媒体服务器配置
    media_servers: List[str] = Field(
        default_factory=list,
        description="媒体服务器列表（['plex', 'jellyfin', 'emby']）"
    )
    auto_refresh: bool = Field(
        default=True,
        description="是否自动刷新媒体服务器"
    )
    refresh_delay: int = Field(
        default=300,
        description="刷新延迟（秒）"
    )
    
    # 服务开关
    enabled: bool = Field(
        default=True,
        description="是否启用STRM系统"
    )
    
    # 同步开关
    periodic_full_sync: bool = Field(
        default=True,
        description="是否启用定期全量同步（定期检查本地STRM文件是否缺失，补全历史文件）"
    )
    
    # 定期全量同步配置
    periodic_full_sync_interval_days: int = Field(
        default=7,  # 默认7天（1周）
        description="定期全量同步间隔（天数），建议3-7天"
    )
    
    # 网盘媒体库路径（用于定期全量同步，只扫描指定路径，降低风控风险）
    cloud_media_library_path: str = Field(
        default='/115/电影',
        description="网盘媒体库路径（只扫描此路径下的文件，不进行全盘扫描，降低风控风险）"
    )


class STRMWorkflowConfig(BaseModel):
    """STRM工作流配置"""
    # 媒体库目的地
    destination: MediaLibraryDestination = MediaLibraryDestination.LOCAL
    
    # 文件操作模式
    operation_mode: FileOperationMode = FileOperationMode.COPY
    
    # 上传配置
    cloud_storage: str = '115'  # 115/123
    cloud_target_path: str = '/电影'  # 云存储目标路径
    rename_on_upload: bool = True  # 上传时重命名
    organize_by_type: bool = True  # 按类型组织
    
    # 字幕配置
    upload_subtitles: bool = True  # 上传字幕文件
    rename_subtitles: bool = True  # 重命名字幕文件
    generate_subtitle_files: bool = True  # 生成字幕文件到STRM目录
    
    # 刮削配置
    scrape_on_cloud: bool = False  # 在网盘进行刮削
    scrape_on_local: bool = True  # 在本地进行刮削
    
    # STRM生成配置（仅当operation_mode为CLOUD_STRM时有效）
    generate_strm: bool = True  # 生成STRM文件
    generate_nfo: bool = True  # 生成NFO文件
    map_cloud_path: bool = True  # 映射云存储路径到本地
    
    # STRM同步配置（仅当operation_mode为CLOUD_STRM时有效）
    strm_sync_config: Optional[STRMSyncConfig] = None
    
    # 媒体服务器配置
    media_servers: List[str] = ['plex', 'jellyfin', 'emby']  # 媒体服务器列表
    auto_refresh: bool = True  # 自动刷新媒体库
    refresh_delay: int = 300  # 刷新延迟（秒）
    
    # 文件树配置
    enable_file_tree: bool = True  # 启用文件树管理
    enable_incremental: bool = True  # 启用增量更新
    overwrite_mode: str = 'never'  # 覆盖模式：never/always/smart
    
    # 文件操作配置
    delete_source: bool = False  # 是否删除源文件（仅当operation_mode为MOVE或CLOUD_MOVE时有效）
    keep_seeding: bool = True  # 是否保留做种（仅当operation_mode为COPY或SYMLINK或HARDLINK时有效）

