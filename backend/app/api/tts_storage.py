"""
TTS 存储管理 Dev API

提供 TTS 存储目录的统计和清理功能（仅 Dev 环境）
"""

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.modules.tts.storage_service import (
    scan_storage,
    build_overview,
    build_cleanup_plan,
    build_cleanup_plan_from_policy,
    execute_cleanup,
)
from app.modules.tts.storage_policy import get_default_storage_policy
from app.modules.tts.storage_runner import run_scheduled_cleanup
from app.schemas.tts import (
    TTSStorageOverviewResponse,
    TTSStorageCategoryStats,
    TTSStorageCleanupPreviewRequest,
    TTSStorageCleanupPreviewResponse,
    TTSStorageCleanupPreviewItem,
    TTSStorageCleanupExecuteRequest,
    TTSStorageCleanupExecuteResponse,
    TTSStoragePolicyResponse,
    TTSStorageCategoryPolicySchema,
    TTSStorageAutoRunRequest,
    TTSStorageAutoRunResponse,
)

router = APIRouter(prefix="/tts/storage", tags=["TTS存储（Dev）"])


def _ensure_debug():
    """确保在 Debug 模式下"""
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="TTS storage tools are Dev-only"
        )


@router.get("/policy", response_model=TTSStoragePolicyResponse, summary="获取 TTS 存储策略")
async def get_storage_policy():
    """
    获取当前 TTS 存储策略
    """
    _ensure_debug()
    
    try:
        policy = get_default_storage_policy(settings)
        
        return TTSStoragePolicyResponse(
            name=policy.name,
            playground=TTSStorageCategoryPolicySchema(
                min_keep_days=policy.playground.min_keep_days,
                min_keep_files=policy.playground.min_keep_files,
                max_keep_files=policy.playground.max_keep_files
            ),
            job=TTSStorageCategoryPolicySchema(
                min_keep_days=policy.job.min_keep_days,
                min_keep_files=policy.job.min_keep_files,
                max_keep_files=policy.job.max_keep_files
            ),
            other=TTSStorageCategoryPolicySchema(
                min_keep_days=policy.other.min_keep_days,
                min_keep_files=policy.other.min_keep_files,
                max_keep_files=policy.other.max_keep_files
            )
        )
    except Exception as e:
        logger.error(f"Failed to get storage policy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage policy: {str(e)}"
        )


@router.get("/overview", response_model=TTSStorageOverviewResponse, summary="获取 TTS 存储概览")
async def get_tts_storage_overview():
    """
    获取 TTS 存储目录的统计信息
    """
    _ensure_debug()
    
    root = Path(settings.SMART_TTS_OUTPUT_ROOT)
    
    try:
        # 扫描文件
        files = scan_storage(root)
        
        # 构建概览
        overview = build_overview(files, root)
        
        # 转换为响应格式
        by_category = {
            cat: TTSStorageCategoryStats(
                files=stats["files"],
                size_bytes=stats["size_bytes"]
            )
            for cat, stats in overview.by_category.items()
        }
        
        return TTSStorageOverviewResponse(
            root=str(overview.root),
            total_files=overview.total_files,
            total_size_bytes=overview.total_size_bytes,
            by_category=by_category
        )
    except Exception as e:
        logger.error(f"Failed to get TTS storage overview: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage overview: {str(e)}"
        )


@router.post("/preview", response_model=TTSStorageCleanupPreviewResponse, summary="预览清理计划")
async def preview_cleanup(req: TTSStorageCleanupPreviewRequest):
    """
    预览清理计划，不实际删除文件
    
    支持两种模式：
    - manual: 手动参数模式，使用 scope/min_age_days/max_files 参数
    - policy: 按策略推荐模式，使用默认策略自动计算清理集合
    """
    _ensure_debug()
    
    root = Path(settings.SMART_TTS_OUTPUT_ROOT)
    
    try:
        used_policy = False
        policy_name = None
        
        if req.mode == "policy":
            # 策略模式：使用策略生成清理计划
            policy = get_default_storage_policy(settings)
            policy_name = policy.name
            
            # 扫描所有文件
            all_files = scan_storage(root, max_files=None)
            
            # 使用策略生成清理计划
            plan = build_cleanup_plan_from_policy(all_files, root, policy)
            used_policy = True
        else:
            # 手动模式：使用原有逻辑
            plan = build_cleanup_plan(
                root=root,
                scope=req.scope.value,
                min_age_days=req.min_age_days,
                max_files=req.max_files
            )
        
        # 构建预览项（只返回前 N 条作为示例）
        sample_size = min(100, len(plan.matched_files))  # 最多返回 100 条示例
        sample = [
            TTSStorageCleanupPreviewItem(
                path=str(f.path),
                size_bytes=f.size_bytes,
                mtime=f.mtime,
                category=f.category
            )
            for f in plan.matched_files[:sample_size]
        ]
        
        return TTSStorageCleanupPreviewResponse(
            root=str(root),
            total_matched_files=plan.total_deleted_files,
            total_freed_bytes=plan.total_freed_bytes,
            sample=sample,
            used_policy=used_policy,
            policy_name=policy_name
        )
    except Exception as e:
        logger.error(f"Failed to preview cleanup: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview cleanup: {str(e)}"
        )


@router.post("/cleanup", response_model=TTSStorageCleanupExecuteResponse, summary="执行清理")
async def run_cleanup(req: TTSStorageCleanupExecuteRequest):
    """
    执行清理操作
    
    支持两种模式：
    - manual: 手动参数模式
    - policy: 按策略推荐模式
    
    支持 dry_run 模式（预览模式，不实际删除）
    """
    _ensure_debug()
    
    root = Path(settings.SMART_TTS_OUTPUT_ROOT)
    
    try:
        if req.mode == "policy":
            # 策略模式：使用策略生成清理计划
            policy = get_default_storage_policy(settings)
            
            # 扫描所有文件
            all_files = scan_storage(root, max_files=None)
            
            # 使用策略生成清理计划
            plan = build_cleanup_plan_from_policy(all_files, root, policy)
        else:
            # 手动模式：使用原有逻辑
            plan = build_cleanup_plan(
                root=root,
                scope=req.scope.value,
                min_age_days=req.min_age_days,
                max_files=req.max_files
            )
        
        # 执行清理
        result_plan = execute_cleanup(plan, dry_run=req.dry_run)
        
        if req.dry_run:
            message = f"Dry-run: would delete {result_plan.total_deleted_files} files, " \
                     f"free {result_plan.total_freed_bytes} bytes"
        else:
            message = f"Deleted {result_plan.total_deleted_files} files, " \
                     f"freed {result_plan.total_freed_bytes} bytes"
        
        return TTSStorageCleanupExecuteResponse(
            root=str(root),
            deleted_files=result_plan.total_deleted_files,
            freed_bytes=result_plan.total_freed_bytes,
            dry_run=req.dry_run,
            message=message
        )
    except Exception as e:
        logger.error(f"Failed to run cleanup: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run cleanup: {str(e)}"
        )


def _build_human_message(result) -> str:
    """构建人类可读的消息"""
    if result.status == "success":
        if result.dry_run:
            return f"预览模式：将删除 {result.deleted_files_count} 个文件，释放 {result.freed_bytes / (1024**2):.2f} MB"
        else:
            return f"清理完成：删除了 {result.deleted_files_count} 个文件，释放了 {result.freed_bytes / (1024**2):.2f} MB"
    elif result.status == "skipped":
        reason_map = {
            "auto_disabled": "自动清理未启用",
            "too_soon": "距离上次执行时间太短",
            "below_warn": "存储占用未达到警告级别",
            "no_root": "存储根目录不存在",
            "scan_error": "扫描存储目录失败",
            "nothing_to_clean": "没有需要清理的文件",
            "plan_error": "构建清理计划失败",
            "dry_run": "预览模式（未实际删除）"
        }
        reason_text = reason_map.get(result.reason, result.reason or "未知原因")
        return f"跳过清理：{reason_text}"
    else:  # failed
        return f"清理失败：{result.reason or '未知错误'}"


@router.post("/auto-run", response_model=TTSStorageAutoRunResponse, summary="执行自动清理（Dev）")
async def auto_run_cleanup(
    req: TTSStorageAutoRunRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    执行一次自动清理
    
    此接口用于外部定时器（cron/systemd timer）调用，或 Dev 页面手动触发。
    根据配置和策略自动决定是否执行清理。
    """
    _ensure_debug()
    
    try:
        result = await run_scheduled_cleanup(
            db=db,
            settings=settings,
            dry_run_override=req.dry_run,
            force=req.force,
        )
        
        return TTSStorageAutoRunResponse(
            success=(result.status == "success"),
            status=result.status,
            reason=result.reason,
            deleted_files_count=result.deleted_files_count,
            freed_bytes=result.freed_bytes,
            dry_run=result.dry_run,
            started_at=result.started_at,
            finished_at=result.finished_at,
            message=_build_human_message(result),
        )
    except Exception as e:
        logger.error(f"Failed to run auto cleanup: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run auto cleanup: {str(e)}"
        )

