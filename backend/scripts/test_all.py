"""
一键回归脚本

串联运行核心测试脚本，出现任意失败立即停止并返回非零状态。

默认执行顺序：
1. quick_test.py
2. test_functional.py
3. test_music_minimal.py
4. test_music_minimal.py --execute
5. test_graphql_minimal.py
6. test_rsshub_minimal.py

运行前请确保后端已启动，并配置好 `API_BASE_URL` / `API_PREFIX`（默认 http://127.0.0.1:8000 /api/v1）。
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
import json
import time

SCRIPT_DIR = Path(__file__).resolve().parent

DEFAULT_SEQUENCE = [
    ("quick_test.py", []),
    ("test_functional.py", []),
    ("test_music_minimal.py", []),
    ("test_music_minimal.py", ["--execute"]),
    ("test_graphql_minimal.py", []),
    ("test_decision_minimal.py", []),
    ("../tests/test_plugins_api.py", []),
    ("test_rsshub_minimal.py", []),
]


def _env_flag(env: dict[str, str], key: str, default: bool) -> bool:
    raw = env.get(key)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def analyze_output(script: str, stdout: str, stderr: str) -> list[str]:
    warnings: list[str] = []
    buffers = [stdout or "", stderr or ""]
    patterns = [
        (
            "创建订阅异常",
            "检测到 {count} 次 '创建订阅异常'，可能由历史脏数据或站点限流导致",
        ),
        (
            "Redis connection failed",
            "检测到 {count} 次 Redis 连接失败，请确认 REDIS_ENABLED 配置或网络",
        ),
        (
            "Redis 连接失败",
            "检测到 {count} 次 Redis 连接失败，请确认 REDIS_ENABLED 配置或网络",
        ),
        (
            "task does not exist",
            "检测到 {count} 次 Scheduler 'task does not exist'，请确认 scheduler_tasks 预置记录",
        ),
        (
            "SignaturePack",
            "检测到 {count} 次 SignaturePack 相关告警，可检查 site_overrides 配置",
        ),
    ]
    for needle, message in patterns:
        count = sum(buf.count(needle) for buf in buffers)
        if count:
            warnings.append(f"{script}: " + message.format(count=count))
    return warnings


def run_script(
    script: str,
    args: list[str],
    env: dict[str, str],
    *,
    show_output: bool,
) -> tuple[list[str], float]:
    path = SCRIPT_DIR / script
    if not path.exists():
        raise FileNotFoundError(f"脚本不存在: {path}")

    cmd = [sys.executable, str(path), *args]
    arg_string = " ".join(args)
    print(f"\n==> 执行 {script} {arg_string}".strip())
    started = time.perf_counter()
    result = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
    )
    duration = time.perf_counter() - started
    if show_output:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="")
    if result.returncode != 0:
        if not show_output:
            if result.stdout:
                print("\n--- STDOUT ---")
                print(result.stdout)
            if result.stderr:
                print("\n--- STDERR ---")
                print(result.stderr)
        print(f"[FAIL] {script} 失败（退出码 {result.returncode}）")
        raise SystemExit(f"{script} 运行失败（退出码 {result.returncode}）")
    print(f"[OK] {script} 完成")
    warnings = analyze_output(script, result.stdout or "", result.stderr or "")
    if warnings and not show_output:
        print("    ↳ 检测到非致命警告，可查看总结")
    return warnings, duration


def main() -> None:
    parser = argparse.ArgumentParser(description="运行 VabHub 核心回归脚本")
    parser.add_argument(
        "--skip-music-execute",
        action="store_true",
        help="跳过 test_music_minimal.py --execute（避免真实下载）",
    )
    parser.add_argument(
        "--with-short-drama",
        action="store_true",
        help="强制执行短剧最小回归脚本（默认需设置 ENABLE_SHORT_DRAMA_TEST=1 才会运行）",
    )
    parser.add_argument(
        "--show-output",
        action="store_true",
        help="实时打印各子脚本完整输出（默认仅在失败时输出捕获内容）",
    )
    parser.add_argument(
        "--report-path",
        type=str,
        default=None,
        help="将执行摘要保存为 JSON 文件（例如 reports/test_all-latest.json）",
    )
    args = parser.parse_args()

    env = os.environ.copy()
    # 与 api_test_config.py 和 app/core/config.py 保持一致
    env.setdefault("API_BASE_URL", "http://127.0.0.1:8000")
    env.setdefault("API_PREFIX", "/api/v1")

    redis_enabled = _env_flag(env, "REDIS_ENABLED", True)
    rsshub_enabled = _env_flag(env, "RSSHUB_ENABLED", True)
    downloader_simulation = _env_flag(env, "DOWNLOAD_SIMULATION_MODE", False)

    skipped: list[tuple[str, str]] = []
    sequence: list[tuple[str, list[str]]] = []
    for script, script_args in DEFAULT_SEQUENCE:
        if script == "test_music_minimal.py" and "--execute" in script_args:
            if args.skip_music_execute:
                skipped.append((f"{script} {' '.join(script_args)}", "用户指定 --skip-music-execute"))
                continue
            if downloader_simulation:
                skipped.append((f"{script} {' '.join(script_args)}", "下载器处于模拟模式"))
                continue
        if script == "test_rsshub_minimal.py" and not rsshub_enabled:
            skipped.append((script, "RSSHub 已禁用"))
            continue
        sequence.append((script, script_args))

    short_drama_enabled = args.with_short_drama or _env_flag(env, "ENABLE_SHORT_DRAMA_TEST", False)
    if short_drama_enabled:
        sequence.append(("test_short_drama_minimal.py", []))

    aggregated_warnings: list[str] = []
    execution_summary: list[dict[str, object]] = []
    for script, script_args in sequence:
        warnings, duration = run_script(
            script,
            script_args,
            env,
            show_output=args.show_output,
        )
        aggregated_warnings.extend(warnings)
        execution_summary.append(
            {
                "script": script,
                "args": script_args,
                "duration_seconds": round(duration, 3),
                "warnings": warnings,
            }
        )

    if skipped:
        print("\n[SKIP] 以下脚本因环境或参数被跳过：")
        for script, reason in skipped:
            print(f" - {script}: {reason}")

    missing_components = []
    if not redis_enabled:
        missing_components.append("Redis")
    if not rsshub_enabled:
        missing_components.append("RSSHub")
    if downloader_simulation:
        missing_components.append("Downloader")

    if aggregated_warnings:
        print("\n[WARN] 已知告警摘要：")
        for item in aggregated_warnings:
            print(f" - {item}")

    if missing_components:
        print(f"\n[INFO] 当前环境缺少：{', '.join(missing_components)}")
    else:
        print("\n[INFO] 当前环境已启用所有可选依赖")

    print("\n所有核心测试脚本已全部通过 [OK]")

    if args.report_path:
        report = {
            "status": "ok",
            "environment": {
                "redis_enabled": redis_enabled,
                "rsshub_enabled": rsshub_enabled,
                "downloader_simulation_mode": downloader_simulation,
            },
            "skipped": [{"script": s, "reason": r} for s, r in skipped],
            "warnings": aggregated_warnings,
            "results": execution_summary,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        report_path = Path(args.report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="utf-8") as fp:
            json.dump(report, fp, ensure_ascii=False, indent=2)
        print(f"[INFO] 测试报告已写入 {report_path}")


if __name__ == "__main__":
    main()

