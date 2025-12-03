"""
系统更新管理器
支持自动更新和热更新功能
支持Docker和源代码两种部署方式的更新
参考MoviePilot的实现
"""

import subprocess
import asyncio
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
from loguru import logger

from app.core.config import settings


class UpdateMode(str, Enum):
    """更新模式"""
    NEVER = "never"  # 从不更新
    RELEASE = "release"  # 仅更新到发行版本
    DEV = "dev"  # 更新到开发版本（包括release）


class DeploymentType(str, Enum):
    """部署类型"""
    DOCKER = "docker"  # Docker容器部署
    SOURCE = "source"  # 源代码部署
    UNKNOWN = "unknown"  # 未知部署方式


class UpdateManager:
    """系统更新管理器"""
    
    def __init__(self, repo_path: Optional[Path] = None):
        """
        初始化更新管理器
        
        Args:
            repo_path: Git仓库路径（默认使用当前工作目录）
        """
        if repo_path is None:
            # 默认使用项目根目录
            repo_path = Path(__file__).parent.parent.parent.parent.parent
        
        self.repo_path = Path(repo_path)
        self.update_mode = UpdateMode.NEVER
        self.auto_update_enabled = False
        
        # 检测部署方式
        self.deployment_type = self._detect_deployment_type()
        logger.info(f"检测到部署方式: {self.deployment_type.value}")
        
    def _detect_deployment_type(self) -> DeploymentType:
        """
        检测部署方式
        
        Returns:
            部署类型
        """
        # 方法1: 检查是否在Docker容器中
        if Path("/.dockerenv").exists():
            return DeploymentType.DOCKER
        
        # 方法2: 检查环境变量
        if os.getenv("DOCKER_CONTAINER") == "true" or os.getenv("container") == "docker":
            return DeploymentType.DOCKER
        
        # 方法3: 检查cgroup（Linux）
        try:
            with open("/proc/self/cgroup", "r") as f:
                content = f.read()
                if "docker" in content or "/docker/" in content:
                    return DeploymentType.DOCKER
        except (FileNotFoundError, PermissionError):
            pass
        
        # 方法4: 检查是否是Git仓库（源代码部署）
        if (self.repo_path / ".git").exists():
            return DeploymentType.SOURCE
        
        # 默认返回未知
        return DeploymentType.UNKNOWN
    
    async def check_update_available(self) -> Dict[str, Any]:
        """
        检查是否有可用更新
        
        Returns:
            更新信息字典
        """
        try:
            # 根据部署方式选择检查方法
            if self.deployment_type == DeploymentType.DOCKER:
                return await self._check_docker_update()
            elif self.deployment_type == DeploymentType.SOURCE:
                return await self._check_git_update()
            else:
                return {
                    "has_update": False,
                    "error": "无法检测部署方式，无法检查更新",
                    "deployment_type": self.deployment_type.value
                }
        except Exception as e:
            logger.error(f"检查更新失败: {e}")
            return {
                "has_update": False,
                "error": str(e),
                "deployment_type": self.deployment_type.value
            }
    
    async def _check_git_update(self) -> Dict[str, Any]:
        """检查Git更新（源代码部署）"""
        # 获取当前版本
        current_version = await self._get_current_version()
        
        # 获取远程版本信息
        remote_info = await self._get_remote_version_info()
        
        # 比较版本
        has_update = False
        if remote_info:
            if self.update_mode == UpdateMode.RELEASE:
                # 仅检查发行版本
                has_update = remote_info.get("latest_release") != current_version
            elif self.update_mode == UpdateMode.DEV:
                # 检查开发版本（包括release）
                latest_commit = remote_info.get("latest_commit")
                current_commit = await self._get_current_commit()
                has_update = latest_commit != current_commit
        
        return {
            "has_update": has_update,
            "current_version": current_version,
            "current_commit": await self._get_current_commit(),
            "remote_info": remote_info,
            "update_mode": self.update_mode.value,
            "deployment_type": "source"
        }
    
    async def _check_docker_update(self) -> Dict[str, Any]:
        """检查Docker镜像更新"""
        try:
            # 获取容器名称和镜像信息
            container_name = os.getenv("CONTAINER_NAME", "vabhub-backend")
            image_name = await self._get_docker_image_name(container_name)
            
            if not image_name:
                return {
                    "has_update": False,
                    "error": "无法获取Docker镜像信息",
                    "deployment_type": "docker"
                }
            
            # 拉取最新镜像信息（不下载）
            logger.info(f"检查Docker镜像更新: {image_name}")
            
            # 获取当前镜像ID
            current_image_id = await self._get_docker_image_id(container_name)
            
            # 拉取最新镜像（dry-run模式，实际会下载）
            pull_result = await asyncio.create_subprocess_exec(
                "docker", "pull", image_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await pull_result.wait()
            
            if pull_result.returncode != 0:
                stderr = (await pull_result.stderr.read()).decode()
                logger.warning(f"Docker pull失败: {stderr}")
                return {
                    "has_update": False,
                    "error": f"无法拉取镜像信息: {stderr}",
                    "deployment_type": "docker"
                }
            
            # 获取新镜像ID
            new_image_id = await self._get_docker_image_id(container_name)
            
            has_update = current_image_id != new_image_id
            
            return {
                "has_update": has_update,
                "current_image": image_name,
                "current_image_id": current_image_id,
                "new_image_id": new_image_id if has_update else current_image_id,
                "container_name": container_name,
                "deployment_type": "docker"
            }
        except Exception as e:
            logger.error(f"检查Docker更新失败: {e}")
            return {
                "has_update": False,
                "error": str(e),
                "deployment_type": "docker"
            }
    
    async def update_system(self, mode: Optional[str] = None) -> Dict[str, Any]:
        """
        更新系统
        
        Args:
            mode: 更新模式（可选，默认使用配置的模式）
        
        Returns:
            更新结果字典
        """
        if mode:
            self.update_mode = UpdateMode(mode)
        
        if self.update_mode == UpdateMode.NEVER:
            return {
                "success": False,
                "message": "更新模式为never，跳过更新"
            }
        
        try:
            # 根据部署方式选择更新方法
            if self.deployment_type == DeploymentType.DOCKER:
                return await self._update_docker_system()
            elif self.deployment_type == DeploymentType.SOURCE:
                return await self._update_source_system()
            else:
                return {
                    "success": False,
                    "message": "无法检测部署方式，无法执行更新",
                    "deployment_type": self.deployment_type.value
                }
        except Exception as e:
            logger.error(f"系统更新失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"更新失败: {str(e)}",
                "error": str(e)
            }
    
    async def _update_source_system(self) -> Dict[str, Any]:
        """更新源代码系统（Git）"""
        # 1. 检查Git仓库
        if not await self._is_git_repo():
            return {
                "success": False,
                "message": "当前目录不是Git仓库，无法自动更新"
            }
        
        # 2. 获取远程更新
        await self._fetch_remote()
        
        # 3. 检查是否有更新
        update_info = await self._check_git_update()
        if not update_info.get("has_update"):
            return {
                "success": True,
                "message": "已是最新版本，无需更新",
                "current_version": update_info.get("current_version")
            }
        
        # 4. 执行更新
        if self.update_mode == UpdateMode.RELEASE:
            # 更新到最新发行版本
            result = await self._update_to_release()
        elif self.update_mode == UpdateMode.DEV:
            # 更新到最新开发版本
            result = await self._update_to_dev()
        else:
            return {
                "success": False,
                "message": f"未知的更新模式: {self.update_mode}"
            }
        
        # 5. 记录更新历史
        await self._record_update_history(result)
        
        return result
    
    async def _update_docker_system(self) -> Dict[str, Any]:
        """更新Docker系统"""
        try:
            container_name = os.getenv("CONTAINER_NAME", "vabhub-backend")
            image_name = await self._get_docker_image_name(container_name)
            
            if not image_name:
                return {
                    "success": False,
                    "message": "无法获取Docker镜像信息"
                }
            
            # 检查是否有更新
            update_info = await self._check_docker_update()
            if not update_info.get("has_update"):
                return {
                    "success": True,
                    "message": "Docker镜像已是最新版本，无需更新",
                    "current_image": update_info.get("current_image")
                }
            
            # 拉取新镜像
            logger.info(f"拉取Docker镜像: {image_name}")
            pull_result = await asyncio.create_subprocess_exec(
                "docker", "pull", image_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await pull_result.wait()
            
            if pull_result.returncode != 0:
                stderr = (await pull_result.stderr.read()).decode()
                return {
                    "success": False,
                    "message": f"拉取Docker镜像失败: {stderr}"
                }
            
            # 重启容器
            logger.info(f"重启Docker容器: {container_name}")
            restart_result = await asyncio.create_subprocess_exec(
                "docker", "restart", container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await restart_result.wait()
            
            if restart_result.returncode != 0:
                stderr = (await restart_result.stderr.read()).decode()
                return {
                    "success": False,
                    "message": f"重启Docker容器失败: {stderr}"
                }
            
            result = {
                "success": True,
                "message": f"Docker镜像更新成功，容器 {container_name} 已重启",
                "image": image_name,
                "container": container_name,
                "requires_restart": False  # Docker容器已自动重启
            }
            
            # 记录更新历史
            await self._record_update_history(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Docker系统更新失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Docker更新失败: {str(e)}",
                "error": str(e)
            }
    
    async def _get_docker_image_name(self, container_name: str) -> Optional[str]:
        """获取Docker镜像名称"""
        try:
            # 方法1: 从环境变量获取
            image_name = os.getenv("IMAGE_NAME")
            if image_name:
                return image_name
            
            # 方法2: 从docker inspect获取
            result = await asyncio.create_subprocess_exec(
                "docker", "inspect", "-f", "{{.Config.Image}}", container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            
            if result.returncode == 0:
                image_name = stdout.decode().strip()
                if image_name:
                    return image_name
            
            # 方法3: 从docker-compose.yml推断（如果存在）
            # 这里可以添加从docker-compose.yml读取的逻辑
            
            return None
        except Exception as e:
            logger.error(f"获取Docker镜像名称失败: {e}")
            return None
    
    async def _get_docker_image_id(self, container_name: str) -> Optional[str]:
        """获取Docker镜像ID"""
        try:
            result = await asyncio.create_subprocess_exec(
                "docker", "inspect", "-f", "{{.Image}}", container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            
            if result.returncode == 0:
                image_id = stdout.decode().strip()
                return image_id
            
            return None
        except Exception as e:
            logger.error(f"获取Docker镜像ID失败: {e}")
            return None
    
    async def hot_reload_modules(self, modules: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        热重载模块（无需重启）
        
        Args:
            modules: 要重载的模块列表（None表示重载所有可重载模块）
        
        Returns:
            重载结果字典
        """
        reloaded_modules = []
        failed_modules = []
        
        try:
            # 可热重载的模块列表
            reloadable_modules = [
                "category_helper",  # 分类配置
                "settings",  # 系统设置
                "plugins",  # 插件
            ]
            
            if modules:
                reloadable_modules = [m for m in modules if m in reloadable_modules]
            
            for module_name in reloadable_modules:
                try:
                    # 使用importlib重新加载模块
                    import importlib
                    import sys
                    
                    # 查找模块
                    module_key = None
                    for key in sys.modules.keys():
                        if module_name in key:
                            module_key = key
                            break
                    
                    if module_key:
                        module = sys.modules[module_key]
                        importlib.reload(module)
                        reloaded_modules.append(module_name)
                        logger.info(f"模块 {module_name} 热重载成功")
                    else:
                        failed_modules.append({
                            "module": module_name,
                            "error": "模块未加载"
                        })
                        
                except Exception as e:
                    logger.error(f"热重载模块 {module_name} 失败: {e}")
                    failed_modules.append({
                        "module": module_name,
                        "error": str(e)
                    })
            
            return {
                "success": len(failed_modules) == 0,
                "reloaded_modules": reloaded_modules,
                "failed_modules": failed_modules,
                "message": f"热重载完成: 成功 {len(reloaded_modules)}, 失败 {len(failed_modules)}"
            }
            
        except Exception as e:
            logger.error(f"热重载失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"热重载失败: {str(e)}",
                "error": str(e)
            }
    
    async def _is_git_repo(self) -> bool:
        """检查是否是Git仓库"""
        try:
            result = await asyncio.create_subprocess_exec(
                "git", "rev-parse", "--git-dir",
                cwd=str(self.repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.wait()
            return result.returncode == 0
        except Exception as e:
            logger.error(f"检查Git仓库失败: {e}")
            return False
    
    async def _get_current_version(self) -> str:
        """获取当前版本"""
        try:
            # 尝试获取Git标签
            result = await asyncio.create_subprocess_exec(
                "git", "describe", "--tags", "--always",
                cwd=str(self.repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            if result.returncode == 0:
                return stdout.decode().strip()
            
            # 如果没有标签，使用commit hash
            commit = await self._get_current_commit()
            return commit[:8] if commit else "unknown"
        except Exception as e:
            logger.error(f"获取当前版本失败: {e}")
            return "unknown"
    
    async def _get_current_commit(self) -> str:
        """获取当前commit hash"""
        try:
            result = await asyncio.create_subprocess_exec(
                "git", "rev-parse", "HEAD",
                cwd=str(self.repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            if result.returncode == 0:
                return stdout.decode().strip()
            return "unknown"
        except Exception as e:
            logger.error(f"获取当前commit失败: {e}")
            return "unknown"
    
    async def _get_remote_version_info(self) -> Optional[Dict[str, Any]]:
        """获取远程版本信息"""
        try:
            # 获取远程分支信息
            result = await asyncio.create_subprocess_exec(
                "git", "ls-remote", "--heads", "origin",
                cwd=str(self.repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            
            if result.returncode != 0:
                return None
            
            # 获取最新标签
            tag_result = await asyncio.create_subprocess_exec(
                "git", "ls-remote", "--tags", "origin",
                cwd=str(self.repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            tag_stdout, _ = await tag_result.communicate()
            
            # 解析结果
            latest_commit = None
            latest_release = None
            
            if stdout:
                lines = stdout.decode().strip().split('\n')
                if lines:
                    latest_commit = lines[0].split()[0] if lines[0] else None
            
            if tag_stdout:
                tag_lines = tag_stdout.decode().strip().split('\n')
                if tag_lines:
                    # 获取最新的标签
                    tags = [line.split()[1].replace('refs/tags/', '') for line in tag_lines if line]
                    if tags:
                        latest_release = tags[-1]
            
            return {
                "latest_commit": latest_commit,
                "latest_release": latest_release
            }
        except Exception as e:
            logger.error(f"获取远程版本信息失败: {e}")
            return None
    
    async def _fetch_remote(self):
        """获取远程更新（使用代理）"""
        try:
            # 使用代理（如果配置了）
            from app.utils.http_client import get_proxy_config
            proxy_config = get_proxy_config()
            
            # 设置Git代理环境变量
            env = os.environ.copy()
            if proxy_config:
                # 解析代理URL
                from urllib.parse import urlparse
                parsed = urlparse(proxy_config)
                if parsed.scheme in ['http', 'https']:
                    # HTTP代理
                    env['HTTP_PROXY'] = proxy_config
                    env['HTTPS_PROXY'] = proxy_config
                    logger.info(f"Git fetch使用代理: {proxy_config}")
                elif parsed.scheme == 'socks5':
                    # SOCKS5代理（Git需要socks5://格式）
                    env['ALL_PROXY'] = proxy_config
                    logger.info(f"Git fetch使用SOCKS5代理: {proxy_config}")
            
            result = await asyncio.create_subprocess_exec(
                "git", "fetch", "origin",
                cwd=str(self.repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            await result.wait()
            if result.returncode != 0:
                stderr = (await result.stderr.read()).decode()
                raise Exception(f"Git fetch失败: {stderr}")
        except Exception as e:
            logger.error(f"获取远程更新失败: {e}")
            raise
    
    async def _update_to_release(self) -> Dict[str, Any]:
        """更新到最新发行版本"""
        try:
            # 获取最新标签
            result = await asyncio.create_subprocess_exec(
                "git", "describe", "--tags", "--abbrev=0", "origin/main",
                cwd=str(self.repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            
            if result.returncode != 0:
                # 如果没有标签，更新到main分支
                return await self._update_to_branch("main")
            
            latest_tag = stdout.decode().strip()
            
            # 切换到最新标签
            checkout_result = await asyncio.create_subprocess_exec(
                "git", "checkout", latest_tag,
                cwd=str(self.repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await checkout_result.wait()
            
            if checkout_result.returncode != 0:
                stderr = (await checkout_result.stderr.read()).decode()
                raise Exception(f"Git checkout失败: {stderr}")
            
            return {
                "success": True,
                "message": f"已更新到发行版本: {latest_tag}",
                "version": latest_tag,
                "commit": await self._get_current_commit()
            }
        except Exception as e:
            logger.error(f"更新到发行版本失败: {e}")
            raise
    
    async def _update_to_dev(self) -> Dict[str, Any]:
        """更新到最新开发版本"""
        return await self._update_to_branch("main")
    
    async def _update_to_branch(self, branch: str) -> Dict[str, Any]:
        """更新到指定分支（使用代理）"""
        try:
            # 使用代理（如果配置了）
            from app.utils.http_client import get_proxy_config
            proxy_config = get_proxy_config()
            
            # 设置Git代理环境变量
            env = os.environ.copy()
            if proxy_config:
                from urllib.parse import urlparse
                parsed = urlparse(proxy_config)
                if parsed.scheme in ['http', 'https']:
                    env['HTTP_PROXY'] = proxy_config
                    env['HTTPS_PROXY'] = proxy_config
                elif parsed.scheme == 'socks5':
                    env['ALL_PROXY'] = proxy_config
            
            # 切换到指定分支
            checkout_result = await asyncio.create_subprocess_exec(
                "git", "checkout", branch,
                cwd=str(self.repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            await checkout_result.wait()
            
            if checkout_result.returncode != 0:
                stderr = (await checkout_result.stderr.read()).decode()
                raise Exception(f"Git checkout失败: {stderr}")
            
            # 拉取最新代码
            pull_result = await asyncio.create_subprocess_exec(
                "git", "pull", "origin", branch,
                cwd=str(self.repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            await pull_result.wait()
            
            if pull_result.returncode != 0:
                stderr = (await pull_result.stderr.read()).decode()
                raise Exception(f"Git pull失败: {stderr}")
            
            return {
                "success": True,
                "message": f"已更新到 {branch} 分支",
                "branch": branch,
                "commit": await self._get_current_commit()
            }
        except Exception as e:
            logger.error(f"更新到分支 {branch} 失败: {e}")
            raise
    
    async def _record_update_history(self, update_result: Dict[str, Any]):
        """记录更新历史"""
        try:
            # 这里可以将更新历史保存到数据库
            # 暂时只记录日志
            logger.info(f"系统更新完成: {update_result}")
        except Exception as e:
            logger.error(f"记录更新历史失败: {e}")

