"""
下载搜索服务
TG-BOT-DL-1: 为 Telegram Bot 提供安全的下载候选搜索
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel
from loguru import logger

from app.modules.search.indexer_manager import IndexerManager
from app.core.intel_local.hr_policy import evaluate_hr_for_site
from app.core.intel_local.repo import HRCasesRepository


class SafeDownloadCandidate(BaseModel):
    """安全下载候选"""
    id: str                     # 内部用的唯一ID（站点+info_hash）
    title: str
    site: str
    size_bytes: Optional[int] = None
    seeders: Optional[int] = None
    leechers: Optional[int] = None
    is_hr: bool = False
    is_h35: bool = False        # H3/H5特殊标记
    is_free: bool = False
    is_half_free: bool = False  # 2x/half 之类
    info_hash: Optional[str] = None
    magnet_link: Optional[str] = None
    torrent_url: Optional[str] = None
    resolution: Optional[str] = None
    quality: Optional[str] = None
    source: Optional[str] = None


class DownloadSearchService:
    """下载搜索服务"""
    
    def __init__(self):
        self.indexer_manager = IndexerManager()
    
    async def search_safe_candidates(
        self,
        user,
        query: str,
        *,
        limit_raw: int = 30,
        limit_safe: int = 10,
        allow_hr: bool = False,
        allow_h3h5: bool = False,
        strict_free_only: bool = True,
        session_factory=None,
    ) -> Tuple[List[SafeDownloadCandidate], Dict[str, Any]]:
        """
        返回(安全候选列表, 统计信息dict)，统计信息用于给TG输出提示。
        """
        logger.info(f"[download_search] 开始搜索安全候选: query='{query}', user={user.id}")
        
        # 初始化统计信息
        stats = {
            "total": 0,
            "filtered_by_site": 0,
            "filtered_by_quality": 0,
            "filtered_by_hr": 0,
            "filtered_by_free": 0,
            "safe_count": 0,
        }
        
        try:
            # 1. 调用索引器搜索
            raw_results = await self.indexer_manager.search_all(
                query=query,
                timeout=30
            )
            stats["total"] = len(raw_results)
            
            if not raw_results:
                logger.info(f"[download_search] 无搜索结果: query='{query}'")
                return [], stats
            
            # 限制原始结果数量
            raw_results = raw_results[:limit_raw]
            
            # 2. 解析和标准化结果
            candidates = []
            for result in raw_results:
                candidate = self._parse_result_to_candidate(result)
                if candidate:
                    candidates.append(candidate)
            
            # 3. 应用安全策略过滤
            safe_candidates = []
            hr_repo = None
            if session_factory:
                from app.core.intel_local.repo.sqlalchemy import SqlAlchemyHRCasesRepository
                hr_repo = SqlAlchemyHRCasesRepository(session_factory)
            
            for candidate in candidates:
                # 检查站点过滤
                if self._is_site_blocked(candidate.site):
                    stats["filtered_by_site"] += 1
                    continue
                
                # 检查质量过滤
                if self._is_quality_blocked(candidate):
                    stats["filtered_by_quality"] += 1
                    continue
                
                # 检查HR状态
                if not allow_hr:
                    is_hr_site = await self._check_site_hr_status(candidate.site, hr_repo)
                    candidate.is_hr = is_hr_site
                    if is_hr_site:
                        stats["filtered_by_hr"] += 1
                        continue
                
                # 检查H3/H5
                if not allow_h3h5 and candidate.is_h35:
                    stats["filtered_by_quality"] += 1
                    continue
                
                # 检查Free状态
                if strict_free_only and not (candidate.is_free or candidate.is_half_free):
                    stats["filtered_by_free"] += 1
                    continue
                
                safe_candidates.append(candidate)
            
            # 4. 排序和截取
            safe_candidates = self._sort_candidates(safe_candidates)
            safe_candidates = safe_candidates[:limit_safe]
            
            stats["safe_count"] = len(safe_candidates)
            
            logger.info(f"[download_search] 搜索完成: total={stats['total']}, safe={stats['safe_count']}")
            return safe_candidates, stats
            
        except Exception as e:
            logger.error(f"[download_search] 搜索失败: {e}")
            return [], stats
    
    def _parse_result_to_candidate(self, result: Dict[str, Any]) -> Optional[SafeDownloadCandidate]:
        """解析索引器结果为安全候选"""
        try:
            title = result.get('title', '')
            if not title:
                return None
            
            # 解析Free状态
            is_free, is_half_free = self._parse_free_status(title)
            
            # 解析H3/H5状态
            is_h35 = self._parse_h35_status(title)
            
            # 生成唯一ID
            site = result.get('site', 'unknown')
            info_hash = result.get('info_hash') or self._extract_info_hash(result.get('magnet_link', ''))
            candidate_id = f"{site}:{info_hash}" if info_hash else f"{site}:{hash(title)}"
            
            return SafeDownloadCandidate(
                id=candidate_id,
                title=title,
                site=site,
                size_bytes=int(result.get('size_gb', 0) * 1024 * 1024 * 1024) if result.get('size_gb') else None,
                seeders=result.get('seeders'),
                leechers=result.get('leechers'),
                is_free=is_free,
                is_half_free=is_half_free,
                is_h35=is_h35,
                info_hash=info_hash,
                magnet_link=result.get('magnet_link'),
                torrent_url=result.get('torrent_url'),
                resolution=result.get('resolution'),
                quality=result.get('quality'),
                source=result.get('source'),
            )
        except Exception as e:
            logger.error(f"[download_search] 解析结果失败: {e}")
            return None
    
    def _parse_free_status(self, title: str) -> Tuple[bool, bool]:
        """从标题解析Free状态"""
        title_upper = title.upper()
        
        # Free模式
        free_patterns = [
            r'\bFREE\b',
            r'\bFREEDOWNLOAD\b',
            r'\b免费\b',
            r'\bFREE下载\b'
        ]
        
        # Half-Free/2x模式
        half_free_patterns = [
            r'\b2X[FREE]*\b',
            r'\b2\.?X[FREE]*\b',
            r'\b50%[FREE]*\b',
            r'\bHALF[FREE]*\b',
            r'\b半免费\b',
            r'\b50%免费\b'
        ]
        
        is_free = any(re.search(pattern, title_upper) for pattern in free_patterns)
        is_half_free = any(re.search(pattern, title_upper) for pattern in half_free_patterns)
        
        return is_free, is_half_free
    
    def _parse_h35_status(self, title: str) -> bool:
        """从标题解析H3/H5状态"""
        title_upper = title.upper()
        
        h35_patterns = [
            r'\bH3\b',
            r'\bH5\b',
            r'\bH3\.?5\b',
            r'\bH\.?3\.?5\b'
        ]
        
        return any(re.search(pattern, title_upper) for pattern in h35_patterns)
    
    def _is_site_blocked(self, site: str) -> bool:
        """检查站点是否被阻止"""
        # TODO: 集成站点屏蔽逻辑
        # 这里可以检查用户设置的屏蔽站点列表
        blocked_sites = []  # 从用户设置或全局配置获取
        return site.lower() in [s.lower() for s in blocked_sites]
    
    def _is_quality_blocked(self, candidate: SafeDownloadCandidate) -> bool:
        """检查质量是否被阻止"""
        # TODO: 集成质量过滤逻辑
        # 这里可以检查分辨率、编码等质量要求
        return False
    
    async def _check_site_hr_status(self, site: str, hr_repo) -> bool:
        """检查站点HR状态"""
        try:
            if not hr_repo:
                # 如果没有HR repo，暂时返回False（不阻止）
                logger.debug(f"[download_search] HR repo未初始化，跳过HR检查: {site}")
                return False
            
            # 调用HR策略检查
            from app.core.intel_local.actions import LocalIntelActionType
            actions = await evaluate_hr_for_site(site=site, repo=hr_repo)
            
            # 检查是否有HR风险标记（更精确的检测）
            risk_actions = [
                action for action in actions 
                if action.type in [
                    LocalIntelActionType.HR_MARK_RISK,
                    LocalIntelActionType.HR_RECORD_PROGRESS,
                    LocalIntelActionType.TORRENT_HR_PENALTY
                ]
            ]
            
            # 如果有HR风险动作，说明站点处于HR状态
            if risk_actions:
                logger.debug(f"[download_search] 站点 {site} 检测到HR风险: {len(risk_actions)} 个动作")
                return True
            
            return False
        except Exception as e:
            logger.warning(f"[download_search] HR状态检查失败: {e}")
            return False
    
    def _sort_candidates(self, candidates: List[SafeDownloadCandidate]) -> List[SafeDownloadCandidate]:
        """排序候选列表"""
        def sort_key(candidate: SafeDownloadCandidate):
            # 优先级: Free > Half-Free > 其他
            priority = 0
            if candidate.is_free:
                priority = 2
            elif candidate.is_half_free:
                priority = 1
            
            # 然后按做种数排序
            seeders = candidate.seeders or 0
            
            return (-priority, -seeders)
        
        return sorted(candidates, key=sort_key)
    
    def _extract_info_hash(self, magnet_link: str) -> Optional[str]:
        """从磁力链接提取info_hash"""
        if not magnet_link:
            return None
        
        match = re.search(r'btih:([a-fA-F0-9]{40})', magnet_link, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        
        return None


# 全局服务实例
download_search_service = DownloadSearchService()
