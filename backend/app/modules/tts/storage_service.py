"""
TTS 存储服务

提供 TTS 存储目录的扫描、统计和清理功能
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Dict, Optional
from datetime import datetime, timedelta, timezone
from loguru import logger

from app.modules.tts.storage_policy import TTSStoragePolicy, TTSStorageCategoryPolicy

TTSFileCategory = Literal["job", "playground", "other"]


@dataclass
class TTSFileInfo:
    """TTS 文件信息"""
    path: Path
    size_bytes: int
    mtime: datetime
    category: TTSFileCategory


@dataclass
class TTSStorageOverview:
    """TTS 存储概览"""
    root: Path
    total_files: int
    total_size_bytes: int
    by_category: Dict[TTSFileCategory, Dict[str, int]]
    # by_category[cat] = {"files": int, "size_bytes": int}


@dataclass
class TTSCleanupPlan:
    """TTS 清理计划"""
    root: Path
    matched_files: List[TTSFileInfo]
    total_deleted_files: int
    total_freed_bytes: int


def _categorize_file(path: Path) -> TTSFileCategory:
    """
    根据文件路径判断类别
    
    规则：
    - playground: 路径包含 /playground/ 或 \playground\
    - job: 路径包含 /jobs/ 或 /job- 前缀
    - other: 其他
    """
    path_str = str(path).replace("\\", "/").lower()
    
    if "playground" in path_str:
        return "playground"
    elif "jobs" in path_str or "/job-" in path_str:
        return "job"
    else:
        return "other"


def scan_storage(root: Path, max_files: Optional[int] = None) -> List[TTSFileInfo]:
    """
    扫描 TTS 存储目录
    
    Args:
        root: TTS 输出根目录
        max_files: 最大扫描文件数（防止极端情况），None 表示不限制
    
    Returns:
        文件信息列表
    """
    files: List[TTSFileInfo] = []
    
    if not root.exists():
        logger.warning(f"TTS storage root does not exist: {root}")
        return files
    
    try:
        for file_path in root.rglob("*"):
            if file_path.is_file():
                try:
                    stat = file_path.stat()
                    category = _categorize_file(file_path)
                    
                    files.append(TTSFileInfo(
                        path=file_path,
                        size_bytes=stat.st_size,
                        mtime=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                        category=category
                    ))
                    
                    # 检查是否达到最大文件数限制
                    if max_files and len(files) >= max_files:
                        logger.warning(f"Reached max_files limit ({max_files}), stopping scan")
                        break
                except (OSError, PermissionError) as e:
                    logger.warning(f"Failed to stat file {file_path}: {e}")
                    continue
    except Exception as e:
        logger.error(f"Error scanning TTS storage: {e}", exc_info=True)
    
    return files


def build_overview(files: List[TTSFileInfo], root: Path) -> TTSStorageOverview:
    """
    构建存储概览
    
    Args:
        files: 文件信息列表
        root: 根目录
    
    Returns:
        存储概览
    """
    total_files = len(files)
    total_size_bytes = sum(f.size_bytes for f in files)
    
    # 按类别聚合
    by_category: Dict[TTSFileCategory, Dict[str, int]] = {
        "job": {"files": 0, "size_bytes": 0},
        "playground": {"files": 0, "size_bytes": 0},
        "other": {"files": 0, "size_bytes": 0}
    }
    
    for file_info in files:
        cat = file_info.category
        by_category[cat]["files"] += 1
        by_category[cat]["size_bytes"] += file_info.size_bytes
    
    return TTSStorageOverview(
        root=root,
        total_files=total_files,
        total_size_bytes=total_size_bytes,
        by_category=by_category
    )


def filter_files_for_cleanup(
    files: List[TTSFileInfo],
    scope: str,  # TTSStorageCleanupScope
    min_age_days: int,
) -> List[TTSFileInfo]:
    """
    根据清理策略过滤文件
    
    Args:
        files: 文件信息列表
        scope: 清理范围（"all", "playground_only", "job_only", "other_only"）
        min_age_days: 最小保留天数
    
    Returns:
        符合条件的文件列表
    """
    now = datetime.now(timezone.utc)
    min_age = timedelta(days=min_age_days)
    
    filtered = []
    
    for file_info in files:
        # 检查类别过滤
        if scope == "playground_only" and file_info.category != "playground":
            continue
        elif scope == "job_only" and file_info.category != "job":
            continue
        elif scope == "other_only" and file_info.category != "other":
            continue
        # scope == "all" 时不过滤类别
        
        # 检查最小保留天数
        age = now - file_info.mtime
        if age >= min_age:
            filtered.append(file_info)
    
    return filtered


def build_cleanup_plan(
    root: Path,
    scope: str,  # TTSStorageCleanupScope
    min_age_days: int,
    max_files: Optional[int] = None,
) -> TTSCleanupPlan:
    """
    构建清理计划
    
    Args:
        root: TTS 输出根目录
        scope: 清理范围
        min_age_days: 最小保留天数
        max_files: 最大匹配文件数（防止一次删太多）
    
    Returns:
        清理计划
    """
    # 扫描文件
    all_files = scan_storage(root, max_files=None)  # 先全扫描，后面再限制匹配数量
    
    # 过滤文件
    matched_files = filter_files_for_cleanup(all_files, scope, min_age_days)
    
    # 限制数量
    if max_files and len(matched_files) > max_files:
        logger.warning(f"Matched {len(matched_files)} files, limiting to {max_files}")
        matched_files = matched_files[:max_files]
    
    total_freed_bytes = sum(f.size_bytes for f in matched_files)
    
    return TTSCleanupPlan(
        root=root,
        matched_files=matched_files,
        total_deleted_files=len(matched_files),
        total_freed_bytes=total_freed_bytes
    )


def build_cleanup_plan_from_policy(
    files: List[TTSFileInfo],
    root: Path,
    policy: TTSStoragePolicy,
) -> TTSCleanupPlan:
    """
    根据策略生成清理计划
    
    对每个类别单独按策略计算：
    1. 按 mtime 降序排序（最新的在前）
    2. 保留最近 min_keep_files 个
    3. 对剩余部分，如果 max_keep_files 有值，则只允许最多 max_keep_files 个，其余候选进删除集合
    4. 同时考虑 min_keep_days：mtime 距今 <= min_keep_days 的文件不删
    
    Args:
        files: 所有文件信息列表
        root: 根目录
        policy: 存储策略
    
    Returns:
        清理计划
    """
    now = datetime.now(timezone.utc)
    matched_files: List[TTSFileInfo] = []
    
    # 按类别分组
    files_by_category: Dict[TTSFileCategory, List[TTSFileInfo]] = {
        "job": [],
        "playground": [],
        "other": []
    }
    
    for file_info in files:
        files_by_category[file_info.category].append(file_info)
    
    # 对每个类别应用策略
    for category in ["job", "playground", "other"]:
        category_files = files_by_category[category]
        if not category_files:
            continue
        
        # 获取该类别的策略
        if category == "job":
            cat_policy = policy.job
        elif category == "playground":
            cat_policy = policy.playground
        else:
            cat_policy = policy.other
        
        # 按 mtime 降序排序（最新的在前）
        category_files.sort(key=lambda f: f.mtime, reverse=True)
        
        # 1. 先保留最近 min_keep_files 个
        keep_files = category_files[:cat_policy.min_keep_files]
        candidate_files = category_files[cat_policy.min_keep_files:]
        
        # 2. 对候选文件，应用 max_keep_files 限制
        if cat_policy.max_keep_files is not None:
            # 计算总共应该保留多少个（包括 min_keep_files）
            total_keep = min(cat_policy.max_keep_files, len(category_files))
            # 如果总数超过 min_keep_files，则从候选文件中再保留一些
            if total_keep > cat_policy.min_keep_files:
                additional_keep = total_keep - cat_policy.min_keep_files
                keep_files.extend(candidate_files[:additional_keep])
                candidate_files = candidate_files[additional_keep:]
        
        # 3. 从候选删除文件中，过滤掉在 min_keep_days 内的文件
        if cat_policy.min_keep_days > 0:
            min_keep_time = now - timedelta(days=cat_policy.min_keep_days)
            for candidate in candidate_files:
                # 如果文件修改时间在保留期内，跳过
                if candidate.mtime >= min_keep_time:
                    continue
                # 否则加入删除列表
                matched_files.append(candidate)
        else:
            # 如果没有 min_keep_days 限制，所有候选文件都可以删除
            matched_files.extend(candidate_files)
    
    # 计算总释放空间
    total_freed_bytes = sum(f.size_bytes for f in matched_files)
    
    return TTSCleanupPlan(
        root=root,
        matched_files=matched_files,
        total_deleted_files=len(matched_files),
        total_freed_bytes=total_freed_bytes
    )


def execute_cleanup(plan: TTSCleanupPlan, dry_run: bool = False) -> TTSCleanupPlan:
    """
    执行清理
    
    Args:
        plan: 清理计划
        dry_run: 是否为预览模式（不实际删除）
    
    Returns:
        更新后的清理计划（包含实际删除的统计）
    """
    if dry_run:
        logger.info(f"Dry-run cleanup: would delete {plan.total_deleted_files} files, "
                   f"free {plan.total_freed_bytes} bytes")
        return plan
    
    deleted_count = 0
    freed_bytes = 0
    errors = []
    
    for file_info in plan.matched_files:
        try:
            if file_info.path.exists():
                file_size = file_info.path.stat().st_size
                file_info.path.unlink()
                deleted_count += 1
                freed_bytes += file_size
                logger.debug(f"Deleted: {file_info.path}")
            else:
                logger.warning(f"File already deleted: {file_info.path}")
        except (OSError, PermissionError) as e:
            error_msg = f"Failed to delete {file_info.path}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    logger.info(
        f"Cleanup completed: deleted {deleted_count}/{plan.total_deleted_files} files, "
        f"freed {freed_bytes} bytes. Errors: {len(errors)}"
    )
    
    if errors:
        logger.warning(f"Cleanup errors: {errors[:10]}")  # 只记录前10个错误
    
    # 更新计划中的实际统计
    plan.total_deleted_files = deleted_count
    plan.total_freed_bytes = freed_bytes
    
    return plan

