"""
数据库连接和会话管理
"""

from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings
from loguru import logger


def _ensure_sqlite_dir(url: str) -> None:
    """
    确保 SQLite 数据库文件的父目录存在
    
    Args:
        url: 数据库连接 URL
    """
    # 仅处理 sqlite / sqlite+aiosqlite
    if not url.startswith("sqlite"):
        return
    
    # 去掉 scheme 部分，获取文件路径
    # 格式可能是: sqlite:///path/to/db 或 sqlite+aiosqlite:///path/to/db
    # 三斜杠后面是相对路径，四斜杠后面是绝对路径
    path_part = url.split("///", 1)
    if len(path_part) < 2 or not path_part[1]:
        return  # 内存数据库或无效路径
    
    db_path = Path(path_part[1])
    
    # 如果路径有父目录且父目录不存在，则创建
    if db_path.parent and db_path.parent != Path("."):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"已创建 SQLite 数据库目录: {db_path.parent}")


# 创建异步数据库引擎
# 默认使用PostgreSQL，如果URL是SQLite则使用SQLite
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite异步支持（用于开发/测试）
    sqlite_url = settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
    
    # 确保 SQLite 数据库目录存在
    _ensure_sqlite_dir(sqlite_url)
    
    engine = create_async_engine(
        sqlite_url,
        echo=settings.DEBUG,
        future=True,
        pool_pre_ping=True
    )
    logger.info("使用SQLite数据库（开发模式）")
else:
    # PostgreSQL异步支持（生产环境推荐）
    # 确保URL格式正确（postgresql:// 或 postgresql+asyncpg://）
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://") and not db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    
    engine = create_async_engine(
        db_url,
        echo=settings.DEBUG,
        future=True,
        pool_pre_ping=True,  # 连接前ping，确保连接有效
        pool_size=5,  # 连接池大小（降低以避免耗尽）
        max_overflow=10,  # 最大溢出连接数
        pool_timeout=30,  # 获取连接超时（秒）
        pool_recycle=1800,  # 30分钟回收连接，防止连接老化
    )
    logger.info("使用PostgreSQL数据库（生产模式，连接池: size=5, overflow=10, timeout=30s, recycle=30min）")

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# 为了向后兼容，提供 async_session_factory 别名
async_session_factory = AsyncSessionLocal

# 创建基础模型类
Base = declarative_base()

# 获取数据库会话的依赖注入函数
async def get_db() -> AsyncSession:
    """获取异步数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# 为兼容性添加别名
get_async_session = get_db
get_session = get_db


async def init_db():
    """初始化数据库"""
    # 导入所有模型以确保它们被注册到Base.metadata
    from app.models.user import User
    from app.models.media import Media, MediaFile
    from app.models.subscription import Subscription
    from app.models.download import DownloadTask
    from app.models.upload import UploadTask, UploadProgress  # 上传任务
    from app.models.workflow import Workflow, WorkflowExecution
    from app.models.site import Site
    from app.models.notification import Notification
    from app.models.music import MusicSubscription, MusicTrack, MusicPlaylist, MusicLibrary, MusicChartRecord
    from app.models.cache import CacheEntry  # L3数据库缓存
    from app.models.identification_history import IdentificationHistory  # 媒体识别历史记录
    from app.models.cloud_storage import CloudStorage, CloudStorageAuth  # 云存储
    from app.models.rss_subscription import RSSSubscription, RSSItem  # RSS订阅
    from app.models.rsshub_simple import RSSHubSourceTemp, RSSHubCompositeTemp, UserRSSHubSubscriptionTemp  # RSSHub集成（简化版本）
    from app.models.subtitle import Subtitle, SubtitleDownloadHistory  # 字幕
    from app.models.multimodal_metrics import (
        MultimodalPerformanceMetric,
        MultimodalPerformanceAlert,
        MultimodalOptimizationHistory
    )  # 多模态分析性能指标
    from app.models.media_server import (
        MediaServer,
        MediaServerSyncHistory,
        MediaServerItem,
        MediaServerPlaybackSession
    )  # 媒体服务器
    from app.models.scheduler_task import (
        SchedulerTask,
        SchedulerTaskExecution
    )
    from app.models.storage_monitor import (
        StorageDirectory,
        StorageUsageHistory,
        StorageAlert
    )  # 存储监控
    from app.models.strm import (
        STRMWorkflowTask,
        STRMFile,
        STRMFileTree,
        STRMLifeEvent,
        STRMConfig
    )  # STRM文件生成系统
    from app.models.directory import Directory  # 目录配置
    from app.models.backup import BackupRecord  # 备份记录
    from app.models.transfer_history import TransferHistory  # 转移历史记录
    from app.models.work_link import WorkLink  # 作品关联（Work Link）
    from app.models.global_rules import GlobalRuleSettings  # 全局规则设置（SETTINGS-RULES-1）
    
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库初始化完成")


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
    logger.info("数据库连接已关闭")

