from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.short_drama.schema_utils import ensure_short_drama_columns
from app.modules.music.schema_utils import ensure_music_schema
from app.modules.rsshub.schema_utils import ensure_subscription_health_columns

MigrationRunner = Callable[[Optional[AsyncSession]], Awaitable[Dict[str, Any]]]


@dataclass
class MigrationStep:
    """单个迁移步骤定义。"""

    id: str
    title: str
    description: str
    requires_session: bool
    runner: MigrationRunner


async def _run_short_drama(_: Optional[AsyncSession]) -> Dict[str, Any]:
    await ensure_short_drama_columns()
    return {"status": "checked"}


async def _run_music(_: Optional[AsyncSession]) -> Dict[str, Any]:
    await ensure_music_schema()
    return {"status": "checked"}


async def _run_rsshub(session: Optional[AsyncSession]) -> Dict[str, Any]:
    if session is None:
        raise RuntimeError("RSSHub 健康字段迁移需要数据库会话")
    await ensure_subscription_health_columns(session)
    return {"status": "checked"}


async def _run_plugin_safety(session: Optional[AsyncSession]) -> Dict[str, Any]:
    """
    PLUGIN-SAFETY-1 数据库迁移
    
    添加插件健康状态字段和审计日志表
    """
    if session is None:
        raise RuntimeError("PLUGIN-SAFETY-1 迁移需要数据库会话")
    
    from sqlalchemy import text
    from app.models.plugin_audit import PluginAuditLog
    
    # 添加插件健康状态字段
    migrations = [
        # 添加 last_error_at 字段
        """
        ALTER TABLE plugins 
        ADD COLUMN IF NOT EXISTS last_error_at TIMESTAMP NULL
        """,
        # 添加 error_count 字段
        """
        ALTER TABLE plugins 
        ADD COLUMN IF NOT EXISTS error_count INTEGER DEFAULT 0
        """,
        # 添加 is_quarantined 字段
        """
        ALTER TABLE plugins 
        ADD COLUMN IF NOT EXISTS is_quarantined BOOLEAN DEFAULT FALSE
        """,
    ]
    
    # 执行插件表迁移
    for migration in migrations:
        try:
            await session.execute(text(migration))
            await session.commit()
        except Exception as e:
            await session.rollback()
            # 字段可能已存在，忽略错误
            print(f"Plugin migration warning: {e}")
    
    # 创建审计日志表
    try:
        # 使用 run_sync 包装同步的 metadata 操作
        await session.run_sync(lambda sync_session: PluginAuditLog.metadata.create_all(sync_session.bind))
        await session.commit()
    except Exception as e:
        await session.rollback()
        print(f"PluginAuditLog creation warning: {e}")
    
    return {"status": "checked", "features": ["plugin_health_fields", "plugin_audit_log"]}


async def _run_video_autoloop_p1(session: Optional[AsyncSession]) -> Dict[str, Any]:
    """
    VIDEO-AUTOLOOP-1-P1 数据库迁移
    
    扩展 Subscription 模型，添加用户归属和安全策略字段
    """
    if session is None:
        raise RuntimeError("VIDEO-AUTOLOOP-1-P1 迁移需要数据库会话")
    
    from sqlalchemy import text
    
    # SQLite兼容的迁移步骤
    migrations = [
        # 添加 owner_id 字段
        """
        ALTER TABLE subscriptions 
        ADD COLUMN IF NOT EXISTS owner_id INTEGER NULL
        """,
        # 添加 security_policy 字段
        """
        ALTER TABLE subscriptions 
        ADD COLUMN IF NOT EXISTS security_policy TEXT NULL
        """,
        """
        ALTER TABLE subscriptions 
        ADD COLUMN IF NOT EXISTS last_success_at TIMESTAMP NULL
        """,
        """
        ALTER TABLE subscriptions 
        ADD COLUMN IF NOT EXISTS last_error VARCHAR(500) NULL
        """,
    ]
    
    # 执行迁移
    for i, migration in enumerate(migrations):
        try:
            await session.execute(text(migration))
            await session.commit()
            print(f"VIDEO-AUTOLOOP-1-P1 migration step {i+1} completed")
        except Exception as e:
            await session.rollback()
            # 字段可能已存在，忽略错误
            print(f"VIDEO-AUTOLOOP-1-P1 migration step {i+1} warning: {e}")
    
    # 如果表中有数据，设置默认用户ID（假设管理员用户ID为1）
    try:
        await session.execute(text("""
            UPDATE subscriptions 
            SET user_id = 1 
            WHERE user_id IS NULL
        """))
        await session.commit()
        print("VIDEO-AUTOLOOP-1-P1: Set default user_id for existing subscriptions")
    except Exception as e:
        await session.rollback()
        print(f"VIDEO-AUTOLOOP-1-P1 user_id update warning: {e}")
    
    return {
        "status": "checked", 
        "features": [
            "subscription_user_id", 
            "subscription_security_fields", 
            "subscription_runtime_fields"
        ]
    }


async def _run_plugin_remote(session: Optional[AsyncSession]) -> Dict[str, Any]:
    """
    PLUGIN-REMOTE-1 数据库迁移
    
    添加远程插件支持相关字段
    """
    if session is None:
        raise RuntimeError("PLUGIN-REMOTE-1 迁移需要数据库会话")
    
    from sqlalchemy import text
    from app.models.plugin import PluginType
    
    # 添加远程插件相关字段
    migrations = [
        # 添加 plugin_type 字段（ENUM）
        """
        ALTER TABLE plugins 
        ADD COLUMN IF NOT EXISTS plugin_type VARCHAR(20) DEFAULT 'local'
        """,
        # 添加 remote_config 字段（JSON）
        """
        ALTER TABLE plugins 
        ADD COLUMN IF NOT EXISTS remote_config JSON NULL
        """,
        # 添加 subscribed_events 字段（JSON array）
        """
        ALTER TABLE plugins 
        ADD COLUMN IF NOT EXISTS subscribed_events JSON DEFAULT '[]'
        """,
        # 添加 plugin_token 字段
        """
        ALTER TABLE plugins 
        ADD COLUMN IF NOT EXISTS plugin_token VARCHAR(255) NULL
        """,
        # 添加 call_count 字段
        """
        ALTER TABLE plugins 
        ADD COLUMN IF NOT EXISTS call_count INTEGER DEFAULT 0
        """,
        # 添加 event_handled_count 字段
        """
        ALTER TABLE plugins 
        ADD COLUMN IF NOT EXISTS event_handled_count INTEGER DEFAULT 0
        """,
        # 添加 last_called_at 字段
        """
        ALTER TABLE plugins 
        ADD COLUMN IF NOT EXISTS last_called_at TIMESTAMP NULL
        """,
    ]
    
    # 执行插件表迁移
    for migration in migrations:
        try:
            await session.execute(text(migration))
            await session.commit()
        except Exception as e:
            await session.rollback()
            # 字段可能已存在，忽略错误
            print(f"Plugin REMOTE migration warning: {e}")
    
    # 为新字段创建索引（PostgreSQL 语法）
    indexes = [
        # plugin_type 索引
        """
        CREATE INDEX IF NOT EXISTS idx_plugins_plugin_type ON plugins(plugin_type)
        """,
        # plugin_token 索引
        """
        CREATE INDEX IF NOT EXISTS idx_plugins_plugin_token ON plugins(plugin_token)
        """,
        # call_count 索引
        """
        CREATE INDEX IF NOT EXISTS idx_plugins_call_count ON plugins(call_count)
        """,
        # event_handled_count 索引
        """
        CREATE INDEX IF NOT EXISTS idx_plugins_event_handled_count ON plugins(event_handled_count)
        """,
        # last_called_at 索引
        """
        CREATE INDEX IF NOT EXISTS idx_plugins_last_called_at ON plugins(last_called_at)
        """,
    ]
    
    # 执行索引创建（可能因数据库类型不同而失败）
    for index in indexes:
        try:
            await session.execute(text(index))
            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"Plugin REMOTE index creation warning: {e}")
    
    return {"status": "checked", "features": ["plugin_type", "remote_config", "plugin_statistics"]}


async def _run_manga_remote_follow(session: Optional[AsyncSession]) -> Dict[str, Any]:
    """
    MANGA-SOURCE-PHASE-2-P3 远程追更支持
    
    添加远程追更支持字段到 UserMangaFollow 模型
    """
    if session is None:
        raise RuntimeError("MANGA-SOURCE-PHASE-2-P3 迁移需要数据库会话")
    
    from sqlalchemy import text
    
    # 迁移步骤
    migrations = [
        # 添加 remote_follow 字段
        """
        ALTER TABLE user_manga_follow 
        ADD COLUMN IF NOT EXISTS remote_follow BOOLEAN DEFAULT FALSE
        """,
    ]
    
    # 执行迁移
    for migration in migrations:
        try:
            await session.execute(text(migration))
            await session.commit()
        except Exception as e:
            await session.rollback()
            # 字段可能已存在，忽略错误
            print(f"MANGA-SOURCE-PHASE-2-P3 migration warning: {e}")
    
    return {"status": "checked", "features": ["remote_follow"]}


async def _run_subs_rules_p1_filter_rule_groups(session: Optional[AsyncSession]) -> Dict[str, Any]:
    """
    SUBS-RULES-1-P1 过滤规则组表创建
    
    创建 FilterRuleGroup 表用于订阅规则中心
    """
    if session is None:
        raise RuntimeError("SUBS-RULES-1-P1 迁移需要数据库会话")
    
    from app.models.filter_rule_group import FilterRuleGroup
    
    try:
        # 使用 run_sync 包装同步的 metadata 操作
        await session.run_sync(lambda sync_session: FilterRuleGroup.metadata.create_all(sync_session.bind))
        await session.commit()
    except Exception as e:
        await session.rollback()
        print(f"FilterRuleGroup table creation warning: {e}")
    
    return {"status": "checked", "features": ["filter_rule_groups_table"]}


def get_migration_steps() -> List[MigrationStep]:
    """返回当前注册的迁移步骤（按执行顺序）。"""

    return [
        MigrationStep(
            id="short_drama_columns",
            title="短剧相关列补齐",
            description="确保 download_tasks/subscriptions/media 包含短剧字段",
            requires_session=False,
            runner=_run_short_drama,
        ),
        MigrationStep(
            id="music_subscription_link",
            title="音乐订阅字段补齐",
            description="为 music_subscriptions 自动补充 subscription_id 等列",
            requires_session=False,
            runner=_run_music,
        ),
        MigrationStep(
            id="rsshub_health_columns",
            title="RSSHub 健康字段补齐",
            description="确保 user_rsshub_subscription 带有健康检查字段",
            requires_session=True,
            runner=_run_rsshub,
        ),
        MigrationStep(
            id="plugin_safety_features",
            title="PLUGIN-SAFETY-1 安全特性",
            description="添加插件健康状态字段和审计日志表",
            requires_session=True,
            runner=_run_plugin_safety,
        ),
        MigrationStep(
            id="plugin_remote_features",
            title="PLUGIN-REMOTE-1 远程插件支持",
            description="添加远程插件类型、配置和行为统计字段",
            requires_session=True,
            runner=_run_plugin_remote,
        ),
        MigrationStep(
            id="video_autoloop_p1",
            title="VIDEO-AUTOLOOP-1-P1 影视订阅模型扩展",
            description="扩展 Subscription 模型，添加用户归属和安全策略字段",
            requires_session=True,
            runner=_run_video_autoloop_p1,
        ),
        MigrationStep(
            id="manga_remote_follow",
            title="MANGA-SOURCE-PHASE-2-P3 远程追更支持",
            description="添加远程追更支持字段到 UserMangaFollow 模型",
            requires_session=True,
            runner=_run_manga_remote_follow,
        ),
        MigrationStep(
            id="subs_rules_p1_filter_rule_groups",
            title="SUBS-RULES-1-P1 过滤规则组表创建",
            description="创建 FilterRuleGroup 表用于订阅规则中心",
            requires_session=True,
            runner=_run_subs_rules_p1_filter_rule_groups,
        ),
    ]


