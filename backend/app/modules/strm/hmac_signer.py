"""
STRM HMAC签名工具
参考vabhub_stream_gateway实现，提供HMAC URL签名功能
"""

import hmac
import hashlib
import time
from typing import Optional, Tuple
from loguru import logger


class STRMHMACSigner:
    """STRM HMAC签名器"""
    
    def __init__(self, secret: Optional[str] = None):
        """
        初始化HMAC签名器
        
        Args:
            secret: HMAC密钥（如果为None，从系统配置获取）
        """
        if secret:
            self.secret = secret
        else:
            # 从系统配置获取密钥
            from app.core.config import settings
            # 优先使用STRM专用的HMAC密钥，如果没有则使用JWT密钥
            self.secret = getattr(settings, 'STRM_HMAC_SECRET', None) or settings.JWT_SECRET_KEY_DYNAMIC
            if not self.secret or self.secret == "change-this-to-a-random-jwt-secret-key-in-production":
                logger.warning("STRM HMAC密钥未配置，使用默认密钥（不安全）")
                self.secret = "dev-secret-change-in-production"
        
        logger.debug("STRM HMAC签名器初始化完成")
    
    def sign_path(self, path: str, timestamp: int) -> str:
        """
        对路径和时间戳进行HMAC签名
        
        Args:
            path: 路径（如 /api/strm/stream/115/pickcode123）
            timestamp: 时间戳（Unix时间戳）
            
        Returns:
            HMAC签名（十六进制字符串）
        """
        # 构建签名消息：path|timestamp
        message = f"{path}|{timestamp}".encode('utf-8')
        
        # 使用HMAC-SHA256生成签名
        signature = hmac.new(
            self.secret.encode('utf-8'),
            message,
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify(self, path: str, timestamp: int, signature: str, ttl: int = 3600) -> bool:
        """
        验证HMAC签名
        
        Args:
            path: 路径
            timestamp: 时间戳
            signature: 签名
            ttl: 有效期（秒，默认3600秒=1小时）
            
        Returns:
            验证是否通过
        """
        # 检查时间戳是否在有效期内
        now = int(time.time())
        if timestamp < now - 5:  # 允许5秒的时钟偏差
            logger.debug(f"HMAC签名时间戳过期: {timestamp} < {now - 5}")
            return False
        
        if timestamp > now + ttl:
            logger.debug(f"HMAC签名时间戳超出有效期: {timestamp} > {now + ttl}")
            return False
        
        # 计算期望的签名
        expected_signature = self.sign_path(path, timestamp)
        
        # 使用安全比较（防止时序攻击）
        return hmac.compare_digest(expected_signature, signature)
    
    def generate_signed_url(
        self,
        path: str,
        ttl: int = 3600,
        base_url: Optional[str] = None
    ) -> Tuple[str, int, str]:
        """
        生成带签名的URL
        
        Args:
            path: 路径（如 /api/strm/stream/115/pickcode123）
            ttl: 有效期（秒，默认3600秒=1小时）
            base_url: 基础URL（可选，如果提供则返回完整URL）
            
        Returns:
            (完整URL或路径, 时间戳, 签名)
        """
        # 计算过期时间戳
        timestamp = int(time.time()) + ttl
        
        # 生成签名
        signature = self.sign_path(path, timestamp)
        
        # 构建URL
        if base_url:
            # 如果提供了base_url，返回完整URL
            url = f"{base_url.rstrip('/')}{path}?ts={timestamp}&sig={signature}"
            return (url, timestamp, signature)
        else:
            # 只返回路径和参数
            url = f"{path}?ts={timestamp}&sig={signature}"
            return (url, timestamp, signature)


# 全局单例
_hmac_signer: Optional[STRMHMACSigner] = None


def get_hmac_signer(secret: Optional[str] = None) -> STRMHMACSigner:
    """获取HMAC签名器单例"""
    global _hmac_signer
    if _hmac_signer is None:
        _hmac_signer = STRMHMACSigner(secret)
    return _hmac_signer

