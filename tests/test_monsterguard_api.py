"""API tests for MonsterGuard routes."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from monsterguard.api import create_compat_router, create_router
from monsterguard.service import MonsterGuardService


def _client(tmp_path: Path) -> TestClient:
    root = Path(__file__).resolve().parents[1]
    app = FastAPI()
    app.include_router(create_router())
    app.include_router(create_compat_router())
    svc = MonsterGuardService(
        enabled=True,
        security_level="medium",
        real_time=False,
        signatures_path=root / "monsterguard" / "database" / "threat_signatures.json",
        cache_dir=tmp_path / "cache",
    )
    app.state.monsterguard = svc
    app.state.guardian_security = svc
    return TestClient(app)


def test_status(tmp_path: Path) -> None:
    c = _client(tmp_path)
    r = c.get("/api/monsterguard/status")
    assert r.status_code == 200
    assert r.json()["product"] == "MonsterGuard"


def test_compat_alias(tmp_path: Path) -> None:
    c = _client(tmp_path)
    assert c.get("/api/guardian-security/status").status_code == 200


def test_scan_url(tmp_path: Path) -> None:
    c = _client(tmp_path)
    r = c.post(
        "/api/monsterguard/scan/url",
        json={"urls": ["https://dlscord-nitro.xyz/gift"]},
    )
    assert r.status_code == 200
    assert r.json()["block"] is True


def test_scan_discord(tmp_path: Path) -> None:
    c = _client(tmp_path)
    r = c.post(
        "/api/monsterguard/scan/discord",
        json={"content": "free nitro gift claim now"},
    )
    assert r.status_code == 200
    assert r.json()["score"] >= 30
