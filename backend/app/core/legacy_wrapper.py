"""
过往版本功能包装器 - 提供更友好的调用接口
"""

from typing import Dict, List, Optional, Any
from loguru import logger
from app.core.legacy_adapter import get_legacy_adapter, get_recommendation_engine, get_media_parser


class RecommendationWrapper:
    """推荐引擎包装器"""
    
    def __init__(self, version: str = "vabhub_1"):
        self.version = version
        self._engine = None
    
    def _get_engine(self):
        """获取推荐引擎实例"""
        if self._engine is None:
            self._engine = get_recommendation_engine(self.version)
        return self._engine
    
    async def get_recommendations(
        self,
        user_id: int,
        limit: int = 20,
        algorithm: str = "hybrid"
    ) -> List[Dict[str, Any]]:
        """获取推荐"""
        try:
            engine = self._get_engine()
            if not engine:
                logger.warning("推荐引擎不可用，返回空列表")
                return []
            
            # 调用推荐引擎
            recommendations = []
            
            # 优先使用 update_recommendations（同步方法）
            if hasattr(engine, "update_recommendations"):
                try:
                    recommendations = engine.update_recommendations(user_id)
                    # 确保返回格式正确
                    if recommendations and isinstance(recommendations, list):
                        # 格式化结果
                        formatted = []
                        for rec in recommendations[:limit]:
                            if isinstance(rec, dict):
                                formatted.append({
                                    "media_id": str(rec.get("media_id", rec.get("id", ""))),
                                    "score": float(rec.get("score", 0.0)),
                                    "reason": rec.get("reason", rec.get("reasons", "推荐")),
                                    "confidence": float(rec.get("confidence", rec.get("score", 0.0))),
                                    "recommendation_type": algorithm
                                })
                        return formatted
                except Exception as e:
                    logger.warning(f"调用 update_recommendations 失败: {e}")
            
            # 尝试异步方法
            if hasattr(engine, "get_recommendations"):
                try:
                    import asyncio
                    import inspect
                    method = getattr(engine, "get_recommendations")
                    if inspect.iscoroutinefunction(method):
                        recommendations = await method(user_id=user_id, limit=limit)
                    else:
                        recommendations = method(user_id=user_id, limit=limit)
                    return recommendations
                except Exception as e:
                    logger.warning(f"调用 get_recommendations 失败: {e}")
            
            # 如果没有找到合适的方法，返回空列表
            logger.warning("推荐引擎不支持推荐方法")
            return []
                
        except Exception as e:
            logger.error(f"获取推荐失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []


class MediaParserWrapper:
    """媒体解析器包装器"""
    
    def __init__(self, version: str = "vabhub_1"):
        self.version = version
        self._parser = None
    
    def _get_parser(self):
        """获取解析器实例"""
        if self._parser is None:
            self._parser = get_media_parser(self.version)
        return self._parser
    
    def parse_filename(self, file_path: str) -> Optional[Dict[str, Any]]:
        """解析文件名"""
        try:
            parser = self._get_parser()
            if not parser:
                logger.warning("媒体解析器不可用")
                return None
            
            # 尝试 parse 方法（新版本）
            if hasattr(parser, "parse"):
                result = parser.parse(file_path)
                # 转换为字典格式
                if result:
                    # 处理 ParsedMediaInfo 对象
                    media_type = getattr(result, "media_type", None)
                    if hasattr(media_type, "value"):
                        type_str = media_type.value
                    elif isinstance(media_type, str):
                        type_str = media_type
                    else:
                        type_str = "unknown"
                    
                    return {
                        "title": getattr(result, "title", ""),
                        "year": getattr(result, "year", None),
                        "season": getattr(result, "season", None),
                        "episode": getattr(result, "episode", None),
                        "type": type_str,
                        "confidence": getattr(result, "confidence", 0.0),
                        "original_title": getattr(result, "original_title", None),
                        "resolution": getattr(result, "resolution", None),
                        "source": getattr(result, "source", None),
                        "video_codec": getattr(result, "video_codec", None),
                        "audio_codec": getattr(result, "audio_codec", None),
                        "release_group": getattr(result, "release_group", None)
                    }
            
            # 尝试 parse_filename 方法（旧版本）
            elif hasattr(parser, "parse_filename"):
                result = parser.parse_filename(file_path)
                # 转换为字典格式
                if result:
                    # 处理字典或对象
                    if isinstance(result, dict):
                        return result
                    else:
                        return {
                            "title": getattr(result, "title", ""),
                            "year": getattr(result, "year", None),
                            "season": getattr(result, "season", None),
                            "episode": getattr(result, "episode", None),
                            "type": getattr(result, "type", getattr(result, "media_type", "unknown")),
                            "confidence": getattr(result, "confidence", 0.0)
                        }
            
            logger.warning("媒体解析器不支持解析方法")
            return None
            
        except Exception as e:
            logger.error(f"解析文件名失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None


class LegacyFunctionRegistry:
    """过往版本功能注册表"""
    
    @staticmethod
    def get_all_functions() -> Dict[str, Dict[str, Any]]:
        """获取所有可用功能"""
        adapter = get_legacy_adapter()
        return adapter.get_available_functions()
    
    @staticmethod
    def call_function(
        function_name: str,
        method_name: str,
        version: str = None,
        **kwargs
    ) -> Any:
        """调用功能方法"""
        adapter = get_legacy_adapter()
        return adapter.call_function(function_name, method_name, version, **kwargs)

