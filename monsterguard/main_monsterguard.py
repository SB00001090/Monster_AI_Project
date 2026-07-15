"""CLI for MonsterGuard: scan / status / report / discord.

Usage:
  python -m monsterguard.main_monsterguard status
  python -m monsterguard.main_monsterguard scan-url https://dlscord-nitro.xyz/gift
  python -m monsterguard.main_monsterguard scan-text "free nitro click here"
  python -m monsterguard.main_monsterguard scan-discord "claim free nitro https://dlscord.xyz"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _default_service():
    from monsterguard.service import MonsterGuardService

    root = Path(__file__).resolve().parent
    repo = root.parent
    return MonsterGuardService(
        enabled=True,
        security_level="medium",
        signatures_path=root / "database" / "threat_signatures.json",
        cache_dir=repo / "data" / "monsterguard",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="monsterguard", description="MonsterGuard CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status")
    sub.add_parser("dashboard")
    sub.add_parser("report")

    p_url = sub.add_parser("scan-url")
    p_url.add_argument("urls", nargs="+")

    p_text = sub.add_parser("scan-text")
    p_text.add_argument("text")

    p_dl = sub.add_parser("scan-download")
    p_dl.add_argument("path_or_url")

    p_dc = sub.add_parser("scan-discord")
    p_dc.add_argument("content")

    args = parser.parse_args(argv)
    svc = _default_service()

    if args.cmd == "status":
        print(json.dumps(svc.status(), ensure_ascii=False, indent=2))
    elif args.cmd == "dashboard":
        print(json.dumps(svc.dashboard(), ensure_ascii=False, indent=2))
    elif args.cmd == "report":
        print(json.dumps(svc.report(), ensure_ascii=False, indent=2))
    elif args.cmd == "scan-url":
        print(json.dumps(svc.scan_urls(args.urls), ensure_ascii=False, indent=2))
    elif args.cmd == "scan-text":
        print(json.dumps(svc.scan_text(args.text), ensure_ascii=False, indent=2))
    elif args.cmd == "scan-download":
        print(json.dumps(svc.scan_download(args.path_or_url), ensure_ascii=False, indent=2))
    elif args.cmd == "scan-discord":
        print(json.dumps(svc.scan_discord_message(args.content), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
