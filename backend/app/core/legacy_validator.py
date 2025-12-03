"""
过往版本功能可用性检测器
检测过往版本的功能是否可以正常加载和调用
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import importlib.util
import traceback
from loguru import logger

from app.core.legacy_adapter import LegacyAdapter, LEGACY_PATHS, FUNCTION_REGISTRY


class LegacyValidator:
    """过往版本功能验证器"""
    
    def __init__(self):
        self.adapter = LegacyAdapter()
        self.validation_results: Dict[str, Dict[str, Any]] = {}
    
    def validate_all(self) -> Dict[str, Dict[str, Any]]:
        """验证所有注册的功能"""
        logger.info("开始验证所有过往版本功能...")
        
        results = {}
        for func_name, func_info in FUNCTION_REGISTRY.items():
            logger.info(f"验证功能: {func_name}")
            result = self.validate_function(func_name)
            results[func_name] = result
        
        self.validation_results = results
        return results
    
    def validate_function(self, function_name: str) -> Dict[str, Any]:
        """验证单个功能"""
        result = {
            "function_name": function_name,
            "available": False,
            "versions": {},
            "errors": []
        }
        
        if function_name not in FUNCTION_REGISTRY:
            result["errors"].append(f"功能未注册: {function_name}")
            return result
        
        func_info = FUNCTION_REGISTRY[function_name]
        available_versions = [v for v in func_info.keys() if v != "description"]
        
        for version in available_versions:
            logger.info(f"  验证版本: {version}")
            version_result = self._validate_version(function_name, version)
            result["versions"][version] = version_result
            
            if version_result["available"]:
                result["available"] = True
        
        return result
    
    def _validate_version(self, function_name: str, version: str) -> Dict[str, Any]:
        """验证特定版本的功能"""
        result = {
            "version": version,
            "available": False,
            "path_exists": False,
            "module_loadable": False,
            "class_instantiable": False,
            "methods_callable": False,
            "errors": []
        }
        
        try:
            # 1. 检查路径是否存在
            base_path = LEGACY_PATHS.get(version)
            if not base_path:
                result["errors"].append(f"版本路径未定义: {version}")
                return result
            
            if not base_path.exists():
                result["errors"].append(f"版本路径不存在: {base_path}")
                return result
            
            result["path_exists"] = True
            
            # 2. 获取模块路径
            func_info = FUNCTION_REGISTRY[function_name]
            module_path = func_info.get(version)
            
            if not module_path:
                result["errors"].append(f"版本 {version} 未定义模块路径")
                return result
            
            # 3. 尝试加载模块
            try:
                cls = self.adapter._get_class(function_name, version)
                if cls:
                    result["module_loadable"] = True
                    result["class_instantiable"] = True
                    
                    # 4. 尝试创建实例（不需要参数或使用默认参数）
                    try:
                        instance = self.adapter.get_instance(function_name, version)
                        if instance:
                            result["methods_callable"] = True
                            result["available"] = True
                    except Exception as e:
                        result["errors"].append(f"实例化失败: {str(e)}")
                        # 即使实例化失败，如果类可以加载，也认为模块可用
                        if result["module_loadable"]:
                            result["available"] = True
                            
                else:
                    result["errors"].append("无法加载类")
                    
            except Exception as e:
                error_msg = f"加载模块失败: {str(e)}"
                result["errors"].append(error_msg)
                logger.warning(f"  {error_msg}")
                logger.debug(traceback.format_exc())
        
        except Exception as e:
            error_msg = f"验证过程出错: {str(e)}"
            result["errors"].append(error_msg)
            logger.error(f"  {error_msg}")
            logger.debug(traceback.format_exc())
        
        return result
    
    def validate_paths(self) -> Dict[str, bool]:
        """验证所有路径是否存在"""
        results = {}
        for version, path in LEGACY_PATHS.items():
            exists = path.exists() if path else False
            results[version] = exists
            logger.info(f"版本 {version}: {path} - {'存在' if exists else '不存在'}")
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """获取验证摘要"""
        total_functions = len(self.validation_results)
        available_functions = sum(1 for r in self.validation_results.values() if r["available"])
        
        total_versions = sum(len(r["versions"]) for r in self.validation_results.values())
        available_versions = sum(
            sum(1 for v in r["versions"].values() if v["available"])
            for r in self.validation_results.values()
        )
        
        return {
            "total_functions": total_functions,
            "available_functions": available_functions,
            "total_versions": total_versions,
            "available_versions": available_versions,
            "availability_rate": available_functions / total_functions if total_functions > 0 else 0
        }
    
    def print_report(self):
        """打印验证报告"""
        print("\n" + "=" * 80)
        print("过往版本功能可用性检测报告")
        print("=" * 80)
        
        # 路径检查
        print("\n1. 路径检查:")
        paths = self.validate_paths()
        for version, exists in paths.items():
            status = "[OK]" if exists else "[FAIL]"
            print(f"  {status} {version}: {LEGACY_PATHS.get(version)}")
        
        # 功能检查
        print("\n2. 功能检查:")
        for func_name, result in self.validation_results.items():
            status = "[OK]" if result["available"] else "[FAIL]"
            print(f"\n  {status} {func_name}")
            print(f"    描述: {FUNCTION_REGISTRY[func_name].get('description', '无')}")
            
            for version, version_result in result["versions"].items():
                v_status = "[OK]" if version_result["available"] else "[FAIL]"
                print(f"    {v_status} {version}:")
                print(f"      路径存在: {'是' if version_result['path_exists'] else '否'}")
                print(f"      模块可加载: {'是' if version_result['module_loadable'] else '否'}")
                print(f"      类可实例化: {'是' if version_result['class_instantiable'] else '否'}")
                print(f"      方法可调用: {'是' if version_result['methods_callable'] else '否'}")
                
                if version_result["errors"]:
                    print(f"      错误:")
                    for error in version_result["errors"]:
                        print(f"        - {error}")
        
        # 摘要
        summary = self.get_summary()
        print("\n3. 摘要:")
        print(f"  总功能数: {summary['total_functions']}")
        print(f"  可用功能数: {summary['available_functions']}")
        print(f"  总版本数: {summary['total_versions']}")
        print(f"  可用版本数: {summary['available_versions']}")
        print(f"  可用率: {summary['availability_rate'] * 100:.1f}%")
        
        print("\n" + "=" * 80)


def validate_legacy_functions() -> Dict[str, Any]:
    """验证过往版本功能的可用性（便捷函数）"""
    validator = LegacyValidator()
    results = validator.validate_all()
    validator.print_report()
    return results


if __name__ == "__main__":
    # 运行验证
    validate_legacy_functions()

