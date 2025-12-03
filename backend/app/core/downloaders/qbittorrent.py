"""
qBittorrent下载器集成
"""
import httpx
from typing import Optional, Dict, List
from loguru import logger


class QBittorrentClient:
    """qBittorrent客户端"""
    
    def __init__(self, host: str = "localhost", port: int = 8080, username: str = "", password: str = ""):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.base_url = f"http://{host}:{port}"
        self.session = httpx.AsyncClient(timeout=30.0)
        self.sid = None
    
    async def login(self) -> bool:
        """登录qBittorrent"""
        try:
            response = await self.session.post(
                f"{self.base_url}/api/v2/auth/login",
                data={
                    "username": self.username or "admin",
                    "password": self.password or "adminadmin"
                }
            )
            if response.status_code == 200 and response.text == "Ok.":
                cookies = response.cookies
                self.sid = cookies.get("SID")
                logger.info("qBittorrent登录成功")
                return True
            else:
                logger.error(f"qBittorrent登录失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"qBittorrent登录异常: {e}")
            return False
    
    async def add_torrent(
        self, 
        torrent: str, 
        save_path: Optional[str] = None, 
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """添加种子或磁力链接"""
        try:
            # 确保已登录
            if not self.sid:
                await self.login()
            
            data = {"urls": torrent}
            if save_path:
                data["savepath"] = save_path
            if category:
                data["category"] = category
            if tags:
                # qBittorrent标签用逗号分隔
                data["tags"] = ",".join(tags)
            
            response = await self.session.post(
                f"{self.base_url}/api/v2/torrents/add",
                data=data
            )
            
            if response.status_code == 200:
                logger.info(f"添加下载任务成功: {torrent[:50]}...")
                return True
            else:
                logger.error(f"添加下载任务失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"添加下载任务异常: {e}")
            return False
    
    async def set_torrent_tags(self, hashes: str, tags: List[str]) -> bool:
        """设置种子标签"""
        try:
            if not self.sid:
                await self.login()
            
            # qBittorrent标签用逗号分隔
            tags_str = ",".join(tags)
            
            response = await self.session.post(
                f"{self.base_url}/api/v2/torrents/addTags",
                data={
                    "hashes": hashes,
                    "tags": tags_str
                }
            )
            
            if response.status_code == 200:
                logger.info(f"设置种子标签成功: {hashes}")
                return True
            else:
                logger.error(f"设置种子标签失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"设置种子标签异常: {e}")
            return False
    
    async def remove_torrent_tags(self, hashes: str, tags: List[str]) -> bool:
        """移除种子标签"""
        try:
            if not self.sid:
                await self.login()
            
            tags_str = ",".join(tags)
            
            response = await self.session.post(
                f"{self.base_url}/api/v2/torrents/removeTags",
                data={
                    "hashes": hashes,
                    "tags": tags_str
                }
            )
            
            if response.status_code == 200:
                logger.info(f"移除种子标签成功: {hashes}")
                return True
            else:
                logger.error(f"移除种子标签失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"移除种子标签异常: {e}")
            return False
    
    async def get_torrents(
        self, 
        status_filter: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict]:
        """获取种子列表"""
        try:
            if not self.sid:
                await self.login()
            
            params = {}
            if status_filter:
                params["filter"] = status_filter
            if tags:
                # qBittorrent标签过滤：使用标签名称，多个标签用逗号分隔
                params["tag"] = ",".join(tags)
            
            response = await self.session.get(
                f"{self.base_url}/api/v2/torrents/info",
                params=params
            )
            
            if response.status_code == 200:
                torrents = response.json()
                
                # 如果指定了标签，进一步过滤（qBittorrent的tag参数可能不够精确）
                if tags:
                    filtered_torrents = []
                    for torrent in torrents:
                        torrent_tags = [tag.strip() for tag in torrent.get("tags", "").split(",") if tag.strip()]
                        # 检查是否包含所有指定的标签
                        if set(tags).issubset(set(torrent_tags)):
                            filtered_torrents.append(torrent)
                    return filtered_torrents
                
                return torrents
            else:
                logger.error(f"获取种子列表失败: {response.text}")
                return []
        except Exception as e:
            logger.error(f"获取种子列表异常: {e}")
            return []
    
    async def get_completed_torrents(self, tags: Optional[List[str]] = None) -> List[Dict]:
        """获取已完成的种子（seeding状态）"""
        return await self.get_torrents(status_filter="seeding", tags=tags)
    
    async def get_downloading_torrents(self, tags: Optional[List[str]] = None) -> List[Dict]:
        """获取正在下载的种子"""
        return await self.get_torrents(status_filter="downloading", tags=tags)
    
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
            if not self.sid:
                await self.login()
            
            # qBittorrent API使用字节/秒，需要转换
            # 0表示无限制
            download_bytes = int(download_limit * 1024 * 1024) if download_limit else 0
            upload_bytes = int(upload_limit * 1024 * 1024) if upload_limit else 0
            
            # 设置下载速度限制
            if download_limit is not None:
                response = await self.session.post(
                    f"{self.base_url}/api/v2/transfer/setDownloadLimit",
                    data={"limit": download_bytes}
                )
                if response.status_code != 200:
                    logger.error(f"设置下载速度限制失败: {response.text}")
                    return False
            
            # 设置上传速度限制
            if upload_limit is not None:
                response = await self.session.post(
                    f"{self.base_url}/api/v2/transfer/setUploadLimit",
                    data={"limit": upload_bytes}
                )
                if response.status_code != 200:
                    logger.error(f"设置上传速度限制失败: {response.text}")
                    return False
            
            logger.info(f"全局速度限制设置成功: 下载={download_limit}MB/s, 上传={upload_limit}MB/s")
            return True
        except Exception as e:
            logger.error(f"设置全局速度限制异常: {e}")
            return False
    
    async def get_global_speed_limit(self) -> Optional[Dict[str, float]]:
        """
        获取全局速度限制
        
        Returns:
            包含download_limit和upload_limit的字典（MB/s），0表示无限制
        """
        try:
            if not self.sid:
                await self.login()
            
            response = await self.session.get(f"{self.base_url}/api/v2/transfer/info")
            if response.status_code == 200:
                info = response.json()
                # qBittorrent返回的是字节/秒，需要转换为MB/s
                download_limit = info.get("dl_rate_limit", 0) / (1024 * 1024)  # 转换为MB/s
                upload_limit = info.get("up_rate_limit", 0) / (1024 * 1024)  # 转换为MB/s
                
                return {
                    "download_limit": download_limit if download_limit > 0 else None,
                    "upload_limit": upload_limit if upload_limit > 0 else None
                }
            else:
                logger.error(f"获取全局速度限制失败: {response.text}")
                return None
        except Exception as e:
            logger.error(f"获取全局速度限制异常: {e}")
            return None
    
    async def set_torrent_speed_limit(
        self, 
        hash: str, 
        download_limit: Optional[float] = None, 
        upload_limit: Optional[float] = None
    ) -> bool:
        """
        设置单个种子的速度限制
        
        Args:
            hash: 种子hash
            download_limit: 下载速度限制（MB/s），None表示不限制
            upload_limit: 上传速度限制（MB/s），None表示不限制
        
        Returns:
            是否设置成功
        """
        try:
            if not self.sid:
                await self.login()
            
            # qBittorrent API使用字节/秒，需要转换
            # -1表示无限制
            download_bytes = int(download_limit * 1024 * 1024) if download_limit else -1
            upload_bytes = int(upload_limit * 1024 * 1024) if upload_limit else -1
            
            response = await self.session.post(
                f"{self.base_url}/api/v2/torrents/setDownloadLimit",
                data={"hashes": hash, "limit": download_bytes}
            )
            if response.status_code != 200:
                logger.error(f"设置种子下载速度限制失败: {response.text}")
                return False
            
            response = await self.session.post(
                f"{self.base_url}/api/v2/torrents/setUploadLimit",
                data={"hashes": hash, "limit": upload_bytes}
            )
            if response.status_code != 200:
                logger.error(f"设置种子上传速度限制失败: {response.text}")
                return False
            
            logger.info(f"种子速度限制设置成功: hash={hash}, 下载={download_limit}MB/s, 上传={upload_limit}MB/s")
            return True
        except Exception as e:
            logger.error(f"设置种子速度限制异常: {e}")
            return False
    
    async def pause_torrent(self, hash: str) -> bool:
        """暂停种子"""
        try:
            if not self.sid:
                await self.login()
            
            response = await self.session.post(
                f"{self.base_url}/api/v2/torrents/pause",
                data={"hashes": hash}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"暂停种子异常: {e}")
            return False
    
    async def resume_torrent(self, hash: str) -> bool:
        """恢复种子"""
        try:
            if not self.sid:
                await self.login()
            
            response = await self.session.post(
                f"{self.base_url}/api/v2/torrents/resume",
                data={"hashes": hash}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"恢复种子异常: {e}")
            return False
    
    async def delete_torrent(self, hash: str, delete_files: bool = False) -> bool:
        """删除种子"""
        try:
            if not self.sid:
                await self.login()
            
            url = f"{self.base_url}/api/v2/torrents/delete"
            if delete_files:
                url = f"{self.base_url}/api/v2/torrents/deletePermanent"
            
            response = await self.session.post(
                url,
                data={"hashes": hash}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"删除种子异常: {e}")
            return False
    
    async def get_torrent_properties(self, hash: str) -> Optional[Dict]:
        """获取种子属性"""
        try:
            if not self.sid:
                await self.login()
            
            response = await self.session.get(
                f"{self.base_url}/api/v2/torrents/properties",
                params={"hash": hash}
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"获取种子属性异常: {e}")
            return None
    
    async def increase_priority(self, hashes: str) -> bool:
        """提高队列优先级（上移）"""
        try:
            if not self.sid:
                await self.login()
            
            response = await self.session.post(
                f"{self.base_url}/api/v2/torrents/increasePrio",
                data={"hashes": hashes}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"提高优先级异常: {e}")
            return False
    
    async def decrease_priority(self, hashes: str) -> bool:
        """降低队列优先级（下移）"""
        try:
            if not self.sid:
                await self.login()
            
            response = await self.session.post(
                f"{self.base_url}/api/v2/torrents/decreasePrio",
                data={"hashes": hashes}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"降低优先级异常: {e}")
            return False
    
    async def top_priority(self, hashes: str) -> bool:
        """置顶（最高优先级）"""
        try:
            if not self.sid:
                await self.login()
            
            response = await self.session.post(
                f"{self.base_url}/api/v2/torrents/topPrio",
                data={"hashes": hashes}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"置顶异常: {e}")
            return False
    
    async def bottom_priority(self, hashes: str) -> bool:
        """置底（最低优先级）"""
        try:
            if not self.sid:
                await self.login()
            
            response = await self.session.post(
                f"{self.base_url}/api/v2/torrents/bottomPrio",
                data={"hashes": hashes}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"置底异常: {e}")
            return False
    
    async def batch_pause(self, hashes: List[str]) -> bool:
        """批量暂停"""
        try:
            if not self.sid:
                await self.login()
            
            hashes_str = "|".join(hashes)
            response = await self.session.post(
                f"{self.base_url}/api/v2/torrents/pause",
                data={"hashes": hashes_str}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"批量暂停异常: {e}")
            return False
    
    async def batch_resume(self, hashes: List[str]) -> bool:
        """批量恢复"""
        try:
            if not self.sid:
                await self.login()
            
            hashes_str = "|".join(hashes)
            response = await self.session.post(
                f"{self.base_url}/api/v2/torrents/resume",
                data={"hashes": hashes_str}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"批量恢复异常: {e}")
            return False
    
    async def batch_delete(self, hashes: List[str], delete_files: bool = False) -> bool:
        """批量删除"""
        try:
            if not self.sid:
                await self.login()
            
            hashes_str = "|".join(hashes)
            url = f"{self.base_url}/api/v2/torrents/delete"
            if delete_files:
                url = f"{self.base_url}/api/v2/torrents/deletePermanent"
            
            response = await self.session.post(
                url,
                data={"hashes": hashes_str}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"批量删除异常: {e}")
            return False
    
    async def close(self):
        """关闭客户端"""
        await self.session.aclose()

