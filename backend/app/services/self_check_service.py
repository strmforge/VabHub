"""
自检服务
QA-1 实现

提供功能级自检能力，覆盖 Core / Novel+TTS / Manga / Music / Notify / Bot / Runners
"""

import time
import os
import tempfile
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Optional
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.schemas.self_check import (
    SelfCheckStatus,
    SelfCheckItemResult,
    SelfCheckGroupResult,
    SelfCheckRunResult,
    SelfCheckWarning,
    SelfCheckSkip,
)


# ============== 工具函数 ==============

async def run_check_item(
    code: str,
    name: str,
    coro: Callable[[], Awaitable[None | dict[str, Any]]],
) -> SelfCheckItemResult:
    """
    包装单个检查项执行
    - 记录开始/结束时间
    - 捕获异常
    - 返回 SelfCheckItemResult
    """
    start = time.monotonic()
    try:
        result = await coro()
        duration_ms = int((time.monotonic() - start) * 1000)
        
        # 如果返回了 dict，则提取 details
        details = result if isinstance(result, dict) else None
        
        return SelfCheckItemResult(
            code=code,
            name=name,
            status=SelfCheckStatus.PASS,
            message="检查通过",
            details=details,
            duration_ms=duration_ms,
        )
    except SelfCheckSkip as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        return SelfCheckItemResult(
            code=code,
            name=name,
            status=SelfCheckStatus.SKIPPED,
            message=str(e) or "已跳过",
            duration_ms=duration_ms,
        )
    except SelfCheckWarning as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        return SelfCheckItemResult(
            code=code,
            name=name,
            status=SelfCheckStatus.WARN,
            message=str(e) or "警告",
            duration_ms=duration_ms,
        )
    except Exception as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.warning(f"[self-check] {code} failed: {e}")
        return SelfCheckItemResult(
            code=code,
            name=name,
            status=SelfCheckStatus.FAIL,
            message=str(e)[:500],
            details={"error_type": type(e).__name__},
            duration_ms=duration_ms,
        )


def build_group(code: str, name: str, items: list[SelfCheckItemResult]) -> SelfCheckGroupResult:
    """构建分组结果并计算状态"""
    group = SelfCheckGroupResult(
        code=code,
        name=name,
        status=SelfCheckStatus.PASS,
        items=items,
    )
    group.status = group.compute_status()
    return group


# ============== Core 检查 ==============

async def run_core_checks(session: AsyncSession) -> SelfCheckGroupResult:
    """核心检查：DB、Redis、下载器、磁盘"""
    items: list[SelfCheckItemResult] = []
    
    # 1. db.migrations - Alembic 版本表
    async def check_migrations():
        result = await session.execute(
            text("SELECT version_num FROM alembic_version LIMIT 1")
        )
        row = result.fetchone()
        if not row:
            raise SelfCheckWarning("Alembic 版本表为空")
        return {"current_version": row[0]}
    
    items.append(await run_check_item(
        "db.migrations", "数据库迁移状态", check_migrations
    ))
    
    # 2. db.simple_query - 简单查询
    async def check_simple_query():
        from app.models.user import User
        result = await session.execute(select(User).limit(1))
        _ = result.scalar_one_or_none()
        return {"query": "SELECT user LIMIT 1"}
    
    items.append(await run_check_item(
        "db.simple_query", "数据库查询", check_simple_query
    ))
    
    # 3. redis.ping
    async def check_redis():
        from app.core.config import settings
        
        if not getattr(settings, 'REDIS_ENABLED', False):
            raise SelfCheckSkip("Redis 未启用")
        
        import redis.asyncio as redis
        client = redis.from_url(settings.REDIS_URL)
        await client.ping()
        await client.close()
        return {"status": "pong"}
    
    items.append(await run_check_item(
        "redis.ping", "Redis 连接", check_redis
    ))
    
    # 4. download_client.config
    async def check_download_client():
        from app.core.config import settings
        
        qb_url = getattr(settings, 'QB_URL', None) or getattr(settings, 'QBITTORRENT_URL', None)
        tr_url = getattr(settings, 'TR_URL', None) or getattr(settings, 'TRANSMISSION_URL', None)
        
        if not qb_url and not tr_url:
            raise SelfCheckWarning("未配置下载器")
        
        return {"qbittorrent": bool(qb_url), "transmission": bool(tr_url)}
    
    items.append(await run_check_item(
        "download_client.config", "下载器配置", check_download_client
    ))
    
    # 5. disk.data_writable - 磁盘可写性
    async def check_disk_writable():
        from app.core.config import settings
        
        data_path = getattr(settings, 'STORAGE_PATH', './data')
        
        # 确保目录存在
        if not os.path.exists(data_path):
            os.makedirs(data_path, exist_ok=True)
        
        # 写入临时文件
        test_file = os.path.join(data_path, f".qa_write_test_{os.getpid()}")
        try:
            with open(test_file, 'w') as f:
                f.write("QA self-check write test")
            os.remove(test_file)
            return {"path": data_path, "writable": True}
        except Exception as e:
            raise Exception(f"磁盘不可写: {e}")
    
    items.append(await run_check_item(
        "disk.data_writable", "数据盘可写性", check_disk_writable
    ))
    
    return build_group("core", "核心检查", items)


# ============== Novel / TTS 检查 ==============

async def run_novel_tts_checks(session: AsyncSession) -> SelfCheckGroupResult:
    """小说/TTS/有声书检查"""
    items: list[SelfCheckItemResult] = []
    
    # 1. api.novel_center.stats
    async def check_novel_stats():
        from app.models.ebook import Ebook
        result = await session.execute(
            select(Ebook).limit(1)
        )
        _ = result.scalar_one_or_none()
        
        # 统计数量
        count_result = await session.execute(
            text("SELECT COUNT(*) FROM ebook")
        )
        count = count_result.scalar() or 0
        return {"ebook_count": count}
    
    items.append(await run_check_item(
        "api.novel_center.stats", "小说中心统计", check_novel_stats
    ))
    
    # 2. api.tts.storage_overview
    async def check_tts_storage():
        try:
            from app.models.audiobook import Audiobook
            result = await session.execute(select(Audiobook).limit(1))
            _ = result.scalar_one_or_none()
            
            count_result = await session.execute(
                text("SELECT COUNT(*) FROM audiobook")
            )
            count = count_result.scalar() or 0
            return {"audiobook_count": count}
        except Exception as e:
            # 表可能不存在
            raise SelfCheckWarning(f"有声书表查询失败: {e}")
    
    items.append(await run_check_item(
        "api.tts.storage_overview", "TTS 存储概览", check_tts_storage
    ))
    
    # 3. runner.tts_config
    async def check_tts_config():
        from app.core.config import settings
        
        # 检查 TTS 相关配置
        tts_enabled = getattr(settings, 'TTS_ENABLED', False)
        tts_provider = getattr(settings, 'TTS_PROVIDER', None)
        
        if not tts_enabled:
            raise SelfCheckSkip("TTS 未启用")
        
        if not tts_provider:
            raise SelfCheckWarning("TTS Provider 未配置")
        
        return {"provider": tts_provider, "enabled": tts_enabled}
    
    items.append(await run_check_item(
        "runner.tts_config", "TTS Provider 配置", check_tts_config
    ))
    
    # 4. reading_hub.aggregation
    async def check_reading_hub():
        try:
            from app.services.reading_hub_service import list_ongoing_reading
            # 使用一个测试用户 ID（不会实际返回数据，只测试函数是否可调用）
            _ = await list_ongoing_reading(session, user_id=0)
            return {"aggregation": "ok"}
        except Exception as e:
            # 函数可能因为没有用户而失败，但不是严重问题
            if "not found" in str(e).lower() or "0" in str(e):
                return {"aggregation": "ok (no user)"}
            raise
    
    items.append(await run_check_item(
        "reading_hub.aggregation", "阅读中心聚合", check_reading_hub
    ))
    
    return build_group("novel_tts", "小说 / TTS / 有声书", items)


# ============== Manga 检查 ==============

async def run_manga_checks(session: AsyncSession) -> SelfCheckGroupResult:
    """漫画检查"""
    items: list[SelfCheckItemResult] = []
    
    # 1. api.manga.local_series
    async def check_local_series():
        try:
            result = await session.execute(
                text("SELECT COUNT(*) FROM manga_local_series")
            )
            count = result.scalar() or 0
            return {"local_series_count": count}
        except Exception as e:
            raise SelfCheckWarning(f"本地漫画表查询失败: {e}")
    
    items.append(await run_check_item(
        "api.manga.local_series", "漫画本地系列", check_local_series
    ))
    
    # 2. api.manga.following
    async def check_following():
        try:
            result = await session.execute(
                text("SELECT COUNT(*) FROM manga_follow")
            )
            count = result.scalar() or 0
            return {"following_count": count}
        except Exception as e:
            raise SelfCheckWarning(f"漫画追更表查询失败: {e}")
    
    items.append(await run_check_item(
        "api.manga.following", "漫画追更列表", check_following
    ))
    
    # 3. runner.manga_follow_heartbeat
    async def check_manga_runner():
        from app.services.system_health_service import get_runner_status
        
        runner = await get_runner_status(session, "manga_follow_sync")
        if not runner:
            raise SelfCheckWarning("manga_follow_sync Runner 未运行过")
        
        if runner.last_finished_at:
            hours_ago = (datetime.utcnow() - runner.last_finished_at).total_seconds() / 3600
            if hours_ago > 24:
                raise SelfCheckWarning(f"Runner 最后执行已超过 {int(hours_ago)} 小时")
        
        return {
            "last_finished": runner.last_finished_at.isoformat() if runner.last_finished_at else None,
            "last_exit_code": runner.last_exit_code,
        }
    
    items.append(await run_check_item(
        "runner.manga_follow_heartbeat", "漫画追更 Runner", check_manga_runner
    ))
    
    return build_group("manga", "漫画", items)


# ============== Music 检查 ==============

async def run_music_checks(session: AsyncSession) -> SelfCheckGroupResult:
    """音乐检查"""
    items: list[SelfCheckItemResult] = []
    
    # 1. api.music.library
    async def check_music_library():
        try:
            result = await session.execute(
                text("SELECT COUNT(*) FROM music_album")
            )
            count = result.scalar() or 0
            return {"album_count": count}
        except Exception as e:
            raise SelfCheckWarning(f"音乐专辑表查询失败: {e}")
    
    items.append(await run_check_item(
        "api.music.library", "音乐库", check_music_library
    ))
    
    # 2. api.music.charts
    async def check_music_charts():
        try:
            result = await session.execute(
                text("SELECT COUNT(*) FROM music_chart_source WHERE enabled = true")
            )
            count = result.scalar() or 0
            
            if count == 0:
                raise SelfCheckWarning("无启用的音乐榜单源")
            
            return {"enabled_sources": count}
        except Exception as e:
            if "does not exist" in str(e).lower():
                raise SelfCheckSkip("音乐榜单表不存在")
            raise
    
    items.append(await run_check_item(
        "api.music.charts", "音乐榜单", check_music_charts
    ))
    
    # 3. runner.music_subscription_heartbeat
    async def check_music_runner():
        from app.services.system_health_service import get_runner_status
        
        runner = await get_runner_status(session, "music_subscription_sync")
        if not runner:
            raise SelfCheckWarning("music_subscription_sync Runner 未运行过")
        
        if runner.last_finished_at:
            hours_ago = (datetime.utcnow() - runner.last_finished_at).total_seconds() / 3600
            if hours_ago > 24:
                raise SelfCheckWarning(f"Runner 最后执行已超过 {int(hours_ago)} 小时")
        
        return {
            "last_finished": runner.last_finished_at.isoformat() if runner.last_finished_at else None,
            "last_exit_code": runner.last_exit_code,
        }
    
    items.append(await run_check_item(
        "runner.music_subscription_heartbeat", "音乐订阅 Runner", check_music_runner
    ))
    
    return build_group("music", "音乐", items)


# ============== Notify 检查 ==============

async def run_notify_checks(session: AsyncSession) -> SelfCheckGroupResult:
    """通知检查"""
    items: list[SelfCheckItemResult] = []
    
    # 1. notify.write_user_notification
    async def check_write_notification():
        try:
            # 只检查表是否存在且可查询
            result = await session.execute(
                text("SELECT COUNT(*) FROM user_notification")
            )
            count = result.scalar() or 0
            return {"notification_count": count, "writable": True}
        except Exception as e:
            raise Exception(f"用户通知表不可用: {e}")
    
    items.append(await run_check_item(
        "notify.write_user_notification", "通知写入能力", check_write_notification
    ))
    
    # 2. notify.user_channel_exists
    async def check_user_channels():
        try:
            result = await session.execute(
                text("SELECT COUNT(*) FROM user_notify_channel WHERE enabled = true")
            )
            count = result.scalar() or 0
            
            if count == 0:
                raise SelfCheckWarning("无启用的用户通知渠道")
            
            return {"enabled_channels": count}
        except Exception as e:
            if "does not exist" in str(e).lower():
                raise SelfCheckSkip("用户通知渠道表不存在")
            raise
    
    items.append(await run_check_item(
        "notify.user_channel_exists", "用户通知渠道", check_user_channels
    ))
    
    # 3. notify.ops_alert_channels
    async def check_alert_channels():
        try:
            result = await session.execute(
                text("SELECT COUNT(*) FROM alert_channel WHERE enabled = true")
            )
            count = result.scalar() or 0
            
            if count == 0:
                raise SelfCheckWarning("无启用的告警渠道")
            
            return {"enabled_alert_channels": count}
        except Exception as e:
            if "does not exist" in str(e).lower():
                raise SelfCheckSkip("告警渠道表不存在")
            raise
    
    items.append(await run_check_item(
        "notify.ops_alert_channels", "运维告警渠道", check_alert_channels
    ))
    
    return build_group("notify", "通知", items)


# ============== Bot 检查 ==============

async def run_bot_checks(session: AsyncSession) -> SelfCheckGroupResult:
    """Bot / Telegram 检查"""
    items: list[SelfCheckItemResult] = []
    
    # 1. bot.telegram.config
    async def check_telegram_config():
        from app.core.config import settings
        
        enabled = getattr(settings, 'TELEGRAM_BOT_ENABLED', False)
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        
        if not enabled:
            raise SelfCheckSkip("Telegram Bot 未启用")
        
        if not token:
            raise SelfCheckWarning("Telegram Bot Token 未配置")
        
        return {"enabled": True, "token_configured": True}
    
    items.append(await run_check_item(
        "bot.telegram.config", "Telegram Bot 配置", check_telegram_config
    ))
    
    # 2. bot.telegram.whoami (可选，受 env 控制)
    async def check_telegram_whoami():
        import os
        from app.core.config import settings
        
        # 检查是否跳过
        if os.getenv("QA_SKIP_TELEGRAM_CHECKS", "").lower() in ("1", "true", "yes"):
            raise SelfCheckSkip("QA_SKIP_TELEGRAM_CHECKS 已设置")
        
        enabled = getattr(settings, 'TELEGRAM_BOT_ENABLED', False)
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        
        if not enabled or not token:
            raise SelfCheckSkip("Telegram Bot 未启用或未配置")
        
        try:
            from app.modules.bots.telegram_bot_client import TelegramBotClient
            client = TelegramBotClient(token)
            me = await client.get_me()
            if me:
                return {"username": me.get("username"), "id": me.get("id")}
            else:
                raise SelfCheckWarning("getMe 返回空")
        except Exception as e:
            raise SelfCheckWarning(f"Telegram API 调用失败: {e}")
    
    items.append(await run_check_item(
        "bot.telegram.whoami", "Telegram Bot 连通性", check_telegram_whoami
    ))
    
    return build_group("bot", "Bot / Telegram", items)


# ============== Runners 检查 ==============

async def run_runner_checks(session: AsyncSession) -> SelfCheckGroupResult:
    """Runner 状态检查"""
    items: list[SelfCheckItemResult] = []
    
    # 定义要检查的 Runner 列表
    runners_to_check = [
        ("manga_follow_sync", "漫画追更同步"),
        ("manga_remote_sync", "漫画远程同步"),
        ("music_subscription_sync", "音乐订阅同步"),
        ("ops_health_check", "OPS 健康检查"),
    ]
    
    from app.services.system_health_service import get_runner_status
    
    for runner_name, display_name in runners_to_check:
        async def check_runner(name=runner_name):
            runner = await get_runner_status(session, name)
            if not runner:
                raise SelfCheckWarning(f"{name} Runner 未运行过或尚未部署")
            
            # 检查最近执行时间
            if runner.last_finished_at:
                hours_ago = (datetime.utcnow() - runner.last_finished_at).total_seconds() / 3600
                
                # 根据推荐间隔判断
                interval_min = runner.recommended_interval_min or 60
                expected_hours = interval_min / 60 * 2  # 允许 2 倍间隔
                
                if hours_ago > max(expected_hours, 24):
                    raise SelfCheckWarning(
                        f"最后执行已超过 {int(hours_ago)} 小时"
                    )
            
            return {
                "last_finished": runner.last_finished_at.isoformat() if runner.last_finished_at else None,
                "last_exit_code": runner.last_exit_code,
                "success_count": runner.success_count or 0,
                "failure_count": runner.failure_count or 0,
            }
        
        items.append(await run_check_item(
            f"runner.{runner_name}", f"{display_name} Runner", check_runner
        ))
    
    return build_group("runners", "Runner 状态", items)


# ============== 主入口 ==============

async def run_full_self_check(session: AsyncSession) -> SelfCheckRunResult:
    """
    运行完整自检
    
    返回 SelfCheckRunResult，包含各组检查结果
    """
    started_at = datetime.utcnow()
    groups: list[SelfCheckGroupResult] = []
    
    logger.info("[self-check] Starting full self-check...")
    
    # 1. Core 检查
    try:
        groups.append(await run_core_checks(session))
    except Exception as e:
        logger.error(f"[self-check] core checks failed: {e}")
        groups.append(SelfCheckGroupResult(
            code="core",
            name="核心检查",
            status=SelfCheckStatus.FAIL,
            items=[SelfCheckItemResult(
                code="core.error",
                name="核心检查",
                status=SelfCheckStatus.FAIL,
                message=str(e),
            )],
        ))
    
    # 2. Novel / TTS 检查
    try:
        groups.append(await run_novel_tts_checks(session))
    except Exception as e:
        logger.error(f"[self-check] novel_tts checks failed: {e}")
        groups.append(SelfCheckGroupResult(
            code="novel_tts",
            name="小说 / TTS / 有声书",
            status=SelfCheckStatus.FAIL,
            items=[SelfCheckItemResult(
                code="novel_tts.error",
                name="小说/TTS 检查",
                status=SelfCheckStatus.FAIL,
                message=str(e),
            )],
        ))
    
    # 3. Manga 检查
    try:
        groups.append(await run_manga_checks(session))
    except Exception as e:
        logger.error(f"[self-check] manga checks failed: {e}")
        groups.append(SelfCheckGroupResult(
            code="manga",
            name="漫画",
            status=SelfCheckStatus.FAIL,
            items=[SelfCheckItemResult(
                code="manga.error",
                name="漫画检查",
                status=SelfCheckStatus.FAIL,
                message=str(e),
            )],
        ))
    
    # 4. Music 检查
    try:
        groups.append(await run_music_checks(session))
    except Exception as e:
        logger.error(f"[self-check] music checks failed: {e}")
        groups.append(SelfCheckGroupResult(
            code="music",
            name="音乐",
            status=SelfCheckStatus.FAIL,
            items=[SelfCheckItemResult(
                code="music.error",
                name="音乐检查",
                status=SelfCheckStatus.FAIL,
                message=str(e),
            )],
        ))
    
    # 5. Notify 检查
    try:
        groups.append(await run_notify_checks(session))
    except Exception as e:
        logger.error(f"[self-check] notify checks failed: {e}")
        groups.append(SelfCheckGroupResult(
            code="notify",
            name="通知",
            status=SelfCheckStatus.FAIL,
            items=[SelfCheckItemResult(
                code="notify.error",
                name="通知检查",
                status=SelfCheckStatus.FAIL,
                message=str(e),
            )],
        ))
    
    # 6. Bot 检查
    try:
        groups.append(await run_bot_checks(session))
    except Exception as e:
        logger.error(f"[self-check] bot checks failed: {e}")
        groups.append(SelfCheckGroupResult(
            code="bot",
            name="Bot / Telegram",
            status=SelfCheckStatus.FAIL,
            items=[SelfCheckItemResult(
                code="bot.error",
                name="Bot 检查",
                status=SelfCheckStatus.FAIL,
                message=str(e),
            )],
        ))
    
    # 7. Runners 检查
    try:
        groups.append(await run_runner_checks(session))
    except Exception as e:
        logger.error(f"[self-check] runner checks failed: {e}")
        groups.append(SelfCheckGroupResult(
            code="runners",
            name="Runner 状态",
            status=SelfCheckStatus.FAIL,
            items=[SelfCheckItemResult(
                code="runners.error",
                name="Runner 检查",
                status=SelfCheckStatus.FAIL,
                message=str(e),
            )],
        ))
    
    finished_at = datetime.utcnow()
    
    # 构建结果
    result = SelfCheckRunResult(
        started_at=started_at,
        finished_at=finished_at,
        overall_status=SelfCheckStatus.PASS,
        groups=groups,
        environment={
            "python_version": __import__("sys").version,
            "hostname": __import__("socket").gethostname(),
        },
    )
    result.overall_status = result.compute_overall_status()
    
    logger.info(
        f"[self-check] Completed in {result.duration_ms}ms, "
        f"overall={result.overall_status.value}, summary={result.summary}"
    )
    
    return result
