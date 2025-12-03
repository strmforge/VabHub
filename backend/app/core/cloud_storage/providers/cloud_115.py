"""
115网盘提供商
使用115官方开发者API（整合Cloud115API、Cloud115OAuth、Cloud115UploadManager）
"""

import asyncio
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

from app.core.cloud_storage.providers.base import (
    CloudStorageProvider,
    CloudFileInfo,
    CloudStorageUsage
)
from app.core.cloud_storage.providers.cloud_115_api import Cloud115API
from app.core.cloud_storage.providers.cloud_115_oauth import Cloud115OAuth
from app.core.cloud_storage.providers.cloud_115_upload import Cloud115UploadManager


class Cloud115Provider(CloudStorageProvider):
    """115网盘提供商"""
    
    # 支持的传输类型
    transtype = {
        "copy": "复制",
        "move": "移动"
    }
    
    def __init__(self):
        self.app_id: Optional[str] = None
        self.app_key: Optional[str] = None
        self.app_secret: Optional[str] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.user_name: Optional[str] = None
        self.expires_at: Optional[datetime] = None
        
        # 配置信息
        self._config: Optional[Dict[str, Any]] = None
        
        # 存储ID（用于token持久化）
        self._storage_id: Optional[int] = None
        self._token_save_callback: Optional[callable] = None  # token保存回调函数
        
        # API基础URL
        self.base_url = "https://proapi.115.com"
        self.passport_url = "https://passportapi.115.com"
        self.qrcode_url = "https://qrcodeapi.115.com"
        
        # 新的API客户端（整合115官方开发者API）
        self._api_client: Optional[Cloud115API] = None
        self._oauth_client: Optional[Cloud115OAuth] = None
        self._upload_manager: Optional[Cloud115UploadManager] = None
        
        # 文件块大小，默认10MB
        self.chunk_size = 10 * 1024 * 1024
        
        # 流控重试间隔时间
        self.retry_delay = 70
    
    async def initialize(self, credentials: Dict[str, Any]) -> bool:
        """初始化115网盘提供商"""
        try:
            self.app_id = credentials.get("app_id")
            self.app_key = credentials.get("app_key")
            # AppSecret是可选的，115网盘API只需要AppID和AppKey
            self.app_secret = credentials.get("app_secret")
            self._config = credentials
            
            # 设置存储ID和token保存回调（用于token持久化）
            self._storage_id = credentials.get("storage_id")
            self._token_save_callback = credentials.get("token_save_callback")
            
            # 如果已有access_token，直接使用
            if credentials.get("access_token"):
                self.access_token = credentials.get("access_token")
                self.refresh_token = credentials.get("refresh_token")
                self.user_id = credentials.get("user_id")
                self.user_name = credentials.get("user_name")
                if credentials.get("expires_at"):
                    if isinstance(credentials["expires_at"], str):
                        self.expires_at = datetime.fromisoformat(credentials["expires_at"])
                    else:
                        self.expires_at = credentials["expires_at"]
            
            # 115网盘API只需要AppID和AppKey
            if not self.app_id or not self.app_key:
                logger.error("115网盘密钥不完整，需要AppID和AppKey")
                return False
            
            # 如果已有access_token，初始化API客户端
            if self.access_token:
                self._api_client = Cloud115API(access_token=self.access_token)
            
            logger.info("115网盘提供商初始化成功（已整合115官方开发者API）")
            return True
        except Exception as e:
            logger.error(f"115网盘提供商初始化失败: {e}")
            return False
    
    def get_config(self) -> Optional[Dict[str, Any]]:
        """获取配置"""
        return self._config
    
    def set_config(self, conf: Dict[str, Any]):
        """设置配置"""
        self._config = conf
        # 更新相关属性
        if "app_id" in conf:
            self.app_id = conf["app_id"]
        if "app_key" in conf:
            self.app_key = conf["app_key"]
        if "app_secret" in conf:
            self.app_secret = conf["app_secret"]
        if "access_token" in conf:
            self.access_token = conf["access_token"]
        if "refresh_token" in conf:
            self.refresh_token = conf["refresh_token"]
        if "user_id" in conf:
            self.user_id = conf["user_id"]
        if "user_name" in conf:
            self.user_name = conf["user_name"]
    
    async def generate_qrcode_async(self, *args, **kwargs) -> Optional[Tuple[Dict[str, Any], str]]:
        """生成二维码（115网盘登录）- 异步版本"""
        try:
            qr_content, qr_url, qr_key = await self.generate_qr_code()
            if qr_content:
                return {
                    "content": qr_content,
                    "url": qr_url,
                    "key": qr_key
                }, qr_url
            return None
        except Exception as e:
            logger.error(f"生成二维码失败: {e}")
            return None
    
    def generate_qrcode(self, *args, **kwargs) -> Optional[Tuple[Dict[str, Any], str]]:
        """
        生成二维码（115网盘登录）
        注意：此方法应在异步上下文中调用generate_qr_code()方法
        """
        logger.warning("generate_qrcode方法已废弃，请使用generate_qr_code()异步方法")
        return None
    
    def check_login(self, *args, **kwargs) -> Optional[Dict[str, str]]:
        """检查登录状态"""
        try:
            if self.access_token and self.user_id:
                return {
                    "user_id": self.user_id,
                    "user_name": self.user_name or "",
                    "access_token": self.access_token[:20] + "..." if self.access_token else ""
                }
            return None
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return None
    
    async def _get_api_client(self) -> Optional[Cloud115API]:
        """获取Cloud115API客户端"""
        if not self.access_token:
            return None
        if not self._api_client:
            self._api_client = Cloud115API(access_token=self.access_token)
        return self._api_client
    
    async def _get_oauth_client(self) -> Optional[Cloud115OAuth]:
        """获取Cloud115OAuth客户端"""
        if not self.app_id:
            return None
        if not self._oauth_client:
            self._oauth_client = Cloud115OAuth(client_id=self.app_id)
        return self._oauth_client
    
    async def _get_upload_manager(self) -> Optional[Cloud115UploadManager]:
        """获取Cloud115UploadManager"""
        api_client = await self._get_api_client()
        if not api_client:
            return None
        if not self._upload_manager:
            self._upload_manager = Cloud115UploadManager(api_client)
        return self._upload_manager
    
    async def is_authenticated(self) -> bool:
        """检查是否已认证"""
        if not self.access_token:
            return False
        
        # 检查token是否过期
        if self.expires_at and datetime.now() >= self.expires_at - timedelta(minutes=5):
            # 尝试刷新token
            if self.refresh_token:
                await self.refresh_token()
            else:
                return False
        
        # 验证token有效性（使用API客户端）
        api_client = await self._get_api_client()
        if api_client:
            try:
                result = await api_client.get_user_info()
                if result and result.get("success"):
                    return True
            except Exception as e:
                logger.debug(f"Token验证失败: {e}")
                return False
        
        return self.access_token is not None
    
    async def generate_qr_code(self) -> Tuple[str, str]:
        """
        生成二维码（使用Cloud115OAuth）
        返回: (二维码内容, 二维码URL)
        """
        try:
            oauth_client = await self._get_oauth_client()
            if not oauth_client:
                raise Exception("OAuth客户端未初始化，请先设置app_id")
            
            # 获取设备码和二维码
            device_info = await oauth_client.get_device_code()
            if not device_info:
                raise Exception("获取设备码失败")
            
            qr_content = device_info.get("qrcode")
            qr_url = device_info.get("qr_url")
            
            if not qr_content:
                raise Exception("二维码内容为空")
            
            return qr_content, qr_url
        except Exception as e:
            logger.error(f"生成115网盘二维码失败: {e}")
            raise
    
    async def check_qr_status(self) -> Tuple[int, str, Dict[str, Any]]:
        """
        检查二维码登录状态（使用Cloud115OAuth）
        返回: (状态, 消息, 令牌数据)
        状态: 0=未扫码, 1=已扫码, 2=已确认, -1=已过期/失败
        """
        try:
            oauth_client = await self._get_oauth_client()
            if not oauth_client:
                return -1, "OAuth客户端未初始化", {}
            
            # 检查二维码状态
            status_info = await oauth_client.poll_qr_status(timeout=30)
            status = status_info.get("status", -1)
            message = status_info.get("message", "")
            
            if status == 2:
                # 已确认登录，获取访问令牌
                token_info = await oauth_client.get_access_token()
                if token_info:
                    # 更新认证信息
                    self.access_token = token_info.get("access_token")
                    self.refresh_token = token_info.get("refresh_token")
                    expires_in = token_info.get("expires_in", 604800)  # 默认7天
                    self.expires_at = datetime.now() + timedelta(seconds=expires_in)
                    
                    # 获取用户信息
                    await self._get_user_info()
                    
                    # 保存token到数据库
                    await self._save_tokens_to_db()
                    
                    # 更新API客户端
                    if self.access_token:
                        self._api_client = Cloud115API(access_token=self.access_token)
                    
                    return 2, "登录成功", {
                        "access_token": self.access_token,
                        "refresh_token": self.refresh_token,
                        "user_id": self.user_id,
                        "user_name": self.user_name
                    }
                else:
                    return -1, "获取访问令牌失败", {}
            
            return status, message, {}
        except Exception as e:
            logger.error(f"检查115网盘二维码状态失败: {e}")
            return -1, f"检查失败: {str(e)}", {}
    
    async def _get_access_token(self) -> Optional[Dict[str, Any]]:
        """获取访问令牌"""
        try:
            if not self._auth_state:
                raise Exception("请先生成二维码")
            
            await self._init_session()
            
            logger.debug(f"获取访问令牌: uid={self._auth_state['uid']}")
            
            async with self.session.post(
                f"{self.passport_url}/open/deviceCodeToToken",
                data={
                    "uid": self._auth_state["uid"],
                    "code_verifier": self._auth_state["code_verifier"]
                }
            ) as response:
                # 检查HTTP状态码
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"获取访问令牌HTTP错误: {response.status}, 响应: {error_text[:200]}")
                    raise Exception(f"HTTP错误: {response.status}")
                
                # 读取响应文本
                response_text = await response.text()
                logger.debug(f"获取访问令牌响应: {response_text[:200]}")
                
                if not response_text:
                    raise Exception("空响应")
                
                try:
                    import json
                    result = json.loads(response_text)
                except json.JSONDecodeError as e:
                    logger.error(f"解析访问令牌响应失败: {response_text[:500]}, 错误: {e}")
                    raise Exception(f"响应格式错误: {response_text[:200]}")
                
                if result.get("code") != 0:
                    error_msg = result.get("message", "获取访问令牌失败")
                    logger.error(f"获取访问令牌失败: code={result.get('code')}, message={error_msg}")
                    raise Exception(f"获取访问令牌失败: {error_msg}")
                
                token_data = result.get("data", {})
                if not token_data:
                    logger.error(f"访问令牌数据为空: {result}")
                    raise Exception("访问令牌数据为空")
                
                logger.info(f"获取访问令牌成功: access_token={token_data.get('access_token', '')[:20]}...")
                return token_data
        except Exception as e:
            logger.error(f"获取115网盘访问令牌失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            return None
    
    async def _get_user_info(self):
        """获取用户信息（使用Cloud115API）"""
        try:
            if not self.access_token:
                return
            
            api_client = await self._get_api_client()
            if not api_client:
                return
            
            result = await api_client.get_user_info()
            if result and result.get("success"):
                user_data = result.get("data", {})
                self.user_id = str(user_data.get("user_id", ""))
                self.user_name = user_data.get("user_name", "")
                logger.info(f"获取115网盘用户信息成功: user_id={self.user_id}, user_name={self.user_name}")
        except Exception as e:
            logger.error(f"获取115网盘用户信息失败: {e}")
    
    async def refresh_token(self) -> bool:
        """刷新访问令牌（使用Cloud115OAuth）"""
        try:
            if not self.refresh_token:
                logger.error("刷新令牌不存在")
                return False
            
            oauth_client = await self._get_oauth_client()
            if not oauth_client:
                logger.error("OAuth客户端未初始化")
                return False
            
            token_info = await oauth_client.refresh_access_token(self.refresh_token)
            if token_info:
                self.access_token = token_info.get("access_token")
                self.refresh_token = token_info.get("refresh_token")
                expires_in = token_info.get("expires_in", 2592000)  # 默认30天
                self.expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # 更新API客户端
                if self.access_token:
                    self._api_client = Cloud115API(access_token=self.access_token)
                
                # 保存刷新后的token到数据库
                await self._save_tokens_to_db()
                
                logger.info("115网盘访问令牌刷新成功")
                return True
            else:
                logger.error("刷新令牌失败")
                return False
        except Exception as e:
            logger.error(f"刷新115网盘访问令牌失败: {e}")
            return False
    
    async def _save_tokens_to_db(self):
        """保存token到数据库（通过回调函数）"""
        try:
            if self._token_save_callback and self._storage_id:
                await self._token_save_callback(
                    storage_id=self._storage_id,
                    access_token=self.access_token,
                    refresh_token=self.refresh_token,
                    expires_at=self.expires_at,
                    user_id=self.user_id,
                    user_name=self.user_name
                )
                logger.debug(f"Token已保存到数据库 (storage_id={self._storage_id})")
        except Exception as e:
            logger.warning(f"保存token到数据库失败: {e}")
            # 不抛出异常，因为token保存失败不应该影响主要功能
    
    async def set_token(self, access_token: str, refresh_token: str = None, expires_in: int = 604800):
        """设置访问令牌（用于从外部设置）"""
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = datetime.now() + timedelta(seconds=expires_in)
    
    async def _ensure_token(self):
        """确保访问令牌有效"""
        if not await self.is_authenticated():
            raise Exception("未登录，请先进行认证")
    
    async def list_files(self, path: str = "/", recursive: bool = False) -> List[CloudFileInfo]:
        """列出文件（使用Cloud115API）"""
        try:
            await self._ensure_token()
            
            api_client = await self._get_api_client()
            if not api_client:
                return []
            
            # 获取文件夹ID（用于分页）
            folder_id = await self._get_folder_id_by_path(path)
            if folder_id is None:
                return []
            
            files = []
            offset = 0
            limit = 1000
            
            while True:
                # 使用Cloud115API的list_files方法
                result = await api_client.list_files(
                    file_id=folder_id,
                    limit=limit,
                    offset=offset,
                    show_dir=1
                )
                
                # Cloud115API.list_files返回的是{"count": count, "data": files, ...}
                # 没有success字段，需要检查data字段
                if not result or not result.get("data"):
                    break
                
                file_list = result.get("data", [])
                
                # 转换文件列表
                for item in file_list:
                    file_info = self._convert_api_response_to_cloud_file_info(item, path)
                    if file_info:
                        files.append(file_info)
                    
                    # 如果是递归模式且是文件夹，递归列出子文件
                    if recursive and file_info and file_info.type == "dir":
                        sub_files = await self.list_files(file_info.path, recursive=True)
                        files.extend(sub_files)
                
                # 检查是否还有更多文件
                if len(file_list) < limit:
                    break
                
                offset += len(file_list)
            
            return files
        except Exception as e:
            logger.error(f"列出115网盘文件失败: {e}")
            return []
    
    def _convert_api_response_to_cloud_file_info(
        self, 
        item: Dict[str, Any], 
        parent_path: str = "/"
    ) -> Optional[CloudFileInfo]:
        """将115 API响应转换为CloudFileInfo"""
        try:
            # 115 API返回的文件信息字段（list_files返回的格式）
            file_id = str(item.get("file_id", ""))
            file_name = item.get("file_name", "")
            file_category = item.get("file_category", "1")  # "1":文件, "0":文件夹
            
            # 构建文件路径
            if parent_path == "/":
                file_path = f"/{file_name}"
            else:
                file_path = f"{parent_path.rstrip('/')}/{file_name}"
            
            # 如果是文件夹，添加/
            if file_category == "0":
                file_path += "/"
            
            # 获取时间戳（list_files返回的是update_time, upload_time等）
            # get_file_info返回的是ptime, utime
            ptime = item.get("ptime") or item.get("upload_time") or item.get("uppt", 0)
            utime = item.get("utime") or item.get("update_time") or item.get("upt", 0)
            
            created_at = None
            if ptime:
                try:
                    if isinstance(ptime, (int, float)) and ptime > 0:
                        created_at = datetime.fromtimestamp(ptime)
                    elif isinstance(ptime, str):
                        # 尝试解析时间字符串
                        created_at = datetime.fromisoformat(ptime.replace('Z', '+00:00'))
                except Exception:
                    pass
            
            modified_at = None
            if utime:
                try:
                    if isinstance(utime, (int, float)) and utime > 0:
                        modified_at = datetime.fromtimestamp(utime)
                    elif isinstance(utime, str):
                        modified_at = datetime.fromisoformat(utime.replace('Z', '+00:00'))
                except Exception:
                    pass
            
            # 获取文件大小（list_files返回的是file_size，get_file_info返回的是size_byte）
            file_size = item.get("size_byte") or item.get("file_size", 0)
            
            return CloudFileInfo(
                id=file_id,
                name=file_name,
                path=file_path,
                size=file_size if file_category == "1" else 0,
                type="dir" if file_category == "0" else "file",
                parent_id=str(item.get("parent_id", "")),
                created_at=created_at,
                modified_at=modified_at,
                metadata={
                    "sha1": item.get("sha1", ""),
                    "pick_code": item.get("pick_code", ""),
                    "icon": item.get("file_ext") or item.get("ico", ""),
                    "file_category": file_category
                }
            )
        except Exception as e:
            logger.error(f"转换文件信息失败: {e}")
            return None
    
    async def _get_folder_id_by_path(self, path: str) -> Optional[str]:
        """根据路径获取文件夹ID（使用Cloud115API）"""
        try:
            api_client = await self._get_api_client()
            if not api_client:
                return None
            
            # 根目录
            if path == "/" or not path:
                return "0"
            
            # 使用Cloud115API获取文件信息
            result = await api_client.get_file_info(path=path)
            if result and result.get("success"):
                data = result.get("data", {})
                file_category = data.get("file_category", "1")
                if file_category == "0":  # 文件夹
                    return str(data.get("file_id", ""))
            
            return None
        except Exception as e:
            logger.error(f"根据路径获取文件夹ID失败: {e}")
            return None
    
    async def get_file_info(self, file_id: str) -> Optional[CloudFileInfo]:
        """获取文件信息（使用Cloud115API）"""
        try:
            await self._ensure_token()
            
            api_client = await self._get_api_client()
            if not api_client:
                return None
            
            result = await api_client.get_file_info(file_id=file_id)
            if not result or not result.get("success"):
                return None
            
            data = result.get("data", {})
            return self._convert_api_response_to_cloud_file_info(data, "/")
        except Exception as e:
            logger.error(f"获取115网盘文件信息失败: {e}")
            return None
    
    async def get_file_info_by_path(self, path: str) -> Optional[CloudFileInfo]:
        """根据路径获取文件信息（使用Cloud115API）"""
        try:
            await self._ensure_token()
            
            api_client = await self._get_api_client()
            if not api_client:
                return None
            
            result = await api_client.get_file_info(path=path)
            if not result or not result.get("success"):
                return None
            
            data = result.get("data", {})
            # 构建文件路径
            file_path = path.rstrip("/")
            if data.get("file_category") == "0":  # 目录
                file_path += "/"
            
            file_info = self._convert_api_response_to_cloud_file_info(data, "/")
            if file_info:
                file_info.path = file_path
            return file_info
        except Exception as e:
            logger.debug(f"获取115网盘文件信息失败（路径: {path}）: {e}")
            return None
    
    async def _delay_get_item(self, path: str, max_retries: int = 3) -> Optional[CloudFileInfo]:
        """
        自动延迟重试获取文件信息
        使用指数退避策略：2秒、4秒、8秒
        """
        for i in range(1, max_retries + 1):
            await asyncio.sleep(2 ** i)  # 指数退避：2秒、4秒、8秒
            file_info = await self.get_file_info_by_path(path)
            if file_info:
                logger.debug(f"延迟获取文件信息成功: {path} (尝试 {i}/{max_retries})")
                return file_info
        logger.warning(f"延迟获取文件信息失败: {path} (已尝试 {max_retries} 次)")
        return None
    
    async def create_folder(self, parent_path: str, name: str) -> Optional[CloudFileInfo]:
        """创建文件夹（使用Cloud115API）"""
        try:
            await self._ensure_token()
            
            api_client = await self._get_api_client()
            if not api_client:
                return None
            
            # 获取父文件夹ID
            parent_id = await self._get_folder_id_by_path(parent_path)
            if parent_id is None:
                logger.error(f"父目录不存在: {parent_path}")
                return None
            
            # 使用Cloud115API创建文件夹
            result = await api_client.create_folder(pid=parent_id, file_name=name)
            if not result or not result.get("success"):
                return None
            
            folder_data = result.get("data", {})
            folder_id = str(folder_data.get("file_id", ""))
            
            return CloudFileInfo(
                id=folder_id,
                name=name,
                path=f"{parent_path.rstrip('/')}/{name}/",
                type="dir",
                parent_id=parent_id,
                created_at=datetime.now(),
                modified_at=datetime.now(),
                metadata={}
            )
        except Exception as e:
            logger.error(f"创建115网盘文件夹失败: {e}")
            return None
    
    async def delete_file(self, file_id: str) -> bool:
        """
        删除文件/目录（使用Cloud115API）
        
        Args:
            file_id: 文件/目录ID
        
        Returns:
            删除是否成功
        """
        try:
            await self._ensure_token()
            
            api_client = await self._get_api_client()
            if not api_client:
                return False
            
            result = await api_client.delete_file(file_ids=file_id)
            return result.get("success", False)
        except Exception as e:
            logger.error(f"【115】删除115网盘文件失败: {e}")
            return False
    
    async def get_folder(self, path: str) -> Optional[CloudFileInfo]:
        """
        获取指定路径的文件夹，如不存在则创建
        
        Args:
            path: 文件夹路径（如：/path/to/folder）
        
        Returns:
            文件夹信息，如果创建失败返回None
        """
        try:
            await self._ensure_token()
            
            # 1. 检查路径是否已存在
            folder = await self.get_file_info_by_path(path)
            if folder:
                return folder
            
            # 2. 逐级查找和创建目录
            parts = [part for part in path.split("/") if part]
            if not parts:
                # 根目录
                return await self.get_file_info_by_path("/")
            
            # 从根目录开始
            current_path = "/"
            current_item = None
            
            for part in parts:
                # 在当前路径下查找目录
                files = await self.list_files(current_path)
                found = False
                
                for file in files:
                    if file.name == part and file.type == "dir":
                        current_item = file
                        current_path = file.path
                        found = True
                        break
                
                if not found:
                    # 创建目录
                    new_folder = await self.create_folder(current_path, part)
                    if not new_folder:
                        logger.warn(f"【115】创建目录 {current_path}{part} 失败！")
                        return None
                    current_item = new_folder
                    current_path = new_folder.path
            
            return current_item
            
        except Exception as e:
            logger.error(f"【115】获取或创建文件夹失败: {e}")
            return None
    
    async def upload_file(self, local_path: str, remote_path: str, progress_callback: Optional[callable] = None) -> bool:
        """
        上传文件（支持秒传、断点续传和分片上传）
        
        Args:
            local_path: 本地文件路径
            remote_path: 远程文件路径（相对于根目录）
            progress_callback: 进度回调函数（可选）
        
        Returns:
            上传是否成功
        """
        if not OSS2_AVAILABLE:
            logger.error("oss2库未安装，无法使用115网盘上传功能")
            return False
        
        try:
            await self._ensure_token()
            
            local_file = Path(local_path)
            if not local_file.exists():
                logger.error(f"本地文件不存在: {local_path}")
                return False
            
            # 解析远程路径
            remote_path_obj = Path(remote_path)
            target_name = remote_path_obj.name
            target_dir_path = str(remote_path_obj.parent)
            
            # 获取目标目录ID
            target_folder_id = await self._get_folder_id_by_path(target_dir_path if target_dir_path != "." else "/")
            if not target_folder_id:
                logger.error(f"目标目录不存在: {target_dir_path}")
                return False
            
            # 计算文件特征值
            file_size = local_file.stat().st_size
            file_sha1 = self._calc_sha1(local_file)
            file_preid = self._calc_sha1(local_file, 128 * 1024 * 1024)  # 前128MB的SHA1
            
            target_param = f"U_1_{target_folder_id}"
            
            # Step 1: 初始化上传
            init_data = {
                "file_name": target_name,
                "file_size": file_size,
                "target": target_param,
                "fileid": file_sha1,
                "preid": file_preid
            }
            
            init_resp = await self._request(
                "POST",
                f"{self.base_url}/open/upload/init",
                data=init_data
            )
            
            if not init_resp or not init_resp.get("state"):
                error_msg = init_resp.get("error", "未知错误") if init_resp else "初始化上传失败"
                logger.error(f"初始化上传失败: {error_msg}")
                return False
            
            init_result = init_resp.get("data", {})
            logger.debug(f"上传 Step 1 初始化结果: {init_result}")
            
            # 获取回调信息
            bucket_name = init_result.get("bucket")
            object_name = init_result.get("object")
            callback = init_result.get("callback")
            sign_check = init_result.get("sign_check")
            pick_code = init_result.get("pick_code")
            sign_key = init_result.get("sign_key")
            
            # Step 2: 处理二次认证
            if init_result.get("code") in [700, 701] and sign_check:
                sign_checks = sign_check.split("-")
                start = int(sign_checks[0])
                end = int(sign_checks[1])
                
                # 计算指定区间的SHA1
                with open(local_file, "rb") as f:
                    f.seek(start)
                    chunk = f.read(end - start + 1)
                    sign_val = hashlib.sha1(chunk).hexdigest().upper()
                
                # 重新初始化请求
                init_data.update({
                    "pick_code": pick_code,
                    "sign_key": sign_key,
                    "sign_val": sign_val
                })
                
                init_resp = await self._request(
                    "POST",
                    f"{self.base_url}/open/upload/init",
                    data=init_data
                )
                
                if not init_resp or not init_resp.get("state"):
                    error_msg = init_resp.get("error", "未知错误") if init_resp else "二次认证失败"
                    logger.error(f"二次认证失败: {error_msg}")
                    return False
                
                init_result = init_resp.get("data", {})
                logger.debug(f"上传 Step 2 二次认证结果: {init_result}")
                
                if not pick_code:
                    pick_code = init_result.get("pick_code")
                if not bucket_name:
                    bucket_name = init_result.get("bucket")
                if not object_name:
                    object_name = init_result.get("object")
                if not callback:
                    callback = init_result.get("callback")
            
            # Step 3: 秒传检测
            if init_result.get("status") == 2:
                logger.info(f"【115】{target_name} 秒传成功")
                if progress_callback:
                    progress_callback(100.0)
                
                # 秒传成功后，尝试获取文件信息
                file_id = init_result.get("file_id", None)
                if file_id:
                    logger.debug(f"【115】{target_name} 使用秒传返回ID获取文件信息")
                    await asyncio.sleep(2)  # 等待文件信息更新
                    info_resp = await self._request(
                        "GET",
                        f"{self.base_url}/open/folder/get_info",
                        params={"file_id": int(file_id)}
                    )
                    if info_resp and info_resp.get("data"):
                        logger.debug(f"【115】秒传文件信息获取成功: {info_resp['data'].get('file_name')}")
                
                # 使用智能延迟获取文件信息
                file_info = await self._delay_get_item(str(target_path))
                if file_info:
                    logger.debug(f"【115】秒传后获取文件信息成功: {file_info.name}")
                
                return True
            
            # Step 4: 获取上传凭证
            token_resp = await self._request(
                "GET",
                f"{self.base_url}/open/upload/get_token"
            )
            
            if not token_resp or not token_resp.get("data"):
                logger.error("获取上传凭证失败")
                return False
            
            token_data = token_resp.get("data", {})
            endpoint = token_data.get("endpoint")
            access_key_id = token_data.get("AccessKeyId")
            access_key_secret = token_data.get("AccessKeySecret")
            security_token = token_data.get("SecurityToken")
            
            logger.debug(f"上传 Step 4 获取上传凭证成功")
            
            # Step 5: 断点续传检测
            resume_resp = await self._request(
                "POST",
                f"{self.base_url}/open/upload/resume",
                data={
                    "file_size": file_size,
                    "target": target_param,
                    "fileid": file_sha1,
                    "pick_code": pick_code
                }
            )
            
            if resume_resp and resume_resp.get("data"):
                logger.debug(f"上传 Step 5 断点续传结果: {resume_resp.get('data')}")
                if resume_resp.get("data", {}).get("callback"):
                    callback = resume_resp["data"]["callback"]
            
            # Step 6: OSS分片上传（使用同步方式，因为oss2是同步库）
            # 注意：oss2是同步库，需要在异步环境中使用run_in_executor
            def _sync_upload():
                """同步上传函数"""
                try:
                    # 创建OSS认证
                    auth = oss2.StsAuth(
                        access_key_id=access_key_id,
                        access_key_secret=access_key_secret,
                        security_token=security_token
                    )
                    bucket = oss2.Bucket(auth, endpoint, bucket_name)
                    
                    # 确定分片大小（默认10MB）
                    part_size = determine_part_size(file_size, preferred_size=10 * 1024 * 1024)
                    logger.info(f"开始上传: {local_path} -> {remote_path}，分片大小: {part_size / 1024 / 1024:.2f}MB")
                    
                    # 初始化分片上传
                    upload_id = bucket.init_multipart_upload(
                        object_name,
                        params={
                            "encoding-type": "url",
                            "sequential": ""
                        }
                    ).upload_id
                    
                    parts = []
                    
                    # 逐个上传分片
                    with open(local_file, 'rb') as fileobj:
                        part_number = 1
                        offset = 0
                        
                        while offset < file_size:
                            num_to_upload = min(part_size, file_size - offset)
                            logger.debug(f"开始上传 {target_name} 分片 {part_number}: {offset} -> {offset + num_to_upload}")
                            
                            result = bucket.upload_part(
                                object_name,
                                upload_id,
                                part_number,
                                data=SizedFileAdapter(fileobj, num_to_upload)
                            )
                            parts.append(PartInfo(part_number, result.etag))
                            
                            logger.debug(f"{target_name} 分片 {part_number} 上传完成")
                            offset += num_to_upload
                            part_number += 1
                            
                            # 更新进度
                            if progress_callback:
                                progress = (offset * 100) / file_size
                                progress_callback(progress)
                    
                    # 完成上传
                    if progress_callback:
                        progress_callback(100.0)
                    
                    # 编码回调
                    def encode_callback(cb: str) -> str:
                        return oss2.utils.b64encode_as_string(cb)
                    
                    # 完成分片上传
                    headers = {
                        'X-oss-callback': encode_callback(callback["callback"]),
                        'x-oss-callback-var': encode_callback(callback["callback_var"]),
                        'x-oss-forbid-overwrite': 'false'
                    }
                    
                    result = bucket.complete_multipart_upload(
                        object_name,
                        upload_id,
                        parts,
                        headers=headers
                    )
                    
                    if result.status == 200:
                        logger.info(f"{target_name} 上传成功")
                        return True
                    else:
                        logger.error(f"{target_name} 上传失败，错误码: {result.status}")
                        return False
                        
                except oss2.exceptions.OssError as e:
                    if e.code == "FileAlreadyExists":
                        logger.warning(f"{target_name} 已存在")
                        return True
                    else:
                        logger.error(f"{target_name} 上传失败: {e.status}, 错误码: {e.code}, 详情: {e.message}")
                        return False
                except Exception as e:
                    logger.error(f"上传过程中发生错误: {e}")
                    return False
            
            # 在线程池中执行同步上传
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, _sync_upload)
            
            if success:
                # 使用智能延迟获取文件信息
                file_info = await self._delay_get_item(str(target_path))
                if file_info:
                    logger.debug(f"上传后获取文件信息成功: {file_info.name}")
                else:
                    logger.warning(f"上传后无法获取文件信息: {target_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"上传115网盘文件失败: {e}")
            return False
    
    async def download_file(
        self, 
        file_id: str, 
        save_path: str, 
        progress_callback: Optional[callable] = None,
        cancel_event: Optional[asyncio.Event] = None
    ) -> bool:
        """
        下载文件（使用Cloud115API）
        
        Args:
            file_id: 文件ID
            save_path: 保存路径
            progress_callback: 进度回调函数（可选）
            cancel_event: 取消事件（可选），用于取消下载
        
        Returns:
            下载是否成功
        """
        try:
            await self._ensure_token()
            
            api_client = await self._get_api_client()
            if not api_client:
                return False
            
            # 获取文件信息
            file_info = await self.get_file_info(file_id)
            if not file_info:
                logger.error(f"【115】获取文件详情失败: {file_id}")
                return False
            
            # 获取pick_code
            pick_code = file_info.metadata.get("pick_code")
            if not pick_code:
                logger.error(f"【115】文件缺少pick_code: {file_info.name}")
                return False
            
            # 获取下载链接
            result = await api_client.get_download_url(pick_code=pick_code)
            if not result or not result.get("success"):
                logger.error(f"【115】获取下载链接失败: {file_info.name}")
                return False
            
            download_url = result.get("download_url")
            if not download_url:
                logger.error(f"【115】下载链接为空: {file_info.name}")
                return False
            
            # 保存文件路径
            save_path_obj = Path(save_path)
            save_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # 获取文件大小
            file_size = file_info.size or 0
            
            # 下载文件（使用httpx）
            import httpx
            
            logger.info(f"【115】开始下载: {file_info.name} -> {save_path}")
            
            async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
                try:
                    async with client.stream("GET", download_url) as response:
                        response.raise_for_status()
                        downloaded_size = 0
                        
                        with open(save_path, "wb") as f:
                            async for chunk in response.aiter_bytes(chunk_size=self.chunk_size):
                                # 检查取消事件
                                if cancel_event and cancel_event.is_set():
                                    logger.info(f"【115】{file_info.name} 下载已取消！")
                                    if save_path_obj.exists():
                                        save_path_obj.unlink()
                                    return False
                                
                                if chunk:
                                    f.write(chunk)
                                    downloaded_size += len(chunk)
                                    
                                    # 更新进度
                                    if progress_callback and file_size:
                                        progress = (downloaded_size * 100) / file_size
                                        progress_callback(progress)
                        
                        # 完成下载
                        if progress_callback:
                            progress_callback(100.0)
                        logger.info(f"【115】下载完成: {file_info.name}")
                        return True
                        
                except asyncio.CancelledError:
                    logger.info(f"【115】{file_info.name} 下载已取消！")
                    if save_path_obj.exists():
                        save_path_obj.unlink()
                    return False
                except httpx.HTTPStatusError as e:
                    logger.error(f"【115】下载HTTP错误: {file_info.name} - {e.response.status_code}")
                    if save_path_obj.exists():
                        save_path_obj.unlink()
                    return False
                except Exception as e:
                    logger.error(f"【115】下载失败: {file_info.name} - {str(e)}")
                    if save_path_obj.exists():
                        save_path_obj.unlink()
                    return False
                
        except Exception as e:
            logger.error(f"【115】下载115网盘文件失败: {e}")
            save_path_obj = Path(save_path)
            if save_path_obj.exists():
                save_path_obj.unlink()
            return False
    
    async def get_storage_usage(self) -> Optional[CloudStorageUsage]:
        """获取存储使用情况（使用Cloud115API）"""
        try:
            await self._ensure_token()
            
            api_client = await self._get_api_client()
            if not api_client:
                return None
            
            result = await api_client.get_user_info()
            if not result or not result.get("success"):
                return None
            
            user_data = result.get("data", {})
            space_info = user_data.get("rt_space_info", {})
            total = space_info.get("all_total", {}).get("size", 0)
            used = space_info.get("all_used", {}).get("size", 0)
            available = space_info.get("all_remain", {}).get("size", 0)
            
            percentage = (used / total * 100) if total > 0 else 0.0
            
            return CloudStorageUsage(
                total=total,
                used=used,
                available=available,
                percentage=percentage
            )
        except Exception as e:
            logger.error(f"获取115网盘存储使用情况失败: {e}")
            return None
    
    async def move_file(self, file_id: str, target_path: str, new_name: Optional[str] = None) -> bool:
        """
        移动文件（使用Cloud115API）
        
        Args:
            file_id: 文件ID
            target_path: 目标路径
            new_name: 新名称（可选）
        
        Returns:
            移动是否成功
        """
        try:
            await self._ensure_token()
            
            api_client = await self._get_api_client()
            if not api_client:
                return False
            
            # 获取目标目录ID
            target_folder_info = await self.get_file_info_by_path(target_path)
            if not target_folder_info or target_folder_info.type != "dir":
                logger.warn(f"【115】目标路径 {target_path} 不是一个有效的目录！")
                return False
            
            # 移动文件
            result = await api_client.move_file(
                file_ids=file_id,
                to_cid=target_folder_info.id
            )
            
            if not result or not result.get("success"):
                return False
            
            # 如果需要重命名
            if new_name:
                # 等待文件移动完成
                await asyncio.sleep(2)
                # 获取新文件信息
                new_file = await self.get_file_info_by_path(f"{target_path.rstrip('/')}/{new_name}")
                if new_file:
                    return await self.rename_file(new_file.id, new_name)
                else:
                    # 如果获取不到，尝试直接重命名
                    return await self.rename_file(file_id, new_name)
            
            return True
        except Exception as e:
            logger.error(f"【115】移动115网盘文件失败: {e}")
            return False
    
    async def copy_file(
        self, 
        file_id: str, 
        target_path: str, 
        new_name: Optional[str] = None,
        recursive: bool = False
    ) -> bool:
        """
        复制文件/目录（使用Cloud115API）
        支持目录递归复制
        
        Args:
            file_id: 文件/目录ID
            target_path: 目标路径
            new_name: 新名称（可选）
            recursive: 是否递归复制目录（默认False）
        
        Returns:
            复制是否成功
        """
        try:
            await self._ensure_token()
            
            api_client = await self._get_api_client()
            if not api_client:
                return False
            
            # 获取源文件信息
            source_file = await self.get_file_info(file_id)
            if not source_file:
                logger.error(f"获取源文件信息失败: {file_id}")
                return False
            
            # 获取目标目录信息
            target_folder_info = await self.get_file_info_by_path(target_path)
            if not target_folder_info or target_folder_info.type != "dir":
                logger.warn(f"【115】目标路径 {target_path} 不是一个有效的目录！")
                return False
            
            # 如果是目录且需要递归复制
            if source_file.type == "dir" and recursive:
                return await self._copy_directory_recursive(source_file, target_path, new_name)
            
            # 单文件/目录复制
            result = await api_client.copy_file(
                file_id=file_id,
                pid=target_folder_info.id
            )
            
            if not result or not result.get("success"):
                return False
            
            # 如果需要重命名
            if new_name:
                # 等待文件复制完成
                await asyncio.sleep(2)
                # 获取新文件信息
                new_file = await self.get_file_info_by_path(f"{target_path.rstrip('/')}/{source_file.name}")
                if new_file:
                    return await self.rename_file(new_file.id, new_name)
            
            return True
        except Exception as e:
            logger.error(f"复制115网盘文件失败: {e}")
            return False
    
    async def _copy_directory_recursive(
        self, 
        source_dir: CloudFileInfo, 
        target_path: str, 
        new_name: Optional[str] = None
    ) -> bool:
        """
        递归复制目录
        
        Args:
            source_dir: 源目录信息
            target_path: 目标路径
            new_name: 新名称（可选）
        
        Returns:
            复制是否成功
        """
        try:
            # 在目标目录创建新目录
            target_dir_name = new_name or source_dir.name
            new_target_dir = await self.create_folder(target_path, target_dir_name)
            if not new_target_dir:
                logger.warn(f"【115】在目标目录创建目录失败: {target_dir_name}")
                return False
            
            # 列出源目录下的所有文件和子目录
            source_files = await self.list_files(source_dir.path)
            
            # 递归复制每个文件和子目录
            for item in source_files:
                if item.type == "dir":
                    # 递归复制子目录
                    success = await self._copy_directory_recursive(item, new_target_dir.path)
                    if not success:
                        logger.warn(f"【115】递归复制子目录失败: {item.path}")
                        return False
                else:
                    # 复制文件（不递归）
                    success = await self.copy_file(
                        item.id,
                        new_target_dir.path,
                        recursive=False
                    )
                    if not success:
                        logger.warn(f"【115】复制文件失败: {item.path}")
                        return False
            
            logger.info(f"【115】递归复制目录完成: {source_dir.path} -> {new_target_dir.path}")
            return True
            
        except Exception as e:
            logger.error(f"【115】递归复制目录失败: {e}")
            return False
    
    async def rename_file(self, file_id: str, new_name: str) -> bool:
        """重命名文件（使用Cloud115API）"""
        try:
            await self._ensure_token()
            
            api_client = await self._get_api_client()
            if not api_client:
                return False
            
            result = await api_client.update_file(file_id=file_id, new_name=new_name)
            return result.get("success", False)
        except Exception as e:
            logger.error(f"重命名115网盘文件失败: {e}")
            return False
    
    def _calc_sha1(self, filepath: Path, size: Optional[int] = None) -> str:
        """
        计算文件SHA1（符合115规范）
        
        Args:
            filepath: 文件路径
            size: 前多少字节（如果为None，计算整个文件）
        
        Returns:
            SHA1哈希值（十六进制字符串）
        """
        sha1 = hashlib.sha1()
        with open(filepath, 'rb') as f:
            if size:
                chunk = f.read(size)
                sha1.update(chunk)
            else:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    sha1.update(chunk)
        return sha1.hexdigest()
    
    async def _get_folder_id_by_path(self, path: str) -> Optional[str]:
        """根据路径获取文件夹ID"""
        try:
            if path == "/" or path == "":
                return "0"  # 根目录ID
            
            # 分割路径
            parts = [p for p in path.strip("/").split("/") if p]
            current_id = "0"
            
            # 逐级查找
            for part in parts:
                files = await self.list_files(path=f"/{'/'.join(parts[:parts.index(part)+1])}")
                for file_info in files:
                    if file_info.name == part and file_info.type == "dir":
                        current_id = file_info.id
                        break
                else:
                    return None
            
            return current_id
        except Exception as e:
            logger.error(f"获取文件夹ID失败: {e}")
            return None
    
    async def close(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
            self.session = None

