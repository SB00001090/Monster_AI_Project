"""Shared helpers for MonsterGuard settings (Python side)."""
from __future__ import annotations

from typing import Any


DEFAULT_MONSTERGUARD: dict[str, Any] = {
    "enabled": True,
    "security_level": "medium",
    "real_time": True,
    "block_downloads": True,
    "use_llm_classifier": False,
    "signatures_path": "monsterguard/database/threat_signatures.json",
    "discord_patterns_path": "monsterguard/database/discord_scam_patterns.json",
    "cache_dir": "./data/monsterguard",
    "reputation_ttl_hours": 24,
}

# Legacy alias
DEFAULT_GUARDIAN_SECURITY = DEFAULT_MONSTERGUARD


def normalize_security_level(level: str | None) -> str:
    val = (level or "medium").strip().lower()
    if val not in ("low", "medium", "high"):
        return "medium"
    return val
