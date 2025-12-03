"""
插件脚手架脚本

用法示例：
    python backend/scripts/create_plugin.py my_pt_plugin --name "My PT Plugin"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = REPO_ROOT / "templates"
PLUGINS_DIR = REPO_ROOT / "plugins"


PLACEHOLDERS = (
    "PLUGIN_ID",
    "PLUGIN_NAME",
    "PLUGIN_VERSION",
    "PLUGIN_DESCRIPTION",
    "PLUGIN_AUTHOR",
)


def guess_display_name(plugin_id: str) -> str:
    parts = plugin_id.replace("-", "_").split("_")
    return " ".join(word.capitalize() for word in parts if word) or plugin_id


def render_template(content: str, mapping: dict[str, str]) -> str:
    rendered = content
    for key, value in mapping.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def create_plugin_file(
    plugin_id: str,
    template_name: str,
    name: str,
    version: str,
    description: str,
    author: str,
    force: bool = False,
) -> Path:
    template_path = TEMPLATE_ROOT / template_name / "plugin.py"
    if not template_path.exists():
        raise SystemExit(f"模板不存在：{template_path}")

    target_path = PLUGINS_DIR / f"{plugin_id}.py"
    if target_path.exists() and not force:
        raise SystemExit(f"目标文件已存在：{target_path}（若需覆盖请添加 --force）")

    content = template_path.read_text(encoding="utf-8")
    replacements = {
        "PLUGIN_ID": plugin_id,
        "PLUGIN_NAME": name,
        "PLUGIN_VERSION": version,
        "PLUGIN_DESCRIPTION": description,
        "PLUGIN_AUTHOR": author,
    }
    missing = [key for key in PLACEHOLDERS if f"{{{{{key}}}}}" not in content]
    if missing:
        raise SystemExit(f"模板缺少占位符：{', '.join(missing)}")

    rendered = render_template(content, replacements)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(rendered, encoding="utf-8")
    return target_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="创建 VabHub 插件骨架")
    parser.add_argument("plugin_id", help="插件 ID / 文件名，例如 my_pt_plugin")
    parser.add_argument(
        "--from-template",
        default="plugin_pt_site",
        help="模板目录名称（默认：plugin_pt_site）",
    )
    parser.add_argument("--name", help="展示名称（默认根据 ID 推断）")
    parser.add_argument("--version", default="0.1.0", help="插件版本（默认 0.1.0）")
    parser.add_argument("--description", help="插件描述（默认自动生成）")
    parser.add_argument("--author", default="VabHub", help="作者名（默认 VabHub）")
    parser.add_argument("--force", action="store_true", help="若目标文件存在则覆盖")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    plugin_id = args.plugin_id.strip()
    if not plugin_id:
        raise SystemExit("插件 ID 不能为空")

    display_name = args.name or guess_display_name(plugin_id)
    description = args.description or f"{display_name} 插件骨架"

    target = create_plugin_file(
        plugin_id=plugin_id,
        template_name=args.from_template,
        name=display_name,
        version=args.version,
        description=description,
        author=args.author,
        force=args.force,
    )

    print("✅ 插件骨架已生成：", target)
    print("下一步：")
    print("  1. 在该文件中补充站点特定逻辑 / API 调用。")
    print("  2. 在后端运行期间可通过 Plugins 页面点击“重载”启用新插件。")
    print("  3. 如需自测，可执行 `python backend/scripts/test_all.py --with-short-drama` 或定制脚本。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)


