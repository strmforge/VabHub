"""
音乐订阅检查 Runner（MUSIC-AUTOLOOP-2-P2）

提供周期性检查音乐订阅的能力，用于 CLI / Cron / systemd 调用
"""

import asyncio
import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.user_music_subscription import UserMusicSubscription, MusicSubscriptionType
from app.services.music_subscription_service import run_subscription_once
from app.core.config import settings
from app.core.database import AsyncSessionLocal


@dataclass
class MusicSubscriptionBatchResult:
    """批量执行音乐订阅检查的结果"""
    total_subscriptions: int  # 本次尝试处理的订阅数
    checked_subscriptions: int  # 实际检查的订阅数
    succeeded_checks: int  # 检查成功的订阅数
    created_tasks: int  # 创建的下载任务数
    failed_checks: int  # 检查失败的订阅数
    skipped_checks: int  # 跳过的订阅数（冷却期内）
    last_subscription_id: Optional[int] = None  # 最后一个被处理的订阅ID


async def run_music_subscription_checks(
    db: AsyncSession,
    max_subscriptions: Optional[int] = None,
    cooldown_minutes: int = 30,
    dry_run: bool = False,
) -> MusicSubscriptionBatchResult:
    """
    批量执行音乐订阅检查
    
    Args:
        db: 数据库会话
        max_subscriptions: 最多处理的订阅数量，None则使用默认值
        cooldown_minutes: 冷却时间（分钟），跳过在此时间内已检查的订阅
        dry_run: 是否为试运行（不创建实际下载任务）
    
    Returns:
        MusicSubscriptionBatchResult: 批量执行结果
    """
    result = MusicSubscriptionBatchResult(
        total_subscriptions=0,
        checked_subscriptions=0,
        succeeded_checks=0,
        created_tasks=0,
        failed_checks=0,
        skipped_checks=0,
    )
    
    # 默认值
    if max_subscriptions is None:
        max_subscriptions = 50
    
    # 计算冷却时间阈值
    cooldown_threshold = datetime.utcnow() - timedelta(minutes=cooldown_minutes)
    
    # 查询需要检查的订阅
    query = select(UserMusicSubscription).where(
        and_(
            UserMusicSubscription.status == "active",
            or_(
                UserMusicSubscription.last_run_at.is_(None),
                UserMusicSubscription.last_run_at < cooldown_threshold
            )
        )
    ).order_by(
        UserMusicSubscription.last_run_at.asc().nullslast()
    ).limit(max_subscriptions)
    
    subscriptions_result = await db.execute(query)
    subscriptions = list(subscriptions_result.scalars().all())
    
    result.total_subscriptions = len(subscriptions)
    
    if not subscriptions:
        logger.info("没有需要检查的音乐订阅")
        return result
    
    logger.info(f"开始检查 {len(subscriptions)} 个音乐订阅")
    
    # 处理每个订阅
    for subscription in subscriptions:
        try:
            result.checked_subscriptions += 1
            result.last_subscription_id = subscription.id
            
            logger.info(f"检查音乐订阅 {subscription.id} ({subscription.subscription_type})")
            
            # 调用音乐订阅服务
            run_result = await run_music_subscription_once(
                db,
                subscription,
                auto_download=not dry_run,
            )
            
            # 统计结果
            if run_result.errors:
                result.failed_checks += 1
                logger.warning(f"音乐订阅 {subscription.id} 检查失败: {run_result.errors}")
            else:
                result.succeeded_checks += 1
                result.created_tasks += run_result.created_tasks
                
                logger.info(
                    f"音乐订阅 {subscription.id} 检查完成: "
                    f"搜索={run_result.found_total}, "
                    f"过滤={sum(run_result.filtered_out.values())}, "
                    f"创建={run_result.created_tasks}"
                )
            
            # 更新订阅的错误状态（如果有）
            if run_result.errors:
                subscription.last_run_at = datetime.utcnow()
                # 这里可以添加 last_error 字段更新，如果模型支持的话
            
            await db.commit()
            
        except Exception as e:
            result.failed_checks += 1
            logger.error(f"音乐订阅 {subscription.id} 处理异常: {e}")
            
            try:
                await db.rollback()
            except Exception as rollback_error:
                logger.error(f"回滚失败: {rollback_error}")
            
            continue
    
    # 输出统计
    logger.info(
        f"音乐订阅检查完成: "
        f"总计={result.total_subscriptions}, "
        f"已检查={result.checked_subscriptions}, "
        f"成功={result.succeeded_checks}, "
        f"失败={result.failed_checks}, "
        f"创建任务={result.created_tasks}"
    )
    
    return result


async def run_once(
    max_subscriptions: Optional[int] = None,
    cooldown_minutes: int = 30,
    dry_run: bool = False,
) -> MusicSubscriptionBatchResult:
    """
    运行一次音乐订阅检查
    
    Args:
        max_subscriptions: 最多处理的订阅数量
        cooldown_minutes: 冷却时间（分钟）
        dry_run: 是否为试运行
    
    Returns:
        MusicSubscriptionBatchResult: 执行结果
    """
    async with AsyncSessionLocal() as db:
        return await run_music_subscription_checks(
            db,
            max_subscriptions=max_subscriptions,
            cooldown_minutes=cooldown_minutes,
            dry_run=dry_run,
        )


async def run_forever(
    interval_seconds: int = 1800,  # 30分钟
    max_subscriptions: Optional[int] = None,
    cooldown_minutes: int = 30,
    dry_run: bool = False,
) -> None:
    """
    持续运行音乐订阅检查
    
    Args:
        interval_seconds: 检查间隔（秒）
        max_subscriptions: 每次最多处理的订阅数量
        cooldown_minutes: 冷却时间（分钟）
        dry_run: 是否为试运行
    """
    logger.info(
        f"音乐订阅检查器启动: "
        f"间隔={interval_seconds}秒, "
        f"最大数量={max_subscriptions or '默认'}, "
        f"冷却时间={cooldown_minutes}分钟, "
        f"试运行={dry_run}"
    )
    
    while True:
        try:
            start_time = datetime.utcnow()
            
            result = await run_once(
                max_subscriptions=max_subscriptions,
                cooldown_minutes=cooldown_minutes,
                dry_run=dry_run,
            )
            
            # 计算下次运行时间
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            sleep_time = max(0, interval_seconds - elapsed)
            
            if sleep_time > 0:
                logger.info(f"等待 {sleep_time:.0f} 秒后进行下次检查")
                await asyncio.sleep(sleep_time)
            else:
                logger.warning(f"本次检查耗时 {elapsed:.0f} 秒，超过间隔时间，立即进行下次检查")
            
        except KeyboardInterrupt:
            logger.info("收到中断信号，停止音乐订阅检查器")
            break
        except Exception as e:
            logger.error(f"音乐订阅检查器运行异常: {e}")
            logger.info("等待 60 秒后重试...")
            await asyncio.sleep(60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="音乐订阅检查器")
    
    parser.add_argument(
        "--mode",
        choices=["once", "loop"],
        default="once",
        help="运行模式: once=运行一次, loop=持续运行"
    )
    
    parser.add_argument(
        "--max-subscriptions",
        type=int,
        default=50,
        help="每次最多处理的订阅数量 (默认: 50)"
    )
    
    parser.add_argument(
        "--cooldown-minutes",
        type=int,
        default=30,
        help="冷却时间（分钟）(默认: 30)"
    )
    
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=1800,
        help="检查间隔（秒，仅在loop模式下有效）(默认: 1800)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="试运行模式（不创建实际下载任务）"
    )
    
    args = parser.parse_args()
    
    # 配置日志
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    try:
        if args.mode == "once":
            result = asyncio.run(run_once(
                max_subscriptions=args.max_subscriptions,
                cooldown_minutes=args.cooldown_minutes,
                dry_run=args.dry_run,
            ))
            
            print(f"\n✅ 音乐订阅检查完成:")
            print(f"   总计订阅: {result.total_subscriptions}")
            print(f"   已检查: {result.checked_subscriptions}")
            print(f"   成功: {result.succeeded_checks}")
            print(f"   失败: {result.failed_checks}")
            print(f"   创建任务: {result.created_tasks}")
            
        else:  # loop
            asyncio.run(run_forever(
                interval_seconds=args.interval_seconds,
                max_subscriptions=args.max_subscriptions,
                cooldown_minutes=args.cooldown_minutes,
                dry_run=args.dry_run,
            ))
            
    except KeyboardInterrupt:
        print("\n⏹️  音乐订阅检查器已停止")
    except Exception as e:
        logger.error(f"运行失败: {e}")
        exit(1)


if __name__ == "__main__":
    main()
