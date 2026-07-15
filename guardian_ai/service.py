"""Shim: GuardianSecurityService → MonsterGuardService."""
from __future__ import annotations

from monsterguard.service import MonsterGuardService as GuardianSecurityService
from monsterguard.service import MonsterGuardService

__all__ = ["GuardianSecurityService", "MonsterGuardService"]
