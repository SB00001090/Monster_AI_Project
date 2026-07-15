"""CLI / library entry for MonsterGuard core (under guardian_ai.monster_guard).

Usage:
  python -m guardian_ai.monster_guard.main_monster_guard status
  python -m guardian_ai.monster_guard.main_monster_guard scan-url https://dlscord-nitro.xyz/gift
  python -m guardian_ai.monster_guard.main_monster_guard scan-discord "free nitro"
  python -m guardian_ai.monster_guard.main_monster_guard run   # 24/7
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(prog="monster-guard", description="MonsterGuard 24/7 core")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("run")
    p_url = sub.add_parser("scan-url")
    p_url.add_argument("url")
    p_text = sub.add_parser("scan-text")
    p_text.add_argument("text")
    p_dc = sub.add_parser("scan-discord")
    p_dc.add_argument("content")

    args = parser.parse_args(argv)

    from guardian_ai.monster_guard.service import MonsterGuardCore
    from guardian_ai.monster_guard.core.service_runner import ServiceRunner

    core = MonsterGuardCore()

    if args.cmd == "status":
        print(json.dumps(core.status(), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "scan-url":
        print(json.dumps(core.scan_url(args.url), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "scan-text":
        print(json.dumps(core.scan_text(args.text), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "scan-discord":
        print(json.dumps(core.scan_discord(args.content), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "run":
        runner = ServiceRunner(core)
        return asyncio.run(runner.run_forever())
    return 1


if __name__ == "__main__":
    sys.exit(main())
