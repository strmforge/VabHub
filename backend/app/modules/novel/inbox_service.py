"""
小说 Inbox 扫描服务

提供独立的小说 Inbox 扫描功能，可被 CLI 或 Organizer 调用
"""
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import Settings
from app.models.novel_inbox_import_log import NovelInboxImportLog, NovelInboxStatus
from app.modules.inbox.router import InboxRouter
from app.modules.inbox.models import InboxItem


@dataclass
class NovelInboxScanResult:
    """小说 Inbox 扫描结果"""
    scanned_files: int  # 扫描到的文件数
    imported_count: int  # 成功导入数
    skipped_already_imported: int  # 已导入跳过数
    skipped_failed_before: int  # 之前失败跳过数
    skipped_unsupported: int  # 不支持格式跳过数
    tts_jobs_created: int  # 创建的 TTS Job 数
    failed_count: int  # 失败数


async def scan_novel_inbox_for_root(
    db: AsyncSession,
    settings: Settings,
    root_dir: Path,
    generate_tts: bool = False,
    max_files: Optional[int] = None,
) -> NovelInboxScanResult:
    """
    扫描指定目录中的小说文件并导入
    
    Args:
        db: 数据库会话
        settings: 应用配置
        root_dir: 要扫描的根目录
        generate_tts: 是否自动创建 TTS Job
        max_files: 最多处理文件数（None 表示不限制）
    
    Returns:
        NovelInboxScanResult: 扫描结果
    """
    if not root_dir.exists():
        logger.warning(f"扫描目录不存在: {root_dir}")
        return NovelInboxScanResult(
            scanned_files=0,
            imported_count=0,
            skipped_already_imported=0,
            skipped_failed_before=0,
            skipped_unsupported=0,
            tts_jobs_created=0,
            failed_count=0
        )
    
    # 支持的扩展名
    supported_extensions = {'.txt', '.epub'}
    
    # 扫描文件
    candidate_files: List[Path] = []
    for ext in supported_extensions:
        candidate_files.extend(root_dir.rglob(f'*{ext}'))
    
    # 限制数量
    if max_files and len(candidate_files) > max_files:
        logger.info(f"发现 {len(candidate_files)} 个文件，限制为 {max_files} 个")
        candidate_files = candidate_files[:max_files]
    
    logger.info(f"扫描到 {len(candidate_files)} 个候选文件")
    
    # 创建 InboxRouter
    router = InboxRouter(db=db)
    
    # 统计结果
    result = NovelInboxScanResult(
        scanned_files=len(candidate_files),
        imported_count=0,
        skipped_already_imported=0,
        skipped_failed_before=0,
        skipped_unsupported=0,
        tts_jobs_created=0,
        failed_count=0
    )
    
    # 处理每个文件
    for file_path in candidate_files:
        try:
            # 检查扩展名
            if file_path.suffix.lower() not in supported_extensions:
                result.skipped_unsupported += 1
                continue
            
            # 创建 InboxItem
            item = InboxItem(
                path=file_path,
                source_tags=None,
                download_task_id=None,
                source_site_id=None,
                source_site_name=None,
                source_category=None
            )
            
            # 检查是否已导入
            original_path_str = str(file_path.resolve())
            existing_log_stmt = select(NovelInboxImportLog).where(
                NovelInboxImportLog.original_path == original_path_str
            )
            existing_log_result = await db.execute(existing_log_stmt)
            existing_log = existing_log_result.scalar_one_or_none()
            
            if existing_log:
                if existing_log.status == NovelInboxStatus.SUCCESS:
                    result.skipped_already_imported += 1
                    logger.debug(f"已导入，跳过: {file_path}")
                    continue
                elif existing_log.status == NovelInboxStatus.FAILED:
                    result.skipped_failed_before += 1
                    logger.debug(f"之前失败，跳过: {file_path}")
                    continue
            
            # 调用 router 处理（对于 TXT，会走 _handle_novel_txt）
            # 注意：这里需要模拟 MediaTypeGuess，或者直接调用 _handle_novel_txt
            # 简化处理：只处理 .txt，.epub 暂时跳过（需要额外处理）
            if file_path.suffix.lower() == '.txt':
                # 直接调用 _handle_novel_txt
                route_result = await router._handle_novel_txt(item, generate_tts_job=generate_tts)
                
                if route_result.startswith("handled:novel_txt"):
                    result.imported_count += 1
                    if ":tts_job_created" in route_result:
                        result.tts_jobs_created += 1
                elif route_result.startswith("skipped:"):
                    if "already_imported" in route_result:
                        result.skipped_already_imported += 1
                    elif "failed_before" in route_result:
                        result.skipped_failed_before += 1
                    else:
                        result.skipped_unsupported += 1
                else:
                    result.failed_count += 1
                    logger.warning(f"处理失败: {file_path}, 结果: {route_result}")
            elif file_path.suffix.lower() == '.epub':
                # EPUB 暂时跳过（需要额外实现）
                result.skipped_unsupported += 1
                logger.debug(f"EPUB 格式暂不支持，跳过: {file_path}")
            
        except Exception as e:
            logger.error(f"处理文件失败: {file_path}, 错误: {e}", exc_info=True)
            result.failed_count += 1
    
    logger.info(
        f"小说 Inbox 扫描完成: "
        f"扫描 {result.scanned_files} 个，"
        f"导入 {result.imported_count} 个，"
        f"跳过已导入 {result.skipped_already_imported} 个，"
        f"跳过之前失败 {result.skipped_failed_before} 个，"
        f"跳过不支持 {result.skipped_unsupported} 个，"
        f"失败 {result.failed_count} 个，"
        f"创建 TTS Job {result.tts_jobs_created} 个"
    )
    
    return result

