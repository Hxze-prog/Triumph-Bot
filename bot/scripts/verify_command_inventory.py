from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COGS = ROOT / "bot" / "cogs"
DASHBOARD_COMMANDS = ROOT / "dashboard" / "src" / "lib" / "commands.ts"
COMMAND_DECORATORS = {"command", "group", "hybrid_command", "hybrid_group"}


def _string_value(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def bot_commands() -> dict[str, str]:
    found: dict[str, str] = {}
    for path in sorted(COGS.glob("*.py")):
        if path.name.startswith("_"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for decorator in item.decorator_list:
                    if not isinstance(decorator, ast.Call):
                        continue
                    if not isinstance(decorator.func, ast.Attribute):
                        continue
                    if decorator.func.attr not in COMMAND_DECORATORS:
                        continue
                    name = item.name
                    for keyword in decorator.keywords:
                        if keyword.arg == "name":
                            name = _string_value(keyword.value) or name
                    parent = None
                    if (
                        isinstance(decorator.func.value, ast.Name)
                        and decorator.func.value.id != "commands"
                    ):
                        parent = decorator.func.value.id
                    full = f"{parent} {name}" if parent else name
                    found[full] = path.stem
    return found


def dashboard_commands() -> list[str]:
    text = DASHBOARD_COMMANDS.read_text(encoding="utf-8")
    return re.findall(r'\bname:\s*"([^"]+)"', text)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare bot command definitions with the dashboard command list."
    )
    parser.add_argument("--expect", type=int, default=93)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    bot = bot_commands()
    dashboard = dashboard_commands()
    dashboard_counts = Counter(dashboard)
    duplicates = sorted(
        name for name, count in dashboard_counts.items() if count > 1
    )
    dashboard_set = set(dashboard)
    bot_set = set(bot)
    missing_in_dashboard = sorted(bot_set - dashboard_set)
    missing_in_bot = sorted(dashboard_set - bot_set)

    errors: list[str] = []
    if len(bot) != args.expect:
        errors.append(f"bot command count is {len(bot)}, expected {args.expect}")
    if len(dashboard) != args.expect:
        errors.append(
            f"dashboard command count is {len(dashboard)}, expected {args.expect}"
        )
    if duplicates:
        errors.append("duplicate dashboard names: " + ", ".join(duplicates))
    if missing_in_dashboard:
        errors.append(
            "bot commands missing from dashboard: " + ", ".join(missing_in_dashboard)
        )
    if missing_in_bot:
        errors.append(
            "dashboard commands missing from bot: " + ", ".join(missing_in_bot)
        )

    module_counts = Counter(bot.values())

    if args.json:
        print(
            json.dumps(
                {
                    "bot_count": len(bot),
                    "dashboard_count": len(dashboard),
                    "expected": args.expect,
                    "modules": dict(sorted(module_counts.items())),
                    "missing_in_dashboard": missing_in_dashboard,
                    "missing_in_bot": missing_in_bot,
                    "duplicates": duplicates,
                    "errors": errors,
                },
                indent=2,
            )
        )
    else:
        print(f"Bot commands:       {len(bot)}")
        print(f"Dashboard commands: {len(dashboard)}")
        print(f"Expected:           {args.expect}")
        print("Modules:")
        for module, count in sorted(module_counts.items()):
            print(f"  {module:16} {count:3}")
        if errors:
            print("FAIL")
            for error in errors:
                print(f"  - {error}")
        else:
            print("PASS: bot and dashboard command inventories match")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
