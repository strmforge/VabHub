"""
云存储密钥管理器
使用Fernet加密存储115网盘、RClone和OpenList的密钥
"""

import os
import json
import base64
import secrets
from typing import Dict, Optional, Any
from pathlib import Path
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from loguru import logger


class CloudKeyManager:
    """云存储密钥管理器（使用Fernet加密）"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        初始化密钥管理器
        
        Args:
            storage_path: 密钥存储文件路径，默认使用 ~/.vabhub/cloud_keys.encrypted
        """
        if storage_path:
            self.storage_path = Path(storage_path).expanduser()
        else:
            self.storage_path = Path.home() / ".vabhub" / "cloud_keys.encrypted"
        
        # 确保目录存在
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 获取或创建主密钥
        self.master_key = self._get_or_create_master_key()
        
        # 创建Fernet加密器
        self.fernet = Fernet(self.master_key)
        
        # 加载密钥
        self.keys: Dict[str, Dict[str, Any]] = {}
        self._load_keys()
    
    def _get_or_create_master_key(self) -> bytes:
        """获取或创建主密钥"""
        # 尝试从环境变量获取
        master_key_env = os.getenv("VABHUB_CLOUD_MASTER_KEY")
        if master_key_env:
            try:
                return base64.urlsafe_b64decode(master_key_env.encode())
            except Exception as e:
                logger.warning(f"从环境变量读取主密钥失败: {e}")
        
        # 尝试从文件获取
        key_file = Path.home() / ".vabhub" / ".master_key"
        if key_file.exists():
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"从文件读取主密钥失败: {e}")
        
        # 生成新密钥
        master_key = Fernet.generate_key()
        try:
            # 保存到文件
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(master_key)
            # 设置文件权限（仅限所有者可读写）
            os.chmod(key_file, 0o600)
            logger.info(f"已生成并保存主密钥到: {key_file}")
            logger.warning("⚠️ 请妥善保管主密钥文件，丢失后将无法解密存储的密钥！")
        except Exception as e:
            logger.warning(f"保存主密钥文件失败: {e}")
        
        return master_key
    
    def _encrypt(self, data: str) -> str:
        """加密数据"""
        encrypted_data = self.fernet.encrypt(data.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
    
    def _decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise ValueError("解密失败，可能是主密钥不匹配")
    
    def _load_keys(self):
        """加载密钥"""
        if not self.storage_path.exists():
            logger.info(f"密钥文件不存在: {self.storage_path}")
            return
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查是否加密
            if data.get('encrypted', False):
                # 解密数据
                encrypted_keys = data.get('keys', '')
                if encrypted_keys:
                    decrypted_keys_json = self._decrypt(encrypted_keys)
                    self.keys = json.loads(decrypted_keys_json)
                else:
                    self.keys = {}
            else:
                # 未加密的旧数据，需要迁移
                self.keys = data.get('keys', {})
                # 保存时自动加密
                self._save_keys()
            
            logger.info(f"已加载 {len(self.keys)} 个云存储密钥")
        except Exception as e:
            logger.error(f"加载密钥失败: {e}")
            self.keys = {}
    
    def _save_keys(self):
        """保存密钥（加密存储）"""
        try:
            # 序列化数据
            keys_json = json.dumps(self.keys, ensure_ascii=False)
            
            # 加密密钥数据
            encrypted_keys = self._encrypt(keys_json)
            
            data = {
                "version": "1.0",
                "encrypted": True,
                "updated_at": datetime.now().isoformat(),
                "keys": encrypted_keys
            }
            
            # 保存到文件
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # 设置文件权限（仅限所有者可读写）
            os.chmod(self.storage_path, 0o600)
            
            logger.debug(f"密钥已保存到: {self.storage_path}")
        except Exception as e:
            logger.error(f"保存密钥失败: {e}")
            raise
    
    def set_115_keys(
        self,
        app_id: str,
        app_key: str,
        app_secret: Optional[str] = None
    ):
        """设置115网盘密钥（只需要AppID和AppKey，AppSecret可选）"""
        self.keys['115'] = {
            "provider": "115",
            "app_id": app_id,
            "app_key": app_key,
            "app_secret": app_secret,  # 可选，115网盘API不需要
            "updated_at": datetime.now().isoformat()
        }
        self._save_keys()
        logger.info("115网盘密钥已保存（已加密）")
    
    def get_115_keys(self) -> Optional[Dict[str, str]]:
        """获取115网盘密钥"""
        if '115' not in self.keys:
            return None
        keys = self.keys['115'].copy()
        # 移除时间戳和provider标识
        keys.pop('updated_at', None)
        keys.pop('provider', None)
        # 如果app_secret为空，也移除它
        if keys.get('app_secret') is None:
            keys.pop('app_secret', None)
        return keys
    
    def set_rclone_config(self, config_content: str, remote_name: str = "VabHub"):
        """设置RClone配置"""
        self.keys['rclone'] = {
            "provider": "rclone",
            "remote_name": remote_name,
            "config_content": config_content,
            "updated_at": datetime.now().isoformat()
        }
        self._save_keys()
        logger.info("RClone配置已保存（已加密）")
    
    def get_rclone_config(self) -> Optional[Dict[str, str]]:
        """获取RClone配置"""
        if 'rclone' not in self.keys:
            return None
        config = self.keys['rclone'].copy()
        config.pop('updated_at', None)
        config.pop('provider', None)
        return config
    
    def set_openlist_config(
        self,
        server_url: str,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None
    ):
        """设置OpenList配置"""
        self.keys['openlist'] = {
            "provider": "openlist",
            "server_url": server_url,
            "app_id": app_id,
            "app_secret": app_secret,
            "updated_at": datetime.now().isoformat()
        }
        self._save_keys()
        logger.info("OpenList配置已保存（已加密）")
    
    def get_openlist_config(self) -> Optional[Dict[str, str]]:
        """获取OpenList配置"""
        if 'openlist' not in self.keys:
            return None
        config = self.keys['openlist'].copy()
        config.pop('updated_at', None)
        config.pop('provider', None)
        return config
    
    def has_keys(self, provider: str) -> bool:
        """检查是否有指定提供商的密钥"""
        return provider in self.keys
    
    def delete_keys(self, provider: str):
        """删除指定提供商的密钥"""
        if provider in self.keys:
            del self.keys[provider]
            self._save_keys()
            logger.info(f"{provider} 密钥已删除")
        else:
            logger.warning(f"{provider} 密钥不存在")
    
    # ==================== API密钥管理 ====================
    
    def set_api_key(self, api_name: str, api_key: str, api_pin: Optional[str] = None):
        """
        设置API密钥（加密存储）
        
        Args:
            api_name: API名称（tmdb, tvdb, fanart等）
            api_key: API Key
            api_pin: API PIN（可选，如TVDB）
        """
        self.keys[f'api_{api_name}'] = {
            "provider": f"api_{api_name}",
            "api_key": api_key,
            "api_pin": api_pin,
            "updated_at": datetime.now().isoformat()
        }
        self._save_keys()
        logger.info(f"{api_name.upper()} API密钥已保存（已加密）")
    
    def get_api_key(self, api_name: str) -> Optional[Dict[str, str]]:
        """
        获取API密钥
        
        Args:
            api_name: API名称（tmdb, tvdb, fanart等）
            
        Returns:
            API密钥字典，包含api_key和可选的api_pin
        """
        key_name = f'api_{api_name}'
        if key_name not in self.keys:
            return None
        
        api_data = self.keys[key_name].copy()
        api_data.pop('updated_at', None)
        api_data.pop('provider', None)
        
        # 如果api_pin为空，也移除它
        if api_data.get('api_pin') is None:
            api_data.pop('api_pin', None)
        
        return api_data
    
    def has_api_key(self, api_name: str) -> bool:
        """检查是否有指定API的密钥"""
        return f'api_{api_name}' in self.keys
    
    def delete_api_key(self, api_name: str):
        """删除指定API的密钥"""
        key_name = f'api_{api_name}'
        if key_name in self.keys:
            del self.keys[key_name]
            self._save_keys()
            logger.info(f"{api_name.upper()} API密钥已删除")
        else:
            logger.warning(f"{api_name.upper()} API密钥不存在")


# 全局密钥管理器实例
_key_manager: Optional[CloudKeyManager] = None


def get_key_manager() -> CloudKeyManager:
    """获取全局密钥管理器实例"""
    global _key_manager
    if _key_manager is None:
        _key_manager = CloudKeyManager()
    return _key_manager

