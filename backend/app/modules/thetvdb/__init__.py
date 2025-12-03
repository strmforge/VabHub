"""
TVDB模块
用于媒体识别，主要作为TMDB的备选数据源
TVDB API集成
"""
from threading import Lock
from typing import Optional, Tuple, Union, List
from loguru import logger

from app.core.config import settings
from app.modules.thetvdb.tvdb_v4_official import TVDB


class TheTvDbModule:
    """
    TVDB媒体信息匹配模块
    作为媒体识别的备选数据源，优先级较低
    """
    __timeout: int = 15
    tvdb: Optional[TVDB] = None
    __auth_lock = Lock()

    def __init__(self):
        """初始化TVDB模块"""
        pass

    def _initialize_tvdb_session(self, is_retry: bool = False) -> None:
        """
        创建或刷新 TVDB 登录会话
        
        Args:
            is_retry: 是否是由于token失效后的重试登录
        """
        action = "刷新" if is_retry else "创建"
        logger.info(f"开始{action}TVDB登录会话...")
        try:
            if not settings.TVDB_V4_API_KEY:
                raise ConnectionError("TVDB API Key 未配置，无法初始化会话。")
            
            # 获取代理配置（直接使用字符串格式，与httpx兼容）
            proxy_config = None
            if settings.PROXY_HOST:
                # httpx可以直接使用字符串格式的代理
                proxy_config = settings.PROXY_HOST
            
            self.tvdb = TVDB(
                apikey=settings.TVDB_V4_API_KEY,
                pin=settings.TVDB_V4_API_PIN,
                proxy=proxy_config,
                timeout=self.__timeout
            )
            
            if self.tvdb:
                logger.info(f"TVDB登录会话{action}成功。")
            else:
                raise ValueError(f"TVDB登录会话{action}后实例仍为None。")
        except Exception as e:
            self.tvdb = None
            raise ConnectionError(f"TVDB登录会话{action}失败: {str(e)}") from e

    def _ensure_tvdb_session(self, is_retry: bool = False) -> None:
        """
        确保TVDB会话存在。如果不存在或需要强制重新初始化，则进行初始化
        
        Args:
            is_retry: 是否重新初始化（例如token失效时）
        """
        # 第一次检查 (无锁)，提高性能，避免不必要锁竞争
        if not self.tvdb or is_retry:
            with self.__auth_lock:
                # 第二次检查 (有锁)，防止多个线程都通过第一次检查后重复初始化
                if not self.tvdb or is_retry:
                    self._initialize_tvdb_session(is_retry=is_retry)

    async def _handle_tvdb_call(self, method_name: str, *args, **kwargs):
        """
        包裹 TVDB 调用，处理 token 失效情况并尝试重新初始化（异步）
        
        Args:
            method_name: 要在 self.tvdb 实例上调用的方法的名称 (字符串)
        """
        try:
            self._ensure_tvdb_session()
            actual_method = getattr(self.tvdb, method_name)
            # TVDB API客户端方法是异步的
            if hasattr(actual_method, '__call__'):
                result = await actual_method(*args, **kwargs)
                return result
            return actual_method(*args, **kwargs)
        except ValueError as e:
            if "Unauthorized" in str(e):
                logger.warning("TVDB Token 可能已失效，正在尝试重新登录...")
                try:
                    self._ensure_tvdb_session(is_retry=True)
                    actual_method = getattr(self.tvdb, method_name)
                    # TVDB API客户端方法是异步的
                    if hasattr(actual_method, '__call__'):
                        result = await actual_method(*args, **kwargs)
                        return result
                    return actual_method(*args, **kwargs)
                except ConnectionError as conn_err:
                    logger.error(f"TVDB Token失效后重新登录失败: {conn_err}")
                    raise
            elif "NotFoundException" in str(e) or "ID not found" in str(e):
                logger.warning(f"TVDB 资源未找到 (调用 {method_name}): {e}")
                return None
            else:
                logger.error(f"TVDB 调用 ({method_name}) 时发生未处理的 ValueError: {str(e)}")
                raise
        except ConnectionError as e:
            logger.error(f"TVDB 连接会话错误: {str(e)}")
            raise
        except AttributeError as e:
            logger.error(f"TVDB 实例上没有方法 '{method_name}': {e}")
            raise
        except Exception as e:
            logger.error(f"TVDB 调用时发生未知错误: {str(e)}", exc_info=True)
            raise

    async def test(self) -> Tuple[bool, str]:
        """
        测试模块连接性（异步）
        
        Returns:
            (是否成功, 错误信息)
        """
        try:
            await self._handle_tvdb_call("get_series", 81189)
            return True, ""
        except Exception as e:
            return False, str(e)

    async def tvdb_info(self, tvdbid: int) -> Optional[dict]:
        """
        获取TVDB信息（异步）
        
        Args:
            tvdbid: TVDB ID
            
        Returns:
            TVDB信息字典，失败返回None
        """
        try:
            logger.info(f"开始获取TVDB信息: {tvdbid} ...")
            return await self._handle_tvdb_call("get_series_extended", tvdbid)
        except Exception as err:
            logger.error(f"获取TVDB信息失败: {str(err)}")
            return None

    async def search_tvdb(self, title: str) -> List[dict]:
        """
        用标题搜索TVDB剧集（异步）
        
        Args:
            title: 标题
            
        Returns:
            TVDB信息列表，失败返回空列表
        """
        try:
            logger.info(f"开始用标题搜索TVDB剧集: {title} ...")
            res = await self._handle_tvdb_call("search", title)
            if res is None:
                return []
            if not isinstance(res, list):
                logger.warning(f"TVDB 搜索 '{title}' 未返回列表：{type(res)}")
                return []
            # 只返回类型为"series"的结果
            return [item for item in res if isinstance(item, dict) and item.get("type") == "series"]
        except Exception as err:
            logger.error(f"用标题搜索TVDB剧集失败 ({title}): {str(err)}")
            return []

    def stop(self):
        """停止模块，清除TVDB会话"""
        logger.info("TheTvDbModule 停止。正在清除 TVDB 会话。")
        with self.__auth_lock:
            self.tvdb = None

