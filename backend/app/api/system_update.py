"""
系统更新API
支持自动更新和热更新功能
"""

from fastapi import APIRouter, HTTPException, status, Depends, Body
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from loguru import logger

from app.core.database import get_db
from app.modules.system.update_manager import UpdateManager, UpdateMode
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter(prefix="/system", tags=["系统更新"])

# 全局更新管理器实例
_update_manager: Optional[UpdateManager] = None


def get_update_manager() -> UpdateManager:
    """获取更新管理器实例"""
    global _update_manager
    if _update_manager is None:
        _update_manager = UpdateManager()
        # 从设置中读取更新模式
        # TODO: 从数据库读取配置
    return _update_manager


class UpdateRequest(BaseModel):
    """更新请求"""
    mode: Optional[str] = None  # never/release/dev
    force: bool = False  # 是否强制更新


class HotReloadRequest(BaseModel):
    """热重载请求"""
    modules: Optional[List[str]] = None  # 要重载的模块列表


@router.get("/update/check", response_model=BaseResponse)
async def check_update():
    """
    检查是否有可用更新
    
    返回统一响应格式：
    {
        "success": true,
        "message": "检查完成",
        "data": {
            "has_update": true,
            "current_version": "...",
            "current_commit": "...",
            "remote_info": {...}
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        manager = get_update_manager()
        update_info = await manager.check_update_available()
        
        return success_response(
            data=update_info,
            message="检查更新完成"
        )
    except Exception as e:
        logger.error(f"检查更新失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"检查更新时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/update", response_model=BaseResponse)
async def update_system(request: UpdateRequest):
    """
    更新系统
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": {
            "version": "...",
            "commit": "...",
            "requires_restart": true
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        manager = get_update_manager()
        
        if request.mode:
            manager.update_mode = UpdateMode(request.mode)
        
        result = await manager.update_system()
        
        if result.get("success"):
            return success_response(
                data={
                    "version": result.get("version"),
                    "commit": result.get("commit"),
                    "requires_restart": True  # 系统更新需要重启
                },
                message=result.get("message", "更新成功")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="UPDATE_FAILED",
                    error_message=result.get("message", "更新失败")
                ).model_dump()
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"系统更新失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"系统更新时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/hot-reload", response_model=BaseResponse)
async def hot_reload_modules(request: HotReloadRequest):
    """
    热重载模块（无需重启）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "热重载完成",
        "data": {
            "reloaded_modules": [...],
            "failed_modules": [...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        manager = get_update_manager()
        result = await manager.hot_reload_modules(request.modules)
        
        return success_response(
            data={
                "reloaded_modules": result.get("reloaded_modules", []),
                "failed_modules": result.get("failed_modules", [])
            },
            message=result.get("message", "热重载完成")
        )
    except Exception as e:
        logger.error(f"热重载失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"热重载时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/version", response_model=BaseResponse)
async def get_version():
    """
    获取当前系统版本信息
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "version": "...",
            "commit": "...",
            "build_time": "...",
            "deployment_type": "..."
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        manager = get_update_manager()
        
        version_info = {
            "version": await manager._get_current_version(),
            "commit": await manager._get_current_commit(),
            "build_time": None,  # TODO: 从构建信息中获取
            "deployment_type": manager.deployment_type.value
        }
        
        return success_response(
            data=version_info,
            message="获取版本信息成功"
        )
    except Exception as e:
        logger.error(f"获取版本信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取版本信息时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/restart", response_model=BaseResponse)
async def restart_system():
    """
    重启系统（如果启用自动更新，会在重启时更新）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "系统正在重启...",
        "data": {
            "will_update": true,
            "update_mode": "..."
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        manager = get_update_manager()
        
        # 检查是否启用自动更新
        will_update = manager.update_mode != UpdateMode.NEVER and manager.auto_update_enabled
        
        # 执行重启（根据部署方式）
        if manager.deployment_type == DeploymentType.DOCKER:
            # Docker: 重启容器
            container_name = os.getenv("CONTAINER_NAME", "vabhub-backend")
            result = await asyncio.create_subprocess_exec(
                "docker", "restart", container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.wait()
            
            if result.returncode != 0:
                stderr = (await result.stderr.read()).decode()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_response(
                        error_code="RESTART_FAILED",
                        error_message=f"重启Docker容器失败: {stderr}"
                    ).model_dump()
                )
        else:
            # 源代码: 触发应用重启（需要外部进程管理器）
            # 这里可以发送信号给进程管理器（如systemd, supervisor等）
            logger.info("触发系统重启（源代码部署）")
            # TODO: 实现源代码部署的重启逻辑
        
        return success_response(
            data={
                "will_update": will_update,
                "update_mode": manager.update_mode.value if will_update else None,
                "deployment_type": manager.deployment_type.value
            },
            message="系统正在重启，请稍候..."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重启系统失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"重启系统时发生错误: {str(e)}"
            ).model_dump()
        )

