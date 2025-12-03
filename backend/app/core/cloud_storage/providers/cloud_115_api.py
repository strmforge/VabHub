"""
115网盘API客户端
基于115网盘开发者API实现文件操作和查询
参考：115网盘开放平台官方文档
基础域名: https://proapi.115.com/
OAuth2认证: 使用Cloud115OAuth类
"""

import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger

# 导入OAuth2认证客户端
try:
    from .cloud_115_oauth import Cloud115OAuth
except ImportError:
    Cloud115OAuth = None
    logger.warning("Cloud115OAuth未导入，OAuth2认证功能不可用")


class Cloud115API:
    """115网盘API客户端"""
    
    def __init__(self, access_token: str, base_url: str = "https://proapi.115.com"):
        """
        初始化115网盘API客户端
        
        Args:
            access_token: 访问令牌
            base_url: API基础URL（官方文档推荐: https://proapi.115.com）
        """
        self.access_token = access_token
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {access_token}"
        }
    
    async def get_file_info(
        self,
        file_id: Optional[str] = None,
        path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取文件(夹)详情
        参考：115网盘开放API文档 - 获取文件(夹)详情
        使用proapi.115.com的API端点: /open/folder/get_info
        
        API说明：
        - 请求头: Authorization: Bearer access_token
        - 请求方法: GET/POST
        - 查询参数: file_id（GET方法）
        - 请求体: path（POST方法，form-data格式）
        - file_id和path需必传一个
        
        Args:
            file_id: 文件(夹)ID
            path: 文件路径（支持/和>分隔符，如: /a/b/c.png 或 >a>b>c）
        
        Returns:
            文件详情，包含：
            - count: 包含文件总数量
            - size: 文件(夹)总大小（格式化字符串）
            - size_byte: 文件(夹)总大小（字节单位）
            - folder_count: 包含文件夹总数量
            - play_long: 视频时长（-1:正在统计,其他数值为视频时长的数值(单位秒)）
            - show_play_long: 是否开启展示视频时长
            - ptime: 上传时间
            - utime: 修改时间
            - file_name: 文件名
            - pick_code: 文件提取码
            - sha1: sha1值
            - file_id: 文件(夹)ID
            - is_mark: 是否星标
            - open_time: 文件(夹)最近打开时间
            - file_category: 文件属性（1:文件; 0:文件夹）
            - paths: 文件(夹)所在的路径（对象数组）
        """
        url = f"{self.base_url}/open/folder/get_info"
        
        async with httpx.AsyncClient() as client:
            try:
                if file_id:
                    # 使用GET方法，通过query参数传递file_id
                    params = {"file_id": file_id}
                    response = await client.get(url, params=params, headers=self.headers)
                elif path:
                    # 使用POST方法，通过form-data传递path
                    # 注意：115网盘API使用form-data格式，不是JSON
                    # 路径支持/和>两种分隔符，最前面需分隔符开头，以分隔符分隔目录层级
                    normalized_path = self.parse_file_path(path)
                    data = {"path": normalized_path}
                    # 移除Content-Type头部，让httpx自动设置form-data
                    headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
                    response = await client.post(url, data=data, headers=headers)
                else:
                    logger.error("file_id和path必须提供其中一个")
                    return {}
                
                response.raise_for_status()
                result = response.json()
                
                # 115 API成功返回state=true或code=0
                if result.get("state") is True or result.get("code") == 0:
                    data = result.get("data", {})
                    
                    # 返回完整的文件详情（根据官方文档的返回数据结构）
                    file_info = {
                        "count": data.get("count", "0"),  # 包含文件总数量
                        "size": data.get("size", "0"),  # 文件(夹)总大小（格式化字符串）
                        "size_byte": data.get("size_byte", 0),  # 文件(夹)总大小（字节单位）
                        "folder_count": data.get("folder_count", "0"),  # 包含文件夹总数量
                        "play_long": data.get("play_long", 0),  # 视频时长（-1:正在统计）
                        "show_play_long": data.get("show_play_long", 0),  # 是否开启展示视频时长
                        "ptime": data.get("ptime", ""),  # 上传时间
                        "utime": data.get("utime", ""),  # 修改时间
                        "file_name": data.get("file_name", ""),  # 文件名
                        "pick_code": data.get("pick_code", ""),  # 文件提取码
                        "sha1": data.get("sha1", ""),  # sha1值
                        "file_id": data.get("file_id", ""),  # 文件(夹)ID
                        "is_mark": data.get("is_mark", "0"),  # 是否星标
                        "open_time": data.get("open_time", 0),  # 文件(夹)最近打开时间
                        "file_category": data.get("file_category", "1"),  # 文件属性（1:文件; 0:文件夹）
                        "paths": data.get("paths", [])  # 文件(夹)所在的路径（对象数组）
                    }
                    
                    logger.debug(f"获取文件详情成功: file_id={file_info.get('file_id')}, file_name={file_info.get('file_name')}")
                    return file_info
                else:
                    error_msg = result.get("message", "未知错误")
                    error_code = result.get("code")
                    logger.error(f"获取文件详情失败: {error_msg} (code: {error_code})")
                    return {}
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"获取文件详情HTTP错误: {e.response.status_code}")
                if e.response.status_code == 401:
                    logger.error("访问令牌无效或已过期，请刷新令牌")
                return {}
            except Exception as e:
                logger.error(f"获取文件详情异常: {e}")
                return {}
    
    async def list_files(
        self,
        file_id: Optional[str] = None,
        path: Optional[str] = None,
        file_type: Optional[int] = None,  # 1.文档;2.图片;3.音乐;4.视频;5.压缩;6.应用;7.书籍
        limit: int = 20,  # 默认20，最大1150
        offset: int = 0,
        suffix: Optional[str] = None,  # 文件后缀名
        asc: int = 1,  # 排序，1:升序 0:降序
        order_by: Optional[str] = None,  # 排序字段: file_name, file_size, user_utime, file_type
        custom_order: Optional[int] = None,  # 是否使用记忆排序
        stdir: Optional[int] = None,  # 筛选文件时，是否显示文件夹;1:要展示文件夹 0不展示
        star: Optional[int] = None,  # 筛选星标文件，1:是 0全部
        cur: Optional[int] = None,  # 是否只显示当前文件夹内文件
        show_dir: int = 0  # 是否显示目录;0或1，默认为0
    ) -> Dict[str, Any]:
        """
        获取文件列表
        参考：115网盘开放API文档 - 获取文件列表
        使用proapi.115.com的API端点: /open/ufile/files
        
        API说明：
        - 请求头: Authorization: Bearer access_token
        - 请求方法: GET
        - 查询参数: cid, type, limit, offset, suffix, asc, o, custom_order, stdir, star, cur, show_dir
        
        Args:
            file_id: 目录ID（cid），对应parent id
            path: 目录路径
            file_type: 文件类型（1.文档;2.图片;3.音乐;4.视频;5.压缩;6.应用;7.书籍）
            limit: 查询数量（默认20，最大1150）
            offset: 查询起始位（默认0）
            suffix: 文件后缀名
            asc: 排序（1:升序 0:降序）
            order_by: 排序字段（file_name:文件名, file_size:文件大小, user_utime:更新时间, file_type:文件类型）
            custom_order: 是否使用记忆排序（1:使用自定义排序, 0:使用记忆排序, 2:自定义排序非文件夹置顶）
            stdir: 筛选文件时，是否显示文件夹（1:要展示文件夹 0不展示）
            star: 筛选星标文件（1:是 0全部）
            cur: 是否只显示当前文件夹内文件
            show_dir: 是否显示目录（0或1，默认为0）
        
        Returns:
            文件列表，包含完整的文件信息
        """
        # 如果提供了path，先获取file_id
        if path and not file_id:
            file_info = await self.get_file_info(path=path)
            if file_info:
                file_id = file_info.get("file_id")
            else:
                logger.error(f"无法获取路径对应的文件ID: {path}")
                return {"count": 0, "data": [], "limit": limit, "offset": offset}
        
        url = f"{self.base_url}/open/ufile/files"
        
        async with httpx.AsyncClient() as client:
            try:
                # 构建查询参数
                params = {}
                
                if file_id:
                    # cid可以是number或string
                    try:
                        params["cid"] = int(file_id)
                    except (ValueError, TypeError):
                        params["cid"] = file_id
                
                if file_type is not None:
                    params["type"] = file_type
                
                if limit is not None:
                    # 限制最大值为1150
                    params["limit"] = min(limit, 1150)
                else:
                    params["limit"] = 20
                
                if offset is not None:
                    params["offset"] = offset
                
                if suffix:
                    params["suffix"] = suffix
                
                if asc is not None:
                    params["asc"] = asc
                
                if order_by:
                    params["o"] = order_by
                
                if custom_order is not None:
                    params["custom_order"] = custom_order
                
                if stdir is not None:
                    params["stdir"] = stdir
                
                if star is not None:
                    params["star"] = star
                
                if cur is not None:
                    params["cur"] = cur
                
                if show_dir is not None:
                    params["show_dir"] = show_dir
                
                response = await client.get(url, params=params, headers=self.headers)
                
                response.raise_for_status()
                result = response.json()
                
                # 115 API成功返回state=true或code=0
                if result.get("state") is True or result.get("code") == 0:
                    data = result.get("data", [])
                    
                    # 返回完整的文件信息（根据官方文档的返回数据结构）
                    files = []
                    for item in data:
                        file_info = {
                            "file_id": str(item.get("fid", "")),
                            "aid": str(item.get("aid", "")),  # 文件状态，1正常, 7删除(回收站), 120彻底删除
                            "parent_id": str(item.get("pid", "")),
                            "file_category": str(item.get("fc", "1")),  # 0文件夹, 1文件
                            "file_name": item.get("fn", ""),
                            "folder_cover": item.get("fco", ""),  # 文件夹封面
                            "is_starred": str(item.get("ism", "0")),  # 是否星标，1:星标
                            "is_encrypted": item.get("isp", 0),  # 是否加密，1:加密
                            "pick_code": item.get("pc", ""),  # 文件提取码
                            "update_time": item.get("upt", 0),  # 修改时间
                            "edit_time": item.get("uet", 0),  # 修改时间
                            "upload_time": item.get("uppt", 0),  # 上传时间
                            "cm": item.get("cm", 0),
                            "file_desc": item.get("fdesc", ""),  # 文件备注
                            "is_play_long": item.get("ispl", 0),  # 是否统计文件夹下视频时长开关
                            "file_tags": item.get("fl", []),  # 文件标签
                            "sha1": item.get("sha1", ""),
                            "file_size": item.get("fs", 0),  # 文件大小
                            "file_status": item.get("fta", ""),  # 文件状态，0/2未上传完成, 1已上传完成
                            "file_ext": item.get("ico", ""),  # 文件后缀名
                            "audio_length": item.get("fatr", ""),  # 音频长度
                            "is_video": item.get("isv", 0),  # 是否为视频
                            "video_quality": item.get("def", 0),  # 视频清晰度
                            "video_quality2": item.get("def2", 0),  # 视频清晰度
                            "play_duration": item.get("play_long", 0),  # 音视频时长
                            "video_image": item.get("v_img", ""),
                            "thumbnail": item.get("thumb", ""),  # 图片缩略图
                            "original_image": item.get("uo", "")  # 原图地址
                        }
                        files.append(file_info)
                    
                    # 获取分页信息
                    count = result.get("count", len(files))
                    sys_count = result.get("sys_count", 0)
                    return_limit = result.get("limit", limit)
                    return_offset = result.get("offset", offset)
                    
                    return {
                        "count": count,
                        "sys_count": sys_count,
                        "data": files,
                        "limit": return_limit,
                        "offset": return_offset
                    }
                else:
                    error_msg = result.get("message", "未知错误")
                    error_code = result.get("code")
                    logger.error(f"获取文件列表失败: {error_msg} (code: {error_code})")
                    return {"count": 0, "data": [], "limit": limit, "offset": offset}
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"获取文件列表HTTP错误: {e.response.status_code}")
                if e.response.status_code == 401:
                    logger.error("访问令牌无效或已过期，请刷新令牌")
                return {"count": 0, "data": [], "limit": limit, "offset": offset}
            except Exception as e:
                logger.error(f"获取文件列表异常: {e}")
                return {"count": 0, "data": [], "limit": limit, "offset": offset}
    
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
        file_type: Optional[int] = None,
        suffix: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        搜索文件(夹)
        
        Args:
            search_value: 查找关键字
            limit: 单页记录数，默认20，offset+limit最大不超过10000
            offset: 数据显示偏移量
            file_label: 文件标签
            cid: 目标目录ID（-1表示不返回列表任何内容）
            gte_day: 搜索结果匹配的开始时间（格式:2020-11-19）
            lte_day: 搜索结果匹配的结束时间（格式:2020-11-20）
            fc: 只显示文件或文件夹（1只显示文件夹，2只显示文件）
            file_type: 一级筛选大分类（1:文档,2:图片,3:音乐,4:视频,5:压缩包,6:应用）
            suffix: 一级筛选选其他时填写的后缀名
        
        Returns:
            搜索结果
        """
        url = f"{self.base_url}/open/ufile/search"
        
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
        if file_type is not None:
            params["type"] = file_type
        if suffix:
            params["suffix"] = suffix
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, headers=self.headers)
                response.raise_for_status()
                result = response.json()
                
                if result.get("state"):
                    return {
                        "count": result.get("count", 0),
                        "data": result.get("data", []),
                        "limit": result.get("limit", limit),
                        "offset": result.get("offset", offset)
                    }
                else:
                    logger.error(f"搜索文件失败: {result.get('message')}")
                    return {"count": 0, "data": [], "limit": limit, "offset": offset}
                    
            except Exception as e:
                logger.error(f"搜索文件异常: {e}")
                return {"count": 0, "data": [], "limit": limit, "offset": offset}
    
    async def delete_file(
        self,
        file_id: Optional[str] = None,
        file_ids: Optional[List[str]] = None,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        批量删除文件(夹)
        参考：115网盘开放API文档 - 删除文件
        使用proapi.115.com的API端点: /open/ufile/delete
        
        API说明：
        - 请求头: Authorization: Bearer access_token
        - 请求方法: POST
        - 请求体: form-data格式
        - 批量删除文件
        
        Args:
            file_id: 文件(夹)ID（单个删除，与file_ids二选一）
            file_ids: 文件(夹)ID列表（批量删除，多个文件以逗号隔开）
            parent_id: 删除的文件(夹)ID所在的父目录ID（可选）
        
        Returns:
            删除结果，包含data数组（string[]类型）
        """
        url = f"{self.base_url}/open/ufile/delete"
        
        async with httpx.AsyncClient() as client:
            try:
                # 构建请求数据
                data = {}
                
                # 处理文件ID（支持单个和批量）
                if file_ids:
                    # 批量删除：多个文件以逗号隔开
                    data["file_ids"] = ",".join(file_ids)
                elif file_id:
                    # 单个删除
                    data["file_ids"] = str(file_id)
                else:
                    logger.error("file_id或file_ids必须提供其中一个")
                    return {"success": False, "message": "file_id或file_ids必须提供其中一个"}
                
                # 添加父目录ID（可选）
                if parent_id:
                    data["parent_id"] = str(parent_id)
                
                # 使用form-data格式
                headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
                response = await client.post(url, data=data, headers=headers)
                
                response.raise_for_status()
                result = response.json()
                
                # 115 API成功返回state=true或code=0
                # 注意：code可能是string类型
                if result.get("state") is True or result.get("code") == 0 or result.get("code") == "0":
                    logger.info(f"删除文件成功: file_id={file_id or file_ids}")
                    return {
                        "success": True,
                        "data": result.get("data", [])  # data是string[]类型
                    }
                else:
                    error_msg = result.get("message", "未知错误")
                    error_code = result.get("code")
                    logger.error(f"删除文件失败: {error_msg} (code: {error_code})")
                    return {
                        "success": False,
                        "message": error_msg,
                        "code": error_code
                    }
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"删除文件HTTP错误: {e.response.status_code}")
                if e.response.status_code == 401:
                    logger.error("访问令牌无效或已过期，请刷新令牌")
                return {"success": False, "message": f"HTTP错误: {e.response.status_code}"}
            except Exception as e:
                logger.error(f"删除文件异常: {e}")
                return {"success": False, "message": str(e)}
    
    async def update_file(
        self,
        file_id: str,
        file_name: Optional[str] = None,
        star: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        更新文件(夹)名称或星标
        参考：115网盘开放API文档 - 文件(夹)更新
        使用proapi.115.com的API端点: /open/ufile/update
        
        API说明：
        - 请求头: Authorization: Bearer access_token
        - 请求方法: POST
        - 请求体: form-data格式
        - 更新文件名或星标文件
        
        Args:
            file_id: 需要更改名字的文件(夹)ID（必填）
            file_name: 新的文件(夹)名字（可选，文件夹名称限制255字节）
            star: 是否星标（可选，1:星标, 0:取消星标）
        
        Returns:
            更新结果，包含file_name和star
        """
        url = f"{self.base_url}/open/ufile/update"
        
        async with httpx.AsyncClient() as client:
            try:
                # 构建请求数据
                data = {
                    "file_id": str(file_id)  # 文件(夹)ID（text类型）
                }
                
                # 更新文件名（如果提供）
                if file_name:
                    # 验证文件夹名称长度（限制255字节）
                    if len(file_name.encode('utf-8')) > 255:
                        logger.error(f"文件名称过长: {len(file_name.encode('utf-8'))}字节，限制255字节")
                        return {"success": False, "message": "文件名称过长，限制255字节"}
                    data["file_name"] = file_name
                
                # 更新星标状态（如果提供）
                if star is not None:
                    data["star"] = str(star)  # 1:星标, 0:取消星标
                
                # 如果没有提供任何更新字段
                if not file_name and star is None:
                    logger.error("file_name和star至少需要提供其中一个")
                    return {"success": False, "message": "file_name和star至少需要提供其中一个"}
                
                # 使用form-data格式
                headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
                response = await client.post(url, data=data, headers=headers)
                
                response.raise_for_status()
                result = response.json()
                
                # 115 API成功返回state=true或code=0
                if result.get("state") is True or result.get("code") == 0:
                    data_result = result.get("data", {})
                    logger.info(f"更新文件成功: file_id={file_id}, file_name={file_name}, star={star}")
                    return {
                        "success": True,
                        "file_name": data_result.get("file_name", file_name),
                        "star": data_result.get("star", str(star) if star is not None else None)
                    }
                else:
                    error_msg = result.get("message", "未知错误")
                    error_code = result.get("code")
                    logger.error(f"更新文件失败: {error_msg} (code: {error_code})")
                    return {
                        "success": False,
                        "message": error_msg,
                        "code": error_code
                    }
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"更新文件HTTP错误: {e.response.status_code}")
                if e.response.status_code == 401:
                    logger.error("访问令牌无效或已过期，请刷新令牌")
                return {"success": False, "message": f"HTTP错误: {e.response.status_code}"}
            except Exception as e:
                logger.error(f"更新文件异常: {e}")
                return {"success": False, "message": str(e)}
    
    async def rename_file(
        self,
        file_id: str,
        new_name: str
    ) -> bool:
        """
        重命名文件(夹)（便捷方法）
        
        Args:
            file_id: 文件(夹)ID
            new_name: 新名称
        
        Returns:
            是否重命名成功
        """
        result = await self.update_file(file_id=file_id, file_name=new_name)
        return result.get("success", False)
    
    async def star_file(
        self,
        file_id: str,
        star: bool = True
    ) -> bool:
        """
        设置文件星标（便捷方法）
        
        Args:
            file_id: 文件(夹)ID
            star: 是否星标（True:星标, False:取消星标）
        
        Returns:
            是否设置成功
        """
        result = await self.update_file(file_id=file_id, star=1 if star else 0)
        return result.get("success", False)
    
    async def move_file(
        self,
        file_id: str,
        target_parent_id: str,
        file_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        批量移动文件(夹)
        参考：115网盘开放API文档 - 文件移动
        使用proapi.115.com的API端点: /open/ufile/move
        
        API说明：
        - 请求头: Authorization: Bearer access_token
        - 请求方法: POST
        - 请求体: form-data格式
        - 批量移动文件
        
        Args:
            file_id: 文件(夹)ID（单个移动，与file_ids二选一）
            file_ids: 文件(夹)ID列表（批量移动，多个文件以逗号隔开）
            target_parent_id: 要移动所在的目录ID（to_cid），根目录为0
        
        Returns:
            移动结果，包含data数组
        """
        url = f"{self.base_url}/open/ufile/move"
        
        async with httpx.AsyncClient() as client:
            try:
                # 构建请求数据
                data = {
                    "to_cid": str(target_parent_id)  # 目标目录ID（string类型），根目录为0
                }
                
                # 处理文件ID（支持单个和批量）
                if file_ids:
                    # 批量移动：多个文件以逗号隔开
                    data["file_ids"] = ",".join(file_ids)
                elif file_id:
                    # 单个移动
                    data["file_ids"] = str(file_id)
                else:
                    logger.error("file_id或file_ids必须提供其中一个")
                    return {}
                
                # 使用form-data格式
                headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
                response = await client.post(url, data=data, headers=headers)
                
                response.raise_for_status()
                result = response.json()
                
                # 115 API成功返回state=true或code=0
                if result.get("state") is True or result.get("code") == 0:
                    logger.info(f"移动文件成功: file_id={file_id or file_ids}, target_parent_id={target_parent_id}")
                    return {
                        "success": True,
                        "data": result.get("data", [])
                    }
                else:
                    error_msg = result.get("message", "未知错误")
                    error_code = result.get("code")
                    logger.error(f"移动文件失败: {error_msg} (code: {error_code})")
                    return {
                        "success": False,
                        "message": error_msg,
                        "code": error_code
                    }
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"移动文件HTTP错误: {e.response.status_code}")
                if e.response.status_code == 401:
                    logger.error("访问令牌无效或已过期，请刷新令牌")
                return {"success": False, "message": f"HTTP错误: {e.response.status_code}"}
            except Exception as e:
                logger.error(f"移动文件异常: {e}")
                return {"success": False, "message": str(e)}
    
    async def copy_file(
        self,
        file_id: str,
        target_parent_id: str,
        file_ids: Optional[List[str]] = None,
        allow_duplicate: bool = True
    ) -> Dict[str, Any]:
        """
        批量复制文件(夹)
        参考：115网盘开放API文档 - 文件复制
        使用proapi.115.com的API端点: /open/ufile/copy
        
        API说明：
        - 请求头: Authorization: Bearer access_token
        - 请求方法: POST
        - 请求体: form-data格式
        - 批量复制文件
        
        Args:
            file_id: 文件(夹)ID（单个复制，与file_ids二选一）
            file_ids: 文件(夹)ID列表（批量复制，多个文件以逗号隔开）
            target_parent_id: 目标目录ID（pid），即所需移动到的目录
            allow_duplicate: 复制的文件在目标目录是否允许重复（默认True：可以，False：不可以）
        
        Returns:
            复制结果，包含data数组
        """
        url = f"{self.base_url}/open/ufile/copy"
        
        async with httpx.AsyncClient() as client:
            try:
                # 构建请求数据
                data = {
                    "pid": str(target_parent_id)  # 目标目录ID（text类型）
                }
                
                # 处理文件ID（支持单个和批量）
                if file_ids:
                    # 批量复制：多个文件以逗号隔开
                    data["file_id"] = ",".join(file_ids)
                elif file_id:
                    # 单个复制
                    data["file_id"] = str(file_id)
                else:
                    logger.error("file_id或file_ids必须提供其中一个")
                    return {}
                
                # 是否允许重复（nodupli参数：0:可以, 1:不可以）
                data["nodupli"] = "0" if allow_duplicate else "1"
                
                # 使用form-data格式
                headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
                response = await client.post(url, data=data, headers=headers)
                
                response.raise_for_status()
                result = response.json()
                
                # 115 API成功返回state=true或code=0
                if result.get("state") is True or result.get("code") == 0:
                    logger.info(f"复制文件成功: file_id={file_id or file_ids}, target_parent_id={target_parent_id}")
                    return {
                        "success": True,
                        "data": result.get("data", [])
                    }
                else:
                    error_msg = result.get("message", "未知错误")
                    error_code = result.get("code")
                    logger.error(f"复制文件失败: {error_msg} (code: {error_code})")
                    return {
                        "success": False,
                        "message": error_msg,
                        "code": error_code
                    }
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"复制文件HTTP错误: {e.response.status_code}")
                if e.response.status_code == 401:
                    logger.error("访问令牌无效或已过期，请刷新令牌")
                return {"success": False, "message": f"HTTP错误: {e.response.status_code}"}
            except Exception as e:
                logger.error(f"复制文件异常: {e}")
                return {"success": False, "message": str(e)}
    
    async def search_files_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        file_type: Optional[int] = 4,  # 4:视频
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        根据时间范围搜索文件（用于增量同步）
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            file_type: 文件类型（4:视频）
            limit: 每页记录数
            offset: 偏移量
        
        Returns:
            文件列表
        """
        gte_day = start_time.strftime("%Y-%m-%d")
        lte_day = end_time.strftime("%Y-%m-%d")
        
        all_files = []
        current_offset = offset
        
        while True:
            result = await self.search_files(
                search_value="",  # 空字符串，或者使用通配符"*"
                limit=limit,
                offset=current_offset,
                gte_day=gte_day,
                lte_day=lte_day,
                fc=2,  # 只显示文件
                file_type=file_type
            )
            
            files = result.get("data", [])
            if not files:
                break
            
            # 过滤出正常状态的文件（area_id=1）
            # area_id=7表示删除(回收站)，area_id=120表示彻底删除
            normal_files = [
                f for f in files 
                if f.get("area_id") == "1"  # 只处理正常状态的文件
            ]
            all_files.extend(normal_files)
            
            # 检查是否还有更多数据
            total_count = result.get("count", 0)
            if len(files) < limit or current_offset + limit >= total_count:
                break
            
            current_offset += limit
            
            # 防止无限循环
            if current_offset >= 10000:  # offset+limit最大不超过10000
                logger.warning("达到搜索API的最大偏移量限制（10000）")
                break
        
        return all_files
    
    async def get_files_by_path(
        self,
        path: str,
        recursive: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        根据路径获取文件列表
        
        Args:
            path: 目录路径
            recursive: 是否递归获取
            limit: 单页记录数
            offset: 偏移量
        
        Returns:
            文件列表
        """
        try:
            # 使用list_files API获取目录下的文件列表
            result = await self.list_files(
                path=path,
                limit=limit,
                offset=offset
            )
            
            files = result.get("data", [])
            
            if recursive:
                # 递归获取子目录下的文件
                all_files = list(files)
                
                for item in files:
                    if item.get("file_category") == "0":  # 文件夹
                        sub_path = f"{path.rstrip('/')}/{item.get('file_name')}"
                        sub_files = await self.get_files_by_path(
                            path=sub_path,
                            recursive=True,
                            limit=limit,
                            offset=0
                        )
                        all_files.extend(sub_files)
                
                return all_files
            else:
                return files
                
        except Exception as e:
            logger.error(f"根据路径获取文件列表失败: {e}")
            return []
    
    async def get_file_changes(
        self,
        last_sync_time: datetime,
        file_type: Optional[int] = 4  # 4:视频
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取文件变更（用于实时对比）
        
        Args:
            last_sync_time: 上次同步时间
            file_type: 文件类型（4:视频）
        
        Returns:
            文件变更（新增、更新、删除）
        """
        changes = {
            "added": [],
            "updated": [],
            "deleted": []
        }
        
        try:
            # 获取时间范围内的文件
            end_time = datetime.now()
            files = await self.search_files_by_time_range(
                start_time=last_sync_time,
                end_time=end_time,
                file_type=file_type
            )
            
            # 根据文件的user_ptime和user_utime判断是新增还是更新
            for file in files:
                user_ptime_str = file.get("user_ptime")
                user_utime_str = file.get("user_utime")
                
                # 解析时间字符串
                user_ptime = None
                user_utime = None
                
                if user_ptime_str:
                    try:
                        # 尝试解析时间字符串（可能是ISO格式或其他格式）
                        user_ptime = self._parse_time_string(user_ptime_str)
                    except Exception as e:
                        logger.warning(f"解析上传时间失败: {user_ptime_str} - {e}")
                
                if user_utime_str:
                    try:
                        user_utime = self._parse_time_string(user_utime_str)
                    except Exception as e:
                        logger.warning(f"解析更新时间失败: {user_utime_str} - {e}")
                
                # 判断是新增还是更新
                if user_ptime and user_ptime > last_sync_time:
                    changes["added"].append(file)
                elif user_utime and user_utime > last_sync_time:
                    changes["updated"].append(file)
            
            # 检测删除的文件
            # 通过area_id字段判断（area_id=7表示删除，120表示彻底删除）
            # 注意：搜索API可能不返回已删除的文件，需要通过其他方式检测
            # 可以定期全量扫描，对比文件列表找出删除的文件
            # 或者使用115网盘的文件变更通知API（如果有的话）
            
        except Exception as e:
            logger.error(f"获取文件变更失败: {e}")
        
        return changes
    
    def _parse_time_string(self, time_str: str) -> datetime:
        """解析时间字符串"""
        # 尝试多种时间格式
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S+00:00",
            "%Y-%m-%d"
        ]
        
        for fmt in formats:
            try:
                if fmt == "%Y-%m-%dT%H:%M:%SZ":
                    return datetime.strptime(time_str.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
                elif fmt == "%Y-%m-%dT%H:%M:%S+00:00":
                    return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                else:
                    return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        
        # 如果所有格式都失败，返回当前时间
        logger.warning(f"无法解析时间字符串: {time_str}")
        return datetime.now()
    
    async def create_folder(
        self,
        parent_id: str,
        folder_name: str
    ) -> Dict[str, Any]:
        """
        新建文件夹
        参考：115网盘开放API文档 - 新建文件夹
        使用proapi.115.com的API端点: /open/folder/add
        
        API说明：
        - 请求头: Authorization: Bearer access_token
        - 请求体: form-data格式
        - 参数: pid (父目录ID), file_name (文件夹名称，限制255个字符)
        - 响应: state (boolean), message (string), code (number), data (object)
        - data包含: file_name (新建的文件夹名称), file_id (新建的文件夹ID)
        
        Args:
            parent_id: 父目录ID（根目录的ID通常为0或特定值，如"3073323042143855813"）
            folder_name: 文件夹名称（限制255个字符）
        
        Returns:
            创建的文件夹信息，包含：
            - file_name: 新建的文件夹名称
            - file_id: 新建的文件夹ID
        """
        url = f"{self.base_url}/open/folder/add"
        
        # 根据官方文档，pid和file_name都是text类型
        # 但实际API可能接受int类型的pid，为了兼容性，先尝试转换为int，失败则使用字符串
        try:
            pid_value = int(parent_id)
        except (ValueError, TypeError):
            pid_value = parent_id
        
        data = {
            "pid": pid_value,
            "file_name": folder_name
        }
        
        # 验证文件夹名称长度
        if len(folder_name) > 255:
            logger.error(f"文件夹名称过长: {len(folder_name)}字符，限制255个字符")
            return {}
        
        async with httpx.AsyncClient() as client:
            try:
                # 使用POST方法，通过form-data传递数据
                # 移除Content-Type头部，让httpx自动设置form-data
                headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
                response = await client.post(url, data=data, headers=headers)
                
                response.raise_for_status()
                result = response.json()
                
                # 115 API成功返回state=true或code=0
                # 根据官方文档，state是boolean类型，true表示正常，false表示异常
                if result.get("state") is True or result.get("code") == 0:
                    data = result.get("data", {})
                    
                    # 返回创建的文件夹信息
                    folder_info = {
                        "file_name": data.get("file_name", folder_name),
                        "file_id": data.get("file_id", "")
                    }
                    
                    logger.info(f"创建文件夹成功: {folder_name} (file_id: {folder_info.get('file_id')})")
                    return folder_info
                else:
                    error_msg = result.get("message", "未知错误")
                    error_code = result.get("code")
                    logger.error(f"创建文件夹失败: {error_msg} (code: {error_code})")
                    return {}
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"创建文件夹HTTP错误: {e.response.status_code}")
                if e.response.status_code == 401:
                    logger.error("访问令牌无效或已过期，请刷新令牌")
                return {}
            except Exception as e:
                logger.error(f"创建文件夹异常: {e}")
                return {}
    
    async def create_folder_by_path(
        self,
        parent_path: str,
        folder_name: str
    ) -> Dict[str, Any]:
        """
        根据路径创建文件夹
        
        Args:
            parent_path: 父目录路径
            folder_name: 文件夹名称
        
        Returns:
            创建的文件夹信息
        """
        try:
            # 首先获取父目录信息
            parent_info = await self.get_file_info(path=parent_path)
            
            if not parent_info:
                logger.error(f"父目录不存在: {parent_path}")
                return {}
            
            parent_id = parent_info.get("file_id")
            if not parent_id:
                logger.error(f"无法获取父目录ID: {parent_path}")
                return {}
            
            # 创建文件夹
            return await self.create_folder(parent_id=parent_id, folder_name=folder_name)
            
        except Exception as e:
            logger.error(f"根据路径创建文件夹失败: {e}")
            return {}
    
    async def get_download_url(
        self,
        pick_code: str
    ) -> Dict[str, Any]:
        """
        获取文件下载地址
        参考：115网盘开放API文档 - 获取文件下载地址
        使用proapi.115.com的API端点: /open/ufile/downurl
        
        API说明：
        - 请求头: Authorization: Bearer access_token
        - 请求方法: POST
        - 请求体: form-data格式
        - 参数: pick_code (文件提取码)
        - 功能: 根据文件提取码获取文件下载地址
        
        Args:
            pick_code: 文件提取码
        
        Returns:
            文件下载信息，包含：
            - success: 是否成功
            - file_id: 文件ID
            - file_name: 文件名
            - file_size: 文件大小
            - pick_code: 文件提取码
            - sha1: 文件sha1值
            - download_url: 文件下载地址
        """
        url = f"{self.base_url}/open/ufile/downurl"
        
        async with httpx.AsyncClient() as client:
            try:
                data = {
                    "pick_code": pick_code
                }
                
                headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
                response = await client.post(url, data=data, headers=headers)
                
                response.raise_for_status()
                result = response.json()
                
                # 115 API成功返回state=true或code=0
                if result.get("state") is True or result.get("code") == 0:
                    data_result = result.get("data", {})
                    
                    # data是一个对象，key是文件ID，value是文件信息
                    # 返回第一个文件的信息（通常只有一个文件）
                    if data_result:
                        # 获取第一个文件的ID和信息
                        file_id = list(data_result.keys())[0]
                        file_info = data_result[file_id]
                        
                        logger.info(f"获取文件下载地址成功: pick_code={pick_code}, file_id={file_id}")
                        return {
                            "success": True,
                            "file_id": file_id,
                            "file_name": file_info.get("file_name", ""),
                            "file_size": file_info.get("file_size", 0),
                            "pick_code": file_info.get("pick_code", pick_code),
                            "sha1": file_info.get("sha1", ""),
                            "download_url": file_info.get("url", {}).get("url", "")  # url对象中的url字段
                        }
                    else:
                        logger.warning(f"获取文件下载地址返回空数据: pick_code={pick_code}")
                        return {
                            "success": False,
                            "error": "返回数据为空"
                        }
                else:
                    error_msg = result.get("message", "未知错误")
                    error_code = result.get("code")
                    logger.error(f"获取文件下载地址失败: {error_msg} (code: {error_code})")
                    return {
                        "success": False,
                        "error": error_msg,
                        "code": error_code
                    }
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"获取文件下载地址HTTP错误: {e.response.status_code}")
                if e.response.status_code == 401:
                    logger.error("访问令牌无效或已过期，请刷新令牌")
                return {
                    "success": False,
                    "error": f"HTTP错误: {e.response.status_code}"
                }
            except Exception as e:
                logger.error(f"获取文件下载地址异常: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
    
    async def get_video_subtitle_list(
        self,
        pick_code: str
    ) -> Dict[str, Any]:
        """
        获取视频字幕列表
        参考：115网盘开放API文档 - 视频字幕列表
        使用proapi.115.com的API端点: /open/video/subtitle
        
        API说明：
        - 请求头: Authorization: Bearer access_token
        - 请求方法: GET
        - 查询参数: pick_code (必须) - 视频文件提取码
        
        Args:
            pick_code: 视频文件提取码
        
        Returns:
            字幕列表信息，包括：
            - autoload: 自动载入字幕列表
            - list: 字幕列表（数组）
                每个字幕项包含：
                - sid: 字幕ID
                - language: 语言
                - title: 字幕标题
                - url: 字幕文件地址
                - type: 字幕文件类型
                - sha1: 字幕文件哈希值
                - file_id: 字幕文件ID
                - file_name: 外挂字幕文件名
                - pick_code: 外挂字幕文件提取码
                - caption_map_id: 字幕映射ID
                - is_caption_map: 是否为字幕映射
                - sync_time: 字幕同步时间
        """
        try:
            url = f"{self.base_url}/open/video/subtitle"
            params = {
                "pick_code": pick_code
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                
                # 检查响应状态
                if result.get("state") is False:
                    error_msg = result.get("message", "获取视频字幕列表失败")
                    logger.error(f"获取视频字幕列表失败: {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "code": result.get("code")
                    }
                
                # 解析返回数据
                data = result.get("data", {})
                autoload = data.get("autoload")
                subtitle_list = data.get("list", [])
                
                logger.info(f"获取视频字幕列表成功: pick_code={pick_code}, 字幕数量={len(subtitle_list)}")
                
                return {
                    "success": True,
                    "pick_code": pick_code,
                    "autoload": autoload,
                    "list": subtitle_list,
                    "count": len(subtitle_list)
                }
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("获取视频字幕列表失败: 认证失败，请检查access_token")
                return {
                    "success": False,
                    "error": "认证失败，请检查access_token",
                    "code": 401
                }
            else:
                logger.error(f"获取视频字幕列表HTTP错误: {e.response.status_code} - {e.response.text}")
                return {
                    "success": False,
                    "error": f"HTTP错误: {e.response.status_code}",
                    "code": e.response.status_code
                }
        except Exception as e:
            logger.error(f"获取视频字幕列表异常: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_upload_token(self) -> Dict[str, Any]:
        """
        获取上传凭证
        参考：115网盘开放API文档 - 获取上传凭证
        使用proapi.115.com的API端点: /open/upload/get_token
        
        API说明：
        - 请求头: Authorization: Bearer access_token
        - 请求方法: GET
        - 功能: 获取上传凭证
        
        Returns:
            上传凭证信息，包含：
            - success: 是否成功
            - endpoint: 上传域名
            - access_key_id: 上传凭证-ID
            - access_key_secret: 上传凭证-密钥
            - security_token: 上传凭证-token
            - expiration: 上传凭证-过期日期
        """
        url = f"{self.base_url}/open/upload/get_token"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                result = response.json()
                
                # 115 API成功返回state=true或code=0
                if result.get("state") is True or result.get("code") == 0:
                    data = result.get("data", [])
                    
                    # data是一个对象数组，通常只有一个元素
                    if data and len(data) > 0:
                        token_info = data[0]
                        
                        logger.info("获取上传凭证成功")
                        return {
                            "success": True,
                            "endpoint": token_info.get("endpoint", ""),
                            "access_key_id": token_info.get("AccessKeyId", ""),
                            "access_key_secret": token_info.get("AccessKeySecrett", ""),  # 注意：官方文档中字段名是AccessKeySecrett（有两个t）
                            "security_token": token_info.get("SecurityToken", ""),
                            "expiration": token_info.get("Expiration", "")
                        }
                    else:
                        logger.warning("获取上传凭证返回空数据")
                        return {
                            "success": False,
                            "error": "返回数据为空"
                        }
                else:
                    error_msg = result.get("message", "未知错误")
                    error_code = result.get("code")
                    logger.error(f"获取上传凭证失败: {error_msg} (code: {error_code})")
                    return {
                        "success": False,
                        "error": error_msg,
                        "code": error_code
                    }
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"获取上传凭证HTTP错误: {e.response.status_code}")
                if e.response.status_code == 401:
                    logger.error("访问令牌无效或已过期，请刷新令牌")
                return {
                    "success": False,
                    "error": f"HTTP错误: {e.response.status_code}"
                }
            except Exception as e:
                logger.error(f"获取上传凭证异常: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
    
    async def init_upload(
        self,
        file_name: str,
        file_size: int,
        target_parent_id: str,
        file_sha1: str,
        pre_sha1: Optional[str] = None,
        pick_code: Optional[str] = None,
        topupload: Optional[int] = None,
        sign_key: Optional[str] = None,
        sign_val: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        文件上传初始化（断点续传上传初始化调度接口）
        参考：115网盘开放API文档 - 文件上传
        使用proapi.115.com的API端点: /open/upload/init
        
        API说明：
        - 请求头: Authorization: Bearer access_token
        - 请求方法: POST
        - 请求体: form-data格式
        - 功能: 断点续传上传初始化调度接口
        
        Args:
            file_name: 文件名
            file_size: 文件大小（字节）
            target_parent_id: 文件上传目标目录ID（0代表根目录，其他数字是文件夹ID）
            file_sha1: 文件sha1值
            pre_sha1: 文件前128K sha1值（可选）
            pick_code: 上传任务key（可选，非秒传的调度接口返回的pick_code字段）
            topupload: 上传调度文件类型调度标记（可选）
                - 0: 单文件上传任务标识一条单独的文件上传记录
                - 1: 文件夹任务调度的第一个子文件上传请求标识一次文件夹上传记录
                - 2: 文件夹任务调度的其余后续子文件不作记作单独上传的上传记录
                - -1: 没有该参数
            sign_key: 二次认证需要（可选）
            sign_val: 二次认证需要（可选，大写）
        
        Returns:
            上传初始化结果，包含：
            - success: 是否成功
            - pick_code: 上传任务唯一ID，用于续传
            - status: 上传状态（1:非秒传; 2:秒传）
            - file_id: 秒传成功返回的新增文件ID
            - target: 文件上传目标约定
            - bucket: 上传的bucket
            - object: OSS objectID
            - callback: 上传完回调信息
            - callback_var: 上传完回调参数
            - sign_key: 本次计算的sha1标识（二次认证）
            - sign_check: 本次计算本地文件sha1区间范围（二次认证）
        """
        url = f"{self.base_url}/open/upload/init"
        
        async with httpx.AsyncClient() as client:
            try:
                # 构建target参数（U_1_0格式，U_1是固定约定，0代表根目录，其他数字是文件夹ID）
                target = f"U_1_{target_parent_id}"
                
                data = {
                    "file_name": file_name,
                    "file_size": str(file_size),
                    "target": target,
                    "fileid": file_sha1  # 文件sha1值
                }
                
                # 添加可选参数
                if pre_sha1:
                    data["preid"] = pre_sha1  # 文件前128K sha1
                
                if pick_code:
                    data["pick_code"] = pick_code  # 上传任务key
                
                if topupload is not None:
                    data["topupload"] = str(topupload)
                
                if sign_key:
                    data["sign_key"] = sign_key
                
                if sign_val:
                    data["sign_val"] = sign_val.upper()  # 大写
                
                headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
                response = await client.post(url, data=data, headers=headers)
                
                response.raise_for_status()
                result = response.json()
                
                # 115 API成功返回state=true或code=0
                if result.get("state") is True or result.get("code") == 0:
                    data_result = result.get("data", [])
                    
                    # data是一个对象数组，通常只有一个元素
                    if data_result and len(data_result) > 0:
                        upload_info = data_result[0]
                        
                        logger.info(f"文件上传初始化成功: file_name={file_name}, status={upload_info.get('status')}")
                        return {
                            "success": True,
                            "pick_code": upload_info.get("pick_code", ""),
                            "status": upload_info.get("status", 1),  # 1:非秒传; 2:秒传
                            "file_id": upload_info.get("file_id", ""),  # 秒传成功返回的文件ID
                            "target": upload_info.get("target", target),
                            "bucket": upload_info.get("bucket", ""),
                            "object": upload_info.get("object", ""),
                            "callback": upload_info.get("callback", [{}])[0].get("callback", "") if upload_info.get("callback") else "",
                            "callback_var": upload_info.get("callback", [{}])[0].get("callback_var", "") if upload_info.get("callback") else "",
                            "sign_key": upload_info.get("sign_key", ""),
                            "sign_check": upload_info.get("sign_check", "")
                        }
                    else:
                        logger.warning("文件上传初始化返回空数据")
                        return {
                            "success": False,
                            "error": "返回数据为空"
                        }
                else:
                    error_msg = result.get("message", "未知错误")
                    error_code = result.get("code")
                    
                    # 处理二次认证相关的错误码
                    if error_code in [700, 701, 702]:
                        logger.warning(f"文件上传初始化需要二次认证: code={error_code}, message={error_msg}")
                        # 返回错误信息，包含status字段用于二次认证
                        data_result = result.get("data", [])
                        if data_result and len(data_result) > 0:
                            upload_info = data_result[0]
                            return {
                                "success": False,
                                "error": error_msg,
                                "code": error_code,
                                "status": upload_info.get("status"),  # 6, 7, 8
                                "sign_key": upload_info.get("sign_key", ""),
                                "sign_check": upload_info.get("sign_check", "")
                            }
                    
                    logger.error(f"文件上传初始化失败: {error_msg} (code: {error_code})")
                    return {
                        "success": False,
                        "error": error_msg,
                        "code": error_code
                    }
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"文件上传初始化HTTP错误: {e.response.status_code}")
                if e.response.status_code == 401:
                    logger.error("访问令牌无效或已过期，请刷新令牌")
                return {
                    "success": False,
                    "error": f"HTTP错误: {e.response.status_code}"
                }
            except Exception as e:
                logger.error(f"文件上传初始化异常: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
    
    async def resume_upload(
        self,
        file_size: int,
        target_parent_id: str,
        file_sha1: str,
        pick_code: str
    ) -> Dict[str, Any]:
        """
        断点续传上传续传调度接口
        参考：115网盘开放API文档 - 断点续传
        使用proapi.115.com的API端点: /open/upload/resume
        
        API说明：
        - 请求头: Authorization: Bearer access_token
        - 请求方法: POST
        - 请求体: form-data格式
        - 功能: 断点续传上传续传调度接口
        
        Args:
            file_size: 文件大小（字节）
            target_parent_id: 文件上传目标目录ID（0代表根目录，其他数字是文件夹ID）
            file_sha1: 文件sha1值
            pick_code: 上传任务key（非秒传的调度接口返回的pick_code字段）
        
        Returns:
            续传调度结果，包含：
            - success: 是否成功
            - pick_code: 上传任务唯一ID，用于续传
            - target: 文件上传目标约定
            - version: 接口版本
            - bucket: 上传的bucket
            - object: OSS objectID
            - callback: 上传完回调信息
            - callback_var: 上传完回调参数
        """
        url = f"{self.base_url}/open/upload/resume"
        
        async with httpx.AsyncClient() as client:
            try:
                # 构建target参数（U_1_0格式，U_1是固定约定，0代表根目录，其他数字是文件夹ID）
                target = f"U_1_{target_parent_id}"
                
                data = {
                    "file_size": str(file_size),
                    "target": target,
                    "fileid": file_sha1,  # 文件sha1值
                    "pick_code": pick_code  # 上传任务key
                }
                
                headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
                response = await client.post(url, data=data, headers=headers)
                
                response.raise_for_status()
                result = response.json()
                
                # 115 API成功返回state=true或code=0
                if result.get("state") is True or result.get("code") == 0:
                    data_result = result.get("data", [])
                    
                    # data是一个对象数组，通常只有一个元素
                    if data_result and len(data_result) > 0:
                        resume_info = data_result[0]
                        
                        logger.info(f"断点续传调度成功: pick_code={pick_code}")
                        return {
                            "success": True,
                            "pick_code": resume_info.get("pick_code", pick_code),
                            "target": resume_info.get("target", target),
                            "version": resume_info.get("version", ""),
                            "bucket": resume_info.get("bucket", ""),
                            "object": resume_info.get("object", ""),
                            "callback": resume_info.get("callback", [{}])[0].get("callback", "") if resume_info.get("callback") else "",
                            "callback_var": resume_info.get("callback", [{}])[0].get("callback_var", "") if resume_info.get("callback") else ""
                        }
                    else:
                        logger.warning("断点续传调度返回空数据")
                        return {
                            "success": False,
                            "error": "返回数据为空"
                        }
                else:
                    error_msg = result.get("message", "未知错误")
                    error_code = result.get("code")
                    logger.error(f"断点续传调度失败: {error_msg} (code: {error_code})")
                    return {
                        "success": False,
                        "error": error_msg,
                        "code": error_code
                    }
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"断点续传调度HTTP错误: {e.response.status_code}")
                if e.response.status_code == 401:
                    logger.error("访问令牌无效或已过期，请刷新令牌")
                return {
                    "success": False,
                    "error": f"HTTP错误: {e.response.status_code}"
                }
            except Exception as e:
                logger.error(f"断点续传调度异常: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
    
    def parse_file_path(self, path: str) -> str:
        """
        解析文件路径（支持/和>分隔符）
        
        Args:
            path: 文件路径
        
        Returns:
            标准化路径
        """
        # 115网盘API支持/和>两种分隔符
        # 最前面需分隔符开头，以分隔符分隔目录层级
        if not path.startswith(("/", ">")):
            path = "/" + path
        
        return path
    
    async def get_video_play_info(self, pick_code: str) -> Dict[str, Any]:
        """
        获取视频播放信息
        参考：115网盘开放API文档 - 视频播放
        使用proapi.115.com的API端点: /open/video/play
        
        Args:
            pick_code: 文件提取码
        
        Returns:
            视频播放信息，包含：
            - success: bool
            - message: str
            - file: dict (文件信息)
            - qualities: list (清晰度列表)
            - raw: dict (原始响应数据)
        """
        url = f"{self.base_url}/open/video/play"
        
        async with httpx.AsyncClient() as client:
            try:
                data = {
                    "pick_code": pick_code
                }
                
                headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
                response = await client.post(url, data=data, headers=headers)
                
                response.raise_for_status()
                result = response.json()
                
                # 115 API成功返回state=true或code=0
                if result.get("state") is True or result.get("code") == 0:
                    data_result = result.get("data", {})
                    
                    # 解析文件信息
                    file_info = {
                        "id": data_result.get("file_id", ""),
                        "name": data_result.get("file_name", ""),
                        "size": data_result.get("file_size", 0),
                        "sha1": data_result.get("file_sha1", ""),
                        "type": data_result.get("file_type", ""),
                    }
                    
                    # 解析时长（play_long可能是字符串或数字）
                    play_long = data_result.get("play_long", 0)
                    if isinstance(play_long, str):
                        try:
                            play_long = int(play_long)
                        except (ValueError, TypeError):
                            play_long = 0
                    file_info["duration"] = max(0, int(play_long)) if play_long else 0
                    
                    # 解析清晰度列表
                    qualities = []
                    definition_list = data_result.get("definition_list_new", [])
                    
                    for idx, def_item in enumerate(definition_list):
                        video_urls = def_item.get("video_url", [])
                        if not video_urls:
                            continue
                        
                        # 取第一个可用的视频URL
                        video_url = video_urls[0] if isinstance(video_urls, list) else video_urls
                        if isinstance(video_url, dict):
                            url_str = video_url.get("url", "")
                        else:
                            url_str = str(video_url)
                        
                        if not url_str:
                            continue
                        
                        # 构建清晰度ID和标题
                        definition = def_item.get("definition", "")
                        definition_n = def_item.get("definition_n", "")
                        title = def_item.get("title", definition or definition_n or f"清晰度{idx+1}")
                        
                        quality = {
                            "id": definition_n or definition or f"def_{idx}",
                            "title": title,
                            "height": def_item.get("height", 0),
                            "width": def_item.get("width", 0),
                            "url": url_str
                        }
                        qualities.append(quality)
                    
                    logger.info(f"获取视频播放信息成功: pick_code={pick_code}, 清晰度数量={len(qualities)}")
                    return {
                        "success": True,
                        "message": result.get("message", "success"),
                        "file": file_info,
                        "qualities": qualities,
                        "raw": data_result
                    }
                else:
                    error_msg = result.get("message", "获取视频播放信息失败")
                    error_code = result.get("code", -1)
                    logger.error(f"获取视频播放信息失败: {error_msg} (code={error_code})")
                    return {
                        "success": False,
                        "message": error_msg,
                        "code": error_code
                    }
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"获取视频播放信息HTTP错误: {e.response.status_code}")
                if e.response.status_code == 401:
                    logger.error("访问令牌无效或已过期，请刷新令牌")
                return {
                    "success": False,
                    "message": f"HTTP错误: {e.response.status_code}",
                    "code": e.response.status_code
                }
            except Exception as e:
                logger.error(f"获取视频播放信息异常: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e),
                    "code": -1
                }
    
    async def get_video_subtitles(self, pick_code: str) -> Dict[str, Any]:
        """
        获取视频字幕列表
        参考：115网盘开放API文档 - 视频字幕
        使用proapi.115.com的API端点: /open/video/subtitle
        
        Args:
            pick_code: 文件提取码
        
        Returns:
            字幕列表，包含：
            - success: bool
            - subtitles: list (字幕列表)
        """
        url = f"{self.base_url}/open/video/subtitle"
        
        async with httpx.AsyncClient() as client:
            try:
                params = {
                    "pick_code": pick_code
                }
                
                response = await client.get(url, params=params, headers=self.headers)
                
                response.raise_for_status()
                result = response.json()
                
                # 115 API成功返回state=true或code=0
                if result.get("state") is True or result.get("code") == 0:
                    data_result = result.get("data", {})
                    
                    # 获取自动加载的字幕ID
                    autoload = data_result.get("autoload", "")
                    autoload_sid = None
                    if autoload:
                        # autoload可能是字符串格式的sid
                        autoload_sid = str(autoload)
                    
                    # 解析字幕列表
                    subtitles = []
                    subtitle_list = data_result.get("list", [])
                    
                    for sub_item in subtitle_list:
                        subtitle = {
                            "sid": str(sub_item.get("sid", "")),
                            "language": sub_item.get("language", ""),
                            "title": sub_item.get("title", ""),
                            "url": sub_item.get("url", ""),
                            "is_default": False,
                            "sync_time": sub_item.get("sync_time", 0)
                        }
                        
                        # 判断是否为默认字幕
                        if autoload_sid and subtitle["sid"] == autoload_sid:
                            subtitle["is_default"] = True
                        
                        subtitles.append(subtitle)
                    
                    logger.info(f"获取视频字幕列表成功: pick_code={pick_code}, 字幕数量={len(subtitles)}")
                    return {
                        "success": True,
                        "subtitles": subtitles
                    }
                else:
                    error_msg = result.get("message", "获取视频字幕列表失败")
                    error_code = result.get("code", -1)
                    logger.error(f"获取视频字幕列表失败: {error_msg} (code={error_code})")
                    return {
                        "success": False,
                        "subtitles": [],
                        "message": error_msg,
                        "code": error_code
                    }
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"获取视频字幕列表HTTP错误: {e.response.status_code}")
                if e.response.status_code == 401:
                    logger.error("访问令牌无效或已过期，请刷新令牌")
                return {
                    "success": False,
                    "subtitles": [],
                    "message": f"HTTP错误: {e.response.status_code}",
                    "code": e.response.status_code
                }
            except Exception as e:
                logger.error(f"获取视频字幕列表异常: {e}", exc_info=True)
                return {
                    "success": False,
                    "subtitles": [],
                    "message": str(e),
                    "code": -1
                }
    
    async def get_video_history(self, pick_code: str) -> Dict[str, Any]:
        """
        获取视频观看历史
        参考：115网盘开放API文档 - 视频历史
        使用proapi.115.com的API端点: /open/video/history
        
        Args:
            pick_code: 文件提取码
        
        Returns:
            观看历史，包含：
            - success: bool
            - position: int (已播放秒数)
            - raw: list (原始响应数据)
        """
        url = f"{self.base_url}/open/video/history"
        
        async with httpx.AsyncClient() as client:
            try:
                data = {
                    "pick_code": pick_code
                }
                
                headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
                response = await client.post(url, data=data, headers=headers)
                
                response.raise_for_status()
                result = response.json()
                
                # 115 API成功返回state=true或code=0
                if result.get("state") is True or result.get("code") == 0:
                    data_result = result.get("data", [])
                    
                    # 取最新一条记录（按add_time最大或最后一个元素）
                    position = 0
                    if data_result and isinstance(data_result, list) and len(data_result) > 0:
                        # 找到最新的记录（按add_time排序，或直接取最后一个）
                        latest = data_result[-1] if data_result else None
                        if latest:
                            time_value = latest.get("time", 0)
                            # 转换为秒数（如果是字符串就int()）
                            if isinstance(time_value, str):
                                try:
                                    position = int(time_value)
                                except (ValueError, TypeError):
                                    position = 0
                            else:
                                position = int(time_value) if time_value else 0
                    
                    logger.info(f"获取视频观看历史成功: pick_code={pick_code}, position={position}秒")
                    return {
                        "success": True,
                        "position": max(0, position),
                        "raw": data_result
                    }
                else:
                    # 如果没有历史记录，返回position=0
                    logger.debug(f"视频无观看历史: pick_code={pick_code}")
                    return {
                        "success": True,
                        "position": 0,
                        "raw": []
                    }
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"获取视频观看历史HTTP错误: {e.response.status_code}")
                if e.response.status_code == 401:
                    logger.error("访问令牌无效或已过期，请刷新令牌")
                return {
                    "success": False,
                    "position": 0,
                    "message": f"HTTP错误: {e.response.status_code}",
                    "code": e.response.status_code
                }
            except Exception as e:
                logger.error(f"获取视频观看历史异常: {e}", exc_info=True)
                return {
                    "success": False,
                    "position": 0,
                    "message": str(e),
                    "code": -1
                }
    
    async def set_video_history(self, pick_code: str, time_sec: int, watch_end: bool = False) -> Dict[str, Any]:
        """
        更新视频观看历史
        参考：115网盘开放API文档 - 视频历史
        使用proapi.115.com的API端点: /open/video/history
        
        Args:
            pick_code: 文件提取码
            time_sec: 已播放秒数
            watch_end: 是否播放完成
        
        Returns:
            更新结果，包含：
            - success: bool
            - message: str
            - code: int
        """
        url = f"{self.base_url}/open/video/history"
        
        async with httpx.AsyncClient() as client:
            try:
                data = {
                    "pick_code": pick_code,
                    "time": int(time_sec),
                    "watch_end": 1 if watch_end else 0
                }
                
                headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
                response = await client.post(url, data=data, headers=headers)
                
                response.raise_for_status()
                result = response.json()
                
                # 115 API成功返回state=true或code=0
                if result.get("state") is True or result.get("code") == 0:
                    logger.info(f"更新视频观看历史成功: pick_code={pick_code}, time={time_sec}秒, watch_end={watch_end}")
                    return {
                        "success": True,
                        "message": result.get("message", "success"),
                        "code": result.get("code", 0)
                    }
                else:
                    error_msg = result.get("message", "更新视频观看历史失败")
                    error_code = result.get("code", -1)
                    logger.error(f"更新视频观看历史失败: {error_msg} (code={error_code})")
                    return {
                        "success": False,
                        "message": error_msg,
                        "code": error_code
                    }
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"更新视频观看历史HTTP错误: {e.response.status_code}")
                if e.response.status_code == 401:
                    logger.error("访问令牌无效或已过期，请刷新令牌")
                return {
                    "success": False,
                    "message": f"HTTP错误: {e.response.status_code}",
                    "code": e.response.status_code
                }
            except Exception as e:
                logger.error(f"更新视频观看历史异常: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e),
                    "code": -1
                }
    
    async def push_video_transcode(self, pick_code: str, op: str = "vip_push") -> Dict[str, Any]:
        """
        推送视频转码任务（可选功能）
        参考：115网盘开放API文档 - 视频转码推送
        使用proapi.115.com的API端点: /open/video/video_push
        
        Args:
            pick_code: 文件提取码
            op: 操作类型（vip_push / pay_push）
        
        Returns:
            推送结果，包含：
            - success: bool
            - message: str
            - code: int
        """
        url = f"{self.base_url}/open/video/video_push"
        
        async with httpx.AsyncClient() as client:
            try:
                data = {
                    "pick_code": pick_code,
                    "op": op
                }
                
                headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
                response = await client.post(url, data=data, headers=headers)
                
                response.raise_for_status()
                result = response.json()
                
                # 115 API成功返回state=true或code=0
                if result.get("state") is True or result.get("code") == 0:
                    logger.info(f"推送视频转码任务成功: pick_code={pick_code}, op={op}")
                    return {
                        "success": True,
                        "message": result.get("message", "success"),
                        "code": result.get("code", 0)
                    }
                else:
                    error_msg = result.get("message", "推送视频转码任务失败")
                    error_code = result.get("code", -1)
                    logger.error(f"推送视频转码任务失败: {error_msg} (code={error_code})")
                    return {
                        "success": False,
                        "message": error_msg,
                        "code": error_code
                    }
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"推送视频转码任务HTTP错误: {e.response.status_code}")
                if e.response.status_code == 401:
                    logger.error("访问令牌无效或已过期，请刷新令牌")
                return {
                    "success": False,
                    "message": f"HTTP错误: {e.response.status_code}",
                    "code": e.response.status_code
                }
            except Exception as e:
                logger.error(f"推送视频转码任务异常: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e),
                    "code": -1
                }