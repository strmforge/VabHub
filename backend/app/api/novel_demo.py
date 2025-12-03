"""
小说导入 Demo API（开发用）

提供本地 TXT 文件导入为电子书的演示接口。
注意：此 API 仅用于开发/演示，不涉及任何网站爬虫。
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from loguru import logger
import uuid
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.schemas import success_response, error_response
from app.core.config import settings
from app.modules.novel.sources.local_txt import LocalTxtNovelSourceAdapter
from app.modules.novel.epub_builder import EpubBuilder
from app.modules.novel.pipeline import NovelToEbookPipeline
from app.modules.novel.models import NovelMetadata
from app.modules.ebook.importer import EBookImporter

router = APIRouter()


class ImportLocalTxtRequest(BaseModel):
    """本地 TXT 文件导入请求"""
    file_path: str  # 后端可访问的本地绝对路径或相对路径
    title: Optional[str] = None  # 书名（如果为空，从文件名推断）
    author: Optional[str] = None  # 作者
    description: Optional[str] = None  # 简介
    encoding: Optional[str] = "utf-8"  # 文件编码
    generate_audiobook: bool = False  # 是否生成有声书（需要 TTS 启用）


class ImportLocalTxtResponse(BaseModel):
    """本地 TXT 文件导入响应"""
    success: bool
    ebook_path: str  # 生成的电子书文件路径
    ebook_id: Optional[int] = None  # 新建或复用的 EBook ID
    audiobook_created: bool = False  # 是否生成了有声书
    audiobook_files_count: int = 0  # 生成的有声书文件数量
    message: str


class UploadTxtNovelResponse(BaseModel):
    """上传 TXT 小说响应"""
    success: bool
    ebook_path: str  # 生成的电子书文件路径
    ebook_id: Optional[int] = None  # 新建或复用的 EBook ID
    audiobook_created: bool = False  # 是否生成了有声书
    audiobook_files_count: int = 0  # 生成的有声书文件数量
    message: str


@router.post("/import-local-txt", response_model=ImportLocalTxtResponse)
async def import_local_txt(
    request: ImportLocalTxtRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    从本地 TXT 文件导入小说为电子书（Demo 用）
    
    此接口仅用于开发/演示，不涉及任何网站爬虫。
    只处理本地文件系统上的 TXT 文件。
    
    Args:
        request: 导入请求（包含文件路径和元数据）
        db: 数据库会话
    
    Returns:
        ImportLocalTxtResponse: 导入结果
    """
    try:
        # 步骤 1: 验证文件路径
        file_path = Path(request.file_path)
        
        # 如果是相对路径，尝试从项目根目录解析
        if not file_path.is_absolute():
            # 可以基于 settings 或其他配置来确定基础路径
            # 这里简单处理：如果文件不存在，尝试从当前工作目录查找
            if not file_path.exists():
                file_path = Path.cwd() / file_path
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="FILE_NOT_FOUND",
                    error_message=f"文件不存在: {request.file_path}"
                ).model_dump()
            )
        
        if not file_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="INVALID_FILE",
                    error_message=f"路径不是文件: {request.file_path}"
                ).model_dump()
            )
        
        # 步骤 2: 构造元数据
        # 如果 title 为空，从文件名推断
        title = request.title
        if not title:
            title = file_path.stem  # 不含扩展名的文件名
        
        metadata = NovelMetadata(
            title=title,
            author=request.author,
            description=request.description,
            language="zh-CN"  # 默认中文
        )
        
        # 步骤 3: 执行导入流水线（复用内部辅助函数）
        result = await _run_novel_pipeline(
            file_path=file_path,
            metadata=metadata,
            db=db,
            generate_audiobook=request.generate_audiobook
        )
        
        if not result or not result.epub_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(
                    error_code="PIPELINE_FAILED",
                    error_message="小说到电子书流水线执行失败"
                ).model_dump()
            )
        
        ebook_id = result.ebook.id if result.ebook else None
        audiobook_files_count = len(result.audiobook_files) if result.audiobook_files else 0
        
        logger.info(f"本地 TXT 小说导入成功: {result.epub_path}, EBook ID: {ebook_id}, 有声书文件数: {audiobook_files_count}")
        
        return ImportLocalTxtResponse(
            success=True,
            ebook_path=str(result.epub_path),
            ebook_id=ebook_id,
            audiobook_created=audiobook_files_count > 0,
            audiobook_files_count=audiobook_files_count,
            message=f"成功导入小说《{metadata.title}》"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入本地 TXT 小说失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"导入失败: {str(e)}"
            ).model_dump()
        )


def _create_safe_filename(original_filename: str) -> str:
    """
    生成安全的文件名（去除特殊字符，避免路径注入）
    
    Args:
        original_filename: 原始文件名
    
    Returns:
        str: 安全的文件名
    """
    # 提取文件名（不含路径）
    filename = Path(original_filename).name
    
    # 去除扩展名
    stem = Path(filename).stem
    
    # 清理文件名：只保留字母、数字、中文、下划线、连字符
    safe_stem = re.sub(r'[^\w\u4e00-\u9fa5-]', '_', stem)
    
    # 如果清理后为空，使用 UUID
    if not safe_stem:
        safe_stem = str(uuid.uuid4())
    
    # 添加 .txt 扩展名
    return f"{safe_stem}.txt"


async def _run_novel_pipeline(
    file_path: Path,
    metadata: NovelMetadata,
    db: AsyncSession,
    output_dir: Optional[Path] = None,
    generate_audiobook: bool = False
):
    """
    执行小说导入流水线的内部辅助函数
    
    Args:
        file_path: TXT 文件路径
        metadata: 小说元数据
        db: 数据库会话
        output_dir: 输出目录（如果为 None，使用默认目录）
        generate_audiobook: 是否生成有声书
    
    Returns:
        NovelPipelineResult: 包含 epub_path、ebook 和 audiobook_files
    """
    from app.modules.audiobook.importer import AudiobookImporter
    from app.modules.tts.factory import get_tts_engine
    
    # 创建适配器和构建器
    source = LocalTxtNovelSourceAdapter(
        file_path=file_path,
        metadata=metadata,
        encoding="utf-8"
    )
    
    epub_builder = EpubBuilder()
    
    # 确定输出目录
    if output_dir is None:
        output_dir = Path(settings.EBOOK_LIBRARY_ROOT) / "novel_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建导入器
    ebook_importer = EBookImporter(db)
    
    # 创建 TTS 引擎和有声书导入器（如果需要）
    tts_engine = get_tts_engine(settings) if generate_audiobook else None
    audiobook_importer = AudiobookImporter(db) if generate_audiobook else None
    
    # 创建流水线
    pipeline = NovelToEbookPipeline(
        db=db,
        ebook_importer=ebook_importer,
        epub_builder=epub_builder,
        tts_engine=tts_engine,
        audiobook_importer=audiobook_importer,
        settings=settings
    )
    
    # 执行流水线
    logger.info(f"开始导入 TXT 小说: {file_path}, 标题: {metadata.title}, 生成有声书: {generate_audiobook}")
    result = await pipeline.run(source, output_dir, generate_audiobook=generate_audiobook)
    
    return result


@router.post("/upload-txt", response_model=UploadTxtNovelResponse, summary="Dev: 上传本地 TXT 小说并导入为电子书")
async def upload_txt_novel(
    file: UploadFile = File(..., description="TXT 小说文件"),
    title: Optional[str] = Form(None, description="书名（可选，为空则从文件名推断）"),
    author: Optional[str] = Form(None, description="作者（可选）"),
    description: Optional[str] = Form(None, description="简介（可选）"),
    generate_audiobook: bool = Form(False, description="是否生成有声书（需要 TTS 启用）"),
    db: AsyncSession = Depends(get_db)
):
    """
    上传 TXT 文件并导入为电子书（Dev 用）
    
    此接口仅用于开发/演示，支持从浏览器上传 TXT 文件并自动导入到 VabHub。
    
    Args:
        file: 上传的 TXT 文件
        title: 书名（可选）
        author: 作者（可选）
        description: 简介（可选）
        db: 数据库会话
    
    Returns:
        UploadTxtNovelResponse: 导入结果
    """
    try:
        # 步骤 1: 校验文件类型
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="INVALID_FILE",
                    error_message="文件名不能为空"
                ).model_dump()
            )
        
        if not file.filename.lower().endswith('.txt'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="INVALID_FILE_TYPE",
                    error_message="只支持 .txt 文件"
                ).model_dump()
            )
        
        # 步骤 2: 生成安全的文件名
        safe_filename = _create_safe_filename(file.filename)
        
        # 步骤 3: 确保上传目录存在
        upload_root = Path(settings.NOVEL_UPLOAD_ROOT)
        upload_root.mkdir(parents=True, exist_ok=True)
        
        # 步骤 4: 保存上传的文件
        saved_file_path = upload_root / safe_filename
        
        # 如果文件已存在，添加 UUID 后缀避免冲突
        if saved_file_path.exists():
            stem = saved_file_path.stem
            suffix = saved_file_path.suffix
            saved_file_path = upload_root / f"{stem}_{uuid.uuid4().hex[:8]}{suffix}"
        
        # 读取并保存文件内容
        content = await file.read()
        saved_file_path.write_bytes(content)
        
        logger.info(f"已保存上传文件: {saved_file_path}")
        
        # 步骤 5: 构造元数据
        # 如果 title 为空，从文件名推断
        final_title = title
        if not final_title:
            final_title = Path(safe_filename).stem
        
        metadata = NovelMetadata(
            title=final_title,
            author=author,
            description=description,
            language="zh-CN"  # 默认中文
        )
        
        # 步骤 6: 执行导入流水线
        result = await _run_novel_pipeline(
            file_path=saved_file_path,
            metadata=metadata,
            db=db,
            generate_audiobook=generate_audiobook
        )
        
        if not result or not result.epub_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(
                    error_code="PIPELINE_FAILED",
                    error_message="小说到电子书流水线执行失败"
                ).model_dump()
            )
        
        ebook_id = result.ebook.id if result.ebook else None
        audiobook_files_count = len(result.audiobook_files) if result.audiobook_files else 0
        
        # 发送电子书导入完成通知（演示用，使用默认用户ID 1）
        if result.ebook:
            try:
                from app.services.notification_service import notify_ebook_imported
                from app.schemas.notification_reading import create_ebook_imported_payload
                
                # 创建标准化 payload
                ebook_payload = create_ebook_imported_payload(
                    ebook_id=result.ebook.id,
                    title=result.ebook.title,
                    cover_url=result.ebook.cover_url,
                    source_type="txt_upload",
                )
                
                # 发送通知（演示用，发送给默认用户）
                await notify_ebook_imported(
                    session=db,
                    user_id=1,  # 演示用，实际应该从认证上下文获取
                    payload=ebook_payload.dict(),
                )
                
                logger.info(f"Created ebook import notification for ebook {result.ebook.id}")
                
            except Exception as notify_err:
                logger.warning(f"Failed to create ebook import notification: {notify_err}")
                # 不影响主流程
        
        logger.info(f"TXT 小说上传并导入成功: {result.epub_path}, EBook ID: {ebook_id}, 有声书文件数: {audiobook_files_count}")
        
        return UploadTxtNovelResponse(
            success=True,
            ebook_path=str(result.epub_path),
            ebook_id=ebook_id,
            audiobook_created=audiobook_files_count > 0,
            audiobook_files_count=audiobook_files_count,
            message=f"成功导入小说《{metadata.title}》"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传并导入 TXT 小说失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"导入失败: {str(e)}"
            ).model_dump()
        )

