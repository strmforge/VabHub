"""
STRM文件生成器
生成STRM文件、NFO文件和字幕文件
支持直接使用115网盘下载地址（无需域名和服务器）
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
from jose import jwt

from .config import STRMConfig


class STRMGenerator:
    """STRM文件生成器"""
    
    def __init__(self, config: STRMConfig, db: Optional[Any] = None):
        """
        初始化STRM生成器
        
        Args:
            config: STRM配置
            db: 数据库会话（可选，用于获取115 API客户端和生命周期追踪）
        """
        self.config = config
        self.media_library_path = Path(config.media_library_path)
        self.cloud_storage_mapping = config.cloud_storage_mapping
        self.db = db
        self._strm_service: Optional[Any] = None
        self._lifecycle_tracker: Optional[Any] = None
        
        # 初始化生命周期追踪器（如果提供了数据库会话）
        if self.db:
            from .lifecycle_tracker import LifecycleTracker
            self._lifecycle_tracker = LifecycleTracker(self.db)
    
    async def generate_strm_file(
        self,
        media_info: Dict[str, Any],
        cloud_file_id: str,
        cloud_storage: str,
        cloud_path: str,
        subtitle_files: Optional[List[str]] = None,
        cloud_115_api: Optional[Any] = None  # Cloud115API客户端（可选，如果为None则自动获取）
    ) -> Dict[str, Any]:
        """
        生成STRM文件
        
        Args:
            media_info: 媒体信息
            cloud_file_id: 云存储文件ID（对于115网盘，这是pick_code）
            cloud_storage: 云存储类型（115/123）
            cloud_path: 云存储路径
            subtitle_files: 字幕文件列表（云存储路径）
            cloud_115_api: 115网盘API客户端（可选，如果为None且需要时，会从系统自动获取）
        
        Returns:
            生成的文件路径字典
        """
        # 如果没有提供115 API客户端，且需要时，从系统获取
        if not cloud_115_api and cloud_storage == '115':
            # 如果启用从115网盘检测字幕，或者使用direct模式，需要API客户端
            if self.config.detect_subtitles_from_cloud or self.config.strm_url_mode == 'direct':
                cloud_115_api = await self._get_115_api_client()
        
        # 1. 构建本地媒体库路径（对应网盘目录结构）
        local_path = self._build_local_path(media_info, cloud_path)
        
        # 2. 生成STRM文件
        strm_path = await self._generate_strm(
            local_path, cloud_file_id, cloud_storage, media_info, cloud_115_api
        )
        
        # 3. 处理字幕文件
        subtitle_paths = []
        cloud_subtitle_info = []  # 115网盘字幕信息（用于外网播放）
        
        if self.config.generate_subtitle_files:
            # 判断是否启用从115网盘检测字幕
            # 如果配置了外网域名和端口，说明需要外网播放功能，自动启用从115网盘检测字幕
            detect_from_cloud = bool(self.config.external_redirect_host) and cloud_storage == '115' and cloud_115_api
            
            if detect_from_cloud:
                # 从115网盘获取字幕列表
                cloud_subtitle_info = await self._detect_subtitles_from_115(
                    cloud_file_id, cloud_115_api
                )
                # 下载字幕到本地STRM目录（供本地播放使用）
                if cloud_subtitle_info:
                    subtitle_paths = await self._download_subtitles_from_115_to_local(
                        local_path, cloud_subtitle_info, media_info, cloud_115_api
                    )
            # 如果提供了字幕文件列表，且未启用从115网盘检测，则下载到本地
            elif subtitle_files:
                subtitle_paths = await self._generate_subtitle_files(
                    local_path, subtitle_files, media_info, cloud_115_api
                )
        
        # 4. 生成NFO文件
        nfo_path = None
        if self.config.generate_nfo:
            nfo_path = await self._generate_nfo(local_path, media_info)
        
        return {
            'strm_path': strm_path,
            'subtitle_paths': subtitle_paths,
            'cloud_subtitle_info': cloud_subtitle_info,  # 115网盘字幕信息
            'nfo_path': nfo_path
        }
    
    async def _get_115_api_client(self) -> Optional[Any]:
        """
        从系统获取115网盘API客户端（使用系统认证）
        
        Returns:
            Cloud115API客户端实例，如果获取失败则返回None
        """
        if not self.db:
            logger.warning("未提供数据库会话，无法获取115 API客户端")
            return None
        
        try:
            # 延迟导入避免循环依赖
            from app.modules.strm.service import STRMService
            
            if not self._strm_service:
                self._strm_service = STRMService(self.db)
            
            api_client = await self._strm_service.get_115_api_client()
            return api_client
        except Exception as e:
            logger.error(f"获取115 API客户端失败: {e}")
            return None
    
    def _build_local_path(
        self,
        media_info: Dict[str, Any],
        cloud_path: str
    ) -> Path:
        """
        构建本地媒体库路径（对应网盘目录结构）
        
        例如：
        云存储路径：/115/电影/xxx (2023)/xxx (2023).mkv
        本地路径：/media_library/Movies/xxx (2023)/xxx (2023).strm
        """
        media_type = media_info.get('type', 'movie')
        
        # 根据媒体类型选择基础路径
        if media_type == 'movie':
            base_path = Path(self.config.movie_path)
        elif media_type == 'tv' or media_type == 'tv_series':
            base_path = Path(self.config.tv_path)
        elif media_type == 'anime':
            base_path = Path(self.config.anime_path)
        elif media_type == 'music' or media_type == 'audio':
            # 音乐：使用music_path或默认路径
            base_path = Path(getattr(self.config, 'music_path', self.config.media_library_path / 'Music'))
        else:
            base_path = Path(self.config.other_path)
        
        # 从云存储路径提取相对路径
        # 例如：/115/电影/xxx (2023)/xxx (2023).mkv
        # 提取：xxx (2023)/
        relative_path = self._extract_relative_path(cloud_path, media_type)
        
        # 构建完整路径
        local_path = base_path / relative_path
        
        return local_path
    
    def _extract_relative_path(self, cloud_path: str, media_type: str) -> str:
        """从云存储路径提取相对路径"""
        # 移除云存储前缀（例如：/115/电影/）
        # 提取相对路径（例如：xxx (2023)/）
        
        # 移除开头的云存储标识
        for storage, prefix in self.cloud_storage_mapping.items():
            if cloud_path.startswith(prefix):
                cloud_path = cloud_path[len(prefix):].lstrip('/')
                break
        
        # 移除媒体类型前缀（例如：电影/、电视剧/、音乐/）
        type_prefixes = ['电影/', '电视剧/', 'TV Shows/', 'Movies/', 'Anime/', '音乐/', 'Music/']
        for prefix in type_prefixes:
            if cloud_path.startswith(prefix):
                cloud_path = cloud_path[len(prefix):]
                break
        
        # 提取目录部分（去除文件名）
        path_parts = cloud_path.split('/')
        if len(path_parts) > 1:
            # 有目录结构
            directory = '/'.join(path_parts[:-1])
            return directory
        else:
            # 只有文件名，使用媒体信息构建目录
            if media_type == 'movie':
                title = path_parts[0].split('.')[0]  # 移除扩展名
                return title
            elif media_type == 'music' or media_type == 'audio':
                # 音乐：使用Artist/Album结构
                artist = media_info.get('artist', 'Unknown Artist')
                album = media_info.get('album', 'Unknown Album')
                if album and album != 'Unknown Album':
                    return f"{artist}/{album}"
                else:
                    return artist
            else:
                return path_parts[0].split('.')[0]
    
    async def _generate_strm(
        self,
        local_path: Path,
        cloud_file_id: str,
        cloud_storage: str,
        media_info: Dict[str, Any],
        cloud_115_api: Optional[Any] = None
    ) -> str:
        """生成STRM文件"""
        # 构建STRM文件路径
        strm_filename = self._generate_strm_filename(media_info, local_path)
        strm_path = local_path.parent / strm_filename
        
        # 确保目录存在
        strm_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 生成STRM文件URL（智能适配内外网）
        strm_url = await self._generate_strm_url(cloud_file_id, cloud_storage, cloud_115_api, request)
        
        # 生成STRM文件内容（包含元数据注释）
        strm_content = self._generate_strm_content(strm_url, media_info, cloud_file_id, cloud_storage)
        
        # 写入STRM文件
        with open(strm_path, 'w', encoding='utf-8') as f:
            f.write(strm_content)
        
        logger.info(f"生成STRM文件: {strm_path} -> {strm_url[:80]}...")
        return str(strm_path)
    
    def _generate_strm_filename(
        self,
        media_info: Dict[str, Any],
        local_path: Path
    ) -> str:
        """生成STRM文件名"""
        media_type = media_info.get('type', 'movie')
        
        if media_type == 'movie':
            # 电影：Title (Year).strm
            title = media_info.get('title', 'unknown')
            year = media_info.get('year', '')
            filename = f"{title} ({year}).strm" if year else f"{title}.strm"
        elif media_type == 'tv' or media_type == 'tv_series':
            # 电视剧：Title - S01E01.strm
            title = media_info.get('title', 'unknown')
            season = media_info.get('season', 1)
            episode = media_info.get('episode', 1)
            filename = f"{title} - S{season:02d}E{episode:02d}.strm"
        elif media_type == 'music' or media_type == 'audio':
            # 音乐：Artist - Title.strm 或 Album/Artist - Title.strm
            artist = media_info.get('artist', 'Unknown Artist')
            title = media_info.get('title', 'Unknown Title')
            album = media_info.get('album')
            track_number = media_info.get('track_number') or media_info.get('track')
            
            if album and album != 'Unknown Album':
                # 如果有专辑信息，使用：Artist - Album - TrackNumber - Title.strm
                if track_number:
                    filename = f"{artist} - {album} - {track_number:02d} - {title}.strm"
                else:
                    filename = f"{artist} - {album} - {title}.strm"
            else:
                # 没有专辑信息，使用：Artist - Title.strm
                filename = f"{artist} - {title}.strm"
        else:
            # 其他：使用原文件名
            filename = local_path.stem + '.strm'
        
        # 清理文件名中的非法字符
        filename = self._sanitize_filename(filename)
        
        return filename
    
    async def _generate_strm_url(
        self,
        cloud_file_id: str,
        cloud_storage: str,
        cloud_115_api: Optional[Any] = None,
        request: Optional[Any] = None
    ) -> str:
        """
        生成STRM文件URL（智能适配内外网环境）
        
        根据配置模式生成URL：
        - direct: 直接使用115网盘下载地址（无需服务器，推荐）
        - local_redirect: 使用本地服务重定向（智能适配内外网，推荐）
        
        Args:
            cloud_file_id: 云存储文件ID
            cloud_storage: 云存储类型
            cloud_115_api: 115网盘API客户端
            request: FastAPI请求对象（用于智能适配）
        """
        if self.config.strm_url_mode == 'direct':
            # 直接使用115网盘下载地址
            return await self._get_direct_download_url(cloud_file_id, cloud_storage, cloud_115_api)
        else:
            # 使用本地服务重定向（智能适配内外网）
            return self._get_local_redirect_url(cloud_file_id, cloud_storage, request)
    
    async def _get_direct_download_url(
        self,
        cloud_file_id: str,
        cloud_storage: str,
        cloud_115_api: Optional[Any] = None
    ) -> str:
        """
        获取115网盘直接下载地址
        
        Args:
            cloud_file_id: 115网盘文件pick_code
            cloud_storage: 云存储类型（115）
            cloud_115_api: 115网盘API客户端
        
        Returns:
            115网盘下载地址
        """
        if cloud_storage != '115':
            logger.warning(f"直接下载地址模式仅支持115网盘，当前存储类型: {cloud_storage}")
            # 回退到本地重定向模式
            return self._get_local_redirect_url(cloud_file_id, cloud_storage)
        
        if not cloud_115_api:
            logger.warning("未提供115网盘API客户端，无法获取直接下载地址，使用本地重定向模式")
            return self._get_local_redirect_url(cloud_file_id, cloud_storage)
        
        try:
            # 调用115网盘API获取下载地址
            result = await cloud_115_api.get_download_url(pick_code=cloud_file_id)
            
            if result.get("success"):
                download_url = result.get("download_url")
                if download_url:
                    logger.info(f"获取115网盘下载地址成功: pick_code={cloud_file_id}")
                    return download_url
                else:
                    logger.warning(f"115网盘下载地址为空: pick_code={cloud_file_id}")
            else:
                error_msg = result.get("error", "未知错误")
                logger.error(f"获取115网盘下载地址失败: {error_msg}")
        except Exception as e:
            logger.error(f"获取115网盘下载地址异常: {e}")
        
        # 如果获取失败，回退到本地重定向模式
        logger.warning(f"无法获取115网盘直接下载地址，回退到本地重定向模式")
        return self._get_local_redirect_url(cloud_file_id, cloud_storage, None)
    
    def _get_local_redirect_url(
        self, 
        cloud_file_id: str, 
        cloud_storage: str,
        request: Optional[Any] = None
    ) -> str:
        """
        生成本地重定向URL（智能适配内外网环境）
        
        Args:
            cloud_file_id: 云存储文件ID（pick_code）
            cloud_storage: 云存储类型（115/123）
            request: FastAPI请求对象（可选，用于检测请求来源）
        
        Returns:
            本地重定向URL（自动适配内外网，可选HMAC签名）
        """
        # 生成JWT token
        token = self._generate_jwt_token(cloud_file_id, cloud_storage)
        
        # 智能选择主机和端口（根据配置和请求来源）
        host, port, protocol = self._get_smart_redirect_address(request)
        base_path = self.config.local_redirect_base_path
        
        # 构建基础URL
        base_url = f"{protocol}://{host}:{port}{base_path}/{cloud_storage}/{token}"
        
        # 如果启用了HMAC签名，添加签名参数
        if self.config.enable_hmac_signature:
            from .hmac_signer import get_hmac_signer
            
            # 构建路径（用于签名）
            path = f"{base_path}/{cloud_storage}/{token}"
            
            # 生成HMAC签名URL
            hmac_signer = get_hmac_signer(self.config.hmac_secret or None)
            signed_url, timestamp, signature = hmac_signer.generate_signed_url(
                path=path,
                ttl=self.config.hmac_ttl,
                base_url=f"{protocol}://{host}:{port}"
            )
            
            logger.debug(f"生成HMAC签名URL: {signed_url[:80]}...")
            return signed_url
        
        return base_url
    
    def _get_smart_redirect_address(
        self, 
        request: Optional[Any] = None
    ) -> tuple[str, int, str]:
        """
        智能获取重定向地址（自动适配内外网环境）
        
        策略：
        1. 如果启用了自动适配，根据请求来源选择内网/外网地址
        2. 如果配置了外网域名，优先使用外网地址（解决公网IP跳动问题）
        3. 否则使用内网地址
        
        Args:
            request: FastAPI请求对象（可选，用于检测请求来源）
        
        Returns:
            (host, port, protocol) 元组
        """
        # 如果启用了自动适配，尝试根据请求来源选择
        if self.config.auto_adapt_network and request:
            # 检测请求来源
            is_external = self._is_external_request(request)
            
            if is_external and self.config.external_redirect_host:
                # 外网请求，使用外网域名
                host = self._get_external_host()  # 获取主机（去除端口）
                port = self._get_external_port()  # 获取端口（从配置或域名中提取）
                protocol = "https" if self.config.use_https else "http"
                
                # 构建完整URL（如果端口是80/443且使用默认协议，可以不显示端口）
                # 但为了兼容性，始终显示端口
                logger.info(f"检测到外网请求，使用外网地址: {protocol}://{host}:{port}")
                return (host, port, protocol)
        
        # 内网请求或未配置外网域名，使用内网地址
        host = self._get_internal_host()
        port = self._get_internal_port()
        protocol = "http"  # 内网通常使用HTTP
        logger.info(f"使用内网地址: {protocol}://{host}:{port}")
        return (host, port, protocol)
    
    def _is_external_request(self, request: Any) -> bool:
        """
        检测是否为外网请求
        
        Args:
            request: FastAPI请求对象
        
        Returns:
            是否为外网请求
        """
        try:
            # 获取客户端IP
            client_ip = request.client.host if request.client else None
            if not client_ip:
                return False
            
            # 判断是否为内网IP
            import ipaddress
            try:
                ip = ipaddress.ip_address(client_ip)
                is_private = ip.is_private
                return not is_private  # 不是内网IP就是外网请求
            except ValueError:
                # 不是IP地址，可能是域名，默认认为是外网
                return True
        except Exception as e:
            logger.warning(f"检测请求来源失败: {e}")
            return False
    
    def _get_internal_host(self) -> str:
        """
        获取内网主机地址
        
        Returns:
            内网主机地址
        """
        # 如果配置了内网主机，直接使用
        if self.config.local_redirect_host:
            return self.config.local_redirect_host
        
        # 自动检测内网IP
        try:
            from app.utils.network import get_local_ip
            local_ip = get_local_ip()
            if local_ip:
                logger.info(f"自动检测到内网IP: {local_ip}")
                return local_ip
        except Exception as e:
            logger.warning(f"自动检测内网IP失败: {e}")
        
        # 如果检测失败，使用localhost
        logger.warning("使用localhost作为内网主机（可能无法从其他设备访问）")
        return "localhost"
    
    def _get_internal_port(self) -> int:
        """
        获取内网端口
        
        Returns:
            内网端口号
        """
        # 如果配置了内网端口，直接使用
        if self.config.local_redirect_port > 0:
            return self.config.local_redirect_port
        
        # 使用系统配置的端口
        try:
            from app.core.config import settings
            port = settings.PORT
            logger.info(f"使用系统配置的内网端口: {port}")
            return port
        except Exception as e:
            logger.warning(f"获取系统端口失败: {e}，使用默认端口8000")
            return 8000
    
    def _get_external_port(self) -> int:
        """
        获取外网端口（支持从域名中提取端口号）
        
        优先级：
        1. 配置的external_redirect_port（如果>0）
        2. 从域名中提取的端口号（如果域名包含端口）
        3. 默认端口（HTTPS:443, HTTP:80）
        
        Returns:
            外网端口号
        """
        # 如果配置了外网端口，直接使用
        if self.config.external_redirect_port > 0:
            return self.config.external_redirect_port
        
        # 尝试从域名中提取端口号（支持格式：domain.com:6000）
        host = self.config.external_redirect_host
        if host and ':' in host:
            try:
                # 提取端口号（例如：vabhub.example.com:6000 -> 6000）
                port_str = host.split(':')[-1]
                port = int(port_str)
                if 1 <= port <= 65535:
                    logger.info(f"从域名中提取端口号: {port}")
                    return port
            except (ValueError, IndexError):
                logger.warning(f"无法从域名中提取端口号: {host}")
        
        # 根据HTTPS选择默认端口
        if self.config.use_https:
            return 443
        else:
            return 80
    
    def _get_external_host(self) -> str:
        """
        获取外网主机（去除端口号，如果域名中包含端口）
        
        Returns:
            外网主机地址（不含端口）
        """
        host = self.config.external_redirect_host
        if not host:
            return ""
        
        # 如果域名中包含端口号，提取主机部分
        if ':' in host:
            # 提取主机部分（例如：vabhub.example.com:6000 -> vabhub.example.com）
            host_part = host.rsplit(':', 1)[0]
            logger.info(f"从域名中提取主机部分: {host_part}")
            return host_part
        
        return host
    
    def _generate_jwt_token(self, pick_code: str, storage_type: str) -> str:
        """
        生成JWT token（用于本地重定向）
        
        Args:
            pick_code: 文件提取码
            storage_type: 云存储类型
        
        Returns:
            JWT token字符串
        """
        # 获取JWT密钥（使用系统配置）
        jwt_secret = self._get_jwt_secret()
        jwt_algorithm = self.config.jwt_algorithm
        
        # 构建payload
        payload = {
            "pick_code": pick_code,
            "storage_type": storage_type,
            "file_type": "video",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=self.config.token_expire_hours)
        }
        
        # 生成token
        token = jwt.encode(payload, jwt_secret, algorithm=jwt_algorithm)
        return token
    
    def _get_jwt_secret(self) -> str:
        """
        获取JWT密钥（使用系统配置）
        
        Returns:
            JWT密钥
        """
        # 如果配置了JWT密钥，直接使用
        if self.config.jwt_secret:
            return self.config.jwt_secret
        
        # 使用系统配置的JWT密钥（动态获取，首次启动时自动生成）
        try:
            from app.core.config import settings
            jwt_secret = settings.JWT_SECRET_KEY_DYNAMIC
            if jwt_secret and jwt_secret != "change-this-to-a-random-jwt-secret-key-in-production":
                return jwt_secret
        except Exception as e:
            logger.warning(f"获取系统JWT密钥失败: {e}")
        
        # 如果都获取失败，使用默认值（不推荐，但至少可以工作）
        logger.warning("使用默认JWT密钥，建议配置系统JWT_SECRET_KEY")
        return "your-secret-key-change-in-production"
    
    def _generate_strm_content(
        self,
        strm_url: str,
        media_info: Dict[str, Any],
        cloud_file_id: str,
        cloud_storage: str
    ) -> str:
        """生成STRM文件内容（包含元数据注释）"""
        # 构建元数据
        metadata = {
            'file_id': cloud_file_id,
            'provider': cloud_storage,
            'media_type': media_info.get('type', 'movie'),
            'title': media_info.get('title', ''),
            'year': media_info.get('year'),
            'season': media_info.get('season'),
            'episode': media_info.get('episode')
        }
        
        # 生成STRM文件内容
        import json
        metadata_json = json.dumps(metadata, ensure_ascii=False, indent=2)
        
        strm_content = f"""# VabHub STRM Metadata
# {metadata_json}
{strm_url}
"""
        
        return strm_content
    
    async def _generate_subtitle_files(
        self,
        local_path: Path,
        subtitle_files: List[str],
        media_info: Dict[str, Any],
        cloud_115_api: Optional[Any] = None
    ) -> List[str]:
        """
        生成字幕文件到STRM目录
        
        字幕文件处理逻辑：
        1. 字幕文件已经在网盘中（和视频文件一起上传、重命名、分类）
        2. 直接从网盘下载字幕文件到本地STRM目录
        3. 字幕文件通常很小，直接下载即可
        """
        subtitle_paths = []
        strm_dir = local_path.parent
        
        # 如果没有115 API客户端，无法下载字幕文件
        if not cloud_115_api:
            logger.warning("未提供115 API客户端，跳过字幕文件下载")
            return subtitle_paths
        
        for subtitle_file in subtitle_files:
            try:
                # subtitle_file可能是云存储路径或pick_code
                # 如果是路径，需要先获取文件信息得到pick_code
                # 如果是pick_code，直接使用
                
                # 尝试从路径中提取pick_code（如果路径格式包含pick_code）
                pick_code = self._extract_pick_code_from_path(subtitle_file)
                
                # 如果无法提取pick_code，尝试通过路径获取文件信息
                if not pick_code:
                    # 这里需要根据实际路径格式来获取pick_code
                    # 暂时假设subtitle_file就是pick_code或包含pick_code的路径
                    logger.warning(f"无法从路径提取pick_code: {subtitle_file}")
                    continue
                
                # 从云存储下载字幕文件
                subtitle_name = Path(subtitle_file).name
                local_subtitle_path = strm_dir / subtitle_name
                
                # 下载字幕文件
                success = await self._download_subtitle_from_cloud(
                    cloud_115_api, pick_code, local_subtitle_path
                )
                
                if success:
                    subtitle_paths.append(str(local_subtitle_path))
                    logger.info(f"下载字幕文件成功: {local_subtitle_path}")
                else:
                    logger.warning(f"下载字幕文件失败: {subtitle_file}")
                    
            except Exception as e:
                logger.error(f"处理字幕文件时出错 {subtitle_file}: {e}")
                continue
        
        return subtitle_paths
    
    async def _detect_subtitles_from_115(
        self,
        video_pick_code: str,
        cloud_115_api: Any
    ) -> List[Dict[str, Any]]:
        """
        从115网盘检测视频字幕列表
        
        Args:
            video_pick_code: 视频文件的pick_code
            cloud_115_api: 115网盘API客户端
        
        Returns:
            字幕信息列表，每个字幕包含：
            - pick_code: 字幕文件pick_code
            - language: 语言
            - title: 字幕标题
            - file_name: 文件名
            - url: 字幕文件地址（如果有）
        """
        try:
            # 调用115 API获取视频字幕列表
            result = await cloud_115_api.get_video_subtitle_list(pick_code=video_pick_code)
            
            if not result.get("success"):
                logger.warning(f"获取视频字幕列表失败: {result.get('error', '未知错误')}")
                return []
            
            subtitle_list = result.get("list", [])
            logger.info(f"从115网盘检测到 {len(subtitle_list)} 个字幕文件: {video_pick_code}")
            
            # 提取字幕信息
            subtitle_info = []
            for subtitle in subtitle_list:
                # 优先使用外挂字幕的pick_code，如果没有则使用内置字幕的url
                subtitle_pick_code = subtitle.get("pick_code")
                if not subtitle_pick_code:
                    # 内置字幕可能只有url，没有pick_code
                    subtitle_url = subtitle.get("url")
                    if subtitle_url:
                        # 尝试从url中提取pick_code，或者使用video_pick_code
                        subtitle_pick_code = video_pick_code
                
                if subtitle_pick_code:
                    subtitle_info.append({
                        "pick_code": subtitle_pick_code,
                        "language": subtitle.get("language", "unknown"),
                        "title": subtitle.get("title", ""),
                        "file_name": subtitle.get("file_name", ""),
                        "url": subtitle.get("url", ""),
                        "type": subtitle.get("type", ""),
                        "sid": subtitle.get("sid", "")
                    })
            
            return subtitle_info
            
        except Exception as e:
            logger.error(f"从115网盘检测字幕时出错: {e}")
            return []
    
    async def _download_subtitles_from_115_to_local(
        self,
        local_path: Path,
        cloud_subtitle_info: List[Dict[str, Any]],
        media_info: Dict[str, Any],
        cloud_115_api: Any
    ) -> List[str]:
        """
        从115网盘下载字幕到本地STRM目录（供本地播放使用）
        
        同时记录115网盘字幕信息（供外网播放API使用）
        
        Args:
            local_path: 本地STRM文件路径
            cloud_subtitle_info: 115网盘字幕信息列表
            media_info: 媒体信息
            cloud_115_api: 115网盘API客户端
        
        Returns:
            下载成功的字幕文件路径列表
        """
        subtitle_paths = []
        strm_dir = local_path.parent
        base_name = local_path.stem
        
        for subtitle_info in cloud_subtitle_info:
            try:
                pick_code = subtitle_info.get("pick_code")
                if not pick_code:
                    continue
                
                # 确定字幕文件名
                # 优先使用115返回的文件名，否则根据语言生成
                subtitle_name = subtitle_info.get("file_name", "")
                if not subtitle_name:
                    # 根据语言生成文件名
                    language = subtitle_info.get("language", "unknown")
                    # 确定字幕扩展名（从type或默认.srt）
                    subtitle_type = subtitle_info.get("type", "").lower()
                    if "ass" in subtitle_type:
                        ext = ".ass"
                    elif "ssa" in subtitle_type:
                        ext = ".ssa"
                    elif "vtt" in subtitle_type:
                        ext = ".vtt"
                    else:
                        ext = ".srt"
                    
                    subtitle_name = f"{base_name}.{language}{ext}"
                
                # 确保文件名在STRM目录中
                if "/" in subtitle_name or "\\" in subtitle_name:
                    subtitle_name = Path(subtitle_name).name
                
                local_subtitle_path = strm_dir / subtitle_name
                
                # 下载字幕文件
                success = await self._download_subtitle_from_cloud(
                    cloud_115_api, pick_code, local_subtitle_path
                )
                
                if success:
                    subtitle_paths.append(str(local_subtitle_path))
                    logger.info(f"下载115网盘字幕到本地成功: {local_subtitle_path}")
                else:
                    logger.warning(f"下载115网盘字幕失败: {subtitle_name} (pick_code: {pick_code})")
                    
            except Exception as e:
                logger.error(f"处理115网盘字幕时出错: {e}")
                continue
        
        return subtitle_paths
    
    def _extract_pick_code_from_path(self, path: str) -> Optional[str]:
        """
        从路径中提取pick_code
        
        支持格式：
        - 直接是pick_code: "cg16zx93h3xy6ddf1"
        - 包含pick_code的路径: "/path/to/file.pick_code.srt"
        - 115网盘路径格式: 需要根据实际情况解析
        """
        # 如果路径看起来就是pick_code（15位字母数字）
        if len(path) == 15 and path.isalnum():
            return path
        
        # 尝试从路径中提取pick_code（15位字母数字）
        import re
        match = re.search(r'([a-z0-9]{15})', path, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    async def _download_subtitle_from_cloud(
        self,
        cloud_115_api: Any,
        pick_code: str,
        local_path: Path
    ) -> bool:
        """
        从115网盘下载字幕文件到本地
        
        Args:
            cloud_115_api: 115网盘API客户端
            pick_code: 字幕文件的pick_code
            local_path: 本地保存路径
        
        Returns:
            是否下载成功
        """
        try:
            # 获取下载地址
            result = await cloud_115_api.get_download_url(pick_code=pick_code)
            
            if not result.get("success"):
                logger.error(f"获取字幕文件下载地址失败: {result.get('message', '未知错误')}")
                return False
            
            download_url = result.get("download_url")
            if not download_url:
                logger.error("字幕文件下载地址为空")
                return False
            
            # 下载文件
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(download_url)
                response.raise_for_status()
                
                # 保存到本地
                local_path.parent.mkdir(parents=True, exist_ok=True)
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"字幕文件下载成功: {local_path} ({len(response.content)} bytes)")
                return True
                
        except Exception as e:
            logger.error(f"下载字幕文件时出错: {e}")
            return False
    
    async def _generate_nfo(
        self,
        local_path: Path,
        media_info: Dict[str, Any]
    ) -> str:
        """生成NFO文件"""
        nfo_path = local_path.parent / f"{local_path.stem}.nfo"
        
        media_type = media_info.get('type', 'movie')
        
        if media_type == 'movie':
            nfo_content = self._generate_movie_nfo(media_info)
        elif media_type == 'tv' or media_type == 'tv_series':
            nfo_content = self._generate_tv_nfo(media_info)
        else:
            return None
        
        # 写入NFO文件
        with open(nfo_path, 'w', encoding='utf-8') as f:
            f.write(nfo_content)
        
        logger.info(f"生成NFO文件: {nfo_path}")
        return str(nfo_path)
    
    def _generate_movie_nfo(self, media_info: Dict[str, Any]) -> str:
        """生成电影NFO文件内容"""
        title = media_info.get('title', '')
        year = media_info.get('year', '')
        overview = media_info.get('overview', '')
        runtime = media_info.get('runtime', 0)
        rating = media_info.get('rating', 0.0)
        genres = media_info.get('genres', [])
        
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<movie>
    <title>{title}</title>
    <year>{year}</year>
    <plot>{overview}</plot>
    <runtime>{runtime}</runtime>
    <rating>{rating}</rating>
    <genre>{'/'.join(genres)}</genre>
</movie>"""
    
    def _generate_tv_nfo(self, media_info: Dict[str, Any]) -> str:
        """生成电视剧NFO文件内容"""
        title = media_info.get('title', '')
        show_title = media_info.get('show_title', title)
        season = media_info.get('season', 1)
        episode = media_info.get('episode', 1)
        overview = media_info.get('overview', '')
        runtime = media_info.get('runtime', 0)
        rating = media_info.get('rating', 0.0)
        
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<episodedetails>
    <title>{title}</title>
    <showtitle>{show_title}</showtitle>
    <season>{season}</season>
    <episode>{episode}</episode>
    <plot>{overview}</plot>
    <runtime>{runtime}</runtime>
    <rating>{rating}</rating>
</episodedetails>"""
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名中的非法字符"""
        # Windows非法字符
        illegal_chars = r'[<>:"/\\|?*]'
        filename = re.sub(illegal_chars, '_', filename)
        
        # 移除首尾空格和点
        filename = filename.strip(' .')
        
        return filename

