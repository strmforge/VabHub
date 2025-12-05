"""
SafetyPolicyEngine 核心评估引擎
实现安全策略的评估逻辑和决策生成
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings
from app.modules.hr_case.repository import get_hr_repository
from app.modules.hr_case.models import HrCase
from app.modules.safety.models import (
    SafetyContext,
    SafetyDecision,
    GlobalSafetySettings,
    SiteSafetySettings,
    SubscriptionSafetySettings,
    SafetyDecisionReason,
)
from app.modules.safety.settings import get_safety_settings_service


logger = logging.getLogger(__name__)


class SafetyPolicyEngine:
    """安全策略引擎"""
    
    def __init__(self):
        self._hr_repo = get_hr_repository()
        self._settings_service = get_safety_settings_service()
        self._logger = logger
    
    async def evaluate(self, ctx: SafetyContext) -> SafetyDecision:
        """评估安全策略"""
        start_time = time.time()
        
        try:
            # Feature Flag 检查
            if not await self._is_feature_enabled():
                return SafetyDecision(
                    decision="ALLOW",
                    reason_code=SafetyDecisionReason.SETTINGS_DISABLED,
                    message="安全策略功能已禁用",
                    confidence=1.0
                )
            
            # 获取相关配置
            global_settings = await self._settings_service.get_global()
            site_settings = await self._settings_service.get_site(ctx.site_key) if ctx.site_key else None
            sub_settings = await self._settings_service.get_subscription(ctx.subscription_id) if ctx.subscription_id else None
            
            # 获取HR状态 (容错处理：如果 HR 表不存在则视为无 HR 数据)
            hr_case = ctx.hr_case
            if ctx.site_key and ctx.torrent_id and not hr_case:
                try:
                    hr_case = await self._hr_repo.get_by_site_and_torrent(ctx.site_key, ctx.torrent_id)
                except Exception as hr_err:
                    # HR 表可能不存在（测试环境或新部署），视为无 HR 数据
                    err_msg = str(hr_err).lower()
                    if "no such table" in err_msg or "does not exist" in err_msg:
                        self._logger.debug(f"HR 表不存在，跳过 HR 检查: {hr_err}")
                        hr_case = None
                    else:
                        # 其他错误重新抛出
                        raise
            
            # 按操作类型评估
            if ctx.action == "download":
                decision = await self._evaluate_download(ctx, hr_case, global_settings, site_settings, sub_settings)
            elif ctx.action == "delete":
                decision = await self._evaluate_delete(ctx, hr_case, global_settings, site_settings, sub_settings)
            elif ctx.action == "move":
                decision = await self._evaluate_move(ctx, hr_case, global_settings, site_settings, sub_settings)
            elif ctx.action == "upload_cleanup":
                decision = await self._evaluate_upload_cleanup(ctx, hr_case, global_settings, site_settings, sub_settings)
            elif ctx.action == "generate_strm":
                decision = await self._evaluate_generate_strm(ctx, hr_case, global_settings, site_settings, sub_settings)
            else:
                decision = SafetyDecision(
                    decision="ALLOW",
                    reason_code=SafetyDecisionReason.UNKNOWN_ACTION,
                    message="未知操作类型，允许执行"
                )
            
            # 设置性能指标
            processing_time = (time.time() - start_time) * 1000
            if decision.processing_time_ms is None:
                # 创建新的决策对象包含处理时间
                decision = SafetyDecision(
                    decision=decision.decision,
                    reason_code=decision.reason_code,
                    message=decision.message,
                    suggested_alternative=decision.suggested_alternative,
                    hr_status_snapshot=decision.hr_status_snapshot,
                    confidence=decision.confidence,
                    requires_user_action=decision.requires_user_action,
                    auto_approve_after=decision.auto_approve_after,
                    processing_time_ms=processing_time,
                    settings_snapshot=decision.settings_snapshot
                )
            
            # 记录决策
            self._log_decision(ctx, decision, processing_time)
            
            return decision
            
        except Exception as e:
            self._logger.error(f"安全策略评估失败: {e}", exc_info=True)
            processing_time = (time.time() - start_time) * 1000
            return SafetyDecision(
                decision="ALLOW",
                reason_code=SafetyDecisionReason.ERROR_OCCURRED,
                message=f"安全策略评估失败，允许执行: {str(e)}",
                confidence=0.5,
                processing_time_ms=processing_time
            )
    
    async def _evaluate_download(self, ctx: SafetyContext, hr_case: Optional[HrCase],
                                global_settings: GlobalSafetySettings,
                                site_settings: Optional[SiteSafetySettings],
                                sub_settings: Optional[SubscriptionSafetySettings]) -> SafetyDecision:
        """评估下载操作"""
        
        # HR保护检查
        if global_settings.enable_hr_protection and hr_case and hr_case.status == "ACTIVE":
            return SafetyDecision(
                decision="DENY",
                reason_code=SafetyDecisionReason.HR_ACTIVE_DOWNLOAD,
                message="该种子正处于HR期，禁止下载",
                hr_status_snapshot={"status": hr_case.status, "deadline": hr_case.deadline}
            )
        
        # 订阅HR检查（应用于所有HR状态）
        if sub_settings and not sub_settings.allow_hr and hr_case:
            return SafetyDecision(
                decision="REQUIRE_CONFIRM",
                reason_code=SafetyDecisionReason.SUBSCRIPTION_NO_HR,
                message="订阅设置不允许HR种子，需要用户确认",
                confidence=0.9,
                requires_user_action=True,
                auto_approve_after=datetime.utcnow() + timedelta(hours=global_settings.auto_approve_hours),
                hr_status_snapshot=self._create_hr_snapshot(hr_case) if hr_case else None
            )
        
        # 站点敏感度检查
        if site_settings and site_settings.hr_sensitivity == "highly_sensitive":
            if hr_case and hr_case.status != "NONE":
                return SafetyDecision(
                    decision="REQUIRE_CONFIRM",
                    reason_code=SafetyDecisionReason.SITE_HIGHLY_SENSITIVE,
                    message="站点为高敏感站点，建议谨慎下载HR种子",
                    requires_user_action=True,
                    auto_approve_after=datetime.utcnow() + timedelta(hours=global_settings.auto_approve_hours)
                )
        
        return SafetyDecision(
            decision="ALLOW",
            reason_code=SafetyDecisionReason.SAFE,
            message="允许下载"
        )
    
    async def _evaluate_delete(self, ctx: SafetyContext, hr_case: Optional[hr_case],
                              global_settings: GlobalSafetySettings,
                              site_settings: Optional[SiteSafetySettings],
                              sub_settings: Optional[SubscriptionSafetySettings]) -> SafetyDecision:
        """评估删除操作"""
        
        # HR期内禁止删除
        if hr_case and hr_case.status == "ACTIVE":
            return SafetyDecision(
                decision="DENY",
                reason_code=SafetyDecisionReason.HR_ACTIVE_DELETE,
                message="该种子正处于HR期，禁止删除源文件",
                hr_status_snapshot={"status": hr_case.status, "seeded_hours": hr_case.seeded_hours}
            )
        
        # 非HR种子的最低保种要求检查
        if not hr_case or hr_case.status in ["NONE", "SAFE"]:
            min_ratio = self._get_effective_min_ratio(global_settings, site_settings)
            if hr_case and hr_case.current_ratio and hr_case.current_ratio < min_ratio:
                return SafetyDecision(
                    decision="REQUIRE_CONFIRM",
                    reason_code=SafetyDecisionReason.LOW_RATIO_WARNING,
                    message=f"当前分享率{hr_case.current_ratio:.2f}低于最低要求{min_ratio:.2f}，是否确认删除？",
                    requires_user_action=True,
                    auto_approve_after=datetime.utcnow() + timedelta(hours=global_settings.auto_approve_hours)
                )
        
        return SafetyDecision(
            decision="ALLOW",
            reason_code=SafetyDecisionReason.SAFE,
            message="允许删除"
        )
    
    async def _evaluate_move(self, ctx: SafetyContext, hr_case: Optional[hr_case],
                            global_settings: GlobalSafetySettings,
                            site_settings: Optional[SiteSafetySettings],
                            sub_settings: Optional[SubscriptionSafetySettings]) -> SafetyDecision:
        """评估移动操作"""
        
        # HR期内影响做种路径的移动需要特别处理
        if hr_case and hr_case.status == "ACTIVE" and ctx.changes_seeding_path:
            if global_settings.prefer_copy_on_move_for_hr:
                return SafetyDecision(
                    decision="REQUIRE_CONFIRM",
                    reason_code=SafetyDecisionReason.HR_MOVE_SUGGEST_COPY,
                    message="HR期内移动会影响做种，建议使用复制而非移动",
                    suggested_alternative="复制文件到目标位置",
                    requires_user_action=True
                )
            else:
                return SafetyDecision(
                    decision="DENY",
                    reason_code=SafetyDecisionReason.HR_ACTIVE_MOVE,
                    message="HR期内禁止移动影响做种路径的文件",
                    hr_status_snapshot={"status": hr_case.status, "deadline": hr_case.deadline}
                )
        
        # HR安全的种子按常规规则处理
        if hr_case and hr_case.status == "SAFE":
            return SafetyDecision(
                decision="ALLOW",
                reason_code=SafetyDecisionReason.HR_SAFE,
                message="HR已完成，允许移动"
            )
        
        return SafetyDecision(
            decision="ALLOW",
            reason_code=SafetyDecisionReason.SAFE,
            message="允许移动"
        )
    
    async def _evaluate_upload_cleanup(self, ctx: SafetyContext, hr_case: Optional[hr_case],
                                      global_settings: GlobalSafetySettings,
                                      site_settings: Optional[SiteSafetySettings],
                                      sub_settings: Optional[SubscriptionSafetySettings]) -> SafetyDecision:
        """评估自动清理操作"""
        
        # 自动清理遇到HR种子时更保守
        if hr_case and hr_case.status == "ACTIVE":
            return SafetyDecision(
                decision="DENY",
                reason_code=SafetyDecisionReason.HR_ACTIVE_CLEANUP,
                message="自动清理检测到HR期种子，已跳过删除",
                hr_status_snapshot={"status": hr_case.status, "torrent_id": hr_case.torrent_id}
            )
        
        return SafetyDecision(
            decision="ALLOW",
            reason_code=SafetyDecisionReason.SAFE,
            message="允许清理"
        )
    
    async def _evaluate_generate_strm(self, ctx: SafetyContext, hr_case: Optional[hr_case],
                                     global_settings: GlobalSafetySettings,
                                     site_settings: Optional[SiteSafetySettings],
                                     sub_settings: Optional[SubscriptionSafetySettings]) -> SafetyDecision:
        """评估生成STRM文件操作"""
        
        # STRM文件生成通常不影响做种，相对安全
        # 但仍需要记录HR状态用于审计
        
        hr_snapshot = None
        if hr_case:
            hr_snapshot = {
                "status": hr_case.status,
                "deadline": hr_case.deadline,
                "seeded_hours": hr_case.seeded_hours
            }
        
        return SafetyDecision(
            decision="ALLOW",
            reason_code=SafetyDecisionReason.SAFE,
            message="允许生成STRM文件",
            hr_status_snapshot=hr_snapshot
        )
    
    def _get_effective_min_ratio(self, global_settings: GlobalSafetySettings, 
                                site_settings: Optional[SiteSafetySettings]) -> float:
        """获取有效的最低分享率要求"""
        if site_settings and site_settings.min_keep_ratio is not None:
            return site_settings.min_keep_ratio
        return global_settings.min_ratio_for_delete
    
    def _get_effective_min_hours(self, global_settings: GlobalSafetySettings,
                               site_settings: Optional[SiteSafetySettings]) -> float:
        """获取有效的最低保种时间要求"""
        if site_settings and site_settings.min_keep_time_hours is not None:
            return site_settings.min_keep_time_hours
        return global_settings.min_keep_hours
    
    def _create_hr_snapshot(self, hr_case: HrCase) -> dict:
        """创建HR状态快照"""
        snapshot = {
            "status": hr_case.status,
        }
        
        # 添加可选字段，处理None值
        if hr_case.deadline:
            snapshot["deadline"] = hr_case.deadline.isoformat()
        if hr_case.seeded_hours is not None:
            snapshot["seeded_hours"] = hr_case.seeded_hours
        if hr_case.current_ratio is not None:
            snapshot["current_ratio"] = hr_case.current_ratio
        if hr_case.requirement_hours is not None:
            snapshot["requirement_hours"] = hr_case.requirement_hours
        if hr_case.torrent_id:
            snapshot["torrent_id"] = hr_case.torrent_id
        
        return snapshot
    
    async def _is_feature_enabled(self) -> bool:
        """检查功能是否启用"""
        try:
            return getattr(settings, 'SAFETY_ENGINE_ENABLED', False)
        except Exception:
            return False
    
    def _log_decision(self, ctx: SafetyContext, decision: SafetyDecision, processing_time: float):
        """记录决策日志"""
        log_level = logging.WARNING if decision.decision == "DENY" else logging.INFO
        self._logger.log(
            log_level,
            f"安全策略决策: {ctx.action} -> {decision.decision} "
            f"(原因: {decision.reason_code}, 耗时: {processing_time:.2f}ms) "
            f"站点: {ctx.site_key}, 种子: {ctx.torrent_id}"
        )
    
    async def batch_evaluate(self, contexts: list[SafetyContext]) -> list[SafetyDecision]:
        """批量评估安全策略"""
        if not contexts:
            return []
        
        # 简单的并行处理，后续可以优化为批量数据库查询
        decisions = []
        for ctx in contexts:
            decision = await self.evaluate(ctx)
            decisions.append(decision)
        
        return decisions
    
    async def get_stats(self) -> dict:
        """获取引擎统计信息"""
        # 这里可以实现统计信息收集
        return {
            "total_evaluations": 0,
            "allowed_count": 0,
            "denied_count": 0,
            "require_confirm_count": 0,
            "avg_processing_time_ms": 0.0,
            "cache_hit_rate": 0.0
        }


# 全局实例
_safety_policy_engine: Optional[SafetyPolicyEngine] = None


def get_safety_policy_engine() -> SafetyPolicyEngine:
    """获取安全策略引擎单例"""
    global _safety_policy_engine
    if _safety_policy_engine is None:
        _safety_policy_engine = SafetyPolicyEngine()
    return _safety_policy_engine


# 便捷函数
async def evaluate_safety(ctx: SafetyContext) -> SafetyDecision:
    """评估安全策略（便捷函数）"""
    engine = get_safety_policy_engine()
    return await engine.evaluate(ctx)


async def batch_evaluate_safety(contexts: list[SafetyContext]) -> list[SafetyDecision]:
    """批量评估安全策略（便捷函数）"""
    engine = get_safety_policy_engine()
    return await engine.batch_evaluate(contexts)
