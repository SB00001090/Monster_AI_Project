"""Offline URL scan tests for MonsterGuard."""
from __future__ import annotations

from pathlib import Path

from monsterguard.service import MonsterGuardService


def _svc(tmp_path: Path) -> MonsterGuardService:
    root = Path(__file__).resolve().parents[1]
    return MonsterGuardService(
        enabled=True,
        security_level="medium",
        real_time=False,
        signatures_path=root / "monsterguard" / "database" / "threat_signatures.json",
        cache_dir=tmp_path / "cache",
    )


def test_clean_github(tmp_path: Path) -> None:
    r = _svc(tmp_path).scan_urls(["https://github.com/SB00001090/Guardian-Ai"])
    assert r["score"] == 0 or r["category"] == "clean"
    assert r["block"] is False


def test_lookalike_dlscord(tmp_path: Path) -> None:
    r = _svc(tmp_path).scan_urls(["https://dlscord-nitro.xyz/gift"])
    assert r["score"] >= 55
    assert r["block"] is True


def test_blacklist_host(tmp_path: Path) -> None:
    r = _svc(tmp_path).scan_urls(["https://discord-nitro-free.xyz/claim"])
    assert r["score"] >= 80
    assert r["block"] is True
