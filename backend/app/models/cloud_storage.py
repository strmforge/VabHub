"""
云存储数据模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from datetime import datetime
from app.core.database import Base


class CloudStorage(Base):
    """云存储配置模型"""
    __tablename__ = "cloud_storages"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # 存储名称
    provider = Column(String(50), nullable=False)  # 提供商：115, rclone, openlist
    enabled = Column(Boolean, default=True)
    
    # 115网盘配置（加密存储，只存储引用）
    app_id = Column(String(100), nullable=True)  # 115网盘AppID
    # app_key 和 app_secret 存储在加密的密钥管理器中
    
    # RClone配置（加密存储）
    rclone_remote_name = Column(String(100), nullable=True)  # RClone远程名称
    rclone_config_path = Column(String(500), nullable=True)  # RClone配置文件路径
    
    # OpenList配置
    openlist_server_url = Column(String(500), nullable=True)  # OpenList服务器地址
    
    # 认证信息（加密存储）
    access_token = Column(Text, nullable=True)  # 访问令牌（加密）
    refresh_token = Column(Text, nullable=True)  # 刷新令牌（加密）
    expires_at = Column(DateTime, nullable=True)  # 令牌过期时间
    user_id = Column(String(100), nullable=True)  # 用户ID
    user_name = Column(String(100), nullable=True)  # 用户名
    
    # 其他配置
    config = Column(JSON, nullable=True)  # 其他配置信息
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CloudStorageAuth(Base):
    """云存储认证记录模型"""
    __tablename__ = "cloud_storage_auths"
    
    id = Column(Integer, primary_key=True, index=True)
    storage_id = Column(Integer, nullable=False, index=True)  # 云存储ID
    provider = Column(String(50), nullable=False)  # 提供商
    auth_type = Column(String(50), nullable=False)  # 认证类型：qrcode, oauth, token
    auth_data = Column(JSON, nullable=True)  # 认证数据（二维码、OAuth状态等）
    status = Column(String(20), default="pending")  # 状态：pending, scanning, confirmed, expired
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

