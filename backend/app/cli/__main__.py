"""
CLI 模块主入口

支持通过 python -m app.cli.run_tts_jobs 或 python -m app.cli.run_tts_storage_cleanup 运行
"""
import sys

if len(sys.argv) < 2:
    print("用法：")
    print("  python -m app.cli.run_tts_jobs [参数]")
    print("  python -m app.cli.run_tts_storage_cleanup [参数]")
    sys.exit(1)

module_name = sys.argv[1]

if module_name == "run_tts_jobs":
    from app.cli.run_tts_jobs import cli_entry
    # 移除模块名，保留实际参数
    sys.argv = ["run_tts_jobs"] + sys.argv[2:]
    cli_entry()
elif module_name == "run_tts_storage_cleanup":
    from app.cli.run_tts_storage_cleanup import cli_entry
    # 移除模块名，保留实际参数
    sys.argv = ["run_tts_storage_cleanup"] + sys.argv[2:]
    cli_entry()
else:
    print(f"未知的 CLI 模块：{module_name}")
    print("可用的模块：")
    print("  - run_tts_jobs")
    print("  - run_tts_storage_cleanup")
    sys.exit(1)

