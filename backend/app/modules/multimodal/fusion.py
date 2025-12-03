"""
多模态特征融合器
实现多模态特征融合、相似度计算和特征权重调整
"""

from typing import Dict, List, Optional, Any, Tuple
from loguru import logger
import numpy as np
import hashlib
import json
import time

# 可选依赖：sklearn用于特征缩放和降维
try:
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.decomposition import PCA
    from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("sklearn未安装，多模态特征融合功能将受限")

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


class MultimodalFeatureFusion:
    """多模态特征融合器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, enable_cache: bool = True, cache_ttl: int = 3600):
        """
        初始化多模态特征融合器
        
        Args:
            config: 配置字典
            enable_cache: 是否启用缓存
            cache_ttl: 缓存过期时间（秒，默认1小时）
        """
        self.config = config or {}
        
        # 特征权重（可配置）
        self.feature_weights = self.config.get('feature_weights', {
            'video': 0.4,
            'audio': 0.3,
            'text': 0.3
        })
        
        # 特征缩放器（如果sklearn可用）
        self.scalers = {}
        if SKLEARN_AVAILABLE:
            self.scalers = {
                'video': StandardScaler(),
                'audio': StandardScaler(),
                'text': StandardScaler()
            }
        
        # 缓存设置
        self.enable_cache = enable_cache and CACHE_AVAILABLE
        self.cache_ttl = cache_ttl
        if self.enable_cache:
            self.cache = get_cache()
            logger.info(f"多模态特征融合器已启用缓存（TTL: {cache_ttl}秒）")
        
        logger.info("MultimodalFeatureFusion initialized")
    
    def _calculate_features_hash(self, video_features: Optional[Dict], audio_features: Optional[Dict], text_features: Optional[Dict]) -> str:
        """计算特征哈希（用于缓存键）"""
        # 创建特征摘要
        feature_summary = {
            'video': bool(video_features),
            'audio': bool(audio_features),
            'text': bool(text_features),
            'weights': self.feature_weights
        }
        # 添加关键特征值（简化，避免完整序列化）
        if video_features:
            feature_summary['video_info'] = video_features.get('video_info', {}).get('width', 0), video_features.get('video_info', {}).get('height', 0)
        if audio_features:
            feature_summary['audio_info'] = audio_features.get('audio_info', {}).get('sample_rate', 0)
        if text_features:
            feature_summary['text_length'] = text_features.get('character_count', 0)
        
        feature_str = json.dumps(feature_summary, sort_keys=True)
        return hashlib.md5(feature_str.encode()).hexdigest()
    
    async def fuse_features(
        self,
        video_features: Optional[Dict[str, Any]] = None,
        audio_features: Optional[Dict[str, Any]] = None,
        text_features: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        融合多模态特征（带缓存和性能监控）
        
        Args:
            video_features: 视频特征字典
            audio_features: 音频特征字典
            text_features: 文本特征字典
            
        Returns:
            融合后的特征字典
        """
        start_time = time.time()
        cache_hit = False
        # 检查缓存
        if self.enable_cache:
            features_hash = self._calculate_features_hash(video_features, audio_features, text_features)
            cache_key = self.cache.generate_key(
                "multimodal:fusion",
                features_hash
            )
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                logger.debug("从缓存获取特征融合结果")
                cache_hit = True
                # 记录性能指标
                if METRICS_AVAILABLE:
                    duration = time.time() - start_time
                    MultimodalMetrics.record_request(
                        operation="feature_fusion",
                        cache_hit=True,
                        duration=duration,
                        error=False
                    )
                return cached_result
        
        try:
            fused_features = {
                "video": self._extract_video_vector(video_features) if video_features else None,
                "audio": self._extract_audio_vector(audio_features) if audio_features else None,
                "text": self._extract_text_vector(text_features) if text_features else None,
                "combined": None,
                "confidence": 0.0,
                "modalities": []
            }
            
            # 记录可用的模态
            if fused_features["video"] is not None:
                fused_features["modalities"].append("video")
            if fused_features["audio"] is not None:
                fused_features["modalities"].append("audio")
            if fused_features["text"] is not None:
                fused_features["modalities"].append("text")
            
            # 融合特征向量
            vectors = []
            weights = []
            
            if fused_features["video"] is not None:
                vectors.append(fused_features["video"])
                weights.append(self.feature_weights.get('video', 0.4))
            
            if fused_features["audio"] is not None:
                vectors.append(fused_features["audio"])
                weights.append(self.feature_weights.get('audio', 0.3))
            
            if fused_features["text"] is not None:
                vectors.append(fused_features["text"])
                weights.append(self.feature_weights.get('text', 0.3))
            
            if vectors:
                # 归一化权重
                total_weight = sum(weights)
                if total_weight > 0:
                    weights = [w / total_weight for w in weights]
                
                # 加权融合
                combined_vector = np.zeros(len(vectors[0]))
                for vec, weight in zip(vectors, weights):
                    # 归一化向量
                    vec_norm = vec / (np.linalg.norm(vec) + 1e-6)
                    combined_vector += vec_norm * weight
                
                fused_features["combined"] = combined_vector.tolist()
                fused_features["confidence"] = len(fused_features["modalities"]) / 3.0
            
            # 存入缓存
            if self.enable_cache:
                await self.cache.set(cache_key, fused_features, self.cache_ttl)
            
            # 记录性能指标
            if METRICS_AVAILABLE:
                duration = time.time() - start_time
                MultimodalMetrics.record_request(
                    operation="feature_fusion",
                    cache_hit=False,
                    duration=duration,
                    error=False
                )
            
            return fused_features
            
        except Exception as e:
            logger.error(f"特征融合失败: {e}")
            # 记录错误
            if METRICS_AVAILABLE:
                duration = time.time() - start_time
                MultimodalMetrics.record_request(
                    operation="feature_fusion",
                    cache_hit=cache_hit,
                    duration=duration,
                    error=True
                )
            return {
                "video": None,
                "audio": None,
                "text": None,
                "combined": None,
                "confidence": 0.0,
                "modalities": []
            }
    
    def _extract_video_vector(self, video_features: Dict[str, Any]) -> Optional[np.ndarray]:
        """提取视频特征向量"""
        try:
            vector = []
            
            # 从video_info提取特征
            video_info = video_features.get("video_info", {})
            vector.extend([
                video_info.get("width", 0) / 1000.0,  # 归一化
                video_info.get("height", 0) / 1000.0,  # 归一化
                video_info.get("fps", 0) / 60.0,  # 归一化
                video_info.get("bitrate", 0) / 10000000.0,  # 归一化
                video_info.get("duration", 0) / 3600.0  # 归一化到小时
            ])
            
            # 从quality_score提取特征
            quality_score = video_features.get("quality_score", 0.0)
            vector.append(quality_score / 100.0)  # 归一化到0-1
            
            # 从scenes提取特征
            scenes = video_features.get("scenes", [])
            if scenes:
                vector.append(len(scenes) / 100.0)  # 场景数量归一化
                vector.append(np.mean([s.get("confidence", 0.0) for s in scenes]))  # 平均置信度
            else:
                vector.extend([0.0, 0.0])
            
            return np.array(vector)
            
        except Exception as e:
            logger.error(f"提取视频特征向量失败: {e}")
            return None
    
    def _extract_audio_vector(self, audio_features: Dict[str, Any]) -> Optional[np.ndarray]:
        """提取音频特征向量"""
        try:
            vector = []
            
            # 从audio_info提取特征
            audio_info = audio_features.get("audio_info", {})
            vector.extend([
                audio_info.get("sample_rate", 0) / 100000.0,  # 归一化
                audio_info.get("channels", 0) / 8.0,  # 归一化
                audio_info.get("bitrate", 0) / 1000000.0,  # 归一化
                audio_info.get("duration", 0) / 3600.0  # 归一化到小时
            ])
            
            # 从quality_score提取特征
            quality_score = audio_features.get("quality_score", 0.0)
            vector.append(quality_score / 100.0)  # 归一化到0-1
            
            # 从features提取特征
            features = audio_features.get("features", {})
            if features:
                vector.extend([
                    features.get("tempo", 0) / 200.0,  # 归一化
                    features.get("energy", 0),  # 已经是0-1范围
                    features.get("loudness", 0) / 100.0,  # 归一化
                    features.get("speechiness", 0),  # 已经是0-1范围
                    features.get("acousticness", 0),  # 已经是0-1范围
                    features.get("instrumentalness", 0),  # 已经是0-1范围
                    features.get("valence", 0),  # 已经是0-1范围
                    features.get("arousal", 0)  # 已经是0-1范围
                ])
            else:
                vector.extend([0.0] * 8)
            
            return np.array(vector)
            
        except Exception as e:
            logger.error(f"提取音频特征向量失败: {e}")
            return None
    
    def _extract_text_vector(self, text_features: Dict[str, Any]) -> Optional[np.ndarray]:
        """提取文本特征向量"""
        try:
            vector = []
            
            # 从基本统计提取特征
            vector.extend([
                text_features.get("word_count", 0) / 1000.0,  # 归一化
                text_features.get("character_count", 0) / 5000.0  # 归一化
            ])
            
            # 从sentiment提取特征
            sentiment = text_features.get("sentiment", {})
            if sentiment:
                vector.extend([
                    sentiment.get("score", 0.5),  # 已经是0-1范围
                    sentiment.get("polarity", 0.0) if "polarity" in sentiment else 0.0,  # 归一化到0-1
                    sentiment.get("subjectivity", 0.5) if "subjectivity" in sentiment else 0.5,  # 已经是0-1范围
                    sentiment.get("confidence", 0.0) if "confidence" in sentiment else 0.0  # 已经是0-1范围
                ])
            else:
                vector.extend([0.5, 0.0, 0.5, 0.0])
            
            # 从keywords提取特征
            keywords = text_features.get("keywords", [])
            if keywords:
                vector.append(len(keywords) / 20.0)  # 关键词数量归一化
                vector.append(np.mean([k.get("score", 0.0) for k in keywords]))  # 平均关键词分数
            else:
                vector.extend([0.0, 0.0])
            
            return np.array(vector)
            
        except Exception as e:
            logger.error(f"提取文本特征向量失败: {e}")
            return None
    
    async def calculate_similarity(
        self,
        features1: Dict[str, Any],
        features2: Dict[str, Any],
        method: str = "cosine"
    ) -> float:
        """
        计算两个多模态特征的相似度（带缓存和性能监控）
        
        Args:
            features1: 第一个特征字典
            features2: 第二个特征字典
            method: 相似度计算方法（cosine, euclidean）
            
        Returns:
            相似度分数（0-1）
        """
        start_time = time.time()
        cache_hit = False
        # 检查缓存
        if self.enable_cache:
            # 创建特征对哈希（确保顺序无关）
            features_pair = sorted([
                self._calculate_features_hash(
                    features1.get("video"),
                    features1.get("audio"),
                    features1.get("text")
                ),
                self._calculate_features_hash(
                    features2.get("video"),
                    features2.get("audio"),
                    features2.get("text")
                )
            ])
            cache_key = self.cache.generate_key(
                "multimodal:similarity",
                features_pair[0],
                features_pair[1],
                method=method
            )
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                logger.debug("从缓存获取相似度计算结果")
                cache_hit = True
                # 记录性能指标
                if METRICS_AVAILABLE:
                    duration = time.time() - start_time
                    MultimodalMetrics.record_request(
                        operation="similarity_calculation",
                        cache_hit=True,
                        duration=duration,
                        error=False
                    )
                return cached_result
        
        try:
            # 融合特征
            fused1 = await self.fuse_features(
                video_features=features1.get("video"),
                audio_features=features1.get("audio"),
                text_features=features1.get("text")
            )
            
            fused2 = await self.fuse_features(
                video_features=features2.get("video"),
                audio_features=features2.get("audio"),
                text_features=features2.get("text")
            )
            
            # 获取融合后的向量
            vec1 = fused1.get("combined")
            vec2 = fused2.get("combined")
            
            if vec1 is None or vec2 is None:
                return 0.0
            
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            # 确保向量长度相同
            min_len = min(len(vec1), len(vec2))
            vec1 = vec1[:min_len]
            vec2 = vec2[:min_len]
            
            # 计算相似度
            if method == "cosine":
                if SKLEARN_AVAILABLE:
                    similarity = cosine_similarity([vec1], [vec2])[0][0]
                else:
                    # 手动计算余弦相似度
                    dot_product = np.dot(vec1, vec2)
                    norm1 = np.linalg.norm(vec1)
                    norm2 = np.linalg.norm(vec2)
                    similarity = dot_product / (norm1 * norm2 + 1e-6)
                
                # 归一化到0-1
                similarity = (similarity + 1) / 2
                
            elif method == "euclidean":
                if SKLEARN_AVAILABLE:
                    distance = euclidean_distances([vec1], [vec2])[0][0]
                    # 转换为相似度（距离越小，相似度越高）
                    similarity = 1.0 / (1.0 + distance)
                else:
                    # 手动计算欧氏距离
                    distance = np.linalg.norm(vec1 - vec2)
                    similarity = 1.0 / (1.0 + distance)
            else:
                logger.warning(f"未知的相似度计算方法: {method}，使用余弦相似度")
                dot_product = np.dot(vec1, vec2)
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                similarity = (np.dot(vec1, vec2) / (norm1 * norm2 + 1e-6) + 1) / 2
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"计算相似度失败: {e}")
            return 0.0
    
    def update_feature_weights(
        self,
        weights: Dict[str, float]
    ):
        """
        更新特征权重
        
        Args:
            weights: 权重字典，例如 {'video': 0.5, 'audio': 0.3, 'text': 0.2}
        """
        try:
            self.feature_weights.update(weights)
            logger.info(f"更新特征权重: {self.feature_weights}")
        except Exception as e:
            logger.error(f"更新特征权重失败: {e}")

