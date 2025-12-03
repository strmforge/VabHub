"""
下载器管理API
用于管理下载器实例（qBittorrent、Transmission等）
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from loguru import logger

from app.core.database import get_db
from app.core.downloaders import DownloaderClient, DownloaderType
from app.modules.settings.service import SettingsService
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter(prefix="/dl", tags=["下载器管理"])


class DownloaderInstance(BaseModel):
    """下载器实例"""
    id: str
    name: str
    type: str  # qBittorrent, Transmission
    host: str
    port: int
    enabled: bool = True
    status: str = "unknown"  # online, offline, error


class DownloaderStats(BaseModel):
    """下载器统计"""
    id: str
    queue_size: int = 0
    active_downloads: int = 0
    active_uploads: int = 0
    download_speed_mbps: float = 0.0
    upload_speed_mbps: float = 0.0
    free_space_gb: Optional[float] = None
    status: str = "unknown"


@router.get("/instances", response_model=BaseResponse)
async def get_downloader_instances(
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有下载器实例列表
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "instances": [DownloaderInstance, ...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        settings_service = SettingsService(db)
        
        instances = []
        
        # 获取qBittorrent配置
        qb_host = await settings_service.get_setting("qbittorrent_host") or "localhost"
        qb_port = await settings_service.get_setting("qbittorrent_port") or 8080
        qb_enabled = await settings_service.get_setting("qbittorrent_enabled", category="download") or True
        
        if qb_enabled:
            # 测试连接状态
            status_str = "offline"
            try:
                client = DownloaderClient(
                    DownloaderType.QBITTORRENT,
                    {
                        "host": qb_host,
                        "port": int(qb_port) if isinstance(qb_port, str) else qb_port,
                        "username": await settings_service.get_setting("qbittorrent_username") or "",
                        "password": await settings_service.get_setting("qbittorrent_password") or ""
                    }
                )
                # 尝试登录以检查连接
                await client.login()
                status_str = "online"
                await client.close()
            except Exception as e:
                logger.debug(f"qBittorrent连接测试失败: {e}")
                status_str = "offline"
            
            instances.append(DownloaderInstance(
                id="qbittorrent",
                name="qBittorrent",
                type="qBittorrent",
                host=qb_host,
                port=int(qb_port) if isinstance(qb_port, str) else qb_port,
                enabled=qb_enabled,
                status=status_str
            ))
        
        # 获取Transmission配置
        tr_host = await settings_service.get_setting("transmission_host") or "localhost"
        tr_port = await settings_service.get_setting("transmission_port") or 9091
        tr_enabled = await settings_service.get_setting("transmission_enabled", category="download") or True
        
        if tr_enabled:
            # 测试连接状态
            status_str = "offline"
            try:
                client = DownloaderClient(
                    DownloaderType.TRANSMISSION,
                    {
                        "host": tr_host,
                        "port": int(tr_port) if isinstance(tr_port, str) else tr_port,
                        "username": await settings_service.get_setting("transmission_username") or "",
                        "password": await settings_service.get_setting("transmission_password") or ""
                    }
                )
                # 尝试连接以检查状态
                await client.get_torrents()
                status_str = "online"
                await client.close()
            except Exception as e:
                logger.debug(f"Transmission连接测试失败: {e}")
                status_str = "offline"
            
            instances.append(DownloaderInstance(
                id="transmission",
                name="Transmission",
                type="Transmission",
                host=tr_host,
                port=int(tr_port) if isinstance(tr_port, str) else tr_port,
                enabled=tr_enabled,
                status=status_str
            ))
        
        return success_response(
            data={"instances": [instance.model_dump() for instance in instances]},
            message="获取下载器实例列表成功"
        )
    except Exception as e:
        logger.error(f"获取下载器实例列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取下载器实例列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{did}/stats", response_model=BaseResponse)
async def get_downloader_stats(
    did: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取下载器统计信息
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": DownloaderStats,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        settings_service = SettingsService(db)
        
        # 确定下载器类型
        if did == "qbittorrent":
            downloader_type = DownloaderType.QBITTORRENT
            config_prefix = "qbittorrent_"
        elif did == "transmission":
            downloader_type = DownloaderType.TRANSMISSION
            config_prefix = "transmission_"
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message=f"下载器不存在: {did}"
                ).model_dump()
            )
        
        # 获取配置
        host = await settings_service.get_setting(f"{config_prefix}host") or "localhost"
        port = await settings_service.get_setting(f"{config_prefix}port") or (8080 if did == "qbittorrent" else 9091)
        username = await settings_service.get_setting(f"{config_prefix}username") or ""
        password = await settings_service.get_setting(f"{config_prefix}password") or ""
        
        # 创建客户端
        client = DownloaderClient(
            downloader_type,
            {
                "host": host,
                "port": int(port) if isinstance(port, str) else port,
                "username": username,
                "password": password
            }
        )
        
        try:
            # 获取统计信息
            if did == "qbittorrent":
                # qBittorrent统计
                torrents = await client.get_torrents()
                active_downloads = sum(1 for t in torrents if t.get("state") == "downloading")
                active_uploads = sum(1 for t in torrents if t.get("state") == "uploading" or t.get("state") == "seeding")
                
                # 从torrents中计算总速度
                download_speed = sum(t.get("dlspeed", 0) for t in torrents) / (1024 * 1024)  # B/s -> MB/s
                upload_speed = sum(t.get("upspeed", 0) for t in torrents) / (1024 * 1024)  # B/s -> MB/s
                
                stats = DownloaderStats(
                    id=did,
                    queue_size=len(torrents),
                    active_downloads=active_downloads,
                    active_uploads=active_uploads,
                    download_speed_mbps=round(download_speed, 2),
                    upload_speed_mbps=round(upload_speed, 2),
                    status="online"
                )
            else:
                # Transmission统计
                torrents = await client.get_torrents()
                active_downloads = sum(1 for t in torrents if t.get("status") == 4)  # 4 = downloading
                active_uploads = sum(1 for t in torrents if t.get("status") == 6)  # 6 = seeding
                
                # 从torrents中计算总速度
                download_speed = sum(t.get("rateDownload", 0) for t in torrents) / (1024 * 1024)  # B/s -> MB/s
                upload_speed = sum(t.get("rateUpload", 0) for t in torrents) / (1024 * 1024)  # B/s -> MB/s
                
                stats = DownloaderStats(
                    id=did,
                    queue_size=len(torrents),
                    active_downloads=active_downloads,
                    active_uploads=active_uploads,
                    download_speed_mbps=round(download_speed, 2),
                    upload_speed_mbps=round(upload_speed, 2),
                    status="online"
                )
            
            await client.close()
            
            return success_response(
                data=stats.model_dump(),
                message="获取下载器统计成功"
            )
        except Exception as e:
            await client.close()
            logger.error(f"获取下载器统计失败: {e}")
            # 返回离线状态
            stats = DownloaderStats(
                id=did,
                status="offline"
            )
            return success_response(
                data=stats.model_dump(),
                message="下载器离线或无法连接"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取下载器统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取下载器统计时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/{did}/test", response_model=BaseResponse)
async def test_downloader(
    did: str,
    db: AsyncSession = Depends(get_db)
):
    """
    测试下载器连接
    
    返回统一响应格式：
    {
        "success": true,
        "message": "连接成功",
        "data": {
            "connected": true,
            "response_time_ms": 100
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        import time
        settings_service = SettingsService(db)
        
        # 确定下载器类型
        if did == "qbittorrent":
            downloader_type = DownloaderType.QBITTORRENT
            config_prefix = "qbittorrent_"
        elif did == "transmission":
            downloader_type = DownloaderType.TRANSMISSION
            config_prefix = "transmission_"
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message=f"下载器不存在: {did}"
                ).model_dump()
            )
        
        # 获取配置
        host = await settings_service.get_setting(f"{config_prefix}host") or "localhost"
        port = await settings_service.get_setting(f"{config_prefix}port") or (8080 if did == "qbittorrent" else 9091)
        username = await settings_service.get_setting(f"{config_prefix}username") or ""
        password = await settings_service.get_setting(f"{config_prefix}password") or ""
        
        # 创建客户端并测试连接
        start_time = time.time()
        client = DownloaderClient(
            downloader_type,
            {
                "host": host,
                "port": int(port) if isinstance(port, str) else port,
                "username": username,
                "password": password
            }
        )
        
        try:
            # 尝试连接
            if did == "qbittorrent":
                # qBittorrent需要通过client.client访问实际的客户端
                if hasattr(client, 'client') and hasattr(client.client, 'login'):
                    await client.client.login()
                else:
                    # 如果没有login方法，尝试获取torrents来测试连接
                    await client.get_torrents()
            else:
                await client.get_torrents()
            
            response_time = int((time.time() - start_time) * 1000)
            await client.close()
            
            return success_response(
                data={
                    "connected": True,
                    "response_time_ms": response_time
                },
                message="连接成功"
            )
        except Exception as e:
            await client.close()
            logger.error(f"下载器连接测试失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="CONNECTION_FAILED",
                    error_message=f"连接失败: {str(e)}"
                ).model_dump()
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试下载器连接失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"测试下载器连接时发生错误: {str(e)}"
            ).model_dump()
        )

