#!/usr/bin/env python3
"""Start MonsterGuard 24/7 service.

Conceptual layout name: start_monster_guard.py
Implementation: guardian_ai.monster_guard (always-on core)

Usage:
  python start_monster_guard.py              # run forever
  python start_monster_guard.py status
  python start_monster_guard.py scan-url https://example.com
  python start_monster_guard.py scan-discord "free nitro"

Same as: python run_monster_guard.py

Developed by Suckbob | Guardian Ai
"""
from __future__ import annotations

import sys

from guardian_ai.monster_guard.main_monster_guard import main


if __name__ == "__main__":
    argv = sys.argv[1:]
    if not argv:
        argv = ["run"]
    raise SystemExit(main(argv))
