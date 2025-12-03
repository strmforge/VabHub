"""
站点域名配置模型
支持多域名管理，用户可自行配置和切换域名，无需等待版本更新
"""

from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from typing import List, Optional


class SiteDomainConfig(Base):
    """
    站点域名配置表
    支持多域名管理：active（活跃域名）、deprecated（废弃域名）
    """
    __tablename__ = "site_domain_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # 活跃域名列表（JSON数组）
    active_domains = Column(JSON, nullable=False, default=list)
    # 废弃域名列表（JSON数组）
    deprecated_domains = Column(JSON, nullable=False, default=list)
    
    # 当前使用的域名（从active_domains中选择）
    current_domain = Column(String(500), nullable=True)
    
    # 域名切换历史（JSON数组，记录切换时间、原因等）
    switch_history = Column(JSON, nullable=False, default=list)
    
    # 自动检测开关（是否自动检测并切换域名）
    auto_detect = Column(Integer, default=1)  # 1-启用，0-禁用
    
    # 最后检测时间
    last_detect_time = Column(DateTime, nullable=True)
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联站点
    site = relationship("Site", backref="domain_config")
    
    __table_args__ = (
        Index('idx_site_domain_config_site_id', 'site_id', unique=True),
    )
    
    def get_active_domains(self) -> List[str]:
        """获取活跃域名列表"""
        if isinstance(self.active_domains, list):
            return self.active_domains
        return []
    
    def get_deprecated_domains(self) -> List[str]:
        """获取废弃域名列表"""
        if isinstance(self.deprecated_domains, list):
            return self.deprecated_domains
        return []
    
    def get_current_domain(self) -> Optional[str]:
        """获取当前使用的域名"""
        if self.current_domain:
            return self.current_domain
        # 如果没有设置，返回第一个活跃域名
        active = self.get_active_domains()
        return active[0] if active else None
    
    def add_active_domain(self, domain: str) -> bool:
        """添加活跃域名"""
        active = self.get_active_domains()
        if domain not in active:
            active.append(domain)
            self.active_domains = active
            return True
        return False
    
    def remove_active_domain(self, domain: str) -> bool:
        """移除活跃域名（移动到废弃列表）"""
        active = self.get_active_domains()
        if domain in active:
            active.remove(domain)
            self.active_domains = active
            
            # 添加到废弃列表
            deprecated = self.get_deprecated_domains()
            if domain not in deprecated:
                deprecated.append(domain)
                self.deprecated_domains = deprecated
            
            # 如果当前域名被移除，切换到第一个活跃域名
            if self.current_domain == domain:
                self.current_domain = active[0] if active else None
            
            return True
        return False
    
    def switch_to_domain(self, domain: str, reason: str = "手动切换") -> bool:
        """切换到指定域名"""
        active = self.get_active_domains()
        if domain not in active:
            return False
        
        old_domain = self.current_domain
        self.current_domain = domain
        
        # 记录切换历史
        history = self.switch_history if isinstance(self.switch_history, list) else []
        history.append({
            "from": old_domain,
            "to": domain,
            "reason": reason,
            "time": datetime.utcnow().isoformat()
        })
        # 只保留最近50条记录
        self.switch_history = history[-50:]
        
        return True

