"""
HNR检测器 - 智能HNR风险检测
整合自acq-guardian项目，支持YAML签名包、站点选择器、改进的误报避免
"""
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from loguru import logger

from app.modules.hnr.signatures.loader import SignaturePackLoader
from app.modules.hnr.utils.text import normalize, cooccur, extract_level

# 避免H.264/HDR10误报的正则表达式（整合自acq-guardian）
RE_HNR_BASIC = re.compile(r"""(?ix)
    \bH(?:\s*&\s*|[/／＆])?R\b | \bHnR\b | \bhit\s*&?\s*run\b
""")

# 修复look-behind断言：使用固定宽度模式
# 分别处理 H.264/H.265 和 H.264/H.265 的情况
RE_HNR_LEVEL = re.compile(r"""(?ix)
    (?<!H\.264)(?<!H\.265)(?<!H264)(?<!H265)  # avoid H.264/H.265 (fixed-width)
    (?<!HDR)                                   # avoid HDR / HDR10
    \bH\s*[-/:：]?\s*(?P<level>[1-9]|10)\b
""")


class HNRVerdict(Enum):
    """HNR判定结果"""
    BLOCKED = "blocked"  # 阻止
    SUSPECTED = "suspected"  # 疑似
    PASS = "pass"  # 通过


@dataclass
class HNRDetectionResult:
    """HNR检测结果"""
    verdict: HNRVerdict
    confidence: float
    matched_rules: List[str]
    category: str
    penalties: Dict[str, Any]
    message: str
    level: Optional[int] = None  # HNR级别（H3, H5, H7等）
    source: str = "unknown"  # 检测来源（list, title, heuristic）


class HNRDetector:
    """HNR检测器 - 整合acq-guardian功能"""
    
    def __init__(self, signature_pack_path: Optional[str] = None):
        """
        初始化HNR检测器
        
        Args:
            signature_pack_path: YAML签名包文件路径，如果为None则使用默认签名
        """
        # 初始化签名包加载器
        if signature_pack_path:
            self.sigpack = SignaturePackLoader(signature_pack_path)
        else:
            # 尝试从默认路径加载
            default_path = Path(__file__).parent / "signatures" / "pack.yaml"
            if default_path.exists():
                self.sigpack = SignaturePackLoader(str(default_path))
            else:
                # 使用默认签名
                self.sigpack = SignaturePackLoader(None)
        
        # 为了兼容性，保留旧的signatures字典
        self.signatures = self._convert_signatures_to_dict()
        self.site_overrides = {}
    
    def _convert_signatures_to_dict(self) -> Dict[str, Dict]:
        """将签名包转换为字典格式（兼容性）"""
        signatures = {}
        for sig in self.sigpack.get_signatures():
            signatures[sig.id] = {
                "id": sig.id,
                "name": sig.name,
                "patterns": {
                    "text": sig.patterns.text,
                    "regex": sig.patterns.regex
                },
                "confidence": sig.confidence,
                "category": sig.category,
                "penalties": sig.penalties
            }
        return signatures
    
    def reload_signatures(self) -> bool:
        """重新加载签名包（热更新）"""
        success = self.sigpack.reload()
        if success:
            self.signatures = self._convert_signatures_to_dict()
            logger.info("签名包已重新加载")
        return success
    
    def detect(
        self,
        title: str,
        subtitle: str = "",
        badges_text: str = "",
        list_html: str = "",
        site_id: Optional[str] = None
    ) -> HNRDetectionResult:
        """
        检测HNR风险 - 整合acq-guardian检测逻辑
        
        Args:
            title: 资源标题
            subtitle: 副标题
            badges_text: 标签文本
            list_html: 列表HTML
            site_id: 站点ID或名称
        
        Returns:
            HNRDetectionResult: 检测结果
        """
        # 标准化所有文本内容
        text_all = normalize(" ".join([title, subtitle, badges_text]))
        badges_html = normalize(" ".join([badges_text, list_html]))
        
        matched_rules = []
        confidence = 0.0
        category = ""
        penalties = {}
        level = None
        source = "unknown"
        reasons = []
        
        # 1) 站点选择器检测（CSS选择器）
        if site_id:
            site_selectors = self.sigpack.get_site_selectors(str(site_id))
            if site_selectors and list_html:
                # 使用CSS选择器匹配（简化版：从HTML中提取标签）
                for selector in site_selectors:
                    # 简化处理：提取选择器中的文本内容
                    # 完整实现需要使用BeautifulSoup
                    selector_text = selector.replace(":contains(", "").replace(")", "").replace("'", "").replace('"', "")
                    if selector_text and selector_text.lower() in badges_html:
                        level = extract_level(badges_html)
                        matched_rules.append(f"site-selector:{selector_text}")
                        confidence = 0.95
                        category = "HNR_BASIC"
                        source = "list"
                        reasons.append(f"站点选择器匹配: {selector_text}")
                        break
        
        # 2) 基本HNR检测（使用改进的正则表达式）
        if not matched_rules and RE_HNR_BASIC.search(text_all):
            level = extract_level(text_all)
            matched_sigs = self.sigpack.match_patterns(text_all, "HNR_BASIC")
            if matched_sigs:
                sig = matched_sigs[0]
                matched_rules.append(sig.id)
                confidence = sig.confidence
                category = sig.category
                penalties = sig.penalties
                source = "title"
                reasons.append("regex:basic")
        
        # 3) HNR级别检测（H3/H5/H7等，避免H.264/HDR10误报）
        if not matched_rules:
            level_match = RE_HNR_LEVEL.search(text_all)
            if level_match:
                try:
                    level = int(level_match.group("level"))
                    matched_sigs = self.sigpack.match_patterns(text_all, "HNR_LEVEL")
                    if matched_sigs:
                        sig = matched_sigs[0]
                        matched_rules.append(sig.id)
                        confidence = sig.confidence
                        category = sig.category
                        penalties = sig.penalties
                        source = "title"
                        reasons.append(f"regex:level (H{level})")
                except (ValueError, IndexError):
                    pass
        
        # 4) 使用签名包匹配
        if not matched_rules:
            matched_sigs = self.sigpack.match_patterns(text_all)
            if matched_sigs:
                sig = matched_sigs[0]
                matched_rules.append(sig.id)
                confidence = sig.confidence
                category = sig.category
                penalties = sig.penalties
                source = "title"
                reasons.append(f"signature:{sig.id}")
        
        # 5) 启发式检测（改进的启发式检测）
        if not matched_rules:
            heuristic_result = self._heuristic_detection(text_all, badges_html)
            if heuristic_result:
                matched_rules.append("heuristic")
                confidence = heuristic_result["confidence"]
                category = heuristic_result["category"]
                penalties = heuristic_result.get("penalties", {})
                source = "heuristic"
                reasons.extend(heuristic_result.get("reasons", []))
        
        # 确定结果
        if confidence >= 0.8:
            verdict = HNRVerdict.BLOCKED
            message = f"检测到HNR风险: {', '.join(matched_rules)}"
            if level:
                message += f" (H{level})"
        elif confidence >= 0.3:
            verdict = HNRVerdict.SUSPECTED
            message = f"疑似HNR风险: {', '.join(matched_rules)}"
            if level:
                message += f" (H{level})"
        else:
            verdict = HNRVerdict.PASS
            message = "无HNR风险"
        
        return HNRDetectionResult(
            verdict=verdict,
            confidence=confidence,
            matched_rules=matched_rules,
            category=category,
            penalties=penalties,
            message=message,
            level=level,
            source=source
        )
    
    def _match_signature(
        self,
        signature: Dict[str, Any],
        text: str,
        html: str,
        site_rules: Dict[str, Any]
    ) -> bool:
        """匹配签名规则（保留兼容性）"""
        patterns = signature.get("patterns", {})
        
        # 文本匹配
        text_patterns = patterns.get("text", [])
        for pattern in text_patterns:
            if pattern.lower() in text.lower():
                return True
        
        # 正则匹配
        regex_patterns = patterns.get("regex", [])
        for pattern in regex_patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            except re.error:
                logger.warning(f"无效的正则表达式: {pattern}")
        
        # HTML匹配（如果需要）
        if html:
            for pattern in text_patterns:
                if pattern.lower() in html.lower():
                    return True
        
        return False
    
    def _heuristic_detection(
        self, 
        text: str, 
        badges_html: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        启发式检测 - 改进的检测逻辑（整合自acq-guardian）
        
        检测未知标签和HNR相关关键词组合
        """
        reasons = []
        score = 0.0
        
        # 1. 检测关键词共现（考核/命中/保种 + 小时/天/做种/时长）
        if cooccur(text, {"考核", "命中", "保种"}, {"小时", "天", "做种", "时长"}):
            score += 0.4
            reasons.append("heuristic:cooccur")
        
        # 2. 检测H-<num>形状（在HTML中，但不是编解码器/HDR）
        if badges_html:
            level_match = RE_HNR_LEVEL.search(badges_html)
            if level_match:
                score += 0.3
                reasons.append("heuristic:shape")
        
        # 3. 检测未知标签片段（新标签）
        novel_tokens = []
        for token in set(badges_html.split()):
            if (token and 
                token not in self.sigpack.known_badges and 
                len(token) <= 8 and 
                any(c.isalpha() for c in token)):
                if any(keyword in token.lower() for keyword in ["hnr", "hit", "保种", "考核"]):
                    novel_tokens.append(token)
        
        if novel_tokens:
            score += 0.2
            reasons.append(f"heuristic:novel({','.join(novel_tokens[:3])})")
        
        # 4. 检测常见的HNR相关关键词组合
        hnr_keywords = ["hit", "run", "penalty", "ban", "警告", "惩罚", "考核", "保种"]
        found_keywords = [kw for kw in hnr_keywords if kw in text]
        
        if len(found_keywords) >= 2:
            score += 0.1
            reasons.append(f"heuristic:keywords({','.join(found_keywords[:3])})")
        
        if score >= 0.3:
            return {
                "confidence": min(score, 1.0),
                "category": "HEURISTIC",
                "penalties": {},
                "reasons": reasons
            }
        
        return None
    
    def calculate_risk_score(
        self,
        current_ratio: float,
        required_ratio: float,
        seed_time_hours: float,
        required_seed_time_hours: float,
        detection_result: Optional[HNRDetectionResult] = None
    ) -> float:
        """计算HNR风险评分"""
        risk_score = 0.0
        
        # 基于分享率的风险
        if required_ratio > 0:
            ratio_risk = max(0, 1 - (current_ratio / required_ratio))
            risk_score += ratio_risk * 0.5
        
        # 基于做种时间的风险
        if required_seed_time_hours > 0:
            time_risk = max(0, 1 - (seed_time_hours / required_seed_time_hours))
            risk_score += time_risk * 0.3
        
        # 基于检测结果的风险
        if detection_result:
            if detection_result.verdict == HNRVerdict.BLOCKED:
                risk_score += 0.2
            elif detection_result.verdict == HNRVerdict.SUSPECTED:
                risk_score += 0.1
        
        return min(1.0, risk_score)

