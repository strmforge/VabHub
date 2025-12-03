"""
过往版本功能适配器 - 允许直接调用过往版本的功能
整合了所有过往版本的实现，提供统一的调用接口
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import importlib.util
import logging
from loguru import logger

# 添加过往版本的路径到sys.path
# 计算项目根目录：从当前文件到项目根目录
# __file__: VabHub/backend/app/core/legacy_adapter.py
# 需要向上4级到达项目根目录: F:\VabHub项目
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent.parent.parent.parent.parent  # 向上5级到 VabHub项目 目录

LEGACY_PATHS = {
    "vabhub_1": _project_root / "VabHub-1" / "backend",
    "vabhub_14": _project_root / "VabHub1.4版" / "VabHub-Core" / "core",
    "vabhub_variant": _project_root / "VabHub-变异版" / "vabhub-Core" / "core",
    "vabhub_lingma": _project_root / "VabHub-Lingma版" / "vabhub-Core" / "core",
}

# 功能映射表 - 记录功能在哪个版本中
FUNCTION_REGISTRY: Dict[str, Dict[str, Any]] = {
    # 推荐引擎
    "recommendation_engine": {
        "vabhub_1": "modules.ai.recommendation.recommendation_engine.RecommendationEngine",
        "vabhub_14": "core.recommendation_engine.RecommendationEngine",
        "description": "推荐引擎 - 协同过滤、内容推荐、混合推荐"
    },
    "intelligent_recommendation": {
        "vabhub_1": "modules.ai.core.intelligent_content_recommendation.IntelligentContentRecommendationEngine",
        "description": "智能内容推荐引擎 - 用户画像分析、内容相似度分析"
    },
    "simple_recommendation": {
        "vabhub_1": "modules.ai.core.simple_recommendation_engine.SimpleRecommendationEngine",
        "description": "简化版推荐引擎 - 基于嵌入向量的推荐"
    },
    
    # 媒体识别
    "media_parser": {
        "vabhub_1": "modules.media.parser.filename_parser.FilenameParser",
        "description": "媒体文件解析器 - 文件名解析、类型识别"
    },
    "media_identification": {
        "vabhub_1": "modules.media.media_identification_service.MediaIdentificationService",
        "description": "媒体识别服务 - 基于文件名和元数据的识别"
    },
    "enhanced_media_identification": {
        "vabhub_1": "modules.media.enhanced_media_identification_service.EnhancedMediaIdentificationService",
        "description": "增强媒体识别服务 - AI增强的识别"
    },
    
    # 榜单系统
    "music_charts": {
        "vabhub_1": "core.music_charts.MusicChartsService",
        "description": "音乐榜单服务 - QQ音乐、网易云音乐、Spotify等"
    },
    "charts_tmdb": {
        "vabhub_14": "plugins.charts_tmdb_plugin.ChartsTMDBPlugin",
        "description": "TMDB影视榜单插件"
    },
    "charts_douban": {
        "vabhub_14": "plugins.charts_douban_plugin.ChartsDoubanPlugin",
        "description": "豆瓣影视榜单插件"
    },
    
    # AI功能
    "ai_classifier": {
        "vabhub_1": "modules.ai.classifier.ai_classifier.AIClassifier",
        "description": "AI分类器 - 媒体内容分类"
    },
    "collaborative_filtering": {
        "vabhub_1": "modules.ai.core.collaborative_filtering.CollaborativeFiltering",
        "description": "协同过滤算法"
    },
    "content_based_recommender": {
        "vabhub_1": "modules.ai.core.content_based_recommender.ContentBasedRecommender",
        "description": "基于内容的推荐"
    },
    
    # 下载管理
    "download_manager": {
        "vabhub_1": "modules.download.download_service.DownloadService",
        "description": "下载服务 - 统一下载管理"
    },
    "qbittorrent_client": {
        "vabhub_1": "modules.download.clients.qbittorrent_client.QBittorrentClient",
        "description": "qBittorrent客户端"
    },
    "transmission_client": {
        "vabhub_1": "modules.download.clients.transmission_client.TransmissionClient",
        "description": "Transmission客户端"
    },
    
    # 缓存管理
    "cache_manager": {
        "vabhub_1": "modules.cache.cache_manager.CacheManager",
        "description": "缓存管理器 - 多级缓存"
    },
    
    # 插件系统
    "plugin_manager": {
        "vabhub_14": "core.plugin_manager.PluginManager",
        "description": "插件管理器"
    },
}


class LegacyAdapter:
    """过往版本功能适配器"""
    
    def __init__(self):
        self._loaded_modules: Dict[str, Any] = {}
        self._loaded_classes: Dict[str, Any] = {}
        self._instances: Dict[str, Any] = {}
        logger.info("初始化过往版本功能适配器")
    
    def _load_module(self, version: str, module_path: str) -> Optional[Any]:
        """加载模块"""
        cache_key = f"{version}:{module_path}"
        
        if cache_key in self._loaded_modules:
            return self._loaded_modules[cache_key]
        
        try:
            base_path = LEGACY_PATHS.get(version)
            if not base_path or not base_path.exists():
                logger.warning(f"版本路径不存在: {version} - {base_path}")
                return None
            
            # 添加到sys.path（先添加，以便处理相对导入）
            if str(base_path) not in sys.path:
                sys.path.insert(0, str(base_path))
            
            # 尝试多种路径策略
            possible_paths = []
            
            # 策略1: 作为包导入（__init__.py）
            package_path = base_path / module_path.replace(".", "/") / "__init__.py"
            if package_path.exists():
                possible_paths.append(("package", package_path))
            
            # 策略2: 作为模块文件（.py）
            module_file_path = base_path / f"{module_path.replace('.', '/')}.py"
            if module_file_path.exists():
                possible_paths.append(("module", module_file_path))
            
            # 策略3: 使用标准导入（需要模块在sys.path中）
            try:
                module = __import__(module_path, fromlist=[""])
                if module:
                    self._loaded_modules[cache_key] = module
                    logger.info(f"成功加载模块（标准导入）: {version}:{module_path}")
                    return module
            except ImportError:
                pass
            
            # 尝试文件加载
            for path_type, full_path in possible_paths:
                try:
                    module_name = module_path.split(".")[-1]
                    spec = importlib.util.spec_from_file_location(module_name, full_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        # 设置模块的 __package__ 属性，帮助处理相对导入
                        if path_type == "package":
                            module.__package__ = ".".join(module_path.split(".")[:-1])
                        spec.loader.exec_module(module)
                        self._loaded_modules[cache_key] = module
                        logger.info(f"成功加载模块（{path_type}）: {version}:{module_path}")
                        return module
                except Exception as e:
                    logger.debug(f"加载路径失败 {path_type}:{full_path}: {e}")
                    continue
            
            logger.warning(f"模块文件不存在: {module_path} (版本: {version})")
            return None
            
        except Exception as e:
            logger.error(f"加载模块失败 {version}:{module_path}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def _get_class(self, function_name: str, version: str = None) -> Optional[type]:
        """获取类"""
        if function_name not in FUNCTION_REGISTRY:
            logger.warning(f"功能未注册: {function_name}")
            return None
        
        func_info = FUNCTION_REGISTRY[function_name]
        
        # 如果指定了版本，使用该版本
        if version and version in func_info:
            module_path = func_info[version]
        else:
            # 使用第一个可用版本
            available_versions = [v for v in func_info.keys() if v != "description"]
            if not available_versions:
                logger.warning(f"功能无可用版本: {function_name}")
                return None
            module_path = func_info[available_versions[0]]
            version = available_versions[0]
        
        cache_key = f"{function_name}:{version}"
        if cache_key in self._loaded_classes:
            return self._loaded_classes[cache_key]
        
        # 解析模块路径和类名
        if ":" in module_path:
            module_path, class_name = module_path.split(":", 1)
        else:
            parts = module_path.split(".")
            class_name = parts[-1]
            module_path = ".".join(parts[:-1])
        
        # 加载模块
        module = self._load_module(version, module_path)
        if not module:
            return None
        
        # 获取类
        if hasattr(module, class_name):
            cls = getattr(module, class_name)
            self._loaded_classes[cache_key] = cls
            logger.info(f"成功加载类: {function_name} - {class_name}")
            return cls
        
        logger.warning(f"类不存在: {module_path}.{class_name}")
        return None
    
    def get_instance(self, function_name: str, version: str = None, **kwargs) -> Optional[Any]:
        """获取实例（单例模式）"""
        cache_key = f"{function_name}:{version}:{hash(str(kwargs))}"
        
        if cache_key in self._instances:
            return self._instances[cache_key]
        
        cls = self._get_class(function_name, version)
        if not cls:
            return None
        
        try:
            instance = cls(**kwargs)
            self._instances[cache_key] = instance
            logger.info(f"创建实例: {function_name}")
            return instance
        except Exception as e:
            logger.error(f"创建实例失败 {function_name}: {e}")
            return None
    
    def call_function(self, function_name: str, method_name: str, version: str = None, **kwargs) -> Any:
        """调用功能方法"""
        instance = self.get_instance(function_name, version)
        if not instance:
            return None
        
        if not hasattr(instance, method_name):
            logger.warning(f"方法不存在: {function_name}.{method_name}")
            return None
        
        method = getattr(instance, method_name)
        try:
            if callable(method):
                return method(**kwargs)
            else:
                return method
        except Exception as e:
            logger.error(f"调用方法失败 {function_name}.{method_name}: {e}")
            return None
    
    def get_available_functions(self) -> Dict[str, Dict[str, Any]]:
        """获取所有可用功能"""
        result = {}
        for func_name, func_info in FUNCTION_REGISTRY.items():
            result[func_name] = {
                "description": func_info.get("description", ""),
                "versions": [v for v in func_info.keys() if v != "description"]
            }
        return result
    
    def register_function(self, name: str, version: str, module_path: str, description: str = ""):
        """注册新功能"""
        if name not in FUNCTION_REGISTRY:
            FUNCTION_REGISTRY[name] = {}
        
        FUNCTION_REGISTRY[name][version] = module_path
        if description:
            FUNCTION_REGISTRY[name]["description"] = description
        
        logger.info(f"注册功能: {name} - {version}:{module_path}")


# 全局适配器实例
_legacy_adapter = None


def get_legacy_adapter() -> LegacyAdapter:
    """获取全局适配器实例"""
    global _legacy_adapter
    if _legacy_adapter is None:
        _legacy_adapter = LegacyAdapter()
    return _legacy_adapter


# 便捷函数
def get_recommendation_engine(version: str = None):
    """获取推荐引擎"""
    adapter = get_legacy_adapter()
    return adapter.get_instance("recommendation_engine", version)


def get_media_parser(version: str = None):
    """获取媒体解析器"""
    adapter = get_legacy_adapter()
    return adapter.get_instance("media_parser", version)


def get_music_charts_service(version: str = None):
    """获取音乐榜单服务"""
    adapter = get_legacy_adapter()
    return adapter.get_instance("music_charts", version)


def get_intelligent_recommendation(version: str = None):
    """获取智能推荐引擎"""
    adapter = get_legacy_adapter()
    return adapter.get_instance("intelligent_recommendation", version)

