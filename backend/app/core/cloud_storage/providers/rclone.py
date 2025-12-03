"""
RClone存储提供商
通过RClone命令行工具操作云存储
"""

import json
import subprocess
import os
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from loguru import logger

from app.core.cloud_storage.providers.base import (
    CloudStorageProvider,
    CloudFileInfo,
    CloudStorageUsage
)


class RCloneProvider(CloudStorageProvider):
    """RClone存储提供商"""
    
    # 支持的传输类型
    transtype = {
        "copy": "复制",
        "move": "移动",
        "sync": "同步"
    }
    
    def __init__(self):
        self.remote_name: Optional[str] = None
        self.config_path: Optional[str] = None
        self._config: Optional[Dict[str, Any]] = None
        self._check_rclone()
    
    def _check_rclone(self) -> bool:
        """检查RClone是否可用"""
        try:
            result = subprocess.run(
                ['rclone', 'version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info("RClone已安装")
                return True
            else:
                logger.warning("RClone未安装或不可用")
                return False
        except FileNotFoundError:
            logger.warning("RClone未安装，请先安装RClone: https://rclone.org/install/")
            return False
        except Exception as e:
            logger.error(f"检查RClone失败: {e}")
            return False
    
    def _get_hidden_shell(self):
        """获取隐藏shell配置（Windows）"""
        if os.name == 'nt':  # Windows
            st = subprocess.STARTUPINFO()
            st.dwFlags = subprocess.STARTF_USESHOWWINDOW
            st.wShowWindow = subprocess.SW_HIDE
            return st
        return None
    
    async def initialize(self, credentials: Dict[str, Any]) -> bool:
        """初始化RClone提供商"""
        try:
            self.remote_name = credentials.get("remote_name", "VabHub")
            self.config_path = credentials.get("config_path")
            self._config = credentials
            
            if not self.config_path:
                # 使用默认配置路径
                if os.name == 'nt':  # Windows
                    self.config_path = os.path.expanduser("~/.config/rclone/rclone.conf")
                else:  # Linux/Mac
                    self.config_path = os.path.expanduser("~/.config/rclone/rclone.conf")
            
            # 检查配置文件是否存在
            if not Path(self.config_path).exists():
                logger.error(f"RClone配置文件不存在: {self.config_path}")
                return False
            
            # 检查远程配置是否存在
            if not await self._check_remote():
                logger.error(f"RClone远程配置 '{self.remote_name}' 不存在")
                return False
            
            logger.info(f"RClone提供商初始化成功 (远程: {self.remote_name})")
            return True
        except Exception as e:
            logger.error(f"RClone提供商初始化失败: {e}")
            return False
    
    def get_config(self) -> Optional[Dict[str, Any]]:
        """获取配置"""
        return self._config
    
    def set_config(self, conf: Dict[str, Any]):
        """设置配置"""
        self._config = conf
        if "remote_name" in conf:
            self.remote_name = conf["remote_name"]
        if "config_path" in conf:
            self.config_path = conf["config_path"]
    
    async def check(self) -> bool:
        """检查RClone是否可用"""
        return self._check_rclone() and await self._check_remote()
    
    async def _check_remote(self) -> bool:
        """检查远程配置"""
        try:
            result = subprocess.run(
                ['rclone', 'listremotes'],
                capture_output=True,
                text=True,
                timeout=10,
                startupinfo=self._get_hidden_shell()
            )
            
            if result.returncode == 0:
                remotes = result.stdout.strip().split('\n')
                # 移除冒号
                remotes = [r.rstrip(':') for r in remotes if r.strip()]
                return self.remote_name in remotes
            return False
        except Exception as e:
            logger.error(f"检查RClone远程配置失败: {e}")
            return False
    
    async def is_authenticated(self) -> bool:
        """检查是否已认证（RClone通过配置文件认证）"""
        return await self._check_remote()
    
    async def list_files(self, path: str = "/", recursive: bool = False) -> List[CloudFileInfo]:
        """列出文件"""
        try:
            if not await self.is_authenticated():
                return []
            
            remote_path = f"{self.remote_name}:{path}"
            
            # 构建命令
            cmd = ['rclone', 'lsjson', remote_path]
            if recursive:
                cmd.append('--recursive')
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                startupinfo=self._get_hidden_shell()
            )
            
            if result.returncode != 0:
                logger.error(f"RClone列出文件失败: {result.stderr}")
                return []
            
            items = json.loads(result.stdout)
            files = []
            
            for item in items:
                file_path = f"{path.rstrip('/')}/{item['Name']}" if path != "/" else f"/{item['Name']}"
                if item.get("IsDir"):
                    file_path += "/"
                
                # 解析修改时间
                modified_at = None
                if item.get("ModTime"):
                    try:
                        # RClone返回的时间格式: "2024-01-01T00:00:00Z"
                        modified_at = datetime.fromisoformat(item["ModTime"].replace('Z', '+00:00'))
                    except:
                        pass
                
                files.append(CloudFileInfo(
                    id=item.get("Path", file_path),
                    name=item["Name"],
                    path=file_path,
                    size=item.get("Size", 0) if not item.get("IsDir") else 0,
                    type="dir" if item.get("IsDir") else "file",
                    modified_at=modified_at,
                    metadata={
                        "mime_type": item.get("MimeType"),
                        "hash": item.get("Hash")
                    }
                ))
            
            return files
        except Exception as e:
            logger.error(f"RClone列出文件失败: {e}")
            return []
    
    async def get_file_info(self, file_id: str) -> Optional[CloudFileInfo]:
        """获取文件信息"""
        try:
            # file_id 在RClone中就是路径
            remote_path = f"{self.remote_name}:{file_id}"
            
            result = subprocess.run(
                ['rclone', 'lsjson', remote_path],
                capture_output=True,
                text=True,
                timeout=10,
                startupinfo=self._get_hidden_shell()
            )
            
            if result.returncode != 0:
                return None
            
            items = json.loads(result.stdout)
            if not items:
                return None
            
            item = items[0]
            
            # 解析修改时间
            modified_at = None
            if item.get("ModTime"):
                try:
                    modified_at = datetime.fromisoformat(item["ModTime"].replace('Z', '+00:00'))
                except:
                    pass
            
            return CloudFileInfo(
                id=item.get("Path", file_id),
                name=item["Name"],
                path=file_id,
                size=item.get("Size", 0) if not item.get("IsDir") else 0,
                type="dir" if item.get("IsDir") else "file",
                modified_at=modified_at,
                metadata={
                    "mime_type": item.get("MimeType"),
                    "hash": item.get("Hash")
                }
            )
        except Exception as e:
            logger.error(f"RClone获取文件信息失败: {e}")
            return None
    
    async def create_folder(self, parent_path: str, name: str) -> Optional[CloudFileInfo]:
        """创建文件夹"""
        try:
            if not await self.is_authenticated():
                return None
            
            folder_path = f"{parent_path.rstrip('/')}/{name}"
            remote_path = f"{self.remote_name}:{folder_path}"
            
            result = subprocess.run(
                ['rclone', 'mkdir', remote_path],
                capture_output=True,
                text=True,
                timeout=10,
                startupinfo=self._get_hidden_shell()
            )
            
            if result.returncode != 0:
                logger.error(f"RClone创建文件夹失败: {result.stderr}")
                return None
            
            # 获取创建的文件夹信息
            return await self.get_file_info(folder_path)
        except Exception as e:
            logger.error(f"RClone创建文件夹失败: {e}")
            return None
    
    async def delete_file(self, file_id: str) -> bool:
        """删除文件"""
        try:
            if not await self.is_authenticated():
                return False
            
            remote_path = f"{self.remote_name}:{file_id}"
            
            result = subprocess.run(
                ['rclone', 'deletefile', remote_path],
                capture_output=True,
                text=True,
                timeout=30,
                startupinfo=self._get_hidden_shell()
            )
            
            return result.returncode == 0
        except Exception as e:
            logger.error(f"RClone删除文件失败: {e}")
            return False
    
    async def upload_file(self, local_path: str, remote_path: str, progress_callback: Optional[callable] = None) -> bool:
        """上传文件"""
        try:
            if not await self.is_authenticated():
                return False
            
            if not Path(local_path).exists():
                logger.error(f"本地文件不存在: {local_path}")
                return False
            
            target_path = f"{self.remote_name}:{remote_path}"
            
            # 构建命令
            cmd = ['rclone', 'copyto', local_path, target_path, '--progress']
            
            # 执行命令并监控进度
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                startupinfo=self._get_hidden_shell()
            )
            
            # 解析进度输出
            for line in process.stdout:
                if progress_callback and '%' in line:
                    # 解析进度百分比
                    try:
                        # RClone进度格式: "Transferred: 1.234M / 5.678M, 22%, 1.234MB/s, ETA 2m3s"
                        parts = line.split('%')
                        if parts:
                            percent_str = parts[0].split()[-1]
                            progress = float(percent_str)
                            progress_callback(progress)
                    except:
                        pass
            
            process.wait()
            return process.returncode == 0
        except Exception as e:
            logger.error(f"RClone上传文件失败: {e}")
            return False
    
    async def download_file(self, file_id: str, save_path: str, progress_callback: Optional[callable] = None) -> bool:
        """下载文件"""
        try:
            if not await self.is_authenticated():
                return False
            
            remote_path = f"{self.remote_name}:{file_id}"
            
            # 确保保存目录存在
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 构建命令
            cmd = ['rclone', 'copyto', remote_path, save_path, '--progress']
            
            # 执行命令并监控进度
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                startupinfo=self._get_hidden_shell()
            )
            
            # 解析进度输出
            for line in process.stdout:
                if progress_callback and '%' in line:
                    # 解析进度百分比
                    try:
                        parts = line.split('%')
                        if parts:
                            percent_str = parts[0].split()[-1]
                            progress = float(percent_str)
                            progress_callback(progress)
                    except:
                        pass
            
            process.wait()
            return process.returncode == 0
        except Exception as e:
            logger.error(f"RClone下载文件失败: {e}")
            return False
    
    async def get_storage_usage(self) -> Optional[CloudStorageUsage]:
        """获取存储使用情况"""
        try:
            if not await self.is_authenticated():
                return None
            
            remote_path = f"{self.remote_name}:/"
            
            result = subprocess.run(
                ['rclone', 'about', remote_path, '--json'],
                capture_output=True,
                text=True,
                timeout=10,
                startupinfo=self._get_hidden_shell()
            )
            
            if result.returncode != 0:
                return None
            
            data = json.loads(result.stdout)
            
            total = data.get("Total", {}).get("bytes", 0)
            used = data.get("Used", {}).get("bytes", 0)
            available = data.get("Free", {}).get("bytes", 0)
            
            percentage = (used / total * 100) if total > 0 else 0.0
            
            return CloudStorageUsage(
                total=total,
                used=used,
                available=available,
                percentage=percentage
            )
        except Exception as e:
            logger.error(f"RClone获取存储使用情况失败: {e}")
            return None

