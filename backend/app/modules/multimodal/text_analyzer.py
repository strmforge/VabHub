"""
文本分析器
提供文本内容分析功能（简化版）
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from loguru import logger
import re
from collections import Counter
from datetime import datetime
import hashlib
import time

# 可选依赖：TextBlob用于情感分析
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logger.warning("TextBlob未安装，情感分析将使用简化版本")

# 导入缓存系统
try:
    from app.core.cache import get_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.warning("缓存系统不可用，将跳过缓存")

# 导入性能监控
try:
    from app.modules.multimodal.metrics import MultimodalMetrics
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    logger.warning("性能监控系统不可用，将跳过性能监控")


class TextAnalyzer:
    """文本分析器（简化版，基于规则和基础NLP）"""
    
    def __init__(self, enable_cache: bool = True, cache_ttl: int = 3600):
        """
        初始化文本分析器
        
        Args:
            enable_cache: 是否启用缓存
            cache_ttl: 缓存过期时间（秒，默认1小时）
        """
        self.enable_cache = enable_cache and CACHE_AVAILABLE
        self.cache_ttl = cache_ttl
        
        if self.enable_cache:
            self.cache = get_cache()
            logger.info(f"文本分析器已启用缓存（TTL: {cache_ttl}秒）")
    
    def _calculate_text_hash(self, text: str) -> str:
        """计算文本哈希（用于缓存键）"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        分析文本内容（带缓存和性能监控）
        
        Args:
            text: 文本内容
            
        Returns:
            分析结果字典
        """
        start_time = time.time()
        cache_hit = False
        try:
            if not text:
                return {
                    "text": "",
                    "error": "文本为空"
                }
            
            # 检查缓存
            if self.enable_cache:
                text_hash = self._calculate_text_hash(text)
                cache_key = self.cache.generate_key(
                    "multimodal:text:analysis",
                    text_hash
                )
                cached_result = await self.cache.get(cache_key)
                if cached_result is not None:
                    logger.debug("从缓存获取文本分析结果")
                    # 更新文本内容（缓存中可能不包含原始文本）
                    cached_result["text"] = text
                    cache_hit = True
                    # 记录性能指标
                    if METRICS_AVAILABLE:
                        duration = time.time() - start_time
                        MultimodalMetrics.record_request(
                            operation="text_analysis",
                            cache_hit=True,
                            duration=duration,
                            error=False
                        )
                    return cached_result
            
            # 提取关键词
            keywords = self._extract_keywords(text)
            
            # 分析情感
            sentiment = self._analyze_sentiment(text)
            
            # 检测语言
            language = self._detect_language(text)
            
            # 生成摘要
            summary = self._generate_summary(text)
            
            # 分析结果
            analysis_result = {
                "text": text,
                "keywords": keywords,
                "sentiment": sentiment,
                "language": language,
                "summary": summary,
                "word_count": len(text.split()),
                "character_count": len(text),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            # 存入缓存
            if self.enable_cache:
                await self.cache.set(cache_key, analysis_result, self.cache_ttl)
            
            # 记录性能指标
            if METRICS_AVAILABLE:
                duration = time.time() - start_time
                MultimodalMetrics.record_request(
                    operation="text_analysis",
                    cache_hit=False,
                    duration=duration,
                    error=False
                )
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"文本分析失败: {e}")
            # 记录错误
            if METRICS_AVAILABLE:
                duration = time.time() - start_time
                MultimodalMetrics.record_request(
                    operation="text_analysis",
                    cache_hit=cache_hit,
                    duration=duration,
                    error=True
                )
            return {
                "text": text,
                "error": str(e),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
    
    def _extract_keywords(self, text: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """提取关键词（基于词频）"""
        try:
            # 简单的关键词提取：基于词频
            # 移除标点符号和常见停用词
            stop_words = {
                "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个",
                "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
                "自己", "这", "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
                "it", "for", "not", "on", "with", "he", "as", "you", "do", "at"
            }
            
            # 分词（简单版本，基于空格和标点）
            words = re.findall(r'\b\w+\b', text.lower())
            
            # 过滤停用词
            words = [w for w in words if w not in stop_words and len(w) > 1]
            
            # 统计词频
            word_freq = Counter(words)
            
            # 返回Top N关键词
            keywords = []
            for word, freq in word_freq.most_common(top_n):
                keywords.append({
                    "word": word,
                    "frequency": freq,
                    "score": freq / len(words) if words else 0
                })
            
            return keywords
            
        except Exception as e:
            logger.error(f"提取关键词失败: {e}")
            return []
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """分析情感（使用TextBlob或基于关键词的简化版）"""
        try:
            # 如果TextBlob可用，使用TextBlob进行更准确的情感分析
            if TEXTBLOB_AVAILABLE:
                try:
                    blob = TextBlob(text)
                    polarity = blob.sentiment.polarity  # -1 to 1
                    subjectivity = blob.sentiment.subjectivity  # 0 to 1
                    
                    # 转换为情感标签
                    if polarity > 0.1:
                        sentiment_label = "positive"
                    elif polarity < -0.1:
                        sentiment_label = "negative"
                    else:
                        sentiment_label = "neutral"
                    
                    # 计算置信度（基于极性的绝对值）
                    confidence = abs(polarity)
                    
                    # 计算正面和负面计数（基于极性）
                    positive_count = max(0, int((polarity + 1) * 10))
                    negative_count = max(0, int((1 - polarity) * 10))
                    
                    return {
                        "label": sentiment_label,
                        "score": (polarity + 1) / 2,  # 归一化到0-1
                        "polarity": polarity,  # 原始极性值（-1到1）
                        "subjectivity": subjectivity,  # 主观性（0到1）
                        "positive_count": positive_count,
                        "negative_count": negative_count,
                        "confidence": confidence,
                        "method": "textblob"
                    }
                except Exception as e:
                    logger.warning(f"TextBlob情感分析失败，使用简化版本: {e}")
            
            # 回退到基于关键词的简化版本
            positive_words = {
                "好", "棒", "优秀", "完美", "喜欢", "爱", "赞", "不错", "满意", "高兴", "开心",
                "good", "great", "excellent", "perfect", "love", "like", "happy", "wonderful"
            }
            
            negative_words = {
                "差", "坏", "糟糕", "讨厌", "不喜欢", "失望", "难过", "伤心", "愤怒", "生气",
                "bad", "terrible", "awful", "hate", "dislike", "sad", "angry", "disappointed"
            }
            
            text_lower = text.lower()
            
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            total = positive_count + negative_count
            if total == 0:
                sentiment_score = 0.5  # 中性
            else:
                sentiment_score = positive_count / total
            
            # 判断情感倾向
            if sentiment_score > 0.6:
                sentiment_label = "positive"
            elif sentiment_score < 0.4:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
            
            return {
                "label": sentiment_label,
                "score": sentiment_score,
                "positive_count": positive_count,
                "negative_count": negative_count,
                "method": "keyword_based"
            }
            
        except Exception as e:
            logger.error(f"情感分析失败: {e}")
            return {
                "label": "neutral",
                "score": 0.5,
                "positive_count": 0,
                "negative_count": 0,
                "method": "fallback"
            }
    
    def _detect_language(self, text: str) -> str:
        """检测语言（使用TextBlob或基于字符的简化版）"""
        try:
            # 如果TextBlob可用，使用TextBlob进行语言检测
            if TEXTBLOB_AVAILABLE:
                try:
                    blob = TextBlob(text)
                    language_code = blob.detect_language()
                    
                    # 语言代码映射
                    language_names = {
                        'en': 'en',
                        'zh': 'zh',
                        'zh-cn': 'zh',
                        'zh-tw': 'zh',
                        'ja': 'ja',
                        'ko': 'ko',
                        'fr': 'fr',
                        'de': 'de',
                        'es': 'es',
                        'it': 'it',
                        'pt': 'pt',
                        'ru': 'ru',
                        'ar': 'ar'
                    }
                    
                    return language_names.get(language_code, language_code)
                except Exception as e:
                    logger.warning(f"TextBlob语言检测失败，使用简化版本: {e}")
            
            # 回退到基于字符的简化版本
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            english_chars = len(re.findall(r'[a-zA-Z]', text))
            japanese_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff]', text))
            korean_chars = len(re.findall(r'[\uac00-\ud7af]', text))
            
            total_chars = chinese_chars + english_chars + japanese_chars + korean_chars
            
            if total_chars == 0:
                return "unknown"
            
            # 计算各语言占比
            chinese_ratio = chinese_chars / total_chars
            english_ratio = english_chars / total_chars
            japanese_ratio = japanese_chars / total_chars
            korean_ratio = korean_chars / total_chars
            
            # 返回占比最大的语言
            ratios = {
                "zh": chinese_ratio,
                "en": english_ratio,
                "ja": japanese_ratio,
                "ko": korean_ratio
            }
            
            return max(ratios, key=ratios.get)
            
        except Exception as e:
            logger.error(f"语言检测失败: {e}")
            return "unknown"
    
    def _generate_summary(self, text: str, max_length: int = 200) -> str:
        """生成摘要（简化版，截取前N个字符）"""
        try:
            if len(text) <= max_length:
                return text
            
            # 简单摘要：截取前N个字符，并在句号处截断
            summary = text[:max_length]
            
            # 尝试在句号处截断
            last_period = summary.rfind('.')
            last_exclamation = summary.rfind('!')
            last_question = summary.rfind('?')
            
            last_sentence_end = max(last_period, last_exclamation, last_question)
            if last_sentence_end > max_length * 0.5:  # 如果句号在摘要的后半部分
                summary = summary[:last_sentence_end + 1]
            else:
                summary = summary + "..."
            
            return summary
            
        except Exception as e:
            logger.error(f"生成摘要失败: {e}")
            return text[:max_length] if len(text) > max_length else text
    
    async def classify_text(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """
        分类文本（简化版，基于关键词匹配）
        
        Args:
            text: 文本内容
            categories: 分类列表
            
        Returns:
            分类结果
        """
        # TODO: 实现文本分类
        # 当前返回空字典，未来可以使用机器学习模型实现
        logger.info(f"文本分类功能暂未实现: {text}")
        return {
            "category": "unknown",
            "confidence": 0.0
        }
    
    async def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算文本相似度（简化版，基于共同词）
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            相似度分数（0-1）
        """
        try:
            # 简单的相似度计算：基于Jaccard相似度
            words1 = set(re.findall(r'\b\w+\b', text1.lower()))
            words2 = set(re.findall(r'\b\w+\b', text2.lower()))
            
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            
            if union == 0:
                return 0.0
            
            return intersection / union
            
        except Exception as e:
            logger.error(f"计算文本相似度失败: {e}")
            return 0.0

