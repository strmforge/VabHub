"""
Telegram Bot状态管理
TG-BOT-TMDB-SEARCH P2实现：搜索结果缓存系统
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from loguru import logger

from app.services.tmdb_search_service import TmdbSearchItem
from app.services.download_search_service import SafeDownloadCandidate
from app.schemas.reading_hub import ReadingOngoingItem, ReadingActivityItem, ReadingShelfItem


@dataclass
class UserTmdbSearchState:
    """用户TMDB搜索状态"""
    user_id: int          # VabHub内部user.id
    tg_user_id: int       # Telegram user id
    created_at: datetime
    items: List[TmdbSearchItem]  # TMDB搜索结果


@dataclass
class UserDownloadSearchState:
    """用户下载搜索状态"""
    user_id: int          # VabHub内部user.id
    tg_user_id: int       # Telegram user id
    created_at: datetime
    query: str            # 搜索关键词
    candidates: List[SafeDownloadCandidate]  # 安全下载候选
    stats: Dict           # 搜索统计信息


@dataclass
class UserReadingListState:
    """用户阅读列表状态"""
    user_id: int          # VabHub内部user.id
    tg_user_id: int       # Telegram user id
    created_at: datetime
    items: List[ReadingOngoingItem]  # 阅读列表
    item_type: str        # "mixed"/"ebook"/"audiobook"/"manga"


@dataclass
class UserReadingActivityState:
    """用户阅读活动状态"""
    user_id: int          # VabHub内部user.id
    tg_user_id: int       # Telegram user id
    created_at: datetime
    items: List[ReadingActivityItem]  # 最近活动列表


class TmdbSearchCache:
    """TMDB搜索结果缓存"""
    
    def __init__(self) -> None:
        self._by_tg_user: Dict[int, UserTmdbSearchState] = {}
    
    def set_results(self, tg_user_id: int, user_id: int, items: List[TmdbSearchItem]) -> None:
        """
        缓存用户的搜索结果
        
        Args:
            tg_user_id: Telegram用户ID
            user_id: VabHub内部用户ID
            items: TMDB搜索结果列表
        """
        # 清理过期缓存
        self.clear_expired()
        
        # 创建新的搜索状态
        state = UserTmdbSearchState(
            user_id=user_id,
            tg_user_id=tg_user_id,
            created_at=datetime.utcnow(),
            items=items
        )
        
        self._by_tg_user[tg_user_id] = state
        logger.debug(f"Cached TMDB search results for tg_user {tg_user_id}, {len(items)} items")
    
    def get_results(self, tg_user_id: int) -> UserTmdbSearchState | None:
        """
        获取用户的搜索结果缓存
        
        Args:
            tg_user_id: Telegram用户ID
            
        Returns:
            搜索状态，如果不存在或已过期则返回None
        """
        # 清理过期缓存
        self.clear_expired()
        
        state = self._by_tg_user.get(tg_user_id)
        if state:
            logger.debug(f"Retrieved TMDB search cache for tg_user {tg_user_id}, {len(state.items)} items")
        return state
    
    def clear_expired(self, ttl_seconds: int = 600) -> None:
        """
        清理过期的缓存条目
        
        Args:
            ttl_seconds: 缓存TTL，默认10分钟
        """
        if not self._by_tg_user:
            return
        
        current_time = datetime.utcnow()
        expired_users = []
        
        for tg_user_id, state in self._by_tg_user.items():
            if current_time - state.created_at > timedelta(seconds=ttl_seconds):
                expired_users.append(tg_user_id)
        
        for tg_user_id in expired_users:
            del self._by_tg_user[tg_user_id]
            logger.debug(f"Expired TMDB search cache for tg_user {tg_user_id}")
        
        if expired_users:
            logger.info(f"Cleared {len(expired_users)} expired TMDB search cache entries")
    
    def clear_user(self, tg_user_id: int) -> None:
        """
        清理特定用户的缓存
        
        Args:
            tg_user_id: Telegram用户ID
        """
        if tg_user_id in self._by_tg_user:
            del self._by_tg_user[tg_user_id]
            logger.debug(f"Cleared TMDB search cache for tg_user {tg_user_id}")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        获取缓存统计信息
        
        Returns:
            包含缓存条目数等信息的字典
        """
        self.clear_expired()
        return {
            "total_cached_users": len(self._by_tg_user),
            "cached_items_total": sum(len(state.items) for state in self._by_tg_user.values())
        }


class DownloadSearchCache:
    """下载搜索结果缓存"""
    
    def __init__(self) -> None:
        self._by_tg_user: Dict[int, UserDownloadSearchState] = {}
    
    def set_results(self, tg_user_id: int, user_id: int, query: str, candidates: List[SafeDownloadCandidate], stats: Dict) -> None:
        """
        缓存用户的下载搜索结果
        
        Args:
            tg_user_id: Telegram用户ID
            user_id: VabHub内部用户ID
            query: 搜索关键词
            candidates: 安全下载候选列表
            stats: 搜索统计信息
        """
        # 清理过期缓存
        self.clear_expired()
        
        # 创建新的搜索状态
        state = UserDownloadSearchState(
            user_id=user_id,
            tg_user_id=tg_user_id,
            created_at=datetime.utcnow(),
            query=query,
            candidates=candidates,
            stats=stats
        )
        
        self._by_tg_user[tg_user_id] = state
        logger.debug(f"Cached download search results for tg_user {tg_user_id}, {len(candidates)} candidates")
    
    def get_results(self, tg_user_id: int) -> UserDownloadSearchState | None:
        """
        获取用户的下载搜索结果
        
        Args:
            tg_user_id: Telegram用户ID
            
        Returns:
            用户的搜索状态，如果不存在或过期则返回None
        """
        # 清理过期缓存
        self.clear_expired()
        
        return self._by_tg_user.get(tg_user_id)
    
    def clear_expired(self, ttl_seconds: int = 600) -> None:
        """
        清理过期的缓存条目
        
        Args:
            ttl_seconds: 缓存TTL，默认10分钟
        """
        if not self._by_tg_user:
            return
        
        current_time = datetime.utcnow()
        expired_users = []
        
        for tg_user_id, state in self._by_tg_user.items():
            if current_time - state.created_at > timedelta(seconds=ttl_seconds):
                expired_users.append(tg_user_id)
        
        for tg_user_id in expired_users:
            del self._by_tg_user[tg_user_id]
            logger.debug(f"Expired download search cache for tg_user {tg_user_id}")
        
        if expired_users:
            logger.info(f"Cleared {len(expired_users)} expired download search cache entries")
    
    def clear_user(self, tg_user_id: int) -> None:
        """
        清理特定用户的缓存
        
        Args:
            tg_user_id: Telegram用户ID
        """
        if tg_user_id in self._by_tg_user:
            del self._by_tg_user[tg_user_id]
            logger.debug(f"Cleared download search cache for tg_user {tg_user_id}")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        获取缓存统计信息
        
        Returns:
            包含缓存条目数等信息的字典
        """
        self.clear_expired()
        return {
            "total_cached_users": len(self._by_tg_user),
            "cached_candidates_total": sum(len(state.candidates) for state in self._by_tg_user.values())
        }


class ReadingListCache:
    """阅读列表缓存"""
    
    def __init__(self) -> None:
        self._by_tg_user: Dict[int, UserReadingListState] = {}
    
    def set_results(self, tg_user_id: int, user_id: int, items: List[ReadingOngoingItem], item_type: str) -> None:
        """
        缓存用户的阅读列表
        
        Args:
            tg_user_id: Telegram用户ID
            user_id: VabHub内部用户ID
            items: 阅读列表
            item_type: 类型 "mixed"/"ebook"/"audiobook"/"manga"
        """
        # 清理过期缓存
        self.clear_expired()
        
        # 创建新的阅读列表状态
        state = UserReadingListState(
            user_id=user_id,
            tg_user_id=tg_user_id,
            created_at=datetime.utcnow(),
            items=items,
            item_type=item_type
        )
        
        self._by_tg_user[tg_user_id] = state
        logger.debug(f"Cached reading list for tg_user {tg_user_id}, {len(items)} items, type: {item_type}")
    
    def get_results(self, tg_user_id: int) -> UserReadingListState | None:
        """
        获取用户的阅读列表缓存
        
        Args:
            tg_user_id: Telegram用户ID
            
        Returns:
            阅读列表状态，如果不存在或已过期则返回None
        """
        # 清理过期缓存
        self.clear_expired()
        
        state = self._by_tg_user.get(tg_user_id)
        if state:
            logger.debug(f"Retrieved reading list cache for tg_user {tg_user_id}, {len(state.items)} items")
        return state
    
    def get_item_by_index(self, tg_user_id: int, index: int) -> ReadingOngoingItem | None:
        """
        根据索引获取缓存中的阅读项
        
        Args:
            tg_user_id: Telegram用户ID
            index: 1-based索引
            
        Returns:
            阅读项，如果索引越界或缓存不存在则返回None
        """
        state = self.get_results(tg_user_id)
        if not state:
            return None
        
        # 转换为0-based索引
        if index < 1 or index > len(state.items):
            return None
        
        return state.items[index - 1]
    
    def clear_expired(self, ttl_seconds: int = 600) -> None:
        """
        清理过期的缓存条目
        
        Args:
            ttl_seconds: 缓存TTL，默认10分钟
        """
        if not self._by_tg_user:
            return
        
        current_time = datetime.utcnow()
        expired_users = []
        
        for tg_user_id, state in self._by_tg_user.items():
            if current_time - state.created_at > timedelta(seconds=ttl_seconds):
                expired_users.append(tg_user_id)
        
        for tg_user_id in expired_users:
            del self._by_tg_user[tg_user_id]
            logger.debug(f"Expired reading list cache for tg_user {tg_user_id}")
        
        if expired_users:
            logger.info(f"Cleared {len(expired_users)} expired reading list cache entries")
    
    def clear_user(self, tg_user_id: int) -> None:
        """
        清理特定用户的缓存
        
        Args:
            tg_user_id: Telegram用户ID
        """
        if tg_user_id in self._by_tg_user:
            del self._by_tg_user[tg_user_id]
            logger.debug(f"Cleared reading list cache for tg_user {tg_user_id}")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        获取缓存统计信息
        
        Returns:
            包含缓存条目数等信息的字典
        """
        self.clear_expired()
        return {
            "total_cached_users": len(self._by_tg_user),
            "cached_items_total": sum(len(state.items) for state in self._by_tg_user.values())
        }


class ReadingActivityCache:
    """阅读活动时间线缓存"""
    
    def __init__(self) -> None:
        self._by_tg_user: Dict[int, UserReadingActivityState] = {}
        self.ttl_seconds = 600  # 10分钟，与ReadingListCache保持一致
    
    def set_results(self, tg_user_id: int, user_id: int, items: List[ReadingActivityItem]) -> None:
        """
        缓存用户的最近活动结果
        
        Args:
            tg_user_id: Telegram用户ID
            user_id: VabHub内部用户ID
            items: 最近活动列表
        """
        state = UserReadingActivityState(
            user_id=user_id,
            tg_user_id=tg_user_id,
            created_at=datetime.utcnow(),
            items=items
        )
        self._by_tg_user[tg_user_id] = state
        logger.debug(f"Cached reading activity for user {user_id}, {len(items)} items")
    
    def get_results(self, tg_user_id: int) -> Optional[UserReadingActivityState]:
        """
        获取用户的缓存活动结果
        
        Args:
            tg_user_id: Telegram用户ID
            
        Returns:
            缓存的状态，如果不存在或已过期返回None
        """
        state = self._by_tg_user.get(tg_user_id)
        if state is None:
            return None
        
        if state.is_expired(self.ttl_seconds):
            # 清理过期缓存
            del self._by_tg_user[tg_user_id]
            return None
        
        return state
    
    def get_item(self, tg_user_id: int, index: int) -> Optional[ReadingActivityItem]:
        """
        根据索引获取某个活动项
        
        Args:
            tg_user_id: Telegram用户ID
            index: 索引（1-based）
            
        Returns:
            活动项，如果不存在返回None
        """
        state = self.get_results(tg_user_id)
        if state is None:
            return None
        
        # 转换为0-based索引
        zero_based_index = index - 1
        if 0 <= zero_based_index < len(state.items):
            return state.items[zero_based_index]
        
        return None
    
    def clear_user(self, tg_user_id: int) -> None:
        """
        清理特定用户的缓存
        
        Args:
            tg_user_id: Telegram用户ID
        """
        if tg_user_id in self._by_tg_user:
            del self._by_tg_user[tg_user_id]
            logger.debug(f"Cleared reading activity cache for tg_user {tg_user_id}")
    
    def clear_expired(self) -> None:
        """清理所有过期的缓存"""
        expired_keys = []
        for tg_user_id, state in self._by_tg_user.items():
            if state.is_expired(self.ttl_seconds):
                expired_keys.append(tg_user_id)
        
        for tg_user_id in expired_keys:
            del self._by_tg_user[tg_user_id]
        
        if expired_keys:
            logger.debug(f"Cleared {len(expired_keys)} expired reading activity caches")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        获取缓存统计信息
        
        Returns:
            包含缓存条目数等信息的字典
        """
        self.clear_expired()
        return {
            "total_cached_users": len(self._by_tg_user),
            "cached_items_total": sum(len(state.items) for state in self._by_tg_user.values())
        }


# 为UserReadingActivityState添加is_expired方法
def _user_reading_activity_state_is_expired(self, ttl_seconds: int) -> bool:
    """检查状态是否已过期"""
    return datetime.utcnow() - self.created_at > timedelta(seconds=ttl_seconds)


# 动态添加方法到dataclass
UserReadingActivityState.is_expired = _user_reading_activity_state_is_expired


# 创建全局缓存实例
reading_list_cache = ReadingListCache()
reading_activity_cache = ReadingActivityCache()
reading_shelf_cache = ReadingShelfCache()
