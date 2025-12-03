"""
OpenList OAuth提供商
通过OpenList获取115网盘的OAuth Token
"""

import aiohttp
import secrets
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from loguru import logger

from app.core.cloud_storage.providers.base import (
    CloudStorageProvider,
    CloudFileInfo,
    CloudStorageUsage
)


class OpenListProvider(CloudStorageProvider):
    """OpenList OAuth提供商（用于115网盘OAuth登录）"""
    
    # OpenList不支持传输类型（它只是OAuth代理）
    transtype = {}
    
    def __init__(self):
        self.server_url: Optional[str] = None
        self.app_id: Optional[str] = None
        self.app_secret: Optional[str] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.expires_at: Optional[datetime] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self._config: Optional[Dict[str, Any]] = None
        
        # OAuth状态
        self._state: Optional[str] = None
        self._code: Optional[str] = None
    
    async def initialize(self, credentials: Dict[str, Any]) -> bool:
        """初始化OpenList提供商"""
        try:
            self.server_url = credentials.get("server_url", "https://api.oplist.org.cn")
            self.app_id = credentials.get("app_id")
            self.app_secret = credentials.get("app_secret")
            self._config = credentials
            
            # 如果已有access_token，直接使用
            if credentials.get("access_token"):
                self.access_token = credentials.get("access_token")
                self.refresh_token = credentials.get("refresh_token")
                if credentials.get("expires_at"):
                    self.expires_at = datetime.fromisoformat(credentials["expires_at"])
            
            # OpenList的app_id和app_secret是可选的
            # 如果没有提供，使用默认的OAuth流程
            
            await self._init_session()
            
            logger.info("OpenList提供商初始化成功")
            return True
        except Exception as e:
            logger.error(f"OpenList提供商初始化失败: {e}")
            return False
    
    def get_config(self) -> Optional[Dict[str, Any]]:
        """获取配置"""
        return self._config
    
    def set_config(self, conf: Dict[str, Any]):
        """设置配置"""
        self._config = conf
        if "server_url" in conf:
            self.server_url = conf["server_url"]
        if "app_id" in conf:
            self.app_id = conf["app_id"]
        if "app_secret" in conf:
            self.app_secret = conf["app_secret"]
        if "access_token" in conf:
            self.access_token = conf["access_token"]
        if "refresh_token" in conf:
            self.refresh_token = conf["refresh_token"]
    
    async def check(self) -> bool:
        """检查OpenList是否可用"""
        return await self.is_authenticated()
    
    async def _init_session(self):
        """初始化HTTP会话"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "VabHub/1.0",
                    "Accept": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=30)
            )
    
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
        
        return self.access_token is not None
    
    async def get_oauth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """
        获取OAuth登录URL
        
        Args:
            redirect_uri: 回调地址
            state: 状态参数（用于防止CSRF攻击）
        
        Returns:
            OAuth登录URL
        """
        if not state:
            state = secrets.token_urlsafe(32)
        self._state = state
        
        # OpenList OAuth URL
        # 注意：这里使用115网盘的OAuth端点，OpenList作为代理
        params = {
            "client_id": self.app_id or "100197729",  # 使用115网盘的AppID
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": "read write"
        }
        
        # 构建URL
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        oauth_url = f"https://115.com/?ac=open&{query_string}"
        
        return oauth_url
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Tuple[bool, Dict[str, Any]]:
        """
        使用授权码换取访问令牌
        
        Args:
            code: 授权码
            redirect_uri: 回调地址
        
        Returns:
            (成功标志, 令牌数据)
        """
        try:
            await self._init_session()
            
            # 通过OpenList交换令牌
            # 注意：OpenList的实际API端点可能需要根据文档调整
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self.app_id or "100197729",
                "client_secret": self.app_secret
            }
            
            async with self.session.post(
                f"{self.server_url}/oauth/token",
                json=data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"OpenList交换令牌失败: {error_text}")
                    return False, {"error": error_text}
                
                result = await response.json()
                
                # 提取令牌信息
                self.access_token = result.get("access_token")
                self.refresh_token = result.get("refresh_token")
                expires_in = result.get("expires_in", 3600)
                self.expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info("OpenList OAuth令牌获取成功")
                return True, {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "expires_in": expires_in,
                    "token_type": result.get("token_type", "Bearer")
                }
        except Exception as e:
            logger.error(f"OpenList交换令牌失败: {e}")
            return False, {"error": str(e)}
    
    async def refresh_token(self) -> bool:
        """刷新访问令牌"""
        try:
            if not self.refresh_token:
                return False
            
            await self._init_session()
            
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.app_id or "100197729",
                "client_secret": self.app_secret
            }
            
            async with self.session.post(
                f"{self.server_url}/oauth/token",
                json=data
            ) as response:
                if response.status != 200:
                    return False
                
                result = await response.json()
                
                self.access_token = result.get("access_token")
                self.refresh_token = result.get("refresh_token")
                expires_in = result.get("expires_in", 3600)
                self.expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info("OpenList访问令牌刷新成功")
                return True
        except Exception as e:
            logger.error(f"OpenList刷新令牌失败: {e}")
            return False
    
    async def get_cookie_from_token(self) -> Optional[str]:
        """
        从OAuth Token获取Cookie
        注意：这个方法可能需要根据OpenList的实际实现调整
        
        Returns:
            Cookie字符串
        """
        try:
            if not self.access_token:
                return None
            
            # 通过OpenList API获取Cookie
            # 注意：这个API端点可能需要根据OpenList文档调整
            await self._init_session()
            
            async with self.session.get(
                f"{self.server_url}/api/115/cookie",
                headers={"Authorization": f"Bearer {self.access_token}"}
            ) as response:
                if response.status != 200:
                    return None
                
                result = await response.json()
                cookie = result.get("cookie")
                
                return cookie
        except Exception as e:
            logger.error(f"从OpenList获取Cookie失败: {e}")
            return None
    
    # 以下方法在OpenList中不直接支持，需要通过115网盘API使用获取的Cookie
    
    async def list_files(self, path: str = "/", recursive: bool = False) -> list:
        """OpenList不直接支持文件列表，需要通过115网盘API"""
        logger.warning("OpenList不直接支持文件操作，请使用115网盘API")
        return []
    
    async def get_file_info(self, file_id: str) -> Optional[CloudFileInfo]:
        """OpenList不直接支持文件信息获取"""
        return None
    
    async def create_folder(self, parent_path: str, name: str) -> Optional[CloudFileInfo]:
        """OpenList不直接支持文件夹创建"""
        return None
    
    async def delete_file(self, file_id: str) -> bool:
        """OpenList不直接支持文件删除"""
        return False
    
    async def upload_file(self, local_path: str, remote_path: str, progress_callback: Optional[callable] = None) -> bool:
        """OpenList不直接支持文件上传"""
        return False
    
    async def download_file(self, file_id: str, save_path: str, progress_callback: Optional[callable] = None) -> bool:
        """OpenList不直接支持文件下载"""
        return False
    
    async def get_storage_usage(self) -> Optional[CloudStorageUsage]:
        """OpenList不直接支持存储使用情况查询"""
        return None
    
    async def close(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
            self.session = None

