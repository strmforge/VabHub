"""
115网盘API客户端
基于115网盘开放平台API实现文件操作和实时对比
"""

import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger


class Cloud115Client:
    """115网盘API客户端"""
    
    def __init__(self, access_token: str, base_url: str = "https://api.115.com"):
        """
        初始化115网盘客户端
        
        Args:
            access_token: 访问令牌
            base_url: API基础URL
        """
        self.access_token = access_token
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
    
    async def get_file_info(
        self,
        file_id: Optional[str] = None,
        path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取文件(夹)详情
        
        API文档：GET/POST 域名+/open/folder/get_info
        
        Args:
            file_id: 文件(夹)ID
            path: 文件路径（支持/和>分隔符）
        
        Returns:
            文件详情
        """
        try:
            if file_id:
                # 使用file_id查询
                response = await self.client.get(
                    "/open/folder/get_info",
                    params={"file_id": file_id}
                )
            elif path:
                # 使用path查询（2025年6月6日新增功能）
                response = await self.client.post(
                    "/open/folder/get_info",
                    data={"path": path}
                )
            else:
                raise ValueError("file_id和path必须提供一个")
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("state"):
                return result.get("data", {})
            else:
                logger.error(f"获取文件详情失败: {result.get('message')}")
                return {}
                
        except Exception as e:
            logger.error(f"获取文件详情异常: {e}")
            return {}
    
    async def search_files(
        self,
        search_value: str,
        limit: int = 20,
        offset: int = 0,
        file_label: Optional[str] = None,
        cid: Optional[int] = None,
        gte_day: Optional[str] = None,
        lte_day: Optional[str] = None,
        fc: Optional[int] = None,
        type: Optional[int] = None,
        suffix: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        根据文件名搜索文件(夹)
        
        API文档：GET 域名+/open/ufile/search
        
        Args:
            search_value: 查找关键字
            limit: 单页记录数，默认20，offset+limit最大不超过10000
            offset: 数据显示偏移量
            file_label: 文件标签搜索
            cid: 目标目录cid=-1时，表示不返回列表任何内容
            gte_day: 搜索结果匹配的开始时间，格式:2020-11-19
            lte_day: 搜索结果匹配的结束时间，格式:2020-11-20
            fc: 只显示文件或文件夹。1只显示文件夹，2只显示文件
            type: 一级筛选大分类，1:文档，2:图片，3:音乐，4:视频，5:压缩包，6:应用
            suffix: 一级筛选选其他时填写的后缀名
        
        Returns:
            搜索结果
        """
        try:
            params = {
                "search_value": search_value,
                "limit": limit,
                "offset": offset
            }
            
            if file_label:
                params["file_label"] = file_label
            if cid is not None:
                params["cid"] = cid
            if gte_day:
                params["gte_day"] = gte_day
            if lte_day:
                params["lte_day"] = lte_day
            if fc is not None:
                params["fc"] = fc
            if type is not None:
                params["type"] = type
            if suffix:
                params["suffix"] = suffix
            
            response = await self.client.get(
                "/open/ufile/search",
                params=params
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("state"):
                return result.get("data", {})
            else:
                logger.error(f"搜索文件失败: {result.get('message')}")
                return {}
                
        except Exception as e:
            logger.error(f"搜索文件异常: {e}")
            return {}
    
    async def search_recent_files(
        self,
        days: int = 1,
        file_type: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        搜索最近修改的文件
        
        Args:
            days: 最近N天
            file_type: 文件类型，4:视频
            limit: 返回数量
        
        Returns:
            文件列表
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        gte_day = start_date.strftime("%Y-%m-%d")
        lte_day = end_date.strftime("%Y-%m-%d")
        
        result = await self.search_files(
            search_value="",  # 空搜索值，通过时间范围筛选
            gte_day=gte_day,
            lte_day=lte_day,
            fc=2,  # 只显示文件
            type=file_type,  # 4:视频
            limit=limit,
            offset=0
        )
        
        return result.get("data", [])
    
    async def get_file_changes(
        self,
        last_sync_time: datetime,
        file_type: Optional[int] = 4  # 4:视频
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取文件变更（新增、更新、删除）
        
        Args:
            last_sync_time: 上次同步时间
            file_type: 文件类型，4:视频
        
        Returns:
            文件变更：added, updated, deleted
        """
        changes = {
            "added": [],
            "updated": [],
            "deleted": []
        }
        
        try:
            # 计算时间范围
            days_since_sync = (datetime.now() - last_sync_time).days
            if days_since_sync < 1:
                days_since_sync = 1
            elif days_since_sync > 30:
                days_since_sync = 30  # 最多查询30天
            
            # 搜索最近修改的文件
            recent_files = await self.search_recent_files(
                days=days_since_sync,
                file_type=file_type,
                limit=1000
            )
            
            # 过滤出新增和更新的文件
            last_sync_timestamp = last_sync_time.timestamp()
            
            for file_info in recent_files:
                user_utime = file_info.get("user_utime")
                if user_utime:
                    # 解析更新时间
                    try:
                        # user_utime格式可能是时间戳或日期字符串
                        if isinstance(user_utime, (int, float)):
                            file_time = user_utime
                        else:
                            file_time = datetime.fromisoformat(user_utime.replace("Z", "+00:00")).timestamp()
                        
                        # 判断是新增还是更新
                        if file_time > last_sync_timestamp:
                            # 检查area_id判断文件状态
                            area_id = file_info.get("area_id", "1")
                            if area_id == "1":  # 正常
                                # 需要进一步判断是新增还是更新
                                # 这里简化处理，都作为更新
                                changes["updated"].append(file_info)
                            elif area_id == "7":  # 删除(回收站)
                                changes["deleted"].append(file_info)
                            elif area_id == "120":  # 彻底删除
                                changes["deleted"].append(file_info)
                    except Exception as e:
                        logger.warning(f"解析文件时间失败: {file_info.get('file_name')} - {e}")
            
            logger.info(f"检测到文件变更: 新增{len(changes['added'])}, 更新{len(changes['updated'])}, 删除{len(changes['deleted'])}")
            
        except Exception as e:
            logger.error(f"获取文件变更失败: {e}")
        
        return changes
    
    async def get_file_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """
        根据路径获取文件详情
        
        Args:
            path: 文件路径
        
        Returns:
            文件详情
        """
        file_info = await self.get_file_info(path=path)
        return file_info if file_info else None
    
    async def list_folder(
        self,
        folder_id: Optional[str] = None,
        path: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        列出文件夹内容
        
        Args:
            folder_id: 文件夹ID
            path: 文件夹路径
            limit: 每页数量
            offset: 偏移量
        
        Returns:
            文件列表
        """
        # 首先获取文件夹信息
        folder_info = await self.get_file_info(file_id=folder_id, path=path)
        
        if not folder_info:
            return []
        
        # 这里需要调用列表API，但文档中没有提供
        # 暂时使用搜索API模拟
        # 实际应该调用 /open/folder/list 类似的API
        return []
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

