"""
系统健康体检报告服务
OPS-2B 实现
"""

from datetime import datetime
from typing import Literal, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.services.system_health_service import get_health_summary


# 检查项建议字典
CHECK_SUGGESTIONS: dict[str, dict[str, str]] = {
    "db.default": {
        "ok": "数据库连接正常",
        "error": "数据库连接失败，请检查 DATABASE_URL 配置和数据库服务状态",
    },
    "service.redis": {
        "ok": "Redis 缓存连接正常",
        "warning": "Redis 未配置或已禁用，部分缓存功能不可用",
        "error": "Redis 连接失败，请检查 REDIS_URL 配置和 Redis 服务状态",
    },
    "service.download_client": {
        "ok": "下载器连接正常",
        "warning": "未配置下载器，资源下载功能不可用",
        "error": "下载器连接失败，请检查 QB_URL/TR_URL 配置和下载器服务状态",
    },
    "external.indexer": {
        "ok": "外部索引器正常",
        "warning": "无启用的外部索引器，请在管理控制台添加",
        "error": "外部索引器检查失败",
    },
    "disk.data": {
        "ok": "磁盘空间充足",
        "warning": "磁盘空间较低，建议清理或扩容",
        "error": "磁盘空间严重不足，请立即清理或扩容",
    },
}

# 通用建议
DEFAULT_SUGGESTIONS = {
    "ok": "正常运行",
    "warning": "存在告警，建议检查",
    "error": "存在错误，需要处理",
    "unknown": "状态未知，请运行健康检查",
}


def _get_suggestion(key: str, status: str) -> str:
    """获取检查项建议"""
    # 尝试精确匹配
    if key in CHECK_SUGGESTIONS:
        return CHECK_SUGGESTIONS[key].get(status, DEFAULT_SUGGESTIONS.get(status, ""))
    
    # 尝试前缀匹配
    for prefix in ["disk.", "manga_source.", "music_chart_source."]:
        if key.startswith(prefix):
            base_key = prefix.rstrip(".")
            if base_key in CHECK_SUGGESTIONS:
                return CHECK_SUGGESTIONS[base_key].get(status, DEFAULT_SUGGESTIONS.get(status, ""))
    
    return DEFAULT_SUGGESTIONS.get(status, "")


def _get_overall_status_text(status: str) -> str:
    """获取整体状态文本"""
    status_texts = {
        "ok": "✅ 健康",
        "warning": "⚠️ 亚健康",
        "error": "❌ 有问题",
        "unknown": "❓ 未知",
    }
    return status_texts.get(status, status)


async def generate_health_report(
    session: AsyncSession,
    format: Literal["json", "markdown"] = "json",
) -> dict[str, Any] | str:
    """
    生成系统健康体检报告
    
    Args:
        session: 数据库会话
        format: 输出格式 (json/markdown)
        
    Returns:
        JSON 格式返回 dict，Markdown 格式返回 str
    """
    summary = await get_health_summary(session)
    generated_at = datetime.utcnow().isoformat() + "Z"
    
    # 构建检查项列表
    checks_data = []
    for check in summary.checks:
        checks_data.append({
            "key": check.key,
            "status": check.status,
            "checked_at": check.last_checked_at.isoformat() if check.last_checked_at else None,
            "message": check.last_error or _get_suggestion(check.key, check.status),
            "suggestion": _get_suggestion(check.key, check.status) if check.status != "ok" else None,
            "meta": check.meta,
        })
    
    # 构建 Runner 列表
    runners_data = []
    for runner in summary.runners:
        suggestion = None
        if runner.last_exit_code and runner.last_exit_code != 0:
            suggestion = f"上次运行失败，错误: {runner.last_error or '未知'}"
        elif runner.last_started_at is None:
            suggestion = "从未运行过，请检查 Runner 配置"
        
        runners_data.append({
            "name": runner.name,
            "runner_type": runner.runner_type,
            "last_started_at": runner.last_started_at.isoformat() if runner.last_started_at else None,
            "last_finished_at": runner.last_finished_at.isoformat() if runner.last_finished_at else None,
            "last_exit_code": runner.last_exit_code,
            "last_duration_ms": runner.last_duration_ms,
            "suggestion": suggestion,
        })
    
    # JSON 报告
    report = {
        "generated_at": generated_at,
        "overall_status": summary.overall_status,
        "summary": {
            "checks_total": summary.total_checks,
            "checks_ok": summary.ok_count,
            "checks_warning": summary.warning_count,
            "checks_error": summary.error_count,
            "checks_unknown": summary.unknown_count,
        },
        "checks": checks_data,
        "runners": runners_data,
    }
    
    if format == "json":
        return report
    
    # Markdown 报告
    return _format_markdown_report(report)


def _format_markdown_report(report: dict[str, Any]) -> str:
    """格式化 Markdown 报告"""
    lines = [
        "# VabHub 系统健康体检报告",
        "",
        f"**生成时间**: {report['generated_at']}",
        f"**整体状态**: {_get_overall_status_text(report['overall_status'])}",
        "",
        "## 摘要",
        "",
        f"- 检查项总数: {report['summary']['checks_total']}",
        f"- 正常: {report['summary']['checks_ok']}",
        f"- 警告: {report['summary']['checks_warning']}",
        f"- 错误: {report['summary']['checks_error']}",
        f"- 未知: {report['summary']['checks_unknown']}",
        "",
        "## 检查项详情",
        "",
    ]
    
    for check in report["checks"]:
        status_icon = {"ok": "✅", "warning": "⚠️", "error": "❌", "unknown": "❓"}.get(check["status"], "❓")
        lines.append(f"### {status_icon} {check['key']}")
        lines.append("")
        lines.append(f"- **状态**: {check['status'].upper()}")
        if check.get("checked_at"):
            lines.append(f"- **检查时间**: {check['checked_at']}")
        if check.get("message"):
            lines.append(f"- **信息**: {check['message']}")
        if check.get("suggestion"):
            lines.append(f"- **建议**: {check['suggestion']}")
        lines.append("")
    
    lines.append("## Runner 状态")
    lines.append("")
    
    for runner in report["runners"]:
        status_icon = "✅" if runner.get("last_exit_code") == 0 else ("❌" if runner.get("last_exit_code") else "❓")
        lines.append(f"### {status_icon} {runner['name']}")
        lines.append("")
        lines.append(f"- **类型**: {runner.get('runner_type', 'unknown')}")
        if runner.get("last_started_at"):
            lines.append(f"- **最后启动**: {runner['last_started_at']}")
        if runner.get("last_finished_at"):
            lines.append(f"- **最后完成**: {runner['last_finished_at']}")
        if runner.get("last_duration_ms"):
            lines.append(f"- **耗时**: {runner['last_duration_ms']} ms")
        if runner.get("last_exit_code") is not None:
            lines.append(f"- **退出码**: {runner['last_exit_code']}")
        if runner.get("suggestion"):
            lines.append(f"- **建议**: {runner['suggestion']}")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("*此报告由 VabHub 自动生成*")
    
    return "\n".join(lines)
