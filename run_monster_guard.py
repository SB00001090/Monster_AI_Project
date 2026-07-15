#!/usr/bin/env python3
"""Start MonsterGuard 24/7 service (standalone entry).

Usage:
  python run_monster_guard.py
  python run_monster_guard.py status
  python run_monster_guard.py scan-url https://example.com

Developed by Suckbob | Guardian Ai
"""
from __future__ import annotations

import sys

from guardian_ai.monster_guard.main_monster_guard import main


if __name__ == "__main__":
    # Default to always-on run when no args
    argv = sys.argv[1:]
    if not argv:
        argv = ["run"]
    raise SystemExit(main(argv))
