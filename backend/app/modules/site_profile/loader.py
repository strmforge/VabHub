"""
站点配置文件加载器
从resources/site-profiles/目录加载YAML配置文件
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
from loguru import logger


class SiteProfileLoader:
    """站点配置文件加载器"""
    
    def __init__(self, resources_dir: Optional[str] = None):
        """
        初始化配置文件加载器
        
        Args:
            resources_dir: 资源目录路径，如果为None，自动查找项目根目录下的resources目录
        """
        if resources_dir:
            self.profiles_dir = Path(resources_dir)
        else:
            # 自动查找项目根目录
            current_file = Path(__file__)
            # 从 backend/app/modules/site_profile/loader.py 向上找到项目根目录
            project_root = current_file.parent.parent.parent.parent.parent
            self.profiles_dir = project_root / "resources" / "site-profiles"
        
        self._profiles_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"站点配置文件目录: {self.profiles_dir}")
    
    def load_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        加载站点配置文件
        
        Args:
            profile_id: 配置文件ID（文件名，不含扩展名）
            
        Returns:
            配置文件字典，如果不存在返回None
        """
        # 检查缓存
        if profile_id in self._profiles_cache:
            return self._profiles_cache[profile_id]
        
        # 检查资源目录是否存在
        if not self.profiles_dir.exists():
            logger.debug(f"配置文件目录不存在: {self.profiles_dir}")
            return None
        
        # 尝试加载YAML文件
        profile_path = self.profiles_dir / f"{profile_id}.yml"
        if not profile_path.exists():
            logger.debug(f"配置文件不存在: {profile_path}")
            return None
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = yaml.safe_load(f)
            
            # 缓存
            self._profiles_cache[profile_id] = profile_data
            logger.debug(f"成功加载配置文件: {profile_id}")
            return profile_data
        except Exception as e:
            logger.error(f"读取配置文件失败: {profile_path}, {e}")
            return None
    
    def list_profiles(self) -> List[str]:
        """
        列出所有可用的配置文件
        
        Returns:
            配置文件ID列表
        """
        if not self.profiles_dir.exists():
            return []
        
        profiles = []
        for yml_file in self.profiles_dir.glob("*.yml"):
            profile_id = yml_file.stem
            if profile_id != "_template":  # 排除模板文件
                profiles.append(profile_id)
        
        return profiles
    
    def find_profile_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        根据域名查找匹配的配置文件
        
        Args:
            domain: 站点域名
            
        Returns:
            匹配的配置文件，如果不存在返回None
        """
        profiles = self.list_profiles()
        
        for profile_id in profiles:
            profile = self.load_profile(profile_id)
            if not profile:
                continue
            
            # 检查域名是否匹配
            meta = profile.get("meta", {})
            domains = meta.get("domains", [])
            
            for profile_domain in domains:
                if domain in profile_domain or profile_domain in domain:
                    logger.debug(f"找到匹配的配置文件: {profile_id} (域名: {domain})")
                    return profile
        
        return None

