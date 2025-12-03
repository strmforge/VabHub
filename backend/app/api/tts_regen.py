"""
TTS 重新生成 Dev API

提供手动重新生成 TTS 有声书的功能（仅 Dev 模式）
"""

from fastapi import APIRouter, Depends, HTTPException, Path as PathParam
from typing import Dict, Any
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.models.ebook import EBook
from app.modules.tts.factory import get_tts_engine
from app.modules.tts.work_regen_service import regenerate_tts_for_ebook
from app.modules.audiobook.importer import AudiobookImporter
from app.modules.novel.pipeline import NovelToEbookPipeline
from app.modules.novel.epub_builder import EpubBuilder
from app.modules.ebook.importer import EBookImporter

router = APIRouter()


@router.post("/regenerate-for-work/{ebook_id}", summary="重新生成 TTS 有声书（Dev）")
async def regenerate_tts_for_work(
    ebook_id: int = PathParam(..., description="电子书 ID"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    为指定作品重新生成 TTS 有声书（基于原始 TXT 小说源）
    
    此接口仅在 Dev 模式下可用。
    要求：
    - EBook 必须包含 novel_source 元数据
    - novel_source.type 必须为 "local_txt"
    - archived_txt_path 对应的文件必须存在
    
    Args:
        ebook_id: 电子书 ID
        db: 数据库会话
    
    Returns:
        Dict[str, Any]: 包含 success, status, created_count, skipped_count, message
    """
    # Dev guard（可选，根据项目需要）
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="此接口仅在 DEBUG 模式下可用"
        )
    
    # 1. 获取 EBook
    result = await db.execute(select(EBook).where(EBook.id == ebook_id))
    ebook = result.scalar_one_or_none()
    
    if not ebook:
        raise HTTPException(
            status_code=404,
            detail=f"未找到 ID 为 {ebook_id} 的电子书"
        )
    
    # 2. 获取 TTS 引擎
    try:
        tts_engine = get_tts_engine(settings=settings)
        if not tts_engine:
            return {
                "success": False,
                "status": "tts_engine_unavailable",
                "created_count": 0,
                "skipped_count": 0,
                "message": "TTS 引擎不可用"
            }
    except Exception as e:
        logger.error(f"获取 TTS 引擎失败: {e}", exc_info=True)
        return {
            "success": False,
            "status": "tts_engine_unavailable",
            "created_count": 0,
            "skipped_count": 0,
            "message": f"获取 TTS 引擎失败: {str(e)}"
        }
    
    # 3. 创建必要的组件（用于调用 pipeline 的内部方法）
    audiobook_importer = AudiobookImporter(db=db)
    epub_builder = EpubBuilder()  # 不需要实际使用，但 pipeline 需要
    ebook_importer = EBookImporter(db=db)  # 不需要实际使用，但 pipeline 需要
    
    pipeline = NovelToEbookPipeline(
        db=db,
        ebook_importer=ebook_importer,
        epub_builder=epub_builder,
        tts_engine=tts_engine,
        audiobook_importer=audiobook_importer,
        settings=settings
    )
    
    # 4. 调用重新生成服务
    try:
        result = await regenerate_tts_for_ebook(
            ebook=ebook,
            db=db,
            settings=settings,
            tts_engine=tts_engine,
            audiobook_importer=audiobook_importer,
            pipeline=pipeline
        )
        
        # 5. 构建响应
        success = result.status == "ok"
        return {
            "success": success,
            "status": result.status,
            "created_count": result.created_count,
            "skipped_count": result.skipped_count,
            "message": result.error_message or (
                f"成功创建 {result.created_count} 个有声书文件" if success else result.error_message
            )
        }
        
    except Exception as e:
        logger.exception(f"重新生成 TTS 失败: {e}")
        return {
            "success": False,
            "status": "error",
            "created_count": 0,
            "skipped_count": 0,
            "message": f"重新生成过程中出错: {str(e)}"
        }

