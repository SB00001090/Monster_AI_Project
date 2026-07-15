"""Thin dual-engine orchestrator documentation entry.

Monster AI (generation / platform) and MonsterGuard (security / Discord scam)
share one process via FastAPI `create_app`.

Developed by Suckbob | Guardian Ai
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


def start_monster(settings: Any | None = None):
    """Create FastAPI app (Monster + Platform + MonsterGuard routers)."""
    from monster_ai.app import create_app
    from monster_ai.config import load_settings

    cfg = settings or load_settings()
    return create_app(cfg)


def build_monsterguard(settings: Any | None = None):
    """Standalone MonsterGuard service (no HTTP)."""
    from monster_ai.config import load_settings, MonsterGuardSettings
    from monsterguard.service import MonsterGuardService

    cfg = settings or load_settings()
    gs = getattr(cfg, "monsterguard", None) or MonsterGuardSettings()
    root = Path(__file__).resolve().parent
    return MonsterGuardService(
        enabled=gs.enabled,
        security_level=gs.security_level,
        real_time=gs.real_time,
        block_downloads=gs.block_downloads,
        use_llm_classifier=gs.use_llm_classifier,
        signatures_path=gs.signatures_path
        if Path(gs.signatures_path).is_absolute()
        else str(root / gs.signatures_path),
        cache_dir=gs.cache_dir,
        reputation_ttl_hours=gs.reputation_ttl_hours,
    )


# Alias for older call sites
build_guardian_security = build_monsterguard


def describe_architecture() -> dict[str, str]:
    return {
        "monster_ai": "Generation, RP, learning, Discord bot, Web UI",
        "modules.guardian": "Guardian Platform — E2E sync, toddler learning, OC, vault",
        "monsterguard": "MonsterGuard HTTP scan engines (/api/monsterguard)",
        "guardian_ai.monster_guard": "MonsterGuard 24/7 core — monitor, auto-block, self-repair",
        "run_monster_guard": "python run_monster_guard.py",
        "forum": "Web layer (Node tRPC + React), not Python forum/",
        "entry": "main.py / run.bat → create_app; orchestrator.start_monster()",
    }
