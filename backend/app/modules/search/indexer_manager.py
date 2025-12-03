"""
索引器管理器
管理多个索引器，包括公开站点和私有PT站点
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
from loguru import logger

from app.core.config import settings

from .indexers.base import IndexerBase, IndexerConfig
from .indexers.public_indexer import PublicIndexer
from .indexers.private_indexer import PrivateIndexer


class IndexerManager:
    """索引器管理器"""
    
    def __init__(self):
        self.indexers: Dict[str, IndexerBase] = {}
        self._initialize_default_indexers()
    
    def _initialize_default_indexers(self):
        """初始化默认索引器（公开站点）"""
        # 公开站点（不需要账号）
        public_indexers = [
            IndexerConfig(
                name='1337x',
                base_url='https://1337x.to',
                is_public=True,
                enabled=True
            ),
            IndexerConfig(
                name='Nyaa',
                base_url='https://nyaa.si',
                is_public=True,
                enabled=True
            ),
            IndexerConfig(
                name='YTS',
                base_url='https://yts.mx',
                is_public=True,
                enabled=True
            )
        ]
        
        for config in public_indexers:
            self.add_indexer(PublicIndexer(config))
    
    def add_indexer(self, indexer: IndexerBase):
        """添加索引器"""
        self.indexers[indexer.name.lower()] = indexer
        logger.info(f"已添加索引器: {indexer.name}")
    
    def remove_indexer(self, name: str):
        """移除索引器"""
        if name.lower() in self.indexers:
            del self.indexers[name.lower()]
            logger.info(f"已移除索引器: {name}")
    
    def get_indexer(self, name: str) -> Optional[IndexerBase]:
        """获取索引器"""
        return self.indexers.get(name.lower())
    
    def get_healthy_indexers(self) -> List[IndexerBase]:
        """获取健康的索引器"""
        return [
            indexer for indexer in self.indexers.values()
            if indexer.is_healthy()
        ]
    
    def get_all_indexers(self) -> List[IndexerBase]:
        """获取所有索引器"""
        return list(self.indexers.values())
    
    async def search_all(
        self,
        query: str,
        media_type: Optional[str] = None,
        year: Optional[int] = None,
        indexer_names: Optional[List[str]] = None,
        timeout: int = 30,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        并发搜索所有索引器
        
        Args:
            query: 搜索关键词
            media_type: 媒体类型
            year: 年份
            indexer_names: 指定要搜索的索引器名称列表（None表示搜索所有）
            timeout: 超时时间（秒）
            **kwargs: 其他搜索参数
        
        Returns:
            合并后的搜索结果列表
        """
        # 选择要搜索的索引器
        if indexer_names:
            selected_indexers = [
                self.indexers[name.lower()]
                for name in indexer_names
                if name.lower() in self.indexers and self.indexers[name.lower()].is_healthy()
            ]
        else:
            selected_indexers = self.get_healthy_indexers()
        
        if not selected_indexers:
            logger.warning("没有可用的健康索引器")
            return []
        
        # 创建搜索任务（应用 Site Guard）
        # 注意：开关判断已集中在 scheduler_hooks.before_pt_scan 中
        search_tasks = []
        for indexer in selected_indexers:
            # Local Intel Site Guard: 检查站点是否被阻止
            try:
                from app.core.intel_local.scheduler_hooks import before_pt_scan
                budget = await before_pt_scan(indexer.name)
                
                if budget.get("blocked"):
                    logger.warning(
                        f"LocalIntel: 站点 {indexer.name} 当前处于风控冷却期 "
                        f"(原因: {budget.get('reason')}, 直到: {budget.get('until')})，跳过搜索"
                    )
                    continue  # 跳过被阻止的站点
                
                # 记录扫描预算（可用于后续控制抓取量）
                max_pages = budget.get("max_pages", 0)
                max_minutes = budget.get("max_minutes", 0)
                if max_pages > 0 and max_pages < 999999:  # 排除无限制的情况
                    logger.debug(
                        f"LocalIntel: 站点 {indexer.name} 扫描预算 - "
                        f"最大页数: {max_pages}, 最大分钟数: {max_minutes}"
                    )
                    # TODO: 将预算传递给索引器，用于控制分页抓取
                    # 当前先记录日志，后续可以在索引器中实现分页控制
            except Exception as e:
                logger.warning(f"LocalIntel Site Guard 检查失败 (站点: {indexer.name}): {e}，继续搜索")
            
            task = asyncio.create_task(
                self._search_with_timeout(indexer, query, media_type, year, timeout, **kwargs)
            )
            search_tasks.append((indexer, task))
        
        # 等待所有搜索完成
        all_results = []
        for indexer, task in search_tasks:
            try:
                results = await task
                if results:
                    all_results.extend(results)
                    indexer.reset_errors()
            except Exception as e:
                logger.error(f"索引器 {indexer.name} 搜索异常: {e}")
                indexer.record_error()
        
        logger.info(f"并发搜索完成: {len(selected_indexers)} 个索引器, {len(all_results)} 个结果")
        return all_results
    
    async def _search_with_timeout(
        self,
        indexer: IndexerBase,
        query: str,
        media_type: Optional[str] = None,
        year: Optional[int] = None,
        timeout: int = 30,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """带超时的搜索"""
        try:
            return await asyncio.wait_for(
                indexer.search(query, media_type=media_type, year=year, **kwargs),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"索引器 {indexer.name} 搜索超时")
            indexer.record_error()
            return []
        except Exception as e:
            logger.error(f"索引器 {indexer.name} 搜索失败: {e}")
            indexer.record_error()
            return []
    
    async def health_check_all(self) -> Dict[str, bool]:
        """检查所有索引器的健康状态"""
        health_tasks = [
            (name, indexer.health_check())
            for name, indexer in self.indexers.items()
        ]
        
        health_results = {}
        for name, task in health_tasks:
            try:
                is_healthy = await task
                health_results[name] = is_healthy
            except Exception as e:
                logger.error(f"索引器 {name} 健康检查异常: {e}")
                health_results[name] = False
        
        return health_results
    
    async def get_indexer_statuses(self) -> Dict[str, Dict[str, Any]]:
        """获取所有索引器的状态"""
        statuses = {}
        for name, indexer in self.indexers.items():
            statuses[name] = indexer.get_status()
        return statuses

