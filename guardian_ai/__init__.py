"""guardian_ai package namespace.

- `guardian_ai.monster_guard` — MonsterGuard 24/7 core (preferred)
- top-level `monsterguard` — FastAPI scan API engines (shared)
- `monster_ai.modules.guardian` — Guardian Platform (E2E / toddler / OC)

Legacy: importing `GuardianSecurityService` still works via monsterguard shim.
"""
from __future__ import annotations

from guardian_ai.monster_guard import MonsterGuardCore

try:
    from monsterguard import MonsterGuardService
    from monsterguard.service import MonsterGuardService as GuardianSecurityService
except ImportError:  # pragma: no cover
    MonsterGuardService = None  # type: ignore[misc, assignment]
    GuardianSecurityService = None  # type: ignore[misc, assignment]

__all__ = ["MonsterGuardCore", "MonsterGuardService", "GuardianSecurityService"]
