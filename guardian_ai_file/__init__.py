"""Conceptual alias package: guardian_ai_file → guardian_ai.

Prefer `guardian_ai.monster_guard` for 24/7 MonsterGuard core.
"""
from __future__ import annotations

from guardian_ai import MonsterGuardCore, MonsterGuardService, GuardianSecurityService

# Nested re-export for docs-style paths
from guardian_ai import monster_guard as monster_guard  # noqa: F401

__all__ = [
    "MonsterGuardCore",
    "MonsterGuardService",
    "GuardianSecurityService",
    "monster_guard",
]
