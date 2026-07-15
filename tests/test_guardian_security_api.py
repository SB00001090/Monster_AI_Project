"""Compat: legacy path still served."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from monsterguard.api import create_compat_router
from monsterguard.service import MonsterGuardService


def test_legacy_status(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    app = FastAPI()
    app.include_router(create_compat_router())
    app.state.monsterguard = MonsterGuardService(
        enabled=True,
        real_time=False,
        signatures_path=root / "monsterguard" / "database" / "threat_signatures.json",
        cache_dir=tmp_path / "cache",
    )
    c = TestClient(app)
    assert c.get("/api/guardian-security/status").status_code == 200
