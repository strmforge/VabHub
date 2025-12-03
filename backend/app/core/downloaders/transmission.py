"""
Transmission下载器集成
"""
import httpx
from typing import Optional, Dict, List
from loguru import logger
import base64
import json


class TransmissionClient:
    """Transmission客户端"""
    
    def __init__(self, host: str = "localhost", port: int = 9091, username: str = "", password: str = "", rpc_path: str = "/transmission/rpc"):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.rpc_path = rpc_path
        self.base_url = f"http://{host}:{port}{rpc_path}"
        self.session = httpx.AsyncClient(timeout=30.0)
        self.session_id = None
    
    def _get_auth_header(self) -> str:
        """生成认证头"""
        credentials = f"{self.username or 'admin'}:{self.password or 'admin'}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    async def _get_session_id(self) -> str:
        """获取会话ID"""
        try:
            headers = {
                "Authorization": self._get_auth_header(),
                "Content-Type": "application/json"
            }
            response = await self.session.post(
                self.base_url,
                headers=headers,
                content=""
            )
            if response.status_code == 409:  # 需要会话ID
                self.session_id = response.headers.get("X-Transmission-Session-Id")
            return self.session_id or ""
        except Exception as e:
            logger.error(f"获取Transmission会话ID异常: {e}")
            return ""
    
    async def _request(self, method: str, arguments: Optional[Dict] = None) -> Optional[Dict]:
        """发送RPC请求"""
        try:
            if not self.session_id:
                await self._get_session_id()
            
            headers = {
                "Authorization": self._get_auth_header(),
                "Content-Type": "application/json",
                "X-Transmission-Session-Id": self.session_id or ""
            }
            
            data = {
                "method": method
            }
            if arguments:
                data["arguments"] = arguments
            
            response = await self.session.post(
                self.base_url,
                headers=headers,
                json=data
            )
            
            if response.status_code == 409:  # 需要更新会话ID
                self.session_id = response.headers.get("X-Transmission-Session-Id")
                headers["X-Transmission-Session-Id"] = self.session_id
                response = await self.session.post(
                    self.base_url,
                    headers=headers,
                    json=data
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result") == "success":
                    return result.get("arguments")
                else:
                    logger.error(f"Transmission请求失败: {result.get('result')}")
                    return None
            else:
                logger.error(f"Transmission请求失败: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Transmission请求异常: {e}")
            return None
    
    async def add_torrent(self, torrent: str, download_dir: Optional[str] = None) -> Optional[int]:
        """添加种子或磁力链接"""
        try:
            arguments = {"filename": torrent}
            if download_dir:
                arguments["download-dir"] = download_dir
            
            result = await self._request("torrent-add", arguments)
            if result and "torrent-added" in result:
                torrent_info = result["torrent-added"]
                return torrent_info.get("id")
            elif result and "torrent-duplicate" in result:
                torrent_info = result["torrent-duplicate"]
                return torrent_info.get("id")
            return None
        except Exception as e:
            logger.error(f"添加Transmission下载任务异常: {e}")
            return None
    
    async def get_torrents(self, ids: Optional[List[int]] = None) -> List[Dict]:
        """获取种子列表"""
        try:
            arguments = {
                "fields": [
                    "id", "name", "status", "percentDone", "totalSize", "downloadedEver",
                    "uploadedEver", "uploadRatio", "rateDownload", "rateUpload", "eta",
                    "addedDate", "doneDate", "downloadDir", "hashString", "labels"
                ]
            }
            if ids:
                arguments["ids"] = ids
            
            result = await self._request("torrent-get", arguments)
            if result:
                return result.get("torrents", [])
            return []
        except Exception as e:
            logger.error(f"获取Transmission种子列表异常: {e}")
            return []
    
    async def set_torrent_labels(self, ids: List[int], labels: List[str]) -> bool:
        """
        设置种子标签（使用labels字段）
        Transmission 4.0+ 支持labels字段
        """
        try:
            # labels字段是字符串数组
            result = await self._request("torrent-set", {
                "ids": ids,
                "labels": labels
            })
            return result is not None
        except Exception as e:
            logger.error(f"设置Transmission标签异常: {e}")
            return False
    
    async def get_torrent_labels(self, torrent_id: int) -> List[str]:
        """获取种子标签"""
        try:
            torrents = await self.get_torrents(ids=[torrent_id])
            if torrents:
                labels = torrents[0].get("labels", [])
                if isinstance(labels, list):
                    return labels
                elif isinstance(labels, str):
                    # 如果是字符串，按逗号分割
                    return [label.strip() for label in labels.split(",") if label.strip()]
            return []
        except Exception as e:
            logger.error(f"获取Transmission标签异常: {e}")
            return []
    
    async def remove_torrent_labels(self, ids: List[int], labels: List[str]) -> bool:
        """
        移除种子标签
        先获取现有标签，然后移除指定标签
        """
        try:
            # 获取所有种子的现有标签
            torrents = await self.get_torrents(ids=ids)
            if not torrents:
                return False
            
            # 为每个种子更新标签
            for torrent in torrents:
                current_labels = torrent.get("labels", [])
                if isinstance(current_labels, str):
                    current_labels = [label.strip() for label in current_labels.split(",") if label.strip()]
                
                # 移除指定标签
                new_labels = [label for label in current_labels if label not in labels]
                
                # 更新标签
                await self.set_torrent_labels([torrent["id"]], new_labels)
            
            return True
        except Exception as e:
            logger.error(f"移除Transmission标签异常: {e}")
            return False
    
    async def pause_torrent(self, ids: List[int]) -> bool:
        """暂停种子"""
        try:
            result = await self._request("torrent-stop", {"ids": ids})
            return result is not None
        except Exception as e:
            logger.error(f"暂停Transmission种子异常: {e}")
            return False
    
    async def resume_torrent(self, ids: List[int]) -> bool:
        """恢复种子"""
        try:
            result = await self._request("torrent-start", {"ids": ids})
            return result is not None
        except Exception as e:
            logger.error(f"恢复Transmission种子异常: {e}")
            return False
    
    async def remove_torrent(self, ids: List[int], delete_local_data: bool = False) -> bool:
        """删除种子"""
        try:
            result = await self._request("torrent-remove", {
                "ids": ids,
                "delete-local-data": delete_local_data
            })
            return result is not None
        except Exception as e:
            logger.error(f"删除Transmission种子异常: {e}")
            return False
    
    async def queue_move_up(self, ids: List[int]) -> bool:
        """队列上移"""
        try:
            result = await self._request("queue-move-up", {"ids": ids})
            return result is not None
        except Exception as e:
            logger.error(f"队列上移异常: {e}")
            return False
    
    async def queue_move_down(self, ids: List[int]) -> bool:
        """队列下移"""
        try:
            result = await self._request("queue-move-down", {"ids": ids})
            return result is not None
        except Exception as e:
            logger.error(f"队列下移异常: {e}")
            return False
    
    async def queue_move_top(self, ids: List[int]) -> bool:
        """队列置顶"""
        try:
            result = await self._request("queue-move-top", {"ids": ids})
            return result is not None
        except Exception as e:
            logger.error(f"队列置顶异常: {e}")
            return False
    
    async def queue_move_bottom(self, ids: List[int]) -> bool:
        """队列置底"""
        try:
            result = await self._request("queue-move-bottom", {"ids": ids})
            return result is not None
        except Exception as e:
            logger.error(f"队列置底异常: {e}")
            return False
    
    async def batch_pause(self, ids: List[int]) -> bool:
        """批量暂停"""
        try:
            result = await self._request("torrent-stop", {"ids": ids})
            return result is not None
        except Exception as e:
            logger.error(f"批量暂停异常: {e}")
            return False
    
    async def batch_resume(self, ids: List[int]) -> bool:
        """批量恢复"""
        try:
            result = await self._request("torrent-start", {"ids": ids})
            return result is not None
        except Exception as e:
            logger.error(f"批量恢复异常: {e}")
            return False
    
    async def batch_delete(self, ids: List[int], delete_files: bool = False) -> bool:
        """批量删除"""
        try:
            result = await self._request("torrent-remove", {
                "ids": ids,
                "delete-local-data": delete_files
            })
            return result is not None
        except Exception as e:
            logger.error(f"批量删除异常: {e}")
            return False
    
    async def set_global_speed_limit(
        self, 
        download_limit: Optional[float] = None, 
        upload_limit: Optional[float] = None
    ) -> bool:
        """
        设置全局速度限制
        
        Args:
            download_limit: 下载速度限制（MB/s），None表示不限制
            upload_limit: 上传速度限制（MB/s），None表示不限制
        
        Returns:
            是否设置成功
        """
        try:
            arguments = {}
            
            # Transmission API使用KB/s，需要转换
            # 0表示无限制
            if download_limit is not None:
                download_kbps = int(download_limit * 1024)  # MB/s -> KB/s
                arguments["speed-limit-down"] = download_kbps
                arguments["speed-limit-down-enabled"] = download_kbps > 0
            
            if upload_limit is not None:
                upload_kbps = int(upload_limit * 1024)  # MB/s -> KB/s
                arguments["speed-limit-up"] = upload_kbps
                arguments["speed-limit-up-enabled"] = upload_kbps > 0
            
            if arguments:
                result = await self._request("session-set", arguments)
                if result:
                    logger.info(f"全局速度限制设置成功: 下载={download_limit}MB/s, 上传={upload_limit}MB/s")
                    return True
                else:
                    logger.error("设置全局速度限制失败")
                    return False
            return True
        except Exception as e:
            logger.error(f"设置全局速度限制异常: {e}")
            return False
    
    async def get_global_speed_limit(self) -> Optional[Dict[str, float]]:
        """
        获取全局速度限制
        
        Returns:
            包含download_limit和upload_limit的字典（MB/s），None表示无限制
        """
        try:
            result = await self._request("session-get", {
                "fields": ["speed-limit-down", "speed-limit-down-enabled", 
                          "speed-limit-up", "speed-limit-up-enabled"]
            })
            if result:
                # Transmission返回的是KB/s，需要转换为MB/s
                download_kbps = result.get("speed-limit-down", 0)
                download_enabled = result.get("speed-limit-down-enabled", False)
                upload_kbps = result.get("speed-limit-up", 0)
                upload_enabled = result.get("speed-limit-up-enabled", False)
                
                return {
                    "download_limit": (download_kbps / 1024) if download_enabled and download_kbps > 0 else None,
                    "upload_limit": (upload_kbps / 1024) if upload_enabled and upload_kbps > 0 else None
                }
            return None
        except Exception as e:
            logger.error(f"获取全局速度限制异常: {e}")
            return None
    
    async def set_torrent_speed_limit(
        self, 
        torrent_id: int, 
        download_limit: Optional[float] = None, 
        upload_limit: Optional[float] = None
    ) -> bool:
        """
        设置单个种子的速度限制
        
        Args:
            torrent_id: 种子ID
            download_limit: 下载速度限制（MB/s），None表示不限制
            upload_limit: 上传速度限制（MB/s），None表示不限制
        
        Returns:
            是否设置成功
        """
        try:
            arguments = {"ids": [torrent_id]}
            
            # Transmission API使用KB/s，需要转换
            # -1表示无限制
            if download_limit is not None:
                download_kbps = int(download_limit * 1024) if download_limit > 0 else -1
                arguments["downloadLimit"] = download_kbps
            
            if upload_limit is not None:
                upload_kbps = int(upload_limit * 1024) if upload_limit > 0 else -1
                arguments["uploadLimit"] = upload_kbps
            
            result = await self._request("torrent-set", arguments)
            if result:
                logger.info(f"种子速度限制设置成功: id={torrent_id}, 下载={download_limit}MB/s, 上传={upload_limit}MB/s")
                return True
            else:
                logger.error(f"设置种子速度限制失败: id={torrent_id}")
                return False
        except Exception as e:
            logger.error(f"设置种子速度限制异常: {e}")
            return False
    
    async def close(self):
        """关闭客户端"""
        await self.session.aclose()

