"""
运行所有实际场景测试脚本
"""

import sys
import subprocess
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_test_script(script_path: str, description: str):
    """运行测试脚本"""
    print("\n" + "="*60)
    print(f"运行测试: {description}")
    print("="*60)
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode == 0:
            print(f"[OK] {description} - 测试通过")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"[FAIL] {description} - 测试失败")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {description} - 测试超时")
        return False
    except Exception as e:
        print(f"[ERROR] {description} - 执行错误: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("运行所有实际场景测试")
    print("="*60)
    
    tests = [
        ("scripts/test_hmac_signature.py", "HMAC签名功能测试"),
        ("scripts/test_douban_fallback.py", "豆瓣回退机制测试"),
        ("scripts/test_chart_row_integration.py", "ChartRow集成测试"),
    ]
    
    results = []
    for script_path, description in tests:
        script_full_path = project_root / script_path
        if script_full_path.exists():
            success = run_test_script(str(script_full_path), description)
            results.append((description, success))
        else:
            print(f"⚠️ 测试脚本不存在: {script_path}")
            results.append((description, None))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(1 for _, success in results if success is True)
    failed = sum(1 for _, success in results if success is False)
    skipped = sum(1 for _, success in results if success is None)
    
    for description, success in results:
        if success is True:
            print(f"[OK] {description}")
        elif success is False:
            print(f"[FAIL] {description}")
        else:
            print(f"[SKIP] {description} (跳过)")
    
    print(f"\n总计: {passed} 通过, {failed} 失败, {skipped} 跳过")
    
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

