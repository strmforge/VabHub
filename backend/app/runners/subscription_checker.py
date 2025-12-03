"""
影视订阅检查 Runner（VIDEO-AUTOLOOP-1-P3）

提供周期性检查订阅的能力，用于 CLI / Cron / systemd 调用
"""

import asyncio
import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.subscription import Subscription
from app.modules.subscription.service import SubscriptionService as ExistingSubscriptionService
from app.core.config import settings
from app.core.database import AsyncSessionLocal


@dataclass
class SubscriptionBatchResult:
    """批量执行订阅检查的结果"""
    total_subscriptions: int  # 本次尝试处理的订阅数
    checked_subscriptions: int  # 实际检查的订阅数
    succeeded_checks: int  # 检查成功的订阅数
    created_tasks: int  # 创建的下载任务数
    failed_checks: int  # 检查失败的订阅数
    skipped_checks: int  # 跳过的订阅数（冷却期内）
    last_subscription_id: Optional[int] = None  # 最后一个被处理的订阅ID


async def run_subscription_checks(
    db: AsyncSession,
    max_subscriptions: Optional[int] = None,
    cooldown_minutes: int = 30,
    dry_run: bool = False,
) -> SubscriptionBatchResult:
    """
    批量执行订阅检查（使用现有SubscriptionService）
    
    Args:
        db: 数据库会话
        max_subscriptions: 最多处理的订阅数量，None则使用默认值
        cooldown_minutes: 冷却时间（分钟），跳过在此时间内已检查的订阅
        dry_run: 是否为试运行（不创建实际下载任务）
    
    Returns:
        SubscriptionBatchResult: 批量执行结果
    """
    # 确定最大处理数量
    if max_subscriptions is None:
        max_subscriptions = 20  # 默认每次处理20个订阅
    
    if max_subscriptions <= 0:
        max_subscriptions = 20
    
    logger.info(
        f"开始批量执行订阅检查，最多处理 {max_subscriptions} 个，"
        f"冷却时间 {cooldown_minutes} 分钟，试运行={dry_run}"
    )
    
    result = SubscriptionBatchResult(
        total_subscriptions=0,
        checked_subscriptions=0,
        succeeded_checks=0,
        created_tasks=0,
        failed_checks=0,
        skipped_checks=0,
        last_subscription_id=None
    )
    
    # 创建现有订阅服务实例
    subscription_service = ExistingSubscriptionService(db)
    
    # 查询需要检查的订阅
    cooldown_time = datetime.utcnow() - timedelta(minutes=cooldown_minutes)
    
    stmt = select(Subscription).where(
        and_(
            Subscription.status == "active",  # 只检查启用的订阅
            or_(
                Subscription.last_check_at.is_(None),  # 从未检查过
                Subscription.last_check_at < cooldown_time  # 超过冷却时间
            )
        )
    ).order_by(
        Subscription.last_check_at.asc().nulls_first()  # 最久未检查的优先
    ).limit(max_subscriptions)
    
    subscriptions_result = await db.execute(stmt)
    subscriptions = subscriptions_result.scalars().all()
    
    result.total_subscriptions = len(subscriptions)
    
    if not subscriptions:
        logger.info("没有需要检查的订阅")
        return result
    
    logger.info(f"找到 {len(subscriptions)} 个需要检查的订阅")
    
    # 逐个检查订阅
    for subscription in subscriptions:
        result.last_subscription_id = subscription.id
        
        try:
            logger.info(
                f"检查订阅 {subscription.id}: {subscription.title} "
                f"(用户={getattr(subscription, 'user_id', 'unknown')}, 类型={subscription.media_type})"
            )
            
            # 执行订阅检查（使用现有服务）
            search_result = await subscription_service.execute_search(
                subscription_id=subscription.id,
                auto_download_override=not dry_run  # 试运行时不自动下载
            )
            
            result.checked_subscriptions += 1
            
            if search_result.get("success", False):
                result.succeeded_checks += 1
                # 从现有服务的结果中提取创建的任务数
                result.created_tasks += search_result.get("downloaded_count", 0)
                
                logger.info(
                    f"订阅 {subscription.id} 检查成功: "
                    f"创建任务={search_result.get('downloaded_count', 0)}, "
                    f"消息={search_result.get('message', '')}"
                )
            else:
                result.failed_checks += 1
                logger.warning(
                    f"订阅 {subscription.id} 检查失败: {search_result.get('message', '未知错误')}"
                )
            
        except Exception as e:
            result.failed_checks += 1
            logger.error(f"订阅 {subscription.id} 检查异常: {e}")
            
            # 更新错误状态
            try:
                subscription.last_check_at = datetime.utcnow()
                subscription.last_error = f"检查异常: {str(e)}"
                await db.commit()
            except Exception as commit_error:
                logger.error(f"更新订阅 {subscription.id} 错误状态失败: {commit_error}")
    
    # 输出批量结果
    logger.info(
        f"订阅检查批量执行完成: "
        f"总数={result.total_subscriptions}, "
        f"已检查={result.checked_subscriptions}, "
        f"成功={result.succeeded_checks}, "
        f"失败={result.failed_checks}, "
        f"创建任务={result.created_tasks}"
    )
    
    return result


async def run_single_subscription_check(
    db: AsyncSession,
    subscription_id: int,
    dry_run: bool = False,
) -> SubscriptionBatchResult:
    """
    检查单个订阅（使用现有SubscriptionService）
    
    Args:
        db: 数据库会话
        subscription_id: 订阅ID
        dry_run: 是否为试运行
    
    Returns:
        SubscriptionBatchResult: 执行结果
    """
    result = SubscriptionBatchResult(
        total_subscriptions=0,
        checked_subscriptions=0,
        succeeded_checks=0,
        created_tasks=0,
        failed_checks=0,
        skipped_checks=0,
        last_subscription_id=None
    )
    
    # 创建现有订阅服务实例
    subscription_service = ExistingSubscriptionService(db)
    
    # 查询订阅
    stmt = select(Subscription).where(Subscription.id == subscription_id)
    subscription_result = await db.execute(stmt)
    subscription = subscription_result.scalar_one_or_none()
    
    if not subscription:
        logger.error(f"订阅 {subscription_id} 不存在")
        return result
    
    result.total_subscriptions = 1
    result.last_subscription_id = subscription_id
    
    logger.info(f"检查单个订阅 {subscription_id}: {subscription.title}")
    
    try:
        # 执行订阅检查（使用现有服务）
        search_result = await subscription_service.execute_search(
            subscription_id=subscription_id,
            auto_download_override=not dry_run  # 试运行时不自动下载
        )
        
        result.checked_subscriptions = 1
        
        if search_result.get("success", False):
            result.succeeded_checks = 1
            # 从现有服务的结果中提取创建的任务数
            result.created_tasks += search_result.get("downloaded_count", 0)
            
            logger.info(
                f"订阅 {subscription_id} 检查成功: "
                f"创建任务={search_result.get('downloaded_count', 0)}, "
                f"消息={search_result.get('message', '')}"
            )
        else:
            result.failed_checks = 1
            logger.warning(
                f"订阅 {subscription_id} 检查失败: {search_result.get('message', '未知错误')}"
            )
        
        # 输出详细结果
        print(f"\n=== 订阅检查结果 ===")
        print(f"订阅ID: {subscription_id}")
        print(f"标题: {subscription.title}")
        print(f"媒体类型: {subscription.media_type}")
        print(f"用户ID: {getattr(subscription, 'user_id', 'unknown')}")
        print(f"安全策略: allow_hr={getattr(subscription, 'allow_hr', False)}, "
              f"allow_h3h5={getattr(subscription, 'allow_h3h5', False)}, "
              f"strict_free_only={getattr(subscription, 'strict_free_only', False)}")
        print(f"创建下载任务: {search_result.get('downloaded_count', 0)}")
        print(f"检查结果: {'成功' if search_result.get('success', False) else '失败'}")
        if not search_result.get('success', False):
            print(f"失败原因: {search_result.get('message', '未知错误')}")
        print(f"试运行: {'是' if dry_run else '否'}")
        print("==================\n")
        
    except Exception as e:
        result.failed_checks = 1
        logger.error(f"订阅 {subscription_id} 检查异常: {e}")
    
    return result


async def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(description="影视订阅检查 Runner")
    
    # 基本参数
    parser.add_argument("--id", type=int, help="检查单个订阅ID")
    parser.add_argument("--once", action="store_true", help="只运行一次（与--id配合使用）")
    
    # 批量参数
    parser.add_argument("--limit", type=int, help="批量检查时的最大订阅数量")
    parser.add_argument("--cooldown", type=int, default=30, help="冷却时间（分钟）")
    
    # 试运行参数
    parser.add_argument("--dry-run", action="store_true", help="试运行，不创建实际下载任务")
    
    # 日志参数
    parser.add_argument("--verbose", "-v", action="store_true", help="详细日志")
    
    args = parser.parse_args()
    
    # 配置日志
    if args.verbose:
        logger.remove()
        logger.add("console", level="DEBUG")
    
    logger.info("影视订阅检查 Runner 启动")
    logger.info(f"参数: {args}")
    
    # 创建数据库会话
    async with AsyncSessionLocal() as db:
        try:
            if args.id:
                # 检查单个订阅
                result = await run_single_subscription_check(
                    db=db,
                    subscription_id=args.id,
                    dry_run=args.dry_run
                )
                
                logger.info(f"单个订阅检查完成: {result}")
                
            else:
                # 批量检查订阅
                result = await run_subscription_checks(
                    db=db,
                    max_subscriptions=args.limit,
                    cooldown_minutes=args.cooldown,
                    dry_run=args.dry_run
                )
                
                logger.info(f"批量订阅检查完成: {result}")
        
        except KeyboardInterrupt:
            logger.info("用户中断，退出")
        except Exception as e:
            logger.error(f"Runner 执行异常: {e}")
            raise
        finally:
            await db.close()


if __name__ == "__main__":
    asyncio.run(main())
