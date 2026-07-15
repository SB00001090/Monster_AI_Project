"""MonsterGuard 24/7 core service package (under guardian_ai).

Canonical entry for the antivirus-style Discord/network protection loop.
Reuses engines from top-level `monsterguard` where helpful, and adds
always-on monitor, auto-block, and self-repair.

Developed by Suckbob | Guardian Ai
"""
from __future__ import annotations

from guardian_ai.monster_guard.service import MonsterGuardCore

__all__ = ["MonsterGuardCore"]
__version__ = "1.1.0"
