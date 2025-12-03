"""
TVDB V4 API官方客户端
适配VabHub，使用httpx异步请求
TVDB API客户端
"""
import json
import urllib.parse
from http import HTTPStatus
from typing import Optional, Dict, Any, List, Union
import httpx
from loguru import logger

from app.core.cache import get_cache
from app.core.config import settings


class Auth:
    """
    TVDB认证类
    """

    def __init__(self, url: str, apikey: str, pin: str = "", proxy: Optional[Dict[str, str]] = None, timeout: int = 15):
        """
        初始化TVDB认证
        
        Args:
            url: 登录URL
            apikey: API Key
            pin: PIN码（可选）
            proxy: 代理配置
            timeout: 超时时间
        """
        login_info = {"apikey": apikey}
        if pin:
            login_info["pin"] = pin

        login_info_bytes = json.dumps(login_info, indent=2)

        try:
            # 使用httpx同步请求（认证需要同步）
            # 将代理字典转换为字符串格式（如果提供了字典）
            proxy_str = None
            if proxy:
                # 如果proxy是字典，转换为字符串格式
                if isinstance(proxy, dict):
                    # 优先使用https代理，如果没有则使用http代理
                    proxy_str = proxy.get("https") or proxy.get("http")
                else:
                    proxy_str = proxy
            
            # 构建客户端参数
            # httpx.Client使用proxy参数（单数），不是proxies
            with httpx.Client(
                proxy=proxy_str,
                timeout=httpx.Timeout(timeout),
                follow_redirects=True
            ) as client:
                response = client.post(
                    url=url,
                    content=login_info_bytes,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    result = response.json()
                    self.token = result["data"]["token"]
                else:
                    try:
                        error_data = response.json()
                        error_msg = f"Code: {response.status_code}, {error_data.get('message', '未知错误')}"
                    except Exception as err:
                        error_msg = f"Code: {response.status_code}, 响应解析失败：{err}"
                    raise Exception(error_msg)
        except Exception as e:
            raise Exception(f"TVDB认证失败: {str(e)}")

    def get_token(self) -> str:
        """
        获取认证token
        
        Returns:
            认证token
        """
        return self.token


class Request:
    """
    请求处理类
    """

    def __init__(self, auth_token: str, proxy: Optional[Union[str, Dict[str, str]]] = None, timeout: int = 15):
        """
        初始化请求处理类
        
        Args:
            auth_token: 认证token
            proxy: 代理配置
            timeout: 超时时间
        """
        self.auth_token = auth_token
        self.links = None
        self.proxy = proxy
        self.timeout = timeout
        self.cache = get_cache()

    async def make_request(self, url: str, if_modified_since: Optional[bool] = None) -> Any:
        """
        向指定的 URL 发起请求并返回数据（异步）
        
        Args:
            url: 请求URL
            if_modified_since: If-Modified-Since头
            
        Returns:
            响应数据
        """
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        if if_modified_since:
            headers["If-Modified-Since"] = str(if_modified_since)

        try:
            # 使用httpx异步请求
            # 将代理字典转换为字符串格式（如果提供了字典）
            proxy_str = None
            if self.proxy:
                if isinstance(self.proxy, dict):
                    # 优先使用https代理，如果没有则使用http代理
                    proxy_str = self.proxy.get("https") or self.proxy.get("http")
                else:
                    proxy_str = self.proxy
            
            # 构建客户端参数
            # httpx.AsyncClient使用proxy参数（单数），不是proxies
            async with httpx.AsyncClient(
                proxy=proxy_str,
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True
            ) as client:
                response = await client.get(url=url, headers=headers)

                if response.status_code == HTTPStatus.NOT_MODIFIED:
                    return {
                        "code": HTTPStatus.NOT_MODIFIED.real,
                        "message": "Not-Modified",
                    }

                if response.status_code == 200:
                    result = response.json()
                    data = result.get("data", None)
                    if data is not None and result.get("status", "failure") != "failure":
                        self.links = result.get("links", None)
                        return data

                    msg = result.get("message", "未知错误")
                    raise ValueError(f"获取 {url} 失败\n  {str(msg)}")
                else:
                    # 处理其他HTTP错误状态码
                    try:
                        error_data = response.json()
                        msg = error_data.get("message", f"HTTP {response.status_code}")
                    except Exception as err:
                        msg = f"HTTP {response.status_code} {err}"
                    raise ValueError(f"获取 {url} 失败\n  {str(msg)}")

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"获取 {url} 失败\n  {str(e)}")


class Url:
    """
    URL构建类
    """

    def __init__(self):
        """初始化URL构建类"""
        self.base_url = "https://api4.thetvdb.com/v4/"

    def construct(self, url_sect: str, url_id: Optional[int] = None,
                  url_subsect: Optional[str] = None, url_lang: Optional[str] = None, **kwargs) -> str:
        """
        构建API URL
        
        Args:
            url_sect: URL部分
            url_id: URL ID（可选）
            url_subsect: URL子部分（可选）
            url_lang: 语言（可选）
            **kwargs: 其他查询参数
            
        Returns:
            完整的API URL
        """
        url = self.base_url + url_sect
        if url_id:
            url += "/" + str(url_id)
        if url_subsect:
            url += "/" + url_subsect
        if url_lang:
            url += "/" + url_lang
        if kwargs:
            params = {var: val for var, val in kwargs.items() if val is not None}
            if params:
                url += "?" + urllib.parse.urlencode(params)
        return url


class TVDB:
    """
    TVDB API主类
    """

    def __init__(self, apikey: str, pin: str = "", proxy: Optional[Union[str, Dict[str, str]]] = None, timeout: int = 15):
        """
        初始化TVDB API客户端
        
        Args:
            apikey: API Key
            pin: PIN码（可选）
            proxy: 代理配置
            timeout: 超时时间
        """
        self.url = Url()
        login_url = self.url.construct("login")
        self.auth = Auth(login_url, apikey, pin, proxy, timeout)
        auth_token = self.auth.get_token()
        self.request = Request(auth_token, proxy, timeout)

    def get_req_links(self) -> Optional[Dict]:
        """
        获取上一次请求返回的链接信息（例如分页链接）
        
        Returns:
            链接信息字典
        """
        return self.request.links

    async def get_series(self, id: int, meta: Optional[str] = None, if_modified_since: Optional[bool] = None) -> Dict:
        """
        返回单个剧集信息的字典
        
        Args:
            id: 剧集ID
            meta: 元数据
            if_modified_since: If-Modified-Since头
            
        Returns:
            剧集信息字典
        """
        url = self.url.construct("series", id, meta=meta)
        return await self.request.make_request(url, if_modified_since)

    async def get_series_extended(self, id: int, meta: Optional[str] = None, short: bool = False, 
                                  if_modified_since: Optional[bool] = None) -> Dict:
        """
        返回单个剧集的扩展信息字典
        
        Args:
            id: 剧集ID
            meta: 元数据
            short: 是否返回简短信息
            if_modified_since: If-Modified-Since头
            
        Returns:
            剧集扩展信息字典
        """
        url = self.url.construct("series", id, "extended", meta=meta, short=short)
        return await self.request.make_request(url, if_modified_since)

    async def search(self, query: str, **kwargs) -> List[Dict]:
        """
        根据查询字符串进行搜索，并返回结果列表
        
        Args:
            query: 搜索查询字符串
            **kwargs: 其他查询参数
            
        Returns:
            搜索结果列表
        """
        url = self.url.construct("search", query=query, **kwargs)
        result = await self.request.make_request(url)
        if isinstance(result, list):
            return result
        return []

