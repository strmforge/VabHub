"""
历史数据迁移脚本：强制将书籍类型的目录配置的 enable_strm 设置为 False

使用方法：
    python -m scripts.migrate_directory_strm_for_books
"""
import asyncio
from sqlalchemy import update
from loguru import logger

from app.core.database import AsyncSessionLocal
from app.models.directory import Directory
from app.models.enums.media_type import MediaType


async def migrate():
    """执行迁移"""
    async with AsyncSessionLocal() as db:
        try:
            # 查找所有 media_type='book' 且 enable_strm=True 的记录
            result = await db.execute(
                update(Directory)
                .where(
                    Directory.media_type == MediaType.BOOK,
                    Directory.enable_strm == True
                )
                .values(enable_strm=False)
            )
            
            affected_rows = result.rowcount
            await db.commit()
            
            if affected_rows > 0:
                logger.info(f"迁移完成：已将 {affected_rows} 条书籍类型目录配置的 enable_strm 设置为 False")
            else:
                logger.info("迁移完成：没有需要更新的记录")
                
        except Exception as e:
            await db.rollback()
            logger.error(f"迁移失败: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    asyncio.run(migrate())

