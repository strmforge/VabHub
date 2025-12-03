"""
密钥管理器
负责在首次安装时自动生成随机密钥，确保每个实例的唯一性
自动生成随机密钥机制
"""

import os
import secrets
import json
from pathlib import Path
from typing import Optional
from loguru import logger


class SecretManager:
    """密钥管理器"""
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        初始化密钥管理器
        
        Args:
            config_file: 配置文件路径（用于持久化密钥）
        """
        if config_file is None:
            # 默认配置文件路径
            config_file = Path("./data/.vabhub_secrets.json")
        
        self.config_file = config_file
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self._secrets: dict = {}
        self._load_secrets()
    
    def _load_secrets(self):
        """从配置文件加载密钥"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._secrets = json.load(f)
                logger.debug(f"已从 {self.config_file} 加载密钥")
            except Exception as e:
                logger.warning(f"加载密钥文件失败: {e}，将使用新生成的密钥")
                self._secrets = {}
        else:
            logger.info("密钥文件不存在，将生成新密钥")
            self._secrets = {}
    
    def _save_secrets(self):
        """保存密钥到配置文件"""
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 设置文件权限（仅所有者可读写）
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._secrets, f, indent=2, ensure_ascii=False)
            
            # 设置文件权限（Unix系统）
            if os.name != 'nt':  # 非Windows系统
                os.chmod(self.config_file, 0o600)  # 仅所有者可读写
            
            logger.debug(f"密钥已保存到 {self.config_file}")
        except Exception as e:
            logger.error(f"保存密钥文件失败: {e}")
            raise
    
    def get_secret(self, key: str, default: Optional[str] = None) -> str:
        """
        获取密钥（如果不存在则自动生成）
        
        Args:
            key: 密钥名称（如 'SECRET_KEY', 'JWT_SECRET_KEY', 'API_TOKEN'）
            default: 默认值（如果提供，将优先使用环境变量）
        
        Returns:
            密钥值
        """
        # 优先使用环境变量
        env_key = key.upper()
        env_value = os.getenv(env_key)
        if env_value:
            logger.debug(f"使用环境变量 {env_key}")
            return env_value
        
        # 优先检查是否已保存密钥（从配置文件加载的）
        if key in self._secrets:
            logger.debug(f"从配置文件加载 {key}")
            return self._secrets[key]
        
        # 如果提供了默认值，检查是否是占位符
        if default:
            # 检查是否是默认占位符（需要替换）
            placeholder_patterns = [
                "change-this-to-a-random",
                "change-this-to",
                "your-secret-key",
                "default"
            ]
            is_placeholder = any(pattern in default.lower() for pattern in placeholder_patterns)
            
            if is_placeholder:
                # 是占位符，需要生成新密钥
                logger.info(f"检测到 {key} 使用占位符，将生成随机密钥")
                return self._generate_and_save_secret(key)
            else:
                # 不是占位符，可能是用户配置的默认值
                # 使用提供的默认值，但不保存（因为可能是临时的）
                return default
        
        # 生成新密钥
        return self._generate_and_save_secret(key)
    
    def _generate_and_save_secret(self, key: str) -> str:
        """
        生成并保存新密钥
        
        Args:
            key: 密钥名称
        
        Returns:
            生成的密钥
        """
        # 生成32字节（256位）的随机密钥，使用URL安全的base64编码
        secret = secrets.token_urlsafe(32)
        
        # 保存到内存和文件
        self._secrets[key] = secret
        self._save_secrets()
        
        logger.info(f"已为 {key} 生成新的随机密钥（长度: {len(secret)} 字符）")
        return secret
    
    def set_secret(self, key: str, value: str):
        """
        手动设置密钥
        
        Args:
            key: 密钥名称
            value: 密钥值
        """
        self._secrets[key] = value
        self._save_secrets()
        logger.info(f"已更新 {key} 的密钥")
    
    def has_secret(self, key: str) -> bool:
        """
        检查密钥是否存在
        
        Args:
            key: 密钥名称
        
        Returns:
            是否存在
        """
        return key in self._secrets
    
    def get_api_token(self) -> str:
        """
        获取API令牌（用于STRM重定向等）
        
        Returns:
            API令牌
        """
        return self.get_secret('API_TOKEN')
    
    def get_secret_key(self) -> str:
        """
        获取应用密钥
        
        Returns:
            应用密钥
        """
        return self.get_secret('SECRET_KEY', default="change-this-to-a-random-secret-key-in-production")
    
    def get_jwt_secret_key(self) -> str:
        """
        获取JWT密钥
        
        Returns:
            JWT密钥
        """
        return self.get_secret('JWT_SECRET_KEY', default="change-this-to-a-random-jwt-secret-key-in-production")


# 全局实例
_secret_manager: Optional[SecretManager] = None


def get_secret_manager() -> SecretManager:
    """
    获取密钥管理器实例（单例模式）
    
    Returns:
        密钥管理器实例
    """
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = SecretManager()
    return _secret_manager


def initialize_secrets():
    """
    初始化密钥（在应用启动时调用）
    确保所有必需的密钥都已生成
    """
    manager = get_secret_manager()
    
    # 初始化必需的密钥
    manager.get_secret_key()  # SECRET_KEY
    manager.get_jwt_secret_key()  # JWT_SECRET_KEY
    manager.get_api_token()  # API_TOKEN
    
    logger.info("密钥初始化完成（所有密钥已生成或加载）")

