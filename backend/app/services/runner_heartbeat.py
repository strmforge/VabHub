"""
Runner 心跳上报工具
OPS-1B 实现

用法:
    from app.services.runner_heartbeat import runner_context

    async def main():
        async with runner_context("my_runner", runner_type="scheduled", recommended_interval_min=5):
            await do_work()
"""

import time
from contextlib import asynccontextmanager
from typing import Optional
from loguru import logger

from app.core.database import async_session_factory
from app.services.system_health_service import (
    runner_heartbeat_start,
    runner_heartbeat_finish,
    get_runner_status,
)


@asynccontextmanager
async def runner_context(
    name: str,
    runner_type: str = "scheduled",
    recommended_interval_min: Optional[int] = None,
):
    """
    Runner 执行上下文管理器
    
    自动在开始时上报 start，结束时上报 finish（包括成功/失败状态）
    
    Args:
        name: Runner 名称，如 "manga_follow_sync"
        runner_type: Runner 类型 (scheduled/manual/critical/optional)
        recommended_interval_min: 推荐运行间隔（分钟）
    """
    start_time = time.monotonic()
    exit_code = 0
    error_msg: Optional[str] = None
    
    # 记录开始
    try:
        async with async_session_factory() as session:
            await runner_heartbeat_start(
                session,
                name=name,
                runner_type=runner_type,
                recommended_interval_min=recommended_interval_min,
            )
            await session.commit()
    except Exception as e:
        logger.warning(f"[runner] failed to record start for {name}: {e}")
    
    try:
        yield
    except Exception as e:
        exit_code = 1
        error_msg = str(e)[:1000]  # 截断错误信息
        raise
    finally:
        duration_ms = int((time.monotonic() - start_time) * 1000)
        
        # 记录结束
        try:
            async with async_session_factory() as session:
                await runner_heartbeat_finish(
                    session,
                    name=name,
                    exit_code=exit_code,
                    duration_ms=duration_ms,
                    error=error_msg,
                )
                await session.commit()
        except Exception as e:
            logger.warning(f"[runner] failed to record finish for {name}: {e}")


def wrap_runner_main(
    name: str,
    runner_type: str = "scheduled",
    recommended_interval_min: Optional[int] = None,
):
    """
    装饰器：包装 Runner 的 async main 函数
    
    用法:
        @wrap_runner_main("my_runner", recommended_interval_min=5)
        async def main(args):
            await do_work()
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            async with runner_context(name, runner_type, recommended_interval_min):
                return await func(*args, **kwargs)
        return wrapper
    return decorator
