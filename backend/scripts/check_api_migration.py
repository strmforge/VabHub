"""
静态检查API文件是否使用统一响应模型
通过分析源代码文件来验证，不需要启动数据库
"""

import re
from pathlib import Path
from typing import List, Tuple


def check_file_uses_unified_response(file_path: Path) -> Tuple[bool, List[str]]:
    """
    检查API文件是否使用统一响应模型
    
    返回: (是否使用, 问题列表)
    """
    if not file_path.exists():
        return False, [f"文件不存在: {file_path}"]
    
    content = file_path.read_text(encoding='utf-8')
    issues = []
    
    # 检查是否导入BaseResponse
    has_base_response_import = (
        'from app.core.schemas import' in content and 
        'BaseResponse' in content
    ) or (
        'from app.core.schemas import BaseResponse' in content
    )
    
    if not has_base_response_import:
        issues.append("未导入BaseResponse")
    
    # 检查是否使用response_model=BaseResponse
    has_response_model = 'response_model=BaseResponse' in content
    
    # 检查是否使用success_response或error_response
    has_helper_functions = (
        'success_response' in content or 
        'error_response' in content
    )
    
    # 检查是否有@router装饰器
    has_router = '@router.' in content
    
    if has_router:
        # 统计使用BaseResponse的路由数量
        router_pattern = r'@router\.(get|post|put|delete|patch)\([^)]*\)'
        routes = re.findall(router_pattern, content, re.IGNORECASE)
        
        # 检查每个路由是否使用BaseResponse
        base_response_routes = len(re.findall(
            r'response_model\s*=\s*BaseResponse',
            content,
            re.IGNORECASE
        ))
        
        total_routes = len(routes)
        
        if total_routes > 0:
            if base_response_routes == 0:
                issues.append(f"有{total_routes}个路由，但都没有使用BaseResponse")
            elif base_response_routes < total_routes:
                issues.append(
                    f"有{total_routes}个路由，但只有{base_response_routes}个使用BaseResponse"
                )
    
    # 判断是否使用统一响应模型
    is_using = (
        has_base_response_import and 
        (has_response_model or has_helper_functions)
    )
    
    return is_using, issues


def main():
    """主函数"""
    print("=" * 80)
    print("API统一响应模型迁移静态检查")
    print("=" * 80)
    print()
    
    backend_root = Path(__file__).parent.parent
    api_dir = backend_root / "app" / "api"
    
    # 需要检查的API文件（排除特殊文件）
    api_files = [
        "auth.py",
        "subscription.py",
        "download.py",
        "search.py",
        "site.py",
        "workflow.py",
        "notification.py",
        "dashboard.py",
        "settings.py",
        "cloud_storage.py",
        "music.py",
        "calendar.py",
        "hnr.py",
        "recommendation.py",
        "media_identification.py",
        "media.py",
        "charts.py",
        "scheduler.py",
    ]
    
    # 特殊文件（不需要统一响应模型）
    special_files = [
        "websocket.py",  # WebSocket协议
        "health.py",     # 健康检查（特殊格式）
    ]
    
    print(f"[检查目录] {api_dir}")
    print()
    
    results = {}
    total_files = 0
    migrated_files = 0
    special_files_count = 0
    
    # 检查需要迁移的文件
    print("[检查需要迁移的API文件]")
    print()
    for filename in api_files:
        file_path = api_dir / filename
        total_files += 1
        
        if file_path.exists():
            is_using, issues = check_file_uses_unified_response(file_path)
            results[filename] = {
                'path': file_path,
                'using': is_using,
                'issues': issues
            }
            
            if is_using:
                print(f"[OK] {filename:30} - 已使用统一响应模型")
                migrated_files += 1
            else:
                print(f"[X] {filename:30} - 未使用统一响应模型")
                if issues:
                    for issue in issues:
                        print(f"   [!] {issue}")
        else:
            print(f"[!] {filename:30} - 文件不存在")
            results[filename] = {
                'path': file_path,
                'using': False,
                'issues': ['文件不存在']
            }
        print()
    
    # 特殊文件说明
    print("[特殊文件（不需要统一响应模型）]")
    for filename in special_files:
        file_path = api_dir / filename
        if file_path.exists():
            print(f"   - {filename}")
            special_files_count += 1
    print()
    
    # 统计结果
    print("=" * 80)
    print("检查结果统计")
    print("=" * 80)
    print(f"总文件数: {total_files}")
    print(f"[OK] 已迁移: {migrated_files} ({migrated_files/total_files*100:.1f}%)")
    print(f"[X] 未迁移: {total_files - migrated_files} ({(total_files - migrated_files)/total_files*100:.1f}%)")
    print(f"[!] 特殊文件: {special_files_count}")
    print()
    
    if migrated_files == total_files:
        print("[成功] 所有需要迁移的API文件都已使用统一响应模型！")
        return 0
    else:
        print("[警告] 仍有部分文件未使用统一响应模型，请检查上述问题")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except Exception as e:
        print(f"[错误] 检查过程出错: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

