"""
RSSHub配置加载服务
从JSON文件加载配置到数据库
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.rsshub import RSSHubSource, RSSHubComposite
from app.core.database import Base


class RSSHubConfigLoader:
    """RSSHub配置加载器"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置加载器
        
        Args:
            config_dir: 配置文件目录，默认为项目根目录下的vabhub_rsshub_pack/config/rsshub
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # 默认路径：项目根目录/vabhub_rsshub_pack/config/rsshub
            # 从backend/app/modules/rsshub/config_loader.py向上找到项目根目录
            current_file = Path(__file__)
            # backend/app/modules/rsshub/config_loader.py -> 向上5级到项目根目录
            project_root = current_file.parent.parent.parent.parent.parent
            # 如果项目根目录是VabHub，再向上找vabhub_rsshub_pack
            if project_root.name == "VabHub":
                # 在VabHub的父目录找vabhub_rsshub_pack
                self.config_dir = project_root.parent / "vabhub_rsshub_pack" / "config" / "rsshub"
            else:
                # 直接在项目根目录下找
                self.config_dir = project_root / "vabhub_rsshub_pack" / "config" / "rsshub"
        
        logger.info(f"RSSHub配置目录: {self.config_dir}")
    
    def load_sources_rank(self) -> List[Dict]:
        """加载榜单源配置"""
        file_path = self.config_dir / "rsshub_sources_rank.json"
        if not file_path.exists():
            logger.warning(f"配置文件不存在: {file_path}")
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_sources_updates(self) -> List[Dict]:
        """加载更新源配置"""
        file_path = self.config_dir / "rsshub_sources_updates.json"
        if not file_path.exists():
            logger.warning(f"配置文件不存在: {file_path}")
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_composites(self) -> List[Dict]:
        """加载组合订阅配置"""
        file_path = self.config_dir / "rsshub_composites.json"
        if not file_path.exists():
            logger.warning(f"配置文件不存在: {file_path}")
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def sync_sources_to_db(self, db: AsyncSession) -> int:
        """
        同步源配置到数据库
        
        Args:
            db: 数据库会话
            
        Returns:
            同步的源数量
        """
        # 加载所有源
        rank_sources = self.load_sources_rank()
        update_sources = self.load_sources_updates()
        all_sources = rank_sources + update_sources
        
        count = 0
        for source_data in all_sources:
            source_id = source_data.get('id')
            if not source_id:
                logger.warning(f"源配置缺少id字段: {source_data}")
                continue
            
            # 检查是否已存在
            result = await db.execute(
                select(RSSHubSource).where(RSSHubSource.id == source_id)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # 更新现有源
                existing.name = source_data.get('name', existing.name)
                existing.url_path = source_data.get('url_path', existing.url_path)
                existing.type = source_data.get('type', existing.type)
                existing.group = source_data.get('group', existing.group)
                existing.description = source_data.get('description', existing.description)
                existing.default_enabled = source_data.get('default_enabled', False)
            else:
                # 创建新源
                new_source = RSSHubSource(
                    id=source_id,
                    name=source_data.get('name', ''),
                    url_path=source_data.get('url_path', ''),
                    type=source_data.get('type', 'video'),
                    group=source_data.get('group', 'rank'),
                    description=source_data.get('description'),
                    default_enabled=source_data.get('default_enabled', False)
                )
                db.add(new_source)
            
            count += 1
        
        await db.commit()
        logger.info(f"同步了 {count} 个RSSHub源到数据库")
        return count
    
    async def sync_composites_to_db(self, db: AsyncSession) -> int:
        """
        同步组合订阅配置到数据库
        
        Args:
            db: 数据库会话
            
        Returns:
            同步的组合数量
        """
        composites_data = self.load_composites()
        
        count = 0
        for composite_data in composites_data:
            composite_id = composite_data.get('id')
            if not composite_id:
                logger.warning(f"组合配置缺少id字段: {composite_data}")
                continue
            
            # 检查是否已存在
            result = await db.execute(
                select(RSSHubComposite).where(RSSHubComposite.id == composite_id)
            )
            existing = result.scalar_one_or_none()
            
            source_ids = composite_data.get('sources', [])
            
            if existing:
                # 更新现有组合
                existing.name = composite_data.get('name', existing.name)
                existing.type = composite_data.get('type', existing.type)
                existing.description = composite_data.get('description', existing.description)
                existing.default_enabled = composite_data.get('default_enabled', False)
                
                # 更新关联的源
                await self._update_composite_sources(db, existing, source_ids)
            else:
                # 创建新组合
                new_composite = RSSHubComposite(
                    id=composite_id,
                    name=composite_data.get('name', ''),
                    type=composite_data.get('type', 'video'),
                    description=composite_data.get('description'),
                    default_enabled=composite_data.get('default_enabled', False)
                )
                db.add(new_composite)
                await db.flush()  # 获取ID
                
                # 关联源
                await self._update_composite_sources(db, new_composite, source_ids)
            
            count += 1
        
        await db.commit()
        logger.info(f"同步了 {count} 个RSSHub组合订阅到数据库")
        return count
    
    async def _update_composite_sources(
        self,
        db: AsyncSession,
        composite: RSSHubComposite,
        source_ids: List[str]
    ):
        """更新组合订阅关联的源"""
        # 清空现有关联
        composite.sources.clear()
        
        # 添加新的关联
        for source_id in source_ids:
            result = await db.execute(
                select(RSSHubSource).where(RSSHubSource.id == source_id)
            )
            source = result.scalar_one_or_none()
            if source:
                composite.sources.append(source)
            else:
                logger.warning(f"源不存在: {source_id}，跳过关联")
    
    async def sync_all_to_db(self, db: AsyncSession) -> Dict[str, int]:
        """
        同步所有配置到数据库
        
        Args:
            db: 数据库会话
            
        Returns:
            同步统计: {"sources": count, "composites": count}
        """
        sources_count = await self.sync_sources_to_db(db)
        composites_count = await self.sync_composites_to_db(db)
        
        return {
            "sources": sources_count,
            "composites": composites_count
        }

