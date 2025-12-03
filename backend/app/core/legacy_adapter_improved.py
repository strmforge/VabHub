"""
改进的过往版本功能适配器 - 增强兼容性和错误处理
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import importlib.util
import importlib
from loguru import logger

from app.core.legacy_adapter import LEGACY_PATHS, FUNCTION_REGISTRY


class ImprovedLegacyAdapter:
    """改进的过往版本功能适配器"""
    
    def __init__(self):
        self._loaded_modules: Dict[str, Any] = {}
        self._loaded_classes: Dict[str, Any] = {}
        self._instances: Dict[str, Any] = {}
        logger.info("初始化改进的过往版本功能适配器")
    
    def _ensure_path_in_syspath(self, base_path: Path):
        """确保路径在sys.path中"""
        path_str = str(base_path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
            logger.debug(f"添加路径到sys.path: {path_str}")
    
    def _try_standard_import(self, module_path: str, base_path: Path) -> Optional[Any]:
        """尝试标准导入"""
        try:
            self._ensure_path_in_syspath(base_path)
            module = importlib.import_module(module_path)
            logger.info(f"标准导入成功: {module_path}")
            return module
        except ImportError as e:
            logger.debug(f"标准导入失败: {module_path} - {e}")
            return None
        except Exception as e:
            logger.debug(f"标准导入出错: {module_path} - {e}")
            return None
    
    def _try_file_import(self, module_path: str, base_path: Path) -> Optional[Any]:
        """尝试文件导入"""
        # 尝试作为包
        package_path = base_path / module_path.replace(".", "/") / "__init__.py"
        if package_path.exists():
            try:
                module_name = module_path.split(".")[-1]
                spec = importlib.util.spec_from_file_location(module_name, package_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    # 设置包路径
                    parent_path = ".".join(module_path.split(".")[:-1])
                    if parent_path:
                        module.__package__ = parent_path
                    spec.loader.exec_module(module)
                    logger.info(f"文件导入成功（包）: {module_path}")
                    return module
            except Exception as e:
                logger.debug(f"包导入失败: {module_path} - {e}")
        
        # 尝试作为模块文件
        module_file = base_path / f"{module_path.replace('.', '/')}.py"
        if module_file.exists():
            try:
                module_name = module_path.split(".")[-1]
                spec = importlib.util.spec_from_file_location(module_name, module_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    # 设置包路径
                    parent_path = ".".join(module_path.split(".")[:-1])
                    if parent_path:
                        module.__package__ = parent_path
                    spec.loader.exec_module(module)
                    logger.info(f"文件导入成功（模块）: {module_path}")
                    return module
            except Exception as e:
                logger.debug(f"模块导入失败: {module_path} - {e}")
        
        return None
    
    def _load_module(self, version: str, module_path: str) -> Optional[Any]:
        """加载模块（改进版）"""
        cache_key = f"{version}:{module_path}"
        
        if cache_key in self._loaded_modules:
            return self._loaded_modules[cache_key]
        
        base_path = LEGACY_PATHS.get(version)
        if not base_path or not base_path.exists():
            logger.warning(f"版本路径不存在: {version} - {base_path}")
            return None
        
        # 策略1: 尝试标准导入
        module = self._try_standard_import(module_path, base_path)
        if module:
            self._loaded_modules[cache_key] = module
            return module
        
        # 策略2: 尝试文件导入
        module = self._try_file_import(module_path, base_path)
        if module:
            self._loaded_modules[cache_key] = module
            return module
        
        logger.warning(f"无法加载模块: {version}:{module_path}")
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
        cache_key = f"{function_name}:{version}:{hash(str(sorted(kwargs.items())))}"
        
        if cache_key in self._instances:
            return self._instances[cache_key]
        
        cls = self._get_class(function_name, version)
        if not cls:
            return None
        
        try:
            # 尝试创建实例（无参数或使用提供的参数）
            instance = cls(**kwargs) if kwargs else cls()
            self._instances[cache_key] = instance
            logger.info(f"创建实例: {function_name}")
            return instance
        except TypeError as e:
            # 如果无参构造失败，尝试使用默认参数
            try:
                import inspect
                sig = inspect.signature(cls.__init__)
                # 获取有默认值的参数
                params = {}
                for param_name, param in sig.parameters.items():
                    if param_name != 'self' and param.default != inspect.Parameter.empty:
                        params[param_name] = param.default
                instance = cls(**params)
                self._instances[cache_key] = instance
                logger.info(f"创建实例（使用默认参数）: {function_name}")
                return instance
            except Exception as e2:
                logger.warning(f"创建实例失败（尝试默认参数）: {function_name} - {e2}")
                return None
        except Exception as e:
            logger.error(f"创建实例失败: {function_name} - {e}")
            return None

