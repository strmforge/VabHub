"""
漫画源服务：封装连接测试与库预览逻辑
"""

from typing import List, Tuple

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.manga_source import MangaSource
from app.modules.manga_sources.factory import get_manga_source_adapter
from app.schemas.manga_source import MangaLibraryInfo


async def get_manga_source_or_none(db: AsyncSession, source_id: int) -> MangaSource | None:
    """根据 ID 获取 MangaSource，找不到则返回 None。"""
    stmt = select(MangaSource).where(MangaSource.id == source_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def test_connection(
    db: AsyncSession,
    source_id: int,
) -> Tuple[bool, str, List[MangaLibraryInfo]]:
    """测试指定漫画源的连接，并尽量返回库/书架列表。

    返回 (ok, message, libraries)
    """

    source = await get_manga_source_or_none(db, source_id)
    if not source:
        return False, f"漫画源不存在 (ID: {source_id})", []

    adapter = get_manga_source_adapter(source)

    try:
        ok = await adapter.ping()
    except Exception as e:  # pragma: no cover - 防御性日志
        logger.error(f"Ping manga source failed (id={source_id}): {e}", exc_info=True)
        return False, f"连接测试失败: {e}", []

    if not ok:
        return False, "无法连接到漫画源，请检查地址和凭证", []

    # 尝试列出库/书架列表
    libraries: List[MangaLibraryInfo] = []
    try:
        libraries = await adapter.list_libraries()
    except Exception as e:  # pragma: no cover - 防御性日志
        logger.warning(
            f"List libraries failed for manga source (id={source_id}): {e}",
            exc_info=True,
        )
        # 连接成功但无法列出库，视为次要问题
        return True, "连接成功，但获取库列表失败，请检查服务配置", []

    names_preview = ", ".join(lib.name for lib in libraries[:5]) if libraries else "无库"
    msg = (
        f"连接成功，找到 {len(libraries)} 个库/书架"
        + (f"：{names_preview}" if libraries else "")
    )
    return True, msg, libraries
