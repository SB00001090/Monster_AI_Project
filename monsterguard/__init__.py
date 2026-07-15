"""MonsterGuard — antivirus-style network protection (local-first).

Distinct from Guardian Platform (`monster_ai.modules.guardian`):
  Platform = E2E sync, toddler learning, OC fingerprint, training vault
  Security = URL/phishing/malware scan, quarantine, real-time protection

Developed by Suckbob | Guardian Ai
"""
from __future__ import annotations

from monsterguard.service import MonsterGuardService

__all__ = ["MonsterGuardService"]
__version__ = "1.0.0"
