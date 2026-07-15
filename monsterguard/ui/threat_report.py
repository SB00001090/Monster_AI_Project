"""Threat report builder."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from monsterguard.service import MonsterGuardService


def build_threat_report(svc: MonsterGuardService) -> dict[str, Any]:
    events = svc.rtp.recent_events(limit=30)
    blocks = [e for e in events if e.get("type") in ("block", "quarantine")]
    return {
        "title": "MonsterGuard Threat Report",
        "enabled": svc.enabled,
        "security_level": svc.security_level,
        "recent_blocks": blocks[:15],
        "recent_events": events[:15],
        "quarantine": svc.quarantine.list_active(limit=15),
        "signatures": svc.signatures.status(),
    }
