"""
Demo 模式安全守卫
RELEASE-1 R3-3 实现

提供装饰器和辅助函数，在 Demo 模式下阻止危险操作。
"""

from functools import wraps
from fastapi import HTTPException, status
from loguru import logger

from app.core.config import settings


class DemoModeError(HTTPException):
    """Demo 模式限制错误"""
    
    def __init__(self, operation: str = "此操作"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "DEMO_MODE_RESTRICTED",
                "error_message": f"当前为 Demo 模式，{operation}已被禁用",
                "demo_mode": True,
            }
        )


def is_demo_mode() -> bool:
    """检查是否为 Demo 模式"""
    return settings.APP_DEMO_MODE


def check_demo_mode(operation: str = "此操作"):
    """
    检查 Demo 模式，如果是则抛出异常
    
    Args:
        operation: 操作描述，用于错误信息
        
    Raises:
        DemoModeError: 如果当前为 Demo 模式
    """
    if is_demo_mode():
        logger.warning(f"Demo 模式阻止操作: {operation}")
        raise DemoModeError(operation)


def demo_guard(operation: str = "此操作"):
    """
    Demo 模式守卫装饰器
    
    用于 API 端点，在 Demo 模式下阻止执行并返回友好错误
    
    用法:
        @router.post("/download")
        @demo_guard("添加下载任务")
        async def add_download(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            check_demo_mode(operation)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def demo_guard_sync(operation: str = "此操作"):
    """
    Demo 模式守卫装饰器（同步版本）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            check_demo_mode(operation)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# 预定义的危险操作列表
DEMO_RESTRICTED_OPERATIONS = {
    # 下载相关
    "add_download": "添加下载任务",
    "delete_download": "删除下载任务",
    "start_download": "开始下载",
    
    # PT 站点相关
    "add_site": "添加 PT 站点",
    "delete_site": "删除 PT 站点",
    "test_site": "测试 PT 站点连接",
    
    # 网盘相关
    "add_cloud_storage": "添加网盘配置",
    "delete_cloud_storage": "删除网盘配置",
    "test_cloud_storage": "测试网盘连接",
    "upload_to_cloud": "上传到网盘",
    
    # 文件操作相关
    "delete_file": "删除文件",
    "move_file": "移动文件",
    "rename_file": "重命名文件",
    "clean_files": "清理文件",
    
    # 系统配置相关
    "update_secrets": "更新密钥配置",
    "update_downloader": "更新下载器配置",
    
    # 外部 API 相关
    "external_api_request": "发起外部 API 请求",
}


def get_demo_restriction_message(operation_key: str) -> str:
    """获取操作的限制提示信息"""
    return DEMO_RESTRICTED_OPERATIONS.get(operation_key, operation_key)
