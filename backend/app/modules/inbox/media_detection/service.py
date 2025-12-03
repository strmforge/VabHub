"""
媒体类型检测服务

聚合多个检测器，提供统一的检测接口。
"""

from typing import List, Optional
from loguru import logger

from app.core.config import settings
from app.modules.inbox.models import InboxItem
from .base import MediaTypeDetector, MediaTypeGuess
from .extension_detector import ExtensionDetector
from .novel_txt_detector import NovelTxtDetector
from .pt_category_detector import PTCategoryDetector


class MediaTypeDetectionService:
    """
    媒体类型检测服务
    
    聚合多个检测器，按优先级尝试检测，返回最佳结果。
    """
    
    def __init__(self, detectors: List[MediaTypeDetector], min_score: float):
        """
        初始化检测服务
        
        Args:
            detectors: 检测器列表（按优先级排序）
            min_score: 最低置信度阈值
        """
        self._detectors = detectors
        self._min_score = min_score
    
    def detect(self, item: InboxItem) -> MediaTypeGuess:
        """
        检测项目的媒体类型
        
        Args:
            item: 待检测的项目
        
        Returns:
            MediaTypeGuess: 检测结果（如果无法识别，返回 unknown）
        """
        guesses: List[MediaTypeGuess] = []
        
        # 遍历所有检测器
        for detector in self._detectors:
            try:
                guess = detector.guess(item)
                if guess is not None:
                    guesses.append(guess)
            except Exception as e:
                # 记录警告日志，不中断整个流程
                logger.warning(f"检测器 {detector.name} 执行失败: {e}")
                continue
        
        # 如果没有检测器匹配
        if not guesses:
            return MediaTypeGuess(
                media_type="unknown",
                score=0.0,
                reason="no_detector_match"
            )
        
        # 按 score 降序排序，取最高分
        best = max(guesses, key=lambda g: g.score)
        
        # 如果最高分低于阈值，返回 unknown
        if best.score < self._min_score:
            return MediaTypeGuess(
                media_type="unknown",
                score=best.score,
                reason=f"below_min_score:{best.reason}"
            )
        
        return best


def get_default_detection_service() -> MediaTypeDetectionService:
    """
    获取默认的检测服务实例
    
    根据配置初始化一组检测器。
    检测器按优先级排序：PT 分类检测器（高可信度） > Novel TXT 检测器 > 扩展名检测器（兜底）
    
    Returns:
        MediaTypeDetectionService: 默认检测服务
    """
    detectors: List[MediaTypeDetector] = []
    
    # 1. PT 分类检测器（高可信度，优先）
    if settings.INBOX_PT_CATEGORY_DETECTOR_ENABLED:
        detectors.append(
            PTCategoryDetector(score=0.95)
        )
    
    # 2. Novel TXT 检测器（对 txt 更细致）
    detectors.append(NovelTxtDetector())
    
    # 3. 扩展名检测器（兜底）
    detectors.append(ExtensionDetector())
    
    return MediaTypeDetectionService(
        detectors=detectors,
        min_score=settings.INBOX_DETECTION_MIN_SCORE
    )

