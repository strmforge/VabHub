"""
VabHub 升级引擎服务
DEPLOY-UPGRADE-1 实现

提供版本检查和升级功能，通过 docker.sock 实现容器级升级。
"""

import os
import asyncio
from typing import Optional
from datetime import datetime
from pathlib import Path

import httpx
from loguru import logger
from pydantic import BaseModel


# ============== 数据模型 ==============

class VersionInfo(BaseModel):
    """版本信息"""
    current_version: str
    build_commit: Optional[str] = None
    update_available: bool = False
    latest_version: Optional[str] = None
    check_source: str = "ghcr"
    checked_at: Optional[datetime] = None


class UpgradeResult(BaseModel):
    """升级结果"""
    success: bool
    message: str
    action: str  # "check_only" | "apply" | "restart"
    details: Optional[dict] = None


# ============== 版本常量 ==============

# 版本信息文件路径
VERSION_FILE = Path("/app/VERSION")
# 版本环境变量
VERSION_ENV = "VABHUB_VERSION"
# 默认版本（开发环境）
DEFAULT_VERSION = "0.1.0-dev"
# GHCR 镜像名称
GHCR_IMAGE = "ghcr.io/strmforge/vabhub"
# Docker Socket 路径
DOCKER_SOCKET = "/var/run/docker.sock"


# ============== 服务实现 ==============

class UpgradeService:
    """升级引擎服务"""
    
    def __init__(self):
        self._cached_version: Optional[VersionInfo] = None
        self._last_check: Optional[datetime] = None
    
    def get_current_version(self) -> str:
        """获取当前运行版本"""
        # 1. 优先从环境变量读取
        version = os.getenv(VERSION_ENV)
        if version:
            return version
        
        # 2. 尝试从版本文件读取
        if VERSION_FILE.exists():
            try:
                return VERSION_FILE.read_text().strip()
            except Exception as e:
                logger.warning(f"读取版本文件失败: {e}")
        
        # 3. 返回默认版本
        return DEFAULT_VERSION
    
    def get_build_commit(self) -> Optional[str]:
        """获取构建 commit"""
        return os.getenv("VABHUB_BUILD_COMMIT") or os.getenv("GIT_COMMIT")
    
    def is_docker_available(self) -> bool:
        """检查 docker.sock 是否可用"""
        return Path(DOCKER_SOCKET).exists()
    
    async def get_version_info(self) -> VersionInfo:
        """获取完整版本信息"""
        current = self.get_current_version()
        commit = self.get_build_commit()
        
        # 检查是否有新版本
        update_available = False
        latest_version = None
        
        try:
            latest_version = await self._fetch_latest_version()
            if latest_version and latest_version != current:
                # 简单比较：如果版本号不同就认为有更新
                update_available = self._compare_versions(current, latest_version)
        except Exception as e:
            logger.warning(f"检查最新版本失败: {e}")
        
        return VersionInfo(
            current_version=current,
            build_commit=commit,
            update_available=update_available,
            latest_version=latest_version,
            check_source="ghcr",
            checked_at=datetime.now()
        )
    
    async def _fetch_latest_version(self) -> Optional[str]:
        """从 GHCR 获取最新版本"""
        # 使用 GHCR API 获取 latest tag 的 digest
        # 简化实现：直接返回 None，后续可以实现真正的版本检查
        try:
            # GHCR 不直接提供版本列表 API，需要通过 GitHub API
            # 这里先实现一个简化版本，检查 GitHub releases
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.github.com/repos/strmforge/VabHub/releases/latest",
                    headers={"Accept": "application/vnd.github.v3+json"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    tag = data.get("tag_name", "")
                    # 移除 v 前缀
                    return tag.lstrip("v") if tag else None
        except Exception as e:
            logger.debug(f"获取最新版本失败: {e}")
        return None
    
    def _compare_versions(self, current: str, latest: str) -> bool:
        """比较版本号，判断是否需要更新"""
        # 简单比较：如果版本号不同且 latest 不是 dev 版本
        if "dev" in latest:
            return False
        return current != latest
    
    async def check_update(self) -> UpgradeResult:
        """检查更新"""
        try:
            info = await self.get_version_info()
            self._cached_version = info
            self._last_check = datetime.now()
            
            if info.update_available:
                return UpgradeResult(
                    success=True,
                    message=f"发现新版本: {info.latest_version}",
                    action="check_only",
                    details={
                        "current_version": info.current_version,
                        "latest_version": info.latest_version,
                        "update_available": True
                    }
                )
            else:
                return UpgradeResult(
                    success=True,
                    message="当前已是最新版本",
                    action="check_only",
                    details={
                        "current_version": info.current_version,
                        "latest_version": info.latest_version,
                        "update_available": False
                    }
                )
        except Exception as e:
            logger.error(f"检查更新失败: {e}")
            return UpgradeResult(
                success=False,
                message=f"检查更新失败: {str(e)}",
                action="check_only"
            )
    
    async def apply_upgrade(self) -> UpgradeResult:
        """执行升级"""
        # 检查 docker.sock 是否可用
        if not self.is_docker_available():
            return UpgradeResult(
                success=False,
                message="升级功能不可用：未挂载 docker.sock。请使用 docker compose pull && docker compose up -d 手动升级。",
                action="apply",
                details={"docker_socket_available": False}
            )
        
        try:
            # 动态导入 docker SDK
            import docker
            
            client = docker.DockerClient(base_url=f"unix://{DOCKER_SOCKET}")
            
            # 获取容器名称
            container_name = os.getenv("VABHUB_CONTAINER_NAME", "vabhub")
            
            # 1. 拉取最新镜像
            logger.info(f"开始拉取最新镜像: {GHCR_IMAGE}:latest")
            client.images.pull(GHCR_IMAGE, tag="latest")
            logger.info("镜像拉取完成")
            
            # 2. 异步执行重启（避免阻塞当前请求）
            # 注意：重启后当前进程会终止，所以这里使用后台任务
            asyncio.create_task(self._restart_container(client, container_name))
            
            return UpgradeResult(
                success=True,
                message="升级已开始，容器将在几秒后重启。请稍后刷新页面。",
                action="apply",
                details={
                    "image": f"{GHCR_IMAGE}:latest",
                    "container": container_name,
                    "status": "restarting"
                }
            )
            
        except ImportError:
            return UpgradeResult(
                success=False,
                message="升级功能不可用：缺少 docker SDK。",
                action="apply"
            )
        except Exception as e:
            logger.error(f"执行升级失败: {e}")
            return UpgradeResult(
                success=False,
                message=f"升级失败: {str(e)}",
                action="apply"
            )
    
    async def _restart_container(self, client, container_name: str):
        """异步重启容器"""
        try:
            # 等待一小段时间，确保响应已发送
            await asyncio.sleep(2)
            
            logger.info(f"正在重启容器: {container_name}")
            container = client.containers.get(container_name)
            container.restart(timeout=30)
            logger.info("容器重启命令已发送")
        except Exception as e:
            logger.error(f"重启容器失败: {e}")


# 单例实例
_upgrade_service: Optional[UpgradeService] = None


def get_upgrade_service() -> UpgradeService:
    """获取升级服务实例"""
    global _upgrade_service
    if _upgrade_service is None:
        _upgrade_service = UpgradeService()
    return _upgrade_service
