"""
管理员命令
BOT-TELEGRAM Phase 2 + BOT-EXT-1

/admin 相关命令（仅管理员可用）
扩展：alerts, disks, ping, errors
"""

from datetime import datetime
from loguru import logger

from app.modules.bots.telegram_router import router
from app.modules.bots.telegram_context import TelegramUpdateContext
from app.modules.bots.telegram_keyboard import inline_keyboard, inline_button


# ============== /admin ==============

@router.command("/admin")
async def cmd_admin(ctx: TelegramUpdateContext) -> None:
    """管理员命令入口"""
    if not ctx.is_admin:
        await ctx.reply_text("⛔ 此命令仅限管理员使用")
        return
    
    args = ctx.args.strip().lower()
    
    if not args:
        await _show_admin_help(ctx)
    elif args == "health":
        await _cmd_health(ctx)
    elif args == "alerts":
        await _cmd_alerts(ctx)
    elif args == "disks":
        await _cmd_disks(ctx)
    elif args == "ping":
        await _cmd_ping(ctx)
    elif args == "errors":
        await _cmd_errors(ctx)
    elif args == "safety_status":
        await _cmd_safety_status(ctx)
    else:
        await ctx.reply_text(f"❓ 未知的管理员命令: {args}")


async def _cmd_safety_status(ctx: TelegramUpdateContext) -> None:
    """P5-3: 查询安全策略状态"""
    try:
        from app.core.database import AsyncSessionLocal
        from app.modules.safety.settings import SafetySettingsService
        from app.modules.hr_case.repository import get_hr_repository
        
        async with AsyncSessionLocal() as db:
            # 获取安全设置
            safety_service = SafetySettingsService(db)
            global_settings = await safety_service.get_global()
            
            # 获取HR案例统计
            hr_repo = get_hr_repository()
            hr_stats = await hr_repo.get_statistics()
            
            # 构建状态消息
            message = "🛡️ **安全策略状态报告**\n\n"
            
            # 全局设置
            message += f"🔧 **全局设置**:\n"
            message += f"• 安全模式: {global_settings.get('mode', 'SAFE')}\n"
            message += f"• HR保护: {'✅ 启用' if global_settings.get('hr_protection_enabled') else '❌ 禁用'}\n"
            message += f"• 删除最低分享率: {global_settings.get('min_ratio_for_delete', 1.0)}\n"
            message += f"• 最少保种时间: {global_settings.get('min_keep_hours', 72)}小时\n"
            message += f"• HR移动策略: {global_settings.get('hr_move_strategy', 'copy')}\n\n"
            
            # HR案例统计
            message += f"📊 **HR案例统计**:\n"
            message += f"• 总案例数: {hr_stats.get('total', 0)}\n"
            message += f"• 活跃案例: {hr_stats.get('active', 0)}\n"
            message += f"• 已完成案例: {hr_stats.get('completed', 0)}\n"
            message += f"• 高风险案例: {hr_stats.get('high_risk', 0)}\n\n"
            
            # 最近的安全事件
            message += f"📋 **最近安全事件**:\n"
            # TODO: 添加安全事件查询逻辑
            message += "• 暂无最近事件\n\n"
            
            message += f"📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            await ctx.reply_text(message, parse_mode="Markdown")
            
    except Exception as e:
        logger.error(f"查询安全状态失败: {e}")
        await ctx.reply_text(f"❌ 查询安全状态失败: {str(e)}")


async def _show_admin_help(ctx: TelegramUpdateContext) -> None:
    """显示管理员帮助"""
    help_text = """
🛠️ **管理员命令**:

/admin health - 系统健康检查
/admin alerts - 查看系统警报
/admin disks - 磁盘空间状态
/admin ping - 系统响应测试
/admin errors - 错误日志摘要
/admin safety_status - 安全策略状态

💡 使用 /admin <命令> 执行具体操作
"""
    await ctx.reply_text(help_text, parse_mode="Markdown")


async def _show_system_health(ctx: TelegramUpdateContext) -> None:
    """显示系统健康状态"""
    try:
        from app.services.system_health_service import get_health_summary
        
        summary = await get_health_summary(ctx.session)
        
        # 构建状态文本
        status_icons = {
            "healthy": "✅",
            "warning": "⚠️",
            "critical": "❌",
            "unknown": "❓",
        }
        
        text = "🏥 *系统健康状态*\n\n"
        
        overall_status = summary.get("overall_status", "unknown")
        text += f"总体状态: {status_icons.get(overall_status, '❓')} {overall_status.upper()}\n\n"
        
        # 各组件状态
        components = summary.get("components", {})
        for name, status in components.items():
            icon = status_icons.get(status, "❓")
            text += f"{icon} {name}: {status}\n"
        
        # 更新时间
        text += f"\n📅 更新时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        
        await ctx.reply_text(text)
        
    except ImportError:
        await ctx.reply_text("❌ 系统健康服务不可用")
    except Exception as e:
        logger.error(f"[telegram] get health summary failed: {e}")
        await ctx.reply_text(f"❌ 获取健康状态失败: {str(e)[:100]}")


async def _show_runner_status(ctx: TelegramUpdateContext) -> None:
    """显示 Runner 状态"""
    try:
        from app.services.system_health_service import get_runner_status_list
        
        runners = await get_runner_status_list(ctx.session, limit=10)
        
        if not runners:
            await ctx.reply_text("📊 *Runner 状态*\n\n暂无 Runner 记录")
            return
        
        text = "📊 *Runner 状态*\n\n"
        
        for runner in runners:
            name = runner.get("name", "unknown")
            status = runner.get("status", "unknown")
            last_heartbeat = runner.get("last_heartbeat")
            
            if status == "running":
                icon = "🟢"
            elif status == "stopped":
                icon = "🔴"
            else:
                icon = "🟡"
            
            text += f"{icon} *{name}*\n"
            text += f"   状态: {status}\n"
            
            if last_heartbeat:
                text += f"   心跳: {last_heartbeat}\n"
            
            text += "\n"
        
        await ctx.reply_text(text)
        
    except ImportError:
        await ctx.reply_text("❌ Runner 状态服务不可用")
    except Exception as e:
        logger.error(f"[telegram] get runner status failed: {e}")
        await ctx.reply_text(f"❌ 获取 Runner 状态失败: {str(e)[:100]}")


async def _show_whoami(ctx: TelegramUpdateContext) -> None:
    """显示当前用户信息"""
    user = ctx.app_user
    
    text = "👤 *当前用户信息*\n\n"
    text += f"🆔 用户名: `{user.username}`\n"
    text += f"📧 邮箱: `{user.email or '未设置'}`\n"
    text += f"👑 管理员: {'是' if ctx.is_admin else '否'}\n"
    text += f"📱 Telegram: @{ctx.username or '未设置'}\n"
    text += f"💬 Chat ID: `{ctx.chat_id}`\n"
    
    if user.created_at:
        text += f"📅 注册时间: {user.created_at.strftime('%Y-%m-%d')}\n"
    
    await ctx.reply_text(text)


async def _show_stats(ctx: TelegramUpdateContext) -> None:
    """显示系统统计"""
    try:
        from sqlalchemy import func, select
        from app.models.user import User
        from app.models.user_notification import UserNotification
        
        # 用户数
        user_count = await ctx.session.scalar(select(func.count(User.id)))
        
        # 通知数
        notif_count = await ctx.session.scalar(select(func.count(UserNotification.id)))
        
        text = "📈 *系统统计*\n\n"
        text += f"👥 用户数: {user_count}\n"
        text += f"🔔 通知数: {notif_count}\n"
        
        # 其他统计...
        try:
            from app.models.user_telegram_binding import UserTelegramBinding
            binding_count = await ctx.session.scalar(select(func.count(UserTelegramBinding.id)))
            text += f"📱 Telegram 绑定: {binding_count}\n"
        except Exception:
            pass
        
        text += f"\n📅 统计时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        
        await ctx.reply_text(text)
        
    except Exception as e:
        logger.error(f"[telegram] get stats failed: {e}")
        await ctx.reply_text(f"❌ 获取统计失败: {str(e)[:100]}")


async def _show_recent_alerts(ctx: TelegramUpdateContext) -> None:
    """显示最近告警"""
    try:
        from sqlalchemy import select, desc
        from app.models.ops_alert_log import OpsAlertLog
        
        stmt = select(OpsAlertLog).order_by(desc(OpsAlertLog.created_at)).limit(10)
        result = await ctx.session.execute(stmt)
        alerts = result.scalars().all()
        
        if not alerts:
            await ctx.reply_text("🔔 *最近告警*\n\n暂无告警记录")
            return
        
        text = "🔔 *最近告警*\n\n"
        
        severity_icons = {
            "critical": "🔴",
            "warning": "🟡",
            "info": "🔵",
        }
        
        for alert in alerts:
            icon = severity_icons.get(getattr(alert, "severity", "info"), "⚪")
            title = getattr(alert, "title", "未知告警")[:30]
            time_str = alert.created_at.strftime("%m-%d %H:%M") if alert.created_at else ""
            
            text += f"{icon} *{title}*\n"
            text += f"   {time_str}\n"
        
        await ctx.reply_text(text)
        
    except ImportError:
        await ctx.reply_text("❌ 告警服务不可用")
    except Exception as e:
        logger.error(f"[telegram] get alerts failed: {e}")
        await ctx.reply_text(f"❌ 获取告警失败: {str(e)[:100]}")


async def _show_disk_status(ctx: TelegramUpdateContext) -> None:
    """显示磁盘状态"""
    try:
        import shutil
        import os
        
        text = "💾 *磁盘空间*\n\n"
        
        # 获取常用路径的磁盘使用情况
        paths_to_check = [
            ("/", "系统盘"),
            ("/data", "数据盘"),
            ("/media", "媒体盘"),
        ]
        
        # Windows 兼容
        if os.name == 'nt':
            paths_to_check = [
                ("C:\\", "系统盘 C:"),
                ("D:\\", "数据盘 D:"),
            ]
        
        for path, name in paths_to_check:
            try:
                if os.path.exists(path):
                    usage = shutil.disk_usage(path)
                    total_gb = usage.total / (1024**3)
                    used_gb = usage.used / (1024**3)
                    free_gb = usage.free / (1024**3)
                    percent = (usage.used / usage.total) * 100
                    
                    # 状态图标
                    if percent >= 90:
                        icon = "🔴"
                    elif percent >= 70:
                        icon = "🟡"
                    else:
                        icon = "🟢"
                    
                    text += f"{icon} *{name}*\n"
                    text += f"   已用: {used_gb:.1f}GB / {total_gb:.1f}GB ({percent:.0f}%)\n"
                    text += f"   剩余: {free_gb:.1f}GB\n\n"
            except Exception:
                pass
        
        await ctx.reply_text(text)
        
    except Exception as e:
        logger.error(f"[telegram] get disk status failed: {e}")
        await ctx.reply_text(f"❌ 获取磁盘状态失败: {str(e)[:100]}")


async def _show_ping_status(ctx: TelegramUpdateContext) -> None:
    """显示关键依赖状态"""
    text = "🏓 *依赖状态检查*\n\n"
    
    # 数据库
    try:
        from sqlalchemy import text as sql_text
        await ctx.session.execute(sql_text("SELECT 1"))
        text += "✅ 数据库: 正常\n"
    except Exception as e:
        text += f"❌ 数据库: 异常 ({str(e)[:30]})\n"
    
    # Redis（如果有）
    try:
        from app.core.redis import redis_client
        if redis_client:
            await redis_client.ping()
            text += "✅ Redis: 正常\n"
    except ImportError:
        text += "⚪ Redis: 未配置\n"
    except Exception as e:
        text += f"❌ Redis: 异常 ({str(e)[:30]})\n"
    
    # 外部索引器（如果有）
    try:
        from app.services.external_indexer_service import check_indexer_health
        ok = await check_indexer_health()
        text += "✅ 外部索引器: 正常\n" if ok else "❌ 外部索引器: 异常\n"
    except ImportError:
        text += "⚪ 外部索引器: 未配置\n"
    except Exception:
        text += "⚪ 外部索引器: 未知\n"
    
    text += f"\n📅 检查时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    
    await ctx.reply_text(text)


async def _show_recent_errors(ctx: TelegramUpdateContext) -> None:
    """显示最近错误任务"""
    try:
        from app.services.bot_task_overview_service import list_user_download_jobs
        
        # 获取失败的任务（管理员视角，不限用户）
        jobs = await list_user_download_jobs(ctx.session, ctx.app_user, status="failed", limit=10)
        
        if not jobs:
            await ctx.reply_text("❌ *最近错误*\n\n暂无失败任务")
            return
        
        text = "❌ *最近错误任务*\n\n"
        
        for job in jobs:
            title = job.title[:25] if job.title else "未知任务"
            error = job.error_message[:50] if job.error_message else "无错误信息"
            time_str = job.created_at.strftime("%m-%d %H:%M") if job.created_at else ""
            
            text += f"• *{title}*\n"
            text += f"   {time_str}\n"
            text += f"   `{error}`\n\n"
        
        await ctx.reply_text(text)
        
    except Exception as e:
        logger.error(f"[telegram] get recent errors failed: {e}")
        await ctx.reply_text(f"❌ 获取错误列表失败: {str(e)[:100]}")
