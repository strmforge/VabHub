"""
Plugin Git Service
PLUGIN-HUB-2 实现

Git 操作封装：克隆、拉取、获取版本等
"""

import asyncio
import re
import shutil
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from loguru import logger

from app.core.config import settings


# ==================== 异常类 ====================

class PluginGitError(Exception):
    """Git 操作基础异常"""
    pass


class PluginInstallError(PluginGitError):
    """插件安装失败"""
    pass


class PluginUpdateError(PluginGitError):
    """插件更新失败"""
    pass


class PluginUninstallError(PluginGitError):
    """插件卸载失败"""
    pass


class RepoNotAllowedError(PluginGitError):
    """仓库地址不在白名单中"""
    pass


class PathTraversalError(PluginGitError):
    """路径穿越检测"""
    pass


# ==================== 路径安全 ====================

# 允许的插件 ID 字符
PLUGIN_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]+$')


def sanitize_plugin_id(plugin_id: str) -> str:
    """
    清理插件 ID，只保留安全字符
    
    Args:
        plugin_id: 原始插件 ID
        
    Returns:
        清理后的插件 ID
        
    Raises:
        ValueError: 如果插件 ID 无效
    """
    if not plugin_id:
        raise ValueError("Plugin ID cannot be empty")
    
    # 检查是否只包含允许的字符
    if not PLUGIN_ID_PATTERN.match(plugin_id):
        # 替换不允许的字符为 -
        sanitized = re.sub(r'[^a-zA-Z0-9_\-\.]', '-', plugin_id)
        logger.warning(f"[plugin-git] Sanitized plugin ID: {plugin_id} -> {sanitized}")
        return sanitized
    
    return plugin_id


def get_plugins_root() -> Path:
    """
    获取插件根目录的绝对路径
    
    Returns:
        插件根目录的绝对路径
    """
    plugins_dir = settings.PLUGINS_DIR
    
    if Path(plugins_dir).is_absolute():
        return Path(plugins_dir).resolve()
    
    # 相对于 backend 目录
    # backend/app/services/plugin_git_service.py -> backend/
    base_dir = Path(__file__).parent.parent.parent
    return (base_dir / plugins_dir).resolve()


def get_plugin_dir(plugin_id: str) -> Path:
    """
    安全获取插件目录路径
    
    Args:
        plugin_id: 插件 ID
        
    Returns:
        插件目录的绝对路径
        
    Raises:
        PathTraversalError: 如果检测到路径穿越
    """
    root = get_plugins_root()
    name = sanitize_plugin_id(plugin_id)
    target = (root / name).resolve()
    
    # 路径穿越检查
    if root != target and root not in target.parents:
        raise PathTraversalError(f"Invalid plugin id, path traversal detected: {plugin_id}")
    
    return target


# ==================== Git Host 白名单 ====================

def extract_host_from_url(repo_url: str) -> str:
    """
    从仓库地址中提取主机名
    
    支持格式：
    - https://github.com/owner/repo
    - git@github.com:owner/repo.git
    - ssh://git@github.com/owner/repo
    
    Args:
        repo_url: 仓库地址
        
    Returns:
        主机名（小写）
    """
    if not repo_url:
        return ""
    
    # 处理 git@host:path 格式
    if repo_url.startswith("git@"):
        # git@github.com:owner/repo.git -> github.com
        parts = repo_url[4:].split(":")
        return parts[0].lower() if parts else ""
    
    # 处理标准 URL 格式
    parsed = urlparse(repo_url)
    host = parsed.netloc or ""
    
    # 移除端口号
    if ":" in host:
        host = host.split(":")[0]
    
    # 移除用户名
    if "@" in host:
        host = host.split("@")[-1]
    
    return host.lower()


def ensure_repo_allowed(repo_url: str) -> None:
    """
    检查仓库地址是否在白名单中
    
    Args:
        repo_url: 仓库地址
        
    Raises:
        RepoNotAllowedError: 如果仓库主机不在白名单中
    """
    if not repo_url:
        raise RepoNotAllowedError("Repository URL is empty")
    
    host = extract_host_from_url(repo_url)
    allowed_hosts = [h.strip().lower() for h in settings.PLUGIN_GIT_ALLOWED_HOSTS if h.strip()]
    
    if not allowed_hosts:
        raise RepoNotAllowedError("No allowed Git hosts configured")
    
    if host not in allowed_hosts:
        raise RepoNotAllowedError(
            f"Repository host '{host}' is not in allowed list. "
            f"Allowed hosts: {', '.join(allowed_hosts)}"
        )
    
    logger.debug(f"[plugin-git] Repo host '{host}' is allowed")


# ==================== Git 命令封装 ====================

async def run_git(args: list[str], cwd: Optional[Path] = None) -> str:
    """
    异步执行 git 命令
    
    Args:
        args: git 命令参数（不包括 'git' 本身）
        cwd: 工作目录
        
    Returns:
        命令标准输出
        
    Raises:
        PluginGitError: 如果命令执行失败
    """
    cmd = ["git"] + args
    cmd_str = " ".join(cmd)
    
    logger.info(f"[plugin-git] Running: {cmd_str}" + (f" in {cwd}" if cwd else ""))
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace").strip()
            logger.error(f"[plugin-git] Command failed: {cmd_str}\n{error_msg}")
            raise PluginGitError(f"Git command failed: {error_msg}")
        
        return stdout.decode("utf-8", errors="replace").strip()
        
    except FileNotFoundError:
        raise PluginGitError("Git is not installed or not in PATH")
    except Exception as e:
        if isinstance(e, PluginGitError):
            raise
        raise PluginGitError(f"Git command error: {e}")


async def git_clone(
    repo_url: str,
    dest: Path,
    branch: Optional[str] = None,
) -> None:
    """
    克隆 Git 仓库
    
    Args:
        repo_url: 仓库地址
        dest: 目标目录
        branch: 分支名（可选）
        
    Raises:
        RepoNotAllowedError: 如果仓库不在白名单中
        PluginInstallError: 如果克隆失败
    """
    # 检查白名单
    ensure_repo_allowed(repo_url)
    
    # 确保父目录存在
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    # 如果目标目录已存在，报错
    if dest.exists():
        raise PluginInstallError(f"Destination directory already exists: {dest}")
    
    # 构建 clone 命令
    args = ["clone", "--depth", "1"]  # 浅克隆
    
    # 分支参数
    effective_branch = branch or settings.PLUGIN_GIT_DEFAULT_BRANCH
    if effective_branch:
        args.extend(["-b", effective_branch])
    
    args.extend([repo_url, str(dest)])
    
    try:
        await run_git(args)
        logger.info(f"[plugin-git] Successfully cloned {repo_url} to {dest}")
    except PluginGitError as e:
        # 清理失败的克隆
        if dest.exists():
            shutil.rmtree(dest, ignore_errors=True)
        raise PluginInstallError(f"Failed to clone repository: {e}")


async def git_pull(dest: Path, branch: Optional[str] = None) -> None:
    """
    拉取最新代码
    
    Args:
        dest: 插件目录
        branch: 分支名（可选）
        
    Raises:
        PluginUpdateError: 如果拉取失败
    """
    if not dest.exists():
        raise PluginUpdateError(f"Plugin directory does not exist: {dest}")
    
    if not (dest / ".git").exists():
        raise PluginUpdateError(f"Not a git repository: {dest}")
    
    try:
        # 先 fetch
        await run_git(["fetch", "--depth", "1", "origin"], cwd=dest)
        
        # 确定分支
        effective_branch = branch or settings.PLUGIN_GIT_DEFAULT_BRANCH
        
        if effective_branch:
            # reset 到指定分支
            await run_git(["reset", "--hard", f"origin/{effective_branch}"], cwd=dest)
        else:
            # 使用当前分支
            current_branch = await run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=dest)
            await run_git(["reset", "--hard", f"origin/{current_branch}"], cwd=dest)
        
        logger.info(f"[plugin-git] Successfully pulled updates for {dest}")
        
    except PluginGitError as e:
        raise PluginUpdateError(f"Failed to pull updates: {e}")


async def git_current_rev(dest: Path) -> str:
    """
    获取当前 commit hash
    
    Args:
        dest: 插件目录
        
    Returns:
        短 commit hash
    """
    if not dest.exists() or not (dest / ".git").exists():
        return ""
    
    try:
        return await run_git(["rev-parse", "--short", "HEAD"], cwd=dest)
    except PluginGitError:
        return ""


async def git_remote_url(dest: Path) -> Optional[str]:
    """
    获取远程仓库地址
    
    Args:
        dest: 插件目录
        
    Returns:
        远程仓库地址或 None
    """
    if not dest.exists() or not (dest / ".git").exists():
        return None
    
    try:
        return await run_git(["remote", "get-url", "origin"], cwd=dest)
    except PluginGitError:
        return None


def remove_plugin_dir(dest: Path) -> None:
    """
    删除插件目录
    
    Args:
        dest: 插件目录
        
    Raises:
        PluginUninstallError: 如果删除失败
    """
    if not dest.exists():
        logger.warning(f"[plugin-git] Directory does not exist: {dest}")
        return
    
    # 确保在 plugins root 内
    root = get_plugins_root()
    if root not in dest.parents and root != dest:
        raise PluginUninstallError(f"Cannot remove directory outside plugins root: {dest}")
    
    try:
        shutil.rmtree(dest)
        logger.info(f"[plugin-git] Successfully removed {dest}")
    except Exception as e:
        raise PluginUninstallError(f"Failed to remove plugin directory: {e}")
