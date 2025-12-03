"""
站点Logo资源加载器
从resources/site-logos/目录加载SVG Logo资源
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger


class SiteLogoResourceLoader:
    """站点Logo资源加载器"""
    
    def __init__(self, resources_dir: Optional[str] = None):
        """
        初始化资源加载器
        
        Args:
            resources_dir: 资源目录路径，如果为None，自动查找项目根目录下的resources目录
        """
        if resources_dir:
            self.resources_dir = Path(resources_dir)
        else:
            # 自动查找项目根目录
            current_file = Path(__file__)
            # 从 backend/app/modules/site_icon/resource_loader.py 向上找到项目根目录
            project_root = current_file.parent.parent.parent.parent.parent
            self.resources_dir = project_root / "resources" / "site-logos"
        
        self.catalog_path = self.resources_dir.parent / "catalog.json"
        self._catalog = None
        self._logo_cache: Dict[str, str] = {}
        
        logger.info(f"站点Logo资源目录: {self.resources_dir}")
    
    def _load_catalog(self) -> Dict[str, Any]:
        """加载资源目录文件"""
        if self._catalog is not None:
            return self._catalog
        
        if not self.catalog_path.exists():
            logger.debug(f"资源目录文件不存在: {self.catalog_path}")
            self._catalog = {"logos": {}}
            return self._catalog
        
        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                self._catalog = json.load(f)
            return self._catalog
        except Exception as e:
            logger.error(f"加载资源目录文件失败: {e}")
            self._catalog = {"logos": {}}
            return self._catalog
    
    def get_logo(self, site_id: str) -> Optional[str]:
        """
        获取站点Logo SVG内容
        
        Args:
            site_id: 站点ID（用于匹配文件名，如 "mantou" 对应 "mantou.svg"）
            
        Returns:
            SVG内容字符串，如果不存在返回None
        """
        # 检查缓存
        if site_id in self._logo_cache:
            return self._logo_cache[site_id]
        
        # 检查资源目录是否存在
        if not self.resources_dir.exists():
            logger.debug(f"资源目录不存在: {self.resources_dir}")
            return None
        
        # 尝试加载SVG文件
        logo_path = self.resources_dir / f"{site_id}.svg"
        if not logo_path.exists():
            logger.debug(f"Logo文件不存在: {logo_path}")
            return None
        
        try:
            with open(logo_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            # 缓存
            self._logo_cache[site_id] = svg_content
            logger.debug(f"成功加载Logo: {site_id}")
            return svg_content
        except Exception as e:
            logger.error(f"读取Logo文件失败: {logo_path}, {e}")
            return None
    
    def list_logos(self) -> Dict[str, str]:
        """
        列出所有可用的Logo
        
        Returns:
            字典，key为站点ID，value为文件路径
        """
        if not self.resources_dir.exists():
            return {}
        
        logos = {}
        for svg_file in self.resources_dir.glob("*.svg"):
            site_id = svg_file.stem
            logos[site_id] = str(svg_file)
        
        return logos
    
    def get_logo_path(self, site_id: str) -> Optional[str]:
        """
        获取Logo文件路径（用于前端访问）
        
        Args:
            site_id: 站点ID
            
        Returns:
            相对路径，如 "/assets/site-logos/mantou.svg"
        """
        logo_path = self.resources_dir / f"{site_id}.svg"
        if logo_path.exists():
            return f"/assets/site-logos/{site_id}.svg"
        return None

