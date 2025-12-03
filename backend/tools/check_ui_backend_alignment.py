"""
前后端对齐检查工具
检查后端API是否满足前端UI的期望
参考vabhub_gap_patch实现
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Set, Any
import httpx
from loguru import logger

from scripts.api_test_config import API_PREFIX as CONFIG_API_PREFIX


def load_expected_endpoints(file_path: str) -> Set[str]:
    """加载期望的API端点列表"""
    expected = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                # 移除HTTP方法前缀（如果有）
                if ' ' in line:
                    method, path = line.split(' ', 1)
                    path = path.strip()
                else:
                    path = line
                
                # 标准化路径格式（移除尾随斜杠，除非是根路径）
                if path and path != '/':
                    path = path.rstrip('/')
                
                expected.add(path)
    except FileNotFoundError:
        logger.error(f"期望端点文件不存在: {file_path}")
        return set()
    except Exception as e:
        logger.error(f"加载期望端点文件失败: {e}")
        return set()
    
    return expected


def fetch_openapi_spec(openapi_url: str) -> Dict[str, Any]:
    """获取OpenAPI规范"""
    try:
        response = httpx.get(openapi_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"获取OpenAPI规范失败: {e}")
        return {}


def normalize_path_params(path: str) -> str:
    """
    标准化路径参数名，将不同的参数名映射到通用名称
    
    例如：
    - {task_id} -> {id}
    - {download_id} -> {id}
    - {subscription_id} -> {id}
    - {sid} -> {id}
    - {tid} -> {id}
    - {media_id} -> {id}
    - {site_id} -> {id}
    - {did} -> {id}
    - {pid} -> {id}
    """
    import re
    # 参数名映射表（将不同的参数名统一为通用名称）
    param_mapping = {
        'task_id': 'id',
        'download_id': 'id',
        'subscription_id': 'id',
        'sid': 'id',
        'tid': 'id',
        'media_id': 'id',
        'site_id': 'id',
        'did': 'id',
        'pid': 'id',
        'track_id': 'id',
        'douban_id': 'id',
        'subject_id': 'id',
        'storage_type': 'type',
        'server': 'id',
        'key': 'id',
        'target_type': 'type',
        'target_id': 'id',
        'backup_id': 'id',
        'notification_id': 'id',
        'subtitle_id': 'id',
        'history_id': 'id',
        'experiment_id': 'id',
        'alert_id': 'id',
        'job_id': 'id',
        'execution_id': 'id',
        'workflow_id': 'id',
        'plugin_name': 'name',
        'check_name': 'name',
        'category': 'name',
        'storage_id': 'id',
        'directory_id': 'id',
        'server_id': 'id',
        'user_id': 'id',
        'tmdb_id': 'id',
        'person_id': 'id'
    }
    
    # 替换路径参数
    def replace_param(match):
        param_name = match.group(1)
        normalized_name = param_mapping.get(param_name, param_name)
        return f"{{{normalized_name}}}"
    
    # 匹配 {param_name} 格式的参数
    normalized = re.sub(r'\{(\w+)\}', replace_param, path)
    return normalized


def extract_endpoints(openapi_spec: Dict[str, Any]) -> Set[str]:
    """从OpenAPI规范中提取所有端点"""
    endpoints = set()
    
    paths = openapi_spec.get("paths", {})
    for path, methods in paths.items():
        # 标准化路径格式（移除尾随斜杠，除非是根路径）
        normalized_path = path.rstrip('/') if path != '/' else path
        
        # 将历史前缀 (/api/v1) 转换为当前 API_PREFIX
        if normalized_path.startswith('/api/v1/'):
            normalized_path = CONFIG_API_PREFIX.rstrip('/') + normalized_path[len('/api/v1'):]
        elif normalized_path == '/api/v1':
            normalized_path = CONFIG_API_PREFIX.rstrip('/') or '/'
        
        endpoints.add(normalized_path)
    
    return endpoints


def compare_endpoints(
    expected: Set[str],
    actual: Set[str]
) -> Dict[str, Any]:
    """
    比较期望端点和实际端点
    支持参数名差异的智能匹配（例如 {task_id} 和 {download_id} 视为相同）
    """
    # 创建参数名标准化后的映射
    expected_normalized = {normalize_path_params(ep): ep for ep in expected}
    actual_normalized = {normalize_path_params(ep): ep for ep in actual}
    
    # 找到匹配的端点（基于标准化后的路径）
    matched_normalized = expected_normalized.keys() & actual_normalized.keys()
    
    # 转换为原始端点名称
    matched = {expected_normalized[norm] for norm in matched_normalized}
    
    # 找到缺失的端点（期望但不在实际中的）
    missing_normalized = expected_normalized.keys() - actual_normalized.keys()
    missing = {expected_normalized[norm] for norm in missing_normalized}
    
    # 找到额外的端点（实际但不在期望中的）
    extra_normalized = actual_normalized.keys() - expected_normalized.keys()
    # 只包含那些在原始期望列表中不存在的端点
    extra = {actual_normalized[norm] for norm in extra_normalized 
             if actual_normalized[norm] not in expected}
    
    # 对于WebSocket端点，特殊处理（OpenAPI可能不包含WebSocket）
    if '/api/ws/ws' in missing:
        # 检查是否有类似的WebSocket端点
        ws_variants = [ep for ep in actual if 'ws' in ep.lower() or 'websocket' in ep.lower()]
        if ws_variants:
            # 如果找到WebSocket相关端点，认为匹配
            missing.discard('/api/ws/ws')
            matched.add('/api/ws/ws')
    
    return {
        "missing": sorted(list(missing)),
        "extra": sorted(list(extra)),
        "matched": sorted(list(matched)),
        "total_expected": len(expected),
        "total_actual": len(actual),
        "coverage": len(matched) / len(expected) * 100 if expected else 0
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="检查前后端API对齐情况")
    parser.add_argument(
        "--openapi",
        type=str,
        default="http://localhost:8001/openapi.json",
        help="OpenAPI规范URL"
    )
    parser.add_argument(
        "--expected",
        type=str,
        default="tools/ui_expected_endpoints.txt",
        help="期望端点文件路径"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="alignment_report.json",
        help="输出报告文件路径（JSON格式）"
    )
    
    args = parser.parse_args()
    
    logger.info("开始检查前后端API对齐情况...")
    logger.info(f"OpenAPI URL: {args.openapi}")
    logger.info(f"期望端点文件: {args.expected}")
    
    # 1. 加载期望端点
    logger.info("加载期望端点...")
    expected_endpoints = load_expected_endpoints(args.expected)
    logger.info(f"期望端点数量: {len(expected_endpoints)}")
    
    # 2. 获取OpenAPI规范
    logger.info("获取OpenAPI规范...")
    openapi_spec = fetch_openapi_spec(args.openapi)
    if not openapi_spec:
        logger.error("无法获取OpenAPI规范，退出")
        sys.exit(1)
    
    # 3. 提取实际端点
    logger.info("提取实际端点...")
    actual_endpoints = extract_endpoints(openapi_spec)
    logger.info(f"实际端点数量: {len(actual_endpoints)}")
    
    # 4. 比较端点
    logger.info("比较端点...")
    comparison = compare_endpoints(expected_endpoints, actual_endpoints)
    
    # 5. 输出结果
    print("\n" + "="*60)
    print("前后端API对齐检查结果")
    print("="*60)
    print(f"期望端点总数: {comparison['total_expected']}")
    print(f"实际端点总数: {comparison['total_actual']}")
    print(f"匹配端点数量: {len(comparison['matched'])}")
    print(f"覆盖率: {comparison['coverage']:.2f}%")
    print(f"缺失端点数量: {len(comparison['missing'])}")
    print(f"额外端点数量: {len(comparison['extra'])}")
    
    if comparison['missing']:
        print("\n缺失的端点:")
        for endpoint in comparison['missing']:
            print(f"  [MISSING] {endpoint}")
    
    if comparison['extra']:
        print("\n额外的端点（不在期望列表中）:")
        for endpoint in comparison['extra']:
            print(f"  [EXTRA] {endpoint}")
    
    if not comparison['missing'] and not comparison['extra']:
        print("\n[OK] 所有端点都匹配！")
    
    # 6. 保存报告
    report = {
        "summary": {
            "total_expected": comparison['total_expected'],
            "total_actual": comparison['total_actual'],
            "matched": len(comparison['matched']),
            "missing": len(comparison['missing']),
            "extra": len(comparison['extra']),
            "coverage": comparison['coverage']
        },
        "missing_endpoints": comparison['missing'],
        "extra_endpoints": comparison['extra'],
        "matched_endpoints": comparison['matched']
    }
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"报告已保存到: {args.output}")
    
    # 7. 返回退出码
    if comparison['missing']:
        sys.exit(1)  # 有缺失端点，返回错误码
    else:
        sys.exit(0)  # 无缺失端点，返回成功码


if __name__ == "__main__":
    main()

