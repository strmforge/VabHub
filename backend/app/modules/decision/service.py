"""下载决策模块核心实现。"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from loguru import logger

from app.modules.decision.models import (
    DecisionCandidate,
    DecisionContext,
    DecisionReasonCode,
    DecisionResult,
)
from app.modules.hnr.detector import HNRDetector, HNRVerdict
from app.modules.subscription.rule_engine import RuleEngine


class DecisionService:
    """统一下载决策入口。"""

    def __init__(
        self,
        *,
        rule_engine: Optional[RuleEngine] = None,
        hnr_detector: Optional[HNRDetector] = None,
    ):
        self.rule_engine = rule_engine or RuleEngine()
        self.hnr_detector = hnr_detector or HNRDetector()

    async def decide_download(
        self, candidate: DecisionCandidate, context: DecisionContext
    ) -> DecisionResult:
        """对候选资源做下载决策。"""

        debug_context: Dict[str, Any] = {}

        # 1) 订阅规则匹配
        subscription_dict = context.subscription.model_dump(exclude_none=True)
        candidate_dict = self._build_rule_engine_payload(candidate)
        matches = self.rule_engine.match_result(candidate_dict, subscription_dict)

        debug_context["rule_engine_input"] = {
            "candidate": candidate_dict,
            "subscription": subscription_dict,
            "matched": matches,
        }

        if not matches:
            return DecisionResult(
                should_download=False,
                reason=DecisionReasonCode.RULE_MISMATCH,
                message="不符合订阅规则",
                debug_context=debug_context if context.debug_enabled else {},
            )

        # 2) 重复与质量比较
        duplicate_reason = self._check_duplicates(candidate, context)
        if duplicate_reason:
            debug_context["duplicate_reason"] = duplicate_reason
            return DecisionResult(
                should_download=False,
                reason=DecisionReasonCode.DUPLICATE_ACTIVE,
                message=duplicate_reason,
                debug_context=debug_context if context.debug_enabled else {},
            )

        quality_score, quality_reason = self._evaluate_quality(candidate, context)
        debug_context["quality"] = {
            "score": quality_score,
            "reason": quality_reason,
        }

        if quality_score <= 0:
            return DecisionResult(
                should_download=False,
                reason=DecisionReasonCode.QUALITY_INFERIOR,
                message=quality_reason or "质量不优于现有版本",
                debug_context=debug_context if context.debug_enabled else {},
            )

        # 3) HNR 风险检测
        hnr_result = self.hnr_detector.detect(
            title=candidate.title,
            subtitle=candidate.subtitle or "",
            badges_text=context.hnr_badges or "",
            list_html=context.hnr_html or "",
            site_id=context.hnr_site,
        )
        debug_context["hnr"] = {
            "verdict": hnr_result.verdict.value,
            "confidence": hnr_result.confidence,
            "matched_rules": hnr_result.matched_rules,
            "category": hnr_result.category,
        }

        if hnr_result.verdict == HNRVerdict.BLOCKED:
            return DecisionResult(
                should_download=False,
                reason=DecisionReasonCode.HNR_BLOCKED,
                message="检测到 H&R 风险（BLOCKED）",
                hnr_verdict=hnr_result.verdict.value,
                debug_context=debug_context if context.debug_enabled else {},
            )
        if hnr_result.verdict == HNRVerdict.SUSPECTED:
            # TODO: 可引入用户偏好决定是否允许
            return DecisionResult(
                should_download=False,
                reason=DecisionReasonCode.HNR_SUSPECTED,
                message="检测到 H&R 风险（SUSPECTED）",
                hnr_verdict=hnr_result.verdict.value,
                debug_context=debug_context if context.debug_enabled else {},
            )

        # 4) SafetyPolicyEngine 安全策略检查 (P3-1)
        try:
            from app.modules.safety.engine import get_safety_policy_engine
            from app.modules.safety.models import SafetyContext
            
            safety_engine = get_safety_policy_engine()
            
            # 创建安全上下文
            safety_ctx = SafetyContext(
                action="download",
                site_key=candidate.site_key,
                torrent_id=candidate.torrent_id,
                trigger="user_web" if context.subscription_id else "system_runner",
                subscription_id=context.subscription_id
            )
            
            # 执行安全策略评估
            safety_decision = await safety_engine.evaluate(safety_ctx)
            debug_context["safety"] = {
                "decision": safety_decision.decision,
                "reason_code": safety_decision.reason_code,
                "message": safety_decision.message,
                "requires_user_action": safety_decision.requires_user_action
            }
            
            if safety_decision.decision == "DENY":
                return DecisionResult(
                    should_download=False,
                    reason=DecisionReasonCode.SAFETY_BLOCKED,
                    message=f"安全策略阻止: {safety_decision.message}",
                    debug_context=debug_context if context.debug_enabled else {},
                )
            elif safety_decision.decision == "REQUIRE_CONFIRM":
                # 对于需要确认的情况，暂时阻止下载，等待用户确认
                return DecisionResult(
                    should_download=False,
                    reason=DecisionReasonCode.SAFETY_REQUIRE_CONFIRM,
                    message=f"需要用户确认: {safety_decision.message}",
                    debug_context=debug_context if context.debug_enabled else {},
                )
                
        except Exception as e:
            # 安全策略检查失败时记录日志但允许下载（安全模式）
            logger.warning(f"安全策略检查失败，允许下载: {e}")
            debug_context["safety_error"] = str(e)

        # 4) 默认认为可以下载
        reason = (
            DecisionReasonCode.OK_UPGRADE
            if quality_reason == "优于现有版本"
            else DecisionReasonCode.OK_NEW
        )

        return DecisionResult(
            should_download=True,
            reason=reason,
            message=quality_reason or "符合订阅规则",
            score=quality_score,
            selected_quality=candidate.quality,
            normalized_quality=self._normalize_quality(candidate),
            hnr_verdict=hnr_result.verdict.value,
            debug_context=debug_context if context.debug_enabled else {},
        )

    def _build_rule_engine_payload(self, candidate: DecisionCandidate) -> Dict[str, Any]:
        payload = {
            "title": candidate.title,
            "quality": candidate.quality,
            "resolution": candidate.resolution,
            "effect": candidate.effect,
            "seeders": candidate.seeders or 0,
            "size_gb": candidate.size_gb,
        }
        payload.update(candidate.raw or {})
        return payload

    def _check_duplicates(
        self, candidate: DecisionCandidate, context: DecisionContext
    ) -> Optional[str]:
        for item in context.existing_items:
            if item.title == candidate.title and item.status in {"downloading", "seeding"}:
                return f"已有活跃任务：{item.title}（{item.status}）"
        return None

    def _evaluate_quality(
        self, candidate: DecisionCandidate, context: DecisionContext
    ) -> Tuple[float, str]:
        """根据订阅偏好与现有条目计算质量分。"""
        subscription = context.subscription
        preferred_quality = (subscription.quality or "").lower()
        preferred_resolution = (subscription.resolution or "").lower()

        quality_score = 0.5  # 基础分
        reason = "符合基础规则"

        if preferred_quality and candidate.quality:
            if preferred_quality in candidate.quality.lower():
                quality_score += 0.3
                reason = "匹配订阅质量"

        if preferred_resolution and candidate.resolution:
            if preferred_resolution in candidate.resolution.lower():
                quality_score += 0.2
                reason = "匹配订阅分辨率"

        # 与现有条目比较
        best_existing = self._best_existing_item(context)
        if best_existing:
            existing_score = self._score_existing_item(best_existing)
            candidate_score = self._score_candidate(candidate)
            debug_info = {
                "existing_score": existing_score,
                "candidate_score": candidate_score,
                "existing_title": best_existing.title,
            }
            logger.debug(f"[decision] 质量比较: {debug_info}")
            if candidate_score > existing_score:
                reason = "优于现有版本"
                quality_score += 0.2
            else:
                reason = "质量不优于现有版本"
                quality_score -= 0.4
            if quality_score <= 0:
                return 0.0, reason
            return quality_score, reason

        return quality_score, reason

    def _best_existing_item(self, context: DecisionContext) -> Optional[Any]:
        best_item: Optional[Any] = None
        best_score = -1.0
        for item in context.existing_items:
            score = self._score_existing_item(item)
            if score > best_score:
                best_item = item
                best_score = score
        return best_item

    def _score_existing_item(self, item: Any) -> float:
        score = 0.0
        if item.quality:
            score += 0.4
        if item.resolution:
            score += 0.2
        if item.status == "completed":
            score += 0.2
        if item.extra.get("preferred"):
            score += 0.2
        return score

    def _score_candidate(self, candidate: DecisionCandidate) -> float:
        score = 0.0
        if candidate.quality:
            score += 0.4
        if candidate.resolution:
            score += 0.2
        if (candidate.seeders or 0) >= 10:
            score += 0.1
        if candidate.size_gb and candidate.size_gb > 0:
            score += 0.1
        return score

    def _normalize_quality(self, candidate: DecisionCandidate) -> Optional[str]:
        quality = (candidate.quality or "").upper()
        if not quality:
            return None
        if "1080" in quality:
            return "1080P"
        if "2160" in quality or "4K" in quality:
            return "2160P"
        if "720" in quality:
            return "720P"
        return quality


_decision_service: Optional[DecisionService] = None


def get_decision_service() -> DecisionService:
    global _decision_service
    if _decision_service is None:
        logger.debug("初始化 DecisionService")
        _decision_service = DecisionService()
    return _decision_service


