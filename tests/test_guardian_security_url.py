"""Compat tests — old guardian_ai import still works via shim."""
from __future__ import annotations

from pathlib import Path

from guardian_ai.service import GuardianSecurityService


def test_shim_service(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    svc = GuardianSecurityService(
        enabled=True,
        security_level="medium",
        real_time=False,
        signatures_path=root / "monsterguard" / "database" / "threat_signatures.json",
        cache_dir=tmp_path / "cache",
    )
    r = svc.scan_urls(["https://github.com"])
    assert r["block"] is False
